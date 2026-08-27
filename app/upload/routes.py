from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Document, DocumentCategory, ExamPaper, Question, QuestionCategory
from app.utils import save_file, is_allowed_extension, get_file_extension
from app.upload.forms import DocumentUploadForm, ExamPaperUploadForm
import os

from app.upload import upload


@upload.route('/<level>/upload', methods=['GET', 'POST'])
@login_required
def upload_center(level):
    """Main upload center for a specific level."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    # Get user's upload statistics
    user_documents = Document.query.filter_by(user_id=current_user.id).count()
    user_papers = ExamPaper.query.filter_by(user_id=current_user.id).count()
    
    return render_template('upload/center.html',
                         level=level,
                         level_name=level.replace('_', ' ').title(),
                         user_documents=user_documents,
                         user_papers=user_papers)


@upload.route('/<level>/upload/document', methods=['GET', 'POST'])
@login_required
def upload_document(level):
    """Upload a document (essay or handout)."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    form = DocumentUploadForm()
    
    # Populate category choices
    categories = DocumentCategory.query.filter_by(level=level).all()
    form.category.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        # Handle file upload
        file = request.files.get('file')
        
        if not file or file.filename == '':
            flash('Please select a file to upload', 'error')
            return render_template('upload/document.html', form=form, level=level)
        
        # Check file extension
        if not is_allowed_extension(file.filename):
            flash('File type not allowed', 'error')
            return render_template('upload/document.html', form=form, level=level)
        
        # Save the file
        success, message, file_path, file_name = save_file(file)
        
        if not success:
            flash(message, 'error')
            return render_template('upload/document.html', form=form, level=level)
        
        # Create document record
        doc_type = form.document_type.data
        
        document = Document(
            title=form.title.data,
            description=form.description.data,
            file_path=file_path,
            file_name=file_name,
            file_type=doc_type,
            category_id=form.category.data,
            user_id=current_user.id,
            is_approved=False  # Needs admin approval
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Document uploaded successfully! It will be available after admin approval.', 'success')
        return redirect(url_for('upload.upload_center', level=level))
    
    return render_template('upload/document.html', form=form, level=level)


@upload.route('/<level>/upload/paper', methods=['GET', 'POST'])
@login_required
def upload_paper(level):
    """Upload an exam paper."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    form = ExamPaperUploadForm()
    
    if form.validate_on_submit():
        # Handle file upload
        file = request.files.get('file')
        
        if not file or file.filename == '':
            flash('Please select a file to upload', 'error')
            return render_template('upload/paper.html', form=form, level=level)
        
        # Check file extension
        if not is_allowed_extension(file.filename):
            flash('File type not allowed', 'error')
            return render_template('upload/paper.html', form=form, level=level)
        
        # Save the file
        success, message, file_path, file_name = save_file(file)
        
        if not success:
            flash(message, 'error')
            return render_template('upload/paper.html', form=form, level=level)
        
        # Create exam paper record
        paper = ExamPaper(
            title=form.title.data,
            description=form.description.data,
            file_path=file_path,
            file_name=file_name,
            level=level,
            subject=form.subject.data,
            year=form.year.data,
            user_id=current_user.id,
            is_approved=False  # Needs admin approval
        )
        
        db.session.add(paper)
        db.session.commit()
        
        flash('Exam paper uploaded successfully! It will be available after admin approval.', 'success')
        return redirect(url_for('upload.upload_center', level=level))
    
    return render_template('upload/paper.html', form=form, level=level)


@upload.route('/<level>/upload/question', methods=['GET', 'POST'])
@login_required
def upload_question(level):
    """Upload a question to the question bank."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        content = request.form.get('content')
        category_id = request.form.get('category')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_answer = request.form.get('correct_answer')
        explanation = request.form.get('explanation')
        marks = request.form.get('marks', 1, type=int)
        difficulty = request.form.get('difficulty', 'medium')
        
        # Validate required fields
        if not content or not category_id:
            flash('Content and category are required', 'error')
            
        # Check if it's a multiple choice question
        is_multiple_choice = bool(option_a and option_b)
        
        if is_multiple_choice and not correct_answer:
            flash('Please select the correct answer for multiple choice questions', 'error')
        
        # Get category
        category = QuestionCategory.query.get(category_id)
        if not category:
            flash('Invalid category', 'error')
        
        # Create question
        question = Question(
            content=content,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            explanation=explanation,
            marks=marks,
            difficulty=difficulty,
            category_id=category_id,
            user_id=current_user.id
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Question added to the bank successfully!', 'success')
        return redirect(url_for('upload.upload_center', level=level))
    
    # GET request - show form
    categories = QuestionCategory.query.filter_by(level=level).all()
    
    return render_template('upload/question.html', 
                         level=level,
                         categories=categories)


@upload.route('/<level>/my-uploads')
@login_required
def my_uploads(level):
    """View user's own uploads."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    # Get user's documents
    documents = Document.query.filter_by(user_id=current_user.id).order_by(
        Document.created_at.desc()
    ).all()
    
    # Get user's exam papers
    papers = ExamPaper.query.filter_by(user_id=current_user.id).order_by(
        ExamPaper.created_at.desc()
    ).all()
    
    # Get user's questions
    questions = Question.query.filter_by(user_id=current_user.id).order_by(
        Question.created_at.desc()
    ).all()
    
    return render_template('upload/my_uploads.html',
                         level=level,
                         documents=documents,
                         papers=papers,
                         questions=questions)
