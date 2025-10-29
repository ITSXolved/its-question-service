"""
Item Bank Retrieval Service for Computer Adaptive Mastery Testing
Facilitates searching and retrieving questions from Supabase
"""
import os
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
import asyncio
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field



# Load environment variables
load_dotenv()

# Define Pydantic models for data validation
class QuestionFilter(BaseModel):
    """Filter parameters for question retrieval."""
    exam_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None
    difficulty_min: Optional[float] = None
    difficulty_max: Optional[float] = None
    text_search: Optional[str] = None

class QuestionResponse(BaseModel):
    """Response model for a question with its attributes."""
    id: str
    content: str
    options: Dict[str, str] = Field(default_factory=dict)
    correct_answer: str
    difficulty: float
    discrimination: float
    guessing: float
    exam_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attributes: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str

class ItemBankService:
    def __init__(self, supabase_client=None):
        """
        Initialize the Item Bank service.

        Args:
            supabase_client: Initialized Supabase client
        """
        if supabase_client:
            self.supabase = supabase_client
        else:
            # Initialize Supabase client if not provided
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError("Supabase URL and key must be set in environment variables")

            from supabase import create_client, Client
            self.supabase = create_client(supabase_url, supabase_key)

    async def search_questions(self, filters: QuestionFilter, page: int = 1,
                    page_size: int = 20) -> Dict[str, Any]:
            """
            Search for questions based on filters with pagination.

            Args:
                filters: Search filters
                page: Page number (starting from 1)
                page_size: Number of items per page

            Returns:
                Dictionary with results and pagination info
            """
            # Start building the query for counting
            count_query = self.supabase.table("questions").select("*", count="exact")

            # Start building the query for data
            data_query = self.supabase.table("questions").select("*")

            # Apply filters to both queries
            for query in [count_query, data_query]:
                if filters.exam_id:
                    query = query.eq("exam_id", filters.exam_id)
                if filters.subject_id:
                    query = query.eq("subject_id", filters.subject_id)
                if filters.chapter_id:
                    query = query.eq("chapter_id", filters.chapter_id)
                if filters.topic_id:
                    query = query.eq("topic_id", filters.topic_id)
                if filters.concept_id:
                    query = query.eq("concept_id", filters.concept_id)

                # Apply difficulty range if provided
                if filters.difficulty_min is not None:
                    query = query.gte("difficulty", filters.difficulty_min)
                if filters.difficulty_max is not None:
                    query = query.lte("difficulty", filters.difficulty_max)

                # Apply text search if provided - CHANGED THIS PART
                if filters.text_search:
                    query = query.ilike("content", f"%{filters.text_search}%")

            # Execute count query
            count_result = count_query.execute()
            total_count = count_result.count

            # Apply pagination to data query
            data_query = data_query.range((page - 1) * page_size, page * page_size - 1)

            # Execute data query
            result = data_query.execute()
            questions = result.data

            # Calculate pagination details
            total_pages = (total_count + page_size - 1) // page_size

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

    async def get_question_with_attributes(self, question_id: str) -> Optional[QuestionResponse]:
        """
        Get a question by ID with its associated attributes.

        Args:
            question_id: ID of the question

        Returns:
            Question with attributes or None if not found
        """
        # Get the question
        result = self.supabase.table("questions").select("*").eq("id", question_id).execute()

        if not result.data:
            return None

        question = result.data[0]

        # Get q-matrix entries for this question
        q_matrix_result = self.supabase.table("q_matrix") \
            .select("attribute_id, value") \
            .eq("question_id", question_id) \
            .execute()

        q_matrix_entries = q_matrix_result.data

        # Get attribute details for the attributes in the q-matrix
        attribute_ids = [entry["attribute_id"] for entry in q_matrix_entries if entry["value"]]

        attributes = []
        if attribute_ids:
            attrs_result = self.supabase.table("attributes") \
                .select("id, name, description, topic_id") \
                .in_("id", attribute_ids) \
                .execute()

            attributes = attrs_result.data

        # Combine question with attributes
        question_response = QuestionResponse(
            **question,
            attributes=attributes
        )

        return question_response

    async def get_item_bank(self, filters: QuestionFilter) -> Dict[str, Any]:
        """
        Get a complete item bank based on filters, including q-matrix.

        Args:
            filters: Search filters

        Returns:
            Dictionary with questions, attributes, and q-matrix
        """
        # Get questions
        query = self.supabase.table("questions").select("*")

        # Apply filters
        if filters.exam_id:
            query = query.eq("exam_id", filters.exam_id)
        if filters.subject_id:
            query = query.eq("subject_id", filters.subject_id)
        if filters.chapter_id:
            query = query.eq("chapter_id", filters.chapter_id)
        if filters.topic_id:
            query = query.eq("topic_id", filters.topic_id)
        if filters.concept_id:
            query = query.eq("concept_id", filters.concept_id)

        # Execute query
        result = query.execute()
        questions = result.data

        if not questions:
            return {
                "questions": [],
                "attributes": [],
                "q_matrix": [],
                "q_matrix_array": np.array([])
            }

        # Get question IDs
        question_ids = [q["id"] for q in questions]

        # Get q-matrix entries for these questions
        q_matrix_result = self.supabase.table("q_matrix") \
            .select("question_id, attribute_id, value") \
            .in_("question_id", question_ids) \
            .execute()

        q_matrix_entries = q_matrix_result.data

        # Get attribute IDs from q-matrix
        attribute_ids = list(set([entry["attribute_id"] for entry in q_matrix_entries]))

        # Get attribute details
        attributes = []
        if attribute_ids:
            attrs_result = self.supabase.table("attributes") \
                .select("id, name, description, topic_id") \
                .in_("id", attribute_ids) \
                .execute()

            attributes = attrs_result.data

        # Convert to EduCDM compatible format
        q_matrix_array = self._convert_to_q_matrix_array(questions, attributes, q_matrix_entries)

        return {
            "questions": questions,
            "attributes": attributes,
            "q_matrix": q_matrix_entries,
            "q_matrix_array": q_matrix_array
        }

    def _convert_to_q_matrix_array(self,
                                 questions: List[Dict[str, Any]],
                                 attributes: List[Dict[str, Any]],
                                 q_matrix_entries: List[Dict[str, Any]]) -> np.ndarray:
        """
        Convert Q-matrix entries to a numpy array for EduCDM.

        Args:
            questions: List of questions
            attributes: List of attributes
            q_matrix_entries: List of Q-matrix entries

        Returns:
            NumPy array representing the Q-matrix
        """
        # Create empty Q-matrix
        q_matrix = np.zeros((len(questions), len(attributes)))

        # Map IDs to indices
        question_index = {q["id"]: i for i, q in enumerate(questions)}
        attribute_index = {a["id"]: j for j, a in enumerate(attributes)}

        # Fill Q-matrix
        for entry in q_matrix_entries:
            q_idx = question_index.get(entry["question_id"])
            a_idx = attribute_index.get(entry["attribute_id"])

            if q_idx is not None and a_idx is not None:
                q_matrix[q_idx, a_idx] = 1 if entry["value"] else 0

        return q_matrix

    async def get_response_pattern(self,
                               user_id: str,
                               session_id: str,
                               item_bank: Dict[str, Any]) -> np.ndarray:
        """
        Get a user's response pattern for an item bank.

        Args:
            user_id: ID of the user
            session_id: ID of the assessment session
            item_bank: Item bank dictionary with questions and attributes

        Returns:
            NumPy array of user responses (1=correct, 0=incorrect, NaN=not answered)
        """
        # Get user responses from the database
        # This assumes you have a "responses" table in your database
        # that stores user responses to questions
        result = self.supabase.table("responses") \
            .select("question_id, is_correct") \
            .eq("user_id", user_id) \
            .eq("session_id", session_id) \
            .execute()

        responses = result.data

        # Create response pattern
        questions = item_bank["questions"]
        response_pattern = np.full(len(questions), np.nan)

        # Map question IDs to indices
        question_index = {q["id"]: i for i, q in enumerate(questions)}

        # Fill response pattern
        for response in responses:
            q_idx = question_index.get(response["question_id"])

            if q_idx is not None:
                response_pattern[q_idx] = 1 if response["is_correct"] else 0

        return response_pattern

    async def export_educdm_data(self, filters: QuestionFilter) -> Dict[str, Any]:
        """
        Export data in a format compatible with EduCDM.

        Args:
            filters: Search filters

        Returns:
            Dictionary with data formatted for EduCDM
        """
        # Get item bank
        item_bank = await self.get_item_bank(filters)

        questions = item_bank["questions"]
        attributes = item_bank["attributes"]
        q_matrix = item_bank["q_matrix_array"]

        # Format for EduCDM
        educdm_data = {
            "Q": q_matrix,
            "item_ids": [q["id"] for q in questions],
            "attribute_ids": [a["id"] for a in attributes],
            "attribute_names": [a["name"] for a in attributes],
        }

        return educdm_data

    async def search_hierarchical_structure(self, query: str, level: str) -> List[Dict[str, Any]]:
            """
            Search for items in the hierarchical structure.

            Args:
                query: Search query
                level: Level to search (exams, subjects, chapters, topics, concepts)

            Returns:
                List of matching items
            """
            # Validate level
            valid_levels = ["exams", "subjects", "chapters", "topics", "concepts"]
            if level not in valid_levels:
                raise ValueError(f"Invalid level. Must be one of: {valid_levels}")

            # Build query
            search_query = self.supabase.table(level).select("*")

            # Apply text search if provided
            if query:
                # Use ilike instead of textSearch
                # This does a case-insensitive LIKE operation with % wildcards
                search_query = search_query.ilike("name", f"%{query}%")

            # Execute query
            result = search_query.execute()
            return result.data
