# Dual Path Hierarchy Implementation Guide

## Overview
The system now supports **two distinct hierarchical paths** for organizing questions:

### 1. **Competitive Exam Path**
```
Exam → Subject → Chapter → Topic → Attributes
```
Used for competitive examinations like JEE, NEET, UPSC, etc.

### 2. **School Path**
```
Exam → Class → Subject → Chapter → Topic → Attributes
```
Used for school-based curricula like CBSE, ICSE, State Boards, etc.

---

## Database Schema Changes

### New Table: `classes`
```sql
CREATE TABLE classes (
    id UUID PRIMARY KEY,
    exam_id UUID REFERENCES exams(id),
    name TEXT NOT NULL,
    description TEXT,
    class_number INTEGER,  -- e.g., 1, 2, 3... 12
    section TEXT,           -- e.g., 'A', 'B', 'C'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Modified Tables:

#### 1. `exams` table
- **Added:** `exam_type` VARCHAR(20) - Values: 'competitive' | 'school'

#### 2. `subjects` table
- **Added:** `class_id` UUID - Links to classes table (for school path)
- **Modified:** `exam_id` now optional (NULL for school path subjects)
- **Constraint:** Subject must have EITHER `exam_id` OR `class_id`, not both

#### 3. `questions` table
- **Added:** `class_id` UUID - Links to classes table

---

## Migration Instructions

### Step 1: Run Database Migration
```sql
-- Execute the migration file in Supabase SQL Editor
-- File: docs/supabase_migration_dual_path.sql
```

### Step 2: Verify Migration
```sql
-- Check exam types
SELECT exam_type, COUNT(*) FROM exams GROUP BY exam_type;

-- Check classes
SELECT * FROM classes;

-- Verify subject paths
SELECT
    s.id,
    s.name,
    CASE
        WHEN s.exam_id IS NOT NULL THEN 'Competitive'
        WHEN s.class_id IS NOT NULL THEN 'School'
    END as path_type
FROM subjects s;
```

---

## API Usage

### Creating Exam Hierarchies

#### Competitive Exam Example
```bash
# 1. Create competitive exam
POST /api/exams
{
  "name": "JEE Main",
  "description": "Joint Entrance Examination",
  "exam_type": "competitive"
}

# 2. Create subject directly under exam
POST /api/subjects
{
  "name": "Physics",
  "description": "JEE Physics",
  "exam_id": "exam-uuid-here"
}

# 3. Create chapter
POST /api/chapters
{
  "name": "Mechanics",
  "subject_id": "subject-uuid-here"
}

# 4. Create topic
POST /api/topics
{
  "name": "Newton's Laws",
  "chapter_id": "chapter-uuid-here"
}

# 5. Create attributes for topic
POST /api/topic/{topic-id}/attributes
[
  {
    "name": "Force Calculation",
    "description": "Ability to calculate forces"
  },
  {
    "name": "Free Body Diagrams",
    "description": "Understanding FBDs"
  }
]
```

#### School Exam Example
```bash
# 1. Create school exam
POST /api/exams
{
  "name": "CBSE",
  "description": "Central Board of Secondary Education",
  "exam_type": "school"
}

# 2. Create class
POST /api/classes
{
  "exam_id": "exam-uuid-here",
  "name": "Class 10",
  "class_number": 10,
  "description": "Class 10 CBSE"
}

# 3. Create subject under class
POST /api/subjects
{
  "name": "Mathematics",
  "description": "Class 10 Mathematics",
  "class_id": "class-uuid-here"
}

# 4. Create chapter (same as competitive)
POST /api/chapters
{
  "name": "Quadratic Equations",
  "subject_id": "subject-uuid-here"
}

# 5. Create topic (same as competitive)
POST /api/topics
{
  "name": "Solving Quadratics",
  "chapter_id": "chapter-uuid-here"
}

# 6. Create attributes (same as competitive)
POST /api/topic/{topic-id}/attributes
[
  {
    "name": "Factorization Method",
    "description": "Solving using factorization"
  }
]
```

---

## New API Endpoints

### Class Management

#### 1. Create Class
```http
POST /api/classes
Content-Type: application/json

{
  "exam_id": "uuid",
  "name": "Class 10",
  "class_number": 10,
  "section": "A",
  "description": "Class 10 CBSE"
}
```

#### 2. Get Classes for Exam
```http
GET /api/exams/{exam_id}/classes
```

#### 3. Get Specific Class
```http
GET /api/classes/{class_id}
```

#### 4. Get Subjects for Class
```http
GET /api/classes/{class_id}/subjects
```

### Updated Endpoints

#### Create Exam (Updated)
```http
POST /api/exams
{
  "name": "Exam Name",
  "description": "Description",
  "exam_type": "competitive"  # or "school"
}
```

#### Create Subject (Updated)
```http
POST /api/subjects

# For competitive exam:
{
  "name": "Physics",
  "exam_id": "uuid"
}

# For school:
{
  "name": "Mathematics",
  "class_id": "uuid"
}
```

---

## Creating Questions

Questions can be created for either path. The system automatically determines the path based on provided IDs.

### Competitive Exam Question
```bash
POST /api/questions/create-with-attributes
{
  "question": {
    "content": "Calculate the force...",
    "options": ["10N", "20N", "30N", "40N"],
    "correct_answer": "20N",
    "exam_id": "jee-uuid",
    "subject_id": "physics-uuid",
    "chapter_id": "mechanics-uuid",
    "topic_id": "newtons-laws-uuid",
    "difficulty": 0.6,
    "discrimination": 1.5,
    "guessing": 0.25
  },
  "selected_attributes": [
    {"attribute_id": "force-calc-uuid", "value": true}
  ]
}
```

### School Question
```bash
POST /api/questions/create-with-attributes
{
  "question": {
    "content": "Solve: x² + 5x + 6 = 0",
    "options": ["-2, -3", "2, 3", "-2, 3", "2, -3"],
    "correct_answer": "-2, -3",
    "exam_id": "cbse-uuid",
    "class_id": "class-10-uuid",
    "subject_id": "math-uuid",
    "chapter_id": "quadratic-uuid",
    "topic_id": "solving-uuid",
    "difficulty": 0.4,
    "discrimination": 1.2,
    "guessing": 0.25
  },
  "selected_attributes": [
    {"attribute_id": "factorization-uuid", "value": true}
  ]
}
```

---

## Hierarchy Tree API

The `/api/hierarchy/tree` endpoint now returns different structures based on exam type:

### Competitive Exam Response
```json
[
  {
    "id": "exam-uuid",
    "name": "JEE Main",
    "exam_type": "competitive",
    "type": "exam",
    "children": [
      {
        "id": "subject-uuid",
        "name": "Physics",
        "type": "subject",
        "children": [
          {
            "id": "chapter-uuid",
            "name": "Mechanics",
            "type": "chapter",
            "children": [
              {
                "id": "topic-uuid",
                "name": "Newton's Laws",
                "type": "topic"
              }
            ]
          }
        ]
      }
    ]
  }
]
```

### School Exam Response
```json
[
  {
    "id": "exam-uuid",
    "name": "CBSE",
    "exam_type": "school",
    "type": "exam",
    "children": [
      {
        "id": "class-uuid",
        "name": "Class 10",
        "class_number": 10,
        "type": "class",
        "children": [
          {
            "id": "subject-uuid",
            "name": "Mathematics",
            "type": "subject",
            "children": [
              {
                "id": "chapter-uuid",
                "name": "Quadratic Equations",
                "type": "chapter",
                "children": [
                  {
                    "id": "topic-uuid",
                    "name": "Solving Quadratics",
                    "type": "topic"
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
]
```

---

## Database Views

Two views are created for easy querying:

### 1. Competitive Exam Questions View
```sql
SELECT * FROM competitive_exam_questions
WHERE exam_name = 'JEE Main';
```

### 2. School Questions View
```sql
SELECT * FROM school_questions
WHERE class_number = 10;
```

---

## Frontend Integration Guide

### Path Detection
```javascript
// Determine which path to use based on exam type
async function getExamPath(examId) {
  const response = await fetch(`/api/exams`);
  const exams = await response.json();
  const exam = exams.find(e => e.id === examId);
  return exam.exam_type; // 'competitive' or 'school'
}

// Build hierarchy UI based on path
async function buildHierarchyUI(examType, examId) {
  if (examType === 'school') {
    // Show: Exam → Classes → Subjects → Chapters → Topics
    const classes = await fetch(`/api/exams/${examId}/classes`).then(r => r.json());
    // ... build UI
  } else {
    // Show: Exam → Subjects → Chapters → Topics
    const subjects = await fetch(`/api/exams/${examId}/subjects`).then(r => r.json());
    // ... build UI
  }
}
```

### Question Creation Form
```javascript
function QuestionForm({ examType }) {
  return (
    <form>
      <select name="exam_id">...</select>

      {examType === 'school' && (
        <select name="class_id">...</select>
      )}

      <select name="subject_id">...</select>
      <select name="chapter_id">...</select>
      <select name="topic_id">...</select>

      {/* Rest of form */}
    </form>
  );
}
```

---

## Testing Checklist

- [ ] Create competitive exam and verify path
- [ ] Create school exam and verify path
- [ ] Create classes for school exam
- [ ] Create subjects for both paths
- [ ] Create chapters, topics for both paths
- [ ] Create attributes for topics
- [ ] Create questions for competitive path
- [ ] Create questions for school path
- [ ] Test hierarchy tree API for both types
- [ ] Verify questions views work correctly
- [ ] Test question retrieval with filters

---

## Migration from Old System

### Existing Data
All existing exams will default to `exam_type = 'competitive'` and continue to work as before.

### Adding School Exams
To add school functionality to existing setup:
1. Create new exam with `exam_type = 'school'`
2. Create classes under the exam
3. Create subjects linked to classes
4. Continue with chapters, topics as normal

---

## Common Queries

### Get all school exams with classes
```sql
SELECT
    e.name as exam_name,
    c.name as class_name,
    c.class_number
FROM exams e
JOIN classes c ON c.exam_id = e.id
WHERE e.exam_type = 'school'
ORDER BY e.name, c.class_number;
```

### Get question count by path
```sql
-- Competitive
SELECT COUNT(*) FROM competitive_exam_questions;

-- School
SELECT COUNT(*) FROM school_questions;
```

### Get subjects by path type
```sql
SELECT
    s.name,
    CASE
        WHEN s.exam_id IS NOT NULL THEN 'Competitive'
        WHEN s.class_id IS NOT NULL THEN 'School'
    END as path_type,
    e.name as exam_name,
    c.name as class_name
FROM subjects s
LEFT JOIN exams e ON s.exam_id = e.id
LEFT JOIN classes c ON s.class_id = c.id;
```

---

## Files Modified

- ✅ `docs/supabase_migration_dual_path.sql` - Database migration
- ✅ `app/supabase_knowledge_base.py` - Added class methods and updated subject creation
- ✅ `app/main.py` - Added class endpoints and updated hierarchy tree
- ✅ `docs/DUAL_PATH_IMPLEMENTATION.md` - This documentation

---

## Support

For questions or issues:
1. Review the migration SQL file
2. Check API endpoint documentation
3. Verify exam_type is set correctly
4. Ensure subjects have correct parent (exam_id OR class_id)

---

## Next Steps

1. **Run the migration:** Execute `docs/supabase_migration_dual_path.sql`
2. **Test the APIs:** Use provided examples to test both paths
3. **Update frontend:** Implement path detection and conditional UI
4. **Migrate data:** Convert existing exams to appropriate type if needed
