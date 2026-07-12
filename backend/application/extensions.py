from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from celery import Celery
from flask_caching import Cache
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3


cache = Cache()
celery = Celery("trekking-app")
db = SQLAlchemy()
mail = Mail()
ph = PasswordHasher()
session = Session()

# Celery Configutation

def init_celery(app):
    celery.conf.update(app.extended_config.__dict__)

    class FlaskTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask

# CORS configuration
def cors_config(app):
    # Enable CORS for frontend server 5173 port
    CORS(app, 
        #  origins=["http://localhost:5173"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        resource={r"/*": {"origins": "http://localhost:5173"}},
         supports_credentials=True
         )
    

# Password hashing and verification functions
def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, password)
        return True
    except VerifyMismatchError:
        return False


# sqlite database configuration
@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.fetchone()
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

def init_extensions(app):
    # Initialize extensions with the Flask app
    cache.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    session.init_app(app)

    cors_config(app)  # Apply CORS configuration

__all__ = [
    # unitialized extensions
    'cache',
    'celery',
    'db',
    'mail',
    'ph',
    'session',

    # helper functions
    'cors_config',
    'init_celery',
    'hash_password',
    'verify_password',
    'init_extensions'
]