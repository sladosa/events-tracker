-- ============================================================
-- Events Tracker Database Schema
-- Generated: 2025-11-03 11:30:14
-- 
-- This schema implements an EAV (Entity-Attribute-Value) pattern
-- with full Row Level Security and CASCADE deletion
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- CORE TABLES
-- ============================================================

-- Users table (managed by Supabase Auth)
-- Note: This references auth.users from Supabase Auth
-- No need to create it, but we reference it in foreign keys

-- Templates table for reusable configurations
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    is_public BOOLEAN DEFAULT false,
    created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on templates
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

-- Templates policies
CREATE POLICY "Users can view public templates"
    ON templates FOR SELECT
    USING (is_public = true OR created_by = auth.uid());

CREATE POLICY "Users can create their own templates"
    ON templates FOR INSERT
    WITH CHECK (created_by = auth.uid());

CREATE POLICY "Users can update their own templates"
    ON templates FOR UPDATE
    USING (created_by = auth.uid());

CREATE POLICY "Users can delete their own templates"
    ON templates FOR DELETE
    USING (created_by = auth.uid());


-- ============================================================
-- METADATA TABLES (EAV Schema Definition)
-- ============================================================

-- Areas: Top-level organization
CREATE TABLE IF NOT EXISTS areas (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES templates(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    icon TEXT,
    color TEXT,
    sort_order INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories: Hierarchical organization within Areas
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY,
    area_id UUID REFERENCES areas(id) ON DELETE CASCADE,
    parent_category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    level INTEGER NOT NULL CHECK (level >= 1 AND level <= 10),
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Attribute Definitions: Define what data can be captured
CREATE TABLE IF NOT EXISTS attribute_definitions (
    id UUID PRIMARY KEY,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    data_type TEXT NOT NULL CHECK (data_type IN ('number', 'text', 'datetime', 'boolean', 'link', 'image')),
    unit TEXT,
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_rules JSONB DEFAULT '{}'::jsonb,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on metadata tables
ALTER TABLE areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE attribute_definitions ENABLE ROW LEVEL SECURITY;

-- Areas policies
CREATE POLICY "Users can view their own areas"
    ON areas FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can create their own areas"
    ON areas FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own areas"
    ON areas FOR UPDATE
    USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own areas"
    ON areas FOR DELETE
    USING (user_id = auth.uid());

-- Categories policies
CREATE POLICY "Users can view their categories"
    ON categories FOR SELECT
    USING (area_id IN (SELECT id FROM areas WHERE user_id = auth.uid()));

CREATE POLICY "Users can create their categories"
    ON categories FOR INSERT
    WITH CHECK (area_id IN (SELECT id FROM areas WHERE user_id = auth.uid()));

CREATE POLICY "Users can update their categories"
    ON categories FOR UPDATE
    USING (area_id IN (SELECT id FROM areas WHERE user_id = auth.uid()));

CREATE POLICY "Users can delete their categories"
    ON categories FOR DELETE
    USING (area_id IN (SELECT id FROM areas WHERE user_id = auth.uid()));

-- Attribute definitions policies
CREATE POLICY "Users can view their attribute definitions"
    ON attribute_definitions FOR SELECT
    USING (category_id IN (
        SELECT c.id FROM categories c
        JOIN areas a ON c.area_id = a.id
        WHERE a.user_id = auth.uid()
    ));

CREATE POLICY "Users can create their attribute definitions"
    ON attribute_definitions FOR INSERT
    WITH CHECK (category_id IN (
        SELECT c.id FROM categories c
        JOIN areas a ON c.area_id = a.id
        WHERE a.user_id = auth.uid()
    ));

CREATE POLICY "Users can update their attribute definitions"
    ON attribute_definitions FOR UPDATE
    USING (category_id IN (
        SELECT c.id FROM categories c
        JOIN areas a ON c.area_id = a.id
        WHERE a.user_id = auth.uid()
    ));

CREATE POLICY "Users can delete their attribute definitions"
    ON attribute_definitions FOR DELETE
    USING (category_id IN (
        SELECT c.id FROM categories c
        JOIN areas a ON c.area_id = a.id
        WHERE a.user_id = auth.uid()
    ));


-- ============================================================
-- DATA TABLES (Actual User Data)
-- ============================================================

-- Events: Main records
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    edited_at TIMESTAMPTZ DEFAULT NOW()
);

-- Event Attributes: EAV data storage
CREATE TABLE IF NOT EXISTS event_attributes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    attribute_definition_id UUID REFERENCES attribute_definitions(id) ON DELETE CASCADE,
    
    -- Value columns (only one will be populated per row)
    value_text TEXT,
    value_number DECIMAL,
    value_datetime TIMESTAMPTZ,
    value_boolean BOOLEAN,
    value_json JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure only one value type is set
    CONSTRAINT single_value_check CHECK (
        (value_text IS NOT NULL)::int +
        (value_number IS NOT NULL)::int +
        (value_datetime IS NOT NULL)::int +
        (value_boolean IS NOT NULL)::int +
        (value_json IS NOT NULL)::int = 1
    )
);

-- Event Attachments: Files, images, links
CREATE TABLE IF NOT EXISTS event_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    type TEXT CHECK (type IN ('image', 'link', 'file')),
    url TEXT NOT NULL,
    filename TEXT,
    size_bytes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on data tables
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_attachments ENABLE ROW LEVEL SECURITY;

-- Events policies
CREATE POLICY "Users can view their own events"
    ON events FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can create their own events"
    ON events FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own events"
    ON events FOR UPDATE
    USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own events"
    ON events FOR DELETE
    USING (user_id = auth.uid());

-- Event attributes policies
CREATE POLICY "Users can view their event attributes"
    ON event_attributes FOR SELECT
    USING (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

CREATE POLICY "Users can create their event attributes"
    ON event_attributes FOR INSERT
    WITH CHECK (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

CREATE POLICY "Users can update their event attributes"
    ON event_attributes FOR UPDATE
    USING (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

CREATE POLICY "Users can delete their event attributes"
    ON event_attributes FOR DELETE
    USING (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

-- Event attachments policies
CREATE POLICY "Users can view their event attachments"
    ON event_attachments FOR SELECT
    USING (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

CREATE POLICY "Users can create their event attachments"
    ON event_attachments FOR INSERT
    WITH CHECK (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

CREATE POLICY "Users can update their event attachments"
    ON event_attachments FOR UPDATE
    USING (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));

CREATE POLICY "Users can delete their event attachments"
    ON event_attachments FOR DELETE
    USING (event_id IN (SELECT id FROM events WHERE user_id = auth.uid()));


-- ============================================================
-- RLS HELPER FUNCTIONS
-- ============================================================

-- Function to check if user owns an area
CREATE OR REPLACE FUNCTION user_owns_area(area_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM areas 
        WHERE id = area_uuid AND user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's areas
CREATE OR REPLACE FUNCTION get_user_areas()
RETURNS SETOF areas AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM areas WHERE user_id = auth.uid()
    ORDER BY sort_order;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Areas indexes
CREATE INDEX IF NOT EXISTS idx_areas_user_id ON areas(user_id);
CREATE INDEX IF NOT EXISTS idx_areas_template_id ON areas(template_id);

-- Categories indexes
CREATE INDEX IF NOT EXISTS idx_categories_area_id ON categories(area_id);
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_category_id);

-- Attribute definitions indexes
CREATE INDEX IF NOT EXISTS idx_attr_def_category_id ON attribute_definitions(category_id);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_category_id ON events(category_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_events_user_date ON events(user_id, event_date DESC);

-- Event attributes indexes
CREATE INDEX IF NOT EXISTS idx_event_attr_event_id ON event_attributes(event_id);
CREATE INDEX IF NOT EXISTS idx_event_attr_def_id ON event_attributes(attribute_definition_id);

-- Event attachments indexes
CREATE INDEX IF NOT EXISTS idx_event_attach_event_id ON event_attachments(event_id);


-- ============================================================
-- METADATA INSERTS (from Excel template)
-- Note: Replace 'auth.uid()' with actual user UUID when running
-- ============================================================

-- Insert Areas
INSERT INTO areas (id, user_id, name, icon, color, sort_order, description) VALUES ('52227947-11bc-4508-811c-ce589a9012f8', auth.uid(), 'Health', '🏥', '#4CAF50', 1, 'Daily health metrics and wellness tracking');
INSERT INTO areas (id, user_id, name, icon, color, sort_order, description) VALUES ('c9a2f253-a944-4f9e-96b5-92c47e239e37', auth.uid(), 'Training', '💪', '#2196F3', 2, 'Workout activities and training sessions');

-- Insert Categories
INSERT INTO categories (id, area_id, parent_category_id, name, description, level, sort_order) VALUES ('f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', '52227947-11bc-4508-811c-ce589a9012f8', NULL, 'Sleep', 'Sleep tracking and analysis', 1, 1);
INSERT INTO categories (id, area_id, parent_category_id, name, description, level, sort_order) VALUES ('c7f37f3d-8478-4ce0-8bda-05efc08f59fc', '52227947-11bc-4508-811c-ce589a9012f8', NULL, 'Daily Wellness', 'Daily health metrics', 1, 2);
INSERT INTO categories (id, area_id, parent_category_id, name, description, level, sort_order) VALUES ('1e005740-26e1-40b7-8f97-4fb70de2f747', 'c9a2f253-a944-4f9e-96b5-92c47e239e37', NULL, 'Cardio', 'Cardiovascular training', 1, 1);
INSERT INTO categories (id, area_id, parent_category_id, name, description, level, sort_order) VALUES ('11abce6d-83e6-4508-969a-ef8bb3b18fc5', 'c9a2f253-a944-4f9e-96b5-92c47e239e37', NULL, 'Strength', 'Resistance training', 1, 2);
INSERT INTO categories (id, area_id, parent_category_id, name, description, level, sort_order) VALUES ('fb7eeb97-b3d9-41da-af6d-e40089ba3fe5', 'c9a2f253-a944-4f9e-96b5-92c47e239e37', '11abce6d-83e6-4508-969a-ef8bb3b18fc5', 'Upper Body', 'Upper body strength exercises', 2, 1);

-- Insert Attribute Definitions
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('8d8cf0c0-1aa6-4cc1-b559-c51ba86eb57a', 'f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', 'Total Sleep', 'number', 'hours', True, NULL, '{"min": 0, "max": 24}'::jsonb, 1);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('15b64707-796a-41ee-a39e-ba392831acd6', 'f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', 'Deep Sleep', 'number', 'hours', False, NULL, '{"min": 0, "max": 12}'::jsonb, 2);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('bd676387-c3f8-412c-bc87-d34755553884', 'f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', 'Sleep Quality', 'number', 'score', False, NULL, '{"min": 0, "max": 100}'::jsonb, 3);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('485e6b19-ed67-4432-9155-c4a64f409294', 'c7f37f3d-8478-4ce0-8bda-05efc08f59fc', 'Steps', 'number', 'steps', False, NULL, '{"min": 0, "max": 100000}'::jsonb, 1);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('cc886e85-5580-4083-bc60-92e47d23ab23', 'c7f37f3d-8478-4ce0-8bda-05efc08f59fc', 'Resting HR', 'number', 'bpm', False, NULL, '{"min": 30, "max": 120}'::jsonb, 2);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('1f3c3762-076d-4702-a3fb-480b9d6f491c', 'c7f37f3d-8478-4ce0-8bda-05efc08f59fc', 'HRV', 'number', 'ms', False, NULL, '{"min": 0, "max": 200}'::jsonb, 3);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('8c26c307-1ca1-46c1-9d1e-4c4c8abf1780', 'c7f37f3d-8478-4ce0-8bda-05efc08f59fc', 'Body Battery', 'number', 'score', False, NULL, '{"min": 0, "max": 100}'::jsonb, 4);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('e080a6a4-fcab-4655-a062-b2e62e1a4ce6', '1e005740-26e1-40b7-8f97-4fb70de2f747', 'Duration', 'number', 'minutes', True, NULL, '{"min": 1, "max": 600}'::jsonb, 1);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('5d792500-e1f1-45bb-adfa-668e0eb6cb48', '1e005740-26e1-40b7-8f97-4fb70de2f747', 'Distance', 'number', 'km', False, NULL, '{"min": 0, "max": 200}'::jsonb, 2);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('99007ce9-aa0a-4e7e-b846-182ad196dd83', '1e005740-26e1-40b7-8f97-4fb70de2f747', 'Avg Heart Rate', 'number', 'bpm', False, NULL, '{"min": 40, "max": 220}'::jsonb, 3);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('1a36d4da-5a26-4029-b1ab-dbafcd9c0795', '1e005740-26e1-40b7-8f97-4fb70de2f747', 'Calories', 'number', 'kcal', False, NULL, '{"min": 0, "max": 5000}'::jsonb, 4);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('aa9e885a-20a4-4da3-8631-2350e1a6f459', '11abce6d-83e6-4508-969a-ef8bb3b18fc5', 'Duration', 'number', 'minutes', True, NULL, '{"min": 1, "max": 180}'::jsonb, 1);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('745a0249-3209-4a60-a1f5-ed85ec59b1e3', '11abce6d-83e6-4508-969a-ef8bb3b18fc5', 'Exercises', 'text', NULL, False, NULL, '{}'::jsonb, 2);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('ebc9a54d-f8d8-4d2a-86fd-8a7803371ce3', 'fb7eeb97-b3d9-41da-af6d-e40089ba3fe5', 'Bench Press Weight', 'number', 'kg', False, NULL, '{"min": 0, "max": 300}'::jsonb, 1);
INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order) VALUES ('6a61280d-0265-46da-a6b7-0dcced4ad6d1', 'fb7eeb97-b3d9-41da-af6d-e40089ba3fe5', 'Reps', 'number', 'count', False, NULL, '{"min": 1, "max": 100}'::jsonb, 2);


-- ============================================================
-- TEST DATA (3 sample events)
-- ============================================================

-- Test Event 1
WITH new_event AS (
    INSERT INTO events (user_id, category_id, event_date, comment)
    VALUES (auth.uid(), 'f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', '2025-11-03', 'Test event 1 for Sleep')
    RETURNING id
)
INSERT INTO event_attributes (event_id, attribute_definition_id, value_number)
VALUES
    ((SELECT id FROM new_event), '8d8cf0c0-1aa6-4cc1-b559-c51ba86eb57a', 10),
    ((SELECT id FROM new_event), '15b64707-796a-41ee-a39e-ba392831acd6', 10),
    ((SELECT id FROM new_event), 'bd676387-c3f8-412c-bc87-d34755553884', 10);

-- Test Event 2
WITH new_event AS (
    INSERT INTO events (user_id, category_id, event_date, comment)
    VALUES (auth.uid(), 'f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', '2025-11-03', 'Test event 2 for Sleep')
    RETURNING id
)
INSERT INTO event_attributes (event_id, attribute_definition_id, value_number)
VALUES
    ((SELECT id FROM new_event), '8d8cf0c0-1aa6-4cc1-b559-c51ba86eb57a', 20),
    ((SELECT id FROM new_event), '15b64707-796a-41ee-a39e-ba392831acd6', 20),
    ((SELECT id FROM new_event), 'bd676387-c3f8-412c-bc87-d34755553884', 20);

-- Test Event 3
WITH new_event AS (
    INSERT INTO events (user_id, category_id, event_date, comment)
    VALUES (auth.uid(), 'f6985d8a-35ed-4d69-9cb3-157a57dbc8d9', '2025-11-03', 'Test event 3 for Sleep')
    RETURNING id
)
INSERT INTO event_attributes (event_id, attribute_definition_id, value_number)
VALUES
    ((SELECT id FROM new_event), '8d8cf0c0-1aa6-4cc1-b559-c51ba86eb57a', 30),
    ((SELECT id FROM new_event), '15b64707-796a-41ee-a39e-ba392831acd6', 30),
    ((SELECT id FROM new_event), 'bd676387-c3f8-412c-bc87-d34755553884', 30);



-- ============================================================
-- SCHEMA CREATION COMPLETE
-- ============================================================

-- Summary:
-- ✓ Core tables created with RLS enabled
-- ✓ Metadata tables (Areas, Categories, Attributes) created
-- ✓ Data tables (Events, Attributes, Attachments) created
-- ✓ Row Level Security policies applied
-- ✓ CASCADE deletion configured
-- ✓ Performance indexes created
-- ✓ Template metadata inserted
-- ✓ Test data generated

-- Next steps:
-- 1. Verify schema in Supabase Dashboard
-- 2. Test RLS policies with a test user
-- 3. Import historical data if available
-- 4. Configure Streamlit app connection