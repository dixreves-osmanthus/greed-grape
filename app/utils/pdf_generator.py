"""
PDF Generation utilities for question papers and documents.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import os


def generate_question_paper_pdf(questions, title="Question Paper", level="high_school", subject="General"):
    """
    Generate a PDF question paper from a list of questions.
    
    Args:
        questions: List of Question objects
        title: Title of the question paper
        level: Education level (high_school/university)
        subject: Subject name
        
    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=72)
    
    # Custom styles
    styles = getSampleStyleSheet()
    
    # Custom styles for the document
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    option_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=3,
        alignment=TA_LEFT,
        leftIndent=20
    )
    
    # Build the document
    story = []
    
    # Title page
    story.append(Paragraph(f"{title}", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Level: {level.replace('_', ' ').title()}", heading_style))
    story.append(Paragraph(f"Subject: {subject}", heading_style))
    story.append(Paragraph(f"Total Questions: {len(questions)}", heading_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(PageBreak())
    
    # Questions
    story.append(Paragraph("Questions", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    for i, question in enumerate(questions, 1):
        # Question number and content
        question_text = f"Q{i}. {question.content}"
        story.append(Paragraph(question_text, question_style))
        
        # Options (if it's a multiple choice question)
        options = []
        if question.option_a:
            options.append(("A", question.option_a))
        if question.option_b:
            options.append(("B", question.option_b))
        if question.option_c:
            options.append(("C", question.option_c))
        if question.option_d:
            options.append(("D", question.option_d))
        
        if options:
            for letter, option_text in options:
                story.append(Paragraph(f"{letter}. {option_text}", option_style))
        
        # Marks
        story.append(Paragraph(f"Marks: {question.marks}", option_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Build the PDF
    doc.build(story)
    
    # Return the PDF bytes
    buffer.seek(0)
    return buffer.getvalue()


def generate_document_pdf(document, title=None, content=None):
    """
    Generate a PDF from a document (essay/handout).
    
    Args:
        document: Document object or file path
        title: Title for the PDF
        content: Text content to include
        
    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    content_style = ParagraphStyle(
        'DocContent',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    story = []
    
    # Title
    if title:
        story.append(Paragraph(title, title_style))
    elif hasattr(document, 'title'):
        story.append(Paragraph(document.title, title_style))
    else:
        story.append(Paragraph("Document", title_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Description if available
    if hasattr(document, 'description') and document.description:
        story.append(Paragraph(document.description, content_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Content
    if content:
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), content_style))
                story.append(Spacer(1, 0.1*inch))
    elif hasattr(document, 'file_path') and os.path.exists(document.file_path):
        # If it's a text file, read and include content
        if document.file_path.endswith('.txt'):
            with open(document.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), content_style))
                    story.append(Spacer(1, 0.1*inch))
        else:
            # For non-text files, just add a note
            story.append(Paragraph(f"This document is available as a file attachment: {document.file_name}", content_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_answer_key_pdf(questions, title="Answer Key"):
    """
    Generate a PDF answer key for questions.
    
    Args:
        questions: List of Question objects
        title: Title for the answer key
        
    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'AnswerTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    answer_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    story = []
    
    # Title
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Total Questions: {len(questions)}", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    # Answer key table
    data = [['Question #', 'Correct Answer', 'Explanation']]
    
    for i, question in enumerate(questions, 1):
        correct_answer = getattr(question, 'correct_answer', 'N/A')
        explanation = getattr(question, 'explanation', '')
        
        # Map answer code to display text
        answer_display = correct_answer.upper() if correct_answer else 'N/A'
        
        data.append([
            str(i),
            answer_display,
            explanation[:50] + '...' if len(explanation) > 50 else explanation
        ])
    
    # Create table
    table = Table(data, colWidths=[1*inch, 1*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
