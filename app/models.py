from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rsa_public_key = db.Column(db.Text, nullable=False)
    rsa_private_key_encrypted = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    files = db.relationship('File', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    shared_with_me = db.relationship('SharedFile', foreign_keys='SharedFile.shared_with_user_id', backref='recipient', lazy='dynamic')
    activities = db.relationship('ActivityLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    s3_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(100))
    encrypted_key = db.Column(db.Text, nullable=False)
    encryption_type = db.Column(db.String(50), default='fernet')
    nonce = db.Column(db.String(255))
    is_deleted = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    shares = db.relationship('SharedFile', backref='file', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<File {self.original_filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'size': self.file_size,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M') if self.uploaded_at else None,
            'encryption': self.encryption_type
        }

class SharedFile(db.Model):
    __tablename__ = 'shared_files'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permissions = db.Column(db.String(20), default='read')
    encrypted_key = db.Column(db.Text, nullable=True)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SharedFile {self.file_id} -> {self.shared_with_user_id}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action} by User {self.user_id}>'