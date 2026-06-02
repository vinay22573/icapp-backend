import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SESSION_DURATION = int(os.getenv('SESSION_DURATION', 3600))  # 1 hour
    SESSIONS = {}  # In-memory session store

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Export the active config
config = DevelopmentConfig  # or ProductionConfig for production