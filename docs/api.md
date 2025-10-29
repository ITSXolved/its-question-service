# ITS Question Service API

The ITS Question Service exposes a Flask-based REST API for managing exams, questions, cognitive attributes, and Previous Year Question (PYQ) workflows. All endpoints respond with JSON and expect JSON request bodies unless otherwise noted.

- **Base URL**: `http://localhost:5200`
- **Content-Type**: `application/json`
- **Authentication**: Not enforced by default. Secure deployment should front this service with authentication and TLS.
- **Environment**: The service depends on Supabase credentials and an OpenRouter API key loaded from the `.env` file (`SUPABASE_URL`, `SUPABASE_KEY`, `OPENROUTER_API_KEY`).

## Error Model

Errors return HTTP status codes `4xx` or `5xx` with a JSON payload such as:

```json
{"error": "Explanation of the failure"}
```

## PYQ Upload & Catalog

### POST /api/pyq/upload/single
Upload one PYQ question.
- **Body**: PYQQuestion schema exported by `PYQUploadService`; includes question text, options, correct answer, hierarchy IDs, metadata (year, source, etc.).
- **Response**: `201 Created` with `{ "success": true, "question_id": "..." }` on success. Validation errors return `400`.

### POST /api/pyq/upload/bulk
Upload many PYQ questions in one request.
- **Body**: `{ "questions": [<PYQQuestion>, ...] }`.
- **Response**: `200 OK` with per-question success counts; malformed items abort with `400`.

### POST /api/pyq/upload/excel
Upload questions via Excel template.
- **Request**: `multipart/form-data` with `file` (Excel) and optional column mapping fields.
- **Response**: `200 OK` with `success`, counts, and any row-level errors. Returns `400` when the file or mapping is missing.

### GET /api/pyq/statistics
Return aggregate statistics filtered by year, session, or source.
- **Query**: `year`, `exam_session`, `source` (optional).
- **Response**: `200 OK` JSON containing counts, trends, or other stats computed by `PYQUploadService`.

### GET /api/pyq/search
Search PYQ questions with pagination.
- **Query**: hierarchy filters (`exam_id`, `subject_id`, `chapter_id`, `topic_id`, `concept_id`), metadata filters (`year`, `exam_session`, `source`, `difficulty_level`, `question_type`), `page`, `page_size`.
- **Response**: `200 OK` with `{ "data": [...], "pagination": {...} }`.

### GET /api/pyq/template/download
Download the Excel template used by the bulk upload route.
- **Response**: XLSX file with sample row and expected column headers.

### GET /api/pyq/filters/options
Retrieve distinct PYQ metadata values (years, sessions, sources, etc.) to power filter UIs.

## PYQ Practice Sessions

### POST /api/pyq/session/create
Start a practice session for a user.
- **Body**: `{ "user_id": "...", "session_name": "...", "filters": {...}, "time_limit": 45 }` where filters follow `PYQSessionFilter`.
- **Response**: `201 Created` with session descriptor when successful.

### GET /api/pyq/session/<session_id>/current
Get the current question in an active session.

### POST /api/pyq/session/<session_id>/submit
Submit an answer for the current question.
- **Body**: `{ "question_id": "...", "user_answer": "...", "time_taken": 120 }`.

### POST /api/pyq/session/<session_id>/navigate/<direction>
Move to the `next` or `previous` question in the session.

### POST /api/pyq/session/<session_id>/jump/<question_index>
Jump to a specific question index.

### GET /api/pyq/session/<session_id>/progress
Return detailed progress metrics (attempted, correct, remaining, etc.).

### POST /api/pyq/session/<session_id>/pause
Pause an in-flight session.

### POST /api/pyq/session/<session_id>/resume
Resume a paused session.

### GET /api/pyq/sessions/user/<user_id>
List sessions for a user; optional `status` query (`active`, `completed`, `all`).

## Hierarchy & Catalog Browsing

### GET /api/hierarchy/exam/<exam_id>/question-count
Return question totals for an exam. Equivalent routes exist for subjects, chapters, topics, and concepts:
- `/api/hierarchy/subject/<subject_id>/question-count`
- `/api/hierarchy/chapter/<chapter_id>/question-count`
- `/api/hierarchy/topic/<topic_id>/question-count`
- `/api/hierarchy/concept/<concept_id>/question-count`

### GET /api/hierarchy/exams
Fetch all exams. Additional list endpoints accept mandatory parent IDs via query parameters:
- `/api/hierarchy/subjects?exam_id=...`
- `/api/hierarchy/chapters?subject_id=...`
- `/api/hierarchy/topics?chapter_id=...`
- `/api/hierarchy/concepts?topic_id=...`

### GET /api/hierarchy/<level>/<item_id>/children
Return the next level of children for the given level (`exam`, `subject`, `chapter`, `topic`).

### GET /api/hierarchy/<level>/<item_id>/chain
Return the full ancestor chain for the selected node.

### GET /api/hierarchy/tree
Return an entire nested tree of exams → subjects → chapters → topics → concepts for navigation UIs.

### POST /api/hierarchy/ensure
Create a missing hierarchy node under a parent when it does not already exist.
- **Body**: `{ "level": "topic", "name": "New Topic", "description": "...", "parent_id": "..." }`.

## Item Bank & Analytics

### GET /api/hierarchy/<level>/<item_id>/stats
Return aggregate metrics (question counts, attribute usage, difficulty distribution) for a node.
- **Query**: none (level is `exam|subject|chapter|topic|concept`).

### GET /api/item-bank/<level>/<item_id>
Fetch item bank entries with pagination and optional difficulty filters.
- **Query**: `page`, `page_size`, `difficulty_min`, `difficulty_max`.
- **Response**: Questions enriched with cognitive attributes and q-matrix data.

### GET /api/hierarchy/<level>/<item_id>/questions
Search questions constrained to a hierarchy level with pagination, returning enriched question objects.

### GET /api/search/hierarchy
Search hierarchy entities by text.
- **Query**: `query` search string, `level` (`exams`, `subjects`, `chapters`, `topics`, or `concepts`). Adds question counts per match.

### GET /api/search/questions
Full-text and filtered question search with pagination.
- **Query**: hierarchy IDs, `text_search`, difficulty range, `page`, `page_size`.

### GET /api/export/educdm/<level>/<item_id>
Export questions, attributes, and Q-matrix data in EduCDM-compatible JSON.

## Exam, Subject, Chapter, Topic, Concept Management

### POST /api/exams
Create a new exam.
- **Body**: `{ "name": "", "description": "" }`.

### POST /api/subjects
Create a subject under an exam.
- **Body**: `{ "exam_id": "", "name": "", "description": "" }`.

### POST /api/chapters
Create a chapter under a subject.

### POST /api/topics
Create a topic under a chapter.

### POST /api/concepts
Create a concept under a topic.

## Attribute Management

### GET /api/hierarchy/attributes
List attributes for a concept.
- **Query**: `concept_id` (required).

### POST /api/attributes
Create a new attribute record.
- **Body**: attribute fields (`name`, `description`, `concept_id`, etc.).

### GET /api/concept/<concept_id>/attributes
Return attributes associated with a given concept.

## Question Creation & Retrieval

### POST /api/questions/generate-attributes
Generate suggested attributes for a question using the LLM.
- **Body**: question draft including `content`, `options`, `correct_answer`, `concept_id`, and hierarchy IDs for context.
- **Response**: Suggested attributes plus existing attributes for the concept.

### POST /api/questions/create-with-attributes
Create a question, optionally creating new attributes and Q-matrix entries in one step.
- **Body**: Full question payload with optional `selected_attributes` and `create_new_attributes` arrays.
- **Response**: Created question, LLM-generated parameters, created attribute list, and Q-matrix counts.

### POST /api/questions/batch
Bulk-create plain questions with optional attribute bindings.
- **Body**: `{ "questions": [ { <question>, "attributes": [ {"attribute_id": "", "value": true }, ... ] }, ... ] }`.

### GET /api/questions
List questions filtered by hierarchy.
- **Query**: hierarchy IDs (`exam_id`, `subject_id`, etc.). Response enriches each question with all concept attributes and q-matrix indices.

### GET /api/questions/<question_id>
Retrieve a single question with attribute detail and q-matrix.

### POST /api/questions/batch-get
Retrieve many questions by ID.
- **Body**: `{ "question_ids": ["id1", "id2"] }`.

## Notes

- All identifiers are Supabase UUID strings.
- Dates and numeric values should be provided in ISO 8601 or numeric form as expected by Supabase schemas.
- The service logs stack traces to stdout on unexpected errors; inspect container logs for diagnostics.
