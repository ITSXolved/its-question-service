# Concept Resources API Documentation

## Overview
This API allows you to add and manage educational resources (videos, images, 3D models, virtual labs, animations, etc.) for concepts in your learning management system.

## Database Schema

### Table: `concept_resources`

```sql
CREATE TABLE IF NOT EXISTS concept_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL, -- 'video', 'image', '3d_model', 'animation', 'virtual_lab', 'pdf', 'interactive'
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration INTEGER, -- for videos/animations in seconds
    file_size INTEGER, -- in bytes
    metadata JSONB, -- store additional properties like resolution, format, author, etc.
    order_index INTEGER DEFAULT 0, -- for sorting resources
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_concept_resources_concept_id ON concept_resources(concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_resources_type ON concept_resources(resource_type);
```

### Resource Types
- `video` - Video content (YouTube, Vimeo, uploaded videos)
- `image` - Images and diagrams
- `3d_model` - 3D models (OBJ, GLTF, etc.)
- `animation` - Animated content
- `virtual_lab` - Virtual laboratory simulations
- `pdf` - PDF documents
- `interactive` - Interactive content/widgets

## API Endpoints

### 1. Add a Single Resource to a Concept

**Endpoint:** `POST /api/concepts/<concept_id>/resources`

**Description:** Add a single resource (video, image, 3D model, etc.) to a concept.

**Request Body:**
```json
{
  "resource_type": "video",
  "title": "Introduction to Photosynthesis",
  "description": "A detailed video explaining the process of photosynthesis",
  "url": "https://www.youtube.com/watch?v=example",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "duration": 300,
  "file_size": 1024000,
  "metadata": {
    "author": "John Doe",
    "resolution": "1080p",
    "language": "English"
  },
  "order_index": 0
}
```

**Required Fields:**
- `resource_type` - Must be one of: video, image, 3d_model, animation, virtual_lab, pdf, interactive
- `title` - Resource title
- `url` - URL to the resource

**Optional Fields:**
- `description` - Resource description
- `thumbnail_url` - URL to thumbnail image
- `duration` - Duration in seconds (for videos/animations)
- `file_size` - File size in bytes
- `metadata` - JSONB object for additional properties
- `order_index` - For sorting (default: 0)
- `is_active` - Active status (default: true)

**Response (201 Created):**
```json
{
  "id": "uuid-here",
  "concept_id": "concept-uuid",
  "resource_type": "video",
  "title": "Introduction to Photosynthesis",
  "description": "A detailed video explaining the process of photosynthesis",
  "url": "https://www.youtube.com/watch?v=example",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "duration": 300,
  "file_size": 1024000,
  "metadata": {
    "author": "John Doe",
    "resolution": "1080p",
    "language": "English"
  },
  "order_index": 0,
  "is_active": true,
  "created_at": "2025-10-04T10:00:00Z",
  "updated_at": "2025-10-04T10:00:00Z"
}
```

---

### 2. Get All Resources for a Concept

**Endpoint:** `GET /api/concepts/<concept_id>/resources`

**Description:** Retrieve all resources for a specific concept.

**Query Parameters:**
- `resource_type` (optional) - Filter by resource type
- `is_active` (optional) - Filter by active status (default: true)

**Example:**
```
GET /api/concepts/abc-123/resources?resource_type=video
```

**Response (200 OK):**
```json
{
  "concept_id": "abc-123",
  "concept_name": "Photosynthesis",
  "resources": [
    {
      "id": "resource-uuid-1",
      "resource_type": "video",
      "title": "Introduction to Photosynthesis",
      "url": "https://youtube.com/...",
      ...
    },
    {
      "id": "resource-uuid-2",
      "resource_type": "3d_model",
      "title": "Chloroplast 3D Model",
      "url": "https://example.com/model.gltf",
      ...
    }
  ],
  "count": 2
}
```

---

### 3. Add Multiple Resources in Bulk

**Endpoint:** `POST /api/concepts/<concept_id>/resources/bulk`

**Description:** Add multiple resources to a concept at once.

**Request Body:**
```json
{
  "resources": [
    {
      "resource_type": "video",
      "title": "Introduction Video",
      "url": "https://youtube.com/...",
      "description": "Basic introduction",
      "duration": 180
    },
    {
      "resource_type": "3d_model",
      "title": "3D Model of Chloroplast",
      "url": "https://example.com/model.gltf",
      "file_size": 2048000
    },
    {
      "resource_type": "virtual_lab",
      "title": "Photosynthesis Simulator",
      "url": "https://example.com/lab",
      "metadata": {
        "interactive": true,
        "difficulty": "medium"
      }
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "created_count": 3,
  "resources": [
    { "id": "uuid-1", ... },
    { "id": "uuid-2", ... },
    { "id": "uuid-3", ... }
  ]
}
```

---

### 4. Get a Specific Resource

**Endpoint:** `GET /api/resources/<resource_id>`

**Description:** Get details of a specific resource by its ID.

**Response (200 OK):**
```json
{
  "id": "resource-uuid",
  "concept_id": "concept-uuid",
  "resource_type": "video",
  "title": "Introduction to Photosynthesis",
  ...
}
```

---

### 5. Update a Resource

**Endpoint:** `PUT /api/resources/<resource_id>`

**Description:** Update any fields of an existing resource.

**Request Body (partial update):**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "url": "https://new-url.com"
}
```

**Response (200 OK):**
```json
{
  "id": "resource-uuid",
  "title": "Updated Title",
  "description": "Updated description",
  ...
}
```

---

### 6. Delete a Resource (Soft Delete)

**Endpoint:** `DELETE /api/resources/<resource_id>`

**Description:** Soft delete a resource by setting `is_active = false`.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Resource deleted successfully"
}
```

---

### 7. Permanently Delete a Resource

**Endpoint:** `DELETE /api/resources/<resource_id>/permanent`

**Description:** Permanently remove a resource from the database.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Resource permanently deleted"
}
```

---

### 8. Get All Resources for a Topic

**Endpoint:** `GET /api/topics/<topic_id>/resources`

**Description:** Get all resources for all concepts under a topic, grouped by concept.

**Response (200 OK):**
```json
{
  "topic_id": "topic-uuid",
  "topic_name": "Plant Biology",
  "concepts": [
    {
      "concept_id": "concept-1",
      "concept_name": "Photosynthesis",
      "concept_description": "Process by which plants make food",
      "resources": [
        {
          "id": "res-1",
          "resource_type": "video",
          "title": "Intro to Photosynthesis",
          ...
        },
        {
          "id": "res-2",
          "resource_type": "3d_model",
          "title": "Chloroplast Model",
          ...
        }
      ],
      "resource_count": 2
    },
    {
      "concept_id": "concept-2",
      "concept_name": "Respiration",
      "resources": [...],
      "resource_count": 3
    }
  ],
  "total_resources": 5
}
```

---

## Usage Examples

### Example 1: Add a YouTube Video
```bash
curl -X POST http://localhost:5200/api/concepts/abc-123/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "video",
    "title": "Introduction to Quantum Mechanics",
    "description": "Basic concepts of quantum mechanics",
    "url": "https://www.youtube.com/watch?v=example",
    "duration": 600,
    "metadata": {
      "platform": "YouTube",
      "quality": "1080p"
    }
  }'
```

### Example 2: Add a 3D Model
```bash
curl -X POST http://localhost:5200/api/concepts/abc-123/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "3d_model",
    "title": "Human Heart 3D Model",
    "url": "https://example.com/models/heart.gltf",
    "thumbnail_url": "https://example.com/thumbnails/heart.png",
    "file_size": 5242880,
    "metadata": {
      "format": "GLTF",
      "polygons": 50000,
      "textures": true
    }
  }'
```

### Example 3: Add Virtual Lab Simulation
```bash
curl -X POST http://localhost:5200/api/concepts/abc-123/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "virtual_lab",
    "title": "Chemistry Lab Simulator",
    "description": "Interactive chemistry experiments",
    "url": "https://lab.example.com/chemistry",
    "metadata": {
      "experiments": ["titration", "distillation"],
      "difficulty": "intermediate"
    }
  }'
```

### Example 4: Bulk Add Resources
```bash
curl -X POST http://localhost:5200/api/concepts/abc-123/resources/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "resources": [
      {
        "resource_type": "video",
        "title": "Lecture 1",
        "url": "https://youtube.com/v1"
      },
      {
        "resource_type": "pdf",
        "title": "Course Notes",
        "url": "https://example.com/notes.pdf"
      },
      {
        "resource_type": "animation",
        "title": "Process Animation",
        "url": "https://example.com/animation.mp4",
        "duration": 120
      }
    ]
  }'
```

### Example 5: Get Only Videos for a Concept
```bash
curl -X GET "http://localhost:5200/api/concepts/abc-123/resources?resource_type=video"
```

### Example 6: Update a Resource
```bash
curl -X PUT http://localhost:5200/api/resources/resource-uuid \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "description": "Updated description"
  }'
```

---

## Integration with Existing System

The resources are linked to **concepts** in your hierarchical knowledge structure:
```
Exam → Subject → Chapter → Topic → Concept → Resources
```

Each concept can have multiple resources of different types, allowing you to provide rich multimedia learning materials for students.

---

## Metadata Field Examples

The `metadata` JSONB field is flexible and can store any additional properties:

**For Videos:**
```json
{
  "platform": "YouTube",
  "quality": "1080p",
  "language": "English",
  "subtitles": ["English", "Spanish"],
  "creator": "Khan Academy"
}
```

**For 3D Models:**
```json
{
  "format": "GLTF",
  "polygons": 50000,
  "animated": true,
  "textures": true,
  "fileFormat": "glb"
}
```

**For Virtual Labs:**
```json
{
  "platform": "PhET",
  "interactive": true,
  "experiments": ["experiment1", "experiment2"],
  "difficulty": "intermediate",
  "supported_browsers": ["Chrome", "Firefox"]
}
```

**For Images:**
```json
{
  "resolution": "1920x1080",
  "format": "PNG",
  "license": "CC-BY-4.0",
  "source": "NASA"
}
```

---

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "error": "Invalid request data"
}
```

**404 Not Found:**
```json
{
  "error": "Concept not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Error message here"
}
```

---

## Next Steps

1. **Create the table in Supabase:**
   - Go to Supabase Dashboard → SQL Editor
   - Run the SQL schema provided above

2. **Test the endpoints:**
   - Use the examples above to test adding resources
   - Verify data is stored correctly in Supabase

3. **Frontend Integration:**
   - Use these endpoints in your frontend to display resources
   - Create UI for uploading/managing resources

4. **Additional Features (Future):**
   - File upload support for storing resources directly
   - Resource analytics (views, completion rates)
   - User-specific resource recommendations
   - Resource ratings and reviews
