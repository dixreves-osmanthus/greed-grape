# Exam Paper Processing Feature

## Overview

This feature allows users to upload exam paper PDFs and automatically extract questions, transcribe them to LaTeX format, extract images, and generate a clean PDF with questions only.

## Features

1. **PDF Upload**: Users can upload exam paper PDFs
2. **Text Extraction**: Extract all text from the PDF
3. **Question Detection**: Automatically identify and separate individual questions
4. **LaTeX Transcription**: Convert questions to proper LaTeX format using Mistral API
5. **Image Extraction**: Extract and trim images from questions
6. **PDF Generation**: Generate a new PDF from the LaTeX code
7. **Preview**: View the processed PDF in the browser
8. **Editing**: Edit LaTeX code for individual questions
9. **Regeneration**: Regenerate PDF after making edits

## Technical Implementation

### Database Models

- `ExamPaper`: Original uploaded exam paper
- `ExtractedExamPaper`: Processed version with extracted data
- `ExtractedQuestion`: Individual questions extracted from the paper
- `QuestionImage`: Images associated with questions

### Services

- `MistralClient`: Handles all Mistral API interactions
  - Text extraction from PDFs/images
  - Question detection and segmentation
  - LaTeX transcription
  
- `PaperProcessor`: Main processing service
  - Extracts text from PDF using pdfplumber
  - Processes text with Mistral API
  - Extracts and trims images
  - Generates PDF from LaTeX

### Routes

- `/<level>/upload/paper`: Upload exam paper
- `/<level>/paper/<id>/process`: Start processing a paper
- `/<level>/paper/<id>/start-processing`: AJAX endpoint to start processing
- `/<level>/paper/<id>/processed`: View processed paper
- `/<level>/processed/<id>/download-pdf`: Download processed PDF
- `/<level>/processed/<id>/regenerate-pdf`: Regenerate PDF
- `/<level>/processed/<id>/question/<qid>/update`: Update question LaTeX
- `/<level>/processed/<id>/progress`: Get processing progress

## Setup

### Requirements

1. Install required packages:
```bash
pip install pdfplumber requests Pillow
```

2. Configure Mistral API key:
```bash
export MISTRAL_API_KEY=your-api-key-here
```

3. Ensure pdflatex is installed for PDF generation:
- On Ubuntu: `sudo apt-get install texlive-latex-extra`
- On Mac: `brew install basictex` or `brew install texlive`
- On Windows: Install MiKTeX or TeX Live

## Usage

1. User uploads an exam paper PDF
2. User clicks "Process" on the paper in "My Uploads"
3. System extracts text and questions
4. System transcribes to LaTeX using Mistral API
5. System extracts and trims images
6. System generates PDF from LaTeX
7. User can:
   - View the processed PDF
   - Edit individual question LaTeX
   - Regenerate PDF
   - Download the final PDF

## File Structure

```
app/
├── services/
│   ├── __init__.py
│   ├── mistral_client.py    # Mistral API client
│   └── paper_processor.py    # Paper processing service
├── models.py                 # Database models
├── upload/
│   ├── routes.py             # Upload routes (includes processing routes)
│   └── templates/
│       ├── process_paper.html    # Processing page
│       └── processed_paper.html   # View processed paper
└── templates/
    └── upload/
        └── my_uploads.html     # Updated with process/view buttons
```

## API Integration

The system uses Mistral API for:

1. **Text Extraction**: Extract raw text from PDF content
2. **Question Segmentation**: Identify individual questions in the text
3. **LaTeX Transcription**: Convert plain text to LaTeX format

Each API call includes:
- Model: `mistral-large-latest`
- Temperature: Low (0.1-0.2) for consistent results
- Max tokens: Up to 8192 for large documents

## Customization

### LaTeX Template

The LaTeX template can be customized in `mistral_client.py`:
- Document class: `exam` (can be changed to `article`, `report`, etc.)
- Packages: `amsmath`, `amssymb`, `graphicx`, etc.
- Geometry: A4 paper with 1-inch margins

### Processing Options

- Image scale: 0.8 (adjustable in `describe_image_for_latex`)
- PDF generation timeout: 60 seconds (adjustable in `_generate_pdf_from_latex`)

## Troubleshooting

### Common Issues

1. **pdflatex not found**: Install a LaTeX distribution
2. **Mistral API key not configured**: Set MISTRAL_API_KEY environment variable
3. **Processing takes too long**: Reduce PDF size or split into smaller files
4. **Images not extracted**: Ensure PDF contains embedded images (not just vector graphics)

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs for:
- API request/response details
- Processing progress
- Error messages

## Future Enhancements

1. Background processing with Celery
2. Batch processing for multiple papers
3. Better question detection with ML models
4. Image OCR for handwritten questions
5. Export to other formats (Word, Markdown)
6. Collaborative editing
7. Version history
