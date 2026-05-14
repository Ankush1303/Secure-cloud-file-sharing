from flask import Flask
from config import config_by_name
from app.extensions import db, migrate, bcrypt, jwt, login_manager

def create_app(config_name='default'):
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        instance_relative_config=True
    )
    app.config.from_object(config_by_name[config_name])
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.files import files_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(files_bp, url_prefix='/files')

    with app.app_context():
        db.create_all()

    return app