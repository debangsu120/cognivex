-- Phase 4: Add candidate_status column to interviews table
-- Run this in Supabase SQL Editor

-- Add candidate_status column with default value
ALTER TABLE interviews ADD COLUMN IF NOT EXISTS candidate_status TEXT DEFAULT 'pending';

-- Add check constraint for valid statuses
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'interviews_candidate_status_check'
    ) THEN
        ALTER TABLE interviews ADD CONSTRAINT interviews_candidate_status_check
        CHECK (candidate_status IN ('pending', 'shortlisted', 'rejected', 'offered'));
    END IF;
END
$$;

-- Create index for faster status queries
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_status ON interviews(candidate_status);
CREATE INDEX IF NOT EXISTS idx_interviews_job_candidate_status ON interviews(job_id, candidate_status);

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'interviews' AND column_name = 'candidate_status';
