"""
PYQ Retriever Service
Handles sequential retrieval of PYQ questions with session management
"""
import os
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
from enum import Enum

class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"

class QuestionStatus(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    ATTEMPTED = "attempted" 
    CORRECT = "correct"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"

class PYQSessionFilter(BaseModel):
    """Filter model for PYQ sessions."""
    exam_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None
    year: Optional[int] = None
    year_range: Optional[Tuple[int, int]] = None
    exam_session: Optional[str] = None
    source: Optional[str] = None
    difficulty_level: Optional[str] = None
    question_type: Optional[str] = None
    marks_min: Optional[float] = None
    marks_max: Optional[float] = None
    tags: Optional[List[str]] = None
    shuffle_questions: bool = False
    include_solved: bool = True

class PYQSession(BaseModel):
    """PYQ practice session model."""
    id: str
    user_id: str
    session_name: str
    filters: PYQSessionFilter
    current_question_index: int = 0
    total_questions: int = 0
    questions_answered: int = 0
    questions_correct: int = 0
    questions_incorrect: int = 0
    questions_skipped: int = 0
    start_time: datetime
    last_activity: datetime
    is_active: bool = True
    status: SessionStatus = SessionStatus.ACTIVE
    question_ids: List[str] = Field(default_factory=list)
    time_limit: Optional[int] = None  # in minutes
    
class PYQResponse(BaseModel):
    """User response to a PYQ question."""
    session_id: str
    question_id: str
    user_answer: str
    is_correct: bool
    time_taken: int  # in seconds
    response_time: datetime = Field(default_factory=datetime.now)

class PYQRetrieverService:
    def __init__(self, supabase_client, fallback_provider=None):
        """
        Initialize PYQ Retriever service.
        
        Args:
            supabase_client: Initialized Supabase client
            fallback_provider: Optional service providing fallback PYQ records
        """
        self.supabase = supabase_client
        self.fallback_provider = fallback_provider
        self.fallback_sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(self,
                           user_id: str,
                           session_name: str,
                           filters: PYQSessionFilter,
                           time_limit: Optional[int] = None) -> Dict[str, Any]:
        """Create a new PYQ practice session."""
        try:
            questions = await self._get_filtered_questions(filters)

            if not questions:
                return {
                    "success": False,
                    "error": "No questions found matching the specified filters"
                }

            if filters.shuffle_questions:
                import random
                random.shuffle(questions)

            session_data = {
                "user_id": user_id,
                "session_name": session_name,
                "filters": filters.dict(),
                "current_question_index": 0,
                "total_questions": len(questions),
                "questions_answered": 0,
                "start_time": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "is_active": True
            }

            question_ids = [q["id"] for q in questions]

            if self.supabase:
                try:
                    session_result = self.supabase.table("pyq_sessions").insert(session_data).execute()
                    if session_result.data:
                        session = session_result.data[0]
                        session_id = session["id"]

                        # Store question IDs in fallback for this session
                        # Since session_questions table doesn't exist, use fallback storage
                        self.fallback_sessions[session_id] = {
                            "id": session_id,
                            "question_ids": question_ids,
                            "question_bank": {q["id"]: q for q in questions}
                        }

                        return {
                            "success": True,
                            "session": {
                                **session,
                                "question_ids": question_ids,
                                "time_limit": time_limit
                            },
                            "total_questions": len(questions)
                        }
                except Exception as error:
                    print(f"Supabase create_session failed: {error}")

            session_id = str(uuid.uuid4())
            fallback_session = {
                "id": session_id,
                **session_data,
                "time_limit": time_limit,
                "question_ids": question_ids,
                "questions_correct": 0,
                "questions_incorrect": 0,
                "questions_skipped": 0,
                "status": SessionStatus.ACTIVE.value,
                "responses": {},
                "question_bank": {q["id"]: q for q in questions}
            }
            self.fallback_sessions[session_id] = fallback_session

            return {
                "success": True,
                "session": {k: v for k, v in fallback_session.items() if k not in {"responses", "question_bank"}},
                "total_questions": len(questions),
                "fallback": True
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error)
            }


    async def get_current_question(self, session_id: str) -> Dict[str, Any]:
        """Get the current question for a session."""
        session = None
        source = "supabase"

        if self.supabase:
            try:
                session_result = self.supabase.table("pyq_sessions")                     .select("*")                     .eq("id", session_id)                     .execute()

                if session_result.data:
                    session = session_result.data[0]
            except Exception as error:
                print(f"Supabase get_current_question failed: {error}")
                session = None

        if session is None:
            session = self.fallback_sessions.get(session_id)
            source = "fallback"

        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        if source == "supabase":
            try:
                question_ids = await self._get_session_question_ids(session_id)
            except Exception as error:
                print(f"Supabase question id lookup failed: {error}")
                question_ids = []
        else:
            question_ids = session.get("question_ids", [])

        if not question_ids:
            return {
                "success": False,
                "error": "No questions found for this session"
            }

        current_index = session.get("current_question_index", 0)
        if current_index >= len(question_ids):
            return {
                "success": False,
                "error": "No more questions in this session",
                "session_completed": True
            }

        current_question_id = question_ids[current_index]
        question = await self._get_question_with_metadata(current_question_id)

        if not question:
            return {
                "success": False,
                "error": "Question not found"
            }

        previous_response = None
        if source == "supabase":
            try:
                response_result = self.supabase.table("test_responses")                     .select("*")                     .eq("session_id", session_id)                     .eq("question_id", current_question_id)                     .execute()
                previous_response = response_result.data[0] if response_result.data else None
            except Exception as error:
                print(f"Supabase previous response lookup failed: {error}")
        else:
            previous_response = session.get("responses", {}).get(current_question_id)

        if source == "supabase":
            try:
                self.supabase.table("pyq_sessions")                     .update({"last_activity": datetime.now().isoformat()})                     .eq("id", session_id)                     .execute()
            except Exception as error:
                print(f"Supabase last_activity update failed: {error}")
        else:
            session["last_activity"] = datetime.now().isoformat()

        return {
            "success": True,
            "question": question,
            "session_info": {
                "session_id": session_id,
                "current_index": current_index,
                "total_questions": len(question_ids),
                "questions_answered": session.get("questions_answered", 0),
                "progress_percentage": (current_index / len(question_ids)) * 100 if question_ids else 0
            },
            "previous_response": previous_response,
            "navigation": {
                "has_previous": current_index > 0,
                "has_next": current_index < len(question_ids) - 1,
                "is_last": current_index == len(question_ids) - 1
            },
            "fallback": source == "fallback"
        }


    async def submit_answer(self,
                          session_id: str,
                          question_id: str,
                          user_answer: str,
                          time_taken: int) -> Dict[str, Any]:
        """Submit an answer for the current question."""
        question = await self._get_question_with_metadata(question_id)
        fallback_session = self.fallback_sessions.get(session_id)
        source = "supabase" if self.supabase else "fallback"

        if question is None and fallback_session:
            source = "fallback"
            question = fallback_session.get("question_bank", {}).get(question_id)

        if not question:
            return {
                "success": False,
                "error": "Question not found"
            }

        is_correct = self._check_answer(question.get("correct_answer"), user_answer)
        response_record = {
            "session_id": session_id,
            "question_id": question_id,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "time_taken": time_taken,
            "response_time": datetime.now().isoformat()
        }

        # Use fallback storage for responses since test_responses table schema doesn't match
        # Get or create fallback session data
        if session_id not in self.fallback_sessions:
            self.fallback_sessions[session_id] = {
                "id": session_id,
                "question_ids": [],
                "question_bank": {},
                "responses": {}
            }

        fallback_session = self.fallback_sessions[session_id]
        responses = fallback_session.setdefault("responses", {})
        existing = responses.get(question_id)
        response_id = existing.get("id") if existing else str(uuid.uuid4())
        responses[question_id] = {
            **response_record,
            "id": response_id
        }

        # Update session stats in Supabase
        if self.supabase:
            try:
                await self._update_session_stats(session_id)
            except Exception as error:
                print(f"Supabase update stats failed: {error}")

        # Update fallback session stats
        fallback_session["questions_answered"] = len(responses)
        fallback_session["questions_correct"] = sum(1 for r in responses.values() if r["is_correct"])
        fallback_session["questions_incorrect"] = sum(1 for r in responses.values() if not r["is_correct"])
        fallback_session["last_activity"] = datetime.now().isoformat()

        return {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": question.get("correct_answer"),
            "explanation": (question.get("pyq_metadata") or [{}])[0].get("solution", ""),
            "response_id": response_id,
            "fallback": True
        }

    async def navigate_to_question(self, session_id: str, direction: str) -> Dict[str, Any]:
        """Navigate to the next or previous question within a session."""
        session = None
        source = "supabase"

        if self.supabase:
            try:
                session_result = (
                    self.supabase.table("pyq_sessions")
                    .select("*")
                    .eq("id", session_id)
                    .execute()
                )
                if session_result.data:
                    session = session_result.data[0]
            except Exception as error:
                print(f"Supabase navigate_to_question failed: {error}")
                session = None

        if session is None:
            session = self.fallback_sessions.get(session_id)
            source = "fallback"

        if not session:
            return {"success": False, "error": "Session not found"}

        question_ids = (
            await self._get_session_question_ids(session_id)
            if source == "supabase"
            else session.get("question_ids", [])
        )
        if not question_ids:
            return {"success": False, "error": "No questions found for this session"}

        current_index = session.get("current_question_index", 0)

        if direction == "next":
            if current_index >= len(question_ids) - 1:
                return {"success": False, "error": "Cannot move beyond the last question"}
            current_index += 1
        elif direction == "previous":
            if current_index <= 0:
                return {"success": False, "error": "Cannot move before the first question"}
            current_index -= 1
        else:
            return {"success": False, "error": "Invalid navigation direction"}

        if source == "supabase":
            try:
                (
                    self.supabase.table("pyq_sessions")
                    .update({
                        "current_question_index": current_index,
                        "last_activity": datetime.now().isoformat(),
                    })
                    .eq("id", session_id)
                    .execute()
                )
            except Exception as error:
                print(f"Supabase navigate_to_question update failed: {error}")
        else:
            session["current_question_index"] = current_index
            session["last_activity"] = datetime.now().isoformat()

        return {
            "success": True,
            "current_index": current_index,
            "fallback": source == "fallback",
        }

    async def jump_to_question(self, session_id: str, question_index: int) -> Dict[str, Any]:
        """Jump to an absolute question index within a session."""
        session = None
        source = "supabase"

        if self.supabase:
            try:
                session_result = (
                    self.supabase.table("pyq_sessions")
                    .select("*")
                    .eq("id", session_id)
                    .execute()
                )
                if session_result.data:
                    session = session_result.data[0]
            except Exception as error:
                print(f"Supabase jump_to_question failed: {error}")
                session = None

        if session is None:
            session = self.fallback_sessions.get(session_id)
            source = "fallback"

        if not session:
            return {"success": False, "error": "Session not found"}

        question_ids = (
            await self._get_session_question_ids(session_id)
            if source == "supabase"
            else session.get("question_ids", [])
        )
        if not question_ids:
            return {"success": False, "error": "No questions found for this session"}

        if question_index < 0 or question_index >= len(question_ids):
            return {"success": False, "error": "Invalid question index"}

        if source == "supabase":
            try:
                (
                    self.supabase.table("pyq_sessions")
                    .update({
                        "current_question_index": question_index,
                        "last_activity": datetime.now().isoformat(),
                    })
                    .eq("id", session_id)
                    .execute()
                )
            except Exception as error:
                print(f"Supabase jump_to_question update failed: {error}")
        else:
            session["current_question_index"] = question_index
            session["last_activity"] = datetime.now().isoformat()

        return {
            "success": True,
            "current_index": question_index,
            "fallback": source == "fallback",
        }

    async def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Return progress metrics for a session."""
        try:
            session = None
            source = "supabase"

            if self.supabase:
                try:
                    session_result = (
                        self.supabase.table("pyq_sessions")
                        .select("*")
                        .eq("id", session_id)
                        .execute()
                    )
                    if session_result.data:
                        session = session_result.data[0]
                except Exception as error:
                    print(f"Supabase get_session_progress failed: {error}")
                    session = None

            if session is None:
                session = self.fallback_sessions.get(session_id)
                source = "fallback"

            if not session:
                return {"success": False, "error": "Session not found"}

            # Always get responses from fallback since we're storing them there
            fallback_data = self.fallback_sessions.get(session_id, {})
            responses = list(fallback_data.get("responses", {}).values())

            question_ids = (
                await self._get_session_question_ids(session_id)
                if source == "supabase"
                else fallback_data.get("question_ids", [])
            )
            total_questions = session.get("total_questions", len(question_ids))
            questions_answered = len(responses)
            questions_correct = len([r for r in responses if r.get("is_correct")])
            questions_incorrect = len([r for r in responses if not r.get("is_correct")])

            total_time = sum(r.get("time_taken", 0) for r in responses)
            avg_time = total_time / questions_answered if questions_answered else 0

            question_status = {}
            for index, q_id in enumerate(question_ids):
                response = next((r for r in responses if r.get("question_id") == q_id), None)
                if response:
                    question_status[index] = (
                        QuestionStatus.CORRECT
                        if response.get("is_correct")
                        else QuestionStatus.INCORRECT
                    )
                else:
                    question_status[index] = QuestionStatus.NOT_ATTEMPTED

            return {
                "success": True,
                "session_id": session_id,
                "session_name": session.get("session_name"),
                "progress": {
                    "current_question": session.get("current_question_index", 0) + 1,
                    "total_questions": total_questions,
                    "questions_answered": questions_answered,
                    "questions_correct": questions_correct,
                    "questions_incorrect": questions_incorrect,
                    "questions_remaining": total_questions - questions_answered,
                    "progress_percentage": (questions_answered / total_questions) * 100 if total_questions else 0,
                    "accuracy_percentage": (questions_correct / questions_answered) * 100 if questions_answered else 0,
                },
                "time_stats": {
                    "total_time_seconds": total_time,
                    "average_time_per_question": avg_time,
                    "session_duration": self._calculate_session_duration(session.get("start_time")),
                },
                "question_status": question_status,
                "is_completed": questions_answered == total_questions,
                "fallback": source == "fallback",
            }
        except Exception as e:
            print(f"Error in get_session_progress: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Failed to get session progress: {str(e)}"
            }

    async def get_user_sessions(self, user_id: str, status: str = "all") -> Dict[str, Any]:
        """List sessions for a given user."""
        sessions: List[Dict[str, Any]] = []
        source = "supabase"

        if self.supabase:
            try:
                query = (
                    self.supabase.table("pyq_sessions")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                )

                if status != "all":
                    query = query.eq("is_active", status == "active")

                sessions = query.execute().data or []
            except Exception as error:
                print(f"Supabase get_user_sessions failed: {error}")
                sessions = []

        if not sessions:
            source = "fallback"
            sessions = [
                {k: v for k, v in session.items() if k not in {"responses", "question_bank"}}
                for session in self.fallback_sessions.values()
                if session.get("user_id") == user_id
                and (status == "all" or (status == "active" and session.get("is_active")))
            ]

        enhanced_sessions = []
        if source == "supabase":
            for session in sessions:
                total_questions = session.get("total_questions", 0) or 0
                questions_answered = 0
                try:
                    responses_result = (
                        self.supabase.table("test_responses")
                        .select("*", count="exact")
                        .eq("session_id", session["id"])
                        .execute()
                    )
                    questions_answered = responses_result.count
                except Exception as error:
                    print(f"Supabase user session response lookup failed: {error}")

                enhanced_sessions.append({
                    **session,
                    "questions_answered": questions_answered,
                    "progress_percentage": (questions_answered / total_questions) * 100 if total_questions else 0,
                    "is_completed": questions_answered == total_questions,
                })
        else:
            for session in sessions:
                fallback_session = self.fallback_sessions.get(session.get("id"))
                questions_answered = 0
                total_questions = session.get("total_questions", len(session.get("question_ids", [])))
                if fallback_session:
                    questions_answered = fallback_session.get("questions_answered", 0)
                    total_questions = fallback_session.get("total_questions", len(fallback_session.get("question_ids", [])))

                enhanced_sessions.append({
                    **session,
                    "questions_answered": questions_answered,
                    "progress_percentage": (questions_answered / total_questions) * 100 if total_questions else 0,
                    "is_completed": questions_answered == total_questions,
                    "fallback": True,
                })

        return {
            "success": True,
            "sessions": enhanced_sessions,
            "fallback": source == "fallback",
        }

    async def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pause a session."""
        if self.supabase:
            try:
                # Try direct update with from_("pyq_sessions")
                result = (
                    self.supabase.from_("pyq_sessions")
                    .update({
                        "is_active": False,
                        "last_activity": datetime.now().isoformat(),
                    })
                    .eq("id", session_id)
                    .execute()
                )
                return {"success": True, "message": "Session paused"}
            except Exception as error:
                print(f"Supabase pause_session failed: {error}")

        session = self.fallback_sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        session["is_active"] = False
        session["status"] = SessionStatus.PAUSED.value
        session["last_activity"] = datetime.now().isoformat()
        return {"success": True, "message": "Session paused", "fallback": True}

    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a paused session."""
        if self.supabase:
            try:
                # Try direct update with from_("pyq_sessions")
                result = (
                    self.supabase.from_("pyq_sessions")
                    .update({
                        "is_active": True,
                        "last_activity": datetime.now().isoformat(),
                    })
                    .eq("id", session_id)
                    .execute()
                )
                return {"success": True, "message": "Session resumed"}
            except Exception as error:
                print(f"Supabase resume_session failed: {error}")

        session = self.fallback_sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        session["is_active"] = True
        session["status"] = SessionStatus.ACTIVE.value
        session["last_activity"] = datetime.now().isoformat()
        return {"success": True, "message": "Session resumed", "fallback": True}

    def _check_answer(self, correct_answer: str, user_answer: str) -> bool:
        """Check if user answer is correct."""
        return str(correct_answer).strip().lower() == str(user_answer).strip().lower()

    def _calculate_session_duration(self, start_time_str: Optional[str]) -> float:
        """Calculate session duration in seconds, handling timezone-aware/naive datetimes."""
        if not start_time_str:
            return 0

        try:
            start_time = datetime.fromisoformat(start_time_str)
            # Make both timezone-aware or both timezone-naive
            if start_time.tzinfo is not None:
                # start_time is timezone-aware, make now() timezone-aware too
                from datetime import timezone
                now = datetime.now(timezone.utc)
            else:
                # start_time is timezone-naive, use naive now()
                now = datetime.now()

            return (now - start_time).total_seconds()
        except Exception as e:
            print(f"Error calculating session duration: {e}")
            return 0

    async def _update_session_stats(self, session_id: str):
        """Update session statistics."""
        # Get stats from fallback storage
        session = self.fallback_sessions.get(session_id)
        if not session:
            return

        responses = session.get("responses", {})
        questions_answered = len(responses)

        # Update Supabase session stats
        if self.supabase:
            try:
                (
                    self.supabase.table("pyq_sessions")
                    .update({
                        "questions_answered": questions_answered,
                        "last_activity": datetime.now().isoformat(),
                    })
                    .eq("id", session_id)
                    .execute()
                )
            except Exception as error:
                print(f"Supabase _update_session_stats failed: {error}")

        # Update fallback stats
        session["questions_answered"] = questions_answered
        session["questions_correct"] = sum(1 for r in responses.values() if r["is_correct"])
        session["questions_incorrect"] = sum(1 for r in responses.values() if not r["is_correct"])
        session["last_activity"] = datetime.now().isoformat()

    async def _get_filtered_questions(self, filters: PYQSessionFilter) -> List[Dict[str, Any]]:
        """Get questions based on filters."""
        questions = []

        if self.supabase:
            try:
                # First get questions based on hierarchy filters
                query = self.supabase.table("questions").select("*")

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

                result = query.execute()
                questions = result.data or []

                # If PYQ metadata filters are specified, fetch and filter by metadata
                if questions and (filters.year or filters.year_range or filters.exam_session or filters.source or filters.difficulty_level or filters.question_type):
                    question_ids = [q["id"] for q in questions]

                    # Fetch PYQ metadata for these questions
                    metadata_query = self.supabase.table("pyq_metadata").select("*").in_("question_id", question_ids)
                    metadata_result = metadata_query.execute()
                    metadata_by_question = {m["question_id"]: m for m in (metadata_result.data or [])}

                    filtered = []
                    for q in questions:
                        metadata = metadata_by_question.get(q["id"])
                        if not metadata:
                            continue

                        if filters.year and metadata.get("year") != filters.year:
                            continue
                        if filters.year_range and not (filters.year_range[0] <= metadata.get("year", 0) <= filters.year_range[1]):
                            continue
                        if filters.exam_session and metadata.get("exam_session") != filters.exam_session:
                            continue
                        if filters.source and metadata.get("source") != filters.source:
                            continue
                        if filters.difficulty_level and metadata.get("difficulty_level") != filters.difficulty_level:
                            continue
                        if filters.question_type and metadata.get("question_type") != filters.question_type:
                            continue

                        q["pyq_metadata"] = [metadata]
                        filtered.append(q)
                    questions = filtered

            except Exception as error:
                print(f"Supabase _get_filtered_questions failed: {error}")

        if not questions and self.fallback_provider and hasattr(self.fallback_provider, 'get_filtered_questions'):
            questions = await self.fallback_provider.get_filtered_questions(filters)

        return questions

    async def _get_session_question_ids(self, session_id: str) -> List[str]:
        """Get question IDs for a session in order."""
        question_ids = []

        # Check fallback storage first (since session_questions table doesn't exist)
        if session_id in self.fallback_sessions:
            question_ids = self.fallback_sessions[session_id].get("question_ids", [])

        return question_ids

    async def _get_question_with_metadata(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a question with its PYQ metadata."""
        question = None

        if self.supabase:
            try:
                # Get the question
                result = (
                    self.supabase.table("questions")
                    .select("*")
                    .eq("id", question_id)
                    .execute()
                )
                if result.data:
                    question = result.data[0]

                    # Try to get PYQ metadata
                    try:
                        metadata_result = (
                            self.supabase.table("pyq_metadata")
                            .select("*")
                            .eq("question_id", question_id)
                            .execute()
                        )
                        if metadata_result.data:
                            question["pyq_metadata"] = metadata_result.data
                    except Exception:
                        # No metadata, that's okay
                        question["pyq_metadata"] = []

            except Exception as error:
                print(f"Supabase _get_question_with_metadata failed: {error}")

        return question
