# Quick Start Guide - Topic-Attribute Direct Mapping

## TL;DR
1. **Attributes now link to topics** (not concepts)
2. **LLM attribute generation is disabled** - create attributes manually
3. **Run database migration** before starting the service

---

## Step-by-Step Setup

### 1. Run Database Migration
```sql
-- Execute this in your Supabase SQL Editor
-- File: docs/supabase_migration_topic_attributes.sql
```

### 2. Update Environment Variables (Optional)
```bash
# .env file
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-service-role-key
# OPENROUTER_API_KEY is no longer needed
```

### 3. Start the Service
```bash
docker compose up --build
```

---

## Common API Operations

### Create Attributes for a Topic
```bash
# Single attribute
curl -X POST http://localhost:5200/api/topic/{topic_id}/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Problem Solving",
    "description": "Ability to break down complex problems"
  }'

# Multiple attributes
curl -X POST http://localhost:5200/api/topic/{topic_id}/attributes \
  -H "Content-Type: application/json" \
  -d '[
    {"name": "Logical Reasoning", "description": "..."},
    {"name": "Mathematical Skills", "description": "..."}
  ]'
```

### Get Attributes for a Topic
```bash
curl http://localhost:5200/api/topic/{topic_id}/attributes
```

### Update an Attribute
```bash
curl -X PUT http://localhost:5200/api/attributes/{attribute_id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "description": "Updated Description"
  }'
```

### Delete an Attribute
```bash
curl -X DELETE http://localhost:5200/api/attributes/{attribute_id}
```

### Create Question with Attributes
```bash
curl -X POST http://localhost:5200/api/questions/create-with-attributes \
  -H "Content-Type: application/json" \
  -d '{
    "question": {
      "content": "What is 2 + 2?",
      "options": ["3", "4", "5", "6"],
      "correct_answer": "4",
      "topic_id": "your-topic-uuid",
      "difficulty": 0.3,
      "discrimination": 1.2,
      "guessing": 0.25
    },
    "selected_attributes": [
      {"attribute_id": "attr-uuid-1", "value": true}
    ]
  }'
```

---

## What Changed?

### Before (Old System)
```
Topic → Concept → Attributes
                ↑
          LLM generates these
```

### After (New System)
```
Topic → Attributes
        ↑
   Manually created via API
```

---

## Migration Checklist

- [ ] Backup database
- [ ] Run migration SQL
- [ ] Verify attributes have `topic_id`
- [ ] Test attribute creation API
- [ ] Update frontend/client code
- [ ] Remove `OPENROUTER_API_KEY` from environment (optional)
- [ ] Test question creation with new attributes

---

## Troubleshooting

**Q: I get "column concept_id does not exist" error**
A: Run the migration SQL file first.

**Q: My old attributes are missing**
A: The migration preserves them by linking to parent topics.

**Q: Can I still use concepts?**
A: Yes, concepts still exist for hierarchy but attributes link to topics.

**Q: How do I generate 3PL parameters without LLM?**
A: Provide them manually in question creation or use defaults (difficulty=0.5, discrimination=1.0, guessing=0.25).

---

## Deprecated Endpoints

| Old Endpoint | Status | Use Instead |
|-------------|--------|-------------|
| `POST /api/questions/generate-attributes` | ❌ Disabled (410) | Manual creation via `POST /api/topic/{topic_id}/attributes` |
| `GET /api/concept/{concept_id}/attributes` | ⚠️ Deprecated | `GET /api/topic/{topic_id}/attributes` |

---

## Need More Help?

- Full details: [`docs/IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md)
- Migration SQL: [`docs/supabase_migration_topic_attributes.sql`](supabase_migration_topic_attributes.sql)
- Main README: [`README.md`](../README.md)
