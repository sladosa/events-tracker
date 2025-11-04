-- ============================================================
-- CLEANUP: Delete old data with NULL user_id
-- Run this in Supabase SQL Editor
-- ============================================================

-- WARNING: This will delete ALL existing data!
-- Make sure you're ready to start fresh!

-- Delete all attributes
DELETE FROM public.attribute_definitions WHERE user_id IS NULL;

-- Delete all categories  
DELETE FROM public.categories WHERE user_id IS NULL;

-- Delete all areas
DELETE FROM public.areas WHERE user_id IS NULL;

-- Verify cleanup (should return 0 for all)
SELECT 
    'areas' as table_name, 
    COUNT(*) as remaining_rows 
FROM public.areas 
WHERE user_id IS NULL

UNION ALL

SELECT 
    'categories' as table_name, 
    COUNT(*) as remaining_rows 
FROM public.categories 
WHERE user_id IS NULL

UNION ALL

SELECT 
    'attribute_definitions' as table_name, 
    COUNT(*) as remaining_rows 
FROM public.attribute_definitions 
WHERE user_id IS NULL;

-- Expected output: All counts should be 0
