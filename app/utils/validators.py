import re
from email_validator import validate_email, EmailNotValidError

class Validator:
    USERNAME_MIN = 3
    USERNAME_MAX = 80
    PASSWORD_MIN = 8
    PASSWORD_MAX = 128

    @staticmethod
    def validate_username(username):
        if not username:
            return False, "Username is required"
        if len(username) < Validator.USERNAME_MIN:
            return False, f"Username must be at least {Validator.USERNAME_MIN} characters"
        if len(username) > Validator.USERNAME_MAX:
            return False, f"Username must be at most {Validator.USERNAME_MAX} characters"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"
        return True, None

    @staticmethod
    def validate_email(email):
        if not email:
            return False, "Email is required"
        try:
            validate_email(email)
            return True, None
        except EmailNotValidError as e:
            return False, str(e)

    @staticmethod
    def validate_password(password):
        if not password:
            return False, "Password is required"
        if len(password) < Validator.PASSWORD_MIN:
            return False, f"Password must be at least {Validator.PASSWORD_MIN} characters"
        if len(password) > Validator.PASSWORD_MAX:
            return False, f"Password must be at most {Validator.PASSWORD_MAX} characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        return True, None

    @staticmethod
    def validate_file_upload(filename, file_size, max_size):
        if not filename:
            return False, "No file selected"
        if file_size == 0:
            return False, "Empty file"
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb:.1f} MB"
        return True, None