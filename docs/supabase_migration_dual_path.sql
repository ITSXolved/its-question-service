-- Migration: Dual Path Hierarchy (School vs Competitive Exam)
-- This migration adds support for two different hierarchical paths:
-- 1. Competitive Exam: Exam → Subject → Chapter → Topic → Attributes
-- 2. School: Exam → Class → Subject → Chapter → Topic → Attributes

-- =====================================================
-- STEP 1: Add exam_type to exams table
-- =====================================================

-- Add exam_type column to distinguish between school and competitive exams
ALTER TABLE exams ADD COLUMN exam_type VARCHAR(20) DEFAULT 'competitive' CHECK (exam_type IN ('competitive', 'school'));

-- Update existing exams to be 'competitive' by default (or update manually as needed)
UPDATE exams SET exam_type = 'competitive' WHERE exam_type IS NULL;

-- Make exam_type NOT NULL
ALTER TABLE exams ALTER COLUMN exam_type SET NOT NULL;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_exams_exam_type ON exams(exam_type);

-- =====================================================
-- STEP 2: Create classes table (for school path)
-- =====================================================

CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID REFERENCES exams(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    class_number INTEGER,  -- e.g., 1, 2, 3... 12
    section TEXT,           -- e.g., 'A', 'B', 'C' (optional)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_class_per_exam UNIQUE(exam_id, name)
);

-- Add index
CREATE INDEX IF NOT EXISTS idx_classes_exam_id ON classes(exam_id);
CREATE INDEX IF NOT EXISTS idx_classes_class_number ON classes(class_number);

-- =====================================================
-- STEP 3: Modify subjects table to support both paths
-- =====================================================

-- Add class_id column to subjects (NULL for competitive exams)
ALTER TABLE subjects ADD COLUMN class_id UUID REFERENCES classes(id) ON DELETE CASCADE;

-- Add index
CREATE INDEX IF NOT EXISTS idx_subjects_class_id ON subjects(class_id);

-- Add constraint to ensure subjects belong to either exam directly (competitive) or through class (school)
-- A subject should have EITHER exam_id (for competitive) OR class_id (for school), but not both
ALTER TABLE subjects ADD CONSTRAINT check_subject_path
    CHECK (
        (exam_id IS NOT NULL AND class_id IS NULL) OR
        (exam_id IS NULL AND class_id IS NOT NULL)
    );

-- =====================================================
-- STEP 4: Update questions table to support both paths
-- =====================================================

-- Add class_id to questions table
ALTER TABLE questions ADD COLUMN class_id UUID REFERENCES classes(id) ON DELETE SET NULL;

-- Add index
CREATE INDEX IF NOT EXISTS idx_questions_class_id ON questions(class_id);

-- =====================================================
-- STEP 5: Create view for easy querying of full hierarchy
-- =====================================================

-- View for competitive exam path questions
CREATE OR REPLACE VIEW competitive_exam_questions AS
SELECT
    q.*,
    e.name as exam_name,
    e.exam_type,
    s.name as subject_name,
    c.name as chapter_name,
    t.name as topic_name
FROM questions q
LEFT JOIN exams e ON q.exam_id = e.id
LEFT JOIN subjects s ON q.subject_id = s.id
LEFT JOIN chapters c ON q.chapter_id = c.id
LEFT JOIN topics t ON q.topic_id = t.id
WHERE e.exam_type = 'competitive' OR e.exam_type IS NULL;

-- View for school path questions
CREATE OR REPLACE VIEW school_questions AS
SELECT
    q.*,
    e.name as exam_name,
    e.exam_type,
    cl.name as class_name,
    cl.class_number,
    s.name as subject_name,
    ch.name as chapter_name,
    t.name as topic_name
FROM questions q
LEFT JOIN exams e ON q.exam_id = e.id
LEFT JOIN classes cl ON q.class_id = cl.id
LEFT JOIN subjects s ON q.subject_id = s.id
LEFT JOIN chapters ch ON q.chapter_id = ch.id
LEFT JOIN topics t ON q.topic_id = t.id
WHERE e.exam_type = 'school';

-- =====================================================
-- STEP 6: Helper function to get complete hierarchy
-- =====================================================

-- Function to get the complete hierarchy for a question
CREATE OR REPLACE FUNCTION get_question_hierarchy(question_uuid UUID)
RETURNS TABLE (
    question_id UUID,
    exam_id UUID,
    exam_name TEXT,
    exam_type VARCHAR(20),
    class_id UUID,
    class_name TEXT,
    subject_id UUID,
    subject_name TEXT,
    chapter_id UUID,
    chapter_name TEXT,
    topic_id UUID,
    topic_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        q.id as question_id,
        e.id as exam_id,
        e.name as exam_name,
        e.exam_type,
        cl.id as class_id,
        cl.name as class_name,
        s.id as subject_id,
        s.name as subject_name,
        ch.id as chapter_id,
        ch.name as chapter_name,
        t.id as topic_id,
        t.name as topic_name
    FROM questions q
    LEFT JOIN exams e ON q.exam_id = e.id
    LEFT JOIN classes cl ON q.class_id = cl.id
    LEFT JOIN subjects s ON q.subject_id = s.id
    LEFT JOIN chapters ch ON q.chapter_id = ch.id
    LEFT JOIN topics t ON q.topic_id = t.id
    WHERE q.id = question_uuid;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- STEP 7: Update PYQ metadata table (if needed)
-- =====================================================

-- Add class_id to pyq_metadata if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'pyq_metadata') THEN
        ALTER TABLE pyq_metadata ADD COLUMN IF NOT EXISTS class_id UUID REFERENCES classes(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_pyq_metadata_class_id ON pyq_metadata(class_id);
    END IF;
END $$;

-- =====================================================
-- STEP 8: Sample data migration (optional)
-- =====================================================

-- Example: Create some school exams and classes
-- Uncomment and modify as needed

/*
-- Create a school exam
INSERT INTO exams (name, description, exam_type)
VALUES ('CBSE', 'Central Board of Secondary Education', 'school');

-- Get the exam_id
DO $$
DECLARE
    cbse_exam_id UUID;
    class_10_id UUID;
BEGIN
    SELECT id INTO cbse_exam_id FROM exams WHERE name = 'CBSE' LIMIT 1;

    -- Create classes
    INSERT INTO classes (exam_id, name, class_number, description)
    VALUES
        (cbse_exam_id, 'Class 10', 10, 'Class 10 CBSE'),
        (cbse_exam_id, 'Class 9', 9, 'Class 9 CBSE')
    RETURNING id INTO class_10_id;

    -- Create subjects for Class 10
    INSERT INTO subjects (class_id, name, description)
    VALUES
        (class_10_id, 'Mathematics', 'Class 10 Mathematics'),
        (class_10_id, 'Science', 'Class 10 Science'),
        (class_10_id, 'Social Science', 'Class 10 Social Science');
END $$;
*/

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check exam types
-- SELECT exam_type, COUNT(*) FROM exams GROUP BY exam_type;

-- Check classes
-- SELECT * FROM classes;

-- Check subjects with their paths
-- SELECT
--     s.id,
--     s.name,
--     CASE
--         WHEN s.exam_id IS NOT NULL THEN 'Competitive (Direct to Exam)'
--         WHEN s.class_id IS NOT NULL THEN 'School (Through Class)'
--     END as path_type,
--     e.name as exam_name,
--     c.name as class_name
-- FROM subjects s
-- LEFT JOIN exams e ON s.exam_id = e.id
-- LEFT JOIN classes c ON s.class_id = c.id;
