import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'
    
    # Mistral API configuration
    MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY') or 'zb87mB47OJCVnZqSYASDu17vQp2zskH9'
    MISTRAL_API_URL = os.environ.get('MISTRAL_API_URL') or 'https://api.mistral.ai/v1'
    
    # Upload configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'app/static/uploads'
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg').split(','))
    
    # Pagination
    POSTS_PER_PAGE = 10
    QUESTIONS_PER_PAGE = 20
