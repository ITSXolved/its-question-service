# ITS Question Service

## Overview
The ITS Question Service is a Flask-based backend that manages the hierarchy, cataloguing, and cognitive metadata that power an Intelligent Tutoring System (ITS). It integrates with Supabase for persistence. PYQ (Previous Year Question) upload and practice-session flows are included alongside traditional item-bank APIs.

**⚠️ IMPORTANT UPDATES:**
1. **Dual Path Support**: The system now supports both **competitive exam** and **school** hierarchical paths
2. **Topic-Attribute Mapping**: Attributes are now **directly linked to topics** (skipping the concept layer)
3. **Manual Attribute Management**: **LLM-based attribute generation has been disabled**. Attributes are created manually via API

The repository ships with a comprehensive Jupyter notebook (`comprehensive_api_test.ipynb`) that seeds sample data and exercises every major endpoint.

## Key Capabilities
- **Dual hierarchy paths:**
  - **Competitive Exam**: Exam → Subject → Chapter → Topic → Attributes
  - **School**: Exam → Class → Subject → Chapter → Topic → Attributes
- **Manual attribute management** with direct topic-to-attribute mapping.
- Question CRUD with Q-matrix persistence and batch utilities.
- PYQ ingestion (single, bulk, Excel) and metadata analytics.
- PYQ practice-session management with navigation, progress, and response tracking.
- Search, export (EduCDM), and hierarchy statistics endpoints.

## Architecture
- **Framework**: Flask + Gunicorn (packaged via Docker for deployment).
- **Persistence**: Supabase tables for hierarchy entities, questions, attributes, and PYQ metadata.
- **Async tasks**: Certain services use `asyncio` helpers to bridge async Supabase calls within sync routes.
- **Attribute Management**: Manual creation and management via REST APIs (LLM integration disabled).
- **Notebooks**: Jupyter notebooks in the repo offer API smoke/regression testing.

Directory highlights:
- `app/`: Flask application and service modules.
- `docs/api.md`: In-depth endpoint documentation.
- `docs/CHANGES_SUMMARY.md`: **START HERE** - Complete summary of all changes.
- `docs/DUAL_PATH_IMPLEMENTATION.md`: Dual hierarchy path implementation guide.
- `docs/HIERARCHY_DIAGRAMS.md`: Visual diagrams of both hierarchy paths.
- `docs/IMPLEMENTATION_SUMMARY.md`: Topic-attribute direct mapping details.
- `docs/supabase_migration_*.sql`: Database migration scripts.
- `comprehensive_api_test.ipynb`: End-to-end API verification notebook.

## Prerequisites
- Python 3.9+ (if running locally without Docker).
- Docker + Docker Compose (recommended for reproducible setups).
- Supabase project with the expected tables.
- **⚠️ Migrations Required**: If upgrading from an older version, you must run BOTH migrations **in order**:
  1. `docs/supabase_migration_topic_attributes.sql` - Attribute restructuring
  2. `docs/supabase_migration_dual_path.sql` - Dual path support

## Environment Configuration
Create a `.env` file (or configure environment variables) with at least:

```
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-service-role-key
```

**Note:** `OPENROUTER_API_KEY` is no longer required as LLM-based attribute generation has been disabled.

Additional Supabase tables (e.g., `pyq_metadata`, `pyq_sessions`, `pyq_responses`) must exist. See the schema comments in `app/pyq_upload_service.py` and `app/pyq_retriever_service.py` if you need the DDL references.

## Running the Service
### Using Docker Compose (recommended)
```
docker compose up --build
```
The API will be available at `http://localhost:5200/api` by default. Logs from the container will show Supabase and Redis integrations (if configured) coming online.

To rebuild after code changes:
```
docker compose build --no-cache
```

### Local Python Environment
1. Create and activate a virtual environment.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Export the required environment variables (or populate a `.env` file).
4. Run the Flask app (development mode):
   ```
   flask --app app/main.py --debug run -p 5200
   ```
   or launch Gunicorn for parity with production:
   ```
   gunicorn --bind 0.0.0.0:5200 app.main:app
   ```

## API Reference
The full endpoint catalogue, payload schemas, and status code expectations are maintained in [`docs/api.md`](docs/api.md). Highlights include:
- `/api/exams` - Create exams with `exam_type` (competitive/school).
- `/api/classes` - **NEW:** Manage classes for school path.
- `/api/hierarchy/...` routes for browsing hierarchy (supports both paths).
- `/api/topic/{topic_id}/attributes` routes for **manual attribute management** (GET, POST).
- `/api/attributes/{attribute_id}` routes for updating and deleting attributes (PUT, DELETE).
- `/api/questions/...` routes for question creation, batch operations, and retrieval.
- `/api/pyq/...` routes for PYQ ingestion, analytics, and session workflows.
- `/api/search/...` and `/api/export/...` utilities.

**Breaking Changes & New Features:** See [`docs/CHANGES_SUMMARY.md`](docs/CHANGES_SUMMARY.md) for complete details.

## Testing & Tooling
- **Comprehensive API Notebook**: Open `comprehensive_api_test.ipynb` to seed test data, exercise endpoints, and summarize responses. Set `API_BASE_URL` and `API_AUTH_TOKEN` (if needed) before running.
- **Legacy notebook**: `revised_api_test.ipynb` remains for ad-hoc experiments and latency checks.
- **Logging**: Gunicorn + Flask logs to stdout; tailor log level in `app/main.py` or container configuration.

## Data Model Notes
- All identifiers are Supabase UUID strings.
- **Two hierarchy paths supported:**
  - Competitive: Exam → Subject → Chapter → Topic
  - School: Exam → Class → Subject → Chapter → Topic
- **Attributes are linked directly to topics** (not concepts). Questions inherit attributes from their topic.
- Question records include cognitive metadata (`difficulty`, `discrimination`, `guessing`) which should be provided manually or defaults are used.
- PYQ uploads create linked metadata rows and optional Q-matrix entries for selected attributes.

## Troubleshooting
- **Service fails to boot**: Ensure environment variables are set and Supabase credentials are valid.
- **Migration errors**: Run BOTH migrations in order: `supabase_migration_topic_attributes.sql` then `supabase_migration_dual_path.sql`.
- **"exam_type required" error**: All exams must now specify `exam_type` ('competitive' or 'school').
- **"Provide either exam_id OR class_id" error**: Subjects for competitive exams use `exam_id`, school subjects use `class_id`.
- **Attribute-related errors**: Attributes are now linked to `topic_id` not `concept_id`.
- **Missing classes table**: Run the dual path migration script.
- **Notebook errors**: Check that the API is running and accessible at the configured base URL.
- **Deprecated endpoint warnings**: See `docs/CHANGES_SUMMARY.md` for migration guide.

## Contributing
1. Fork or branch from `main`.
2. Run notebooks or targeted curl calls to validate changes.
3. Keep `docs/api.md` and this README in sync when adding or modifying endpoints.
4. Use conventional Python formatting and include succinct comments only when clarifying complex behavior.

## License
Internal project – update this section with license information if the code is distributed externally.
