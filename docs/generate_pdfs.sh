#!/bin/bash

# Generate PDF Documentation
# This script converts all markdown documentation to PDF format

echo "📄 Generating PDF Documentation..."
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc is not installed!"
    echo "Please install it using:"
    echo "  macOS: brew install pandoc"
    echo "  Ubuntu: sudo apt-get install pandoc"
    echo "  Windows: choco install pandoc"
    exit 1
fi

# Change to docs directory
cd "$(dirname "$0")"

# Create PDFs directory
mkdir -p PDFs

# Convert each markdown file to PDF
echo "Converting FRONTEND_ADMIN_APP_GUIDE.md..."
pandoc FRONTEND_ADMIN_APP_GUIDE.md -o PDFs/FRONTEND_ADMIN_APP_GUIDE.pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=blue \
    -V urlcolor=blue \
    --metadata title="Admin App - Frontend Developer Guide" \
    --metadata author="ITS Question Service" \
    --metadata date="$(date +%Y-%m-%d)"

echo "Converting API_QUICK_REFERENCE.md..."
pandoc API_QUICK_REFERENCE.md -o PDFs/API_QUICK_REFERENCE.pdf \
    --pdf-engine=xelatex \
    --toc \
    -V geometry:margin=0.75in \
    -V fontsize=10pt \
    -V colorlinks=true \
    -V linkcolor=blue \
    --metadata title="API Quick Reference" \
    --metadata author="ITS Question Service"

echo "Converting ADMIN_APP_ARCHITECTURE.md..."
pandoc ADMIN_APP_ARCHITECTURE.md -o PDFs/ADMIN_APP_ARCHITECTURE.pdf \
    --pdf-engine=xelatex \
    --toc \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=blue \
    --metadata title="Admin App - Architecture Overview" \
    --metadata author="ITS Question Service"

echo "Converting README_FRONTEND_DOCS.md..."
pandoc README_FRONTEND_DOCS.md -o PDFs/README_FRONTEND_DOCS.pdf \
    --pdf-engine=xelatex \
    --toc \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=blue \
    --metadata title="Frontend Documentation - Index" \
    --metadata author="ITS Question Service"

echo "Converting TOPIC_RESOURCES_API.md..."
pandoc TOPIC_RESOURCES_API.md -o PDFs/TOPIC_RESOURCES_API.pdf \
    --pdf-engine=xelatex \
    --toc \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=blue \
    --metadata title="Topic Resources API Documentation" \
    --metadata author="ITS Question Service"

# Create a combined PDF
echo ""
echo "Creating combined documentation PDF..."
pandoc \
    README_FRONTEND_DOCS.md \
    ADMIN_APP_ARCHITECTURE.md \
    FRONTEND_ADMIN_APP_GUIDE.md \
    API_QUICK_REFERENCE.md \
    TOPIC_RESOURCES_API.md \
    -o PDFs/COMPLETE_FRONTEND_DOCUMENTATION.pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=blue \
    -V urlcolor=blue \
    --metadata title="Complete Frontend Documentation" \
    --metadata subtitle="Admin Material Upload Web App" \
    --metadata author="ITS Question Service" \
    --metadata date="$(date +%Y-%m-%d)"

echo ""
echo "✅ PDF generation complete!"
echo ""
echo "Generated PDFs:"
echo "  📄 FRONTEND_ADMIN_APP_GUIDE.pdf"
echo "  📄 API_QUICK_REFERENCE.pdf"
echo "  📄 ADMIN_APP_ARCHITECTURE.pdf"
echo "  📄 README_FRONTEND_DOCS.pdf"
echo "  📄 TOPIC_RESOURCES_API.pdf"
echo "  📄 COMPLETE_FRONTEND_DOCUMENTATION.pdf (Combined)"
echo ""
echo "Location: docs/PDFs/"
echo ""
echo "To view:"
echo "  open PDFs/COMPLETE_FRONTEND_DOCUMENTATION.pdf"
