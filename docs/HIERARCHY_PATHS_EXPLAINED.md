# Hierarchy Paths Explained - Competitive vs School Exams

## Overview

The system supports **TWO DIFFERENT HIERARCHY PATHS** based on exam type:
1. **Competitive Exam Path** - For JEE, NEET, CAT, etc.
2. **School Exam Path** - For CBSE, ICSE, State Boards, etc.

---

## Key Difference: Class Level

The main difference is the **CLASS LEVEL** which exists **ONLY for school exams**.

### Competitive Path (4-5 levels)
```
Exam → Subject → Chapter → Topic → Concept
```

### School Path (5-6 levels)
```
Exam → Class → Subject → Chapter → Topic → Concept
         ↑
      EXTRA LEVEL
```

---

## Path 1: Competitive Exam

### When to Use
- JEE (Joint Entrance Examination)
- NEET (Medical entrance)
- CAT (Management entrance)
- GATE (Graduate entrance)
- Any competitive/entrance examination

### Hierarchy
```
┌─────────────────┐
│ EXAM            │ exam_type: "competitive"
│ (JEE Main 2025) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ SUBJECT         │ Direct under exam (no class)
│ (Physics)       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ CHAPTER         │
│ (Mechanics)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ TOPIC           │
│ (Newton's Laws) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ CONCEPT         │ Optional
│ (First Law)     │
└─────────────────┘
```

### API Flow

**Create Exam:**
```json
POST /api/exams
{
  "name": "JEE Main 2025",
  "exam_type": "competitive"
}
```

**Create Subject (directly under exam):**
```json
POST /api/subjects
{
  "exam_id": "exam-uuid",
  "name": "Physics"
}
```

**Get Subjects:**
```
GET /api/hierarchy/subjects?exam_id={exam_id}
```

---

## Path 2: School Exam

### When to Use
- CBSE (Central Board of Secondary Education)
- ICSE (Indian Certificate of Secondary Education)
- State Boards (Maharashtra, UP, etc.)
- Any school/board examination

### Hierarchy
```
┌─────────────────┐
│ EXAM            │ exam_type: "school"
│ (CBSE Board)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ CLASS           │ ← REQUIRED for school exams
│ (Class 10)      │    (Class 10, 11, 12, etc.)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ SUBJECT         │ Under class (not directly under exam)
│ (Physics)       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ CHAPTER         │
│ (Light)         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ TOPIC           │
│ (Reflection)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ CONCEPT         │ Optional
│ (Laws of Ref.)  │
└─────────────────┘
```

### API Flow

**Create Exam:**
```json
POST /api/exams
{
  "name": "CBSE Board",
  "exam_type": "school"
}
```

**Create Class (required for school exams):**
```json
POST /api/classes
{
  "exam_id": "exam-uuid",
  "name": "Class 10",
  "class_number": 10,
  "section": "A"
}
```

**Create Subject (under class, not exam):**
```json
POST /api/subjects
{
  "class_id": "class-uuid",
  "name": "Physics"
}
```

**Get Classes:**
```
GET /api/hierarchy/classes?exam_id={exam_id}
```

**Get Subjects:**
```
GET /api/hierarchy/subjects?class_id={class_id}
```

---

## Frontend Implementation

### Conditional Class Selector

```typescript
const HierarchySelector: React.FC = () => {
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [selectedClass, setSelectedClass] = useState<Class | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);

  // Check if school exam
  const isSchoolExam = selectedExam?.exam_type === 'school';

  return (
    <div>
      {/* Exam Selector - Always visible */}
      <select onChange={e => setSelectedExam(findExam(e.target.value))}>
        <option>Select Exam...</option>
        {exams.map(exam => (
          <option key={exam.id} value={exam.id}>
            {exam.name} ({exam.exam_type})
          </option>
        ))}
      </select>

      {/* Class Selector - Only for school exams */}
      {isSchoolExam && (
        <select onChange={e => setSelectedClass(findClass(e.target.value))}>
          <option>Select Class...</option>
          {classes.map(cls => (
            <option key={cls.id} value={cls.id}>
              {cls.name}
            </option>
          ))}
        </select>
      )}

      {/* Subject Selector - Always visible but depends on exam type */}
      <select
        disabled={!selectedExam || (isSchoolExam && !selectedClass)}
        onChange={e => setSelectedSubject(findSubject(e.target.value))}
      >
        <option>Select Subject...</option>
        {subjects.map(subject => (
          <option key={subject.id} value={subject.id}>
            {subject.name}
          </option>
        ))}
      </select>

      {/* Rest of hierarchy... */}
    </div>
  );
};
```

### Loading Subjects Based on Exam Type

```typescript
useEffect(() => {
  if (!selectedExam) return;

  if (selectedExam.exam_type === 'school' && selectedClass) {
    // School path: Load subjects under class
    fetch(`/api/hierarchy/subjects?class_id=${selectedClass.id}`)
      .then(r => r.json())
      .then(setSubjects);
  } else if (selectedExam.exam_type === 'competitive') {
    // Competitive path: Load subjects under exam
    fetch(`/api/hierarchy/subjects?exam_id=${selectedExam.id}`)
      .then(r => r.json())
      .then(setSubjects);
  }
}, [selectedExam, selectedClass]);
```

---

## API Endpoints Summary

### Creating Hierarchy

| Level | Competitive Path | School Path |
|-------|------------------|-------------|
| **Exam** | `POST /api/exams` with `exam_type: "competitive"` | `POST /api/exams` with `exam_type: "school"` |
| **Class** | ❌ Not applicable | ✅ `POST /api/classes` with `exam_id` |
| **Subject** | `POST /api/subjects` with `exam_id` | `POST /api/subjects` with `class_id` |
| **Chapter** | `POST /api/chapters` with `subject_id` | `POST /api/chapters` with `subject_id` |
| **Topic** | `POST /api/topics` with `chapter_id` | `POST /api/topics` with `chapter_id` |
| **Concept** | `POST /api/concepts` with `topic_id` | `POST /api/concepts` with `topic_id` |

### Getting Hierarchy

| Level | Competitive Path | School Path |
|-------|------------------|-------------|
| **Classes** | ❌ Not applicable | `GET /api/hierarchy/classes?exam_id={id}` |
| **Subjects** | `GET /api/hierarchy/subjects?exam_id={id}` | `GET /api/hierarchy/subjects?class_id={id}` |
| **Chapters** | `GET /api/hierarchy/chapters?subject_id={id}` | `GET /api/hierarchy/chapters?subject_id={id}` |
| **Topics** | `GET /api/hierarchy/topics?chapter_id={id}` | `GET /api/hierarchy/topics?chapter_id={id}` |
| **Concepts** | `GET /api/hierarchy/concepts?topic_id={id}` | `GET /api/hierarchy/concepts?topic_id={id}` |

---

## UI Mockups

### Competitive Exam Selection
```
┌─────────────────────────────────────┐
│ Exam Type: ● Competitive ○ School   │
├─────────────────────────────────────┤
│ Exam:    [JEE Main 2025      ▼]    │
│ Subject: [Physics            ▼]    │
│ Chapter: [Mechanics          ▼]    │
│ Topic:   [Newton's Laws      ▼]    │
│                                      │
│ Breadcrumb:                          │
│ JEE Main > Physics > Mechanics > ... │
└─────────────────────────────────────┘
```

### School Exam Selection
```
┌─────────────────────────────────────┐
│ Exam Type: ○ Competitive ● School   │
├─────────────────────────────────────┤
│ Exam:    [CBSE Board         ▼]    │
│ Class:   [Class 10           ▼]    │ ← EXTRA
│ Subject: [Physics            ▼]    │
│ Chapter: [Light              ▼]    │
│ Topic:   [Reflection         ▼]    │
│                                      │
│ Breadcrumb:                          │
│ CBSE > Class 10 > Physics > Light >..│
└─────────────────────────────────────┘
```

---

## Database Schema

### Tables Involved

**exams** table:
```sql
CREATE TABLE exams (
  id UUID PRIMARY KEY,
  name TEXT,
  description TEXT,
  exam_type TEXT  -- 'competitive' or 'school'
);
```

**classes** table (school exams only):
```sql
CREATE TABLE classes (
  id UUID PRIMARY KEY,
  exam_id UUID REFERENCES exams(id),
  name TEXT,
  class_number INTEGER,
  section TEXT
);
```

**subjects** table:
```sql
CREATE TABLE subjects (
  id UUID PRIMARY KEY,
  exam_id UUID,       -- For competitive path
  class_id UUID,      -- For school path
  name TEXT,
  description TEXT,
  FOREIGN KEY (exam_id) REFERENCES exams(id),
  FOREIGN KEY (class_id) REFERENCES classes(id)
);
```

---

## Common Questions

### Q: Can a school exam skip the class level?
**A:** No. If `exam_type: "school"`, you must create classes first, then subjects under those classes.

### Q: Can a competitive exam have classes?
**A:** No. If `exam_type: "competitive"`, classes are not used. Subjects go directly under the exam.

### Q: How do I know which path to use?
**A:** Check the `exam_type` field:
- `"competitive"` → Use exam → subject path
- `"school"` → Use exam → class → subject path

### Q: What happens if I provide both exam_id and class_id when creating a subject?
**A:** The API will reject it. You must provide EITHER `exam_id` (competitive) OR `class_id` (school), not both.

### Q: Can I have multiple sections in one class?
**A:** Yes. Create multiple class entries:
```json
POST /api/classes
{"exam_id": "...", "name": "Class 10", "section": "A"}

POST /api/classes
{"exam_id": "...", "name": "Class 10", "section": "B"}
```

---

## Examples

### Example 1: JEE Main (Competitive)

```
JEE Main 2025 (competitive)
├── Physics
│   ├── Mechanics
│   │   └── Newton's Laws
│   │       ├── First Law
│   │       ├── Second Law
│   │       └── Third Law
│   └── Optics
│       └── Wave Optics
└── Chemistry
    └── Organic Chemistry
```

### Example 2: CBSE (School)

```
CBSE Board (school)
├── Class 10
│   ├── Physics
│   │   ├── Light
│   │   │   └── Reflection & Refraction
│   │   └── Electricity
│   └── Chemistry
│       └── Acids, Bases & Salts
└── Class 11
    ├── Physics
    │   └── Thermodynamics
    └── Chemistry
        └── Organic Chemistry
```

---

## Summary

✅ **Competitive Exam** = Exam → Subject → Chapter → Topic → Concept (4-5 levels)

✅ **School Exam** = Exam → **Class** → Subject → Chapter → Topic → Concept (5-6 levels)

**The class level is MANDATORY for school exams and NOT USED for competitive exams.**

---

## Related Documentation

- **Complete Guide:** `FRONTEND_ADMIN_APP_GUIDE.md`
- **Architecture:** `ADMIN_APP_ARCHITECTURE.md`
- **API Reference:** `API_QUICK_REFERENCE.md`
