"""
PDF to LaTeX Transcriber Module

Main service that orchestrates PDF reading and LaTeX transcription.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path

from .pdf_reader import PDFReader, PDFPage, ExtractedMath
from .mistral_client import MistralClient, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionOptions:
    """Options for PDF to LaTeX transcription."""
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    model: Optional[str] = None
    include_images: bool = False
    preserve_layout: bool = True
    output_format: str = "latex"  # "latex", "tex", "md"
    
    # Advanced options
    chunk_size: int = 4000  # Max tokens per API call
    overlap: int = 200  # Token overlap between chunks
    batch_size: int = 1  # Number of pages to process in parallel


@dataclass
class TranscriptionResult:
    """Result of a PDF to LaTeX transcription."""
    latex_code: str
    page_count: int
    processed_pages: List[int]
    math_expressions_found: int
    usage_stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PDF2LaTeX:
    """
    Main service for converting PDF documents to LaTeX.
    
    Combines PDF reading capabilities with Mistral API transcription
    to produce high-quality LaTeX output from PDF documents containing
    mathematical expressions.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        options: Optional[TranscriptionOptions] = None
    ):
        """
        Initialize the PDF to LaTeX converter.
        
        Args:
            api_key: Mistral API key
            base_url: Custom Mistral API base URL
            model: Model to use for transcription
            options: Transcription options
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.options = options or TranscriptionOptions()
        
        # Initialize components
        self.pdf_reader = PDFReader()
        self.mistral_client = MistralClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
    
    def convert(
        self,
        pdf_path: str,
        options: Optional[TranscriptionOptions] = None
    ) -> TranscriptionResult:
        """
        Convert a PDF file to LaTeX.
        
        Args:
            pdf_path: Path to the PDF file
            options: Transcription options (overrides default)
            
        Returns:
            TranscriptionResult containing the LaTeX code and metadata
        """
        # Use provided options or default
        opts = options or self.options
        
        # Validate PDF file
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.lower().endswith('.pdf'):
            logger.warning(f"File {pdf_path} does not have .pdf extension")
        
        # Read PDF
        logger.info(f"Reading PDF: {pdf_path}")
        pages = self.pdf_reader.read_pdf(pdf_path)
        page_count = len(pages)
        
        logger.info(f"Found {page_count} pages in PDF")
        
        # Extract mathematical expressions for statistics
        math_expressions = self.pdf_reader.extract_math_expressions(pdf_path)
        math_count = len(math_expressions)
        logger.info(f"Found {math_count} mathematical expressions")
        
        # Process pages
        latex_pages = []
        processed_pages = []
        usage_stats = {"total_tokens": 0, "api_calls": 0}
        
        for i, page in enumerate(pages):
            page_num = i + 1
            logger.info(f"Processing page {page_num}/{page_count}")
            
            # Transcribe page to LaTeX
            latex_page = self._transcribe_page(
                page=page,
                page_number=page_num,
                total_pages=page_count,
                options=opts
            )
            
            latex_pages.append(latex_page)
            processed_pages.append(page_num)
            
            # Update usage stats (approximate)
            usage_stats["total_tokens"] += len(page.text.split())
            usage_stats["api_calls"] += 1
        
        # Combine all pages
        latex_code = self._combine_pages(latex_pages, opts)
        
        # Add document structure
        if opts.preserve_layout:
            latex_code = self._add_document_structure(latex_code, pages)
        
        return TranscriptionResult(
            latex_code=latex_code,
            page_count=page_count,
            processed_pages=processed_pages,
            math_expressions_found=math_count,
            usage_stats=usage_stats,
            metadata={
                "pdf_path": pdf_path,
                "model": opts.model or self.model or self.mistral_client.model,
                "temperature": opts.temperature,
                "options": opts.__dict__
            }
        )
    
    def _transcribe_page(
        self,
        page: PDFPage,
        page_number: int,
        total_pages: int,
        options: TranscriptionOptions
    ) -> str:
        """
        Transcribe a single page to LaTeX.
        
        Args:
            page: PDFPage object
            page_number: Current page number
            total_pages: Total number of pages
            options: Transcription options
            
        Returns:
            LaTeX code for the page
        """
        # Use the Mistral client to transcribe the page
        try:
            latex_code = self.mistral_client.transcribe_page_to_latex(
                page_text=page.text,
                page_number=page_number,
                total_pages=total_pages,
                temperature=options.temperature
            )
            return latex_code
        except Exception as e:
            logger.error(f"Failed to transcribe page {page_number}: {str(e)}")
            # Return the original text as fallback
            return f"% Page {page_number} (transcription failed)\n{page.text}\n"
    
    def _combine_pages(self, latex_pages: List[str], options: TranscriptionOptions) -> str:
        """
        Combine transcribed pages into a single LaTeX document.
        
        Args:
            latex_pages: List of LaTeX code for each page
            options: Transcription options
            
        Returns:
            Combined LaTeX document
        """
        # Add standard LaTeX document structure
        document_class = "article"
        
        preamble = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{geometry}
\geometry{a4paper, margin=1in}

\title{Transcribed Document}
\author{PDF to LaTeX Converter}
\date{\today}

\begin{document}

\maketitle

"""
        
        end_document = r"""
\end{document}
"""
        
        # Combine all pages
        combined = preamble + "\n\n".join(latex_pages) + end_document
        return combined
    
    def _add_document_structure(self, latex_code: str, pages: List[PDFPage]) -> str:
        """
        Add document structure based on PDF content analysis.
        
        Args:
            latex_code: Current LaTeX code
            pages: List of PDF pages
            
        Returns:
            LaTeX code with enhanced structure
        """
        # This is a placeholder for more advanced structure detection
        # For now, we'll just ensure basic document structure
        return latex_code
    
    def convert_to_file(
        self,
        pdf_path: str,
        output_path: str,
        options: Optional[TranscriptionOptions] = None
    ) -> TranscriptionResult:
        """
        Convert a PDF to LaTeX and save to a file.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Path to save the LaTeX file
            options: Transcription options
            
        Returns:
            TranscriptionResult
        """
        result = self.convert(pdf_path, options)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.latex_code)
        
        logger.info(f"LaTeX output saved to: {output_path}")
        return result
    
    def convert_math_only(
        self,
        pdf_path: str,
        options: Optional[TranscriptionOptions] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract and convert only mathematical expressions from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            options: Transcription options
            
        Returns:
            List of dictionaries containing original text and LaTeX transcription
        """
        # Extract mathematical expressions
        math_expressions = self.pdf_reader.extract_math_expressions(pdf_path)
        
        results = []
        for i, expr in enumerate(math_expressions):
            logger.info(f"Converting math expression {i+1}/{len(math_expressions)}")
            
            # Transcribe the expression to LaTeX
            latex_code = self.mistral_client.transcribe_to_latex(
                text=expr.expression,
                context=expr.context,
                temperature=options.temperature if options else 0.3
            )
            
            results.append({
                "original": expr.expression,
                "latex": latex_code,
                "page": expr.page_number,
                "position": expr.position,
                "is_inline": expr.is_inline,
                "context": expr.context
            })
        
        return results
    
    def batch_convert(
        self,
        pdf_paths: List[str],
        output_dir: str,
        options: Optional[TranscriptionOptions] = None
    ) -> List[TranscriptionResult]:
        """
        Convert multiple PDF files to LaTeX.
        
        Args:
            pdf_paths: List of PDF file paths
            output_dir: Directory to save LaTeX files
            options: Transcription options
            
        Returns:
            List of TranscriptionResult objects
        """
        results = []
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        for pdf_path in pdf_paths:
            # Generate output filename
            pdf_name = os.path.basename(pdf_path)
            tex_name = os.path.splitext(pdf_name)[0] + ".tex"
            output_path = os.path.join(output_dir, tex_name)
            
            logger.info(f"Converting {pdf_name} to {tex_name}")
            
            try:
                result = self.convert_to_file(pdf_path, output_path, options)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to convert {pdf_path}: {str(e)}")
                continue
        
        return results
    
    def check_api_health(self) -> bool:
        """
        Check if the Mistral API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        return self.mistral_client.check_health()
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available models from the Mistral API.
        
        Returns:
            List of model information
        """
        return self.mistral_client.list_models()
    
    def close(self):
        """Close the Mistral client connection."""
        self.mistral_client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
