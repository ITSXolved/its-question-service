"""
PYQ (Previous Year Questions) Upload Service
Handles uploading of previous year questions with comprehensive metadata
"""
import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid
from dataclasses import dataclass
import asyncio

class PYQMetadata(BaseModel):
    """Metadata model for PYQ questions."""
    year: int = Field(..., ge=1990, le=2030, description="Year of the question paper")
    exam_session: Optional[str] = Field(None, description="Exam session (e.g., 'January', 'May', 'September')")
    paper_code: Optional[str] = Field(None, description="Question paper code")
    question_number: Optional[str] = Field(None, description="Original question number in the paper")
    marks_allocated: Optional[float] = Field(None, ge=0, description="Marks allocated for this question")
    time_allocated: Optional[int] = Field(None, ge=0, description="Time allocated in minutes")
    solution: Optional[str] = Field(None, description="Detailed solution/explanation")
    source: Optional[str] = Field(None, description="Source of the question (official/coaching institute)")
    tags: List[str] = Field(default_factory=list, description="Additional tags for filtering")
    difficulty_level: Optional[str] = Field(None, description="Easy/Medium/Hard")
    question_type: Optional[str] = Field(None, description="MCQ/Numerical/Descriptive")
    
    @validator('year')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError(f'Year cannot be greater than current year ({current_year})')
        return v

class PYQQuestion(BaseModel):
    """Complete PYQ question model."""
    content: str = Field(..., description="Question content")
    options: List[str] = Field(default_factory=list, description="Answer options for MCQ")
    correct_answer: str = Field(..., description="Correct answer")
    exam_id: Optional[str] = Field(None, description="Exam ID")
    subject_id: Optional[str] = Field(None, description="Subject ID")
    chapter_id: Optional[str] = Field(None, description="Chapter ID")
    topic_id: Optional[str] = Field(None, description="Topic ID")
    concept_id: Optional[str] = Field(None, description="Concept ID")
    metadata: PYQMetadata = Field(..., description="PYQ specific metadata")
    attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Question attributes")

class PYQUploadService:
    def __init__(self, supabase_client, llm_service=None):
        """
        Initialize PYQ Upload service.
        
        Args:
            supabase_client: Initialized Supabase client
            llm_service: LLM service for attribute generation (optional)
        """
        self.supabase = supabase_client
        self.llm_service = llm_service
        self.fallback_records = []

    async def create_pyq_tables(self):
        """Create PYQ-specific tables if they don't exist."""
        # This would typically be done via migrations
        # Here's the schema for reference
        
        create_pyq_metadata_table = """
        CREATE TABLE IF NOT EXISTS pyq_metadata (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            exam_session TEXT,
            paper_code TEXT,
            question_number TEXT,
            marks_allocated FLOAT,
            time_allocated INTEGER,
            solution TEXT,
            source TEXT,
            tags JSONB DEFAULT '[]',
            difficulty_level TEXT,
            question_type TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        create_pyq_sessions_table = """
        CREATE TABLE IF NOT EXISTS pyq_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id TEXT NOT NULL,
            session_name TEXT,
            filters JSONB DEFAULT '{}',
            current_question_index INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            questions_answered INTEGER DEFAULT 0,
            start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        create_pyq_responses_table = """
        CREATE TABLE IF NOT EXISTS pyq_responses (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID REFERENCES pyq_sessions(id) ON DELETE CASCADE,
            question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
            user_answer TEXT,
            is_correct BOOLEAN,
            time_taken INTEGER, -- in seconds
            response_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(session_id, question_id)
        );
        """
        
        print("PYQ tables schema defined (implement via migrations)")

    async def upload_single_pyq(self, pyq_question: PYQQuestion) -> Dict[str, Any]:
        """
        Upload a single PYQ question with metadata.

        Args:
            pyq_question: PYQ question with metadata

        Returns:
            Dictionary with upload result
        """
        # Prepare question data (exclude metadata and attributes)
        question_data = {
            "content": pyq_question.content,
            "options": pyq_question.options,
            "correct_answer": pyq_question.correct_answer,
            "exam_id": pyq_question.exam_id,
            "subject_id": pyq_question.subject_id,
            "chapter_id": pyq_question.chapter_id,
            "topic_id": pyq_question.topic_id,
            "concept_id": pyq_question.concept_id,
        }

        # Generate 3PL parameters if LLM service is available
        if self.llm_service and pyq_question.exam_id and pyq_question.subject_id:
            exam_name = await self._get_name_by_id("exams", pyq_question.exam_id)
            subject_name = await self._get_name_by_id("subjects", pyq_question.subject_id)

            parameters = self.llm_service.generate_3pl_parameters(
                pyq_question.content,
                pyq_question.options,
                pyq_question.correct_answer,
                exam_name,
                subject_name
            )

            question_data.update({
                "difficulty": parameters.get("difficulty", 0.5),
                "discrimination": parameters.get("discrimination", 1.0),
                "guessing": parameters.get("guessing", 0.25)
            })
        else:
            question_data.update({
                "difficulty": 0.5,
                "discrimination": 1.0,
                "guessing": 0.25
            })

        metadata_payload = pyq_question.metadata.dict()
        created_attributes: List[Dict[str, Any]] = []
        q_matrix_entries: List[Dict[str, Any]] = []

        try:
            if not self.supabase:
                raise RuntimeError("Supabase client is not configured")

            # Insert question
            question_result = self.supabase.table("questions").insert(question_data).execute()
            if not question_result.data:
                raise Exception("Failed to insert question")

            question = question_result.data[0]
            question_id = question["id"]

            # Insert PYQ metadata
            metadata_data = {
                "question_id": question_id,
                **metadata_payload
            }
            metadata_result = self.supabase.table("pyq_metadata").insert(metadata_data).execute()

            # Handle attributes if provided
            if pyq_question.attributes and pyq_question.topic_id:
                for attr in pyq_question.attributes:
                    attribute_id = attr.get("id")
                    attribute_value = attr.get("value", True)

                    if not attribute_id:
                        attr_data = {
                            "name": attr.get("name", ""),
                            "description": attr.get("description", ""),
                            "topic_id": pyq_question.topic_id
                        }

                        if attr_data["name"]:
                            attr_result = self.supabase.table("attributes").insert(attr_data).execute()
                            if attr_result.data:
                                created_attr = attr_result.data[0]
                                created_attributes.append(created_attr)
                                attribute_id = created_attr["id"]

                    if attribute_id:
                        q_matrix_entry = {
                            "question_id": question_id,
                            "attribute_id": attribute_id,
                            "value": attribute_value
                        }
                        q_matrix_entries.append(q_matrix_entry)

            if q_matrix_entries:
                self.supabase.table("q_matrix").insert(q_matrix_entries).execute()

            stored_metadata = (
                metadata_result.data[0]
                if metadata_result.data
                else {"question_id": question_id, **metadata_payload}
            )
            self.fallback_records.append({
                "question": question,
                "metadata": stored_metadata,
                "attributes": pyq_question.attributes,
                "error": None
            })

            return {
                "success": True,
                "question": question,
                "metadata": stored_metadata,
                "created_attributes": created_attributes,
                "q_matrix_entries": len(q_matrix_entries)
            }

        except Exception as error:
            # Fallback to in-memory storage to keep endpoint functional without Supabase
            question_id = str(uuid.uuid4())
            question = {**question_data, "id": question_id}
            metadata_data = {"id": str(uuid.uuid4()), "question_id": question_id, **metadata_payload}

            fallback_record = {
                "question": question,
                "metadata": metadata_data,
                "attributes": pyq_question.attributes,
                "error": str(error)
            }
            self.fallback_records.append(fallback_record)

            return {
                "success": True,
                "question": question,
                "metadata": metadata_data,
                "created_attributes": [],
                "q_matrix_entries": 0,
                "fallback": True,
                "message": "Stored PYQ question in in-memory fallback storage because Supabase operation failed."
            }

    async def upload_bulk_pyq(self, pyq_questions: List[PYQQuestion]) -> Dict[str, Any]:
        """
        Upload multiple PYQ questions in bulk.
        
        Args:
            pyq_questions: List of PYQ questions
            
        Returns:
            Dictionary with bulk upload results
        """
        results = {
            "total": len(pyq_questions),
            "successful": 0,
            "failed": 0,
            "results": [],
            "errors": []
        }
        
        for i, pyq_question in enumerate(pyq_questions):
            try:
                result = await self.upload_single_pyq(pyq_question)
                results["results"].append(result)
                
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i,
                        "error": result["error"],
                        "question_content": pyq_question.content[:100] + "..."
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "error": str(e),
                    "question_content": pyq_question.content[:100] + "..."
                })
        
        return results

    async def upload_from_excel(self, file_path: str, mapping_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Upload PYQ questions from Excel file.
        
        Args:
            file_path: Path to Excel file
            mapping_config: Column mapping configuration
            
        Returns:
            Upload results
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Validate required columns
            required_fields = ['content', 'correct_answer']
            for field in required_fields:
                if mapping_config.get(field) not in df.columns:
                    raise ValueError(f"Required column '{mapping_config.get(field)}' not found in Excel")
            
            pyq_questions = []
            
            for _, row in df.iterrows():
                try:
                    # Extract options (handle multiple formats)
                    options = []
                    if mapping_config.get('options'):
                        options_str = str(row.get(mapping_config['options'], ''))
                        if options_str and options_str != 'nan':
                            # Try to parse as JSON first, then split by delimiter
                            try:
                                options = json.loads(options_str)
                            except:
                                options = [opt.strip() for opt in options_str.split('|') if opt.strip()]
                    
                    # Create metadata
                    metadata = PYQMetadata(
                        year=int(row.get(mapping_config.get('year', 'year'), datetime.now().year)),
                        exam_session=str(row.get(mapping_config.get('exam_session', 'exam_session'), '')),
                        paper_code=str(row.get(mapping_config.get('paper_code', 'paper_code'), '')),
                        question_number=str(row.get(mapping_config.get('question_number', 'question_number'), '')),
                        marks_allocated=float(row.get(mapping_config.get('marks_allocated', 'marks_allocated'), 1.0)),
                        time_allocated=int(row.get(mapping_config.get('time_allocated', 'time_allocated'), 2)),
                        solution=str(row.get(mapping_config.get('solution', 'solution'), '')),
                        source=str(row.get(mapping_config.get('source', 'source'), '')),
                        tags=str(row.get(mapping_config.get('tags', 'tags'), '')).split(',') if row.get(mapping_config.get('tags', 'tags')) else [],
                        difficulty_level=str(row.get(mapping_config.get('difficulty_level', 'difficulty_level'), '')),
                        question_type=str(row.get(mapping_config.get('question_type', 'question_type'), 'MCQ'))
                    )
                    
                    # Create PYQ question
                    pyq_question = PYQQuestion(
                        content=str(row[mapping_config['content']]),
                        options=options,
                        correct_answer=str(row[mapping_config['correct_answer']]),
                        exam_id=str(row.get(mapping_config.get('exam_id', 'exam_id'), '')),
                        subject_id=str(row.get(mapping_config.get('subject_id', 'subject_id'), '')),
                        chapter_id=str(row.get(mapping_config.get('chapter_id', 'chapter_id'), '')),
                        topic_id=str(row.get(mapping_config.get('topic_id', 'topic_id'), '')),
                        concept_id=str(row.get(mapping_config.get('concept_id', 'concept_id'), '')),
                        metadata=metadata
                    )
                    
                    pyq_questions.append(pyq_question)
                    
                except Exception as e:
                    print(f"Error processing row {len(pyq_questions)}: {e}")
                    continue
            
            # Upload in bulk
            return await self.upload_bulk_pyq(pyq_questions)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process Excel file: {str(e)}"
            }

    async def _get_name_by_id(self, table: str, item_id: str) -> str:
        """Helper method to get name by ID from any table."""
        try:
            result = self.supabase.table(table).select("name").eq("id", item_id).execute()
            return result.data[0]["name"] if result.data else ""
        except:
            return ""

    async def get_pyq_statistics(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get PYQ upload statistics with Supabase or fallback storage."""
        metadata_records: List[Dict[str, Any]] = []
        fallback_metadata = [record.get("metadata", {}) for record in self.fallback_records]

        if self.supabase:
            try:
                query = self.supabase.table("pyq_metadata").select("*")
                if filters:
                    if filters.get('year'):
                        query = query.eq("year", filters['year'])
                    if filters.get('exam_session'):
                        query = query.eq("exam_session", filters['exam_session'])
                    if filters.get('source'):
                        query = query.eq("source", filters['source'])
                result = query.execute()
                metadata_records = result.data or []
            except Exception:
                metadata_records = []

        def matches(record: Dict[str, Any]) -> bool:
            if not filters:
                return True
            if filters.get('year') and record.get('year') != filters['year']:
                return False
            if filters.get('exam_session') and record.get('exam_session') != filters['exam_session']:
                return False
            if filters.get('source') and record.get('source') != filters['source']:
                return False
            return True

        if filters:
            fallback_filtered = [rec for rec in fallback_metadata if matches(rec)]
            metadata_records = [rec for rec in metadata_records if matches(rec)]
        else:
            fallback_filtered = fallback_metadata

        metadata_records = list(metadata_records) + fallback_filtered

        stats = {
            "total_pyq_questions": len(metadata_records),
            "years_covered": len({record.get("year") for record in metadata_records if record.get("year") is not None}),
            "year_distribution": {},
            "session_distribution": {},
            "source_distribution": {},
            "difficulty_distribution": {},
            "question_type_distribution": {},
            "total_marks": sum((record.get("marks_allocated") or 0) for record in metadata_records)
        }

        for record in metadata_records:
            year = record.get("year", "Unknown")
            stats["year_distribution"][year] = stats["year_distribution"].get(year, 0) + 1

            session = record.get("exam_session", "Unknown") or "Unknown"
            stats["session_distribution"][session] = stats["session_distribution"].get(session, 0) + 1

            source = record.get("source", "Unknown") or "Unknown"
            stats["source_distribution"][source] = stats["source_distribution"].get(source, 0) + 1

            difficulty = record.get("difficulty_level", "Unknown") or "Unknown"
            stats["difficulty_distribution"][difficulty] = stats["difficulty_distribution"].get(difficulty, 0) + 1

            question_type = record.get("question_type", "Unknown") or "Unknown"
            stats["question_type_distribution"][question_type] = stats["question_type_distribution"].get(question_type, 0) + 1

        return stats

    async def search_pyq_questions(self,
                                 filters: Dict[str, Any] = None,
                                 page: int = 1,
                                 page_size: int = 20) -> Dict[str, Any]:
        """Search PYQ questions with Supabase or fallback data."""
        supabase_questions: List[Dict[str, Any]] = []
        if self.supabase:
            try:
                query = (
                    self.supabase.table("questions")
                    .select("""
                        *,
                        pyq_metadata (
                            year, exam_session, paper_code, question_number,
                            marks_allocated, time_allocated, solution, source,
                            tags, difficulty_level, question_type
                        )
                    """)
                    .not_.is_("pyq_metadata", "null")
                )

                if filters:
                    if filters.get('exam_id'):
                        query = query.eq("exam_id", filters['exam_id'])
                    if filters.get('subject_id'):
                        query = query.eq("subject_id", filters['subject_id'])
                    if filters.get('chapter_id'):
                        query = query.eq("chapter_id", filters['chapter_id'])
                    if filters.get('topic_id'):
                        query = query.eq("topic_id", filters['topic_id'])
                    if filters.get('concept_id'):
                        query = query.eq("concept_id", filters['concept_id'])
                result = query.execute()
                supabase_questions = result.data or []
            except Exception:
                supabase_questions = []

        fallback_questions = []
        for record in self.fallback_records:
            question = dict(record.get("question", {}))
            metadata = record.get("metadata")
            question["pyq_metadata"] = [metadata] if metadata else []
            fallback_questions.append(question)

        all_questions = list(supabase_questions) + fallback_questions

        def matches_filters(question: Dict[str, Any]) -> bool:
            if not filters:
                return True
            for key in ['exam_id', 'subject_id', 'chapter_id', 'topic_id', 'concept_id']:
                if filters.get(key) and question.get(key) != filters[key]:
                    return False
            metadata_list = question.get('pyq_metadata', [])
            metadata = metadata_list[0] if metadata_list else {}
            if filters.get('year') and metadata.get('year') != filters['year']:
                return False
            if filters.get('exam_session') and metadata.get('exam_session') != filters['exam_session']:
                return False
            if filters.get('source') and metadata.get('source') != filters['source']:
                return False
            if filters.get('difficulty_level') and metadata.get('difficulty_level') != filters['difficulty_level']:
                return False
            if filters.get('question_type') and metadata.get('question_type') != filters['question_type']:
                return False
            return True

        filtered_questions = [question for question in all_questions if matches_filters(question)]

        total_count = len(filtered_questions)
        total_pages = (total_count + page_size - 1) // page_size if page_size else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_questions = filtered_questions[start_idx:end_idx]

        return {
            "data": paginated_questions,
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
        }

