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
    exam_papers = db.relationship('ExamPaper', backref='paper_uploader', lazy=True)
    extracted_papers = db.relationship('ExtractedExamPaper', backref='extractor', lazy=True)
    
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
    
    # Relationship to extracted version
    extracted_version = db.relationship('ExtractedExamPaper', backref='original_paper', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<ExamPaper {self.title}>'


# New models for exam paper processing
class ExtractedExamPaper(db.Model):
    """Stores the extracted and processed version of an exam paper."""
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference to original paper
    exam_paper_id = db.Column(db.Integer, db.ForeignKey('exam_paper.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Processing status
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    
    # LaTeX content
    latex_content = db.Column(db.Text)
    
    # Generated PDF
    processed_pdf_path = db.Column(db.String(500))
    processed_pdf_name = db.Column(db.String(200))
    
    # Metadata
    total_questions = db.Column(db.Integer, default=0)
    questions_with_images = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Extracted questions
    extracted_questions = db.relationship('ExtractedQuestion', backref='extracted_paper', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ExtractedExamPaper {self.id} - {self.status}>'


class ExtractedQuestion(db.Model):
    """Stores individual questions extracted from an exam paper."""
    id = db.Column(db.Integer, primary_key=True)
    
    extracted_paper_id = db.Column(db.Integer, db.ForeignKey('extracted_exam_paper.id'), nullable=False)
    
    # Question data
    question_number = db.Column(db.Integer)
    content = db.Column(db.Text, nullable=False)
    content_latex = db.Column(db.Text)
    
    # Options for multiple choice
    option_a = db.Column(db.Text)
    option_a_latex = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_b_latex = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_c_latex = db.Column(db.Text)
    option_d = db.Column(db.Text)
    option_d_latex = db.Column(db.Text)
    
    # Marks
    marks = db.Column(db.Float)
    
    # Images associated with this question
    question_images = db.relationship('QuestionImage', backref='question', lazy=True, cascade='all, delete-orphan')
    
    # Processing metadata
    confidence_score = db.Column(db.Float)  # 0-1
    needs_review = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExtractedQuestion {self.id} - Q{self.question_number}>'


class QuestionImage(db.Model):
    """Stores images extracted from exam paper questions."""
    id = db.Column(db.Integer, primary_key=True)
    
    extracted_question_id = db.Column(db.Integer, db.ForeignKey('extracted_question.id'), nullable=False)
    
    # Image file info
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    original_file_name = db.Column(db.String(200))
    
    # Image metadata
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    
    # Position in question (for ordering)
    position = db.Column(db.Integer, default=0)
    
    # Description/alt text
    description = db.Column(db.String(500))
    
    # LaTeX reference (if included in LaTeX)
    latex_reference = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuestionImage {self.id} - {self.file_name}>'
