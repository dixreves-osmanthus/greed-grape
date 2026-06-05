#!/usr/bin/env python3
"""
Basic usage examples for the pdf2latex module
"""

import os
from pdf2latex import PDF2LaTeX, TranscriptionOptions

def example_basic_conversion():
    """Example: Basic PDF to LaTeX conversion"""
    print("=== Basic Conversion Example ===")
    
    # Initialize with your Mistral API key
    # Replace with your actual API key
    api_key = os.getenv("MISTRAL_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        print("Please set MISTRAL_API_KEY environment variable or replace the placeholder")
        return
    
    # Create converter
    converter = PDF2LaTeX(api_key=api_key)
    
    # Convert a PDF file
    pdf_path = "example.pdf"  # Replace with your PDF file
    
    if not os.path.exists(pdf_path):
        print(f"PDF file {pdf_path} not found. Please create or specify an existing PDF.")
        return
    
    try:
        result = converter.convert(pdf_path)
        print(f"✓ Successfully converted {pdf_path}")
        print(f"  Pages: {result.page_count}")
        print(f"  Math expressions found: {result.math_expressions_found}")
        print(f"  LaTeX code length: {len(result.latex_code)} characters")
        
        # Save to file
        output_path = "output.tex"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.latex_code)
        print(f"  Saved to: {output_path}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
    
    finally:
        converter.close()


def example_with_options():
    """Example: Conversion with custom options"""
    print("\n=== Conversion with Custom Options ===")
    
    api_key = os.getenv("MISTRAL_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        return
    
    # Custom options
    options = TranscriptionOptions(
        temperature=0.2,  # Lower temperature for more deterministic output
        model="mistral-large-latest",
        preserve_layout=True,
        max_tokens=4000
    )
    
    converter = PDF2LaTeX(api_key=api_key, options=options)
    
    pdf_path = "example.pdf"
    if not os.path.exists(pdf_path):
        return
    
    try:
        result = converter.convert(pdf_path, options)
        print(f"✓ Converted with custom options")
        print(f"  Temperature: {options.temperature}")
        print(f"  Model: {options.model}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
    
    finally:
        converter.close()


def example_math_only():
    """Example: Extract and convert only mathematical expressions"""
    print("\n=== Math-Only Extraction Example ===")
    
    api_key = os.getenv("MISTRAL_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        return
    
    converter = PDF2LaTeX(api_key=api_key)
    
    pdf_path = "example.pdf"
    if not os.path.exists(pdf_path):
        return
    
    try:
        math_results = converter.convert_math_only(pdf_path)
        print(f"✓ Found {len(math_results)} mathematical expressions")
        
        for i, result in enumerate(math_results[:3], 1):  # Show first 3
            print(f"\n  Expression {i}:")
            print(f"    Original: {result['original'][:50]}...")
            print(f"    LaTeX:    {result['latex'][:50]}...")
            print(f"    Page:     {result['page']}")
            print(f"    Inline:   {result['is_inline']}")
        
    except Exception as e:
        print(f"✗ Math extraction failed: {e}")
    
    finally:
        converter.close()


def example_batch_conversion():
    """Example: Batch convert multiple PDF files"""
    print("\n=== Batch Conversion Example ===")
    
    api_key = os.getenv("MISTRAL_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        return
    
    converter = PDF2LaTeX(api_key=api_key)
    
    # List of PDF files to convert
    pdf_files = ["example1.pdf", "example2.pdf", "example3.pdf"]
    
    # Filter to existing files
    existing_files = [f for f in pdf_files if os.path.exists(f)]
    
    if not existing_files:
        print("No PDF files found for batch conversion")
        return
    
    try:
        results = converter.batch_convert(
            pdf_paths=existing_files,
            output_dir="./latex_output/"
        )
        print(f"✓ Converted {len(results)} files to ./latex_output/")
        
    except Exception as e:
        print(f"✗ Batch conversion failed: {e}")
    
    finally:
        converter.close()


def example_check_api():
    """Example: Check API connectivity"""
    print("\n=== API Health Check Example ===")
    
    api_key = os.getenv("MISTRAL_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        return
    
    converter = PDF2LaTeX(api_key=api_key)
    
    try:
        health = converter.check_api_health()
        if health:
            print("✓ Mistral API is accessible")
        else:
            print("✗ Mistral API is not accessible")
        
        # List available models
        models = converter.list_available_models()
        print(f"  Available models: {len(models)}")
        for model in models[:3]:  # Show first 3
            print(f"    - {model.get('id', 'Unknown')}")
        
    except Exception as e:
        print(f"✗ API check failed: {e}")
    
    finally:
        converter.close()


def main():
    """Run all examples"""
    print("PDF to LaTeX Converter - Usage Examples")
    print("=" * 50)
    
    example_basic_conversion()
    example_with_options()
    example_math_only()
    example_batch_conversion()
    example_check_api()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
