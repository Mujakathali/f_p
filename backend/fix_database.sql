-- SQL script to add user_id column to memories table
-- Run this in pgAdmin or psql

-- Check if user_id column exists
SELECT column_name 
FROM information_schema.columns 
WHERE table_name='memories' AND column_name='user_id';

-- Add user_id column if it doesn't exist
ALTER TABLE memories 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);

-- Update existing memories to assign them to the first user
UPDATE memories 
SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
WHERE user_id IS NULL;

-- Verify the changes
SELECT COUNT(*) as total_memories, 
       COUNT(user_id) as memories_with_user_id 
FROM memories;

-- Show sample data
SELECT id, user_id, type, LEFT(raw_text, 50) as text_preview 
FROM memories 
LIMIT 5;
