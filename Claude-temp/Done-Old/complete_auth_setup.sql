-- ============================================================
-- COMPLETE SETUP: Add user_id columns + RLS policies
-- ============================================================

-- STEP 1: Add user_id columns to all tables
-- ============================================================

ALTER TABLE public.areas 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.categories 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.attribute_definitions 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.events 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.event_attributes 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.event_attachments 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.templates 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;


-- STEP 2: Enable RLS on all tables
-- ============================================================

ALTER TABLE public.areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attribute_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.templates ENABLE ROW LEVEL SECURITY;


-- STEP 3: Drop any existing policies
-- ============================================================

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

DROP POLICY IF EXISTS "Users can view own events" ON public.events;
DROP POLICY IF EXISTS "Users can insert own events" ON public.events;
DROP POLICY IF EXISTS "Users can update own events" ON public.events;
DROP POLICY IF EXISTS "Users can delete own events" ON public.events;

DROP POLICY IF EXISTS "Users can view own event_attributes" ON public.event_attributes;
DROP POLICY IF EXISTS "Users can insert own event_attributes" ON public.event_attributes;
DROP POLICY IF EXISTS "Users can update own event_attributes" ON public.event_attributes;
DROP POLICY IF EXISTS "Users can delete own event_attributes" ON public.event_attributes;

DROP POLICY IF EXISTS "Users can view own attachments" ON public.event_attachments;
DROP POLICY IF EXISTS "Users can insert own attachments" ON public.event_attachments;
DROP POLICY IF EXISTS "Users can update own attachments" ON public.event_attachments;
DROP POLICY IF EXISTS "Users can delete own attachments" ON public.event_attachments;

DROP POLICY IF EXISTS "Users can view own templates" ON public.templates;
DROP POLICY IF EXISTS "Users can insert own templates" ON public.templates;
DROP POLICY IF EXISTS "Users can update own templates" ON public.templates;
DROP POLICY IF EXISTS "Users can delete own templates" ON public.templates;


-- STEP 4: Create proper RLS policies
-- ============================================================

-- AREAS policies
CREATE POLICY "Users can view own areas" ON public.areas
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own areas" ON public.areas
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own areas" ON public.areas
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own areas" ON public.areas
FOR DELETE USING (auth.uid() = user_id);

-- CATEGORIES policies
CREATE POLICY "Users can view own categories" ON public.categories
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own categories" ON public.categories
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own categories" ON public.categories
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own categories" ON public.categories
FOR DELETE USING (auth.uid() = user_id);

-- ATTRIBUTE_DEFINITIONS policies
CREATE POLICY "Users can view own attributes" ON public.attribute_definitions
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own attributes" ON public.attribute_definitions
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own attributes" ON public.attribute_definitions
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own attributes" ON public.attribute_definitions
FOR DELETE USING (auth.uid() = user_id);

-- EVENTS policies
CREATE POLICY "Users can view own events" ON public.events
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own events" ON public.events
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own events" ON public.events
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own events" ON public.events
FOR DELETE USING (auth.uid() = user_id);

-- EVENT_ATTRIBUTES policies
CREATE POLICY "Users can view own event_attributes" ON public.event_attributes
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own event_attributes" ON public.event_attributes
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own event_attributes" ON public.event_attributes
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own event_attributes" ON public.event_attributes
FOR DELETE USING (auth.uid() = user_id);

-- EVENT_ATTACHMENTS policies
CREATE POLICY "Users can view own attachments" ON public.event_attachments
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own attachments" ON public.event_attachments
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own attachments" ON public.event_attachments
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own attachments" ON public.event_attachments
FOR DELETE USING (auth.uid() = user_id);

-- TEMPLATES policies
CREATE POLICY "Users can view own templates" ON public.templates
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own templates" ON public.templates
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own templates" ON public.templates
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own templates" ON public.templates
FOR DELETE USING (auth.uid() = user_id);


-- STEP 5: Verify setup
-- ============================================================

-- Check that user_id columns exist
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name IN ('areas', 'categories', 'attribute_definitions', 'events', 'event_attributes', 'event_attachments', 'templates')
    AND column_name = 'user_id'
ORDER BY table_name;

-- Check that RLS is enabled
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('areas', 'categories', 'attribute_definitions', 'events', 'event_attributes', 'event_attachments', 'templates')
ORDER BY tablename;
