-- ============================================================
-- FIX: Add user_id to existing test data
-- This allows the test user to see the data
-- ============================================================

-- Set user_id for all areas
UPDATE public.areas 
SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- Set user_id for all categories
UPDATE public.categories 
SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- Set user_id for all attribute_definitions
UPDATE public.attribute_definitions 
SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- Verify the changes
SELECT 'areas' as table_name, COUNT(*) as updated_rows 
FROM public.areas 
WHERE user_id = '00000000-0000-0000-0000-000000000000'

UNION ALL

SELECT 'categories' as table_name, COUNT(*) as updated_rows 
FROM public.categories 
WHERE user_id = '00000000-0000-0000-0000-000000000000'

UNION ALL

SELECT 'attribute_definitions' as table_name, COUNT(*) as updated_rows 
FROM public.attribute_definitions 
WHERE user_id = '00000000-0000-0000-0000-000000000000';