from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Question, QuestionCategory, Document, DocumentCategory, ExamPaper
from app.utils import generate_question_paper_pdf, generate_document_pdf
import os
import random

from app.api import api


@api.route('/questions/<level>')
def get_questions(level):
    """Get questions for a specific level."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    category_id = request.args.get('category', type=int)
    difficulty = request.args.get('difficulty')
    limit = request.args.get('limit', 20, type=int)
    
    query = Question.query.join(QuestionCategory).filter(
        QuestionCategory.level == level
    )
    
    if category_id:
        query = query.filter(Question.category_id == category_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    questions = query.limit(limit).all()
    
    return jsonify([{
        'id': q.id,
        'content': q.content,
        'options': {
            'a': q.option_a,
            'b': q.option_b,
            'c': q.option_c,
            'd': q.option_d
        },
        'correct_answer': q.correct_answer,
        'explanation': q.explanation,
        'marks': q.marks,
        'difficulty': q.difficulty,
        'category': q.category.name,
        'subject': q.category.subject
    } for q in questions])


@api.route('/questions/random/<level>')
def get_random_questions(level):
    """Get random questions for a specific level."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    num_questions = request.args.get('num', 10, type=int)
    category_id = request.args.get('category', type=int)
    difficulty = request.args.get('difficulty')
    
    query = Question.query.join(QuestionCategory).filter(
        QuestionCategory.level == level
    )
    
    if category_id:
        query = query.filter(Question.category_id == category_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    all_questions = query.all()
    
    if len(all_questions) < num_questions:
        selected = all_questions
    else:
        selected = random.sample(all_questions, num_questions)
    
    return jsonify([{
        'id': q.id,
        'content': q.content,
        'options': {
            'a': q.option_a,
            'b': q.option_b,
            'c': q.option_c,
            'd': q.option_d
        },
        'correct_answer': q.correct_answer,
        'explanation': q.explanation,
        'marks': q.marks,
        'difficulty': q.difficulty
    } for q in selected])


@api.route('/questions/generate-pdf/<level>', methods=['POST'])
@login_required
def generate_pdf(level):
    """Generate PDF question paper via API."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    data = request.get_json()
    question_ids = data.get('question_ids', [])
    title = data.get('title', f'{level.replace("_", " ").title()} Question Paper')
    
    if not question_ids:
        return jsonify({'error': 'No question IDs provided'}), 400
    
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    if len(questions) != len(question_ids):
        return jsonify({'error': 'Some questions not found'}), 404
    
    # Generate PDF
    pdf_content = generate_question_paper_pdf(questions, title=title, level=level)
    
    # Save temporarily
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    temp_dir = os.path.join('app/static/uploads', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    pdf_path = os.path.join(temp_dir, f'api_{timestamp}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)
    
    return jsonify({
        'success': True,
        'pdf_url': f'/static/uploads/temp/{os.path.basename(pdf_path)}',
        'question_count': len(questions)
    })


@api.route('/documents/<level>')
def get_documents(level):
    """Get documents for a specific level."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    doc_type = request.args.get('type')
    category_id = request.args.get('category', type=int)
    limit = request.args.get('limit', 20, type=int)
    
    query = Document.query.join(DocumentCategory).filter(
        Document.is_approved == True,
        DocumentCategory.level == level
    )
    
    if doc_type:
        query = query.filter(Document.file_type == doc_type)
    if category_id:
        query = query.filter(Document.category_id == category_id)
    
    documents = query.limit(limit).all()
    
    return jsonify([{
        'id': d.id,
        'title': d.title,
        'description': d.description,
        'file_name': d.file_name,
        'file_type': d.file_type,
        'category': d.doc_category.name,
        'subject': d.doc_category.subject,
        'download_count': d.download_count,
        'created_at': d.created_at.isoformat()
    } for d in documents])


@api.route('/categories/questions/<level>')
def get_question_categories(level):
    """Get question categories for a specific level."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    categories = QuestionCategory.query.filter_by(level=level).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'subject': c.subject,
        'question_count': Question.query.filter_by(category_id=c.id).count()
    } for c in categories])


@api.route('/categories/documents/<level>')
def get_document_categories(level):
    """Get document categories for a specific level."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    categories = DocumentCategory.query.filter_by(level=level).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'subject': c.subject,
        'document_type': c.document_type,
        'document_count': Document.query.filter_by(category_id=c.id, is_approved=True).count()
    } for c in categories])


@api.route('/papers/<level>')
def get_papers(level):
    """Get exam papers for a specific level."""
    if level not in ['high_school', 'university']:
        return jsonify({'error': 'Invalid level'}), 400
    
    subject = request.args.get('subject')
    year = request.args.get('year')
    limit = request.args.get('limit', 20, type=int)
    
    query = ExamPaper.query.filter(
        ExamPaper.is_approved == True,
        ExamPaper.level == level
    )
    
    if subject:
        query = query.filter(ExamPaper.subject == subject)
    if year:
        query = query.filter(ExamPaper.year == year)
    
    papers = query.limit(limit).all()
    
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'subject': p.subject,
        'year': p.year,
        'file_name': p.file_name,
        'download_count': p.download_count,
        'created_at': p.created_at.isoformat()
    } for p in papers])
