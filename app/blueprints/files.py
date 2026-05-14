from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
import io
import os
from app.services.file_service import FileService
from app.services.auth_service import AuthService
from app.utils.validators import Validator

files_bp = Blueprint('files', __name__, template_folder='../templates/files')

@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        algorithm = request.form.get('algorithm', 'fernet')
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        valid, error = Validator.validate_file_upload(
            file.filename,
            file_size,
            current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        )
        if not valid:
            flash(error, 'danger')
            return redirect(request.url)
        file_record, error = FileService.upload_file(
            file,
            current_user,
            algorithm=algorithm,
            ip_address=request.remote_addr
        )
        if error:
            flash(error, 'danger')
            return redirect(request.url)
        flash(f'File "{file_record.original_filename}" uploaded and encrypted successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('files/upload.html', user=current_user)

@files_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    file_data, filename, error = FileService.download_file(
        file_id,
        current_user,
        ip_address=request.remote_addr
    )
    if error:
        flash(error, 'danger')
        return redirect(url_for('main.dashboard'))
    return send_file(
        io.BytesIO(file_data),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=filename
    )

@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    success = FileService.soft_delete_file(file_id, current_user.id)
    if success:
        flash('File deleted successfully', 'success')
    else:
        flash('File not found or access denied', 'danger')
    return redirect(url_for('main.dashboard'))

@files_bp.route('/share/<int:file_id>', methods=['POST'])
@login_required
def share(file_id):
    username = request.form.get('username', '').strip()
    permissions = request.form.get('permissions', 'read')
    if not username:
        flash('Please enter a username', 'danger')
        return redirect(url_for('main.dashboard'))
    share, error = FileService.share_file(
        file_id,
        current_user.id,
        username,
        permissions
    )
    if error:
        flash(error, 'danger')
    else:
        flash(f'File shared with {username}', 'success')
    return redirect(url_for('main.dashboard'))

@files_bp.route('/api/list')
@login_required
def api_list_files():
    files = FileService.get_user_files(current_user.id)
    return jsonify({
        'files': [f.to_dict() for f in files]
    })