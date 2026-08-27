from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Question, QuestionCategory, Document, DocumentCategory, ExamPaper
from app.utils import (
    generate_question_paper_pdf, generate_answer_key_pdf, generate_document_pdf,
    save_file, get_level_name, get_difficulty_name, get_document_type_name,
    format_date, format_file_size, truncate_text
)
from config import Config
import os
import random

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Home page with level selection."""
    return render_template('index.html')


@main.route('/<level>')
def level_home(level):
    """Level-specific home page (high_school or university)."""
    if level not in ['high_school', 'university']:
        flash('Invalid level selected', 'error')
        return redirect(url_for('main.index'))
    
    # Get categories for this level
    question_categories = QuestionCategory.query.filter_by(level=level).all()
    document_categories = DocumentCategory.query.filter_by(level=level).all()
    
    # Get recent documents
    recent_documents = Document.query.filter(
        Document.is_approved == True,
        DocumentCategory.level == level
    ).join(DocumentCategory).order_by(Document.created_at.desc()).limit(6).all()
    
    # Get recent exam papers
    recent_papers = ExamPaper.query.filter(
        ExamPaper.is_approved == True,
        ExamPaper.level == level
    ).order_by(ExamPaper.created_at.desc()).limit(6).all()
    
    return render_template('level_home.html',
                         level=level,
                         level_name=get_level_name(level),
                         question_categories=question_categories,
                         document_categories=document_categories,
                         recent_documents=recent_documents,
                         recent_papers=recent_papers,
                         get_document_type_name=get_document_type_name,
                         format_date=format_date)


# Question-related routes
@main.route('/<level>/questions')
def questions(level):
    """Browse questions by category."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    category_id = request.args.get('category', type=int)
    difficulty = request.args.get('difficulty')
    subject = request.args.get('subject')
    page = request.args.get('page', 1, type=int)
    
    query = Question.query.join(QuestionCategory).filter(
        QuestionCategory.level == level
    )
    
    if category_id:
        query = query.filter(Question.category_id == category_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if subject:
        query = query.filter(QuestionCategory.subject == subject)
    
    # Get categories for filtering
    categories = QuestionCategory.query.filter_by(level=level).all()
    subjects = db.session.query(QuestionCategory.subject).filter_by(level=level).distinct().all()
    subjects = [s[0] for s in subjects]
    
    questions = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=Config.QUESTIONS_PER_PAGE
    )
    
    return render_template('questions/browse.html',
                         level=level,
                         level_name=get_level_name(level),
                         questions=questions,
                         categories=categories,
                         subjects=subjects,
                         selected_category=category_id,
                         selected_difficulty=difficulty,
                         selected_subject=subject,
                         get_difficulty_name=get_difficulty_name,
                         format_date=format_date,
                         truncate_text=truncate_text)


@main.route('/<level>/questions/generate', methods=['GET', 'POST'])
def generate_question_paper(level):
    """Generate a custom question paper."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get parameters
        category_ids = request.form.getlist('categories')
        difficulty = request.form.get('difficulty')
        num_questions = request.form.get('num_questions', 10, type=int)
        include_answers = request.form.get('include_answers') == 'on'
        
        # Build query
        query = Question.query.join(QuestionCategory).filter(
            QuestionCategory.level == level
        )
        
        if category_ids:
            query = query.filter(Question.category_id.in_(category_ids))
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        
        all_questions = query.all()
        
        # Select random questions
        if len(all_questions) < num_questions:
            selected_questions = all_questions
        else:
            selected_questions = random.sample(all_questions, min(num_questions, len(all_questions)))
        
        if not selected_questions:
            flash('No questions found matching your criteria', 'error')
            return redirect(request.url)
        
        # Generate PDF
        title = request.form.get('title', f'{get_level_name(level)} Question Paper')
        subject = request.form.get('subject', 'General')
        
        pdf_content = generate_question_paper_pdf(
            selected_questions, 
            title=title, 
            level=level, 
            subject=subject
        )
        
        # Generate answer key if requested
        answer_key = None
        if include_answers:
            answer_key = generate_answer_key_pdf(selected_questions, title=f"{title} - Answer Key")
        
        # Save PDF temporarily for download
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        pdf_path = os.path.join(temp_dir, f'question_paper_{timestamp}.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        # Also save answer key if generated
        answer_key_path = None
        if answer_key:
            answer_key_path = os.path.join(temp_dir, f'answer_key_{timestamp}.pdf')
            with open(answer_key_path, 'wb') as f:
                f.write(answer_key)
        
        return render_template('questions/preview.html',
                             level=level,
                             level_name=get_level_name(level),
                             questions=selected_questions,
                             title=title,
                             subject=subject,
                             pdf_path=pdf_path,
                             answer_key_path=answer_key_path,
                             get_difficulty_name=get_difficulty_name)
    
    # GET request - show form
    categories = QuestionCategory.query.filter_by(level=level).all()
    subjects = db.session.query(QuestionCategory.subject).filter_by(level=level).distinct().all()
    subjects = [s[0] for s in subjects]
    
    return render_template('questions/generate.html',
                         level=level,
                         level_name=get_level_name(level),
                         categories=categories,
                         subjects=subjects)


@main.route('/<level>/questions/download/<path:filename>')
def download_question_paper(level, filename):
    """Download generated question paper."""
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    file_path = os.path.join(temp_dir, filename)
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.level_home', level=level))
    
    return send_file(file_path, as_attachment=True)


# Document-related routes
@main.route('/<level>/documents')
def documents(level):
    """Browse documents (essays and handouts)."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    category_id = request.args.get('category', type=int)
    doc_type = request.args.get('type')
    subject = request.args.get('subject')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    
    query = Document.query.join(DocumentCategory).filter(
        Document.is_approved == True,
        DocumentCategory.level == level
    )
    
    if category_id:
        query = query.filter(Document.category_id == category_id)
    if doc_type:
        query = query.filter(Document.file_type == doc_type)
    if subject:
        query = query.filter(DocumentCategory.subject == subject)
    if search:
        query = query.filter(Document.title.ilike(f'%{search}%'))
    
    # Get categories for filtering
    categories = DocumentCategory.query.filter_by(level=level).all()
    subjects = db.session.query(DocumentCategory.subject).filter_by(level=level).distinct().all()
    subjects = [s[0] for s in subjects]
    
    documents = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=Config.POSTS_PER_PAGE
    )
    
    return render_template('documents/browse.html',
                         level=level,
                         level_name=get_level_name(level),
                         documents=documents,
                         categories=categories,
                         subjects=subjects,
                         selected_category=category_id,
                         selected_type=doc_type,
                         selected_subject=subject,
                         search_query=search,
                         get_document_type_name=get_document_type_name,
                         format_date=format_date,
                         format_file_size=format_file_size,
                         truncate_text=truncate_text)


@main.route('/<level>/documents/<int:doc_id>')
def view_document(level, doc_id):
    """View a single document."""
    document = Document.query.get_or_404(doc_id)
    
    if not document.is_approved:
        flash('Document is not approved yet', 'error')
        return redirect(url_for('main.documents', level=level))
    
    # Increment view count
    document.view_count += 1
    db.session.commit()
    
    # Get related documents
    related_docs = Document.query.filter(
        Document.category_id == document.category_id,
        Document.id != doc_id,
        Document.is_approved == True
    ).order_by(Document.created_at.desc()).limit(4).all()
    
    return render_template('documents/view.html',
                         level=level,
                         level_name=get_level_name(level),
                         document=document,
                         related_docs=related_docs,
                         get_document_type_name=get_document_type_name,
                         format_date=format_date,
                         format_file_size=format_file_size)


@main.route('/<level>/documents/download/<int:doc_id>')
def download_document(level, doc_id):
    """Download a document."""
    document = Document.query.get_or_404(doc_id)
    
    if not document.is_approved:
        flash('Document is not approved yet', 'error')
        return redirect(url_for('main.documents', level=level))
    
    # Increment download count
    document.download_count += 1
    db.session.commit()
    
    file_path = document.file_path
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.documents', level=level))
    
    return send_file(file_path, as_attachment=True, download_name=document.file_name)


@main.route('/<level>/documents/preview/<int:doc_id>')
def preview_document(level, doc_id):
    """Preview a document as PDF."""
    document = Document.query.get_or_404(doc_id)
    
    if not document.is_approved:
        flash('Document is not approved yet', 'error')
        return redirect(url_for('main.documents', level=level))
    
    # Generate PDF from the document
    pdf_content = generate_document_pdf(document)
    
    # Save temporarily
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    pdf_path = os.path.join(temp_dir, f'doc_{doc_id}_{timestamp}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)
    
    return send_file(pdf_path, as_attachment=False)


# Exam paper routes
@main.route('/<level>/papers')
def exam_papers(level):
    """Browse exam papers."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    subject = request.args.get('subject')
    year = request.args.get('year')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    
    query = ExamPaper.query.filter(
        ExamPaper.is_approved == True,
        ExamPaper.level == level
    )
    
    if subject:
        query = query.filter(ExamPaper.subject == subject)
    if year:
        query = query.filter(ExamPaper.year == year)
    if search:
        query = query.filter(ExamPaper.title.ilike(f'%{search}%'))
    
    # Get subjects and years for filtering
    subjects = db.session.query(ExamPaper.subject).filter_by(level=level).distinct().all()
    subjects = [s[0] for s in subjects]
    years = db.session.query(ExamPaper.year).filter_by(level=level).distinct().all()
    years = [y[0] for y in years if y]
    
    papers = query.order_by(ExamPaper.created_at.desc()).paginate(
        page=page, per_page=Config.POSTS_PER_PAGE
    )
    
    return render_template('papers/browse.html',
                         level=level,
                         level_name=get_level_name(level),
                         papers=papers,
                         subjects=subjects,
                         years=years,
                         selected_subject=subject,
                         selected_year=year,
                         search_query=search,
                         format_date=format_date,
                         format_file_size=format_file_size,
                         truncate_text=truncate_text)


@main.route('/<level>/papers/download/<int:paper_id>')
def download_paper(level, paper_id):
    """Download an exam paper."""
    paper = ExamPaper.query.get_or_404(paper_id)
    
    if not paper.is_approved:
        flash('Paper is not approved yet', 'error')
        return redirect(url_for('main.exam_papers', level=level))
    
    # Increment download count
    paper.download_count += 1
    db.session.commit()
    
    file_path = paper.file_path
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.exam_papers', level=level))
    
    return send_file(file_path, as_attachment=True, download_name=paper.file_name)


@main.route('/<level>/papers/<int:paper_id>')
def view_paper(level, paper_id):
    """View exam paper details."""
    paper = ExamPaper.query.get_or_404(paper_id)
    
    if not paper.is_approved:
        flash('Paper is not approved yet', 'error')
        return redirect(url_for('main.exam_papers', level=level))
    
    # Get related papers
    related_papers = ExamPaper.query.filter(
        ExamPaper.subject == paper.subject,
        ExamPaper.level == paper.level,
        ExamPaper.id != paper_id,
        ExamPaper.is_approved == True
    ).order_by(ExamPaper.created_at.desc()).limit(4).all()
    
    return render_template('papers/view.html',
                         level=level,
                         level_name=get_level_name(level),
                         paper=paper,
                         related_papers=related_papers,
                         format_date=format_date,
                         format_file_size=format_file_size)
