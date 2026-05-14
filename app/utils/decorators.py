from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_login import current_user
from app.models import User

def jwt_or_login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            jwt_user_id = get_jwt_identity()
            user = User.query.get(jwt_user_id)
            if user:
                request.current_user = user
                return fn(*args, **kwargs)
        except Exception:
            pass
        if current_user.is_authenticated:
            request.current_user = current_user
            return fn(*args, **kwargs)
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return wrapper