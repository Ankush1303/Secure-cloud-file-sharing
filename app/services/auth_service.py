from datetime import datetime
from flask import current_app
from app.extensions import db, bcrypt
from app.models import User, ActivityLog
from app.services.crypto_service import CryptoService

class AuthService:
    @staticmethod
    def register_user(username, email, password):
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        private_pem, public_pem = CryptoService.generate_rsa_keypair()
        master_key = current_app.config.get('RSA_MASTER_KEY')
        if not master_key:
            from cryptography.fernet import Fernet
            master_key = Fernet.generate_key().decode('utf-8')
        encrypted_private = CryptoService.encrypt_private_key(private_pem, master_key)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            rsa_public_key=public_pem,
            rsa_private_key_encrypted=encrypted_private
        )
        db.session.add(user)
        db.session.commit()
        AuthService.log_activity(user.id, 'signup', details=f"User {username} registered")
        return user, None

    @staticmethod
    def authenticate_user(username_or_email, password):
        user = User.query.filter_by(username=username_or_email).first()
        if not user:
            user = User.query.filter_by(email=username_or_email).first()
        if not user:
            return None, "Invalid username or password"
        if not user.is_active:
            return None, "Account is deactivated"
        if not bcrypt.check_password_hash(user.password_hash, password):
            return None, "Invalid username or password"
        user.last_login = datetime.utcnow()
        db.session.commit()
        AuthService.log_activity(user.id, 'login', details=f"User {user.username} logged in")
        return user, None

    @staticmethod
    def get_user_private_key(user):
        master_key = current_app.config.get('RSA_MASTER_KEY')
        if not master_key:
            return None
        try:
            return CryptoService.decrypt_private_key(user.rsa_private_key_encrypted, master_key)
        except Exception as e:
            current_app.logger.error(f"Failed to decrypt private key: {e}")
            return None

    @staticmethod
    def log_activity(user_id, action, file_id=None, details=None, ip_address=None):
        try:
            log = ActivityLog(
                user_id=user_id,
                action=action,
                file_id=file_id,
                details=details,
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to log activity: {e}")

    @staticmethod
    def get_user_stats(user_id):
        from app.models import File
        total_files = File.query.filter_by(user_id=user_id, is_deleted=False).count()
        total_size = db.session.query(db.func.sum(File.file_size)).filter_by(
            user_id=user_id, is_deleted=False
        ).scalar() or 0
        recent_uploads = File.query.filter_by(user_id=user_id, is_deleted=False).order_by(
            File.uploaded_at.desc()
        ).limit(5).all()
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'recent_uploads': [f.to_dict() for f in recent_uploads]
        }