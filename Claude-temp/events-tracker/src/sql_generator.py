"""
SQL Generator Module
Generates PostgreSQL/Supabase SQL with RLS and CASCADE deletion
"""
from typing import List, Dict
from datetime import datetime, date
import json


class SQLGenerator:
    """Generate SQL statements for Supabase database setup."""
    
    def __init__(self, areas: List, categories: List, attributes: List):
        self.areas = areas
        self.categories = categories
        self.attributes = attributes
    
    def generate_full_schema(self) -> str:
        """Generate complete SQL schema including tables, RLS, and test data."""
        sql_parts = [
            self._generate_header(),
            self._generate_core_tables(),
            self._generate_metadata_tables(),
            self._generate_data_tables(),
            self._generate_rls_policies(),
            self._generate_indexes(),
            self._generate_metadata_inserts(),
            self._generate_test_data(),
            self._generate_footer()
        ]
        
        return "\n\n".join(sql_parts)
    
    def _generate_header(self) -> str:
        """Generate SQL file header with metadata."""
        return f"""-- ============================================================
-- Events Tracker Database Schema
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 
-- This schema implements an EAV (Entity-Attribute-Value) pattern
-- with full Row Level Security and CASCADE deletion
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
"""
    
    def _generate_core_tables(self) -> str:
        """Generate core user and template tables."""
        return """-- ============================================================
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
"""
    
    def _generate_metadata_tables(self) -> str:
        """Generate metadata tables (Areas, Categories, Attributes)."""
        return """-- ============================================================
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
"""
    
    def _generate_data_tables(self) -> str:
        """Generate data tables (Events and Attributes)."""
        return """-- ============================================================
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
"""
    
    def _generate_rls_policies(self) -> str:
        """Generate additional RLS helper functions."""
        return """-- ============================================================
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
"""
    
    def _generate_indexes(self) -> str:
        """Generate performance indexes."""
        return """-- ============================================================
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
"""
    
    def _generate_metadata_inserts(self) -> str:
        """Generate INSERT statements for metadata from parsed Excel."""
        sql_parts = ["-- ============================================================"]
        sql_parts.append("-- METADATA INSERTS (from Excel template)")
        sql_parts.append("-- Note: Replace 'auth.uid()' with actual user UUID when running")
        sql_parts.append("-- ============================================================\n")
        
        # Areas inserts
        sql_parts.append("-- Insert Areas")
        for area in self.areas:
            icon = f"'{area.icon}'" if area.icon else "NULL"
            color = f"'{area.color}'" if area.color else "NULL"
            desc = f"'{area.description}'" if area.description else "NULL"
            
            sql_parts.append(
                f"INSERT INTO areas (id, user_id, name, icon, color, sort_order, description) "
                f"VALUES ('{area.uuid}', auth.uid(), '{area.name}', {icon}, {color}, "
                f"{area.sort_order}, {desc});"
            )
        
        # Categories inserts
        sql_parts.append("\n-- Insert Categories")
        for cat in self.categories:
            parent = f"'{cat.parent_uuid}'" if cat.parent_uuid else "NULL"
            desc = f"'{cat.description}'" if cat.description else "NULL"
            
            sql_parts.append(
                f"INSERT INTO categories (id, area_id, parent_category_id, name, description, "
                f"level, sort_order) VALUES ('{cat.uuid}', '{cat.area_uuid}', {parent}, "
                f"'{cat.name}', {desc}, {cat.level}, {cat.sort_order});"
            )
        
        # Attributes inserts
        sql_parts.append("\n-- Insert Attribute Definitions")
        for attr in self.attributes:
            unit = f"'{attr.unit}'" if attr.unit else "NULL"
            default = f"'{attr.default_value}'" if attr.default_value else "NULL"
            
            sql_parts.append(
                f"INSERT INTO attribute_definitions (id, category_id, name, data_type, unit, "
                f"is_required, default_value, validation_rules, sort_order) "
                f"VALUES ('{attr.uuid}', '{attr.category_uuid}', '{attr.name}', "
                f"'{attr.data_type}', {unit}, {attr.is_required}, {default}, "
                f"'{attr.validation_rules}'::jsonb, {attr.sort_order});"
            )
        
        return "\n".join(sql_parts)
    
    def _generate_test_data(self) -> str:
        """Generate 3 test event records."""
        # Find first category for test data
        if not self.categories:
            return "-- No categories defined, skipping test data generation"
        
        test_category = self.categories[0]
        
        # Find attributes for this category
        category_attrs = [a for a in self.attributes if a.category_uuid == test_category.uuid]
        
        today = date.today()
        
        sql_parts = ["\n-- ============================================================"]
        sql_parts.append("-- TEST DATA (3 sample events)")
        sql_parts.append("-- ============================================================\n")
        
        for i in range(3):
            event_uuid = f"gen_random_uuid()"
            event_date = f"'{today.isoformat()}'"
            comment = f"'Test event {i+1} for {test_category.name}'"
            
            sql_parts.append(
                f"-- Test Event {i+1}\n"
                f"WITH new_event AS (\n"
                f"    INSERT INTO events (user_id, category_id, event_date, comment)\n"
                f"    VALUES (auth.uid(), '{test_category.uuid}', {event_date}, {comment})\n"
                f"    RETURNING id\n"
                f")"
            )
            
            # Add attribute values
            if category_attrs:
                attr_inserts = []
                for attr in category_attrs[:3]:  # Limit to first 3 attributes
                    if attr.data_type == 'number':
                        value_col = 'value_number'
                        value = f"{(i+1) * 10}"
                    elif attr.data_type == 'text':
                        value_col = 'value_text'
                        value = f"'Sample text {i+1}'"
                    elif attr.data_type == 'boolean':
                        value_col = 'value_boolean'
                        value = 'true' if i % 2 == 0 else 'false'
                    else:
                        continue
                    
                    attr_inserts.append(
                        f"    ((SELECT id FROM new_event), '{attr.uuid}', {value})"
                    )
                
                if attr_inserts:
                    sql_parts.append(
                        f"INSERT INTO event_attributes (event_id, attribute_definition_id, {value_col})\n"
                        f"VALUES\n" + ",\n".join(attr_inserts) + ";\n"
                    )
        
        return "\n".join(sql_parts)
    
    def _generate_footer(self) -> str:
        """Generate SQL file footer."""
        return """
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
"""
