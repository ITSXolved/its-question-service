-- ============================================
-- Topic Resources Table Creation Script
-- ============================================
-- Run this in Supabase SQL Editor before testing the API

-- Create the topic_resources table
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
    metadata JSONB, -- store additional properties like resolution, format, author, etc.
    order_index INTEGER DEFAULT 0, -- for sorting resources
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_topic_resources_topic_id ON topic_resources(topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_resources_type ON topic_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_topic_resources_active ON topic_resources(is_active);

-- Add a check constraint for valid resource types
ALTER TABLE topic_resources
ADD CONSTRAINT check_resource_type
CHECK (resource_type IN ('video', 'image', '3d_model', 'animation', 'virtual_lab', 'pdf', 'interactive', 'article', 'simulation'));

-- Create a trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_topic_resources_updated_at
BEFORE UPDATE ON topic_resources
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '✅ topic_resources table created successfully!';
    RAISE NOTICE '✅ Indexes created successfully!';
    RAISE NOTICE '✅ Constraints added successfully!';
    RAISE NOTICE '✅ Trigger for updated_at created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'You can now run the API tests!';
END $$;

-- Optional: If you had concept_resources and want to migrate
-- Uncomment the following to migrate data from concept_resources to topic_resources

/*
INSERT INTO topic_resources (topic_id, resource_type, title, description, url, thumbnail_url, duration, file_size, metadata, order_index, is_active, created_at, updated_at)
SELECT
    c.topic_id,
    cr.resource_type,
    cr.title,
    cr.description,
    cr.url,
    cr.thumbnail_url,
    cr.duration,
    cr.file_size,
    cr.metadata,
    cr.order_index,
    cr.is_active,
    cr.created_at,
    cr.updated_at
FROM concept_resources cr
INNER JOIN concepts c ON cr.concept_id = c.id
WHERE c.topic_id IS NOT NULL;

-- Then optionally drop the old table
-- DROP TABLE IF EXISTS concept_resources CASCADE;
*/
