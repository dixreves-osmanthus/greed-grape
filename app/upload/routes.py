from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Document, DocumentCategory, ExamPaper, Question, QuestionCategory, ExtractedExamPaper, ExtractedQuestion, QuestionImage
from app.utils import save_file, is_allowed_extension, get_file_extension
from app.upload.forms import DocumentUploadForm, ExamPaperUploadForm
from app.services.paper_processor import PaperProcessor
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
            is_approved=False
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
            is_approved=False
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


@upload.route('/<level>/paper/<int:paper_id>/process', methods=['GET'])
@login_required
def process_paper(level, paper_id):
    """Process an uploaded exam paper to extract questions and images."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    # Get the exam paper
    paper = ExamPaper.query.get(paper_id)
    if not paper:
        flash('Exam paper not found', 'error')
        return redirect(url_for('upload.my_uploads', level=level))
    
    # Check if user owns the paper
    if paper.user_id != current_user.id:
        flash('You do not have permission to process this paper', 'error')
        return redirect(url_for('upload.my_uploads', level=level))
    
    # Check if already processed
    if paper.extracted_version:
        return redirect(url_for('upload.view_processed_paper', 
                               level=level, 
                               paper_id=paper_id))
    
    return render_template('upload/process_paper.html',
                         level=level,
                         paper=paper)


@upload.route('/<level>/paper/<int:paper_id>/start-processing', methods=['POST'])
@login_required
def start_processing(level, paper_id):
    """Start processing an exam paper in the background."""
    if level not in ['high_school', 'university']:
        return jsonify({'success': False, 'error': 'Invalid level'})
    
    # Get the exam paper
    paper = ExamPaper.query.get(paper_id)
    if not paper:
        return jsonify({'success': False, 'error': 'Exam paper not found'})
    
    # Check if user owns the paper
    if paper.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    # Check if already processed
    if paper.extracted_version:
        return jsonify({'success': False, 'error': 'Already processed'})
    
    try:
        # Initialize processor with Mistral API key
        processor = PaperProcessor(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config.get('MISTRAL_API_KEY')
        )
        
        # Process the paper (this will create the extracted paper record)
        success, result = processor.process_paper(paper_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'extracted_paper_id': result.id,
                'redirect_url': url_for('upload.view_processed_paper', 
                                       level=level, 
                                       paper_id=paper_id)
            })
        else:
            return jsonify({'success': False, 'error': str(result)})
            
    except Exception as e:
        current_app.logger.error(f"Error processing paper: {e}")
        return jsonify({'success': False, 'error': str(e)})


@upload.route('/<level>/paper/<int:paper_id>/processed', methods=['GET'])
@login_required
def view_processed_paper(level, paper_id):
    """View the processed exam paper with extracted questions."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    # Get the exam paper
    paper = ExamPaper.query.get(paper_id)
    if not paper:
        flash('Exam paper not found', 'error')
        return redirect(url_for('upload.my_uploads', level=level))
    
    # Check if user owns the paper
    if paper.user_id != current_user.id:
        flash('You do not have permission to view this paper', 'error')
        return redirect(url_for('upload.my_uploads', level=level))
    
    # Get extracted version
    extracted_paper = paper.extracted_version
    if not extracted_paper:
        return redirect(url_for('upload.process_paper', level=level, paper_id=paper_id))
    
    # Get extracted questions
    questions = ExtractedQuestion.query.filter_by(
        extracted_paper_id=extracted_paper.id
    ).order_by(ExtractedQuestion.question_number).all()
    
    # Get images for each question
    questions_with_images = []
    for q in questions:
        images = QuestionImage.query.filter_by(
            extracted_question_id=q.id
        ).order_by(QuestionImage.position).all()
        questions_with_images.append({
            'question': q,
            'images': images
        })
    
    # Get categories for the add to database feature
    categories = QuestionCategory.query.filter_by(level=level).all()
    
    return render_template('upload/processed_paper.html',
                         level=level,
                         paper=paper,
                         extracted_paper=extracted_paper,
                         questions_with_images=questions_with_images,
                         categories=categories)


@upload.route('/<level>/processed/<int:extracted_paper_id>/download-pdf', methods=['GET'])
@login_required
def download_processed_pdf(level, extracted_paper_id):
    """Download the processed PDF."""
    if level not in ['high_school', 'university']:
        flash('Invalid level', 'error')
        return redirect(url_for('main.index'))
    
    # Get extracted paper
    extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
    if not extracted_paper:
        flash('Processed paper not found', 'error')
        return redirect(url_for('upload.my_uploads', level=level))
    
    # Check if user owns the extracted paper
    if extracted_paper.user_id != current_user.id:
        flash('You do not have permission to download this file', 'error')
        return redirect(url_for('upload.my_uploads', level=level))
    
    if not extracted_paper.processed_pdf_path:
        flash('PDF not generated yet', 'error')
        return redirect(url_for('upload.view_processed_paper', 
                               level=level, 
                               paper_id=extracted_paper.exam_paper_id))
    
    # Send the file
    try:
        return send_from_directory(
            os.path.dirname(extracted_paper.processed_pdf_path),
            os.path.basename(extracted_paper.processed_pdf_path),
            as_attachment=True
        )
    except Exception as e:
        current_app.logger.error(f"Error sending PDF: {e}")
        flash('Error sending PDF file', 'error')
        return redirect(url_for('upload.view_processed_paper', 
                               level=level, 
                               paper_id=extracted_paper.exam_paper_id))


@upload.route('/<level>/processed/<int:extracted_paper_id>/regenerate-pdf', methods=['POST'])
@login_required
def regenerate_pdf(level, extracted_paper_id):
    """Regenerate PDF from updated LaTeX content."""
    if level not in ['high_school', 'university']:
        return jsonify({'success': False, 'error': 'Invalid level'})
    
    # Get extracted paper
    extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
    if not extracted_paper:
        return jsonify({'success': False, 'error': 'Processed paper not found'})
    
    # Check if user owns the extracted paper
    if extracted_paper.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    try:
        # Initialize processor with Mistral API key
        processor = PaperProcessor(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config.get('MISTRAL_API_KEY')
        )
        
        # Regenerate PDF
        success = processor.regenerate_pdf(extracted_paper_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'PDF regenerated successfully',
                'pdf_url': url_for('upload.download_processed_pdf',
                                   level=level,
                                   extracted_paper_id=extracted_paper_id)
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to regenerate PDF'})
            
    except Exception as e:
        current_app.logger.error(f"Error regenerating PDF: {e}")
        return jsonify({'success': False, 'error': str(e)})


@upload.route('/<level>/processed/<int:extracted_paper_id>/question/<int:question_id>/update', methods=['POST'])
@login_required
def update_question_latex(level, extracted_paper_id, question_id):
    """Update LaTeX content for a specific question."""
    if level not in ['high_school', 'university']:
        return jsonify({'success': False, 'error': 'Invalid level'})
    
    # Get extracted paper
    extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
    if not extracted_paper:
        return jsonify({'success': False, 'error': 'Processed paper not found'})
    
    # Check if user owns the extracted paper
    if extracted_paper.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    # Get question
    question = ExtractedQuestion.query.get(question_id)
    if not question or question.extracted_paper_id != extracted_paper_id:
        return jsonify({'success': False, 'error': 'Question not found'})
    
    # Get new LaTeX content
    latex_content = request.form.get('latex_content')
    if not latex_content:
        return jsonify({'success': False, 'error': 'No LaTeX content provided'})
    
    try:
        # Update question
        processor = PaperProcessor(current_app.config['UPLOAD_FOLDER'])
        success = processor.update_question_latex(question_id, latex_content)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Question LaTeX updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update question'})
            
    except Exception as e:
        current_app.logger.error(f"Error updating question: {e}")
        return jsonify({'success': False, 'error': str(e)})


@upload.route('/<level>/processed/<int:extracted_paper_id>/progress', methods=['GET'])
@login_required
def get_processing_progress(level, extracted_paper_id):
    """Get the current processing progress for a paper."""
    if level not in ['high_school', 'university']:
        return jsonify({'success': False, 'error': 'Invalid level'})
    
    # Get extracted paper
    extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
    if not extracted_paper:
        return jsonify({'success': False, 'error': 'Processed paper not found'})
    
    # Check if user owns the extracted paper
    if extracted_paper.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    return jsonify({
        'success': True,
        'status': extracted_paper.status,
        'progress': extracted_paper.progress,
        'total_questions': extracted_paper.total_questions,
        'questions_with_images': extracted_paper.questions_with_images,
        'completed_at': extracted_paper.completed_at.isoformat() if extracted_paper.completed_at else None
    })


@upload.route('/<level>/processed/<int:extracted_paper_id>/add-question', methods=['POST'])
@login_required
def add_question_to_bank(level, extracted_paper_id):
    """Add a single extracted question to the question bank."""
    if level not in ['high_school', 'university']:
        return jsonify({'success': False, 'error': 'Invalid level'})
    
    # Get extracted paper
    extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
    if not extracted_paper:
        return jsonify({'success': False, 'error': 'Processed paper not found'})
    
    # Check if user owns the extracted paper
    if extracted_paper.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    # Get form data
    extracted_question_id = request.form.get('extracted_question_id')
    category_id = request.form.get('category_id')
    difficulty = request.form.get('difficulty', 'medium')
    marks = request.form.get('marks', 1, type=int)
    explanation = request.form.get('explanation', '')
    correct_answer = request.form.get('correct_answer', '')
    latex_content = request.form.get('latex_content', '')
    
    # Validate required fields
    if not extracted_question_id or not category_id:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    try:
        # Get the extracted question
        extracted_question = ExtractedQuestion.query.get(extracted_question_id)
        if not extracted_question:
            return jsonify({'success': False, 'error': 'Question not found'})
        
        # Get the category
        category = QuestionCategory.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'Category not found'})
        
        # Create new question in the question bank
        question = Question(
            content=extracted_question.content,
            content_latex=latex_content or extracted_question.content_latex or extracted_question.content,
            option_a=extracted_question.option_a or '',
            option_b=extracted_question.option_b or '',
            option_c=extracted_question.option_c or '',
            option_d=extracted_question.option_d or '',
            correct_answer=correct_answer,
            explanation=explanation,
            marks=marks,
            difficulty=difficulty,
            category_id=category_id,
            user_id=current_user.id
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Mark extracted question as reviewed
        extracted_question.needs_review = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question added to database successfully',
            'question_id': question.id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding question to bank: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@upload.route('/<level>/processed/<int:extracted_paper_id>/add-all-questions', methods=['POST'])
@login_required
def add_all_questions_to_bank(level, extracted_paper_id):
    """Add all extracted questions to the question bank."""
    if level not in ['high_school', 'university']:
        return jsonify({'success': False, 'error': 'Invalid level'})
    
    # Get extracted paper
    extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
    if not extracted_paper:
        return jsonify({'success': False, 'error': 'Processed paper not found'})
    
    # Check if user owns the extracted paper
    if extracted_paper.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    # Get all extracted questions
    extracted_questions = ExtractedQuestion.query.filter_by(
        extracted_paper_id=extracted_paper_id
    ).all()
    
    if not extracted_questions:
        return jsonify({'success': False, 'error': 'No questions found'})
    
    # Get auto-approve flag
    auto_approve = request.form.get('auto_approve', 'false').lower() == 'true'
    
    try:
        added_count = 0
        
        for eq in extracted_questions:
            # Find the first category for this level
            category = QuestionCategory.query.filter_by(
                level=level,
                subject=extracted_paper.original_paper.subject
            ).first()
            
            # If no category found, use the first available
            if not category:
                category = QuestionCategory.query.filter_by(level=level).first()
            
            if not category:
                continue
            
            # Create new question
            question = Question(
                content=eq.content,
                content_latex=eq.content_latex or eq.content,
                option_a=eq.option_a or '',
                option_b=eq.option_b or '',
                option_c=eq.option_c or '',
                option_d=eq.option_d or '',
                correct_answer=eq.correct_answer or '',
                explanation=eq.explanation or '',
                marks=eq.marks or 1,
                difficulty='medium',
                category_id=category.id,
                user_id=current_user.id
            )
            
            db.session.add(question)
            
            # Mark as reviewed
            eq.needs_review = False
            added_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{added_count} questions added to database',
            'added_count': added_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding all questions to bank: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
