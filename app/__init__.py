from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-prod' # Secure key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///health_system.db')
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Register Blueprints
    from .auth import auth as auth_blueprint
    from .main import main as main_blueprint
    # from .api import api as api_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    # app.register_blueprint(api_blueprint, url_prefix='/api')

    # Create Tables
    from .models import User, PatientRecord
    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
