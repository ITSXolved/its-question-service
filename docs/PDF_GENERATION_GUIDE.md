# PDF Generation Guide

This guide shows you how to convert the markdown documentation to PDF format.

## 📚 Files to Convert

The following markdown files will be converted to PDF:

1. **README_FRONTEND_DOCS.md** - Documentation index
2. **ADMIN_APP_ARCHITECTURE.md** - Architecture diagrams and overview
3. **FRONTEND_ADMIN_APP_GUIDE.md** - Complete developer guide (main document)
4. **API_QUICK_REFERENCE.md** - API quick reference card
5. **TOPIC_RESOURCES_API.md** - Resource API documentation

---

## Method 1: Using Pandoc (Recommended - Best Quality)

### Install Pandoc

**macOS:**
```bash
brew install pandoc
brew install basictex  # For PDF generation
```

**Ubuntu/Debian:**
```bash
sudo apt-get install pandoc texlive-xetex
```

**Windows:**
```bash
choco install pandoc miktex
```

### Generate PDFs

Run the shell script:
```bash
cd "/Users/zainuscloud/Documents/Xolway Docs/Software Code/Backend Service/its-question-service/docs"
./generate_pdfs.sh
```

This will create:
- Individual PDFs for each document
- One combined PDF: `COMPLETE_FRONTEND_DOCUMENTATION.pdf`

**Output location:** `docs/PDFs/`

---

## Method 2: Using Python Script

### Install Requirements

```bash
pip install markdown weasyprint

# On macOS, you may also need:
brew install cairo pango gdk-pixbuf libffi
```

### Generate PDFs

```bash
cd "/Users/zainuscloud/Documents/Xolway Docs/Software Code/Backend Service/its-question-service/docs"
python3 generate_pdfs.py
```

**Output location:** `docs/PDFs/`

---

## Method 3: Using VS Code Extension

### Install Extension

1. Open VS Code
2. Go to Extensions (⌘+Shift+X / Ctrl+Shift+X)
3. Search for "Markdown PDF"
4. Install "Markdown PDF" by yzane

### Generate PDFs

1. Open any markdown file (e.g., `FRONTEND_ADMIN_APP_GUIDE.md`)
2. Press ⌘+Shift+P (Mac) or Ctrl+Shift+P (Windows)
3. Type "Markdown PDF: Export (pdf)"
4. PDF will be created in the same directory

**Repeat for each markdown file.**

---

## Method 4: Using Online Converter

### Quick Online Conversion

1. Go to https://www.markdowntopdf.com/
2. Upload markdown file
3. Download generated PDF

**Or use:**
- https://cloudconvert.com/md-to-pdf
- https://dillinger.io/ (Markdown editor with PDF export)

---

## Method 5: Using grip (GitHub-style Markdown)

### Install grip

```bash
pip install grip
```

### Generate PDF

```bash
# Start grip server
grip FRONTEND_ADMIN_APP_GUIDE.md

# Open browser to http://localhost:6419
# Print to PDF using browser (⌘+P / Ctrl+P)
```

---

## Method 6: Manual Conversion (macOS)

### Using Preview/Safari

1. Open markdown file in VS Code or any markdown viewer
2. View the rendered HTML
3. Press ⌘+P
4. Select "Save as PDF"
5. Save the PDF

---

## Recommended: Use the Shell Script

**Easiest and best quality:**

```bash
# 1. Install pandoc (one-time setup)
brew install pandoc

# 2. Run the script
cd docs
./generate_pdfs.sh

# 3. View PDFs
open PDFs/
```

---

## Expected Output

After running `generate_pdfs.sh`, you'll have:

```
docs/PDFs/
├── FRONTEND_ADMIN_APP_GUIDE.pdf          (~50 pages)
├── API_QUICK_REFERENCE.pdf               (~10 pages)
├── ADMIN_APP_ARCHITECTURE.pdf            (~30 pages)
├── README_FRONTEND_DOCS.pdf              (~15 pages)
├── TOPIC_RESOURCES_API.pdf               (~20 pages)
└── COMPLETE_FRONTEND_DOCUMENTATION.pdf   (~120 pages)
```

---

## Features of Generated PDFs

The PDFs will include:

✅ **Table of Contents** - Clickable navigation
✅ **Syntax Highlighting** - For code blocks
✅ **Clickable Links** - All URLs are clickable
✅ **Proper Formatting** - Headers, tables, lists
✅ **Page Numbers** - For easy reference
✅ **Professional Layout** - 1-inch margins, 11pt font

---

## Troubleshooting

### Pandoc: Command not found
**Solution:** Install pandoc using the instructions above

### LaTeX Error
**Solution:**
```bash
# Install full LaTeX distribution
brew install --cask mactex  # macOS
sudo apt-get install texlive-full  # Ubuntu
```

### Python: weasyprint not found
**Solution:**
```bash
pip install weasyprint
brew install cairo pango gdk-pixbuf libffi  # macOS dependencies
```

### Permission Denied
**Solution:**
```bash
chmod +x generate_pdfs.sh
chmod +x generate_pdfs.py
```

### Unicode/Emoji Rendering Issues
**Solution:** Use XeLaTeX engine (already configured in script)

---

## Customizing PDF Output

### Modify Shell Script

Edit `generate_pdfs.sh` to change PDF settings:

```bash
# Change margins
-V geometry:margin=1.5in

# Change font size
-V fontsize=12pt

# Change paper size
-V papersize=a4

# Add page numbers
-V pagestyle=plain
```

### Modify Python Script

Edit `generate_pdfs.py` to customize CSS styling in the `css_style` variable.

---

## Quick Start

**For the impatient:**

```bash
# One-liner to install and generate
brew install pandoc && cd docs && ./generate_pdfs.sh && open PDFs/
```

This will:
1. Install pandoc (if not installed)
2. Generate all PDFs
3. Open the PDFs folder

---

## Sharing PDFs

The generated PDFs are ready to share with:
- Frontend developers
- Team members
- Stakeholders
- Documentation repositories

**Combined PDF** (`COMPLETE_FRONTEND_DOCUMENTATION.pdf`) contains all documentation in one file - perfect for offline reading!

---

## Alternative: Export from macOS

### Using Safari

1. Open markdown file in GitHub or rendered view
2. File → Export as PDF
3. Save

### Using Chrome

1. Open markdown file
2. ⌘+P or Ctrl+P
3. Destination: Save as PDF
4. Save

---

## Notes

- **Best Quality:** Pandoc with XeLaTeX
- **Easiest:** VS Code extension
- **No Installation:** Online converters
- **Most Flexible:** Python script

**Recommended:** Use `generate_pdfs.sh` for best results!

---

## Support

If you encounter issues:

1. Check pandoc installation: `pandoc --version`
2. Check LaTeX installation: `xelatex --version`
3. Try Python script as alternative
4. Use online converter as fallback

For questions, refer to:
- Pandoc docs: https://pandoc.org/
- WeasyPrint docs: https://weasyprint.org/

---

**Ready to generate PDFs!** 🎉

Run:
```bash
./generate_pdfs.sh
```
