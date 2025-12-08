import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Handle Heroku's postgres:// URL format (SQLAlchemy 2.0+ requires postgresql://)
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
    CLERK_PUBLISHABLE_KEY = os.environ.get('CLERK_PUBLISHABLE_KEY')
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

