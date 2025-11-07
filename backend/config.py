import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
    CLERK_PUBLISHABLE_KEY = os.environ.get('CLERK_PUBLISHABLE_KEY')

