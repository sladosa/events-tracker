# Events Tracker - Context Document for AI-Assisted Development

> Complete technical documentation for Events Tracker project. Use this document when starting development sessions with Claude, GPT, or other AI coding assistants.

**Version:** 1.1  
**Last Updated:** November 17, 2025, 17:30 UTC  
**Status:** Complete and self-contained

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Technologies](#2-architecture--technologies)
3. [Database Schema](#3-database-schema)
4. [Python Modules & Functionality](#4-python-modules--functionality)
5. [Key Workflows](#5-key-workflows)
6. [Data Flow](#6-data-flow)
7. [Security](#7-security)
8. [Current Issues & Tasks](#8-current-issues--tasks)
9. [Excel Template Format](#9-excel-template-format)
10. [Testing Instructions](#10-testing-instructions)
11. [Deployment Notes](#11-deployment-notes)
12. [Useful Code Snippets](#12-useful-code-snippets)
13. [Development Guidelines](#13-development-guidelines)
14. [Quick Start for New Sessions](#14-quick-start-for-new-sessions)

---

## 1. PROJECT OVERVIEW

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

## 2. ARCHITECTURE & TECHNOLOGIES

### Backend
- **Language:** Python 3.11
- **Framework:** Streamlit (web interface)
- **Database:** Supabase (PostgreSQL with Row Level Security)
- **Libraries:** 
  - pandas (data manipulation)
  - openpyxl (Excel processing)
  - supabase-py (database client)

### Database Pattern
- **EAV (Entity-Attribute-Value)** pattern for flexible data structure
- **Row Level Security (RLS)** for multi-tenant security
- **CASCADE deletion** for referential integrity

---

## 3. DATABASE SCHEMA

### Core Tables

**templates** - Reusable configurations
- id (UUID, PK)
- name, description, icon
- is_public (boolean)
- created_by, user_id (FK to auth.users)

**areas** - Top-level organization
- id (UUID, PK)
- user_id (FK to auth.users)
- template_id (FK to templates)
- name, icon, color, description
- sort_order (integer), slug (text)

**categories** - Hierarchical event types (max 10 levels)
- id (UUID, PK)
- area_id (FK to areas)
- parent_category_id (FK to categories) - self-referencing
- user_id (FK to auth.users)
- name, description, level (1-10), sort_order, slug
- path (ltree type for hierarchical queries)

**attribute_definitions** - Define what data can be captured
- id (UUID, PK)
- category_id (FK to categories)
- user_id (FK to auth.users)
- name, unit, default_value
- data_type (CHECK: 'number', 'text', 'datetime', 'boolean', 'link', 'image')
- is_required (boolean), validation_rules (JSONB), sort_order

### Data Tables

**events** - Main event records
- id (UUID, PK)
- user_id (FK to auth.users)
- category_id (FK to categories)
- event_date (date, NOT NULL)
- comment (text)
- created_at, edited_at (timestamps)

**event_attributes** - EAV storage for event data
- id (UUID, PK)
- event_id (FK to events)
- attribute_definition_id (FK to attribute_definitions)
- user_id (FK to auth.users)
- value_text, value_number, value_datetime, value_boolean, value_json
- CONSTRAINT: Only ONE value column can be populated per row

**event_attachments** - Files, images, links
- id (UUID, PK)
- event_id (FK to events)
- user_id (FK to auth.users)
- type (CHECK: 'image', 'link', 'file')
- url, filename, size_bytes

### Audit Tables

**name_change_history** - Track renames
- id (UUID, PK)
- object_type (CHECK: 'area', 'category', 'attribute')
- object_id, old_name, new_name
- changed_by (FK to auth.users), changed_at, change_reason

**template_versions** - Version control for templates
- id (UUID, PK)
- version_number, snapshot_data (JSONB)
- created_by (FK to auth.users), description

---

## 4. PYTHON MODULES & FUNCTIONALITY

### ✅ auth.py - Authentication
**Status:** FULLY FUNCTIONAL  
**Features:**
- AuthManager class for Supabase Auth integration
- signup(), login(), logout() methods
- is_authenticated() - Check auth status
- get_user_id(), get_user_email() - User info
- show_login_page(), show_user_info_sidebar() - Streamlit UI

### ✅ supabase_client.py - Database Connection
**Status:** ACTIVE  
**Purpose:** Manages Supabase client initialization and connection

### ✅ sql_generator.py - Schema Generation
**Status:** FULLY FUNCTIONAL  
**Features:**
- SQLGenerator class
- generate_full_schema() - Complete SQL with RLS, indexes
- _generate_core_tables(), _generate_metadata_tables(), _generate_data_tables()
- _generate_rls_policies(), _generate_indexes()
- Supports CASCADE deletion
- Generates INSERT statements from Excel data

### ✅ excel_parser_new.py - Template Parsing
**Status:** FULLY FUNCTIONAL  
**Features:**
- ExcelTemplateParser class
- parse() - Extract Areas, Categories, Attributes from Excel
- load_from_database() - Load existing structure from Supabase
- Creates TemplateObject structures for rename detection
- Handles hierarchical paths (Area → Category → Subcategory)

### ✅ reverse_engineer.py - Export Structure
**Status:** FULLY FUNCTIONAL  
**Features:**
- ReverseEngineer class
- export_to_excel() - Save structure to Excel file
- export_to_bytes() - Generate in-memory Excel for download
- Converts Supabase structure back to template format
- Creates timestamped backup filenames

### ✅ bulk_import.py - Mass Event Import
**Status:** FULLY FUNCTIONAL  
**Features:**
- Import multiple events from Excel/CSV
- Uses "›" separator for hierarchical categories (e.g., "Health › Sleep")
- Mixed categories in same file (different event types)
- Duplicate detection (same category + date)
- Skip or overwrite duplicates
- Detailed validation with row-by-row error messages
- generate_template() - Creates Excel template with instructions
- validate_import_file() - Pre-import validation
- import_events() - Batch insert to database

### ✅ event_entry.py - Single Event Form
**Status:** FULLY FUNCTIONAL  
**Features:**
- Dynamic form based on selected category
- Hierarchical category selection (Area → Category)
- Dynamic attribute inputs (all 6 data types)
- Required field validation
- Sticky last-used category (session state)
- Comment field (optional)
- Mobile-optimized layout

### ✅ structure_viewer.py - Browse Hierarchy
**Status:** FULLY FUNCTIONAL (RECENTLY FIXED)  
**Features:**
- Interactive tree view of Areas → Categories → Attributes
- Search functionality
- Filter by Area, Filter by Level (1-10)
- Uses indentation instead of nested expanders
- Shows attribute details (type, unit, required, default)
- Statistics dashboard (counts, max depth)

### ✅ rename_detector.py - Smart Rename Detection
**Status:** FUNCTIONAL  
**Features:**
- TemplateObject dataclass for tracking objects
- Detects renames vs. new objects when re-uploading Excel
- Compares names, UUIDs, hierarchical paths
- Prevents data loss during structure updates

### ✅ view_data_export.py - View-Based Export **[UPDATED 2025-11-16]**
**Status:** FULLY FUNCTIONAL ⭐  
**Last Modified:** 2025-11-16 09:30 UTC  
**Lines of Code:** ~350  
**Description:** Export events to Excel for viewing and editing with advanced filters and color-coding

**Key Features:**
- **Excel Export with Styling**
  - Color-coded columns: PINK (read-only) vs BLUE (editable)
  - Professional formatting: borders, fills, fonts, alignment
  - Auto-sized columns with max width limits
  - Frozen panes (header + first 3 columns)
- **Advanced Filtering**
  - Filter by category (single or all)
  - Date range selection (from/to)
  - Attribute selection (choose which attributes to export)
- **User Guidance**
  - Instructions sheet included in Excel workbook
  - Clear documentation on which columns can be edited
  - Safety notes about PINK vs BLUE columns

**Functions:**
- `get_all_areas_categories()` - Fetch areas and categories for filters
- `get_category_attributes()` - Get attributes for selected category
- `get_events_with_data()` - Query events with filters and join attribute data
- `create_excel_export()` - Generate styled Excel workbook with openpyxl
- `render_view_data_export()` - Streamlit UI with filters and download

**Dependencies:** streamlit, pandas, openpyxl, supabase

### ✅ view_data_import.py - View-Based Import **[UPDATED 2025-11-16]**
**Status:** FULLY FUNCTIONAL ⭐  
**Last Modified:** 2025-11-16 09:30 UTC  
**Lines of Code:** ~380  
**Description:** Import edited Excel files, detect changes, show diff, and apply updates to database

**Key Features:**
- **Excel Parsing & Validation**
  - Parse uploaded Excel with openpyxl
  - Validate required columns (Event_ID, Category_Path, Date)
  - Handle empty rows and malformed data
  - Error reporting for invalid files
- **Change Detection Engine**
  - Compare uploaded data vs current database values
  - Field-level diff detection
  - Normalize values (handle None, empty strings, whitespace)
  - Detect modified events with list of changed fields
- **Detailed Diff Viewer**
  - Show old vs new values side-by-side
  - Preview first 10 modified events
  - Display category path and date for context
  - Error list for invalid Event_IDs
- **Database Update**
  - Apply changes with RLS (Row Level Security) checks
  - Update `event_attributes` table (EAV values)
  - Update `events.comment` field
  - Handle attribute deletion (set to None)
  - Insert new attribute values if not exist
  - Type conversion for numeric attributes

**Functions:**
- `parse_uploaded_excel()` - Parse Excel file to DataFrame
- `get_current_event_data()` - Fetch current event data from database
- `detect_changes()` - Compare uploaded vs database and build diff
- `apply_changes()` - Execute updates to Supabase
- `render_view_data_import()` - Streamlit UI with upload, preview, diff, confirm

**Safety Features:**
- Confirmation step before applying changes
- Read-only columns (Event_ID, Category_Path, Date) not updated
- Detailed error reporting for failed updates
- Success/failure counts displayed to user

**Dependencies:** streamlit, pandas, openpyxl, supabase

---

## 5. KEY WORKFLOWS

### Workflow 1: Initial Setup
1. User signs up / logs in (auth.py)
2. User uploads Excel template with structure (excel_parser_new.py)
3. System generates SQL schema (sql_generator.py)
4. Structure saved to Supabase with RLS

### Workflow 2: Single Event Entry
1. User selects Area (event_entry.py)
2. User selects Category (hierarchical dropdown)
3. Form dynamically loads attributes for that category
4. User fills in values (type-specific inputs)
5. Event saved to `events` table
6. Attributes saved to `event_attributes` table (EAV)

### Workflow 3: Bulk Event Import
1. User downloads template (bulk_import.py → generate_template())
2. User fills Excel with events (mix of categories OK)
3. User uploads filled Excel
4. System validates (validate_import_file())
5. User reviews errors/preview
6. User chooses duplicate handling
7. System imports (import_events())

### Workflow 4: Structure Export/Backup
1. User clicks "Export Structure" (reverse_engineer.py)
2. System fetches Areas, Categories, Attributes from Supabase
3. System converts to Excel format (3 sheets)
4. User downloads timestamped backup file
5. User can edit and re-upload (rename detection prevents data loss)

### Workflow 5: Export → Edit → Import
1. User exports events to Excel (view_data_export.py)
2. Excel has color-coded columns: PINK (read-only), BLUE (editable)
3. User edits BLUE columns, saves file
4. User uploads file (view_data_import.py)
5. System detects changes (field-level diff)
6. User previews diff before applying
7. System updates database with RLS checks

### Workflow 6: Browse Structure
1. User opens Structure Viewer (structure_viewer.py)
2. System displays hierarchical tree
3. User filters by Area/Level or searches
4. User views attributes for each category
5. User copies category paths for bulk import

---

## 6. DATA FLOW

### Hierarchical Path Format
**Excel Template:** Uses "›" separator  
**Example:** `Health › Nutrition › Meals › Breakfast`

**Database Storage:**
- Separate records linked by `parent_category_id`
- `level` column tracks depth
- `path` column (ltree) enables fast hierarchical queries

### Attribute Value Storage (EAV Pattern)
**Challenge:** Different categories have different attributes  
**Solution:** Store in `event_attributes` table with type-specific columns

**Example Event:**
```
Event: "Morning Run" (Category: Training › Cardio › Running)
Storage:
event_id | attribute_definition_id | value_number | value_text    | value_boolean
abc-123  | def-456 (Distance)      | 5.2          | NULL          | NULL
abc-123  | def-789 (Route)         | NULL         | "Park Loop"   | NULL
abc-123  | ghi-012 (Felt Good)     | NULL         | NULL          | true
```

---

## 7. SECURITY

### Row Level Security (RLS) Policies
**Every table has policies:**
- Users can ONLY view/edit their own data
- Enforced at database level (not just application)
- Uses `auth.uid()` from Supabase Auth

**Example Policy:**
```sql
CREATE POLICY "Users can view their own events"
ON events FOR SELECT
USING (user_id = auth.uid());
```

### Cascade Deletion
- Delete Area → deletes all Categories, Attributes, Events
- Delete Category → deletes all child Categories, Attributes, Events
- Delete Event → deletes all Attributes, Attachments

---

## 8. CURRENT ISSUES & TASKS

### ✅ Recently Solved
- [x] Structure Viewer nested expander bug (fixed with indentation)
- [x] Bulk import mixed categories support
- [x] Rename detection to prevent data loss
- [x] View Data Export/Import complete workflows (2025-11-16)

### ⚠️ Known Issues
- [ ] Analytics dashboard incomplete (UI working, filters pending)
- [ ] Missing bulk delete functionality
- [ ] No event editing UI (only add new) - PLANNED
- [ ] No change history/audit log for edits

### 🚀 Planned Features
- [ ] Advanced analytics dashboard with charts
- [ ] Event editing with pre-filled forms
- [ ] Event change history/audit log
- [ ] Batch edit multiple events
- [ ] Template marketplace (share public templates)
- [ ] Mobile responsive PWA
- [ ] Export analytics charts to PDF
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Docker deployment support
- [ ] Multi-language support (i18n)

---

## 9. EXCEL TEMPLATE FORMAT

### Sheet: Areas
```
area_id | area_name | icon | color   | sort_order | description
uuid-1  | Health    | 🏥   | #3498db | 1          | ...
uuid-2  | Training  | 💪   | #e74c3c | 2          | ...
```

### Sheet: Categories
```
category_id | area_name | parent_category | category_name | description | level | sort_order
uuid-3      | Health    |                 | Nutrition     | ...         | 1     | 1
uuid-4      | Health    | Nutrition       | Meals         | ...         | 2     | 1
uuid-5      | Health    | Meals           | Breakfast     | ...         | 3     | 1
```

### Sheet: Attributes
```
attribute_id | category_name | attribute_name | data_type | unit | is_required | default_value | validation_rules | sort_order
uuid-6       | Breakfast     | Calories       | number    | kcal | TRUE        |               | {}               | 1
uuid-7       | Breakfast     | Time           | datetime  |      | TRUE        |               | {}               | 2
```

---

## 10. TESTING INSTRUCTIONS

### Test User Creation
1. Go to login page
2. Sign up with test email
3. Confirm email (check Supabase Auth)
4. Log in

### Test Structure Upload
1. Use MOCK_Hierarchical_View_Enhanced.xlsx
2. Upload via structure upload page
3. Check Structure Viewer for correct hierarchy
4. Verify database tables populated

### Test Event Entry
1. Open "Add Event" page
2. Select Area → Category
3. Fill in attributes
4. Save and verify in database

### Test Bulk Import
1. Download template from Bulk Import page
2. Add 5-10 test events (mix categories)
3. Upload and validate
4. Import and verify counts

### Test View Data Export/Import
1. Create several test events
2. Export to Excel (verify PINK and BLUE columns)
3. Edit some BLUE column values
4. Re-import Excel
5. Check diff viewer (should show changes)
6. Confirm import
7. Verify database updated

---

## 11. DEPLOYMENT NOTES

### Environment Variables Needed
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key (for admin operations)
```

### Streamlit Config (.streamlit/config.toml)
```toml
[server]
maxUploadSize = 200  # Allow large Excel files
headless = true

[theme]
primaryColor = "#3498db"
```

### Python Requirements
```
streamlit>=1.28.0
pandas>=1.5.0
openpyxl>=3.10.0
supabase>=2.0.0
python-dotenv>=1.0.0
```

---

## 12. USEFUL CODE SNIPPETS

### Get Current User ID
```python
from auth import AuthManager

auth = AuthManager(supabase_client)
user_id = auth.get_user_id()
```

### Fetch Events for User
```python
events = supabase_client.table('events') \
    .select('*, categories(name), event_attributes(*)') \
    .eq('user_id', user_id) \
    .order('event_date', desc=True) \
    .execute()
```

### Create New Event with Attributes
```python
# Insert event
event_data = {
    'user_id': user_id,
    'category_id': category_id,
    'event_date': '2025-11-17',
    'comment': 'Test event'
}
event = client.table('events').insert(event_data).execute()
event_id = event.data[0]['id']

# Insert attributes
attr_records = [
    {
        'event_id': event_id,
        'attribute_definition_id': 'attr-uuid-1',
        'value_number': 5.2,
        'user_id': user_id
    },
    {
        'event_id': event_id,
        'attribute_definition_id': 'attr-uuid-2',
        'value_text': 'Test value',
        'user_id': user_id
    }
]
client.table('event_attributes').insert(attr_records).execute()
```

### Update Event
```python
# Must include user_id for RLS!
client.table('events') \
    .update({'comment': 'Updated comment'}) \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

### Delete Event (Soft Delete)
```python
from datetime import datetime

client.table('events') \
    .update({'deleted_at': datetime.now().isoformat()}) \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

---

## 13. DEVELOPMENT GUIDELINES

### 13.1 Docstring Header Format (REQUIRED)

All Python modules must have this header structure with **UPDATED timestamp**:

```python
"""
Events Tracker - [Module Name]
================================
Created: YYYY-MM-DD HH:MM UTC
Last Modified: YYYY-MM-DD HH:MM UTC  ← ALWAYS UPDATE THIS!
Python: 3.11

Description:
[Brief description of module purpose and functionality]
"""
```

**Example:**
```python
"""
Events Tracker - Event Entry Module
====================================
Created: 2025-11-10 09:00 UTC
Last Modified: 2025-11-17 14:30 UTC
Python: 3.11

Description:
Dynamic event entry form with hierarchical category selection
and type-safe attribute inputs based on attribute definitions.
"""
```

### 13.2 Code Style Standards

**PEP 8 Compliance:**
- Max line length: 100 characters
- 4 spaces for indentation (no tabs)
- Two blank lines between top-level functions/classes
- One blank line between methods

**Naming Conventions:**
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private methods/vars: `_leading_underscore`

**Type Hints:**
```python
def fetch_events(client: Client, user_id: str) -> List[Dict]:
    pass

def validate_date(date_str: str) -> Optional[datetime]:
    pass
```

**Docstrings (Google Style):**
```python
def create_event(event_data: Dict, user_id: str) -> Optional[str]:
    """
    Create new event in database with attributes.
    
    Args:
        event_data: Dictionary containing event details and attributes
        user_id: UUID of authenticated user
        
    Returns:
        Event ID if successful, None if failed
        
    Raises:
        ValueError: If required fields missing
        DatabaseError: If database operation fails
    """
```

### 13.3 Error Handling Pattern

**Always use try-except with user-friendly messages:**

```python
try:
    response = client.table('events') \
        .select('*') \
        .eq('user_id', user_id) \
        .execute()
    return response.data
except Exception as e:
    st.error(f"❌ Error fetching events: {str(e)}")
    return []
```

### 13.4 Database Query Pattern (RLS - CRITICAL)

**ALWAYS include user_id for Row Level Security:**

```python
# ✅ CORRECT - Includes user_id
response = client.table('events') \
    .select('*') \
    .eq('user_id', user_id) \
    .execute()

# ❌ WRONG - Missing user_id (RLS violation!)
response = client.table('events') \
    .select('*') \
    .execute()
```

**Query Patterns:**

```python
# SELECT with JOIN
events = client.table('events') \
    .select('*, event_attributes(*, attribute_definitions(*))') \
    .eq('user_id', user_id) \
    .eq('category_id', category_id) \
    .execute()

# INSERT
new_event = {
    'user_id': user_id,
    'category_id': category_id,
    'event_date': '2025-11-17',
    'comment': 'Test'
}
result = client.table('events').insert(new_event).execute()

# UPDATE (MUST include user_id)
client.table('events') \
    .update({'comment': 'Updated comment'}) \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()

# DELETE (MUST include user_id)
client.table('events') \
    .delete() \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

### 13.5 Streamlit UI Patterns

**Message Types:**

```python
# Success
st.success("✅ Event saved successfully!")

# Error
st.error("❌ Failed to save event")

# Info
st.info("ℹ️ Select a category to continue")

# Warning
st.warning("⚠️ This action cannot be undone")
```

**Progress Indicators:**

```python
# Spinner
with st.spinner("Loading events..."):
    events = fetch_events(client, user_id)

# Progress bar
progress_bar = st.progress(0)
for i, item in enumerate(items):
    process_item(item)
    progress_bar.progress((i + 1) / len(items))
```

**User Confirmation:**

```python
if st.button("Delete Event", type="primary"):
    st.warning("⚠️ Are you sure? This cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete"):
            delete_event()
    with col2:
        if st.button("Cancel"):
            st.rerun()
```

**Form Layout:**

```python
with st.form("event_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        date = st.date_input("Date")
        category = st.selectbox("Category", options)
    
    with col2:
        time = st.time_input("Time")
        comment = st.text_area("Comment")
    
    submitted = st.form_submit_button("Save Event")
    if submitted:
        # Handle submission
        pass
```

### 13.6 Testing Requirements

**Test Cases:**
```python
# Manual test checklist
"""
TEST CASES:
1. Happy path: Valid data saves successfully
2. Missing required field: Shows validation error
3. Invalid date format: Shows format error
4. RLS: User A cannot see User B's data
5. Edge case: Empty attributes list handled
6. Performance: 100+ events load in <2 seconds
"""
```

**Edge Cases to Consider:**
- Empty data (no events, no categories, no attributes)
- Missing fields (None, null, empty string)
- Invalid data types (string where number expected)
- Long text (comments, descriptions)
- Special characters in names
- Concurrent updates (multiple users)
- Network failures (Supabase timeout)

### 13.7 Git Commit Message Format

```bash
<type>: <subject>

<body>

Last Modified: YYYY-MM-DD HH:MM UTC
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Example:**
```bash
git commit -m "feat: Add event editing functionality

- Created src/event_edit.py with pre-filled forms
- Updated streamlit_app.py menu
- Added RLS validation
- Reused form components from event_entry.py

Last Modified: 2025-11-17 14:30 UTC"
```

---

## 14. QUICK START FOR NEW SESSIONS

### When Starting a New Development Session:

**Provide to Claude/AI Assistant:**

```markdown
Hi Claude! Continuing Events Tracker development.

**ATTACHED:**
- context-LATEST.md (this document - all guidelines included)
- database/schema.sql (PostgreSQL schema)
- src/[relevant_module].py (code to modify, if applicable)
- streamlit_app.py (main application)

**TASK:**
[Describe your specific task here]

**Example:**
> Add event editing functionality with pre-filled forms based on existing event data.

**KEY REQUIREMENTS:**
- Follow all guidelines in Section 13 of context document
- Update "Last Modified" timestamp in docstring header
- Include RLS checks (user_id in all database queries)
- Use existing UI patterns from code
- Add error handling for edge cases

**DELIVERABLES:**
1. Modified/new code files with UPDATED timestamps
2. Integration instructions (where to place files, how to update streamlit_app.py)
3. Testing notes and edge cases
4. Snippet for docs/context-LATEST.md update (if new module)

**That's it!** All coding standards, patterns, and examples are in Section 13.
```

### For Specific Tasks:

**New Module Example:**
```markdown
**TASK:** Create new module `src/event_edit.py`

**Functionality:**
- Load existing event by event_id with all attributes
- Pre-fill form with current values
- Allow editing of attributes
- Validate and save changes
- Show success/error messages

**Requirements:**
- Reuse form components from event_entry.py (DRY principle)
- Add RLS checks (user_id validation)
- UPDATE "Last Modified" timestamp in docstring
- Add to streamlit_app.py navigation menu
```

**Bug Fix Example:**
```markdown
**TASK:** Fix bug in `src/bulk_import.py`

**Issue:** European date format (DD/MM/YYYY) not parsing correctly

**Location:**
- File: src/bulk_import.py
- Function: validate_import_file()
- Lines: ~150

**Requirements:**
- Support DD/MM/YYYY format
- Maintain backward compatibility with YYYY-MM-DD
- UPDATE "Last Modified" timestamp in docstring
- Add inline comment explaining the fix
```

**Feature Addition Example:**
```markdown
**TASK:** Add "Select All Attributes" checkbox to export

**File:** src/view_data_export.py
**Function:** render_view_data_export()

**Feature:**
- Add checkbox: "Select All Attributes"
- If checked, export all attributes for selected category
- If unchecked, show multiselect for individual attributes (current behavior)

**Requirements:**
- UPDATE "Last Modified" timestamp in docstring
- Follow existing Streamlit UI patterns from code
```

---

**END OF CONTEXT DOCUMENT**

---

## Document Info

- **Size:** ~15,000 characters
- **Last Updated:** November 17, 2025, 17:30 UTC
- **Status:** Complete and self-contained
- **Version:** 1.1

**This document contains everything needed for AI-assisted development. No external files or guidelines required!**