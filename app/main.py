"""
Flask API for Computer Adaptive Mastery Testing System
Enhanced with PYQ (Previous Year Questions) Upload and Retrieval Services
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import traceback
from typing import Dict, List, Any, Optional, Union
import os
import asyncio
import uuid
from io import BytesIO
from zipfile import ZipFile
from xml.sax.saxutils import escape

# Import the existing services
from .item_bank_service import ItemBankService, QuestionFilter
from .supabase_knowledge_base import *
from .llm_attribute_service import *

# Import the new PYQ services
from .pyq_upload_service import PYQUploadService, PYQQuestion, PYQMetadata
from .pyq_retriever_service import PYQRetrieverService, PYQSessionFilter, SessionStatus

# Import image upload service
from .image_upload_service import ImageUploadService

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Environment variables
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')

# Initialize services
kb = SupabaseKnowledgeBase(supabase_url, supabase_key)
# LLM service disabled - attribute generation is now manual
# llm_service = LLMAttributeService(openrouter_api_key)
llm_service = None
item_bank_service = ItemBankService(kb.client)

# Initialize PYQ services (without LLM attribute generation)
pyq_upload_service = PYQUploadService(kb.client, llm_service=None)
pyq_retriever_service = PYQRetrieverService(kb.client, fallback_provider=pyq_upload_service)

# Initialize image upload service
image_upload_service = ImageUploadService(kb.client)

# Helper functions (keeping existing ones)
def get_exams():
    """Get all exams."""
    result = kb.client.table("exams").select("*").execute()
    return result.data

def get_subjects(exam_id=None):
    """Get subjects, optionally filtered by exam_id."""
    query = kb.client.table("subjects").select("*").eq("exam_id", exam_id)
    result = query.execute()
    subjects = result.data
    return subjects

def get_chapters(subject_id=None):
    """Get chapters, optionally filtered by subject_id."""
    query = kb.client.table("chapters").select("*")
    if subject_id:
        query = query.eq("subject_id", subject_id)
    result = query.execute()
    return result.data

def get_topics(chapter_id=None):
    """Get topics, optionally filtered by chapter_id."""
    query = kb.client.table("topics").select("*")
    if chapter_id:
        query = query.eq("chapter_id", chapter_id)
    result = query.execute()
    return result.data

def get_concepts(topic_id=None):
    """Get concepts, optionally filtered by topic_id."""
    query = kb.client.table("concepts").select("*")
    if topic_id:
        query = query.eq("topic_id", topic_id)
    result = query.execute()
    return result.data

def get_exam_by_id(exam_id):
    """Get exam by ID."""
    result = kb.client.table("exams").select("*").eq("id", exam_id).execute()
    return result.data[0] if result.data else None

def get_subject_by_id(subject_id):
    """Get subject by ID."""
    result = kb.client.table("subjects").select("*").eq("id", subject_id).execute()
    return result.data[0] if result.data else None

def get_chapter_by_id(chapter_id):
    """Get chapter by ID."""
    result = kb.client.table("chapters").select("*").eq("id", chapter_id).execute()
    return result.data[0] if result.data else None

def get_topic_by_id(topic_id):
    """Get topic by ID."""
    result = kb.client.table("topics").select("*").eq("id", topic_id).execute()
    return result.data[0] if result.data else None

def get_concept_by_id(concept_id):
    """Get concept by ID."""
    result = kb.client.table("concepts").select("*").eq("id", concept_id).execute()
    return result.data[0] if result.data else None

def get_attribute_by_id(attribute_id):
    """Get attribute by ID."""
    result = kb.client.table("attributes").select("*").eq("id", attribute_id).execute()
    return result.data[0] if result.data else None

def get_question_by_id(question_id):
    """Get question by ID."""
    result = kb.client.table("questions").select("*").eq("id", question_id).execute()
    return result.data[0] if result.data else None

# Helper function to run async functions
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def _xlsx_column_letter(index: int) -> str:
    """Convert zero-based column index to Excel column letters."""
    letters = ''
    while True:
        index, remainder = divmod(index, 26)
        letters = chr(remainder + 65) + letters
        if index == 0:
            break
        index -= 1
    return letters


def _build_worksheet_xml(headers, rows):
    """Build minimal worksheet XML with inline strings."""
    rows_xml = []

    def cell_xml(col_idx: int, row_idx: int, value) -> str:
        col_letter = _xlsx_column_letter(col_idx)
        cell_ref = f"{col_letter}{row_idx}"
        text = '' if value is None else str(value)
        return f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'

    header_cells = ''.join(cell_xml(col_idx, 1, header) for col_idx, header in enumerate(headers))
    rows_xml.append(f'<row r="1">{header_cells}</row>')

    for row_offset, row in enumerate(rows, start=2):
        data_cells = ''.join(cell_xml(col_idx, row_offset, value) for col_idx, value in enumerate(row))
        rows_xml.append(f'<row r="{row_offset}">{data_cells}</row>')

    sheet_data = ''.join(rows_xml)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheetData>{sheet_data}</sheetData>'
            '</worksheet>')


def _build_xlsx(headers, rows, sheet_name="PYQ_Template") -> BytesIO:
    """Create an in-memory XLSX file with the provided headers and rows."""
    output = BytesIO()
    with ZipFile(output, 'w') as zf:
        zf.writestr('[Content_Types].xml',
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    '<Default Extension="xml" ContentType="application/xml"/>'
                    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                    '</Types>')
        zf.writestr('_rels/.rels',
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                    '</Relationships>')
        zf.writestr('xl/_rels/workbook.xml.rels',
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                    '</Relationships>')
        zf.writestr('xl/workbook.xml',
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    '<sheets>'
                    f'<sheet name="{sheet_name}" sheetId="1" r:id="rId1"/>'
                    '</sheets>'
                    '</workbook>')
        zf.writestr('xl/worksheets/sheet1.xml', _build_worksheet_xml(headers, rows))
    output.seek(0)
    return output

# Helper function to build subject subtree (shared between both paths)
def build_subject_tree_node(subject):
    """Build a subject node with its chapters, topics hierarchy."""
    subject_node = {
        "id": subject["id"],
        "name": subject["name"],
        "description": subject["description"],
        "type": "subject",
        "children": []
    }

    # Get chapters for this subject
    chapters = get_chapters(subject["id"])
    for chapter in chapters:
        chapter_node = {
            "id": chapter["id"],
            "name": chapter["name"],
            "description": chapter["description"],
            "type": "chapter",
            "children": []
        }

        # Get topics for this chapter
        topics = get_topics(chapter["id"])
        for topic in topics:
            topic_node = {
                "id": topic["id"],
                "name": topic["name"],
                "description": topic["description"],
                "type": "topic",
                "children": []
            }

            # Get concepts for this topic (if still using concepts)
            concepts = get_concepts(topic["id"])
            for concept in concepts:
                concept_node = {
                    "id": concept["id"],
                    "name": concept["name"],
                    "description": concept["description"],
                    "type": "concept"
                }
                topic_node["children"].append(concept_node)

            chapter_node["children"].append(topic_node)

        subject_node["children"].append(chapter_node)

    return subject_node

#=====================================================
# PYQ UPLOAD ENDPOINTS
#=====================================================

@app.route('/api/pyq/upload/single', methods=['POST'])
def upload_single_pyq():
    """Upload a single PYQ question with metadata."""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        # Create PYQ question object
        pyq_question = PYQQuestion(**data)
        
        # Upload the question
        result = run_async(pyq_upload_service.upload_single_pyq(pyq_question))
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/upload/bulk', methods=['POST'])
def upload_bulk_pyq():
    """Upload multiple PYQ questions in bulk."""
    try:
        data = request.json
        
        if not data or "questions" not in data:
            return jsonify({"error": "Invalid request data. Expected 'questions' array"}), 400
        
        # Create PYQ question objects
        pyq_questions = []
        for q_data in data["questions"]:
            try:
                pyq_question = PYQQuestion(**q_data)
                pyq_questions.append(pyq_question)
            except Exception as e:
                return jsonify({"error": f"Invalid question data: {str(e)}"}), 400
        
        # Upload questions in bulk
        result = run_async(pyq_upload_service.upload_bulk_pyq(pyq_questions))
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/upload/excel', methods=['POST'])
def upload_pyq_from_excel():
    """Upload PYQ questions from Excel file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get mapping configuration from form data
        mapping_config = {}
        for key in request.form:
            mapping_config[key] = request.form[key]
        
        if not mapping_config:
            # Default mapping configuration
            mapping_config = {
                'content': 'content',
                'correct_answer': 'correct_answer',
                'options': 'options',
                'year': 'year',
                'exam_session': 'exam_session',
                'paper_code': 'paper_code',
                'question_number': 'question_number',
                'marks_allocated': 'marks_allocated',
                'time_allocated': 'time_allocated',
                'solution': 'solution',
                'source': 'source',
                'tags': 'tags',
                'difficulty_level': 'difficulty_level',
                'question_type': 'question_type',
                'exam_id': 'exam_id',
                'subject_id': 'subject_id',
                'chapter_id': 'chapter_id',
                'topic_id': 'topic_id',
                'concept_id': 'concept_id'
            }
        
        # Save file temporarily
        file_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
        file.save(file_path)
        
        # Upload from Excel
        result = run_async(pyq_upload_service.upload_from_excel(file_path, mapping_config))
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/statistics', methods=['GET'])
def get_pyq_statistics():
    """Get PYQ upload statistics."""
    try:
        # Get filters from query parameters
        filters = {}
        
        year = request.args.get('year')
        if year:
            filters['year'] = int(year)
        
        exam_session = request.args.get('exam_session')
        if exam_session:
            filters['exam_session'] = exam_session
        
        source = request.args.get('source')
        if source:
            filters['source'] = source
        
        # Get statistics
        stats = run_async(pyq_upload_service.get_pyq_statistics(filters))
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/search', methods=['GET'])
def search_pyq_questions():
    """Search PYQ questions with filters."""
    try:
        # Extract filters from query parameters
        filters = {}
        
        # Hierarchy filters
        for param in ['exam_id', 'subject_id', 'chapter_id', 'topic_id', 'concept_id']:
            value = request.args.get(param)
            if value:
                filters[param] = value
        
        # PYQ specific filters
        year = request.args.get('year')
        if year:
            filters['year'] = int(year)
        
        for param in ['exam_session', 'source', 'difficulty_level', 'question_type']:
            value = request.args.get(param)
            if value:
                filters[param] = value
        
        # Pagination
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # Search questions
        result = run_async(pyq_upload_service.search_pyq_questions(filters, page, page_size))
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#=====================================================
# PYQ RETRIEVER/SESSION ENDPOINTS
#=====================================================

@app.route('/api/pyq/session/create', methods=['POST'])
def create_pyq_session():
    """Create a new PYQ practice session."""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        user_id = data.get('user_id')
        session_name = data.get('session_name', 'PYQ Practice Session')
        filters_data = data.get('filters', {})
        time_limit = data.get('time_limit')  # in minutes
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Create filters object
        filters = PYQSessionFilter(**filters_data)
        
        # Create session
        result = run_async(pyq_retriever_service.create_session(
            user_id, session_name, filters, time_limit
        ))
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/current', methods=['GET'])
def get_current_question(session_id):
    """Get the current question for a session."""
    try:
        result = run_async(pyq_retriever_service.get_current_question(session_id))
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/submit', methods=['POST'])
def submit_answer(session_id):
    """Submit an answer for the current question."""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        question_id = data.get('question_id')
        user_answer = data.get('user_answer')
        time_taken = data.get('time_taken', 0)  # in seconds
        
        if not question_id or user_answer is None:
            return jsonify({"error": "question_id and user_answer are required"}), 400
        
        # Submit answer
        result = run_async(pyq_retriever_service.submit_answer(
            session_id, question_id, str(user_answer), int(time_taken)
        ))
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/navigate/<direction>', methods=['POST'])
def navigate_question(session_id, direction):
    """Navigate to next/previous question."""
    try:
        result = run_async(pyq_retriever_service.navigate_to_question(session_id, direction))
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/jump/<int:question_index>', methods=['POST'])
def jump_to_question(session_id, question_index):
    """Jump to a specific question by index."""
    try:
        result = run_async(pyq_retriever_service.jump_to_question(session_id, question_index))
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/progress', methods=['GET'])
def get_session_progress(session_id):
    """Get detailed session progress."""
    try:
        result = run_async(pyq_retriever_service.get_session_progress(session_id))
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/pause', methods=['POST'])
def pause_session(session_id):
    """Pause a session."""
    try:
        result = run_async(pyq_retriever_service.pause_session(session_id))
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/session/<session_id>/resume', methods=['POST'])
def resume_session(session_id):
    """Resume a paused session."""
    try:
        result = run_async(pyq_retriever_service.resume_session(session_id))
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/sessions/user/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    """Get all sessions for a user."""
    try:
        status = request.args.get('status', 'all')
        result = run_async(pyq_retriever_service.get_user_sessions(user_id, status))
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#=====================================================
# PYQ UTILITY ENDPOINTS
#=====================================================

@app.route('/api/pyq/template/download', methods=['GET'])
def download_pyq_template():
    """Download Excel template for PYQ upload."""
    try:
        headers = [
            'content', 'options', 'correct_answer', 'year', 'exam_session',
            'paper_code', 'question_number', 'marks_allocated', 'time_allocated',
            'solution', 'source', 'tags', 'difficulty_level', 'question_type',
            'exam_id', 'subject_id', 'chapter_id', 'topic_id', 'concept_id'
        ]

        rows = [[
            'Sample question content here',
            '["Option A", "Option B", "Option C", "Option D"]',
            'Option A',
            2023,
            'January',
            'PAPER-001',
            'Q1',
            1.0,
            2,
            'Detailed solution here',
            'Official',
            'tag1,tag2',
            'Medium',
            'MCQ',
            '', '', '', '', ''
        ]]

        output = _build_xlsx(headers, rows)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='pyq_upload_template.xlsx'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pyq/filters/options', methods=['GET'])
def get_pyq_filter_options():
    """Get available filter options for PYQ sessions."""
    try:
        metadata_records = []
        try:
            result = kb.client.table("pyq_metadata").select("*").execute()
            metadata_records = result.data or []
        except Exception:
            fallback_records = getattr(pyq_upload_service, 'fallback_records', [])
            metadata_records = [record.get('metadata', {}) for record in fallback_records]

        filter_options = {
            "years": sorted({record.get("year") for record in metadata_records if record.get("year") is not None}),
            "exam_sessions": sorted({record.get("exam_session") for record in metadata_records if record.get("exam_session")}),
            "sources": sorted({record.get("source") for record in metadata_records if record.get("source")}),
            "difficulty_levels": sorted({record.get("difficulty_level") for record in metadata_records if record.get("difficulty_level")}),
            "question_types": sorted({record.get("question_type") for record in metadata_records if record.get("question_type")})
        }

        return jsonify(filter_options), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#=====================================================
# EXISTING ENDPOINTS (keeping all existing functionality)
#=====================================================

# Hierarchical Navigation Endpoints
@app.route('/api/hierarchy/exam/<exam_id>/question-count', methods=['GET'])
def get_exam_question_count(exam_id):
    """Get total question count for a specific exam."""
    try:
        count_query = kb.client.table("questions") \
            .select("id", count="exact") \
            .eq("exam_id", exam_id)
        
        count_result = count_query.execute()
        
        return jsonify({
            "exam_id": exam_id, 
            "total_question_count": count_result.count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/subject/<subject_id>/question-count', methods=['GET'])
def get_subject_question_count(subject_id):
    """Get total question count for a specific subject."""
    try:
        count_query = kb.client.table("questions") \
            .select("id", count="exact") \
            .eq("subject_id", subject_id)
        
        count_result = count_query.execute()
        
        return jsonify({
            "subject_id": subject_id, 
            "total_question_count": count_result.count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/chapter/<chapter_id>/question-count', methods=['GET'])
def get_chapter_question_count(chapter_id):
    """Get total question count for a specific chapter."""
    try:
        count_query = kb.client.table("questions") \
            .select("id", count="exact") \
            .eq("chapter_id", chapter_id)
        
        count_result = count_query.execute()
        
        return jsonify({
            "chapter_id": chapter_id, 
            "total_question_count": count_result.count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/topic/<topic_id>/question-count', methods=['GET'])
def get_topic_question_count(topic_id):
    """Get total question count for a specific topic."""
    try:
        count_query = kb.client.table("questions") \
            .select("id", count="exact") \
            .eq("topic_id", topic_id)
        
        count_result = count_query.execute()
        
        return jsonify({
            "topic_id": topic_id, 
            "total_question_count": count_result.count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/concept/<concept_id>/question-count', methods=['GET'])
def get_concept_question_count(concept_id):
    """Get total question count for a specific concept."""
    try:
        count_query = kb.client.table("questions") \
            .select("id", count="exact") \
            .eq("concept_id", concept_id)
        
        count_result = count_query.execute()
        
        return jsonify({
            "concept_id": concept_id, 
            "total_question_count": count_result.count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/exams', methods=['GET'])
def get_exams_new():
    """Get all exams with question counts."""
    try:
        # Get all exams
        result = kb.client.table("exams").select("*").execute()
        exams = result.data
        
        return jsonify(exams)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/subjects', methods=['GET'])
def get_subjects_new():
    """Get subjects for an exam with question counts."""
    try:
        exam_id = request.args.get('exam_id')
        if not exam_id:
            return jsonify({"error": "exam_id parameter is required"}), 400
        
        # Get subjects for this exam
        query = kb.client.table("subjects").select("*").eq("exam_id", exam_id)
        result = query.execute()
        subjects = result.data
        
        return jsonify(subjects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/chapters', methods=['GET'])
def get_chapters_new():
    """Get chapters for a subject with question counts."""
    try:
        subject_id = request.args.get('subject_id')
        if not subject_id:
            return jsonify({"error": "subject_id parameter is required"}), 400
        
        # Get chapters for this subject
        query = kb.client.table("chapters").select("*").eq("subject_id", subject_id)
        result = query.execute()
        chapters = result.data
        
        return jsonify(chapters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/topics', methods=['GET'])
def get_topics_new():
    """Get topics for a chapter with question counts."""
    try:
        chapter_id = request.args.get('chapter_id')
        if not chapter_id:
            return jsonify({"error": "chapter_id parameter is required"}), 400
        
        # Get topics for this chapter
        query = kb.client.table("topics").select("*").eq("chapter_id", chapter_id)
        result = query.execute()
        topics = result.data
        
        return jsonify(topics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/concepts', methods=['GET'])
def get_concepts_new():
    """Get concepts for a topic with question counts."""
    try:
        topic_id = request.args.get('topic_id')
        if not topic_id:
            return jsonify({"error": "topic_id parameter is required"}), 400
        
        # Get concepts for this topic
        query = kb.client.table("concepts").select("*").eq("topic_id", topic_id)
        result = query.execute()
        concepts = result.data
        
        return jsonify(concepts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Item Bank and Statistics Endpoints
@app.route('/api/hierarchy/<level>/<item_id>/stats', methods=['GET'])
def get_hierarchy_stats(level, item_id):
    """Get statistics for a hierarchy level item."""
    try:
        # Validate level
        valid_levels = ["exam", "subject", "chapter", "topic", "concept"]
        if level not in valid_levels:
            return jsonify({"error": f"Invalid level. Must be one of: {valid_levels}"}), 400
        
        # Get questions count
        filter_params = {}
        filter_params[f"{level}_id"] = item_id
        
        question_filter = QuestionFilter(**filter_params)
        result = run_async(item_bank_service.get_item_bank(question_filter))
        
        # Calculate statistics
        questions = result["questions"]
        attributes = result["attributes"]
        q_matrix = result["q_matrix_array"]
        
        # Basic stats
        stats = {
            "question_count": len(questions),
            "attribute_count": len(attributes),
            "difficulty_avg": sum(q.get("difficulty", 0) for q in questions) / len(questions) if questions else 0,
            "discrimination_avg": sum(q.get("discrimination", 0) for q in questions) / len(questions) if questions else 0,
            "guessing_avg": sum(q.get("guessing", 0) for q in questions) / len(questions) if questions else 0,
            "attributes": [
                {"id": attr["id"], "name": attr["name"], "question_count": int(q_matrix[:, i].sum())}
                for i, attr in enumerate(attributes)
            ],
            "difficulty_distribution": {
                "very_easy": len([q for q in questions if q.get("difficulty", 0) < -1]),
                "easy": len([q for q in questions if -1 <= q.get("difficulty", 0) < 0]),
                "medium": len([q for q in questions if 0 <= q.get("difficulty", 0) < 1]),
                "hard": len([q for q in questions if 1 <= q.get("difficulty", 0) < 2]),
                "very_hard": len([q for q in questions if q.get("difficulty", 0) >= 2])
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/item-bank/<level>/<item_id>', methods=['GET'])
def get_item_bank(level, item_id):
    """Get the item bank for a hierarchy level."""
    try:
        # Validate level
        valid_levels = ["exam", "subject", "chapter", "topic", "concept"]
        if level not in valid_levels:
            return jsonify({"error": f"Invalid level. Must be one of: {valid_levels}"}), 400
        
        # Extract pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # Build filter
        filter_params = {}
        filter_params[f"{level}_id"] = item_id
        
        # Add optional difficulty filters
        difficulty_min = request.args.get('difficulty_min')
        if difficulty_min is not None:
            filter_params["difficulty_min"] = float(difficulty_min)
            
        difficulty_max = request.args.get('difficulty_max')
        if difficulty_max is not None:
            filter_params["difficulty_max"] = float(difficulty_max)
            
        text_search = request.args.get('text_search')
        if text_search:
            filter_params["text_search"] = text_search
        
        # Create question filter
        question_filter = QuestionFilter(**filter_params)
        
        # Search questions
        result = run_async(item_bank_service.search_questions(question_filter, page, page_size))
        
        # Get attributes for each question
        questions = result["data"]
        for question in questions:
            q_matrix_result = kb.client.table("q_matrix") \
                .select("attribute_id, value") \
                .eq("question_id", question["id"]) \
                .execute()
                
            q_matrix_entries = q_matrix_result.data
            attribute_ids = [entry["attribute_id"] for entry in q_matrix_entries if entry["value"]]
            
            if attribute_ids:
                attrs_result = kb.client.table("attributes") \
                    .select("id, name, description") \
                    .in_("id", attribute_ids) \
                    .execute()
                    
                question["attributes"] = attrs_result.data
            else:
                question["attributes"] = []
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Search Endpoints
@app.route('/api/search/hierarchy', methods=['GET'])
def search_hierarchy():
    """Search across the hierarchical structure."""
    try:
        query = request.args.get('query', '')
        level = request.args.get('level', 'exams')
        
        # Use the ItemBankService to search
        results = run_async(item_bank_service.search_hierarchical_structure(query, level))
        
        # Add question counts
        for item in results:
            count_result = kb.client.table("questions") \
                .select("*", count="exact") \
                .eq(f"{level[:-1]}_id", item["id"]) \
                .execute()
                
            item["question_count"] = count_result.count
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search/questions', methods=['GET'])
def search_questions():
    """Search for questions across the item bank."""
    try:
        # Extract pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # Build filter from request parameters
        filter_params = {}
        
        for param in ['exam_id', 'subject_id', 'chapter_id', 'topic_id', 'concept_id', 'text_search']:
            value = request.args.get(param)
            if value:
                filter_params[param] = value
        
        # Add optional difficulty filters
        difficulty_min = request.args.get('difficulty_min')
        if difficulty_min is not None:
            filter_params["difficulty_min"] = float(difficulty_min)
            
        difficulty_max = request.args.get('difficulty_max')
        if difficulty_max is not None:
            filter_params["difficulty_max"] = float(difficulty_max)
        
        # Create question filter
        question_filter = QuestionFilter(**filter_params)
        
        # Search questions
        result = run_async(item_bank_service.search_questions(question_filter, page, page_size))
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Advanced Data Export Endpoints
@app.route('/api/export/educdm/<level>/<item_id>', methods=['GET'])
def export_educdm(level, item_id):
    """Export data in EduCDM compatible format."""
    try:
        # Validate level
        valid_levels = ["exam", "subject", "chapter", "topic", "concept"]
        if level not in valid_levels:
            return jsonify({"error": f"Invalid level. Must be one of: {valid_levels}"}), 400
        
        # Build filter
        filter_params = {}
        filter_params[f"{level}_id"] = item_id
        
        # Create question filter
        question_filter = QuestionFilter(**filter_params)
        
        # Export data
        result = run_async(item_bank_service.export_educdm_data(question_filter))
        
        # Convert numpy arrays to lists for JSON serialization
        result["Q"] = result["Q"].tolist()
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# API ROUTES (keeping all existing ones)

# Exam Routes
@app.route('/api/exams', methods=['POST'])
def api_add_exam():
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    exam_type = data.get('exam_type', 'competitive')  # 'competitive' or 'school'

    if not name:
        return jsonify({"error": "Name is required"}), 400

    if exam_type not in ['competitive', 'school']:
        return jsonify({"error": "exam_type must be 'competitive' or 'school'"}), 400

    exam = kb.add_exam(name, description, exam_type)
    return jsonify(exam), 201

# Class Routes (for School path)
@app.route('/api/classes', methods=['POST'])
def api_add_class():
    """Add a new class to a school exam."""
    data = request.json
    exam_id = data.get('exam_id')
    name = data.get('name')
    description = data.get('description', '')
    class_number = data.get('class_number')
    section = data.get('section')

    if not exam_id or not name:
        return jsonify({"error": "Exam ID and name are required"}), 400

    try:
        class_obj = kb.add_class(exam_id, name, description, class_number, section)
        return jsonify(class_obj), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/exams/<exam_id>/classes', methods=['GET'])
def api_get_classes_for_exam(exam_id):
    """Get all classes for a school exam."""
    try:
        classes = kb.get_classes_by_exam(exam_id)
        return jsonify(classes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/classes/<class_id>', methods=['GET'])
def api_get_class(class_id):
    """Get a specific class by ID."""
    try:
        class_obj = kb.get_class_by_id(class_id)
        if not class_obj:
            return jsonify({"error": "Class not found"}), 404
        return jsonify(class_obj)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/classes/<class_id>/subjects', methods=['GET'])
def api_get_subjects_for_class(class_id):
    """Get all subjects for a class (school path)."""
    try:
        subjects = kb.get_subjects_by_class(class_id)
        return jsonify(subjects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Subject Routes
@app.route('/api/subjects', methods=['POST'])
def api_add_subject():
    """
    Add a new subject.
    For competitive exam: provide exam_id
    For school: provide class_id
    """
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    exam_id = data.get('exam_id')  # For competitive path
    class_id = data.get('class_id')  # For school path

    if not name:
        return jsonify({"error": "Name is required"}), 400

    if not exam_id and not class_id:
        return jsonify({"error": "Either exam_id (competitive) or class_id (school) is required"}), 400

    if exam_id and class_id:
        return jsonify({"error": "Provide either exam_id OR class_id, not both"}), 400

    try:
        subject = kb.add_subject(name, description, exam_id, class_id)
        return jsonify(subject), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chapters', methods=['POST'])
def api_add_chapter():
    data = request.json
    subject_id = data.get('subject_id')
    name = data.get('name')
    description = data.get('description', '')
    
    if not subject_id or not name:
        return jsonify({"error": "Subject ID and name are required"}), 400
    
    chapter = kb.add_chapter(subject_id, name, description)
    return jsonify(chapter), 201

@app.route('/api/topics', methods=['POST'])
def api_add_topic():
    data = request.json
    chapter_id = data.get('chapter_id')
    name = data.get('name')
    description = data.get('description', '')
    
    if not chapter_id or not name:
        return jsonify({"error": "Chapter ID and name are required"}), 400
    
    topic = kb.add_topic(chapter_id, name, description)
    return jsonify(topic), 201

@app.route('/api/concepts', methods=['POST'])
def api_add_concept():
    data = request.json
    topic_id = data.get('topic_id')
    name = data.get('name')
    description = data.get('description', '')
    
    if not topic_id or not name:
        return jsonify({"error": "Topic ID and name are required"}), 400
    
    concept = kb.add_concept(topic_id, name, description)
    return jsonify(concept), 201

# Attribute Routes
@app.route('/api/hierarchy/attributes', methods=['GET'])
def api_get_attributes():
    concept_id = request.args.get('concept_id')
    if not concept_id:
        return jsonify({"error": "Concept ID is required"}), 400
    
    attributes = kb.get_attributes_by_concept(concept_id)
    return jsonify(attributes)

@app.route('/api/attributes', methods=['POST'])
def create_attribute():
    """Create a new cognitive attribute."""
    try:
        # Get the attribute data from the request
        attribute_data = request.json
        
        # Create the attribute
        result = kb.client.table("attributes").insert(attribute_data).execute()
        
        if not result.data:
            return jsonify({"error": "Failed to create attribute"}), 500
            
        attribute = result.data[0]
        
        return jsonify(attribute), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/topic/<topic_id>/attributes', methods=['GET'])
def get_topic_attributes(topic_id):
    """Get all attributes for a topic."""
    try:
        # Get attributes for this topic
        result = kb.client.table("attributes") \
            .select("id, name, description") \
            .eq("topic_id", topic_id) \
            .execute()

        attributes = result.data

        return jsonify(attributes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/topic/<topic_id>/attributes', methods=['POST'])
def add_topic_attributes(topic_id):
    """
    Manually add attributes to a topic.
    Accepts either a single attribute object or an array of attributes.
    """
    try:
        data = request.json

        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        # Support both single attribute and array of attributes
        attributes = data if isinstance(data, list) else [data]

        created_attributes = []
        for attr_data in attributes:
            attribute_data = {
                "name": attr_data.get("name"),
                "description": attr_data.get("description", ""),
                "topic_id": topic_id
            }

            if not attribute_data["name"]:
                continue

            # Create the attribute
            result = kb.client.table("attributes").insert(attribute_data).execute()

            if result.data:
                created_attributes.append(result.data[0])

        return jsonify({
            "success": True,
            "created_count": len(created_attributes),
            "attributes": created_attributes
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/attributes/<attribute_id>', methods=['PUT'])
def update_attribute(attribute_id):
    """Update an attribute."""
    try:
        data = request.json

        update_data = {}
        if "name" in data:
            update_data["name"] = data["name"]
        if "description" in data:
            update_data["description"] = data["description"]

        if not update_data:
            return jsonify({"error": "No fields to update"}), 400

        result = kb.client.table("attributes") \
            .update(update_data) \
            .eq("id", attribute_id) \
            .execute()

        return jsonify(result.data[0] if result.data else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/attributes/<attribute_id>', methods=['DELETE'])
def delete_attribute(attribute_id):
    """Delete an attribute."""
    try:
        result = kb.client.table("attributes") \
            .delete() \
            .eq("id", attribute_id) \
            .execute()

        return jsonify({"success": True, "message": "Attribute deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DEPRECATED: Kept for backward compatibility
@app.route('/api/concept/<concept_id>/attributes', methods=['GET'])
def get_concept_attributes(concept_id):
    """
    DEPRECATED: Get all attributes for a concept.
    This endpoint is deprecated. Attributes are now linked to topics.
    Use /api/topic/{topic_id}/attributes instead.
    """
    try:
        # Try to get the topic_id for this concept
        concept_result = kb.client.table("concepts").select("topic_id").eq("id", concept_id).execute()
        if concept_result.data and concept_result.data[0].get("topic_id"):
            topic_id = concept_result.data[0]["topic_id"]
            return get_topic_attributes(topic_id)

        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DISABLED: LLM attribute generation - attributes are now created manually
# @app.route('/api/questions/generate-attributes', methods=['POST'])
# def generate_attribute_suggestions():
#     """
#     DEPRECATED: This endpoint is disabled. Use manual attribute creation instead.
#     """
#     return jsonify({"error": "Attribute generation is disabled. Please use manual attribute creation via /api/topics/{topic_id}/attributes"}), 410

@app.route('/api/questions/create-with-attributes', methods=['POST'])
def create_question_with_selected_attributes():
    """
    Create a question with user-selected attributes.
    Note: 3PL parameters should be provided in the request or defaults will be used.
    """
    try:
        # Get the data from the request
        data = request.json

        if not data:
            return jsonify({"error": "Invalid data"}), 400

        # Extract data
        question_data = data.get("question", {})
        selected_attributes = data.get("selected_attributes", [])
        create_new_attributes = data.get("create_new_attributes", [])

        # Validate required fields
        if not question_data or not "content" in question_data:
            return jsonify({"error": "Missing question data"}), 400

        content = question_data.get("content", "")
        topic_id = question_data.get("topic_id")

        # Set default 3PL parameters if not provided
        if "difficulty" not in question_data:
            question_data["difficulty"] = 0.5
        if "discrimination" not in question_data:
            question_data["discrimination"] = 1.0
        if "guessing" not in question_data:
            question_data["guessing"] = 0.25

        parameters = {
            "difficulty": question_data["difficulty"],
            "discrimination": question_data["discrimination"],
            "guessing": question_data["guessing"]
        }

        # Create the question
        question_result = kb.client.table("questions").insert(question_data).execute()

        if not question_result.data:
            return jsonify({"error": "Failed to create question"}), 500

        question = question_result.data[0]
        question_id = question["id"]

        # Create any new attributes that the user specified
        created_attributes = []
        if create_new_attributes and topic_id:
            for attr in create_new_attributes:
                attr_data = {
                    "name": attr.get("name", ""),
                    "description": attr.get("description", ""),
                    "topic_id": topic_id  # Changed from concept_id to topic_id
                }

                # Validate attribute data
                if not attr_data["name"]:
                    continue

                attr_result = kb.client.table("attributes").insert(attr_data).execute()

                if attr_result.data:
                    created_attr = attr_result.data[0]
                    created_attributes.append(created_attr)

                    # Add to selected attributes for Q-matrix creation
                    selected_attributes.append({
                        "attribute_id": created_attr["id"],
                        "value": True
                    })

        # Create Q-matrix entries for selected attributes
        q_matrix_entries = []
        for attr in selected_attributes:
            if "attribute_id" in attr and "value" in attr:
                q_matrix_entry = {
                    "question_id": question_id,
                    "attribute_id": attr["attribute_id"],
                    "value": attr["value"]
                }
                q_matrix_entries.append(q_matrix_entry)

        # Insert Q-matrix entries in batch
        if q_matrix_entries:
            q_matrix_result = kb.client.table("q_matrix").insert(q_matrix_entries).execute()

        # Return the created question with attributes and parameters
        response = {
            "question": question,
            "parameters": parameters,
            "selected_attributes_count": len(selected_attributes),
            "created_attributes": created_attributes,
            "q_matrix_entries": len(q_matrix_entries)
        }

        return jsonify(response), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Question Routes (keeping all existing ones)
@app.route('/api/questions', methods=['GET'])
def api_get_questions():
    """
    Get questions with filters, including attributes and q_matrix data.
    The q-matrix is formed based on all attributes under the question's concept.
    """
    # Extract filter parameters
    exam_id = request.args.get('exam_id')
    subject_id = request.args.get('subject_id')
    chapter_id = request.args.get('chapter_id')
    topic_id = request.args.get('topic_id')
    concept_id = request.args.get('concept_id')
    
    # Get questions with filters
    questions = kb.get_questions_by_filters(
        exam_id=exam_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        topic_id=topic_id,
        concept_id=concept_id
    )
    
    # Enhance each question with attributes and q_matrix
    enhanced_questions = []
    for question in questions:
        # Get the topic_id for this question
        question_topic_id = question.get("topic_id")
        if not question_topic_id:
            # If no topic_id, skip attribute and q_matrix processing
            question["attributes"] = []
            question["q_matrix"] = []
            enhanced_questions.append(question)
            continue

        # Get ALL attributes for this topic
        topic_attrs_result = kb.client.table("attributes") \
            .select("id, name, description") \
            .eq("topic_id", question_topic_id) \
            .execute()
        topic_attributes = topic_attrs_result.data
        
        # Get Q-matrix entries for this question
        q_matrix_result = kb.client.table("q_matrix") \
            .select("attribute_id, value") \
            .eq("question_id", question["id"]) \
            .execute()
        q_matrix_entries = q_matrix_result.data
        
        # Create a mapping of attribute_id to value from q_matrix
        q_matrix_map = {}
        for entry in q_matrix_entries:
            q_matrix_map[entry["attribute_id"]] = entry["value"]
        
        # Format all topic attributes with value
        formatted_attributes = []
        for attr in topic_attributes:
            # Check if this attribute has a q_matrix entry for this question
            value = q_matrix_map.get(attr["id"], False)

            attr_with_value = {
                "id": attr["id"],
                "name": attr["name"],
                "description": attr["description"],
                "value": value
            }
            formatted_attributes.append(attr_with_value)
        
        # Create q_matrix as array of indices of attributes with value=true
        q_matrix_indices = []
        for i, attr in enumerate(formatted_attributes):
            if attr["value"]:
                q_matrix_indices.append(i)
        
        # Add attributes and q_matrix to question
        question["attributes"] = formatted_attributes
        question["q_matrix"] = q_matrix_indices
        
        enhanced_questions.append(question)
    
    return jsonify(enhanced_questions)

@app.route('/api/questions/<question_id>', methods=['GET'])
def api_get_question(question_id):
    """
    Get a specific question by ID, including attributes and q_matrix data.
    The q-matrix is formed based on all attributes under the question's topic.
    """
    # Get question by ID
    question = get_question_by_id(question_id)
    
    if not question:
        return jsonify({"error": "Question not found"}), 404
    
    # Get the topic_id for this question
    question_topic_id = question.get("topic_id")
    if not question_topic_id:
        # If no topic_id, return with empty attributes and q_matrix
        question["attributes"] = []
        question["q_matrix"] = []
        return jsonify(question)

    # Get ALL attributes for this topic
    topic_attrs_result = kb.client.table("attributes") \
        .select("id, name, description") \
        .eq("topic_id", question_topic_id) \
        .execute()
    topic_attributes = topic_attrs_result.data
    
    # Get Q-matrix entries for this question
    q_matrix_result = kb.client.table("q_matrix") \
        .select("attribute_id, value") \
        .eq("question_id", question_id) \
        .execute()
    q_matrix_entries = q_matrix_result.data
    
    # Create a mapping of attribute_id to value from q_matrix
    q_matrix_map = {}
    for entry in q_matrix_entries:
        q_matrix_map[entry["attribute_id"]] = entry["value"]
    
    # Format all topic attributes with value
    formatted_attributes = []
    for attr in topic_attributes:
        # Check if this attribute has a q_matrix entry for this question
        value = q_matrix_map.get(attr["id"], False)
        
        attr_with_value = {
            "id": attr["id"],
            "name": attr["name"],
            "description": attr["description"],
            "value": value
        }
        formatted_attributes.append(attr_with_value)
    
    # Create q_matrix as array of indices of attributes with value=true
    q_matrix_indices = []
    for i, attr in enumerate(formatted_attributes):
        if attr["value"]:
            q_matrix_indices.append(i)
    
    # Add attributes and q_matrix to question
    question["attributes"] = formatted_attributes
    question["q_matrix"] = q_matrix_indices
    
    return jsonify(question)

@app.route('/api/hierarchy/<level>/<item_id>/questions/enhanced', methods=['GET'])
def api_get_enhanced_questions_by_hierarchy(level, item_id):
    """
    Get questions with enhanced attribute information including:
    - All attributes available at this hierarchical level
    - Q-matrix in vector form for each question
    - Attribute metadata

    The response includes a unified attribute list for the entire level,
    and each question has a binary vector indicating which attributes apply.
    """
    try:
        # Extract pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # Validate level
        valid_levels = ["exam", "subject", "chapter", "topic", "class"]
        if level not in valid_levels:
            return jsonify({"error": f"Invalid level. Must be one of: {valid_levels}"}), 400

        # Build filter based on hierarchy level
        filter_params = {}
        filter_params[f"{level}_id"] = item_id

        # Create question filter
        question_filter = QuestionFilter(**filter_params)

        # Search questions
        result = run_async(item_bank_service.search_questions(question_filter, page, page_size))
        questions = result["data"]

        if not questions:
            return jsonify({
                "level": level,
                "level_id": item_id,
                "total_questions": 0,
                "attributes": [],
                "questions": [],
                "pagination": result["pagination"]
            })

        # Collect all unique topic IDs from questions at this level
        topic_ids = set()
        for question in questions:
            if question.get("topic_id"):
                topic_ids.add(question["topic_id"])

        # Get all attributes for all topics at this level
        all_attributes = []
        attribute_id_to_index = {}

        if topic_ids:
            # Fetch attributes for all topics
            attrs_result = kb.client.table("attributes") \
                .select("id, name, description, topic_id") \
                .in_("topic_id", list(topic_ids)) \
                .execute()

            all_attributes = attrs_result.data

            # Create a mapping of attribute_id to index
            for idx, attr in enumerate(all_attributes):
                attribute_id_to_index[attr["id"]] = idx

        # Process each question
        enhanced_questions = []
        for question in questions:
            # Get Q-matrix entries for this question
            q_matrix_result = kb.client.table("q_matrix") \
                .select("attribute_id, value") \
                .eq("question_id", question["id"]) \
                .execute()

            q_matrix_entries = q_matrix_result.data

            # Create binary vector for this question
            # Vector length = total number of attributes at this level
            q_vector = [0] * len(all_attributes)

            # Fill in the vector based on q_matrix entries
            for entry in q_matrix_entries:
                attr_id = entry["attribute_id"]
                if attr_id in attribute_id_to_index and entry["value"]:
                    idx = attribute_id_to_index[attr_id]
                    q_vector[idx] = 1

            # Add enhanced data to question
            enhanced_question = {
                **question,
                "q_vector": q_vector,
                "attribute_count": sum(q_vector)
            }

            enhanced_questions.append(enhanced_question)

        # Return enhanced response
        response = {
            "level": level,
            "level_id": item_id,
            "total_questions": result["pagination"]["total"],
            "attributes": all_attributes,
            "attribute_count": len(all_attributes),
            "questions": enhanced_questions,
            "pagination": result["pagination"]
        }

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/hierarchy/<level>/<item_id>/questions', methods=['GET'])
def api_get_questions_by_hierarchy(level, item_id):
    """
    Get questions using hierarchy, including attributes and q_matrix data.
    The q-matrix is formed based on all attributes under each question's topic.
    """
    # Extract pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    # Build filter based on hierarchy level
    filter_params = {}
    filter_params[f"{level}_id"] = item_id

    # Create question filter
    question_filter = QuestionFilter(**filter_params)

    # Search questions
    result = run_async(item_bank_service.search_questions(question_filter, page, page_size))
    
    # Enhance each question with attributes and q_matrix
    questions = result["data"]
    for question in questions:
        # Get the topic_id for this question
        question_topic_id = question.get("topic_id")
        if not question_topic_id:
            # If no topic_id, skip attribute and q_matrix processing
            question["attributes"] = []
            question["q_matrix"] = []
            continue

        # Get ALL attributes for this topic
        topic_attrs_result = kb.client.table("attributes") \
            .select("id, name, description") \
            .eq("topic_id", question_topic_id) \
            .execute()
        topic_attributes = topic_attrs_result.data
        
        # Get Q-matrix entries for this question
        q_matrix_result = kb.client.table("q_matrix") \
            .select("attribute_id, value") \
            .eq("question_id", question["id"]) \
            .execute()
        q_matrix_entries = q_matrix_result.data
        
        # Create a mapping of attribute_id to value from q_matrix
        q_matrix_map = {}
        for entry in q_matrix_entries:
            q_matrix_map[entry["attribute_id"]] = entry["value"]
        
        # Format all topic attributes with value
        formatted_attributes = []
        for attr in topic_attributes:
            # Check if this attribute has a q_matrix entry for this question
            value = q_matrix_map.get(attr["id"], False)

            attr_with_value = {
                "id": attr["id"],
                "name": attr["name"],
                "description": attr["description"],
                "value": value
            }
            formatted_attributes.append(attr_with_value)
        
        # Create q_matrix as array of indices of attributes with value=true
        q_matrix_indices = []
        for i, attr in enumerate(formatted_attributes):
            if attr["value"]:
                q_matrix_indices.append(i)
        
        # Add attributes and q_matrix to question
        question["attributes"] = formatted_attributes
        question["q_matrix"] = q_matrix_indices
    
    # Return the enhanced result
    return jsonify(result)

# Add a new endpoint to get a batch of questions by IDs
@app.route('/api/questions/batch-get', methods=['POST'])
def api_get_questions_batch():
    """
    Get multiple questions by their IDs in a single request.
    The q-matrix is formed based on all attributes under each question's concept.
    """
    data = request.json
    question_ids = data.get('question_ids', [])
    
    if not question_ids or not isinstance(question_ids, list):
        return jsonify({"error": "Valid question_ids array is required"}), 400
    
    # Get questions by their IDs
    result = kb.client.table("questions") \
        .select("*") \
        .in_("id", question_ids) \
        .execute()
    questions = result.data
    
    # Create a map of topic_id to attributes for batch processing
    topic_attributes_map = {}

    # Collect all distinct topic IDs
    topic_ids = set()
    for question in questions:
        if question.get("topic_id"):
            topic_ids.add(question["topic_id"])

    # Batch fetch attributes for all topics
    if topic_ids:
        for topic_id in topic_ids:
            attrs_result = kb.client.table("attributes") \
                .select("id, name, description") \
                .eq("topic_id", topic_id) \
                .execute()
            topic_attributes_map[topic_id] = attrs_result.data
    
    # Create a map of question_id to q_matrix entries for batch processing
    q_matrix_map = {}
    if questions:
        for question_id in question_ids:
            q_matrix_result = kb.client.table("q_matrix") \
                .select("attribute_id, value") \
                .eq("question_id", question_id) \
                .execute()
            
            # Convert to a map of attribute_id -> value for easier lookup
            attr_value_map = {}
            for entry in q_matrix_result.data:
                attr_value_map[entry["attribute_id"]] = entry["value"]
            
            q_matrix_map[question_id] = attr_value_map
    
    # Enhance each question with attributes and q_matrix
    for question in questions:
        topic_id = question.get("topic_id")
        if not topic_id or topic_id not in topic_attributes_map:
            question["attributes"] = []
            question["q_matrix"] = []
            continue

        # Get the attributes for this topic
        topic_attributes = topic_attributes_map[topic_id]
        
        # Get the q_matrix entries for this question
        question_q_matrix = q_matrix_map.get(question["id"], {})

        # Format all topic attributes with value
        formatted_attributes = []
        for attr in topic_attributes:
            # Check if this attribute has a q_matrix entry for this question
            value = question_q_matrix.get(attr["id"], False)
            
            attr_with_value = {
                "id": attr["id"],
                "name": attr["name"],
                "description": attr["description"],
                "value": value
            }
            formatted_attributes.append(attr_with_value)
        
        # Create q_matrix as array of indices of attributes with value=true
        q_matrix_indices = []
        for i, attr in enumerate(formatted_attributes):
            if attr["value"]:
                q_matrix_indices.append(i)
        
        # Add attributes and q_matrix to question
        question["attributes"] = formatted_attributes
        question["q_matrix"] = q_matrix_indices
    
    return jsonify({"questions": questions})

@app.route('/api/hierarchy/<level>/<item_id>/children', methods=['GET'])
def api_get_hierarchy_children(level, item_id):
    # Get children at this level
    children = kb.get_children(level, item_id)
    return jsonify(children)

@app.route('/api/hierarchy/<level>/<item_id>/chain', methods=['GET'])
def api_get_hierarchy_chain(level, item_id):
    # Get full hierarchy chain
    chain = kb.get_hierarchy_chain(level, item_id)
    return jsonify(chain)

# Getting the full hierarchy tree - useful for UI navigation
@app.route('/api/hierarchy/tree', methods=['GET'])
def api_get_hierarchy_tree():
    """
    Get the entire hierarchy tree as a nested JSON object.
    Supports both competitive and school exam paths.
    This is useful for UI navigation and visualization.
    """
    # Get all exams
    result = kb.client.table("exams").select("*").execute()
    exams = result.data
    tree = []

    for exam in exams:
        exam_type = exam.get("exam_type", "competitive")
        exam_node = {
            "id": exam["id"],
            "name": exam["name"],
            "description": exam["description"],
            "exam_type": exam_type,
            "type": "exam",
            "children": []
        }

        if exam_type == "school":
            # School path: Exam → Class → Subject → Chapter → Topic
            classes = kb.get_classes_by_exam(exam["id"])
            for class_obj in classes:
                class_node = {
                    "id": class_obj["id"],
                    "name": class_obj["name"],
                    "description": class_obj.get("description"),
                    "class_number": class_obj.get("class_number"),
                    "type": "class",
                    "children": []
                }

                # Get subjects for this class
                subjects = kb.get_subjects_by_class(class_obj["id"])
                for subject in subjects:
                    subject_node = build_subject_tree_node(subject)
                    class_node["children"].append(subject_node)

                exam_node["children"].append(class_node)

        else:
            # Competitive path: Exam → Subject → Chapter → Topic
            subjects = kb.get_subjects_by_exam(exam["id"])
            for subject in subjects:
                subject_node = build_subject_tree_node(subject)
                exam_node["children"].append(subject_node)

        tree.append(exam_node)

    return jsonify(tree)

# Add an endpoint to ensure a hierarchical element exists
@app.route('/api/hierarchy/ensure', methods=['POST'])
def api_ensure_hierarchy():
    """
    Ensure that a hierarchical element exists, creating it if it doesn't.
    This allows the UI to add a missing level in the hierarchy.
    """
    data = request.json
    level = data.get('level')
    name = data.get('name')
    description = data.get('description', '')
    parent_id = data.get('parent_id')
    
    if not level or not name or not parent_id:
        return jsonify({"error": "Level, name, and parent_id are required"}), 400
    
    # Check if the element already exists
    if level == 'subject':
        elements = get_subjects(parent_id)
    elif level == 'chapter':
        elements = get_chapters(parent_id)
    elif level == 'topic':
        elements = get_topics(parent_id)
    elif level == 'concept':
        elements = get_concepts(parent_id)
    else:
        return jsonify({"error": "Invalid level"}), 400
    
    # Check if the element already exists
    for element in elements:
        if element['name'].lower() == name.lower():
            return jsonify({"exists": True, "element": element})
    
    # Element doesn't exist, create it
    if level == 'subject':
        element = kb.add_subject(parent_id, name, description)
    elif level == 'chapter':
        element = kb.add_chapter(parent_id, name, description)
    elif level == 'topic':
        element = kb.add_topic(parent_id, name, description)
    elif level == 'concept':
        element = kb.add_concept(parent_id, name, description)
    
    return jsonify({"exists": False, "element": element})

@app.route('/api/questions/batch', methods=['POST'])
def batch_create_questions():
    """Create multiple questions with Q-matrix entries in a batch."""
    try:
        # Get the batch data from the request
        batch_data = request.json
        
        if not batch_data or "questions" not in batch_data:
            return jsonify({"error": "Invalid batch data format"}), 400
            
        questions = batch_data["questions"]
        created_questions = []
        all_q_matrix_entries = []
        
        # Process each question
        for question_data in questions:
            # Extract attributes if present
            attributes = question_data.pop("attributes", []) if question_data else []
            
            # Create the question
            result = kb.client.table("questions").insert(question_data).execute()
            
            if not result.data:
                continue
                
            question = result.data[0]
            question_id = question["id"]
            created_questions.append(question)
            
            # Create Q-matrix entries if attributes were provided
            q_matrix_entries = []
            if attributes:
                for attr in attributes:
                    if "attribute_id" in attr and "value" in attr:
                        q_matrix_entry = {
                            "question_id": question_id,
                            "attribute_id": attr["attribute_id"],
                            "value": attr["value"]
                        }
                        q_matrix_entries.append(q_matrix_entry)
            
            # If no attributes were explicitly provided but a topic_id was,
            # auto-generate the Q-matrix entries using default values
            elif "topic_id" in question_data and question_data["topic_id"]:
                topic_id = question_data["topic_id"]

                # Get attributes for this topic
                attr_result = kb.client.table("attributes") \
                    .select("id") \
                    .eq("topic_id", topic_id) \
                    .execute()

                topic_attributes = attr_result.data

                if topic_attributes:
                    for attr in topic_attributes:
                        q_matrix_entry = {
                            "question_id": question_id,
                            "attribute_id": attr["id"],
                            "value": True  # Default to True for auto-generated entries
                        }
                        q_matrix_entries.append(q_matrix_entry)
            
            # Add these entries to our collection
            all_q_matrix_entries.extend(q_matrix_entries)
        
        # Insert all Q-matrix entries in a single batch if there are any
        if all_q_matrix_entries:
            q_matrix_result = kb.client.table("q_matrix").insert(all_q_matrix_entries).execute()
        
        # Return the created questions with Q-matrix entries
        response = {
            "questions": created_questions,
            "q_matrix_entries_count": len(all_q_matrix_entries)
        }
        
        return jsonify(response), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# TOPIC RESOURCES ENDPOINTS
# ============================================================================

@app.route('/api/topics/<topic_id>/resources', methods=['POST'])
def add_topic_resource(topic_id):
    """
    Add a resource (video, image, virtual lab, 3D model, animation) to a topic.

    Request body:
    {
        "resource_type": "video|image|3d_model|animation|virtual_lab|pdf|interactive|article|simulation",
        "title": "Resource title",
        "description": "Resource description",
        "url": "https://...",
        "thumbnail_url": "https://... (optional)",
        "duration": 300 (optional, for videos in seconds),
        "file_size": 1024000 (optional, in bytes),
        "metadata": {} (optional, additional properties),
        "order_index": 0 (optional, for sorting)
    }
    """
    try:
        data = request.json

        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        # Validate required fields
        resource_type = data.get('resource_type')
        title = data.get('title')
        url = data.get('url')

        if not all([resource_type, title, url]):
            return jsonify({"error": "resource_type, title, and url are required"}), 400

        # Validate resource type
        valid_types = ['video', 'image', '3d_model', 'animation', 'virtual_lab', 'pdf', 'interactive', 'article', 'simulation']
        if resource_type not in valid_types:
            return jsonify({"error": f"Invalid resource_type. Must be one of: {valid_types}"}), 400

        # Verify topic exists
        topic = get_topic_by_id(topic_id)
        if not topic:
            return jsonify({"error": "Topic not found"}), 404

        # Prepare resource data
        resource_data = {
            "topic_id": topic_id,
            "resource_type": resource_type,
            "title": title,
            "description": data.get('description', ''),
            "url": url,
            "thumbnail_url": data.get('thumbnail_url'),
            "duration": data.get('duration'),
            "file_size": data.get('file_size'),
            "metadata": data.get('metadata', {}),
            "order_index": data.get('order_index', 0),
            "is_active": data.get('is_active', True)
        }

        # Insert resource
        result = kb.client.table("topic_resources").insert(resource_data).execute()

        if not result.data:
            return jsonify({"error": "Failed to create resource"}), 500

        return jsonify(result.data[0]), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/topics/<topic_id>/resources', methods=['GET'])
def get_topic_resources(topic_id):
    """
    Get all resources for a topic, optionally filtered by resource type.

    Query parameters:
    - resource_type: Filter by type (optional)
    - is_active: Filter by active status (optional, default: true)
    """
    try:
        # Verify topic exists
        topic = get_topic_by_id(topic_id)
        if not topic:
            return jsonify({"error": "Topic not found"}), 404

        # Build query
        query = kb.client.table("topic_resources").select("*").eq("topic_id", topic_id)

        # Apply filters
        resource_type = request.args.get('resource_type')
        if resource_type:
            query = query.eq("resource_type", resource_type)

        is_active = request.args.get('is_active', 'true').lower() == 'true'
        query = query.eq("is_active", is_active)

        # Order by order_index
        query = query.order("order_index")

        result = query.execute()

        return jsonify({
            "topic_id": topic_id,
            "topic_name": topic.get("name"),
            "resources": result.data,
            "count": len(result.data)
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/topics/<topic_id>/resources/bulk', methods=['POST'])
def add_bulk_topic_resources(topic_id):
    """
    Add multiple resources to a topic at once.

    Request body:
    {
        "resources": [
            {
                "resource_type": "video",
                "title": "Introduction Video",
                "url": "https://...",
                ...
            },
            {
                "resource_type": "3d_model",
                "title": "3D Model",
                "url": "https://...",
                ...
            }
        ]
    }
    """
    try:
        data = request.json

        if not data or "resources" not in data:
            return jsonify({"error": "Invalid request data. Expected 'resources' array"}), 400

        # Verify topic exists
        topic = get_topic_by_id(topic_id)
        if not topic:
            return jsonify({"error": "Topic not found"}), 404

        resources = data["resources"]
        valid_types = ['video', 'image', '3d_model', 'animation', 'virtual_lab', 'pdf', 'interactive', 'article', 'simulation']

        # Prepare all resources
        resource_data_list = []
        for idx, res in enumerate(resources):
            # Validate required fields
            if not all(k in res for k in ['resource_type', 'title', 'url']):
                continue

            if res['resource_type'] not in valid_types:
                continue

            resource_data = {
                "topic_id": topic_id,
                "resource_type": res['resource_type'],
                "title": res['title'],
                "description": res.get('description', ''),
                "url": res['url'],
                "thumbnail_url": res.get('thumbnail_url'),
                "duration": res.get('duration'),
                "file_size": res.get('file_size'),
                "metadata": res.get('metadata', {}),
                "order_index": res.get('order_index', idx),
                "is_active": res.get('is_active', True)
            }
            resource_data_list.append(resource_data)

        if not resource_data_list:
            return jsonify({"error": "No valid resources to insert"}), 400

        # Bulk insert
        result = kb.client.table("topic_resources").insert(resource_data_list).execute()

        return jsonify({
            "success": True,
            "created_count": len(result.data),
            "resources": result.data
        }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    """Get a specific resource by ID."""
    try:
        result = kb.client.table("topic_resources").select("*").eq("id", resource_id).execute()

        if not result.data:
            return jsonify({"error": "Resource not found"}), 404

        return jsonify(result.data[0]), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/resources/<resource_id>', methods=['PUT'])
def update_resource(resource_id):
    """
    Update a resource.

    Request body: Any fields to update (resource_type, title, url, etc.)
    """
    try:
        data = request.json

        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        # Validate resource type if provided
        if 'resource_type' in data:
            valid_types = ['video', 'image', '3d_model', 'animation', 'virtual_lab', 'pdf', 'interactive', 'article', 'simulation']
            if data['resource_type'] not in valid_types:
                return jsonify({"error": f"Invalid resource_type. Must be one of: {valid_types}"}), 400

        # Update resource
        result = kb.client.table("topic_resources").update(data).eq("id", resource_id).execute()

        if not result.data:
            return jsonify({"error": "Resource not found"}), 404

        return jsonify(result.data[0]), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/resources/<resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    """Delete a resource (soft delete by setting is_active=false)."""
    try:
        # Soft delete
        result = kb.client.table("topic_resources").update({
            "is_active": False
        }).eq("id", resource_id).execute()

        if not result.data:
            return jsonify({"error": "Resource not found"}), 404

        return jsonify({
            "success": True,
            "message": "Resource deleted successfully"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/resources/<resource_id>/permanent', methods=['DELETE'])
def permanently_delete_resource(resource_id):
    """Permanently delete a resource from the database."""
    try:
        result = kb.client.table("topic_resources").delete().eq("id", resource_id).execute()

        return jsonify({
            "success": True,
            "message": "Resource permanently deleted"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/chapters/<chapter_id>/resources', methods=['GET'])
def get_chapter_resources(chapter_id):
    """
    Get all resources for all topics under a chapter.
    Groups resources by topic.
    """
    try:
        # Verify chapter exists
        chapter = get_chapter_by_id(chapter_id)
        if not chapter:
            return jsonify({"error": "Chapter not found"}), 404

        # Get all topics for this chapter
        topics = get_topics(chapter_id)

        if not topics:
            return jsonify({
                "chapter_id": chapter_id,
                "chapter_name": chapter.get("name"),
                "topics": []
            }), 200

        # Get resources for each topic
        topic_ids = [t["id"] for t in topics]

        resources_result = kb.client.table("topic_resources").select("*").in_("topic_id", topic_ids).eq("is_active", True).order("order_index").execute()

        # Group resources by topic
        resources_by_topic = {}
        for res in resources_result.data:
            tid = res["topic_id"]
            if tid not in resources_by_topic:
                resources_by_topic[tid] = []
            resources_by_topic[tid].append(res)

        # Build response
        topic_resources = []
        for topic in topics:
            topic_resources.append({
                "topic_id": topic["id"],
                "topic_name": topic["name"],
                "topic_description": topic.get("description"),
                "resources": resources_by_topic.get(topic["id"], []),
                "resource_count": len(resources_by_topic.get(topic["id"], []))
            })

        return jsonify({
            "chapter_id": chapter_id,
            "chapter_name": chapter.get("name"),
            "topics": topic_resources,
            "total_resources": len(resources_result.data)
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================================
# IMAGE UPLOAD ENDPOINTS
# ============================================================================

@app.route('/api/questions/<question_id>/image', methods=['POST'])
def upload_question_image(question_id):
    """
    Upload an image for a question.

    Request: multipart/form-data with 'image' file
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image_file = request.files['image']

        if image_file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Upload image
        result = image_upload_service.upload_question_image(
            question_id=question_id,
            image_file=image_file.read(),
            file_name=image_file.filename
        )

        if not result['success']:
            return jsonify(result), 400

        # Update question with image URL
        kb.client.table("questions").update({
            "question_image_url": result['url']
        }).eq("id", question_id).execute()

        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/questions/<question_id>/options/<option_key>/image', methods=['POST'])
def upload_option_image(question_id, option_key):
    """
    Upload an image for a specific option.

    Request: multipart/form-data with 'image' file
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image_file = request.files['image']

        if image_file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Upload image
        result = image_upload_service.upload_option_image(
            question_id=question_id,
            option_key=option_key,
            image_file=image_file.read(),
            file_name=image_file.filename
        )

        if not result['success']:
            return jsonify(result), 400

        # Get current option_images
        question = kb.client.table("questions").select("option_images").eq("id", question_id).execute()

        if question.data:
            option_images = question.data[0].get('option_images', {})
            option_images[option_key] = result['url']

            # Update question with new option image
            kb.client.table("questions").update({
                "option_images": option_images
            }).eq("id", question_id).execute()

        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/questions/<question_id>/options/images', methods=['POST'])
def upload_multiple_option_images(question_id):
    """
    Upload multiple option images at once.

    Request: multipart/form-data with files named 'option_A', 'option_B', etc.
    """
    try:
        option_images = []

        for key in request.files:
            if key.startswith('option_'):
                option_key = key.replace('option_', '')
                image_file = request.files[key]

                option_images.append({
                    'option_key': option_key,
                    'file': image_file.read(),
                    'file_name': image_file.filename
                })

        if not option_images:
            return jsonify({"error": "No option images provided"}), 400

        # Upload all images
        result = image_upload_service.upload_multiple_option_images(
            question_id=question_id,
            option_images=option_images
        )

        # Update question with option image URLs
        option_image_urls = {}
        for res in result['results']:
            if res['success']:
                option_image_urls[res['option_key']] = res['url']

        if option_image_urls:
            kb.client.table("questions").update({
                "option_images": option_image_urls
            }).eq("id", question_id).execute()

        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/questions/<question_id>/images', methods=['DELETE'])
def delete_question_images(question_id):
    """
    Delete all images associated with a question.
    """
    try:
        result = image_upload_service.delete_all_question_images(question_id)

        if result['success']:
            # Clear image URLs from database
            kb.client.table("questions").update({
                "question_image_url": None,
                "option_images": {}
            }).eq("id", question_id).execute()

        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/storage/bucket/create', methods=['POST'])
def create_storage_bucket():
    """
    Create the storage bucket for question images (admin endpoint).
    Note: You may need to create the bucket manually in Supabase Dashboard
    if the API key doesn't have sufficient permissions.
    """
    try:
        result = image_upload_service.create_bucket_if_not_exists()
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5200)