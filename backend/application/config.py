import redis
from dotenv import load_dotenv
import os
from .schedules import beat_schedule

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))

def get_redis_client(db_number=0):
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=db_number, decode_responses=True)

class Config:
    # Flask configuration variables
    DEBUG = True

    # SQLAlchemy configuration variables
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///vma.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

   

    # Cache configuration variables
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'  # Redis
    CACHE_DEFAULT_TIMEOUT = 300  # Default cache timeout in seconds

    # Celery configuration variables
    broker_url=f'redis://{REDIS_HOST}:{REDIS_PORT}/2'
    result_backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/2'
    result_expires=120  # Result expiration time in seconds
    timezone="Asia/Kolkata"
    enable_utc=False
    CELERY_RESULT_EXPIRES = 60

    # Scheduler configuration variables
    beat_schedule = beat_schedule

    # Mail configuration variables
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_DEBUG = True  # Enable debug mode for Flask-Mail

    # Session configuration variables
    SECRET_KEY = 'something_secret'
    SESSION_USE_SIGNER = True  # Sign the session cookie to prevent tampering
    SESSION_COOKIE_NAME = 'trek_session'
    SESSION_KEY_PREFIX = 'flask_app:'  # Prefix for session keys in Redis

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # For https
    SESSION_COOKIE_SAMESITE = 'Lax'  # Can be 'Strict', 'Lax', or 'None'
    SESSION_PERMANENT = True # Stores session data in the database instead of cookies

    SESSION_TYPE = 'redis'  # Use Redis for session storage
    SESSION_REDIS = get_redis_client(db_number=0)  # Redis client for Flask-Session
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session expiration on each request
    PERMANENT_SESSION_LIFETIME = 60  # Session lifetime in seconds 

    # Random key to test extended configuration
    himanshu=1


