from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from app.models import ActivityLog

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = AuthService.get_user_stats(current_user.id)
    files = FileService.get_user_files(current_user.id)
    shared_files = FileService.get_shared_files(current_user.id)
    recent_activity = ActivityLog.query.filter_by(user_id=current_user.id).order_by(
        ActivityLog.timestamp.desc()
    ).limit(10).all()
    return render_template('files/dashboard.html',
                         stats=stats,
                         files=files,
                         shared_files=shared_files,
                         activity=recent_activity,
                         user=current_user)

@main_bp.route('/history')
@login_required
def history():
    files = FileService.get_user_files(current_user.id)
    return render_template('files/history.html', files=files, user=current_user)