# Topic Resources API - Setup Guide

## Overview

This guide will help you set up and test the **Topic Resources API** - a system for managing educational resources (videos, images, 3D models, virtual labs, animations, etc.) attached to **topics** in your learning hierarchy.

## Why Topic-Level Resources?

Resources are now attached to **topics** instead of concepts because:
- ✅ Topics are higher-level learning units
- ✅ Resources can apply to multiple concepts under a topic
- ✅ Better organization and less duplication
- ✅ Easier content management
- ✅ More scalable for large content libraries

## Table Structure

### `topic_resources` Table

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| topic_id | UUID | Foreign key to topics table |
| resource_type | TEXT | Type: video, image, 3d_model, animation, virtual_lab, pdf, interactive, article, simulation |
| title | TEXT | Resource title |
| description | TEXT | Resource description |
| url | TEXT | URL to the resource |
| thumbnail_url | TEXT | URL to thumbnail image |
| duration | INTEGER | Duration in seconds (for videos/animations) |
| file_size | INTEGER | File size in bytes |
| metadata | JSONB | Additional properties (flexible JSON) |
| order_index | INTEGER | For sorting resources |
| is_active | BOOLEAN | Active status (for soft delete) |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

---

## Step-by-Step Setup

### Step 1: Create the Database Table

1. **Open Supabase Dashboard**: https://supabase.com/dashboard
2. Navigate to your project
3. Go to **SQL Editor** (left sidebar)
4. Click **New Query**
5. Copy and paste the contents of `CREATE_TOPIC_RESOURCES_TABLE.sql`
6. Click **Run** or press `Ctrl+Enter` / `Cmd+Enter`

The script will create:
- ✅ `topic_resources` table
- ✅ Indexes for performance
- ✅ Constraints for data validation
- ✅ Auto-update trigger for `updated_at`

### Step 2: Verify Environment Variables

Make sure your `.env` file contains:

```env
SUPABASE_URL=https://enilfsnxhqcafhigmzsc.supabase.co
SUPABASE_KEY=your_supabase_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

### Step 3: Install Dependencies

```bash
cd "/Users/zainuscloud/Documents/Xolway Docs/Software Code/Backend Service/its-question-service"
pip install -r requirements.txt
```

### Step 4: Start the Flask Server

**Option A: Using the start script**
```bash
chmod +x start_server.sh
./start_server.sh
```

**Option B: Direct Python command**
```bash
python -m app.main
```

The server should start on **http://localhost:5200**

You should see:
```
 * Running on http://127.0.0.1:5200
 * Debugger is active!
```

### Step 5: Run the Tests

**Start Jupyter Notebook:**
```bash
jupyter notebook topic_resources_test.ipynb
```

**Run All Cells** to execute the comprehensive test suite.

---

## API Endpoints

### Resource Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/topics/<id>/resources` | Add single resource |
| POST | `/api/topics/<id>/resources/bulk` | Add multiple resources |
| GET | `/api/topics/<id>/resources` | Get all resources for topic |
| GET | `/api/topics/<id>/resources?resource_type=video` | Filter by type |
| GET | `/api/chapters/<id>/resources` | Get resources by chapter |
| GET | `/api/resources/<id>` | Get specific resource |
| PUT | `/api/resources/<id>` | Update resource |
| DELETE | `/api/resources/<id>` | Soft delete |
| DELETE | `/api/resources/<id>/permanent` | Permanent delete |

---

## Quick Test Examples

### 1. Add a Video Resource

```bash
curl -X POST http://localhost:5200/api/topics/YOUR_TOPIC_ID/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "video",
    "title": "Introduction to Photosynthesis",
    "description": "Basic concepts explained",
    "url": "https://www.youtube.com/watch?v=example",
    "duration": 600,
    "metadata": {
      "platform": "YouTube",
      "quality": "1080p"
    }
  }'
```

### 2. Add a Virtual Lab

```bash
curl -X POST http://localhost:5200/api/topics/YOUR_TOPIC_ID/resources \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "virtual_lab",
    "title": "Chemistry Simulator",
    "url": "https://phet.colorado.edu/chemistry",
    "metadata": {
      "platform": "PhET",
      "interactive": true
    }
  }'
```

### 3. Get All Resources

```bash
curl http://localhost:5200/api/topics/YOUR_TOPIC_ID/resources
```

### 4. Filter by Resource Type

```bash
curl http://localhost:5200/api/topics/YOUR_TOPIC_ID/resources?resource_type=video
```

---

## Resource Types Supported

| Type | Description | Examples |
|------|-------------|----------|
| `video` | Video content | YouTube, Vimeo, uploaded videos |
| `image` | Images and diagrams | PNG, JPG, SVG diagrams |
| `3d_model` | 3D models | GLTF, OBJ, FBX files |
| `animation` | Animated content | MP4 animations, GIFs |
| `virtual_lab` | Virtual labs | PhET, Labster simulations |
| `pdf` | PDF documents | Study guides, textbooks |
| `interactive` | Interactive widgets | H5P, interactive apps |
| `article` | Articles | Blog posts, research papers |
| `simulation` | Simulations | Physics, chemistry sims |

---

## Test Coverage

The test notebook (`topic_resources_test.ipynb`) includes:

1. ✅ Add single video resource
2. ✅ Add 3D model resource
3. ✅ Add virtual lab resource
4. ✅ Bulk add multiple resources
5. ✅ Get all resources for topic
6. ✅ Filter resources by type
7. ✅ Update resource
8. ✅ Get chapter resources (grouped by topics)
9. ✅ Soft delete resource
10. ✅ Error handling (invalid types, missing fields, invalid IDs)
11. ✅ Resource statistics and summaries

---

## Troubleshooting

### Error: Connection Refused
- **Problem:** Flask server is not running
- **Solution:** Start the server using `./start_server.sh` or `python -m app.main`

### Error: Table doesn't exist
- **Problem:** `topic_resources` table not created
- **Solution:** Run the SQL script in Supabase

### Error: Topic not found (404)
- **Problem:** Topic ID doesn't exist
- **Solution:** Create a topic first or use an existing topic ID from your database

### Error: Invalid resource type
- **Problem:** Using unsupported resource type
- **Solution:** Use one of: video, image, 3d_model, animation, virtual_lab, pdf, interactive, article, simulation

---

## File Structure

```
its-question-service/
├── CREATE_TOPIC_RESOURCES_TABLE.sql   # Database schema
├── topic_resources_test.ipynb         # Test suite
├── docs/
│   └── TOPIC_RESOURCES_API.md        # Complete API docs
├── app/
│   └── main.py                        # Updated endpoints (lines 2046-2383)
└── TOPIC_RESOURCES_SETUP.md          # This file
```

---

## Next Steps

1. ✅ Create the database table in Supabase
2. ✅ Start the Flask server
3. ✅ Run the test notebook
4. 📱 Integrate into your frontend application
5. 🎨 Build UI for resource management
6. 📊 Add analytics for resource usage

---

## Frontend Integration Example

```javascript
// Add a video resource
async function addVideoResource(topicId) {
  const response = await fetch(`/api/topics/${topicId}/resources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resource_type: 'video',
      title: 'Introduction Video',
      url: 'https://youtube.com/watch?v=...',
      duration: 600,
      metadata: {
        platform: 'YouTube',
        quality: '1080p'
      }
    })
  });

  const resource = await response.json();
  console.log('Created:', resource);
}

// Get all resources for a topic
async function getTopicResources(topicId, resourceType = null) {
  let url = `/api/topics/${topicId}/resources`;
  if (resourceType) {
    url += `?resource_type=${resourceType}`;
  }

  const response = await fetch(url);
  const data = await response.json();

  return data.resources;
}

// Get resources grouped by topics for a chapter
async function getChapterResources(chapterId) {
  const response = await fetch(`/api/chapters/${chapterId}/resources`);
  const data = await response.json();

  // data.topics contains array of topics with their resources
  return data.topics;
}
```

---

## Support

For detailed API documentation, see: [docs/TOPIC_RESOURCES_API.md](docs/TOPIC_RESOURCES_API.md)

For questions or issues, check the test notebook for working examples.
