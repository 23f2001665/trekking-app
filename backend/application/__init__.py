from .config import Config
from .extensions import *
from .models import UserRoleName, User
from flask import Flask, request, jsonify, g
from sqlalchemy import select
from .routes import *
import os


PRESERVE_CASE_JSON_FIELDS = {
    'password',
}


def normalize_json_value(field_name, value):
    if value is None:
        return ''

    if isinstance(value, str):
        value = value.strip()
        if field_name not in PRESERVE_CASE_JSON_FIELDS:
            value = value.lower()
        return value

    if isinstance(value, dict):
        return {
            nested_key: normalize_json_value(nested_key, nested_value)
            for nested_key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [normalize_json_value(field_name, item) for item in value]

    return value


def validate_json_body():
    if request.method not in ("POST", "PUT", "PATCH"):
        return
    
    excluded_enpoints = ["auth.logout"]

    # Skip requests that don't expect JSON (e.g., file uploads)
    if not request.is_json:
        if request.endpoint in excluded_enpoints:
            return
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400

    g.data = {
        key: normalize_json_value(key, value)
        for key, value in data.items()
    }
    
def create_database(app):
    """Create the database tables."""
    database_path = app.config.get('DATABASE_PATH', 'instance')
    instance_path = os.path.join(database_path, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    with app.app_context():
        db.create_all()

def routes_register(app):
    """Register the blueprints for the application."""
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(trek_bp, url_prefix='/treks')
    app.register_blueprint(booking_bp, url_prefix='/bookings')
    app.register_blueprint(summary_bp, url_prefix='/summary')

    app.before_request(validate_json_body)  # Register the JSON validation function

def create_admin_user(app):
    """Create an admin user if it doesn't exist."""
    with app.app_context():
        stmt = select(User).where(User.role == UserRoleName.ADMIN)
        admin_user = db.session.execute(stmt).scalars().first()
        if not admin_user:
            admin_user = User(
                email=app.config['ADMIN_EMAIL'],
                first_name=app.config['ADMIN_FIRST_NAME'],
                last_name=app.config['ADMIN_LAST_NAME'],
                role=UserRoleName.ADMIN
            )
            admin_user.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin_user)
            db.session.commit()
        
# app setup
def create_app():
    app = Flask(__name__)
    app.extended_config = Config  # Load configuration from config.py
    app.config.from_object(Config)  # Load configuration from config.py

    # extensions setup
    init_extensions(app)
    init_celery(app)

    create_database(app)
    routes_register(app)
    create_admin_user(app)
    return app
