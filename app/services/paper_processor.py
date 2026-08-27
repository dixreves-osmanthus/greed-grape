"""Exam paper processing service for extracting questions and images."""

import os
import re
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from PIL import Image
import pdfplumber
import io

from app import db
from app.models import (
    ExamPaper, ExtractedExamPaper, ExtractedQuestion, QuestionImage
)
from app.services.mistral_client import MistralClient

# Configure logging
logger = logging.getLogger(__name__)


class PaperProcessor:
    """
    Service for processing uploaded exam papers:
    - Extract text from PDF
    - Identify and extract individual questions
    - Extract and trim images from questions
    - Transcribe to LaTeX
    - Generate preview PDF
    """
    
    def __init__(self, upload_folder: str, mistral_api_key: Optional[str] = None):
        """
        Initialize paper processor.
        
        Args:
            upload_folder: Path to upload folder for storing files
            mistral_api_key: Mistral API key (optional)
        """
        self.upload_folder = upload_folder
        self.processed_folder = os.path.join(upload_folder, 'processed')
        self.images_folder = os.path.join(upload_folder, 'question_images')
        
        # Create folders if they don't exist
        os.makedirs(self.processed_folder, exist_ok=True)
        os.makedirs(self.images_folder, exist_ok=True)
        
        # Initialize Mistral client
        self.mistral = MistralClient(mistral_api_key)
    
    def process_paper(self, exam_paper_id: int, user_id: int) -> Tuple[bool, Optional[ExtractedExamPaper]]:
        """
        Process an exam paper: extract text, questions, and images.
        
        Args:
            exam_paper_id: ID of the exam paper to process
            user_id: ID of the user processing the paper
            
        Returns:
            Tuple of (success, extracted_paper or error message)
        """
        try:
            # Get the exam paper
            exam_paper = ExamPaper.query.get(exam_paper_id)
            if not exam_paper:
                return False, "Exam paper not found"
            
            # Check if already processed
            if exam_paper.extracted_version:
                return True, exam_paper.extracted_version
            
            # Create extracted paper record
            extracted_paper = ExtractedExamPaper(
                exam_paper_id=exam_paper_id,
                user_id=user_id,
                status='processing',
                progress=0
            )
            db.session.add(extracted_paper)
            db.session.commit()
            
            # Update progress
            extracted_paper.progress = 10
            extracted_paper.status = 'extracting_text'
            db.session.commit()
            
            # Step 1: Extract text from PDF
            text = self._extract_text_from_pdf(exam_paper.file_path)
            if not text:
                extracted_paper.status = 'failed'
                extracted_paper.progress = 10
                db.session.commit()
                return False, "Failed to extract text from PDF"
            
            extracted_paper.progress = 30
            extracted_paper.status = 'extracting_questions'
            db.session.commit()
            
            # Step 2: Process text with Mistral
            result = self.mistral.process_exam_paper_text(text)
            
            if not result or 'questions' not in result:
                extracted_paper.status = 'failed'
                extracted_paper.progress = 30
                db.session.commit()
                return False, "Failed to extract questions"
            
            extracted_paper.progress = 50
            extracted_paper.status = 'extracting_images'
            db.session.commit()
            
            # Step 3: Extract images from PDF
            images = self._extract_images_from_pdf(exam_paper.file_path)
            
            extracted_paper.progress = 60
            extracted_paper.status = 'saving_questions'
            db.session.commit()
            
            # Step 4: Save extracted questions and images
            questions_data = result['questions']
            total_questions = len(questions_data)
            questions_with_images = 0
            
            for i, q_data in enumerate(questions_data):
                # Create extracted question
                extracted_question = ExtractedQuestion(
                    extracted_paper_id=extracted_paper.id,
                    question_number=q_data.get('question_number', i + 1),
                    content=q_data.get('content', ''),
                    content_latex=q_data.get('content_latex', q_data.get('content', '')),
                    option_a=q_data.get('options', [None])[0] if q_data.get('options') else None,
                    option_a_latex=q_data.get('options_latex', [None])[0] if q_data.get('options_latex') else None,
                    option_b=q_data.get('options', [None, None])[1] if len(q_data.get('options', [])) > 1 else None,
                    option_b_latex=q_data.get('options_latex', [None, None])[1] if len(q_data.get('options_latex', [])) > 1 else None,
                    option_c=q_data.get('options', [None, None, None])[2] if len(q_data.get('options', [])) > 2 else None,
                    option_c_latex=q_data.get('options_latex', [None, None, None])[2] if len(q_data.get('options_latex', [])) > 2 else None,
                    option_d=q_data.get('options', [None, None, None, None])[3] if len(q_data.get('options', [])) > 3 else None,
                    option_d_latex=q_data.get('options_latex', [None, None, None, None])[3] if len(q_data.get('options_latex', [])) > 3 else None,
                    marks=q_data.get('marks', 1),
                    confidence_score=0.9,  # Default confidence
                    needs_review=False
                )
                db.session.add(extracted_question)
                db.session.commit()
                
                # Save images for this question
                question_has_images = False
                for img_data in images.get(str(i + 1), []):
                    image_path = self._save_question_image(
                        img_data['image'],
                        extracted_question.id,
                        img_data.get('position', 0)
                    )
                    if image_path:
                        question_has_images = True
                        question_image = QuestionImage(
                            extracted_question_id=extracted_question.id,
                            file_path=image_path,
                            file_name=os.path.basename(image_path),
                            original_file_name=img_data.get('original_name', f'question_{i+1}_image.png'),
                            width=img_data.get('width'),
                            height=img_data.get('height'),
                            file_size=img_data.get('size'),
                            file_type=img_data.get('type', 'png'),
                            position=img_data.get('position', 0),
                            description=img_data.get('description', '')
                        )
                        db.session.add(question_image)
                
                if question_has_images:
                    questions_with_images += 1
                
                # Update progress
                progress = 60 + int((i + 1) / total_questions * 30)
                extracted_paper.progress = progress
                db.session.commit()
            
            # Save LaTeX content
            extracted_paper.latex_content = result.get('latex_document', '')
            extracted_paper.total_questions = total_questions
            extracted_paper.questions_with_images = questions_with_images
            
            extracted_paper.progress = 90
            extracted_paper.status = 'generating_pdf'
            db.session.commit()
            
            # Step 5: Generate PDF from LaTeX
            pdf_path = self._generate_pdf_from_latex(
                extracted_paper.latex_content,
                extracted_paper.id
            )
            
            if pdf_path:
                extracted_paper.processed_pdf_path = pdf_path
                extracted_paper.processed_pdf_name = os.path.basename(pdf_path)
            
            extracted_paper.progress = 100
            extracted_paper.status = 'completed'
            extracted_paper.completed_at = datetime.utcnow()
            db.session.commit()
            
            return True, extracted_paper
            
        except Exception as e:
            logger.error(f"Error processing paper: {e}")
            # Update status to failed
            extracted_paper = ExtractedExamPaper.query.filter_by(
                exam_paper_id=exam_paper_id, user_id=user_id
            ).first()
            if extracted_paper:
                extracted_paper.status = 'failed'
                db.session.commit()
            return False, str(e)
    
    def _extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF using pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            return text if text.strip() else None
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return None
    
    def _extract_images_from_pdf(self, pdf_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract images from PDF and group them by question.
        
        Returns:
            Dictionary mapping question numbers to list of image data
        """
        images_by_question = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Get images from page
                    page_images = page.images
                    
                    for img_num, img in enumerate(page_images):
                        # Get image data
                        img_data = page.extract_image(img)
                        
                        # Create PIL image
                        pil_img = Image.open(io.BytesIO(img_data['image']))
                        
                        # Get image info
                        width, height = pil_img.size
                        
                        # Try to determine which question this image belongs to
                        # This is a simple heuristic - in practice, you'd need more sophisticated logic
                        question_num = self._determine_question_for_image(page, img, page_num)
                        
                        if question_num not in images_by_question:
                            images_by_question[question_num] = []
                        
                        images_by_question[question_num].append({
                            'image': img_data['image'],
                            'width': width,
                            'height': height,
                            'size': len(img_data['image']),
                            'type': 'png',
                            'position': img_num,
                            'page': page_num + 1,
                            'original_name': f'page_{page_num+1}_img_{img_num+1}.png'
                        })
            
            return images_by_question
            
        except Exception as e:
            logger.error(f"Failed to extract images from PDF: {e}")
            return {}
    
    def _determine_question_for_image(self, page, img, page_num: int) -> str:
        """
        Determine which question an image belongs to.
        This is a simple heuristic based on image position.
        """
        # Get image bounding box
        x0, y0, x1, y1 = img['x0'], img['top'], img['x1'], img['bottom']
        
        # Extract text near the image to find question number
        text_nearby = page.extract_text(
            x_tolerance=20,
            y_tolerance=20,
            x0=x0 - 20,
            y0=y0 - 20,
            x1=x1 + 20,
            y1=y1 + 20
        )
        
        if text_nearby:
            # Look for question number patterns
            q_match = re.search(r'(?:Question|Q|q\.?|\d+\.)\s*(\d+)', text_nearby)
            if q_match:
                return q_match.group(1)
        
        # Default: return page number as fallback
        return f"page_{page_num + 1}"
    
    def _save_question_image(self, image_bytes: bytes, question_id: int, position: int = 0) -> Optional[str]:
        """
        Save a question image to disk and trim if necessary.
        
        Args:
            image_bytes: Raw image bytes
            question_id: ID of the extracted question
            position: Position of the image in the question
            
        Returns:
            Path to saved image or None if failed
        """
        try:
            # Open image and trim whitespace
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Trim whitespace
            img = self._trim_image(img)
            
            # Generate filename
            filename = f"q{question_id}_img{position}.png"
            filepath = os.path.join(self.images_folder, filename)
            
            # Save image
            img.save(filepath, format='PNG', optimize=True)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save question image: {e}")
            return None
    
    def _trim_image(self, img: Image.Image) -> Image.Image:
        """
        Trim whitespace from an image.
        
        Args:
            img: PIL Image to trim
            
        Returns:
            Trimmed PIL Image
        """
        # Convert to grayscale for thresholding
        gray = img.convert('L')
        
        # Create a binary image (black and white)
        # Using a threshold to determine what's "empty"
        bw = gray.point(lambda x: 0 if x < 240 else 255, '1')
        
        # Find bounding box of non-white pixels
        bbox = bw.getbbox()
        
        if bbox:
            # Crop to bounding box
            return img.crop(bbox)
        
        # If no non-white pixels found, return original
        return img
    
    def _generate_pdf_from_latex(self, latex_content: str, paper_id: int) -> Optional[str]:
        """
        Generate PDF from LaTeX content using pdflatex.
        
        Args:
            latex_content: LaTeX document content
            paper_id: ID of the extracted paper
            
        Returns:
            Path to generated PDF or None if failed
        """
        try:
            # Create a temporary directory for processing
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write LaTeX to file
                latex_path = os.path.join(tmpdir, f'paper_{paper_id}.tex')
                with open(latex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Try to compile with pdflatex
                try:
                    # Run pdflatex
                    result = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', latex_path],
                        cwd=tmpdir,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        # PDF should be in the tmpdir
                        pdf_name = f'paper_{paper_id}.pdf'
                        pdf_path_in_tmp = os.path.join(tmpdir, pdf_name)
                        
                        if os.path.exists(pdf_path_in_tmp):
                            # Move to processed folder
                            final_path = os.path.join(
                                self.processed_folder,
                                f'extracted_{paper_id}.pdf'
                            )
                            os.rename(pdf_path_in_tmp, final_path)
                            return final_path
                    else:
                        logger.error(f"pdflatex failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.error("pdflatex timed out")
                except FileNotFoundError:
                    logger.error("pdflatex not found. Please install a LaTeX distribution.")
                    
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate PDF from LaTeX: {e}")
            return None
    
    def get_extracted_paper(self, extracted_paper_id: int) -> Optional[ExtractedExamPaper]:
        """Get an extracted exam paper by ID."""
        return ExtractedExamPaper.query.get(extracted_paper_id)
    
    def get_extracted_questions(self, extracted_paper_id: int) -> List[ExtractedQuestion]:
        """Get all extracted questions for a paper."""
        return ExtractedQuestion.query.filter_by(
            extracted_paper_id=extracted_paper_id
        ).order_by(ExtractedQuestion.question_number).all()
    
    def get_question_images(self, question_id: int) -> List[QuestionImage]:
        """Get all images for a question."""
        return QuestionImage.query.filter_by(
            extracted_question_id=question_id
        ).order_by(QuestionImage.position).all()
    
    def delete_extracted_paper(self, extracted_paper_id: int) -> bool:
        """Delete an extracted paper and all its associated data."""
        try:
            extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
            if not extracted_paper:
                return False
            
            # Delete associated files
            if extracted_paper.processed_pdf_path:
                try:
                    os.remove(extracted_paper.processed_pdf_path)
                except OSError:
                    pass
            
            # Delete from database (cascade will handle questions and images)
            db.session.delete(extracted_paper)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete extracted paper: {e}")
            db.session.rollback()
            return False
    
    def update_question_latex(self, question_id: int, latex_content: str) -> bool:
        """Update the LaTeX content for a question."""
        try:
            question = ExtractedQuestion.query.get(question_id)
            if not question:
                return False
            
            question.content_latex = latex_content
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update question LaTeX: {e}")
            db.session.rollback()
            return False
    
    def regenerate_pdf(self, extracted_paper_id: int) -> bool:
        """Regenerate PDF from updated LaTeX content."""
        try:
            extracted_paper = ExtractedExamPaper.query.get(extracted_paper_id)
            if not extracted_paper:
                return False
            
            # Get all questions
            questions = self.get_extracted_questions(extracted_paper_id)
            
            # Build LaTeX document
            questions_data = []
            for q in questions:
                q_data = {
                    'question_number': q.question_number,
                    'content_latex': q.content_latex or q.content,
                    'options_latex': [
                        q.option_a_latex or q.option_a,
                        q.option_b_latex or q.option_b,
                        q.option_c_latex or q.option_c,
                        q.option_d_latex or q.option_d
                    ],
                    'marks': q.marks or 1
                }
                questions_data.append(q_data)
            
            # Generate LaTeX
            latex_doc = self.mistral.generate_latex_document(
                questions_data,
                title=f"Exam Paper {extracted_paper_id}"
            )
            
            # Update LaTeX content
            extracted_paper.latex_content = latex_doc
            
            # Generate new PDF
            pdf_path = self._generate_pdf_from_latex(latex_doc, extracted_paper_id)
            
            if pdf_path:
                # Delete old PDF if exists
                if extracted_paper.processed_pdf_path:
                    try:
                        os.remove(extracted_paper.processed_pdf_path)
                    except OSError:
                        pass
                
                extracted_paper.processed_pdf_path = pdf_path
                extracted_paper.processed_pdf_name = os.path.basename(pdf_path)
                extracted_paper.updated_at = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to regenerate PDF: {e}")
            db.session.rollback()
            return False
