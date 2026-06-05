"""
PDF to LaTeX Transcription Module

A Python module that reads PDFs with mathematical expressions and uses Mistral API
to transcribe them to LaTeX code.

Usage:
    from pdf2latex import PDF2LaTeX
    
    # Initialize with your Mistral API key
    converter = PDF2LaTeX(api_key="your-mistral-api-key")
    
    # Convert PDF to LaTeX
    latex_code = converter.convert("math_paper.pdf")
    
    # Save to file
    converter.convert_to_file("math_paper.pdf", "output.tex")
"""

from .pdf_reader import PDFReader
from .mistral_client import MistralClient
from .transcriber import PDF2LaTeX, TranscriptionOptions, TranscriptionResult
from .cli import main

__version__ = "1.0.0"
__all__ = ["PDFReader", "MistralClient", "PDF2LaTeX", "TranscriptionOptions", "TranscriptionResult", "main"]
