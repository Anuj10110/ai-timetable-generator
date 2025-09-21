"""
Configuration settings for the AI Timetable Generator application.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///timetable.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Session Configuration
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    
    # Security Headers
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    
    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Enhanced Timetable Settings
    DEFAULT_MAX_GENERATION_TIME = 300  # seconds
    DEFAULT_FREE_PERIODS = [
        ("11:00", "12:00"),  # Late morning break
        ("13:00", "14:00"),  # Lunch break
        ("15:00", "16:00"),  # Afternoon break
    ]
    
    # Faculty Settings
    DEFAULT_MAX_CLASSES_PER_DAY = 6
    DEFAULT_MAX_HOURS_PER_WEEK = 20
    
    # Classroom Settings
    DEFAULT_CAPACITY_BUFFER = 0.1  # 10% capacity buffer
    
    # Time Slot Settings
    DEFAULT_TIME_SLOTS = [
        ("09:00", "10:30", 90),
        ("10:30", "12:00", 90),
        ("12:00", "13:30", 90),
        ("13:30", "15:00", 90),
        ("15:00", "16:30", 90),
        ("16:30", "18:00", 90)
    ]

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DEVELOPMENT = False
    
    # Production Security Settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Additional security headers
    FORCE_HTTPS = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}