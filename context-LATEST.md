# 1 Events Tracker - Context Document for AI-Assisted Development

> Complete technical documentation for Events Tracker project. Use this document when starting development sessions with Claude, GPT, or other AI coding assistants.

**Version:** 2.0  
**Last Updated:** November 20, 2025  
**Status:** Refactored for better maintainability

---

# 2 Table of Contents

- [Project Overview](#project-overview)
- [Architecture and Technologies](#architecture-and-technologies)
- [Database Schema](#database-schema)
- [Python Modules and Functionality](#python-modules-and-functionality)
- [Key Workflows](#key-workflows)
- [Data Flow](#data-flow)
- [Security](#security)
- [Current Issues and Tasks](#current-issues-and-tasks)
- [Excel Template Format](#excel-template-format)
- [Testing Instructions](#testing-instructions)
- [Deployment Notes](#deployment-notes)
- [Useful Code Snippets](#useful-code-snippets)
- [Development Guidelines](#development-guidelines)
- [Quick Start for New Sessions](#quick-start-for-new-sessions)

---

# 3 Project Overview

**Application Name:** Events Tracker  
**Description:** A flexible, hierarchical event tracking application using Entity-Attribute-Value (EAV) pattern  
**Purpose:** Allow users to define custom event structures and record events with dynamic attributes

**Perfect for:**
- Personal tracking (fitness, health, habits, finances)
- Project management and time tracking
- Research data collection
- IoT device data logging
- Any scenario requiring flexible, user-defined metadata

---

# 4 Architecture and Technologies

## 4.1 Backend

- **Language:** Python 3.11
- **Framework:** Streamlit (web interface)
- **Database:** Supabase (PostgreSQL with Row Level Security)
- **Libraries:** 
  - pandas (data manipulation)
  - openpyxl (Excel processing)
  - supabase-py (database client)

## 4.2 Database Pattern

- **EAV (Entity-Attribute-Value)** pattern for flexible data structure
- **Row Level Security (RLS)** for multi-tenant security
- **CASCADE deletion** for referential integrity

---

# 5 Database Schema

## 5.1 Core Tables

### 5.1.1 templates
Reusable configurations
- id (UUID, PK)
- name, description, icon
- is_public (boolean)
- created_by, user_id (FK to auth.users)

### 5.1.2 areas
Top-level organization
- id (UUID, PK)
- user_id (FK to auth.users)
- template_id (FK to templates)
- name, icon, color, description
- sort_order (integer), slug (text)

### 5.1.3 categories
Hierarchical event types (max 10 levels)
- id (UUID, PK)
- area_id (FK to areas)
- parent_category_id (FK to categories) - self-referencing
- user_id (FK to auth.users)
- name, description, level (1-10), sort_order, slug
- path (ltree type for hierarchical queries)

### 5.1.4 attribute_definitions
Define what data can be captured
- id (UUID, PK)
- category_id (FK to categories)
- user_id (FK to auth.users)
- name, unit, default_value
- data_type (CHECK: 'number', 'text', 'datetime', 'boolean', 'link', 'image')
- is_required (boolean), validation_rules (JSONB), sort_order

## 5.2 Data Tables

### 5.2.1 events
Main event records
- id (UUID, PK)
- user_id (FK to auth.users)
- category_id (FK to categories)
- event_date (date, NOT NULL)
- comment (text)
- created_at, edited_at (timestamps)

### 5.2.2 event_attributes
EAV storage for event data
- id (UUID, PK)
- event_id (FK to events)
- attribute_definition_id (FK to attribute_definitions)
- user_id (FK to auth.users)
- value_text, value_number, value_datetime, value_boolean, value_json
- CONSTRAINT: Only ONE value column can be populated per row

### 5.2.3 event_attachments
Files, images, links
- id (UUID, PK)
- event_id (FK to events)
- user_id (FK to auth.users)
- type (CHECK: 'image', 'link', 'file')
- url, filename, size_bytes

## 5.3 Audit Tables

### 5.3.1 name_change_history
Track renames
- id (UUID, PK)
- object_type (CHECK: 'area', 'category', 'attribute')
- object_id, old_name, new_name
- changed_by (FK to auth.users), changed_at, change_reason

### 5.3.2 template_versions
Version control for templates
- id (UUID, PK)
- version_number, snapshot_data (JSONB)
- created_by (FK to auth.users), description

---

# 6 Python Modules and Functionality

## 6.1 Authentication Module

**File:** `auth.py`  
**Status:** Fully Functional ✅  

Features:
- AuthManager class for Supabase Auth integration
- signup(), login(), logout() methods
- is_authenticated() - Check auth status
- get_user_id(), get_user_email() - User info
- show_login_page(), show_user_info_sidebar() - Streamlit UI

## 6.2 Database Connection

**File:** `supabase_client.py`  
**Status:** Active ✅  
**Purpose:** Manages Supabase client initialization and connection

## 6.3 Schema Generation

**File:** `sql_generator.py`  
**Status:** Fully Functional ✅  

Features:
- SQLGenerator class
- generate_full_schema() - Complete SQL with RLS, indexes
- _generate_core_tables(), _generate_metadata_tables(), _generate_data_tables()
- _generate_rls_policies(), _generate_indexes()
- Supports CASCADE deletion
- Generates INSERT statements from Excel data

## 6.4 Template Parsing

**File:** `excel_parser_new.py`  
**Status:** Fully Functional ✅  

Features:
- ExcelTemplateParser class
- parse() - Extract Areas, Categories, Attributes from Excel
- load_from_database() - Load existing structure from Supabase
- Creates TemplateObject structures for rename detection
- Handles hierarchical paths (Area → Category → Subcategory)

## 6.5 Export Structure

**File:** `reverse_engineer.py`  
**Status:** Fully Functional ✅  

Features:
- ReverseEngineer class
- export_to_excel() - Save structure to Excel file
- export_to_bytes() - Generate in-memory Excel for download
- Converts Supabase structure back to template format
- Creates timestamped backup filenames

## 6.6 Mass Event Import

**File:** `bulk_import.py`  
**Status:** Fully Functional ✅  

Features:
- Import multiple events from Excel/CSV
- Uses "›" separator for hierarchical categories (e.g., "Health › Sleep")
- Mixed categories in same file (different event types)
- Duplicate detection (same category + date)
- Skip or overwrite duplicates
- Detailed validation with row-by-row error messages

## 6.7 Single Event Form

**File:** `event_entry.py`  
**Status:** Fully Functional ✅  

Features:
- Dynamic form based on selected category
- Hierarchical category selection (Area → Category)
- Dynamic attribute inputs (all 6 data types)
- Required field validation
- Sticky last-used category (session state)
- Comment field (optional)
- Mobile-optimized layout

## 6.8 Structure Viewer

**File:** `structure_viewer.py`  
**Status:** Fully Functional ✅  

Features:
- Interactive tree view of Areas → Categories → Attributes
- Search functionality
- Filter by Area, Filter by Level (1-10)
- Uses indentation instead of nested expanders
- Shows attribute details (type, unit, required, default)
- Statistics dashboard (counts, max depth)

## 6.9 Smart Rename Detection

**File:** `rename_detector.py`  
**Status:** Functional ✅  

Features:
- TemplateObject dataclass for tracking objects
- Detects renames vs. new objects when re-uploading Excel
- Compares names, UUIDs, hierarchical paths
- Prevents data loss during structure updates

## 6.10 View-Based Export

**File:** `view_data_export.py`  
**Status:** Fully Functional ⭐  
**Last Modified:** 2025-11-16 09:30 UTC  

Export events to Excel for viewing and editing with advanced filters and color-coding.

Key features:
- Color-coded columns: PINK (read-only) vs BLUE (editable)
- Professional formatting: borders, fills, fonts, alignment
- Auto-sized columns with max width limits
- Frozen panes (header + first 3 columns)
- Filter by category (single or all)
- Date range selection (from/to)
- Attribute selection (choose which attributes to export)
- Instructions sheet included in workbook

## 6.11 View-Based Import

**File:** `view_data_import.py`  
**Status:** Fully Functional ⭐  
**Last Modified:** 2025-11-16 09:30 UTC  

Import edited Excel files, detect changes, show diff, and apply updates to database.

Key features:
- Parse uploaded Excel with openpyxl
- Validate required columns (Event_ID, Category_Path, Date)
- Handle empty rows and malformed data
- Field-level diff detection
- Compare uploaded data vs current database values
- Normalize values (handle None, empty strings, whitespace)
- Show old vs new values side-by-side
- Preview first 10 modified events
- Apply changes with RLS checks

---

# 7 Key Workflows

## 7.1 User Registration and Login

1. User navigates to app
2. If not authenticated, show login/signup form
3. On signup: Create user in Supabase Auth → Auto-login
4. On login: Validate credentials → Store session
5. Set user_id in session state for all operations

## 7.2 Creating Event Structure

1. User uploads Excel template OR uses UI to define Areas/Categories/Attributes
2. System validates structure (hierarchy, data types)
3. Generate SQL statements for all tables
4. Execute with RLS policies
5. Store in Supabase with user_id foreign keys

## 7.3 Recording Events

### 7.3.1 Single Event Entry
1. Select Area → Category from dropdown
2. System loads attribute definitions for selected category
3. User fills dynamic form (all attributes)
4. Validate required fields
5. Insert into events + event_attributes tables

### 7.3.2 Bulk Import
1. User downloads template Excel
2. Fill multiple events (can be mixed categories)
3. Upload file
4. System validates all rows
5. Show preview with duplicate detection
6. Batch insert to database

## 7.4 Exporting and Re-importing Data

1. User selects filters (category, date range, attributes)
2. System generates styled Excel with color-coded columns
3. User edits BLUE columns only (attributes, comment)
4. Re-upload edited file
5. System detects changes (diff view)
6. Preview changes before applying
7. Update database with modified values

---

# 8 Data Flow

## 8.1 Write Path (Recording Events)

```
User Input (Streamlit Form)
    ↓
Validation (required fields, data types)
    ↓
event_entry.py / bulk_import.py
    ↓
INSERT to 'events' table
    ↓
For each attribute:
    INSERT to 'event_attributes' (EAV)
    ↓
Success message to user
```

## 8.2 Read Path (Viewing Events)

```
User selects filters
    ↓
view_data_export.py
    ↓
SELECT events 
    JOIN event_attributes
    JOIN attribute_definitions
    WHERE user_id = current_user
    ↓
Pivot EAV data to columns
    ↓
Generate styled Excel
    ↓
Download to user
```

## 8.3 Update Path (Editing via Excel)

```
User uploads edited Excel
    ↓
view_data_import.py parses file
    ↓
Load current values from database
    ↓
Compare field-by-field (diff detection)
    ↓
Show preview of changes
    ↓
User confirms
    ↓
UPDATE event_attributes
    WHERE event_id AND attribute_definition_id
    AND user_id = current_user
    ↓
Success confirmation
```

---

# 9 Security

## 9.1 Row Level Security (RLS)

All tables have RLS policies enforcing:
- Users can only access their own data
- Every query MUST include `user_id` filter
- Authentication required for all operations

## 9.2 Policies Structure

```sql
-- SELECT policy
CREATE POLICY "Users can view own records"
ON table_name FOR SELECT
USING (auth.uid() = user_id);

-- INSERT policy
CREATE POLICY "Users can create own records"
ON table_name FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- UPDATE policy
CREATE POLICY "Users can update own records"
ON table_name FOR UPDATE
USING (auth.uid() = user_id);

-- DELETE policy
CREATE POLICY "Users can delete own records"
ON table_name FOR DELETE
USING (auth.uid() = user_id);
```

## 9.3 Authentication Flow

1. User signs up → Supabase creates user in `auth.users`
2. User logs in → Receives JWT token
3. All API calls include JWT in headers
4. Supabase validates JWT and sets `auth.uid()`
5. RLS policies use `auth.uid()` to filter data

---

# 10 Current Issues and Tasks

## 10.1 Recently Fixed
- ✅ Structure Viewer rendering errors (categories without attributes)
- ✅ Excel export/import with change detection
- ✅ Rename detection algorithm improvements

## 10.2 Known Issues
None currently

## 10.3 Planned Features
- Event editing UI (pre-filled forms)
- Event deletion with confirmation
- Batch operations (multi-select events)
- Advanced search/filtering in event list
- Dashboard with statistics and charts
- Export to CSV/JSON formats

---

# 11 Excel Template Format

## 11.1 Structure Definition Template

Columns:
- **Area**: Top-level grouping
- **Category**: Event type (use "›" for hierarchy: "Parent › Child")
- **Attribute Name**: Data field name
- **Data Type**: number, text, datetime, boolean, link, image
- **Unit**: Optional unit (kg, km, %, etc.)
- **Required**: TRUE/FALSE
- **Default Value**: Optional default

Example:
```
Area         | Category        | Attribute Name | Data Type | Unit | Required
Health       | Sleep           | Duration       | number    | hrs  | TRUE
Health       | Sleep           | Quality        | number    | 1-10 | FALSE
Training     | Running › Long  | Distance       | number    | km   | TRUE
```

## 11.2 Event Import Template

Columns:
- **Category Path**: "Area › Category" (e.g., "Health › Sleep")
- **Date**: YYYY-MM-DD format
- **[Attribute columns]**: Dynamic based on category
- **Comment**: Optional text

Example:
```
Category Path | Date       | Duration | Quality | Comment
Health › Sleep| 2025-11-20 | 7.5      | 8       | Slept well
Health › Sleep| 2025-11-19 | 6.2      | 6       | Woke up early
```

## 11.3 Event Export Format (for editing)

Color-coded columns:
- **PINK (Read-only)**: Event_ID, Category_Path, Date, Created_At
- **BLUE (Editable)**: All attribute columns, Comment

User can edit BLUE columns and re-upload for bulk updates.

---

# 12 Testing Instructions

## 12.1 Manual Testing Checklist

**Authentication:**
- [ ] Sign up with new email
- [ ] Login with existing credentials
- [ ] Logout and verify session cleared
- [ ] Try accessing app without login (should redirect)

**Structure Creation:**
- [ ] Upload valid Excel template
- [ ] Verify areas/categories/attributes created
- [ ] Check hierarchy (parent-child relationships)
- [ ] Test rename detection on re-upload

**Event Entry:**
- [ ] Create single event with all attribute types
- [ ] Verify required field validation
- [ ] Test date picker
- [ ] Check comment field saves correctly

**Bulk Import:**
- [ ] Download import template
- [ ] Import file with multiple events
- [ ] Verify duplicate detection
- [ ] Test skip vs overwrite duplicates

**View Export/Import:**
- [ ] Export events with filters
- [ ] Verify Excel formatting (colors, frozen panes)
- [ ] Edit BLUE columns in Excel
- [ ] Re-import and check diff detection
- [ ] Verify database updates correctly

**Security:**
- [ ] Create event as User A
- [ ] Login as User B
- [ ] Verify User B cannot see User A's events

---

# 13 Deployment Notes

## 13.1 Streamlit Cloud Setup

1. Push code to GitHub repository
2. Connect Streamlit Cloud to repo
3. Configure secrets in Streamlit dashboard:
   ```toml
   [supabase]
   url = "https://xxx.supabase.co"
   key = "eyJ..."
   ```
4. Deploy and verify authentication works

## 13.2 Environment Variables

Required secrets:
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon/public key

Optional:
- `DEBUG_MODE`: Enable additional logging

## 13.3 Database Setup

1. Create Supabase project
2. Run schema.sql to create tables
3. Enable RLS on all tables
4. Verify policies are active
5. Test with dummy user account

---

# 14 Useful Code Snippets

## 14.1 Database Query with RLS

```python
# ✅ CORRECT - Always include user_id
user_id = st.session_state.auth.get_user_id()
response = client.table('events') \
    .select('*') \
    .eq('user_id', user_id) \
    .execute()

# ❌ WRONG - Missing user_id (RLS violation!)
response = client.table('events') \
    .select('*') \
    .execute()
```

## 14.2 Join with EAV Pattern

```python
# SELECT with JOIN
events = client.table('events') \
    .select('*, event_attributes(*, attribute_definitions(*))') \
    .eq('user_id', user_id) \
    .eq('category_id', category_id) \
    .execute()
```

## 14.3 Insert Event with Attributes

```python
# INSERT event
new_event = {
    'user_id': user_id,
    'category_id': category_id,
    'event_date': '2025-11-20',
    'comment': 'Test'
}
result = client.table('events').insert(new_event).execute()
event_id = result.data[0]['id']

# INSERT attributes (EAV)
for attr_def in attribute_definitions:
    attribute_data = {
        'event_id': event_id,
        'attribute_definition_id': attr_def['id'],
        'user_id': user_id,
        'value_number': form_data[attr_def['name']]  # or value_text, etc.
    }
    client.table('event_attributes').insert(attribute_data).execute()
```

## 14.4 Streamlit UI Patterns

```python
# Success message
st.success("✅ Event saved successfully!")

# Error message
st.error("❌ Failed to save event")

# Spinner
with st.spinner("Loading events..."):
    events = fetch_events(client, user_id)

# Form with validation
with st.form("event_form"):
    date = st.date_input("Date", value=datetime.now())
    category = st.selectbox("Category", options)
    
    submitted = st.form_submit_button("Save Event")
    if submitted:
        if not category:
            st.error("Please select a category")
        else:
            save_event(date, category)
```

---

# 15 Development Guidelines

## 15.1 Code Style

- Follow PEP 8 for Python code
- Use type hints where applicable
- Add docstrings for all functions/classes
- Keep functions focused (single responsibility)
- Use meaningful variable names
-  Keep documentation (.md) in numbering style of this document

## 15.2 Module Structure

Every module should have - structure below described with updated header elements (Last Modified, Module Name - Brief Description, Features, Dependencies)
```python
"""
Module Name - Brief Description

Features:
- Feature 1
- Feature 2

Dependencies: streamlit, pandas, supabase

Last Modified: YYYY-MM-DD HH:MM UTC
"""

import streamlit as st
# ... other imports

def main_function():
    """Main entry point."""
    pass

# Helper functions below
```

## 15.3 Error Handling

Always wrap database operations:
```python
try:
    result = client.table('events').insert(data).execute()
    st.success("✅ Event saved!")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    # Log error for debugging
```

## 15.4 RLS Requirements

Every database query MUST include user_id:
```python
# ✅ CORRECT
response = client.table('events') \
    .select('*') \
    .eq('user_id', user_id) \
    .execute()

# ❌ WRONG
response = client.table('events').select('*').execute()
```

## 15.5 Testing

- Test happy path (valid data)
- Test edge cases (empty, null, invalid)
- Test RLS (user isolation)
- Test performance (100+ records)
- Verify error messages are user-friendly

## 15.6 Git Workflow

```bash
# Commit message format
git commit -m "feat: Add event editing functionality

- Created src/event_edit.py
- Updated streamlit_app.py menu
- Added RLS validation

Last Modified: 2025-11-20 10:00 UTC"
```

---

# 16 Quick Start for New Sessions

When starting a new development session with an AI assistant:

```markdown
Hi Claude! Continuing Events Tracker development.

**ATTACHED:**
- context-LATEST.md (this document)
- database/schema.sql (PostgreSQL schema)
- src/[relevant_module].py (code to modify)
- streamlit_app.py (main application)

**TASK:**
[Describe specific task]

**REQUIREMENTS:**
- Follow guidelines in "Development Guidelines" section
- Update "Last Modified" timestamp in docstring
- Include RLS checks (user_id in all queries)
- Use existing UI patterns
- Add error handling

**DELIVERABLES:**
1. Modified/new code files with updated timestamps
2. Integration instructions
3. Testing notes
```

---

# 17 Document Info

- **Version:** 2.0 (Refactored)
- **Last Updated:** November 20, 2025
- **Status:** Complete and maintainable
- **Changes from 1.1:**
  - Removed hardcoded numbers from headings
  - Improved anchor link structure
  - Better consistency in formatting
  - Enhanced maintainability

**This document contains everything needed for AI-assisted development!**
