-- Migration: Change attributes from concept_id to topic_id
-- This migration makes attributes directly connected to topics instead of concepts

-- Step 1: Add topic_id column to attributes table
ALTER TABLE attributes ADD COLUMN topic_id UUID REFERENCES topics(id) ON DELETE CASCADE;

-- Step 2: Migrate existing data (populate topic_id from concept's topic_id)
-- This preserves existing attribute relationships by moving them to the parent topic
UPDATE attributes
SET topic_id = (
    SELECT c.topic_id
    FROM concepts c
    WHERE c.id = attributes.concept_id
);

-- Step 3: Drop the concept_id column
ALTER TABLE attributes DROP COLUMN concept_id;

-- Step 4: Make topic_id NOT NULL
ALTER TABLE attributes ALTER COLUMN topic_id SET NOT NULL;

-- Step 5: Add index on topic_id for better query performance
CREATE INDEX IF NOT EXISTS idx_attributes_topic_id ON attributes(topic_id);

-- Optional: Remove concept_id from questions table if you want to skip concepts entirely
-- Uncomment these lines if you want to completely remove concept references from questions
-- ALTER TABLE questions DROP COLUMN IF EXISTS concept_id;

-- Optional: Drop concepts table if no longer needed
-- WARNING: Only uncomment if you're absolutely sure concepts are not needed
-- DROP TABLE IF EXISTS concepts CASCADE;

-- Verify the migration
-- Run this to check that all attributes now have topic_id
SELECT COUNT(*) as total_attributes FROM attributes;
SELECT COUNT(*) as attributes_with_topic FROM attributes WHERE topic_id IS NOT NULL;
