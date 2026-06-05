"""
PDF Reader Module

Extracts text and mathematical expressions from PDF files.
Supports multiple extraction strategies for optimal results.
"""

import re
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """Represents a single page from a PDF with extracted content."""
    page_number: int
    text: str
    images: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class ExtractedMath:
    """Represents extracted mathematical content."""
    expression: str
    context: str  # Surrounding text
    page_number: int
    position: Tuple[float, float]  # (x, y) coordinates
    is_inline: bool


class PDFReader:
    """
    PDF Reader that extracts text and mathematical expressions.
    
    Uses PyMuPDF (fitz) for high-quality PDF text extraction with
    support for mathematical notation detection.
    """
    
    def __init__(self):
        """Initialize the PDF reader."""
        self._validate_pymupdf()
    
    def _validate_pymupdf(self):
        """Check if PyMuPDF is available."""
        try:
            import fitz
            self.fitz = fitz
        except ImportError:
            raise ImportError(
                "PyMuPDF (fitz) is required. Install with: pip install pymupdf"
            )
    
    def read_pdf(self, file_path: str) -> List[PDFPage]:
        """
        Read a PDF file and extract all pages.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of PDFPage objects containing extracted content
        """
        doc = self.fitz.open(file_path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Extract text with layout information
            text = page.get_text("text")
            
            # Extract images
            images = self._extract_images(page)
            
            # Extract metadata
            metadata = {
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
            }
            
            pages.append(PDFPage(
                page_number=page_num + 1,
                text=text,
                images=images,
                metadata=metadata
            ))
        
        doc.close()
        return pages
    
    def _extract_images(self, page) -> List[Dict[str, Any]]:
        """Extract images from a PDF page."""
        images = []
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            images.append({
                "xref": xref,
                "width": base_image["width"],
                "height": base_image["height"],
                "colorspace": base_image["colorspace"],
                "image": base_image["image"],
            })
        
        return images
    
    def extract_text_with_layout(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text with detailed layout information.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing text blocks with coordinates
        """
        doc = self.fitz.open(file_path)
        text_blocks = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_blocks.append({
                                "text": span["text"],
                                "x": span["bbox"][0],
                                "y": span["bbox"][1],
                                "width": span["bbox"][2] - span["bbox"][0],
                                "height": span["bbox"][3] - span["bbox"][1],
                                "page": page_num + 1,
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                            })
        
        doc.close()
        return text_blocks
    
    def extract_math_expressions(self, file_path: str) -> List[ExtractedMath]:
        """
        Extract mathematical expressions from a PDF.
        
        Uses heuristics to identify mathematical content based on:
        - Special characters ($, \\, _, ^, etc.)
        - Font information (mathematical fonts)
        - Layout patterns
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of ExtractedMath objects
        """
        text_blocks = self.extract_text_with_layout(file_path)
        math_expressions = []
        
        # Patterns that indicate mathematical content
        math_patterns = [
            r'\\',  # LaTeX commands
            r'\$',   # Inline math delimiters
            r'\\\$',  # Display math delimiters
            r'\\begin\{',  # LaTeX environments
            r'\\end\{',
            r'\\frac',
            r'\\sqrt',
            r'\\sum',
            r'\\int',
            r'\\prod',
            r'\\lim',
            r'\\alpha',
            r'\\beta',
            r'\\gamma',
            r'\\delta',
            r'\\epsilon',
            r'\\zeta',
            r'\\eta',
            r'\\theta',
            r'\\lambda',
            r'\\mu',
            r'\\nu',
            r'\\xi',
            r'\\pi',
            r'\\sigma',
            r'\\tau',
            r'\\phi',
            r'\\chi',
            r'\\psi',
            r'\\omega',
        ]
        
        # Also look for Unicode mathematical symbols
        unicode_math_patterns = [
            r'[∀∃∈∉∋∌⊆⊂⊃⊇⊄⊅∪∩∖∧∨¬⇒⇔∴∵∫∮∯∰∱∲∳∵∶∷≈≡≢≤≥≪≫⊕⊗⊥⊤⊣⌈⌉⌊⌋⌜⌝⌞⌟⟨⟩⟪⟫⟮⟯]',
            r'[αβγδεζηθικλμνξοπρστυφχψω]',
            r'[ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]',
        ]
        
        # Combine patterns
        combined_pattern = "|".join(math_patterns + unicode_math_patterns)
        math_regex = re.compile(combined_pattern)
        
        for block in text_blocks:
            text = block["text"]
            if math_regex.search(text):
                # Find the context (surrounding text)
                context_start = max(0, block["text"].rfind(" ", 0, text.find(text)))
                context_end = min(len(text), text.find(" ", text.rfind(text)))
                context = text[context_start:context_end]
                
                math_expressions.append(ExtractedMath(
                    expression=text,
                    context=context,
                    page_number=block["page"],
                    position=(block["x"], block["y"]),
                    is_inline=block["height"] < 20  # Heuristic for inline vs display
                ))
        
        return math_expressions
    
    def get_full_text(self, file_path: str) -> str:
        """
        Get the full text content of a PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Complete text as a single string
        """
        pages = self.read_pdf(file_path)
        return "\n\n".join(page.text for page in pages)
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Number of pages
        """
        doc = self.fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return page_count
