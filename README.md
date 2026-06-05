# PDF to LaTeX Converter with Mistral API

A Python module that reads PDF files containing mathematical expressions and uses the Mistral API to transcribe them to LaTeX code.

## Features

- **PDF Reading**: Extract text and mathematical expressions from PDF files using PyMuPDF
- **Mathematical Expression Detection**: Automatically identify and extract mathematical content
- **Mistral API Integration**: Use Mistral's powerful language models for accurate LaTeX transcription
- **Flexible Output**: Generate complete LaTeX documents or extract only mathematical expressions
- **Batch Processing**: Convert multiple PDF files in one operation
- **Customizable**: Control temperature, model selection, and other transcription parameters
- **CLI Interface**: Easy-to-use command line interface

## Installation

### Prerequisites

- Python 3.9 or higher
- Mistral API key (get one at [Mistral AI](https://mistral.ai/))

### Install from source

```bash
# Clone the repository
git clone https://github.com/dixreves-osmanthus/greed-grape.git
cd greed-grape

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Install dependencies only

```bash
pip install pymupdf httpx tenacity
```

## Usage

### Quick Start

```python
from pdf2latex import PDF2LaTeX

# Initialize with your Mistral API key
converter = PDF2LaTeX(api_key="your-mistral-api-key")

# Convert a PDF to LaTeX
result = converter.convert("math_paper.pdf")

# Save to file
with open("output.tex", "w") as f:
    f.write(result.latex_code)

# Or use the built-in method
converter.convert_to_file("math_paper.pdf", "output.tex")

# Close the connection
converter.close()
```

### Using Context Manager

```python
with PDF2LaTeX(api_key="your-api-key") as converter:
    result = converter.convert("math_paper.pdf")
    print(f"Found {result.math_expressions_found} mathematical expressions")
```

### Extract Only Mathematical Expressions

```python
with PDF2LaTeX(api_key="your-api-key") as converter:
    math_results = converter.convert_math_only("math_paper.pdf")
    
    for result in math_results:
        print(f"Page {result['page']}: {result['original']} -> {result['latex']}")
```

### Custom Options

```python
from pdf2latex import PDF2LaTeX, TranscriptionOptions

options = TranscriptionOptions(
    temperature=0.2,  # Lower for more deterministic output
    model="mistral-large-latest",
    preserve_layout=True,
    max_tokens=4000
)

converter = PDF2LaTeX(api_key="your-api-key", options=options)
result = converter.convert("math_paper.pdf", options)
```

### Batch Processing

```python
converter = PDF2LaTeX(api_key="your-api-key")

# Convert multiple PDFs
pdf_files = ["paper1.pdf", "paper2.pdf", "paper3.pdf"]
results = converter.batch_convert(pdf_files, output_dir="./latex_output/")
```

## Command Line Interface

### Basic Conversion

```bash
# Convert a single PDF
python -m pdf2latex.cli math_paper.pdf -o output.tex -k YOUR_API_KEY

# Convert with custom options
python -m pdf2latex.cli math_paper.pdf -o output.tex -k YOUR_API_KEY \
    --model mistral-large-latest \
    --temperature 0.2
```

### Extract Mathematical Expressions Only

```bash
python -m pdf2latex.cli math_paper.pdf --math-only -k YOUR_API_KEY
```

### Batch Conversion

```bash
# Convert multiple PDFs
python -m pdf2latex.cli *.pdf -o ./output/ -k YOUR_API_KEY

# Or explicitly use batch mode
python -m pdf2latex.cli paper1.pdf paper2.pdf -o ./output/ -k YOUR_API_KEY --batch
```

### Utility Commands

```bash
# Check API connectivity
python -m pdf2latex.cli --check-api -k YOUR_API_KEY

# List available models
python -m pdf2latex.cli --list-models -k YOUR_API_KEY

# Enable verbose logging
python -m pdf2latex.cli math_paper.pdf -o output.tex -k YOUR_API_KEY -v
```

### CLI Help

```bash
python -m pdf2latex.cli --help
```

## API Reference

### PDF2LaTeX Class

#### Constructor

```python
PDF2LaTeX(
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    options: Optional[TranscriptionOptions] = None
)
```

- `api_key`: Mistral API key (required)
- `base_url`: Custom Mistral API base URL (default: `https://api.mistral.ai/v1`)
- `model`: Model to use (default: `mistral-large-latest`)
- `options`: Transcription options

#### Main Methods

```python
# Convert PDF to LaTeX
convert(pdf_path: str, options: Optional[TranscriptionOptions] = None) -> TranscriptionResult

# Convert PDF to LaTeX and save to file
convert_to_file(pdf_path: str, output_path: str, options: Optional[TranscriptionOptions] = None) -> TranscriptionResult

# Extract and convert only mathematical expressions
convert_math_only(pdf_path: str, options: Optional[TranscriptionOptions] = None) -> List[Dict[str, Any]]

# Batch convert multiple PDFs
batch_convert(pdf_paths: List[str], output_dir: str, options: Optional[TranscriptionOptions] = None) -> List[TranscriptionResult]

# Check API health
check_api_health() -> bool

# List available models
list_available_models() -> List[Dict[str, Any]]
```

### TranscriptionOptions

```python
TranscriptionOptions(
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    include_images: bool = False,
    preserve_layout: bool = True,
    output_format: str = "latex",
    chunk_size: int = 4000,
    overlap: int = 200,
    batch_size: int = 1
)
```

### TranscriptionResult

```python
TranscriptionResult(
    latex_code: str,
    page_count: int,
    processed_pages: List[int],
    math_expressions_found: int,
    usage_stats: Dict[str, Any],
    metadata: Dict[str, Any]
)
```

## Supported Mathematical Notation

The module can handle various mathematical expressions including:

- **Basic operations**: `+`, `-`, `*`, `/`, `=`, `≠`, `<`, `>`, `≤`, `≥`
- **Exponents and indices**: `x²`, `x³`, `x₁`, `x₂`
- **Fractions**: `a/b`, `a over b`
- **Roots**: `√x`, `cube root of x`
- **Summations and integrals**: `∑`, `∫`, `∏`
- **Greek letters**: `α`, `β`, `γ`, `Δ`, `Σ`, `Π`
- **Special functions**: `sin`, `cos`, `tan`, `log`, `ln`, `exp`
- **Matrices and vectors**: Matrix notation, vector notation
- **LaTeX commands**: `\frac`, `\sqrt`, `\sum`, `\int`, `\lim`, etc.

## Examples

See the `examples/` directory for complete usage examples:

- `basic_usage.py`: Comprehensive examples of all features

## Configuration

### Environment Variables

- `MISTRAL_API_KEY`: Your Mistral API key (recommended for CLI usage)

### Custom API Endpoints

You can use the module with compatible API endpoints:

```python
# Use with LocalAI or other compatible endpoints
converter = PDF2LaTeX(
    api_key="not-needed",
    base_url="http://localhost:8080/v1"
)
```

## Error Handling

The module includes comprehensive error handling:

- Invalid API keys
- Network connectivity issues
- PDF reading errors
- API rate limits
- Token limits

## Performance Considerations

- **Large PDFs**: For PDFs with many pages, consider processing in batches
- **Complex documents**: Documents with complex layouts may require manual review
- **API costs**: Be aware of Mistral API pricing and token usage
- **Rate limits**: Respect API rate limits (automatic retry with exponential backoff)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Mistral AI](https://mistral.ai/) for the powerful language models
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF reading capabilities
- [httpx](https://www.python-httpx.org/) for HTTP client functionality
- [tenacity](https://tenacity.readthedocs.io/) for retry logic

## Support

For issues, questions, or feature requests:

1. Check the documentation and examples
2. Review the API reference
3. Open an issue on GitHub

## Changelog

### Version 1.0.0

- Initial release
- PDF reading with PyMuPDF
- Mistral API integration
- Mathematical expression detection
- CLI interface
- Batch processing support
- Comprehensive error handling
