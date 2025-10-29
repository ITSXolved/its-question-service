# Hierarchy Structure Diagrams

## Visual Comparison of Both Paths

---

## Competitive Exam Path

```
┌─────────────────────────────────────────────────────┐
│  Exam (exam_type: competitive)                      │
│  e.g., "JEE Main", "NEET", "UPSC"                  │
└────────────────┬────────────────────────────────────┘
                 │
                 ├─── Subject (exam_id)
                 │    e.g., "Physics", "Chemistry"
                 │    └─── Chapter (subject_id)
                 │         e.g., "Mechanics", "Thermodynamics"
                 │         └─── Topic (chapter_id)
                 │              e.g., "Newton's Laws", "Heat Transfer"
                 │              └─── Attributes (topic_id)
                 │                   e.g., "Force Calculation", "Concept Understanding"
                 │
                 └─── Subject (exam_id)
                      "..."
```

### Example: JEE Main Physics

```
JEE Main (competitive)
  ↓
Physics (exam_id = JEE Main)
  ↓
Mechanics (subject_id = Physics)
  ↓
Newton's Laws (chapter_id = Mechanics)
  ↓
Attributes:
  - Force Calculation (topic_id = Newton's Laws)
  - Free Body Diagrams (topic_id = Newton's Laws)
  - Problem Solving (topic_id = Newton's Laws)
```

---

## School Path

```
┌─────────────────────────────────────────────────────┐
│  Exam (exam_type: school)                           │
│  e.g., "CBSE", "ICSE", "State Board"               │
└────────────────┬────────────────────────────────────┘
                 │
                 ├─── Class (exam_id)
                 │    e.g., "Class 10", "Class 12"
                 │    │
                 │    └─── Subject (class_id)
                 │         e.g., "Mathematics", "Science"
                 │         └─── Chapter (subject_id)
                 │              e.g., "Quadratic Equations", "Electricity"
                 │              └─── Topic (chapter_id)
                 │                   e.g., "Solving Quadratics", "Ohm's Law"
                 │                   └─── Attributes (topic_id)
                 │                        e.g., "Factorization", "Formula Application"
                 │
                 └─── Class (exam_id)
                      "..."
```

### Example: CBSE Class 10 Mathematics

```
CBSE (school)
  ↓
Class 10 (exam_id = CBSE, class_number = 10)
  ↓
Mathematics (class_id = Class 10)
  ↓
Quadratic Equations (subject_id = Mathematics)
  ↓
Solving Quadratics (chapter_id = Quadratic Equations)
  ↓
Attributes:
  - Factorization Method (topic_id = Solving Quadratics)
  - Quadratic Formula (topic_id = Solving Quadratics)
  - Graphical Method (topic_id = Solving Quadratics)
```

---

## Side-by-Side Comparison

| Level | Competitive Exam | School |
|-------|-----------------|--------|
| **1** | Exam | Exam |
| **2** | Subject | Class |
| **3** | Chapter | Subject |
| **4** | Topic | Chapter |
| **5** | Attributes | Topic |
| **6** | - | Attributes |

---

## Database Relationships

### Competitive Exam Path

```sql
exams (exam_type='competitive')
  ↓ (exam_id)
subjects
  ↓ (subject_id)
chapters
  ↓ (chapter_id)
topics
  ↓ (topic_id)
attributes
```

### School Path

```sql
exams (exam_type='school')
  ↓ (exam_id)
classes
  ↓ (class_id)
subjects
  ↓ (subject_id)
chapters
  ↓ (chapter_id)
topics
  ↓ (topic_id)
attributes
```

---

## Question Relationships

### Competitive Exam Question

```
Question
  ├─ exam_id → Exam (competitive)
  ├─ subject_id → Subject (linked to exam)
  ├─ chapter_id → Chapter
  ├─ topic_id → Topic
  └─ attributes (via topic_id)
```

### School Question

```
Question
  ├─ exam_id → Exam (school)
  ├─ class_id → Class (NEW!)
  ├─ subject_id → Subject (linked to class)
  ├─ chapter_id → Chapter
  ├─ topic_id → Topic
  └─ attributes (via topic_id)
```

---

## API Call Flow

### Creating Competitive Exam Hierarchy

```
1. POST /api/exams
   { "name": "JEE Main", "exam_type": "competitive" }
   ↓ Returns: exam_id

2. POST /api/subjects
   { "name": "Physics", "exam_id": <exam_id> }
   ↓ Returns: subject_id

3. POST /api/chapters
   { "name": "Mechanics", "subject_id": <subject_id> }
   ↓ Returns: chapter_id

4. POST /api/topics
   { "name": "Newton's Laws", "chapter_id": <chapter_id> }
   ↓ Returns: topic_id

5. POST /api/topic/<topic_id>/attributes
   [
     { "name": "Force Calculation" },
     { "name": "Free Body Diagrams" }
   ]
   ↓ Returns: attribute_ids
```

### Creating School Hierarchy

```
1. POST /api/exams
   { "name": "CBSE", "exam_type": "school" }
   ↓ Returns: exam_id

2. POST /api/classes
   { "exam_id": <exam_id>, "name": "Class 10", "class_number": 10 }
   ↓ Returns: class_id

3. POST /api/subjects
   { "name": "Mathematics", "class_id": <class_id> }
   ↓ Returns: subject_id

4. POST /api/chapters
   { "name": "Quadratic Equations", "subject_id": <subject_id> }
   ↓ Returns: chapter_id

5. POST /api/topics
   { "name": "Solving Quadratics", "chapter_id": <chapter_id> }
   ↓ Returns: topic_id

6. POST /api/topic/<topic_id>/attributes
   [
     { "name": "Factorization Method" },
     { "name": "Quadratic Formula" }
   ]
   ↓ Returns: attribute_ids
```

---

## Hierarchy Tree JSON Structure

### Competitive Exam Tree

```json
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
              "type": "topic",
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

### School Tree

```json
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
                  "type": "topic",
                  "children": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## UI Navigation Flow

### Competitive Exam UI

```
┌─────────────────────────────────┐
│ Select Exam: [JEE Main ▼]      │ ← exam_type = competitive
├─────────────────────────────────┤
│ Select Subject: [Physics ▼]     │ ← filtered by exam_id
├─────────────────────────────────┤
│ Select Chapter: [Mechanics ▼]   │ ← filtered by subject_id
├─────────────────────────────────┤
│ Select Topic: [Newton's Laws ▼] │ ← filtered by chapter_id
├─────────────────────────────────┤
│ Attributes: [Show All]           │ ← filtered by topic_id
└─────────────────────────────────┘
```

### School UI

```
┌──────────────────────────────────┐
│ Select Exam: [CBSE ▼]           │ ← exam_type = school
├──────────────────────────────────┤
│ Select Class: [Class 10 ▼]      │ ← filtered by exam_id
├──────────────────────────────────┤
│ Select Subject: [Mathematics ▼]  │ ← filtered by class_id
├──────────────────────────────────┤
│ Select Chapter: [Quadratics ▼]   │ ← filtered by subject_id
├──────────────────────────────────┤
│ Select Topic: [Solving... ▼]     │ ← filtered by chapter_id
├──────────────────────────────────┤
│ Attributes: [Show All]            │ ← filtered by topic_id
└──────────────────────────────────┘
```

---

## Key Differences Highlighted

### Subject Creation

**Competitive:**
```json
POST /api/subjects
{
  "name": "Physics",
  "exam_id": "uuid" ← Links directly to exam
}
```

**School:**
```json
POST /api/subjects
{
  "name": "Mathematics",
  "class_id": "uuid" ← Links to class, not exam
}
```

### Question Creation

**Competitive:**
```json
{
  "exam_id": "uuid",
  "subject_id": "uuid",
  "chapter_id": "uuid",
  "topic_id": "uuid"
  // No class_id
}
```

**School:**
```json
{
  "exam_id": "uuid",
  "class_id": "uuid", ← Additional field
  "subject_id": "uuid",
  "chapter_id": "uuid",
  "topic_id": "uuid"
}
```

---

## Summary

- **Competitive**: Direct path from Exam → Subject
- **School**: Extra layer of Class between Exam and Subject
- **Both**: Use same structure from Chapter onwards
- **Attributes**: Always link to Topics for both paths
- **Questions**: School questions have additional `class_id` field

---

This visual guide should help understand the dual path hierarchy system!
