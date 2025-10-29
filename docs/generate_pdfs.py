#!/usr/bin/env python3
"""
Generate PDF documentation from Markdown files
Alternative to shell script - uses markdown2pdf or weasyprint
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import markdown
        import weasyprint
        return True
    except ImportError:
        print("❌ Required packages not installed!")
        print("")
        print("Please install:")
        print("  pip install markdown weasyprint")
        print("")
        print("On macOS, you may also need:")
        print("  brew install cairo pango gdk-pixbuf libffi")
        return False

def markdown_to_pdf(md_file, pdf_file, title="Documentation"):
    """Convert markdown file to PDF using weasyprint"""
    try:
        import markdown
        from weasyprint import HTML, CSS

        # Read markdown file
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )

        # Add CSS styling
        css_style = """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; border-bottom: 2px solid #bdc3c7; padding-bottom: 8px; margin-top: 30px; }
            h3 { color: #7f8c8d; margin-top: 20px; }
            code {
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
            }
            pre code {
                background-color: transparent;
                padding: 0;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #3498db;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            blockquote {
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin-left: 0;
                color: #555;
            }
        </style>
        """

        # Complete HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            {css_style}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Convert to PDF
        HTML(string=full_html).write_pdf(pdf_file)
        return True

    except Exception as e:
        print(f"❌ Error converting {md_file}: {str(e)}")
        return False

def main():
    """Main function to generate PDFs"""
    print("📄 Generating PDF Documentation...")
    print("")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Get current directory
    docs_dir = Path(__file__).parent
    pdf_dir = docs_dir / "PDFs"
    pdf_dir.mkdir(exist_ok=True)

    # Files to convert
    files_to_convert = [
        ("README_FRONTEND_DOCS.md", "Frontend Documentation - Index"),
        ("ADMIN_APP_ARCHITECTURE.md", "Admin App - Architecture Overview"),
        ("FRONTEND_ADMIN_APP_GUIDE.md", "Admin App - Frontend Developer Guide"),
        ("API_QUICK_REFERENCE.md", "API Quick Reference"),
        ("TOPIC_RESOURCES_API.md", "Topic Resources API Documentation"),
    ]

    # Convert each file
    success_count = 0
    for md_file, title in files_to_convert:
        md_path = docs_dir / md_file
        pdf_path = pdf_dir / md_file.replace('.md', '.pdf')

        if not md_path.exists():
            print(f"⚠️  Skipping {md_file} (not found)")
            continue

        print(f"Converting {md_file}...")
        if markdown_to_pdf(md_path, pdf_path, title):
            print(f"✅ Created {pdf_path.name}")
            success_count += 1
        else:
            print(f"❌ Failed to create {pdf_path.name}")

    print("")
    print(f"✅ Successfully generated {success_count}/{len(files_to_convert)} PDFs")
    print(f"Location: {pdf_dir}/")
    print("")

    # List generated files
    if success_count > 0:
        print("Generated PDFs:")
        for pdf_file in sorted(pdf_dir.glob("*.pdf")):
            print(f"  📄 {pdf_file.name}")
        print("")
        print("To view:")
        print(f"  open {pdf_dir}/")

if __name__ == "__main__":
    main()
