"""
Command Line Interface for PDF to LaTeX Converter

Provides a user-friendly CLI for converting PDF files to LaTeX using Mistral API.
"""

import argparse
import logging
import sys
import os
from typing import List, Optional

from .transcriber import PDF2LaTeX, TranscriptionOptions
from .mistral_client import MistralClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert PDF files with mathematical expressions to LaTeX using Mistral API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single PDF to LaTeX
  python -m pdf2latex.cli math_paper.pdf -o output.tex -k YOUR_API_KEY

  # Convert with custom model and temperature
  python -m pdf2latex.cli math_paper.pdf -o output.tex -k YOUR_API_KEY --model mistral-large-latest --temperature 0.2

  # Convert multiple PDFs to a directory
  python -m pdf2latex.cli *.pdf -o output_dir/ -k YOUR_API_KEY

  # Extract only mathematical expressions
  python -m pdf2latex.cli math_paper.pdf --math-only -k YOUR_API_KEY

  # Check API health
  python -m pdf2latex.cli --check-api -k YOUR_API_KEY
        """
    )
    
    # Required arguments
    parser.add_argument(
        'pdf_files',
        nargs='+',
        help='PDF file(s) to convert'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file or directory (default: <input>.tex for single file, ./output/ for multiple)'
    )
    
    # API configuration
    parser.add_argument(
        '-k', '--api-key',
        type=str,
        required=True,
        help='Mistral API key'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='Custom Mistral API base URL (default: https://api.mistral.ai/v1)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model to use (default: mistral-large-latest)'
    )
    
    # Transcription options
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.3,
        help='Sampling temperature (0-2, lower for more deterministic output)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='Maximum number of tokens to generate per API call'
    )
    
    parser.add_argument(
        '--preserve-layout',
        action='store_true',
        default=True,
        help='Preserve document layout and structure'
    )
    
    parser.add_argument(
        '--no-preserve-layout',
        action='store_false',
        dest='preserve_layout',
        help='Do not preserve document layout'
    )
    
    # Special modes
    parser.add_argument(
        '--math-only',
        action='store_true',
        default=False,
        help='Extract and convert only mathematical expressions'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        default=False,
        help='Batch convert multiple PDF files'
    )
    
    # Utility options
    parser.add_argument(
        '--check-api',
        action='store_true',
        default=False,
        help='Check API connectivity and exit'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        default=False,
        help='List available models and exit'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        default=False,
        help='Suppress non-error output'
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool, quiet: bool):
    """Configure logging based on verbosity settings."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.INFO)


def check_api_health(api_key: str, base_url: Optional[str] = None) -> bool:
    """Check if the Mistral API is accessible."""
    try:
        client = MistralClient(api_key=api_key, base_url=base_url)
        health = client.check_health()
        client.close()
        return health
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        return False


def list_models(api_key: str, base_url: Optional[str] = None) -> List[dict]:
    """List available models from the Mistral API."""
    try:
        client = MistralClient(api_key=api_key, base_url=base_url)
        models = client.list_models()
        client.close()
        return models
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        return []


def convert_single_pdf(
    pdf_path: str,
    output_path: Optional[str],
    api_key: str,
    base_url: Optional[str] = None,
    options: Optional[TranscriptionOptions] = None
) -> bool:
    """Convert a single PDF file to LaTeX."""
    try:
        # Determine output path
        if not output_path:
            base_name = os.path.splitext(pdf_path)[0]
            output_path = f"{base_name}.tex"
        
        converter = PDF2LaTeX(
            api_key=api_key,
            base_url=base_url,
            options=options
        )
        
        result = converter.convert_to_file(pdf_path, output_path)
        
        logger.info(f"Successfully converted {pdf_path} to {output_path}")
        logger.info(f"Pages processed: {result.page_count}")
        logger.info(f"Math expressions found: {result.math_expressions_found}")
        
        converter.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert {pdf_path}: {str(e)}")
        return False


def convert_math_only(
    pdf_path: str,
    api_key: str,
    base_url: Optional[str] = None,
    temperature: float = 0.3
) -> bool:
    """Extract and convert only mathematical expressions."""
    try:
        options = TranscriptionOptions(temperature=temperature)
        converter = PDF2LaTeX(
            api_key=api_key,
            base_url=base_url,
            options=options
        )
        
        results = converter.convert_math_only(pdf_path)
        
        logger.info(f"Found {len(results)} mathematical expressions in {pdf_path}")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Expression {i} (Page {result['page']}) ---")
            print(f"Original: {result['original']}")
            print(f"LaTeX:    {result['latex']}")
            print("-" * 50)
        
        converter.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract math expressions: {str(e)}")
        return False


def batch_convert(
    pdf_paths: List[str],
    output_dir: str,
    api_key: str,
    base_url: Optional[str] = None,
    options: Optional[TranscriptionOptions] = None
) -> int:
    """Convert multiple PDF files to LaTeX."""
    success_count = 0
    
    try:
        converter = PDF2LaTeX(
            api_key=api_key,
            base_url=base_url,
            options=options
        )
        
        results = converter.batch_convert(pdf_paths, output_dir)
        success_count = len(results)
        
        logger.info(f"Successfully converted {success_count}/{len(pdf_paths)} files")
        
        converter.close()
        
    except Exception as e:
        logger.error(f"Batch conversion failed: {str(e)}")
    
    return success_count


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    setup_logging(args.verbose, args.quiet)
    
    # Create transcription options
    options = TranscriptionOptions(
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        model=args.model,
        preserve_layout=args.preserve_layout
    )
    
    # Handle utility commands
    if args.check_api:
        health = check_api_health(args.api_key, args.base_url)
        if health:
            print("✓ Mistral API is accessible")
        else:
            print("✗ Mistral API is not accessible")
            sys.exit(1)
        return
    
    if args.list_models:
        models = list_models(args.api_key, args.base_url)
        print("Available models:")
        for model in models:
            print(f"  - {model.get('id', 'Unknown')}")
        return
    
    # Handle main conversion
    if args.math_only:
        # Convert only mathematical expressions
        for pdf_path in args.pdf_files:
            convert_math_only(
                pdf_path,
                args.api_key,
                args.base_url,
                args.temperature
            )
    elif args.batch or len(args.pdf_files) > 1:
        # Batch convert multiple files
        output_dir = args.output or "./output/"
        success_count = batch_convert(
            args.pdf_files,
            output_dir,
            args.api_key,
            args.base_url,
            options
        )
        
        if success_count < len(args.pdf_files):
            sys.exit(1)
    else:
        # Convert single file
        success = convert_single_pdf(
            args.pdf_files[0],
            args.output,
            args.api_key,
            args.base_url,
            options
        )
        
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
