# Frontend Developer Documentation - Index

Welcome! This directory contains complete documentation for building the admin web application.

---

## 📚 Documentation Files

### 1. **FRONTEND_ADMIN_APP_GUIDE.md** (Main Guide)
**Complete documentation for all 4 pages of the admin app**

**Contents:**
- ✅ Page 1: Dashboard with Content Count & Filters
- ✅ Page 2: Hierarchical Creation Workflow
- ✅ Page 3: Question Upload Service (with images, batch upload, edit/delete)
- ✅ Page 4: Resource Upload Service (topic-based learning materials)
- ✅ Page 5: Enhanced Question Fetching with Q-Matrix Display
- ✅ Complete API reference with examples
- ✅ UI/UX mockups for each page
- ✅ Frontend implementation examples (React/TypeScript)
- ✅ Error handling patterns

👉 **Start here** for comprehensive guidance

---

### 2. **API_QUICK_REFERENCE.md** (Quick Reference)
**One-page cheat sheet for all API endpoints**

**Contents:**
- ⚡ Quick syntax for all endpoints
- ⚡ Common patterns and workflows
- ⚡ TypeScript type definitions
- ⚡ HTTP status codes
- ⚡ File upload notes
- ⚡ 3PL parameters guide

👉 Use this for **quick lookups** while coding

---

### 3. **TOPIC_RESOURCES_API.md** (Resources API)
**Detailed documentation for the resource management system**

**Contents:**
- 📖 Topic-based resource structure
- 📖 All 9 resource types explained
- 📖 Complete CRUD operations
- 📖 Metadata field examples
- 📖 Frontend integration examples

👉 Reference for **resource management** features

---

## 🎯 Quick Start Guide

### For Backend Setup:
1. Read: `TOPIC_RESOURCES_SETUP.md`
2. Run: `CREATE_TOPIC_RESOURCES_TABLE.sql` in Supabase
3. Start server: `python -m app.main`
4. Test: Open `topic_resources_test.ipynb`

### For Frontend Development:
1. Read: `FRONTEND_ADMIN_APP_GUIDE.md`
2. Bookmark: `API_QUICK_REFERENCE.md`
3. Start coding with provided examples
4. Test against: `http://localhost:5200/api`

---

## 📋 Admin App Pages Overview

### Page 1: Dashboard
**Purpose:** Monitor content and statistics

**Features:**
- Content count at all hierarchy levels
- Filter by exam → subject → chapter → topic
- Visual statistics and charts
- Difficulty distribution
- Attribute analysis

**Key APIs:**
- `GET /api/hierarchy/exams`
- `GET /api/hierarchy/{level}/{id}/question-count`
- `GET /api/hierarchy/{level}/{id}/stats`

---

### Page 2: Content Creation
**Purpose:** Create hierarchical structure

**Workflow:**
1. Select exam type (competitive/school)
2. Create/select: Exam → Subject → Chapter → Topic → Concept
3. Cascading dropdowns with dynamic loading
4. Tree view of entire hierarchy

**Key APIs:**
- `POST /api/exams`
- `POST /api/subjects`
- `POST /api/chapters`
- `POST /api/topics`
- `POST /api/concepts`
- `GET /api/hierarchy/tree`

---

### Page 3: Question Upload
**Purpose:** Upload and manage questions

**Features:**
- Single question upload
- Batch upload (multiple questions)
- Question image upload
- Option images upload (A, B, C, D)
- Attribute selection/creation
- 3PL parameters (difficulty, discrimination, guessing)
- Edit existing questions
- Delete questions (soft/permanent)

**Key APIs:**
- `POST /api/questions/create-with-attributes`
- `POST /api/questions/batch`
- `POST /api/questions/{id}/image`
- `POST /api/questions/{id}/options/images`
- `GET/PUT/DELETE /api/questions/{id}`
- `GET /api/topic/{id}/attributes`

---

### Page 4: Resource Upload
**Purpose:** Add learning materials to topics

**Features:**
- 9 resource types support
- Single resource upload
- Bulk resource upload
- Resource metadata management
- Preview and edit resources
- Delete resources

**Resource Types:**
- 🎥 Video (YouTube, Vimeo)
- 📄 PDF documents
- 🧪 Virtual labs
- 🎭 3D models
- ✨ Animations
- 🖼️ Images
- 🎮 Interactive widgets
- 📰 Articles
- ⚙️ Simulations

**Key APIs:**
- `POST /api/topics/{id}/resources`
- `POST /api/topics/{id}/resources/bulk`
- `GET /api/topics/{id}/resources`
- `GET /api/chapters/{id}/resources`
- `GET/PUT/DELETE /api/resources/{id}`

---

### Page 5: Question Browser
**Purpose:** View and analyze questions

**Features:**
- View questions at any hierarchy level
- Q-Matrix visualization
- Attribute mapping display
- Filter by difficulty, type
- Search questions
- Pagination
- View question images
- See which attributes each question tests

**Key APIs:**
- `GET /api/hierarchy/{level}/{id}/questions/enhanced`
- `GET /api/hierarchy/{level}/{id}/questions`
- `GET /api/search/questions`
- `GET /api/item-bank/{level}/{id}`

---

## 🔑 Key Concepts

### Hierarchy Structure
```
Exam (JEE Main)
└── Subject (Physics)
    └── Chapter (Mechanics)
        └── Topic (Newton's Laws)
            ├── Concept (First Law)
            ├── Concept (Second Law)
            └── Resources (Videos, PDFs, Labs)
```

### Q-Matrix Explained
**What is it?**
- Binary vector showing which attributes a question tests
- Example: `[1, 1, 0, 0]` means question tests first 2 attributes

**How to display:**
```javascript
// attributes = ["Understanding Laws", "Applying Forces", "Problem Solving", "Advanced"]
// q_vector = [1, 1, 0, 0]

// Question tests:
✓ Understanding Laws
✓ Applying Forces
○ Problem Solving
○ Advanced
```

### 3PL Parameters
**Item Response Theory parameters:**
- **Difficulty** (-3 to 3): How hard the question is
- **Discrimination** (0 to 3): How well it differentiates ability
- **Guessing** (0 to 1): Probability of guessing correctly (usually 0.25 for 4 options)

---

## 💻 Technology Stack Recommendations

### Frontend
- **Framework:** React or Next.js
- **Language:** TypeScript (types provided)
- **UI Library:** Material-UI, Ant Design, or Chakra UI
- **State Management:** React Query or Redux Toolkit
- **Forms:** React Hook Form or Formik
- **File Upload:** react-dropzone
- **Rich Text:** Draft.js or TinyMCE

### API Client
```typescript
// Using fetch with TypeScript
const api = {
  baseURL: 'http://localhost:5200/api',

  async get(endpoint: string) {
    const response = await fetch(`${this.baseURL}${endpoint}`);
    if (!response.ok) throw new Error('Request failed');
    return response.json();
  },

  async post(endpoint: string, data: any) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Request failed');
    return response.json();
  }
};
```

---

## 🎨 UI Component Examples

### Question Card Component
```typescript
import React from 'react';

interface QuestionCardProps {
  question: EnhancedQuestion;
  attributes: Attribute[];
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, attributes }) => {
  return (
    <div className="question-card">
      <div className="question-header">
        <span>ID: {question.id}</span>
        <span>Difficulty: {question.difficulty.toFixed(2)}</span>
      </div>

      {question.question_image_url && (
        <img src={question.question_image_url} alt="Question" />
      )}

      <div className="question-content">
        <p>{question.content}</p>
      </div>

      <div className="options">
        {Object.entries(question.options).map(([key, value]) => (
          <div key={key} className={`option ${question.correct_answer === key ? 'correct' : ''}`}>
            {question.option_images?.[key] && (
              <img src={question.option_images[key]} alt={`Option ${key}`} />
            )}
            <span>{key}. {value}</span>
          </div>
        ))}
      </div>

      <div className="q-matrix">
        <h4>Tests {question.attribute_count} Attributes:</h4>
        <div className="q-matrix-grid">
          {attributes.map((attr, idx) => (
            <div
              key={attr.id}
              className={`q-cell ${question.q_vector[idx] ? 'active' : 'inactive'}`}
              title={attr.name}
            >
              {question.q_vector[idx] ? '✓' : '○'}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### Hierarchy Selector
```typescript
import React, { useState, useEffect } from 'react';

export const HierarchySelector: React.FC = () => {
  const [exams, setExams] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [topics, setTopics] = useState([]);

  const [selectedExam, setSelectedExam] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);

  useEffect(() => {
    fetch('/api/hierarchy/exams')
      .then(r => r.json())
      .then(setExams);
  }, []);

  useEffect(() => {
    if (selectedExam) {
      fetch(`/api/hierarchy/subjects?exam_id=${selectedExam.id}`)
        .then(r => r.json())
        .then(setSubjects);
    }
  }, [selectedExam]);

  // Similar for chapters, topics...

  return (
    <div className="hierarchy-selector">
      <select onChange={e => setSelectedExam(exams.find(ex => ex.id === e.target.value))}>
        <option>Select Exam...</option>
        {exams.map(exam => (
          <option key={exam.id} value={exam.id}>{exam.name}</option>
        ))}
      </select>

      <select onChange={e => setSelectedSubject(subjects.find(s => s.id === e.target.value))} disabled={!selectedExam}>
        <option>Select Subject...</option>
        {subjects.map(subject => (
          <option key={subject.id} value={subject.id}>{subject.name}</option>
        ))}
      </select>

      {/* Continue for chapters, topics */}
    </div>
  );
};
```

---

## 🧪 Testing

### Test the backend is running:
```bash
curl http://localhost:5200/api/hierarchy/exams
```

### Use provided test notebooks:
- `topic_resources_test.ipynb`
- `endpoint_coverage_test.ipynb`

### Frontend testing:
```typescript
// Example with Jest
test('fetches questions with Q-matrix', async () => {
  const data = await fetch('/api/hierarchy/topic/123/questions/enhanced')
    .then(r => r.json());

  expect(data.questions).toBeDefined();
  expect(data.attributes).toBeDefined();
  expect(data.questions[0].q_vector).toBeInstanceOf(Array);
});
```

---

## 📞 Support & Help

### Documentation Files
- **Main Guide:** `FRONTEND_ADMIN_APP_GUIDE.md` (Complete reference)
- **Quick Reference:** `API_QUICK_REFERENCE.md` (Cheat sheet)
- **Resources API:** `TOPIC_RESOURCES_API.md` (Resources details)
- **Setup Guide:** `../TOPIC_RESOURCES_SETUP.md` (Backend setup)

### Troubleshooting
1. **Server not responding:** Check server is running on port 5200
2. **404 errors:** Verify endpoint URLs match documentation
3. **Table errors:** Ensure database tables are created in Supabase
4. **CORS issues:** Check CORS settings in Flask app

### Example Code
All documentation includes working TypeScript/React examples that you can copy and adapt.

---

## 🚀 Getting Started Checklist

**Backend Setup:**
- [ ] Create database tables in Supabase
- [ ] Start Flask server (`python -m app.main`)
- [ ] Verify server responds at `http://localhost:5200/api/hierarchy/exams`
- [ ] Run test notebook to verify all endpoints work

**Frontend Setup:**
- [ ] Read `FRONTEND_ADMIN_APP_GUIDE.md`
- [ ] Bookmark `API_QUICK_REFERENCE.md`
- [ ] Set up React/TypeScript project
- [ ] Install UI library (Material-UI, etc.)
- [ ] Create API client with base URL
- [ ] Build hierarchy selector component
- [ ] Test API integration

**Development:**
- [ ] Page 1: Dashboard with statistics
- [ ] Page 2: Hierarchical creation
- [ ] Page 3: Question upload
- [ ] Page 4: Resource upload
- [ ] Page 5: Question browser with Q-matrix

---

## 📝 Notes

- All endpoints return JSON
- Base URL: `http://localhost:5200/api`
- Port: `5200`
- Authentication: Not currently implemented
- File uploads use `multipart/form-data`
- All other requests use `application/json`

---

Happy coding! 🎉

For questions, refer to the detailed guides or test notebooks for working examples.
