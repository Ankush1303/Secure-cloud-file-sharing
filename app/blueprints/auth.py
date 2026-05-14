from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService
from app.utils.validators import Validator

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        valid, error = Validator.validate_username(username)
        if not valid:
            flash(error, 'danger')
            return render_template('auth/signup.html')
        valid, error = Validator.validate_email(email)
        if not valid:
            flash(error, 'danger')
            return render_template('auth/signup.html')
        valid, error = Validator.validate_password(password)
        if not valid:
            flash(error, 'danger')
            return render_template('auth/signup.html')
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/signup.html')
        user, error = AuthService.register_user(username, email, password)
        if error:
            flash(error, 'danger')
            return render_template('auth/signup.html')
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        if not username_or_email or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('auth/login.html')
        user, error = AuthService.authenticate_user(username_or_email, password)
        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')
        login_user(user, remember=bool(remember))
        access_token = create_access_token(identity=user.id)
        response = make_response(redirect(url_for('main.dashboard')))
        set_access_cookies(response, access_token)
        flash(f'Welcome back, {user.username}!', 'success')
        return response
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    AuthService.log_activity(
        current_user.id, 'logout',
        details=f"User {current_user.username} logged out",
        ip_address=request.remote_addr
    )
    logout_user()
    response = make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(response)
    flash('You have been logged out.', 'info')
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    stats = AuthService.get_user_stats(current_user.id)
    return render_template('auth/profile.html', user=current_user, stats=stats)