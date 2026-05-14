import os
import uuid
import base64
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import File, SharedFile
from app.services.crypto_service import CryptoService
from app.services.auth_service import AuthService

LOCAL_ENCRYPTED_DIR = "local_storage/encrypted"

class FileService:
    @staticmethod
    def allowed_file(filename):
        allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

    @staticmethod
    def upload_file(file_obj, user, algorithm='fernet', ip_address=None):
        if not file_obj or file_obj.filename == '':
            return None, "No file selected"
        if not FileService.allowed_file(file_obj.filename):
            return None, "File type not allowed"
        file_data = file_obj.read()
        file_size = len(file_data)
        if file_size == 0:
            return None, "Empty file"
        if file_size > current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024):
            return None, "File too large"

        os.makedirs(LOCAL_ENCRYPTED_DIR, exist_ok=True)

        original_filename = secure_filename(file_obj.filename)
        unique_id = str(uuid.uuid4())
        local_path = os.path.join(LOCAL_ENCRYPTED_DIR, f"user_{user.id}_{unique_id}.enc")

        try:
            sym_key, nonce, enc_algorithm = CryptoService.generate_file_encryption_key(algorithm)
            encrypted_data = CryptoService.encrypt_file_data(file_data, sym_key, nonce, enc_algorithm)
            encrypted_sym_key = CryptoService.encrypt_symmetric_key(sym_key, user.rsa_public_key)

            with open(local_path, 'wb') as f:
                f.write(encrypted_data)

            file_record = File(
                user_id=user.id,
                filename=local_path,
                original_filename=original_filename,
                s3_path=local_path,
                file_size=file_size,
                mime_type=file_obj.content_type or 'application/octet-stream',
                encrypted_key=encrypted_sym_key,
                encryption_type=enc_algorithm,
                nonce=base64.b64encode(nonce).decode('utf-8') if nonce else None
            )
            db.session.add(file_record)
            db.session.commit()

            AuthService.log_activity(
                user.id, 'upload',
                file_id=file_record.id,
                details=f"Uploaded {original_filename} ({file_size} bytes)",
                ip_address=ip_address
            )
            return file_record, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Upload failed: {e}")
            return None, f"Upload failed: {str(e)}"

    @staticmethod
    def download_file(file_id, user, ip_address=None):
        file_record = File.query.get(file_id)
        if not file_record:
            return None, None, "File not found"

        if file_record.user_id == user.id:
            encrypted_sym_key = file_record.encrypted_key
        else:
            share = SharedFile.query.filter_by(
                file_id=file_id,
                shared_with_user_id=user.id
            ).first()
            if not share:
                return None, None, "Access denied"
            encrypted_sym_key = share.encrypted_key
            if not encrypted_sym_key:
                return None, None, "Shared key not found"

        try:
            with open(file_record.s3_path, 'rb') as f:
                encrypted_data = f.read()

            private_key = AuthService.get_user_private_key(user)
            if not private_key:
                return None, None, "Failed to retrieve encryption keys"

            sym_key = CryptoService.decrypt_symmetric_key(encrypted_sym_key, private_key)

            nonce = None
            if file_record.nonce:
                nonce = base64.b64decode(file_record.nonce)

            file_data = CryptoService.decrypt_file_data(encrypted_data, sym_key, file_record.encryption_type)

            AuthService.log_activity(
                user.id, 'download',
                file_id=file_id,
                details=f"Downloaded {file_record.original_filename}",
                ip_address=ip_address
            )
            return file_data, file_record.original_filename, None

        except Exception as e:
            current_app.logger.error(f"Download failed: {e}")
            return None, None, f"Download failed: {str(e)}"

    @staticmethod
    def get_user_files(user_id, include_deleted=False):
        query = File.query.filter_by(user_id=user_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(File.uploaded_at.desc()).all()

    @staticmethod
    def get_shared_files(user_id):
        shared = SharedFile.query.filter_by(shared_with_user_id=user_id).all()
        files = []
        for s in shared:
            if s.file and not s.file.is_deleted:
                files.append(s.file)
        return files

    @staticmethod
    def soft_delete_file(file_id, user_id):
        file_record = File.query.get(file_id)
        if not file_record or file_record.user_id != user_id:
            return False
        file_record.is_deleted = True
        db.session.commit()
        AuthService.log_activity(
            user_id, 'delete',
            file_id=file_id,
            details=f"Deleted {file_record.original_filename}"
        )
        return True

    @staticmethod
    def share_file(file_id, owner_id, shared_with_username, permissions='read'):
        from app.models import User
        file_record = File.query.get(file_id)
        if not file_record or file_record.user_id != owner_id:
            return None, "File not found or access denied"
        target_user = User.query.filter_by(username=shared_with_username).first()
        if not target_user:
            return None, "User not found"
        if target_user.id == owner_id:
            return None, "Cannot share with yourself"
        existing = SharedFile.query.filter_by(file_id=file_id, shared_with_user_id=target_user.id).first()
        if existing:
            return None, "File already shared with this user"

        try:
            owner_private_key = AuthService.get_user_private_key(file_record.owner)
            if not owner_private_key:
                return None, "Failed to retrieve owner encryption keys"

            sym_key = CryptoService.decrypt_symmetric_key(file_record.encrypted_key, owner_private_key)
            recipient_encrypted_key = CryptoService.encrypt_symmetric_key(sym_key, target_user.rsa_public_key)

            share = SharedFile(
                file_id=file_id,
                shared_by_user_id=owner_id,
                shared_with_user_id=target_user.id,
                permissions=permissions,
                encrypted_key=recipient_encrypted_key
            )
            db.session.add(share)
            db.session.commit()

            AuthService.log_activity(
                owner_id, 'share',
                file_id=file_id,
                details=f"Shared {file_record.original_filename} with {shared_with_username}"
            )
            return share, None

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Share failed: {e}")
            return None, f"Share failed: {str(e)}"