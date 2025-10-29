-- ============================================
-- Concept Resources Table Creation Script
-- ============================================
-- Run this in Supabase SQL Editor before testing the API

-- Create the concept_resources table
CREATE TABLE IF NOT EXISTS concept_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration INTEGER,
    file_size INTEGER,
    metadata JSONB,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_concept_resources_concept_id ON concept_resources(concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_resources_type ON concept_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_concept_resources_active ON concept_resources(is_active);

-- Add a check constraint for valid resource types
ALTER TABLE concept_resources
ADD CONSTRAINT check_resource_type
CHECK (resource_type IN ('video', 'image', '3d_model', 'animation', 'virtual_lab', 'pdf', 'interactive'));

-- Create a trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_concept_resources_updated_at
BEFORE UPDATE ON concept_resources
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '✅ concept_resources table created successfully!';
    RAISE NOTICE '✅ Indexes created successfully!';
    RAISE NOTICE '✅ Constraints added successfully!';
    RAISE NOTICE '✅ Trigger for updated_at created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'You can now run the API tests!';
END $$;
