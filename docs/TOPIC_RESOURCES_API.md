# Topic Resources API Documentation

## Overview
This API allows you to add and manage educational resources (videos, images, 3D models, virtual labs, animations, etc.) for **topics** in your learning management system. Resources are attached at the topic level for better organization and reusability.

## Database Schema

### Table: `topic_resources`

```sql
CREATE TABLE IF NOT EXISTS topic_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration INTEGER, -- for videos/animations in seconds
    file_size INTEGER, -- in bytes
    metadata JSONB, -- store additional properties
    order_index INTEGER DEFAULT 0, -- for sorting
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Resource Types
- `video` - Video content (YouTube, Vimeo, uploaded videos)
- `image` - Images and diagrams
- `3d_model` - 3D models (OBJ, GLTF, etc.)
- `animation` - Animated content
- `virtual_lab` - Virtual laboratory simulations
- `pdf` - PDF documents
- `interactive` - Interactive content/widgets
- `article` - Articles and blog posts
- `simulation` - Interactive simulations

## Hierarchy Structure

Resources are attached to **topics**:
```
Exam → Subject → Chapter → Topic → [Resources]
                                  → Concepts
```

**Why Topic-level?**
- Topics are higher-level learning units
- Resources can apply to multiple concepts under a topic
- Better organization and less duplication
- Easier content management

## API Endpoints

### 1. Add a Single Resource to a Topic

**Endpoint:** `POST /api/topics/<topic_id>/resources`

**Description:** Add a single resource to a topic.

**Request Body:**
```json
{
  "resource_type": "video",
  "title": "Introduction to Photosynthesis",
  "description": "A detailed video explaining photosynthesis",
  "url": "https://www.youtube.com/watch?v=example",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "duration": 600,
  "file_size": 1024000,
  "metadata": {
    "platform": "YouTube",
    "quality": "1080p",
    "language": "English",
    "creator": "Khan Academy"
  },
  "order_index": 0
}
```

**Required Fields:**
- `resource_type` - One of: video, image, 3d_model, animation, virtual_lab, pdf, interactive, article, simulation
- `title` - Resource title
- `url` - URL to the resource

**Response (201 Created):**
```json
{
  "id": "uuid-here",
  "topic_id": "topic-uuid",
  "resource_type": "video",
  "title": "Introduction to Photosynthesis",
  "url": "https://www.youtube.com/watch?v=example",
  "created_at": "2025-10-04T10:00:00Z",
  ...
}
```

---

### 2. Get All Resources for a Topic

**Endpoint:** `GET /api/topics/<topic_id>/resources`

**Query Parameters:**
- `resource_type` (optional) - Filter by resource type
- `is_active` (optional) - Filter by active status (default: true)

**Example:**
```
GET /api/topics/abc-123/resources?resource_type=video
```

**Response (200 OK):**
```json
{
  "topic_id": "abc-123",
  "topic_name": "Photosynthesis",
  "resources": [
    {
      "id": "resource-uuid-1",
      "resource_type": "video",
      "title": "Introduction to Photosynthesis",
      "url": "https://youtube.com/...",
      ...
    }
  ],
  "count": 1
}
```

---

### 3. Add Multiple Resources in Bulk

**Endpoint:** `POST /api/topics/<topic_id>/resources/bulk`

**Request Body:**
```json
{
  "resources": [
    {
      "resource_type": "video",
      "title": "Introduction Video",
      "url": "https://youtube.com/...",
      "duration": 600
    },
    {
      "resource_type": "3d_model",
      "title": "Chloroplast 3D Model",
      "url": "https://example.com/model.gltf",
      "file_size": 2048000
    },
    {
      "resource_type": "virtual_lab",
      "title": "Photosynthesis Simulator",
      "url": "https://example.com/lab"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "created_count": 3,
  "resources": [...]
}
```

---

### 4. Get a Specific Resource

**Endpoint:** `GET /api/resources/<resource_id>`

**Response (200 OK):**
```json
{
  "id": "resource-uuid",
  "topic_id": "topic-uuid",
  "resource_type": "video",
  "title": "Introduction to Photosynthesis",
  ...
}
```

---

### 5. Update a Resource

**Endpoint:** `PUT /api/resources/<resource_id>`

**Request Body (partial update):**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "metadata": {
    "quality": "4K",
    "updated": true
  }
}
```

---

### 6. Delete a Resource (Soft Delete)

**Endpoint:** `DELETE /api/resources/<resource_id>`

**Description:** Soft delete by setting `is_active = false`.

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

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Resource permanently deleted"
}
```

---

### 8. Get All Resources for a Chapter

**Endpoint:** `GET /api/chapters/<chapter_id>/resources`

**Description:** Get all resources for all topics under a chapter, grouped by topic.

**Response (200 OK):**
```json
{
  "chapter_id": "chapter-uuid",
  "chapter_name": "Plant Biology",
  "topics": [
    {
      "topic_id": "topic-1",
      "topic_name": "Photosynthesis",
      "topic_description": "Process by which plants make food",
      "resources": [
        {
          "id": "res-1",
          "resource_type": "video",
          "title": "Intro to Photosynthesis",
          ...
        }
      ],
      "resource_count": 1
    },
    {
      "topic_id": "topic-2",
      "topic_name": "Respiration",
      "resources": [...],
      "resource_count": 3
    }
  ],
  "total_resources": 4
}
```

---

## Usage Examples

### Example 1: Add a YouTube Video
```bash
curl -X POST http://localhost:5200/api/topics/abc-123/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "video",
    "title": "Introduction to Quantum Mechanics",
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
curl -X POST http://localhost:5200/api/topics/abc-123/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "3d_model",
    "title": "Human Heart 3D Model",
    "url": "https://example.com/models/heart.gltf",
    "file_size": 5242880,
    "metadata": {
      "format": "GLTF",
      "polygons": 50000
    }
  }'
```

### Example 3: Add Virtual Lab
```bash
curl -X POST http://localhost:5200/api/topics/abc-123/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "virtual_lab",
    "title": "Chemistry Lab Simulator",
    "url": "https://phet.colorado.edu/chemistry",
    "metadata": {
      "platform": "PhET",
      "interactive": true
    }
  }'
```

### Example 4: Bulk Add Resources
```bash
curl -X POST http://localhost:5200/api/topics/abc-123/resources/bulk \
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
      }
    ]
  }'
```

### Example 5: Get Only Videos for a Topic
```bash
curl http://localhost:5200/api/topics/abc-123/resources?resource_type=video
```

### Example 6: Get All Resources for a Chapter
```bash
curl http://localhost:5200/api/chapters/xyz-789/resources
```

---

## Metadata Field Examples

The `metadata` JSONB field can store any additional properties:

**For Videos:**
```json
{
  "platform": "YouTube",
  "quality": "1080p",
  "language": "English",
  "subtitles": ["English", "Spanish"],
  "creator": "Khan Academy",
  "views": 1000000
}
```

**For 3D Models:**
```json
{
  "format": "GLTF",
  "polygons": 50000,
  "animated": true,
  "textures": true,
  "file_format": "glb"
}
```

**For Virtual Labs:**
```json
{
  "platform": "PhET",
  "interactive": true,
  "experiments": ["experiment1", "experiment2"],
  "difficulty": "intermediate"
}
```

**For Articles:**
```json
{
  "author": "Dr. Smith",
  "publication_date": "2024-01-15",
  "source": "Scientific American",
  "reading_time": 10
}
```

---

## Error Responses

**400 Bad Request:**
```json
{
  "error": "Invalid request data"
}
```

**404 Not Found:**
```json
{
  "error": "Topic not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Error message here"
}
```

---

## Complete API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/topics/<id>/resources` | Add single resource to topic |
| POST | `/api/topics/<id>/resources/bulk` | Add multiple resources to topic |
| GET | `/api/topics/<id>/resources` | Get all resources for topic |
| GET | `/api/chapters/<id>/resources` | Get resources grouped by topics |
| GET | `/api/resources/<id>` | Get specific resource |
| PUT | `/api/resources/<id>` | Update resource |
| DELETE | `/api/resources/<id>` | Soft delete resource |
| DELETE | `/api/resources/<id>/permanent` | Permanently delete resource |

---

## Benefits of Topic-Level Resources

1. **Better Organization** - Resources at topic level apply to all related concepts
2. **Less Duplication** - Share resources across multiple concepts
3. **Easier Management** - Manage resources at a higher, more logical level
4. **Scalability** - Better suited for large content libraries
5. **Flexibility** - Can still link specific concepts to resources via metadata if needed

---

## Migration from Concept-Level

If you previously had concept-level resources, the SQL script includes migration code:

```sql
-- Migrate from concept_resources to topic_resources
INSERT INTO topic_resources (topic_id, resource_type, title, ...)
SELECT c.topic_id, cr.resource_type, cr.title, ...
FROM concept_resources cr
INNER JOIN concepts c ON cr.concept_id = c.id
WHERE c.topic_id IS NOT NULL;
```

---

**Need Help?** Check the test notebook at `topic_resources_test.ipynb` for working examples.
