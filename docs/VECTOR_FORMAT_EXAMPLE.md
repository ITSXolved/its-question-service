# Q-Vector Format - Visual Example

## Scenario

You have a **Chapter: "Algebra"** with questions from 2 topics:
- **Topic 1:** Linear Equations
- **Topic 2:** Quadratic Equations

### Attributes at this Chapter Level

| Index | Attribute ID | Name | Topic |
|-------|-------------|------|-------|
| 0 | attr-1 | Algebraic Manipulation | Topic 1 |
| 1 | attr-2 | Equation Solving | Topic 1 |
| 2 | attr-3 | Substitution Method | Topic 1 |
| 3 | attr-4 | Factorization | Topic 2 |
| 4 | attr-5 | Quadratic Formula | Topic 2 |
| 5 | attr-6 | Completing the Square | Topic 2 |

**Total Attributes:** 6

---

## Questions and Their Q-Vectors

### Question 1: "Solve: 2x + 5 = 13"
**Tests:** Algebraic Manipulation + Equation Solving

**Q-Vector:** `[1, 1, 0, 0, 0, 0]`

**Explanation:**
- Index 0 (Algebraic Manipulation) = 1 ✓
- Index 1 (Equation Solving) = 1 ✓
- Index 2 (Substitution) = 0
- Index 3 (Factorization) = 0
- Index 4 (Quadratic Formula) = 0
- Index 5 (Completing Square) = 0

---

### Question 2: "Solve: x² - 5x + 6 = 0 using factorization"
**Tests:** Factorization

**Q-Vector:** `[0, 0, 0, 1, 0, 0]`

**Explanation:**
- Index 0-2 = 0 (not testing Topic 1 attributes)
- Index 3 (Factorization) = 1 ✓
- Index 4-5 = 0

---

### Question 3: "Solve: 2x² + 7x + 3 = 0 using quadratic formula"
**Tests:** Quadratic Formula + Algebraic Manipulation

**Q-Vector:** `[1, 0, 0, 0, 1, 0]`

**Explanation:**
- Index 0 (Algebraic Manipulation) = 1 ✓
- Index 1-3 = 0
- Index 4 (Quadratic Formula) = 1 ✓
- Index 5 = 0

---

### Question 4: "Solve system: {2x + y = 5, x - y = 1}"
**Tests:** Substitution Method + Equation Solving

**Q-Vector:** `[0, 1, 1, 0, 0, 0]`

**Explanation:**
- Index 0 = 0
- Index 1 (Equation Solving) = 1 ✓
- Index 2 (Substitution Method) = 1 ✓
- Index 3-5 = 0

---

## Complete Q-Matrix for Chapter

Rows = Questions, Columns = Attributes

```
        Alg  Eqn  Sub  Fac  Quad  Comp
        Man  Sol  Met  tor  Form  Sqr
Q1:     [1,   1,   0,   0,   0,   0]  → 2 attributes
Q2:     [0,   0,   0,   1,   0,   0]  → 1 attribute
Q3:     [1,   0,   0,   0,   1,   0]  → 2 attributes
Q4:     [0,   1,   1,   0,   0,   0]  → 2 attributes
```

---

## API Response

```json
{
  "level": "chapter",
  "level_id": "algebra-chapter-uuid",
  "total_questions": 4,
  "attribute_count": 6,

  "attributes": [
    {
      "id": "attr-1",
      "name": "Algebraic Manipulation",
      "description": "Simplifying and manipulating algebraic expressions",
      "topic_id": "topic-1-uuid"
    },
    {
      "id": "attr-2",
      "name": "Equation Solving",
      "description": "Solving linear equations",
      "topic_id": "topic-1-uuid"
    },
    {
      "id": "attr-3",
      "name": "Substitution Method",
      "description": "Using substitution to solve systems",
      "topic_id": "topic-1-uuid"
    },
    {
      "id": "attr-4",
      "name": "Factorization",
      "description": "Factoring quadratic expressions",
      "topic_id": "topic-2-uuid"
    },
    {
      "id": "attr-5",
      "name": "Quadratic Formula",
      "description": "Applying quadratic formula",
      "topic_id": "topic-2-uuid"
    },
    {
      "id": "attr-6",
      "name": "Completing the Square",
      "description": "Completing the square method",
      "topic_id": "topic-2-uuid"
    }
  ],

  "questions": [
    {
      "id": "q1-uuid",
      "content": "Solve: 2x + 5 = 13",
      "options": ["x = 2", "x = 4", "x = 6", "x = 8"],
      "correct_answer": "x = 4",
      "topic_id": "topic-1-uuid",
      "q_vector": [1, 1, 0, 0, 0, 0],
      "attribute_count": 2
    },
    {
      "id": "q2-uuid",
      "content": "Solve: x² - 5x + 6 = 0 using factorization",
      "options": ["x = 1, 6", "x = 2, 3", "x = -2, -3", "x = 0, 5"],
      "correct_answer": "x = 2, 3",
      "topic_id": "topic-2-uuid",
      "q_vector": [0, 0, 0, 1, 0, 0],
      "attribute_count": 1
    },
    {
      "id": "q3-uuid",
      "content": "Solve: 2x² + 7x + 3 = 0 using quadratic formula",
      "options": [...],
      "correct_answer": "...",
      "topic_id": "topic-2-uuid",
      "q_vector": [1, 0, 0, 0, 1, 0],
      "attribute_count": 2
    },
    {
      "id": "q4-uuid",
      "content": "Solve system: {2x + y = 5, x - y = 1}",
      "options": [...],
      "correct_answer": "...",
      "topic_id": "topic-1-uuid",
      "q_vector": [0, 1, 1, 0, 0, 0],
      "attribute_count": 2
    }
  ],

  "pagination": {
    "total": 4,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "has_more": false
  }
}
```

---

## Using the Q-Matrix

### Python Example

```python
import numpy as np

# Extract Q-matrix
Q = np.array([
    [1, 1, 0, 0, 0, 0],  # Q1
    [0, 0, 0, 1, 0, 0],  # Q2
    [1, 0, 0, 0, 1, 0],  # Q3
    [0, 1, 1, 0, 0, 0]   # Q4
])

print("Q-Matrix shape:", Q.shape)
# Output: Q-Matrix shape: (4, 6)

# Attribute coverage (how many questions test each attribute)
coverage = Q.sum(axis=0)
print("Attribute coverage:", coverage)
# Output: [2, 2, 1, 1, 1, 0]
# Interpretation:
#   - Algebraic Manipulation: 2 questions
#   - Equation Solving: 2 questions
#   - Substitution: 1 question
#   - Factorization: 1 question
#   - Quadratic Formula: 1 question
#   - Completing Square: 0 questions (not tested!)

# Question complexity (number of attributes per question)
complexity = Q.sum(axis=1)
print("Question complexity:", complexity)
# Output: [2, 1, 2, 2]
```

### JavaScript Example

```javascript
const response = await fetch('/api/hierarchy/chapter/algebra-chapter-uuid/questions/enhanced');
const data = await response.json();

// Build Q-matrix as 2D array
const Q = data.questions.map(q => q.q_vector);

console.log('Q-Matrix:', Q);
// [
//   [1, 1, 0, 0, 0, 0],
//   [0, 0, 0, 1, 0, 0],
//   [1, 0, 0, 0, 1, 0],
//   [0, 1, 1, 0, 0, 0]
// ]

// Find which questions test "Equation Solving" (index 1)
const attr_idx = 1;
const questions_testing_attr = data.questions.filter(
  (q, idx) => Q[idx][attr_idx] === 1
);

console.log('Questions testing Equation Solving:', questions_testing_attr.length);
// Output: 2
```

---

## Benefits of Vector Format

### 1. **Efficient Storage**
- Compact binary representation
- Easy to serialize/deserialize
- Minimal data transfer

### 2. **Direct ML Integration**
```python
# Ready to use in ML models
from sklearn.ensemble import RandomForestClassifier

# Features = Q-vectors
X = np.array([q['q_vector'] for q in questions])

# Target = difficulty or student performance
y = np.array([q['difficulty'] for q in questions])

model = RandomForestClassifier()
model.fit(X, y)
```

### 3. **Matrix Operations**
```python
# Similarity between questions
from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity(Q)

# Questions similar to Q1
similar_to_q1 = np.argsort(similarity[0])[::-1][1:3]
print(f"Most similar to Q1: Q{similar_to_q1}")
```

### 4. **Easy Filtering**
```python
# Find questions testing exactly 2 attributes
q_with_2_attrs = [
    q for q in questions
    if q['attribute_count'] == 2
]

# Find questions testing "Factorization"
factorization_idx = 3
q_with_factorization = [
    q for q in questions
    if q['q_vector'][factorization_idx] == 1
]
```

---

## Visualization

### Attribute Coverage Heatmap

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Create heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(
    Q,
    cmap='YlOrRd',
    xticklabels=[a['name'] for a in attributes],
    yticklabels=[f"Q{i+1}" for i in range(len(questions))],
    cbar_kws={'label': 'Tests Attribute'}
)
plt.title('Q-Matrix: Questions × Attributes')
plt.xlabel('Attributes')
plt.ylabel('Questions')
plt.tight_layout()
plt.show()
```

### Attribute Coverage Bar Chart

```python
coverage = Q.sum(axis=0)
attr_names = [a['name'] for a in attributes]

plt.figure(figsize=(10, 5))
plt.bar(attr_names, coverage)
plt.xlabel('Attributes')
plt.ylabel('Number of Questions')
plt.title('Attribute Coverage in Chapter')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
```

---

## Summary

The q_vector format provides:
- ✅ Consistent attribute indexing across all questions
- ✅ Binary representation (0 or 1)
- ✅ Ready for matrix operations
- ✅ Easy to understand and use
- ✅ Efficient for ML/analytics
- ✅ Reveals attribute coverage gaps

**Key Point:** Each question's q_vector maps directly to the `attributes` array by index!
