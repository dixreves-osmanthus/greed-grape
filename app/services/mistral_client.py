"""Mistral API client for text extraction and LaTeX transcription."""

import os
import base64
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

import requests
from PIL import Image
import io

# Configure logging
logger = logging.getLogger(__name__)


class MistralClient:
    """
    Client for interacting with Mistral API for:
    - Text extraction from PDFs/images
    - Question detection and segmentation
    - LaTeX transcription
    - Image description for accessibility
    """
    
    API_BASE_URL = "https://api.mistral.ai/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mistral client.
        
        Args:
            api_key: Mistral API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            logger.warning("Mistral API key not provided. Some features may not work.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def _make_request(self, endpoint: str, data: Dict[str, Any], timeout: int = 60) -> Optional[Dict[str, Any]]:
        """Make a request to Mistral API."""
        if not self.api_key:
            logger.error("Mistral API key not configured")
            return None
        
        url = f"{self.API_BASE_URL}/{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Mistral API request failed: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from a PDF file using Mistral's OCR capabilities.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            prompt = """You are a text extraction assistant. Extract all text from the following PDF content.
            Return ONLY the raw text without any formatting, commentary, or explanations.
            Preserve all mathematical expressions, special characters, and formatting as much as possible."""
            
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            response = self._make_request("chat/completions", {
                "model": "mistral-large-latest",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"PDF content (base64): {pdf_b64[:8000]}"}
                ],
                "temperature": 0.1,
                "max_tokens": 8192
            })
            
            if response and 'choices' in response:
                return response['choices'][0]['message']['content']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return None
    
    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image using Mistral's vision capabilities.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = """Extract all text from this image. Return ONLY the raw text without any formatting or commentary.
            Preserve mathematical expressions and special characters."""
            
            response = self._make_request("chat/completions", {
                "model": "mistral-large-latest",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Image content: {image_b64}"}
                ],
                "temperature": 0.1,
                "max_tokens": 4096
            })
            
            if response and 'choices' in response:
                return response['choices'][0]['message']['content']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            return None
    
    def transcribe_to_latex(self, text: str, context: str = "exam question") -> Optional[str]:
        """
        Transcribe plain text to LaTeX format.
        
        Args:
            text: Plain text to convert
            context: Context for the text
            
        Returns:
            LaTeX formatted text or None if failed
        """
        prompt = f"""You are a LaTeX transcription expert. Convert the following text to proper LaTeX format.
        
Context: {context}

Rules:
1. Use \\ for new lines in paragraphs
2. Use \\section{{}} for section headings
3. Use \\subsection{{}} for subsection headings
4. For mathematical expressions:
   - Use $...$ for inline math
   - Use \\[...\\] for display math
   - Use \\frac{{num}}{{den}} for fractions
   - Use \\sqrt{{}} for square roots
   - Use \\sum for summations
   - Use \\int for integrals
   - Use ^{{}} for superscripts
   - Use _{{\text{{sub}}}} for subscripts
5. For multiple choice questions, format as:
   \\item[a.] Option A text
   \\item[b.] Option B text
6. For images, use \\includegraphics[scale=0.8]{{filename.png}}
7. Use \\textbf{{}} for bold text
8. Use \\textit{{}} for italic text
9. Preserve all special characters and formatting

Text to convert:
{text}

Return ONLY the LaTeX code without any explanations or commentary."""
        
        response = self._make_request("chat/completions", {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": "You are a LaTeX transcription expert. Return ONLY LaTeX code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 8192
        })
        
        if response and 'choices' in response:
            return response['choices'][0]['message']['content']
        
        return None
    
    def extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract individual questions from exam paper text.
        
        Args:
            text: Full text of the exam paper
            
        Returns:
            List of dictionaries, each containing question data
        """
        prompt = f"""You are an exam paper parser. Extract all questions from the following text.
        
Text:
{text}

Format each question as a JSON object with these fields:
- question_number: number or string identifier
- content: the question text
- options: array of option texts (for multiple choice)
- marks: number of marks (if available)
- question_type: "multiple_choice", "short_answer", "essay", etc.

Return ONLY a JSON array of question objects. Do not include any other text.

Example output:
[{{"question_number": 1, "content": "What is 2+2?", "options": ["A. 3", "B. 4", "C. 5"], "marks": 1, "question_type": "multiple_choice"}}]"""
        
        response = self._make_request("chat/completions", {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": "You are an exam paper parser. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 8192
        })
        
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content']
            try:
                import re
                json_match = re.search(r'\[(.*?)\])', content, re.DOTALL)
                if json_match:
                    json_str = f"[{json_match.group(1)}]"
                    return json.loads(json_str)
                else:
                    return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse questions JSON: {e}")
                return []
        
        return []
    
    def describe_image_for_latex(self, image_path: str) -> Optional[str]:
        """
        Generate a description of an image for LaTeX inclusion.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            LaTeX code for including the image or None if failed
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
            
            filename = Path(image_path).name
            latex = f"\\includegraphics[scale=0.8]{{{filename}}}"
            
            return latex
            
        except Exception as e:
            logger.error(f"Failed to describe image: {e}")
            return None
    
    def generate_latex_document(self, questions: List[Dict[str, Any]], title: str = "Exam Paper") -> str:
        """
        Generate a complete LaTeX document from extracted questions.
        
        Args:
            questions: List of question dictionaries
            title: Document title
            
        Returns:
            Complete LaTeX document as string
        """
        latex = r"""\documentclass[12pt]{exam}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{geometry}

\geometry{a4paper, margin=1in}

\title{%s}
\date{\today}

\begin{document}

\maketitle

\begin{questions}
""" % title
        
        for q in questions:
            question_num = q.get('question_number', '')
            content = q.get('content_latex', q.get('content', ''))
            options = q.get('options', [])
            marks = q.get('marks', 1)
            
            latex += f"\\question[{marks}] {content}"
            latex += "\n\n"
            
            if options:
                for i, option in enumerate(options):
                    letter = chr(97 + i)
                    latex += f"\\item[{letter}.] {option}"
                    latex += "\n"
            
            latex += "\n"
        
        latex += r"""\end{questions}

\end{document}
"""
        
        return latex
    
    def process_exam_paper_text(self, text: str) -> Dict[str, Any]:
        """
        Complete processing of exam paper text:
        1. Extract questions
        2. Transcribe to LaTeX
        
        Args:
            text: Full text of the exam paper
            
        Returns:
            Dictionary with processed data
        """
        questions = self.extract_questions_from_text(text)
        
        processed_questions = []
        for q in questions:
            content_latex = self.transcribe_to_latex(
                q.get('content', ''),
                context="exam question"
            )
            
            options_latex = []
            for opt in q.get('options', []):
                opt_latex = self.transcribe_to_latex(opt, context="exam option")
                options_latex.append(opt_latex or opt)
            
            processed_q = {
                'question_number': q.get('question_number'),
                'content': q.get('content', ''),
                'content_latex': content_latex or q.get('content', ''),
                'options': q.get('options', []),
                'options_latex': options_latex,
                'marks': q.get('marks', 1),
                'question_type': q.get('question_type', 'unknown')
            }
            processed_questions.append(processed_q)
        
        latex_doc = self.generate_latex_document(processed_questions)
        
        return {
            'questions': processed_questions,
            'latex_document': latex_doc,
            'total_questions': len(processed_questions)
        }
