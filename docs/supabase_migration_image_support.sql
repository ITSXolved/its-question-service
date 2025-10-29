-- Migration: Add Image Support to Questions
-- This migration adds optional image URL columns to questions table

-- =====================================================
-- STEP 1: Add image columns to questions table
-- =====================================================

-- Add question_image_url column for question images
ALTER TABLE questions
ADD COLUMN IF NOT EXISTS question_image_url TEXT;

-- Add option_images column for option images (JSONB format)
-- Format: {"A": "url1", "B": "url2", "C": "url3", "D": "url4"}
ALTER TABLE questions
ADD COLUMN IF NOT EXISTS option_images JSONB DEFAULT '{}'::jsonb;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_questions_question_image
ON questions(question_image_url)
WHERE question_image_url IS NOT NULL;

-- =====================================================
-- STEP 2: Add image columns to pyq_metadata (if needed)
-- =====================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'pyq_metadata') THEN
        ALTER TABLE pyq_metadata
        ADD COLUMN IF NOT EXISTS solution_image_url TEXT;
    END IF;
END $$;

-- =====================================================
-- STEP 3: Create storage bucket (run this in Supabase Dashboard)
-- =====================================================

-- Note: This needs to be run in Supabase Dashboard or via the management API
-- 1. Go to Supabase Dashboard → Storage
-- 2. Create a new bucket named 'question-images'
-- 3. Set it to 'Public' if you want images to be publicly accessible
-- 4. Or use RLS policies for private access

-- =====================================================
-- STEP 4: Storage policies (optional - for public access)
-- =====================================================

-- Allow public read access to images
-- Run this if you created the bucket as private
/*
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'question-images');

-- Allow authenticated users to upload
CREATE POLICY "Authenticated Upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'question-images');

-- Allow users to delete their own uploads
CREATE POLICY "Users can delete own images"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'question-images');
*/

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check if columns were added successfully
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'questions'
-- AND column_name IN ('question_image_url', 'option_images');

-- Sample query to test the new columns
-- SELECT id, content, question_image_url, option_images
-- FROM questions
-- WHERE question_image_url IS NOT NULL
-- LIMIT 5;
