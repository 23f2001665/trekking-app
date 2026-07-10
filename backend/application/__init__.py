from .config import Config
from .extensions import *
from flask import Flask
from .tasks import add

def create_database(app):
    """Create the database tables."""
    with app.app_context():
        db.create_all()
        
# app setup
def create_app():
    app = Flask(__name__)
    app.extended_config = Config  # Load configuration from config.py
    app.config.from_object(Config)  # Load configuration from config.py

    # extensions setup
    init_extensions(app)
    init_celery(app)

    create_database(app)

    return app
