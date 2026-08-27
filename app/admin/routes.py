from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import (
    User, Question, QuestionCategory, Document, DocumentCategory, ExamPaper
)
from app.utils import save_file, delete_file, get_level_name, get_difficulty_name, format_date
from app.admin.forms import (
    CategoryForm, DocumentCategoryForm, QuestionForm, 
    UserForm, ApprovalForm
)
import os

from app.admin import admin


@admin.route('/')
@login_required
def dashboard():
    """Admin dashboard."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    # Statistics
    total_users = User.query.count()
    total_questions = Question.query.count()
    total_documents = Document.query.count()
    total_papers = ExamPaper.query.count()
    
    # Pending approvals
    pending_documents = Document.query.filter_by(is_approved=False).count()
    pending_papers = ExamPaper.query.filter_by(is_approved=False).count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_questions = Question.query.order_by(Question.created_at.desc()).limit(5).all()
    recent_documents = Document.query.order_by(Document.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_questions=total_questions,
                         total_documents=total_documents,
                         total_papers=total_papers,
                         pending_documents=pending_documents,
                         pending_papers=pending_papers,
                         recent_users=recent_users,
                         recent_questions=recent_questions,
                         recent_documents=recent_documents,
                         format_date=format_date)


# User management
@admin.route('/users')
@login_required
def manage_users():
    """Manage users."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=10
    )
    
    return render_template('admin/users.html', users=users, format_date=format_date)


@admin.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Add a new user."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('admin/add_user.html', form=form)
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('Username already taken', 'error')
            return render_template('admin/add_user.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('User added successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/add_user.html', form=form)


@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit a user."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Cannot delete current user
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Delete user's uploads
    documents = Document.query.filter_by(user_id=user.id).all()
    for doc in documents:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        db.session.delete(doc)
    
    papers = ExamPaper.query.filter_by(user_id=user.id).all()
    for paper in papers:
        if os.path.exists(paper.file_path):
            os.remove(paper.file_path)
        db.session.delete(paper)
    
    questions = Question.query.filter_by(user_id=user.id).all()
    for question in questions:
        db.session.delete(question)
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))


# Category management
@admin.route('/categories/questions')
@login_required
def manage_question_categories():
    """Manage question categories."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    categories = QuestionCategory.query.order_by(QuestionCategory.name).all()
    
    return render_template('admin/question_categories.html', categories=categories)


@admin.route('/categories/questions/add', methods=['GET', 'POST'])
@login_required
def add_question_category():
    """Add a new question category."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = QuestionCategory(
            name=form.name.data,
            description=form.description.data,
            level=form.level.data,
            subject=form.subject.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Question category added successfully!', 'success')
        return redirect(url_for('admin.manage_question_categories'))
    
    return render_template('admin/add_question_category.html', form=form)


@admin.route('/categories/questions/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question_category(category_id):
    """Edit a question category."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    category = QuestionCategory.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.level = form.level.data
        category.subject = form.subject.data
        
        db.session.commit()
        
        flash('Question category updated successfully!', 'success')
        return redirect(url_for('admin.manage_question_categories'))
    
    return render_template('admin/edit_question_category.html', form=form, category=category)


@admin.route('/categories/questions/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_question_category(category_id):
    """Delete a question category."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    category = QuestionCategory.query.get_or_404(category_id)
    
    # Delete all questions in this category
    questions = Question.query.filter_by(category_id=category.id).all()
    for question in questions:
        db.session.delete(question)
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Question category deleted successfully!', 'success')
    return redirect(url_for('admin.manage_question_categories'))


# Document category management
@admin.route('/categories/documents')
@login_required
def manage_document_categories():
    """Manage document categories."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    categories = DocumentCategory.query.order_by(DocumentCategory.name).all()
    
    return render_template('admin/document_categories.html', categories=categories)


@admin.route('/categories/documents/add', methods=['GET', 'POST'])
@login_required
def add_document_category():
    """Add a new document category."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    form = DocumentCategoryForm()
    
    if form.validate_on_submit():
        category = DocumentCategory(
            name=form.name.data,
            description=form.description.data,
            level=form.level.data,
            subject=form.subject.data,
            document_type=form.document_type.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Document category added successfully!', 'success')
        return redirect(url_for('admin.manage_document_categories'))
    
    return render_template('admin/add_document_category.html', form=form)


@admin.route('/categories/documents/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document_category(category_id):
    """Edit a document category."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    category = DocumentCategory.query.get_or_404(category_id)
    form = DocumentCategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.level = form.level.data
        category.subject = form.subject.data
        category.document_type = form.document_type.data
        
        db.session.commit()
        
        flash('Document category updated successfully!', 'success')
        return redirect(url_for('admin.manage_document_categories'))
    
    return render_template('admin/edit_document_category.html', form=form, category=category)


@admin.route('/categories/documents/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_document_category(category_id):
    """Delete a document category."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    category = DocumentCategory.query.get_or_404(category_id)
    
    # Delete all documents in this category
    documents = Document.query.filter_by(category_id=category.id).all()
    for doc in documents:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        db.session.delete(doc)
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Document category deleted successfully!', 'success')
    return redirect(url_for('admin.manage_document_categories'))


# Question management
@admin.route('/questions')
@login_required
def manage_questions():
    """Manage questions."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = Question.query.order_by(Question.created_at.desc())
    
    if category_id:
        query = query.filter(Question.category_id == category_id)
    
    questions = query.paginate(page=page, per_page=20)
    categories = QuestionCategory.query.all()
    
    return render_template('admin/questions.html', 
                         questions=questions,
                         categories=categories,
                         selected_category=category_id,
                         get_difficulty_name=get_difficulty_name,
                         format_date=format_date)


@admin.route('/questions/add', methods=['GET', 'POST'])
@login_required
def add_question():
    """Add a new question."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    form = QuestionForm()
    form.category.choices = [(c.id, c.name) for c in QuestionCategory.query.all()]
    
    if form.validate_on_submit():
        question = Question(
            content=form.content.data,
            option_a=form.option_a.data,
            option_b=form.option_b.data,
            option_c=form.option_c.data,
            option_d=form.option_d.data,
            correct_answer=form.correct_answer.data,
            explanation=form.explanation.data,
            marks=form.marks.data,
            difficulty=form.difficulty.data,
            category_id=form.category.data,
            user_id=current_user.id
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.manage_questions'))
    
    return render_template('admin/add_question.html', form=form)


@admin.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit a question."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question)
    form.category.choices = [(c.id, c.name) for c in QuestionCategory.query.all()]
    
    if form.validate_on_submit():
        question.content = form.content.data
        question.option_a = form.option_a.data
        question.option_b = form.option_b.data
        question.option_c = form.option_c.data
        question.option_d = form.option_d.data
        question.correct_answer = form.correct_answer.data
        question.explanation = form.explanation.data
        question.marks = form.marks.data
        question.difficulty = form.difficulty.data
        question.category_id = form.category.data
        
        db.session.commit()
        
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin.manage_questions'))
    
    return render_template('admin/edit_question.html', form=form, question=question)


@admin.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.manage_questions'))


# Document management
@admin.route('/documents/pending')
@login_required
def pending_documents():
    """View pending documents for approval."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    documents = Document.query.filter_by(is_approved=False).order_by(
        Document.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('admin/pending_documents.html', 
                         documents=documents,
                         format_date=format_date)


@admin.route('/documents/<int:doc_id>/approve', methods=['POST'])
@login_required
def approve_document(doc_id):
    """Approve a document."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    document = Document.query.get_or_404(doc_id)
    document.is_approved = True
    db.session.commit()
    
    flash('Document approved successfully!', 'success')
    return redirect(url_for('admin.pending_documents'))


@admin.route('/documents/<int:doc_id>/reject', methods=['POST'])
@login_required
def reject_document(doc_id):
    """Reject a document."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    document = Document.query.get_or_404(doc_id)
    
    # Delete the file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    db.session.delete(document)
    db.session.commit()
    
    flash('Document rejected and deleted', 'success')
    return redirect(url_for('admin.pending_documents'))


@admin.route('/papers/pending')
@login_required
def pending_papers():
    """View pending exam papers for approval."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    papers = ExamPaper.query.filter_by(is_approved=False).order_by(
        ExamPaper.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('admin/pending_papers.html', papers=papers, format_date=format_date)


@admin.route('/papers/<int:paper_id>/approve', methods=['POST'])
@login_required
def approve_paper(paper_id):
    """Approve an exam paper."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    paper = ExamPaper.query.get_or_404(paper_id)
    paper.is_approved = True
    db.session.commit()
    
    flash('Exam paper approved successfully!', 'success')
    return redirect(url_for('admin.pending_papers'))


@admin.route('/papers/<int:paper_id>/reject', methods=['POST'])
@login_required
def reject_paper(paper_id):
    """Reject an exam paper."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    paper = ExamPaper.query.get_or_404(paper_id)
    
    # Delete the file
    if os.path.exists(paper.file_path):
        os.remove(paper.file_path)
    
    db.session.delete(paper)
    db.session.commit()
    
    flash('Exam paper rejected and deleted', 'success')
    return redirect(url_for('admin.pending_papers'))


# Bulk operations
@admin.route('/documents/bulk-approve', methods=['POST'])
@login_required
def bulk_approve_documents():
    """Bulk approve documents."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    doc_ids = request.form.getlist('doc_ids')
    
    for doc_id in doc_ids:
        document = Document.query.get(doc_id)
        if document:
            document.is_approved = True
    
    db.session.commit()
    
    flash(f'{len(doc_ids)} documents approved successfully!', 'success')
    return redirect(url_for('admin.pending_documents'))


@admin.route('/papers/bulk-approve', methods=['POST'])
@login_required
def bulk_approve_papers():
    """Bulk approve exam papers."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.index'))
    
    paper_ids = request.form.getlist('paper_ids')
    
    for paper_id in paper_ids:
        paper = ExamPaper.query.get(paper_id)
        if paper:
            paper.is_approved = True
    
    db.session.commit()
    
    flash(f'{len(paper_ids)} exam papers approved successfully!', 'success')
    return redirect(url_for('admin.pending_papers'))
