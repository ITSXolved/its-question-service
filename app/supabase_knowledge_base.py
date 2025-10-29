"""
Supabase Knowledge Base Setup for Computer Adaptive Mastery Testing
Enhanced with hierarchical retrieval methods
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, List, Any, Optional, Union

# Load environment variables
load_dotenv()

class SupabaseKnowledgeBase:
    def __init__(self, supabase_url=None, supabase_key=None):
        """Initialize Supabase client with environment variables."""
        # Use parameters if provided, otherwise fall back to defaults
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be set in environment variables")

        self.client = create_client(self.supabase_url, self.supabase_key)

    def create_tables(self):
        """
        Create necessary tables in Supabase for knowledge base.
        This is typically done via migrations or SQL scripts in production.
        For demonstration, we show the required schema.
        """
        # Note: In production, use migrations rather than direct SQL execution

        # Define SQL queries for table creation
        create_exams_table = """
        CREATE TABLE IF NOT EXISTS exams (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_subjects_table = """
        CREATE TABLE IF NOT EXISTS subjects (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            exam_id UUID REFERENCES exams(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_chapters_table = """
        CREATE TABLE IF NOT EXISTS chapters (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_topics_table = """
        CREATE TABLE IF NOT EXISTS topics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_concepts_table = """
        CREATE TABLE IF NOT EXISTS concepts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_attributes_table = """
        CREATE TABLE IF NOT EXISTS attributes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_questions_table = """
        CREATE TABLE IF NOT EXISTS questions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            content TEXT NOT NULL,
            options JSONB,
            correct_answer TEXT,
            difficulty FLOAT,
            discrimination FLOAT,
            guessing FLOAT,  -- 3PL parameter
            exam_id UUID REFERENCES exams(id),
            subject_id UUID REFERENCES subjects(id),
            chapter_id UUID REFERENCES chapters(id),
            topic_id UUID REFERENCES topics(id),
            concept_id UUID REFERENCES concepts(id),
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        create_q_matrix_table = """
        CREATE TABLE IF NOT EXISTS q_matrix (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
            attribute_id UUID REFERENCES attributes(id) ON DELETE CASCADE,
            value BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(question_id, attribute_id)
        );
        """

        # Execute table creation
        # Note: In a real production system, use a migration framework
        # The following code is for demonstration purposes only
        tables = [
            create_exams_table,
            create_subjects_table,
            create_chapters_table,
            create_topics_table,
            create_concepts_table,
            create_attributes_table,
            create_questions_table,
            create_q_matrix_table
        ]

        # In production, replace with proper migration logic
        print("Tables would be created with appropriate migration framework")

    def add_exam(self, name, description="", exam_type="competitive"):
        """
        Add a new exam to the knowledge base.

        Args:
            name: Exam name
            description: Exam description
            exam_type: 'competitive' or 'school'
        """
        data = {
            "name": name,
            "description": description,
            "exam_type": exam_type
        }
        result = self.client.table("exams").insert(data).execute()
        return result.data

    def add_class(self, exam_id, name, description="", class_number=None, section=None):
        """
        Add a new class to a school exam.

        Args:
            exam_id: ID of the school exam
            name: Class name (e.g., 'Class 10')
            description: Class description
            class_number: Numeric class level (e.g., 10)
            section: Section identifier (e.g., 'A', 'B')
        """
        data = {
            "exam_id": exam_id,
            "name": name,
            "description": description,
            "class_number": class_number,
            "section": section
        }
        result = self.client.table("classes").insert(data).execute()
        return result.data

    def add_subject(self, name, description="", exam_id=None, class_id=None):
        """
        Add a new subject.

        For competitive exams: provide exam_id
        For school exams: provide class_id

        Args:
            name: Subject name
            description: Subject description
            exam_id: ID of exam (for competitive path)
            class_id: ID of class (for school path)
        """
        if not exam_id and not class_id:
            raise ValueError("Either exam_id or class_id must be provided")

        if exam_id and class_id:
            raise ValueError("Provide either exam_id OR class_id, not both")

        data = {
            "name": name,
            "description": description,
            "exam_id": exam_id,
            "class_id": class_id
        }
        result = self.client.table("subjects").insert(data).execute()
        return result.data

    def add_chapter(self, subject_id, name, description=""):
        """Add a new chapter to a subject."""
        data = {"subject_id": subject_id, "name": name, "description": description}
        result = self.client.table("chapters").insert(data).execute()
        return result.data

    def add_topic(self, chapter_id, name, description=""):
        """Add a new topic to a chapter."""
        data = {"chapter_id": chapter_id, "name": name, "description": description}
        result = self.client.table("topics").insert(data).execute()
        return result.data

    def add_concept(self, topic_id, name, description=""):
        """Add a new concept to a topic."""
        data = {"topic_id": topic_id, "name": name, "description": description}
        result = self.client.table("concepts").insert(data).execute()
        return result.data

    def add_attribute(self, topic_id, name, description=""):
        """Add a new attribute to a topic."""
        data = {"topic_id": topic_id, "name": name, "description": description}
        result = self.client.table("attributes").insert(data).execute()
        return result.data

    def add_question(self, content, options, correct_answer, exam_id=None, subject_id=None,
                    chapter_id=None, topic_id=None, concept_id=None,
                    difficulty=0.5, discrimination=1.0, guessing=0.25, metadata=None):
        """Add a new question with 3PL parameters."""
        data = {
            "content": content,
            "options": options,
            "correct_answer": correct_answer,
            "exam_id": exam_id,
            "subject_id": subject_id,
            "chapter_id": chapter_id,
            "topic_id": topic_id,
            "concept_id": concept_id,
            "difficulty": difficulty,
            "discrimination": discrimination,
            "guessing": guessing,
            "metadata": metadata or {}
        }
        result = self.client.table("questions").insert(data).execute()
        return result.data

    def add_q_matrix_entry(self, question_id, attribute_id, value=True):
        """Create an entry in the Q-matrix."""
        data = {
            "question_id": question_id,
            "attribute_id": attribute_id,
            "value": value
        }
        result = self.client.table("q_matrix").insert(data).execute()
        return result.data

    def get_attributes_by_topic(self, topic_id):
        """Get all attributes for a specific topic."""
        result = self.client.table("attributes").select("*").eq("topic_id", topic_id).execute()
        return result.data

    def get_attributes_by_concept(self, concept_id):
        """Get all attributes linked to a concept via its topic."""
        concept_result = self.client.table("concepts").select("topic_id").eq("id", concept_id).execute()
        if not concept_result.data:
            return []
        topic_id = concept_result.data[0].get("topic_id")
        if not topic_id:
            return []
        return self.get_attributes_by_topic(topic_id)

    def get_classes_by_exam(self, exam_id):
        """Get all classes for a school exam."""
        result = self.client.table("classes").select("*").eq("exam_id", exam_id).execute()
        return result.data

    def get_class_by_id(self, class_id):
        """Get a specific class by ID."""
        result = self.client.table("classes").select("*").eq("id", class_id).execute()
        return result.data[0] if result.data else None

    def get_subjects_by_class(self, class_id):
        """Get all subjects for a specific class (school path)."""
        result = self.client.table("subjects").select("*").eq("class_id", class_id).execute()
        return result.data

    def get_subjects_by_exam(self, exam_id):
        """Get all subjects for a specific exam (competitive path)."""
        result = self.client.table("subjects").select("*").eq("exam_id", exam_id).execute()
        return result.data

    def get_questions_by_filters(self, exam_id=None, subject_id=None, chapter_id=None,
                               topic_id=None, concept_id=None):
        """Get questions matching the specified filters."""
        query = self.client.table("questions").select("*")

        if exam_id:
            query = query.eq("exam_id", exam_id)
        if subject_id:
            query = query.eq("subject_id", subject_id)
        if chapter_id:
            query = query.eq("chapter_id", chapter_id)
        if topic_id:
            query = query.eq("topic_id", topic_id)
        if concept_id:
            query = query.eq("concept_id", concept_id)

        result = query.execute()
        return result.data

    def get_q_matrix_for_question(self, question_id):
        """Get Q-matrix entries for a specific question."""
        result = self.client.table("q_matrix") \
                .select("attribute_id, value") \
                .eq("question_id", question_id) \
                .execute()
        return result.data

    # ======== ADDED HIERARCHICAL RETRIEVAL METHODS ========

    def get_questions_by_exam(self, exam_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific exam.

        Args:
            exam_id: ID of the exam

        Returns:
            List of questions
        """
        result = self.client.table("questions").select("*").eq("exam_id", exam_id).execute()
        return result.data

    def get_questions_by_subject(self, subject_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific subject.

        Args:
            subject_id: ID of the subject

        Returns:
            List of questions
        """
        result = self.client.table("questions").select("*").eq("subject_id", subject_id).execute()
        return result.data

    def get_questions_by_chapter(self, chapter_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific chapter.

        Args:
            chapter_id: ID of the chapter

        Returns:
            List of questions
        """
        result = self.client.table("questions").select("*").eq("chapter_id", chapter_id).execute()
        return result.data

    def get_questions_by_topic(self, topic_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific topic.

        Args:
            topic_id: ID of the topic

        Returns:
            List of questions
        """
        result = self.client.table("questions").select("*").eq("topic_id", topic_id).execute()
        return result.data

    def get_questions_by_concept(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific concept.

        Args:
            concept_id: ID of the concept

        Returns:
            List of questions
        """
        result = self.client.table("questions").select("*").eq("concept_id", concept_id).execute()
        return result.data

    def get_questions_with_details(self,
                                 hierarchy_level: str,
                                 item_id: str,
                                 with_attributes: bool = False) -> List[Dict[str, Any]]:
        """
        Get questions with detailed hierarchical information for a specific item at any level.

        Args:
            hierarchy_level: One of 'exam', 'subject', 'chapter', 'topic', 'concept'
            item_id: ID of the item at the specified level
            with_attributes: Whether to include attribute information

        Returns:
            List of questions with detailed hierarchical information
        """
        # Validate hierarchy level
        valid_levels = ['exam', 'subject', 'chapter', 'topic', 'concept']
        if hierarchy_level not in valid_levels:
            raise ValueError(f"Invalid hierarchy level. Must be one of: {valid_levels}")

        # Build select statement
        select_statement = """
            *,
            exams:exam_id (id, name, description),
            subjects:subject_id (id, name, description),
            chapters:chapter_id (id, name, description),
            topics:topic_id (id, name, description),
            concepts:concept_id (id, name, description)
        """

        # Build query
        query = self.client.table("questions").select(select_statement)

        # Apply filter based on hierarchy level
        if hierarchy_level == 'exam':
            query = query.eq("exam_id", item_id)
        elif hierarchy_level == 'subject':
            query = query.eq("subject_id", item_id)
        elif hierarchy_level == 'chapter':
            query = query.eq("chapter_id", item_id)
        elif hierarchy_level == 'topic':
            query = query.eq("topic_id", item_id)
        elif hierarchy_level == 'concept':
            query = query.eq("concept_id", item_id)

        # Execute query
        result = query.execute()
        questions = result.data

        # If attributes are requested, fetch them for each question
        if with_attributes and questions:
            for question in questions:
                q_matrix = self.get_q_matrix_for_question(question["id"])

                # Get attribute IDs that are true in the Q-matrix
                attribute_ids = [entry["attribute_id"] for entry in q_matrix if entry["value"]]

                # Fetch attribute details if there are any
                if attribute_ids:
                    attr_result = self.client.table("attributes") \
                        .select("id, name, description, topic_id") \
                        .in_("id", attribute_ids) \
                        .execute()

                    question["attributes"] = attr_result.data
                else:
                    question["attributes"] = []

        return questions

    def get_hierarchy_chain(self,
                          hierarchy_level: str,
                          item_id: str) -> Dict[str, Any]:
        """
        Get the complete hierarchy chain for an item at any level.
        For example, if you provide a topic_id, it will return the topic, its parent chapter,
        the chapter's parent subject, and the subject's parent exam.

        Args:
            hierarchy_level: One of 'exam', 'subject', 'chapter', 'topic', 'concept'
            item_id: ID of the item at the specified level

        Returns:
            Dictionary with the complete hierarchy chain
        """
        # Validate hierarchy level
        valid_levels = ['exam', 'subject', 'chapter', 'topic', 'concept']
        if hierarchy_level not in valid_levels:
            raise ValueError(f"Invalid hierarchy level. Must be one of: {valid_levels}")

        hierarchy = {}

        # Base case: exam level
        if hierarchy_level == 'exam':
            result = self.client.table("exams").select("*").eq("id", item_id).execute()
            if result.data:
                hierarchy["exam"] = result.data[0]

            return hierarchy

        # Get the immediate item
        result = self.client.table(hierarchy_level + "s").select("*").eq("id", item_id).execute()
        if not result.data:
            return hierarchy

        hierarchy[hierarchy_level] = result.data[0]

        # Handle each level
        if hierarchy_level == 'subject':
            # Get parent exam
            exam_id = result.data[0].get("exam_id")
            if exam_id:
                exam_result = self.client.table("exams").select("*").eq("id", exam_id).execute()
                if exam_result.data:
                    hierarchy["exam"] = exam_result.data[0]

        elif hierarchy_level == 'chapter':
            # Get parent subject
            subject_id = result.data[0].get("subject_id")
            if subject_id:
                subject_result = self.client.table("subjects").select("*").eq("id", subject_id).execute()
                if subject_result.data:
                    hierarchy["subject"] = subject_result.data[0]

                    # Get parent exam
                    exam_id = subject_result.data[0].get("exam_id")
                    if exam_id:
                        exam_result = self.client.table("exams").select("*").eq("id", exam_id).execute()
                        if exam_result.data:
                            hierarchy["exam"] = exam_result.data[0]

        elif hierarchy_level == 'topic':
            # Get parent chapter
            chapter_id = result.data[0].get("chapter_id")
            if chapter_id:
                chapter_result = self.client.table("chapters").select("*").eq("id", chapter_id).execute()
                if chapter_result.data:
                    hierarchy["chapter"] = chapter_result.data[0]

                    # Get parent subject
                    subject_id = chapter_result.data[0].get("subject_id")
                    if subject_id:
                        subject_result = self.client.table("subjects").select("*").eq("id", subject_id).execute()
                        if subject_result.data:
                            hierarchy["subject"] = subject_result.data[0]

                            # Get parent exam
                            exam_id = subject_result.data[0].get("exam_id")
                            if exam_id:
                                exam_result = self.client.table("exams").select("*").eq("id", exam_id).execute()
                                if exam_result.data:
                                    hierarchy["exam"] = exam_result.data[0]

        elif hierarchy_level == 'concept':
            # Get parent topic
            topic_id = result.data[0].get("topic_id")
            if topic_id:
                topic_result = self.client.table("topics").select("*").eq("id", topic_id).execute()
                if topic_result.data:
                    hierarchy["topic"] = topic_result.data[0]

                    # Get parent chapter
                    chapter_id = topic_result.data[0].get("chapter_id")
                    if chapter_id:
                        chapter_result = self.client.table("chapters").select("*").eq("id", chapter_id).execute()
                        if chapter_result.data:
                            hierarchy["chapter"] = chapter_result.data[0]

                            # Get parent subject
                            subject_id = chapter_result.data[0].get("subject_id")
                            if subject_id:
                                subject_result = self.client.table("subjects").select("*").eq("id", subject_id).execute()
                                if subject_result.data:
                                    hierarchy["subject"] = subject_result.data[0]

                                    # Get parent exam
                                    exam_id = subject_result.data[0].get("exam_id")
                                    if exam_id:
                                        exam_result = self.client.table("exams").select("*").eq("id", exam_id).execute()
                                        if exam_result.data:
                                            hierarchy["exam"] = exam_result.data[0]

        return hierarchy

    def get_children(self, hierarchy_level: str, item_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all direct children of an item at any level.
        For example, if you provide an exam_id, it will return all subjects in that exam.

        Args:
            hierarchy_level: One of 'exam', 'subject', 'chapter', 'topic', 'concept'
            item_id: ID of the item at the specified level

        Returns:
            Dictionary with lists of children items
        """
        # Validate hierarchy level
        valid_levels = ['exam', 'subject', 'chapter', 'topic', 'concept']
        if hierarchy_level not in valid_levels:
            raise ValueError(f"Invalid hierarchy level. Must be one of: {valid_levels}")

        children = {}

        # Different handling based on hierarchy level
        if hierarchy_level == 'exam':
            # Get subjects in this exam
            subjects_result = self.client.table("subjects").select("*").eq("exam_id", item_id).execute()
            children["subjects"] = subjects_result.data

        elif hierarchy_level == 'subject':
            # Get chapters in this subject
            chapters_result = self.client.table("chapters").select("*").eq("subject_id", item_id).execute()
            children["chapters"] = chapters_result.data

        elif hierarchy_level == 'chapter':
            # Get topics in this chapter
            topics_result = self.client.table("topics").select("*").eq("chapter_id", item_id).execute()
            children["topics"] = topics_result.data

        elif hierarchy_level == 'topic':
            # Get concepts in this topic
            concepts_result = self.client.table("concepts").select("*").eq("topic_id", item_id).execute()
            children["concepts"] = concepts_result.data

            # Get attributes for this topic (direct relationship)
            attributes_result = self.client.table("attributes").select("*").eq("topic_id", item_id).execute()
            children["attributes"] = attributes_result.data

        elif hierarchy_level == 'concept':
            # Concepts no longer have attributes (now linked to topics)
            children["attributes"] = []

        # Get questions for this item at any level
        questions = self.get_questions_by_filters(
            exam_id=item_id if hierarchy_level == 'exam' else None,
            subject_id=item_id if hierarchy_level == 'subject' else None,
            chapter_id=item_id if hierarchy_level == 'chapter' else None,
            topic_id=item_id if hierarchy_level == 'topic' else None,
            concept_id=item_id if hierarchy_level == 'concept' else None
        )
        children["questions"] = questions

        return children


    def get_questions_by_hierarchy(self,
                              hierarchy_level: str,
                              item_id: str,
                              with_details: bool = False,
                              with_attributes: bool = False,
                              page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        """
        Get questions by hierarchy level with pagination and optional details.
        """
        # Validate hierarchy level
        valid_levels = ['exam', 'subject', 'chapter', 'topic', 'concept']
        if hierarchy_level not in valid_levels:
            raise ValueError(f"Invalid hierarchy level. Must be one of: {valid_levels}")

        # Build select statement
        if with_details:
            select_statement = """
                *,
                exams:exam_id (id, name, description),
                subjects:subject_id (id, name, description),
                chapters:chapter_id (id, name, description),
                topics:topic_id (id, name, description),
                concepts:concept_id (id, name, description)
            """
        else:
            select_statement = "*"

        # Build query
        query = self.client.table("questions").select(select_statement)

        # Apply filter based on hierarchy level
        if hierarchy_level == 'exam':
            query = query.eq("exam_id", item_id)
        elif hierarchy_level == 'subject':
            query = query.eq("subject_id", item_id)
        elif hierarchy_level == 'chapter':
            query = query.eq("chapter_id", item_id)
        elif hierarchy_level == 'topic':
            query = query.eq("topic_id", item_id)
        elif hierarchy_level == 'concept':
            query = query.eq("concept_id", item_id)

        # Get all results first (not efficient for large datasets)
        all_results = query.execute()
        total_count = len(all_results.data)

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        # Apply pagination manually
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        questions = all_results.data[start_idx:end_idx]

        # If attributes are requested, fetch them for each question
        if with_attributes and questions:
            for question in questions:
                q_matrix = self.get_q_matrix_for_question(question["id"])

                # Get attribute IDs that are true in the Q-matrix
                attribute_ids = [entry["attribute_id"] for entry in q_matrix if entry["value"]]

                # Fetch attribute details if there are any
                if attribute_ids:
                    attr_result = self.client.table("attributes") \
                        .select("id, name, description, topic_id") \
                        .in_("id", attribute_ids) \
                        .execute()

                    question["attributes"] = attr_result.data
                else:
                    question["attributes"] = []

        return {
            "data": questions,
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
        }

    # kb.create_tables()  # Only run once during initial setup