#!/usr/bin/env python3
"""
Setup script for pdf2latex module
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="pdf2latex",
    version="1.0.0",
    description="Convert PDF files with mathematical expressions to LaTeX using Mistral API",
    author="dixreves-osmanthus",
    author_email="",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pdf2latex=pdf2latex.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Processing :: Markup :: LaTeX",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    keywords=[
        "pdf", "latex", "tex", "mathematics", "mistral", "api", 
        "conversion", "transcription", "math", "equations"
    ],
)
