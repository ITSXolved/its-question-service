# Dual Path Quick Reference

## Two Hierarchy Paths

### Competitive Exam
```
Exam (competitive) → Subject → Chapter → Topic → Attributes
```

### School
```
Exam (school) → Class → Subject → Chapter → Topic → Attributes
```

---

## Quick Setup

### 1. Run Migration
```sql
-- Execute in Supabase SQL Editor
\i docs/supabase_migration_dual_path.sql
```

### 2. Create Competitive Exam Setup
```bash
# Create exam
curl -X POST http://localhost:5200/api/exams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JEE Main",
    "exam_type": "competitive"
  }'

# Create subject (directly under exam)
curl -X POST http://localhost:5200/api/subjects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Physics",
    "exam_id": "exam-uuid"
  }'
```

### 3. Create School Setup
```bash
# Create exam
curl -X POST http://localhost:5200/api/exams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CBSE",
    "exam_type": "school"
  }'

# Create class
curl -X POST http://localhost:5200/api/classes \
  -H "Content-Type: application/json" \
  -d '{
    "exam_id": "exam-uuid",
    "name": "Class 10",
    "class_number": 10
  }'

# Create subject (under class)
curl -X POST http://localhost:5200/api/subjects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mathematics",
    "class_id": "class-uuid"
  }'
```

---

## New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/classes` | Create a class |
| `GET` | `/api/exams/{exam_id}/classes` | Get classes for exam |
| `GET` | `/api/classes/{class_id}` | Get specific class |
| `GET` | `/api/classes/{class_id}/subjects` | Get subjects for class |

---

## Updated Endpoints

### Create Exam
```json
POST /api/exams
{
  "name": "Exam Name",
  "exam_type": "competitive" // or "school"
}
```

### Create Subject
```json
// Competitive path
{
  "name": "Subject Name",
  "exam_id": "uuid"
}

// School path
{
  "name": "Subject Name",
  "class_id": "uuid"
}
```

---

## Key Differences

| Feature | Competitive | School |
|---------|------------|--------|
| Hierarchy | Exam → Subject | Exam → Class → Subject |
| Subject linked to | `exam_id` | `class_id` |
| Question has | `exam_id` | `exam_id` + `class_id` |

---

## Database Changes

### New Table
- `classes` - School classes (Class 1-12, etc.)

### Modified Columns
- `exams.exam_type` - 'competitive' or 'school'
- `subjects.class_id` - Links to classes (school path)
- `questions.class_id` - For school questions

### Constraints
- Subjects must have EITHER `exam_id` OR `class_id`
- Not both

---

## Example: Complete Workflow

### Competitive Exam (JEE)
```
1. Create Exam (JEE, type=competitive)
   ↓
2. Create Subject (Physics, exam_id=JEE)
   ↓
3. Create Chapter (Mechanics, subject_id=Physics)
   ↓
4. Create Topic (Newton's Laws, chapter_id=Mechanics)
   ↓
5. Create Attributes (Force Calculation, topic_id=Newton's Laws)
   ↓
6. Create Question (with topic_id, attribute_ids)
```

### School (CBSE Class 10)
```
1. Create Exam (CBSE, type=school)
   ↓
2. Create Class (Class 10, exam_id=CBSE)
   ↓
3. Create Subject (Mathematics, class_id=Class10)
   ↓
4. Create Chapter (Quadratics, subject_id=Math)
   ↓
5. Create Topic (Solving, chapter_id=Quadratics)
   ↓
6. Create Attributes (Factorization, topic_id=Solving)
   ↓
7. Create Question (with class_id, topic_id, attribute_ids)
```

---

## Troubleshooting

**Q: Subject creation fails with "Provide either exam_id OR class_id"**
A: Check you're not sending both. Competitive uses `exam_id`, school uses `class_id`.

**Q: Can I convert competitive to school?**
A: Yes, update exam_type and migrate subjects to classes.

**Q: Do attributes work differently?**
A: No, attributes link to topics same way for both paths.

**Q: What about existing data?**
A: All existing exams default to 'competitive' and work as before.

---

## Quick Tests

```bash
# Test competitive path
curl http://localhost:5200/api/hierarchy/tree | jq '.[] | select(.exam_type=="competitive")'

# Test school path
curl http://localhost:5200/api/hierarchy/tree | jq '.[] | select(.exam_type=="school")'

# Get classes for a school exam
curl http://localhost:5200/api/exams/{exam_id}/classes
```

---

## See Also

- [Full Implementation Guide](DUAL_PATH_IMPLEMENTATION.md)
- [Migration SQL](supabase_migration_dual_path.sql)
- [Main README](../README.md)
