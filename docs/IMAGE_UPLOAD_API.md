# Image Upload API Documentation

## Overview

The Image Upload API allows you to attach images to questions and their options. Images are stored in Supabase Storage and referenced in the database.

## Setup

### 1. Run Database Migration

Execute the SQL migration to add image support:

```bash
# Run in Supabase SQL Editor
cat docs/supabase_migration_image_support.sql
```

### 2. Create Storage Bucket

**Option A: Via API (Recommended)**
```bash
POST /api/storage/bucket/create
```

**Option B: Via Supabase Dashboard**
1. Go to Supabase Dashboard → Storage
2. Create bucket named `question-images`
3. Set to Public or configure RLS policies

## Database Schema

### Questions Table Updates

```sql
-- New columns added to questions table
question_image_url TEXT              -- URL to question image
option_images JSONB DEFAULT '{}'     -- JSON object mapping option keys to image URLs

-- Example option_images format:
{
  "A": "https://supabase.co/storage/.../option_A.png",
  "B": "https://supabase.co/storage/.../option_B.png",
  "C": "https://supabase.co/storage/.../option_C.png",
  "D": "https://supabase.co/storage/.../option_D.png"
}
```

## API Endpoints

### 1. Upload Question Image

Upload an image for the question itself.

**Endpoint:** `POST /api/questions/{question_id}/image`

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form field named `image` with image file

**Example (cURL):**
```bash
curl -X POST \
  http://localhost:5200/api/questions/123e4567-e89b-12d3-a456-426614174000/image \
  -F "image=@question.png"
```

**Example (Python requests):**
```python
import requests

question_id = "123e4567-e89b-12d3-a456-426614174000"
files = {'image': open('question.png', 'rb')}

response = requests.post(
    f'http://localhost:5200/api/questions/{question_id}/image',
    files=files
)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "url": "https://.../question-images/questions/123.../question.png",
  "path": "questions/123.../question.png",
  "message": "Image uploaded successfully"
}
```

---

### 2. Upload Single Option Image

Upload an image for a specific option.

**Endpoint:** `POST /api/questions/{question_id}/options/{option_key}/image`

**Parameters:**
- `question_id`: UUID of the question
- `option_key`: Option identifier (e.g., "A", "B", "C", "D" or "0", "1", "2", "3")

**Example (cURL):**
```bash
curl -X POST \
  http://localhost:5200/api/questions/123e4567-e89b-12d3-a456-426614174000/options/A/image \
  -F "image=@option_a.png"
```

**Response:**
```json
{
  "success": true,
  "url": "https://.../question-images/questions/123.../options/option_A.png",
  "path": "questions/123.../options/option_A.png",
  "option_key": "A",
  "message": "Option image uploaded successfully"
}
```

---

### 3. Upload Multiple Option Images

Upload images for multiple options at once.

**Endpoint:** `POST /api/questions/{question_id}/options/images`

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form fields named `option_A`, `option_B`, `option_C`, `option_D`, etc.

**Example (Python):**
```python
import requests

question_id = "123e4567-e89b-12d3-a456-426614174000"
files = {
    'option_A': open('option_a.png', 'rb'),
    'option_B': open('option_b.png', 'rb'),
    'option_C': open('option_c.png', 'rb'),
    'option_D': open('option_d.png', 'rb')
}

response = requests.post(
    f'http://localhost:5200/api/questions/{question_id}/options/images',
    files=files
)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "total": 4,
  "success_count": 4,
  "message": "Uploaded 4/4 option images",
  "results": [
    {
      "success": true,
      "url": "https://.../option_A.png",
      "option_key": "A"
    },
    ...
  ]
}
```

---

### 4. Delete Question Images

Delete all images associated with a question.

**Endpoint:** `DELETE /api/questions/{question_id}/images`

**Example:**
```bash
curl -X DELETE \
  http://localhost:5200/api/questions/123e4567-e89b-12d3-a456-426614174000/images
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 5,
  "message": "Deleted 5 images"
}
```

---

## Complete Example Workflow

### Upload Question with Images

```python
import requests

# 1. Create question (existing endpoint)
question_data = {
    "question": {
        "content": "What is shown in the diagram?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "exam_id": "exam-id",
        "subject_id": "subject-id",
        "topic_id": "topic-id",
        "difficulty": 0.5,
        "discrimination": 1.0,
        "guessing": 0.25
    },
    "selected_attributes": [],
    "create_new_attributes": []
}

response = requests.post(
    'http://localhost:5200/api/questions/create-with-attributes',
    json=question_data
)
question = response.json()['question']
question_id = question['id']

# 2. Upload question image
with open('diagram.png', 'rb') as f:
    files = {'image': f}
    response = requests.post(
        f'http://localhost:5200/api/questions/{question_id}/image',
        files=files
    )
    print("Question image uploaded:", response.json())

# 3. Upload option images
option_files = {
    'option_A': open('option_a.png', 'rb'),
    'option_B': open('option_b.png', 'rb'),
    'option_C': open('option_c.png', 'rb'),
    'option_D': open('option_d.png', 'rb')
}

response = requests.post(
    f'http://localhost:5200/api/questions/{question_id}/options/images',
    files=option_files
)
print("Option images uploaded:", response.json())

# Close files
for f in option_files.values():
    f.close()
```

---

## Querying Questions with Images

Retrieve questions to see image URLs:

```python
import requests

question_id = "123e4567-e89b-12d3-a456-426614174000"
response = requests.get(f'http://localhost:5200/api/questions/{question_id}')

question = response.json()
print("Question image:", question.get('question_image_url'))
print("Option images:", question.get('option_images'))

# Example output:
# Question image: https://...supabase.co/storage/v1/object/public/question-images/questions/123.../question.png
# Option images: {
#   "A": "https://.../option_A.png",
#   "B": "https://.../option_B.png",
#   "C": "https://.../option_C.png",
#   "D": "https://.../option_D.png"
# }
```

---

## Storage Structure

Images are organized in Supabase Storage:

```
question-images/
└── questions/
    └── {question_id}/
        ├── question.{ext}           # Question image
        └── options/
            ├── option_A.{ext}       # Option A image
            ├── option_B.{ext}       # Option B image
            ├── option_C.{ext}       # Option C image
            └── option_D.{ext}       # Option D image
```

---

## Supported Image Formats

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- GIF (`.gif`)
- WebP (`.webp`)
- SVG (`.svg`)

---

## Error Handling

### Common Errors

**No file provided:**
```json
{
  "error": "No image file provided"
}
```

**Question not found:**
The image will upload but won't update the database if question doesn't exist.

**Storage errors:**
```json
{
  "success": false,
  "error": "Upload failed: ...",
  "message": "Failed to upload image: ..."
}
```

---

## Best Practices

1. **Image Size:** Compress images before upload (recommended max 2MB per image)
2. **Format:** Use PNG for diagrams, JPEG for photos
3. **Naming:** Use descriptive filenames for easier debugging
4. **Cleanup:** Delete old images when updating questions
5. **Security:** Ensure proper RLS policies if bucket is private

---

## Security Considerations

### Public Bucket (Default)
- Anyone can read images
- Only authenticated users can upload
- Configure in Supabase Dashboard

### Private Bucket (RLS)
```sql
-- Example RLS policies
CREATE POLICY "Public Read Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'question-images');

CREATE POLICY "Authenticated Upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'question-images');
```

---

## Testing

Run the image upload tests:

```bash
# Using pytest
pytest tests/test_image_upload.py

# Manual testing with curl
bash tests/test_image_upload.sh
```
