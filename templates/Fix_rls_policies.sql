-- ============================================================
-- FIX: Update RLS policies to allow NULL user_id (test data)
-- This allows test data to be visible to everyone
-- ============================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own areas" ON public.areas;
DROP POLICY IF EXISTS "Users can insert own areas" ON public.areas;
DROP POLICY IF EXISTS "Users can update own areas" ON public.areas;
DROP POLICY IF EXISTS "Users can delete own areas" ON public.areas;

DROP POLICY IF EXISTS "Users can view own categories" ON public.categories;
DROP POLICY IF EXISTS "Users can insert own categories" ON public.categories;
DROP POLICY IF EXISTS "Users can update own categories" ON public.categories;
DROP POLICY IF EXISTS "Users can delete own categories" ON public.categories;

DROP POLICY IF EXISTS "Users can view own attributes" ON public.attribute_definitions;
DROP POLICY IF EXISTS "Users can insert own attributes" ON public.attribute_definitions;
DROP POLICY IF EXISTS "Users can update own attributes" ON public.attribute_definitions;
DROP POLICY IF EXISTS "Users can delete own attributes" ON public.attribute_definitions;

-- Create new policies that allow NULL user_id (test data) OR matching user_id
-- AREAS policies
CREATE POLICY "Users can view own areas or test data" ON public.areas
FOR SELECT USING (user_id IS NULL OR user_id = auth.uid());

CREATE POLICY "Users can insert own areas" ON public.areas
FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own areas or test data" ON public.areas
FOR UPDATE USING (user_id IS NULL OR user_id = auth.uid());

CREATE POLICY "Users can delete own areas or test data" ON public.areas
FOR DELETE USING (user_id IS NULL OR user_id = auth.uid());

-- CATEGORIES policies
CREATE POLICY "Users can view own categories or test data" ON public.categories
FOR SELECT USING (user_id IS NULL OR user_id = auth.uid());

CREATE POLICY "Users can insert own categories" ON public.categories
FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own categories or test data" ON public.categories
FOR UPDATE USING (user_id IS NULL OR user_id = auth.uid());

CREATE POLICY "Users can delete own categories or test data" ON public.categories
FOR DELETE USING (user_id IS NULL OR user_id = auth.uid());

-- ATTRIBUTE_DEFINITIONS policies
CREATE POLICY "Users can view own attributes or test data" ON public.attribute_definitions
FOR SELECT USING (user_id IS NULL OR user_id = auth.uid());

CREATE POLICY "Users can insert own attributes" ON public.attribute_definitions
FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own attributes or test data" ON public.attribute_definitions
FOR UPDATE USING (user_id IS NULL OR user_id = auth.uid());

CREATE POLICY "Users can delete own attributes or test data" ON public.attribute_definitions
FOR DELETE USING (user_id IS NULL OR user_id = auth.uid());

-- Verify: Count records that should now be visible
SELECT 'areas' as table_name, COUNT(*) as visible_rows 
FROM public.areas 
WHERE user_id IS NULL

UNION ALL

SELECT 'categories', COUNT(*) 
FROM public.categories 
WHERE user_id IS NULL

UNION ALL

SELECT 'attribute_definitions', COUNT(*) 
FROM public.attribute_definitions 
WHERE user_id IS NULL;