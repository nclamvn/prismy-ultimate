#!/bin/bash
# Setup development environment for Advanced PDF

echo "🔧 Setting up Advanced PDF development environment..."

# Install system dependencies
echo "📦 Installing system dependencies..."
# macOS
if command -v brew &> /dev/null; then
    echo "Installing for macOS..."
    brew install tesseract tesseract-lang poppler ghostscript
fi

# Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    echo "Installing for Ubuntu/Debian..."
    sudo apt-get update
    sudo apt-get install -y \
        tesseract-ocr \
        tesseract-ocr-vie \
        poppler-utils \
        ghostscript
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install \
    pdfplumber==0.9.0 \
    camelot-py[cv]==0.11.0 \
    pytesseract==0.3.10 \
    pdf2image==1.16.3 \
    PyMuPDF==1.23.8 \
    tabula-py==2.8.2

# Install dev dependencies
pip install \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    pytest-benchmark==4.0.0

echo "✅ Environment setup complete!"
echo "Run 'pytest tests/unit/modules/extraction/test_advanced_pdf.py' to verify"
