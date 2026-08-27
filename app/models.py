from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    questions = db.relationship('Question', backref='author', lazy=True)
    documents = db.relationship('Document', backref='uploader', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class QuestionCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20), nullable=False)  # 'high_school' or 'university'
    subject = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuestionCategory {self.name}>'


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_d = db.Column(db.Text)
    correct_answer = db.Column(db.String(10))  # 'a', 'b', 'c', or 'd'
    explanation = db.Column(db.Text)
    marks = db.Column(db.Integer, default=1)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    
    category_id = db.Column(db.Integer, db.ForeignKey('question_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Question {self.id}>'


class DocumentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20), nullable=False)  # 'high_school' or 'university'
    subject = db.Column(db.String(100), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'essay' or 'handout'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    documents = db.relationship('Document', backref='doc_category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DocumentCategory {self.name}>'


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'essay' or 'handout'
    
    category_id = db.Column(db.Integer, db.ForeignKey('document_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.title}>'


class ExamPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    
    level = db.Column(db.String(20), nullable=False)  # 'high_school' or 'university'
    subject = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(50))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    download_count = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExamPaper {self.title}>'
