# Events Tracker - Complete Context Document

> Comprehensive technical documentation for Events Tracker project. Use this document when starting development sessions with Claude, GPT, or other AI coding assistants.

**Version:** 2.2 (Merged)  
**Last Updated:** November 23, 2025  
**Status:** Production Ready ✅

---

## 📑 Table of Contents

- [Project Overview](#project-overview)
- [Architecture and Technologies](#architecture-and-technologies)
- [Database Schema](#database-schema)
- [Python Modules and Functionality](#python-modules-and-functionality)
- [User Interface](#user-interface)
- [Key Workflows](#key-workflows)
- [Data Flow](#data-flow)
- [Excel Integration](#excel-integration)
- [Security](#security)
- [Performance Considerations](#performance-considerations)
- [Testing Instructions](#testing-instructions)
- [Deployment Notes](#deployment-notes)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Useful Code Snippets](#useful-code-snippets)
- [Development Guidelines](#development-guidelines)
- [Quick Start for New Sessions](#quick-start-for-new-sessions)
- [Future Enhancements](#future-enhancements)

---

## 📋 Project Overview

**Application Name:** Events Tracker  
**Description:** A comprehensive, hierarchical event tracking system using Entity-Attribute-Value (EAV) pattern  
**Purpose:** Allow users to define custom event structures and record events with dynamic attributes

### What It Does

**Events Tracker** enables users to:
- Define hierarchical structure (Areas → Categories → Attributes)
- Record events with custom attributes
- Export/import data for offline editing
- Manage structure through Excel templates
- View and analyze tracked events

### Perfect For

- Personal tracking (fitness, health, habits, finances)
- Project management and time tracking
- Research data collection
- IoT device data logging
- Any scenario requiring flexible, user-defined metadata

---

## 🏗️ Architecture and Technologies

### Tech Stack

**Frontend:**
- Streamlit 1.28.0 (web interface)
- Interactive UI with session state management

**Backend:**
- Python 3.11
- pandas 2.0.0 (data manipulation)
- openpyxl 3.1.0 (Excel processing)
- numpy 1.24.0 (numerical operations)

**Database:**
- Supabase (PostgreSQL)
- Row Level Security (RLS) for multi-tenant security
- CASCADE deletion for referential integrity

**Authentication:**
- Supabase Auth
- Email + password authentication
- Session management

**File Processing:**
- pandas (data manipulation)
- openpyxl (Excel generation and parsing)

### Project Structure

```
events-tracker/
├── streamlit_app.py              # Main application entry point
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── secrets.toml              # Supabase credentials (not in repo)
└── src/
    ├── __init__.py
    ├── auth.py                   # Authentication module
    ├── supabase_client.py        # Database operations
    ├── structure_viewer.py       # Hierarchical structure browser
    ├── event_entry.py            # Single event creation
    ├── bulk_import.py            # Bulk event import
    ├── view_data_export.py       # Export events to Excel
    ├── view_data_import.py       # Import edited events
    ├── excel_parser.py           # Template parser (UUID-based)
    ├── excel_parser_new.py       # Template parser (name-based)
    ├── generate_template.py      # Template generator
    ├── reverse_engineer.py       # Export structure to Excel
    ├── enhanced_structure_exporter.py  # Advanced Excel export v2.1
    ├── rename_detector.py        # Smart rename detection
    ├── sql_generator.py          # SQL generation utilities
    └── excel_validators.py       # Excel validation utilities
```

### Database Pattern

- **EAV (Entity-Attribute-Value)** pattern for flexible data structure
- **Row Level Security (RLS)** for multi-tenant security
- **Hierarchical Categories** with up to 10 levels of nesting
- **UUID-based identity** management

---

## 🗄️ Database Schema

### Core Tables

#### areas
Top-level organization
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `name` (text)
- `icon` (text)
- `color` (text)
- `sort_order` (integer)
- `description` (text)
- `created_at`, `updated_at` (timestamp)

#### categories
Hierarchical event types (max 10 levels)
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `area_id` (uuid, FK → areas)
- `parent_category_id` (uuid, FK → categories, nullable) - self-referencing
- `name` (text)
- `description` (text)
- `level` (integer, 1-10)
- `sort_order` (integer)
- `created_at`, `updated_at` (timestamp)

#### attribute_definitions
Define what data can be captured
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `category_id` (uuid, FK → categories)
- `name` (text)
- `data_type` (text: 'number', 'text', 'datetime', 'boolean', 'link', 'image')
- `unit` (text, nullable)
- `is_required` (boolean)
- `default_value` (text, nullable)
- `validation_rules` (jsonb)
- `sort_order` (integer)
- `created_at`, `updated_at` (timestamp)

### Data Tables

#### events
Main event records
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `category_id` (uuid, FK → categories)
- `event_date` (date, NOT NULL)
- `comment` (text, nullable)
- `created_at`, `edited_at` (timestamp)

#### event_attributes
EAV storage for event data
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `event_id` (uuid, FK → events)
- `attribute_definition_id` (uuid, FK → attribute_definitions)
- `value_number` (numeric, nullable)
- `value_text` (text, nullable)
- `value_datetime` (timestamp, nullable)
- `value_boolean` (boolean, nullable)
- `value_json` (jsonb, nullable)
- `created_at` (timestamp)
- **CONSTRAINT:** Only ONE value column can be populated per row

### Security: Row Level Security (RLS)

All tables have RLS policies ensuring:
- Users can only access their own data
- `user_id` must match authenticated user
- Implemented via Supabase Auth

**Example RLS Policy:**
```sql
CREATE POLICY "Users can only access own data"
ON areas
FOR ALL
USING (user_id = auth.uid());
```

---

## 🔧 Python Modules and Functionality

### Authentication Module

**File:** `src/auth.py`  
**Status:** Fully Functional ✅  

**Features:**
- AuthManager class for Supabase Auth integration
- signup(), login(), logout() methods
- is_authenticated() - Check auth status
- get_user_id(), get_user_email() - User info
- show_login_page(), show_user_info_sidebar() - Streamlit UI

### Database Connection

**File:** `src/supabase_client.py`  
**Status:** Active ✅  
**Purpose:** Manages Supabase client initialization and connection

### Structure Viewer

**File:** `src/structure_viewer.py`  
**Status:** Fully Functional ✅  

**Features:**
- Interactive tree view of Areas → Categories → Attributes
- Expandable/collapsible hierarchy
- Shows attribute properties (data type, unit, required, default)
- Search functionality
- Filter by Area, Filter by Level (1-10)
- Uses indentation instead of nested expanders
- Statistics dashboard (counts, max depth)

### Single Event Entry

**File:** `src/event_entry.py`  
**Status:** Fully Functional ✅  

**Features:**
- Single event creation form
- Hierarchical category selection (Area → Category)
- Dynamic attribute inputs based on category
- Support for all 6 data types (number, text, datetime, boolean, link, image)
- "Sticky" last-used category for quick entry
- Required field validation
- Comment field (optional)
- Mobile-optimized layout

### Bulk Import

**File:** `src/bulk_import.py`  
**Status:** Fully Functional ✅  

**Features:**
- Import multiple events from Excel/CSV
- Uses "›" separator for hierarchical categories (e.g., "Health › Sleep")
- Mixed categories in same file (different event types)
- Download template with current structure
- Validation and preview before import
- Duplicate detection (same category + date)
- Skip or overwrite duplicates
- Detailed error reporting with line numbers

### View Data - Export

**File:** `src/view_data_export.py`  
**Status:** Fully Functional ⭐  
**Last Modified:** 2025-11-16 09:30 UTC  

**Features:**
- Export events to Excel for viewing/editing
- Advanced filters:
  - Filter by category (single or all)
  - Date range selection (from/to)
  - Attribute selection (choose which attributes to export)
- Color-coded columns:
  - **PINK (Read-only):** Event_ID, Category_Path, Date, Created_At
  - **BLUE (Editable):** All attribute columns, Comment
- Professional formatting:
  - Borders, fills, fonts, alignment
  - Auto-sized columns with max width limits
  - Frozen panes (header + first 3 columns)
- Instructions sheet included in workbook

### View Data - Import

**File:** `src/view_data_import.py`  
**Status:** Fully Functional ⭐  
**Last Modified:** 2025-11-16 09:30 UTC  

**Features:**
- Import edited Excel file with change detection
- Parse uploaded Excel with openpyxl
- Validate required columns (Event_ID, Category_Path, Date)
- Handle empty rows and malformed data
- Field-level diff detection
- Compare uploaded data vs current database values
- Normalize values (handle None, empty strings, whitespace)
- Shows detailed diff (old vs new values side-by-side)
- Preview first 10 modified events
- Validation before applying changes
- Updates only changed values with RLS checks
- Full error reporting

### Enhanced Structure Exporter

**File:** `src/enhanced_structure_exporter.py`  
**Status:** Fully Functional ⭐ (v2.1)  
**Last Modified:** 2025-11-23  

**Features:**
- Export complete structure to Excel with professional formatting
- **Layout:**
  - Row 1: Blank (for title/info)
  - Row 2: Headers with auto filter
  - Row 3+: Data
- **Color-coded columns:**
  - Pink: Auto-generated (Type, Level, Sort_Order, Area, Category_Path)
  - Blue: Editable (Category, Attribute_Name, Data_Type, Unit, Is_Required, Default_Value, Validation_Min, Validation_Max)
- **Smart features:**
  - Drop-down validations (Type, Data_Type, Is_Required)
  - Auto-formulas (Level, Area extraction)
  - Column grouping:
    - B-C (Level, Sort_Order): Collapsed
    - F (Category): Collapsed
    - H-M (Attribute details): Expanded
  - Row grouping (Areas and Categories): Collapsed by default
  - Auto filter on all columns (A2:N...)
  - Freeze panes at G3 (after Attribute_Name)
  - Column D (Area): Minimal width to fit content
- **Help sheet** with comprehensive instructions
- Optimal column widths and professional appearance

### Structure Export (Legacy)

**File:** `src/reverse_engineer.py`  
**Status:** Functional ✅  

**Features:**
- ReverseEngineer class
- export_to_excel() - Save structure to Excel file
- export_to_bytes() - Generate in-memory Excel for download
- Converts Supabase structure back to template format
- Creates timestamped backup filenames

### Template Parsing

**File:** `src/excel_parser_new.py`  
**Status:** Fully Functional ✅  

**Features:**
- ExcelTemplateParser class
- Parse Excel template with name-based references
- Extract Areas, Categories, Attributes from Excel
- load_from_database() - Load existing structure from Supabase
- Creates TemplateObject structures for rename detection
- Handles hierarchical paths (Area → Category → Subcategory)
- Smart rename detection
- Show detected changes before applying
- Validation and error reporting

**File:** `src/excel_parser.py`  
**Status:** Legacy (UUID-based) ✅  

**Features:**
- UUID-based template parsing
- Backward compatibility

### Smart Rename Detection

**File:** `src/rename_detector.py`  
**Status:** Functional ✅  

**Features:**
- TemplateObject dataclass for tracking objects
- Detects renames vs. new objects when re-uploading Excel
- Compares names, UUIDs, hierarchical paths
- Prevents data loss during structure updates
- Maintains referential integrity

### SQL Generator

**File:** `src/sql_generator.py`  
**Status:** Fully Functional ✅  

**Features:**
- SQLGenerator class
- generate_full_schema() - Complete SQL with RLS, indexes
- _generate_core_tables(), _generate_data_tables()
- _generate_rls_policies(), _generate_indexes()
- Supports CASCADE deletion
- Generates INSERT statements from Excel data

### Excel Validators

**File:** `src/excel_validators.py`  
**Status:** Functional ✅  

**Features:**
- Validation utilities for Excel processing
- Data type validation
- Required field checks
- Format validation

### Template Generator

**File:** `src/generate_template.py`  
**Status:** Functional ✅  

**Features:**
- Generate sample Excel templates
- Useful for testing and onboarding

---

## 🎨 User Interface

### Main Pages

#### 1. **Login/Signup** (auth.py)
- Email + password authentication
- User registration with email confirmation
- Session management
- Remember me functionality

#### 2. **View Structure** (structure_viewer.py)
- Interactive tree view of Areas → Categories → Attributes
- Expandable/collapsible hierarchy
- Shows attribute properties (data type, unit, required, default, validation rules)
- Search and filter functionality
- Statistics dashboard

#### 3. **Add Event** (event_entry.py)
- Single event creation form
- Hierarchical category selection
- Dynamic attribute inputs based on category
- "Sticky" last-used category for quick entry
- Validation of required fields
- Comment field

#### 4. **Bulk Import** (bulk_import.py)
- Import multiple events from Excel/CSV
- Download template with current structure
- Validation and preview before import
- Error reporting with line numbers
- Duplicate handling options

#### 5. **View Data - Export** (view_data_export.py)
- Export events to Excel for viewing/editing
- Filters: category, date range, specific attributes
- Color-coded columns:
  - **PINK:** Read-only (Event_ID, Category_Path, Date)
  - **BLUE:** Editable (attribute values, comment)
- Includes Instructions sheet

#### 6. **View Data - Import** (view_data_import.py)
- Import edited Excel file with change detection
- Shows detailed diff (old vs new values)
- Validation before applying changes
- Updates only changed values
- Full error reporting

#### 7. **Download Structure** (enhanced_structure_exporter.py)
- Export complete structure to Excel
- **Enhanced version (v2.1)** features:
  - Headers in row 2 (row 1 blank for title)
  - Color-coded columns (Pink=auto, Blue=editable)
  - Drop-down validations (Type, Data_Type, Is_Required)
  - Auto-formulas (Level, Area extraction)
  - Smart column grouping with collapse/expand
  - Row grouping (Areas and Categories): Collapsed
  - Auto filter on all columns
  - Freeze panes (G3)
  - Help sheet with detailed instructions
  - Optimal column widths

#### 8. **Upload Template** (excel_parser_new.py)
- Parse Excel template with name-based references
- Smart rename detection
- Show detected changes before applying
- Validation and error reporting

#### 9. **Help**
- Comprehensive usage guide
- Feature descriptions
- Best practices

---

## 🔄 Key Workflows

### User Registration and Login

1. User navigates to app
2. If not authenticated, show login/signup form
3. On signup: Create user in Supabase Auth → Auto-login
4. On login: Validate credentials → Store session
5. Set user_id in session state for all operations

### Creating Event Structure

**Option 1: Excel Upload**
1. User creates Excel template following format
2. Upload via "Upload Template" page
3. System validates structure (hierarchy, data types)
4. Show preview of changes
5. User confirms
6. Generate SQL statements for all tables
7. Execute with RLS policies
8. Store in Supabase with user_id foreign keys

**Option 2: Manual Entry (future enhancement)**
1. Use UI forms to define Areas/Categories/Attributes
2. Save incrementally to database

### Recording Events

**Single Event:**
1. Navigate to "Add Event" page
2. Select Area and Category from hierarchy
3. Form dynamically loads attributes for selected category
4. Fill in attribute values
5. Add optional comment
6. Submit → Validate → Save to database
7. Last-used category remembered for next entry

**Bulk Import:**
1. Navigate to "Bulk Import" page
2. Download template with current structure
3. Fill Excel/CSV with event data
4. Upload file
5. System validates and shows preview
6. Confirm import
7. Events saved with duplicate detection

### Viewing and Editing Events

**Export:**
1. Navigate to "View Data - Export"
2. Select filters (category, date range, attributes)
3. Click "Export to Excel"
4. Download file with color-coded columns
5. Edit BLUE columns in Excel (offline)

**Import Changes:**
1. Navigate to "View Data - Import"
2. Upload edited Excel file
3. System detects changes (field-level diff)
4. Preview changes (old vs new values)
5. Confirm updates
6. Database updated only for changed values

### Managing Structure

**Download Structure:**
1. Navigate to "Download Structure"
2. Click "Download Enhanced Excel"
3. Receive formatted Excel with:
   - All Areas, Categories, Attributes
   - Color coding, validations, formulas
   - Help sheet with instructions
   - Professional formatting

**Update Structure:**
1. Edit downloaded structure Excel
2. Upload via "Upload Template"
3. System detects renames vs new items
4. Preview changes
5. Confirm → Database updated
6. Referential integrity maintained

---

## 📊 Data Flow

### Event Creation Flow
```
User → Add Event Form → Validation → Database
                            ↓
                      Event record created
                            ↓
                   Attribute values saved (EAV)
                            ↓
                      Success message
```

### Bulk Import Flow
```
User uploads Excel/CSV
        ↓
Parse and validate
        ↓
Preview with row counts
        ↓
User confirms
        ↓
Batch insert to database
  - Events table
  - Event_attributes table (EAV)
        ↓
Report success/errors
```

### Structure Export Flow
```
User requests download
        ↓
Fetch structure from database
  - Areas
  - Categories (hierarchical)
  - Attribute definitions
        ↓
Build hierarchical DataFrame
        ↓
Apply Excel formatting
  - Color coding (Pink/Blue)
  - Drop-down validations
  - Auto-formulas
  - Column/row grouping
  - Freeze panes, auto filter
        ↓
Add Help sheet
        ↓
Return Excel file for download
```

### View Data Export/Import Flow
```
EXPORT:
User applies filters → Query database → Build DataFrame → 
Format Excel (colors, validations) → Download

IMPORT:
User uploads edited Excel → Parse file → Detect changes →
Show diff (old vs new) → User confirms → Apply updates → Report results
```

---

## 📄 Excel Integration

### Enhanced Structure Export Format (v2.1)

**Layout:**
- **Row 1:** Blank (for title/info)
- **Row 2:** Headers with auto filter
- **Row 3+:** Data

**Column Order:**
```
A: Type           (Pink - auto)
B: Level          (Pink - auto, collapsed)
C: Sort_Order     (Pink - auto, collapsed)
D: Area           (Pink - auto, minimal width)
E: Category_Path  (Pink - auto)
F: Category       (Blue - editable, collapsed)
G: Attribute_Name (Blue - editable)
H: Data_Type      (Blue - editable, expanded)
I: Unit           (Blue - editable, expanded)
J: Is_Required    (Blue - editable, expanded)
K: Default_Value  (Blue - editable, expanded)
L: Validation_Min (Blue - editable, expanded)
M: Validation_Max (Blue - editable, expanded)
```

**Features:**
- Drop-down validations for Type, Data_Type, Is_Required
- Auto-formulas: Level (calculates hierarchy depth), Area (extracts from Category_Path)
- Column grouping: B-C, F collapsed; H-M expanded
- Row grouping: All areas and categories collapsed by default
- Auto filter on row 2 (A2:M...)
- Freeze panes at G3 (after Attribute_Name)
- Help sheet with comprehensive instructions

**Example Structure:**
```
Type     | Level | ... | Category_Path        | Attribute_Name | Data_Type | ...
Area     | 1     | ... | Health               |                |           | ...
Category | 2     | ... | Health › Sleep       |                |           | ...
Attribute| 2     | ... | Health › Sleep       | Duration       | number    | ...
Attribute| 2     | ... | Health › Sleep       | Quality        | number    | ...
```

### Event Import Template

**Columns:**
- **Category Path:** "Area › Category" (e.g., "Health › Sleep")
- **Date:** YYYY-MM-DD format
- **[Attribute columns]:** Dynamic based on category
- **Comment:** Optional text

**Example:**
```
Category Path  | Date       | Duration | Quality | Comment
Health › Sleep | 2025-11-20 | 7.5      | 8       | Slept well
Health › Sleep | 2025-11-19 | 6.2      | 6       | Woke up early
Training › Run | 2025-11-20 | 45       | 9       | Morning run
```

### Event Export Format (for editing)

**Color-coded columns:**
- **PINK (Read-only):** Event_ID, Category_Path, Date, Created_At
- **BLUE (Editable):** All attribute columns, Comment

**Instructions Sheet:**
- How to edit values
- Which columns are editable
- How to save and re-import
- Data type requirements

User can edit BLUE columns and re-upload for bulk updates.

---

## 🔐 Security

### Row Level Security (RLS)

All tables have RLS policies ensuring:
- Users can only access their own data
- `user_id` must match authenticated user
- Implemented via Supabase Auth

**Example RLS Policy:**
```sql
-- All tables follow this pattern
CREATE POLICY "Users can only access own data"
ON areas
FOR ALL
USING (user_id = auth.uid());
```

### Credentials Management

- **Never commit** secrets to Git
- Use `.env` for local development
- Use Streamlit secrets for cloud deployment
- Rotate API keys if exposed (e.g., GitGuardian incidents)

### Input Validation

- Validate all user inputs
- Sanitize file uploads
- Check data types before database insert
- Use Pydantic models for structured validation
- Validate Excel files before processing

### RLS Requirements in Code

Every database query MUST include user_id:

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

---

## ⚡ Performance Considerations

### Database Queries

**Optimization strategies:**
- Use `.select()` with specific columns when possible
- Use `.order()` for sorted results
- Use `.in_()` for batch lookups
- Avoid N+1 queries (use joins where possible)
- Limit result sets for large queries

**Example optimized query:**
```python
# Good: Specific columns with join
events = client.table('events') \
    .select('id, event_date, category_id, categories(name)') \
    .eq('user_id', user_id) \
    .limit(100) \
    .execute()

# Bad: Select all with N+1 queries
events = client.table('events').select('*').eq('user_id', user_id).execute()
for event in events.data:
    category = client.table('categories').select('*').eq('id', event['category_id']).execute()
```

### Memory Usage

**Typical loads:**
- DataFrame operations kept in memory
- Structure: ~300 bytes per row
- 1000 rows ≈ 300 KB (acceptable)
- Excel files: typically < 5 MB
- Large exports (10,000+ events): Use pagination or streaming

### Streamlit Performance

**Best practices:**
- Cache database clients with `@st.cache_resource`
- Use `st.spinner()` for user feedback during long operations
- Minimize re-runs with session state
- Use `st.rerun()` sparingly
- Lazy load heavy components (use tabs, expanders)

**Example caching:**
```python
@st.cache_resource
def get_supabase_client():
    """Cached Supabase client initialization."""
    return create_client(url, key)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_structure(_client, user_id):
    """Cached structure loading."""
    return fetch_areas_categories_attributes(_client, user_id)
```

---

## ✅ Testing Instructions

### Manual Testing Checklist

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

**Structure Viewer:**
- [ ] View hierarchical structure (expand/collapse)
- [ ] Search functionality
- [ ] Filter by Area
- [ ] Filter by Level
- [ ] Verify attribute details displayed correctly

**Event Entry:**
- [ ] Create single event with all attribute types
- [ ] Verify required field validation
- [ ] Test date picker
- [ ] Check comment field saves correctly
- [ ] Verify "sticky" category works

**Bulk Import:**
- [ ] Download import template
- [ ] Import file with multiple events
- [ ] Verify duplicate detection
- [ ] Test skip vs overwrite duplicates
- [ ] Check error reporting for invalid data

**View Export/Import:**
- [ ] Export events with filters (category, date range, attributes)
- [ ] Verify Excel formatting (colors, frozen panes, auto filter)
- [ ] Edit BLUE columns in Excel
- [ ] Re-import and check diff detection
- [ ] Verify database updates correctly
- [ ] Test with empty values, special characters

**Structure Export/Import:**
- [ ] Download enhanced structure (v2.1)
- [ ] Verify Excel formatting (colors, grouping, validations, help sheet)
- [ ] Edit structure in Excel
- [ ] Upload modified structure
- [ ] Verify rename detection works
- [ ] Check referential integrity maintained

**Security:**
- [ ] Create event as User A
- [ ] Login as User B
- [ ] Verify User B cannot see User A's events
- [ ] Test RLS on all tables

**Performance:**
- [ ] Test with 100+ events
- [ ] Test with deep category hierarchy (5+ levels)
- [ ] Test with many attributes (20+)
- [ ] Verify Excel export/import performance

### Test Data

Use `src/generate_template.py` to create sample structure:
- 2 Areas (Health, Training)
- 5 Categories (Sleep, Wellness, Cardio, Strength, Upper Body)
- 15 Attributes (various types)

---

## 🚀 Deployment Notes

### Streamlit Cloud Setup

**Step-by-step:**
1. Push code to GitHub repository
2. Connect Streamlit Cloud to repo (main or test-branch)
3. Configure secrets in Streamlit Cloud dashboard:
   ```toml
   [supabase]
   url = "https://xxx.supabase.co"
   key = "eyJ..."
   ```
4. Verify build succeeds
5. Test login/authentication
6. Verify database connectivity

### Environment Variables

**Required secrets:**
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon/public key

**Optional:**
- `DEBUG_MODE`: Enable additional logging

### Database Setup

1. Create Supabase project
2. Run schema.sql to create tables
3. Enable RLS on all tables
4. Verify policies are active
5. Test with dummy user account
6. Check CASCADE deletion rules

### Deployment Checklist

**Pre-Deployment:**
- [ ] Test all features locally
- [ ] Validate database migrations
- [ ] Check RLS policies
- [ ] Update requirements.txt
- [ ] Review error handling
- [ ] Remove debug code
- [ ] Check secrets not in repo

**Deployment:**
- [ ] Push to GitHub (main or test-branch)
- [ ] Verify Streamlit Cloud build succeeds
- [ ] Check secrets configured in Cloud
- [ ] Test login/authentication
- [ ] Verify database connectivity

**Post-Deployment:**
- [ ] Smoke test all pages
- [ ] Test event creation (single and bulk)
- [ ] Test Excel export/import
- [ ] Verify RLS working correctly
- [ ] Monitor error logs
- [ ] Check performance metrics

### Git Workflow

```bash
# Commit message format
git commit -m "feat: Add event editing functionality

- Created src/event_edit.py
- Updated streamlit_app.py menu
- Added RLS validation

Last Modified: 2025-11-23 12:00 UTC"

# Push to GitHub
git add .
git commit -m "feature: description"
git push origin main

# Streamlit Cloud auto-deploys from GitHub
# Configure secrets in Streamlit Cloud dashboard
```

---

## 🐛 Common Issues and Solutions

### Database Connection Issues

**Issue:** "No module named 'src.module'"  
**Solution:** Ensure `__init__.py` exists in src/ directory

**Issue:** Supabase connection fails  
**Solution:** 
- Check SUPABASE_URL and SUPABASE_KEY in secrets
- Verify network connectivity
- Check Supabase project is active

**Issue:** RLS blocking queries  
**Solution:** 
- Ensure `user_id` passed to all queries
- Verify RLS policies are correct
- Check user is authenticated

### Excel Processing Issues

**Issue:** Excel cannot open file  
**Solution:** 
- Update openpyxl to >= 3.1.0
- Check file is not corrupted
- Verify Excel format is correct (.xlsx)

**Issue:** AttributeError in enhanced exporter  
**Solution:** 
- Don't assign strings to comment property
- Use Comment object from openpyxl
- Update openpyxl version

**Issue:** Row groups not collapsing  
**Solution:** 
- Pass `hidden=True` to `ws.row_dimensions.group()`
- Verify Excel version supports grouping

**Issue:** Drop-down validations not working  
**Solution:**
- Check DataValidation formula syntax
- Verify validation range is correct
- Test in Excel (not Google Sheets)

### Data Import Issues

**Issue:** Duplicate detection not working  
**Solution:**
- Check category path format (use "›" separator)
- Verify date format (YYYY-MM-DD)
- Ensure category exists in database

**Issue:** Required field validation fails  
**Solution:**
- Check attribute definition is_required flag
- Verify value is not empty/None
- Check data type matches

**Issue:** Change detection missing edits  
**Solution:**
- Verify Event_ID column is present
- Check value normalization (whitespace, None)
- Compare actual database values

### Performance Issues

**Issue:** Slow page load  
**Solution:**
- Add caching to expensive operations
- Use pagination for large datasets
- Optimize database queries

**Issue:** Memory error on large exports  
**Solution:**
- Limit export size (date range, category filter)
- Use streaming for very large files
- Increase server memory allocation

### Authentication Issues

**Issue:** User session not persisting  
**Solution:**
- Check session state management
- Verify Supabase Auth tokens
- Clear browser cache/cookies

**Issue:** RLS policy errors  
**Solution:**
- Verify user_id in all queries
- Check RLS policies in Supabase dashboard
- Test with SQL query directly

---

## 💻 Useful Code Snippets

### Database Operations

**Query with RLS:**
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

**Join with EAV Pattern:**
```python
# SELECT with JOIN - get events with attributes and definitions
events = client.table('events') \
    .select('*, event_attributes(*, attribute_definitions(*))') \
    .eq('user_id', user_id) \
    .eq('category_id', category_id) \
    .execute()
```

**Insert Event with Attributes:**
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

**Update with RLS:**
```python
# UPDATE event
client.table('events') \
    .update({'comment': 'Updated comment'}) \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

**Delete with CASCADE:**
```python
# DELETE event (CASCADE deletes event_attributes automatically)
client.table('events') \
    .delete() \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

### Streamlit UI Patterns

**Messages:**
```python
# Success message
st.success("✅ Event saved successfully!")

# Error message
st.error("❌ Failed to save event")

# Warning message
st.warning("⚠️ This action cannot be undone")

# Info message
st.info("ℹ️ Fill in all required fields")
```

**Spinner:**
```python
# Show spinner during long operations
with st.spinner("Loading events..."):
    events = fetch_events(client, user_id)
```

**Form with Validation:**
```python
# Streamlit form
with st.form("event_form"):
    date = st.date_input("Date", value=datetime.now())
    category = st.selectbox("Category", options)
    
    submitted = st.form_submit_button("Save Event")
    if submitted:
        if not category:
            st.error("Please select a category")
        else:
            save_event(date, category)
            st.success("Event saved!")
```

**Session State:**
```python
# Initialize session state
if 'last_category' not in st.session_state:
    st.session_state.last_category = None

# Use session state
st.session_state.last_category = selected_category
```

**Expanders:**
```python
# Use expanders for optional details
with st.expander("Advanced Options", expanded=False):
    show_advanced_options()
```

### Error Handling

**Try-Catch Pattern:**
```python
try:
    result = client.table('events').insert(data).execute()
    st.success("✅ Event saved!")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    # Log error for debugging
    print(f"Error details: {str(e)}")
```

**Validation Pattern:**
```python
def validate_event_data(data):
    """Validate event data before insert."""
    errors = []
    
    if not data.get('event_date'):
        errors.append("Date is required")
    
    if not data.get('category_id'):
        errors.append("Category is required")
    
    # Check required attributes
    for attr in required_attributes:
        if not data.get(attr['name']):
            errors.append(f"{attr['name']} is required")
    
    return errors

# Usage
errors = validate_event_data(form_data)
if errors:
    for error in errors:
        st.error(f"❌ {error}")
else:
    save_event(form_data)
```

---

## 📐 Development Guidelines

### Code Style

- Follow **PEP 8** for Python code
- Use **type hints** where applicable for function parameters and returns
- Add **docstrings** for all classes and public methods
- Use **f-strings** for string formatting
- Use **Pathlib** for file paths (where appropriate)
- Keep functions focused (single responsibility principle)
- Use meaningful variable names (avoid abbreviations)

### Naming Conventions

- **snake_case** for functions and variables
- **PascalCase** for classes
- **UPPER_CASE** for constants
- Descriptive names (avoid abbreviations unless standard)

**Examples:**
```python
# Good
def calculate_event_duration(start_time, end_time):
    pass

class EventManager:
    pass

MAX_UPLOAD_SIZE = 10_000_000

# Bad
def calc(s, e):
    pass

class evtMgr:
    pass

maxSize = 10000000
```

### Module Structure

Every module should follow this structure:

```python
"""
Module Name - Brief Description

Features:
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

Dependencies: streamlit, pandas, supabase

Last Modified: YYYY-MM-DD HH:MM UTC
"""

import streamlit as st
from typing import Optional, Dict, List
# ... other imports

# Constants
DEFAULT_PAGE_SIZE = 100
MAX_RETRIES = 3

def main_function(client, user_id: str) -> Optional[Dict]:
    """
    Main entry point for the module.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
        
    Returns:
        Dict with results or None on error
        
    Raises:
        ValueError: If user_id is invalid
    """
    try:
        # Implementation
        pass
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Helper functions below
def _helper_function(data: List) -> Dict:
    """Private helper function."""
    pass
```

### Documentation

- Keep documentation (.md files) in numbering style of this document
- Update "Last Modified" timestamp in docstrings when changing code
- Include examples in docstrings where helpful
- Document complex algorithms or business logic
- Add inline comments for non-obvious code

### Error Handling

Always wrap database operations:

```python
try:
    result = client.table('events').insert(data).execute()
    st.success("✅ Event saved!")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    # Log error for debugging in production
    if DEBUG_MODE:
        print(f"Stack trace: {traceback.format_exc()}")
```

### RLS Requirements

**CRITICAL:** Every database query MUST include user_id:

```python
# ✅ CORRECT
response = client.table('events') \
    .select('*') \
    .eq('user_id', user_id) \
    .execute()

# ❌ WRONG - Will fail or return no data due to RLS
response = client.table('events').select('*').execute()
```

### Testing Approach

- **Test happy path** (valid data)
- **Test edge cases** (empty, null, invalid data)
- **Test RLS** (user isolation)
- **Test performance** (100+ records)
- **Verify error messages** are user-friendly
- **Test UI** (all buttons, forms, navigation)

### Git Workflow

**Commit message format:**
```bash
git commit -m "feat: Add event editing functionality

- Created src/event_edit.py
- Updated streamlit_app.py menu
- Added RLS validation
- Added unit tests

Last Modified: 2025-11-23 12:00 UTC"
```

**Branch strategy:**
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/xyz`: Individual feature branches
- `bugfix/xyz`: Bug fix branches

**Pull request checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] RLS checks included
- [ ] Error handling implemented
- [ ] Timestamps updated

---

## 🚀 Quick Start for New Sessions

When starting a new development session with an AI assistant:

```markdown
Hi Claude! Continuing Events Tracker development.

**ATTACHED FILES:**
- CONTEXT_MERGED_v2.2.md (this complete context document)
- database/schema.sql (PostgreSQL schema with RLS)
- src/[relevant_module].py (code to modify)
- streamlit_app.py (main application)

**CURRENT TASK:**
[Describe specific task or feature to implement]

**CONTEXT:**
[Brief explanation of what was done previously, if applicable]

**REQUIREMENTS:**
- Follow guidelines in "Development Guidelines" section
- Update "Last Modified" timestamp in docstrings
- Include RLS checks (user_id in all queries)
- Use existing UI patterns from similar modules
- Add comprehensive error handling
- Test with sample data

**EXPECTED DELIVERABLES:**
1. Modified/new code files with updated timestamps
2. Integration instructions (how to add to streamlit_app.py)
3. Testing notes (what to test and how)
4. Documentation updates (if applicable)

**QUESTIONS:**
[Any specific questions or clarifications needed]
```

### Example Session Starters

**Adding a new feature:**
```markdown
Task: Add event editing functionality
- Allow users to edit existing events
- Preserve event_id and created_at
- Update edited_at timestamp
- Show change history (optional)
```

**Fixing a bug:**
```markdown
Task: Fix duplicate detection in bulk import
- Current behavior: Duplicates not being detected correctly
- Expected behavior: Same category + date = duplicate
- Test case: Upload same event twice
```

**Optimizing performance:**
```markdown
Task: Optimize event loading for large datasets
- Current issue: Slow page load with 1000+ events
- Goal: Load events with pagination
- Target: < 2 seconds for initial load
```

---

## 🎯 Future Enhancements

### Short-term (Next 1-3 months)

- [ ] **Event Editing:** Edit existing events inline or in a form
- [ ] **Event Deletion:** Delete events with confirmation
- [ ] **Batch Operations:** Delete/update multiple events at once
- [ ] **Export Structure to Multiple Sheets:** Separate sheets for Areas, Categories, Attributes
- [ ] **Advanced Search:** Filter events by multiple criteria
- [ ] **Data Validation:** Enhanced validation rules (regex, ranges, dependencies)

### Medium-term (3-6 months)

- [ ] **Event Filtering and Search:**
  - Full-text search across events
  - Advanced filters (date range, category, attribute values)
  - Save filter presets
- [ ] **Data Visualization:**
  - Charts and graphs (line, bar, pie)
  - Trend analysis
  - Heatmaps for frequency
- [ ] **Export Formats:**
  - CSV, JSON export
  - PDF reports
- [ ] **Import from Other Sources:**
  - Google Sheets integration
  - API imports
  - CSV imports with mapping
- [ ] **Mobile Optimization:**
  - Responsive design improvements
  - Touch-friendly interfaces
  - Mobile app (PWA)

### Long-term (6-12 months)

- [ ] **Multi-user Collaboration:**
  - Shared templates
  - Shared events with permissions
  - Collaborative editing
  - Team workspaces
- [ ] **Template Marketplace:**
  - Share structures publicly
  - Browse and import community templates
  - Rating and reviews
- [ ] **API for Integrations:**
  - RESTful API
  - Webhooks
  - OAuth integration
- [ ] **Machine Learning Insights:**
  - Pattern detection
  - Anomaly detection
  - Predictions and recommendations
- [ ] **Custom Reports:**
  - Report builder
  - Scheduled reports via email
  - Dashboard widgets
- [ ] **Audit Trail:**
  - Full change history
  - Rollback capability
  - User action logs

---

## 📦 Dependencies

### Core Dependencies

```txt
streamlit==1.28.0
supabase==2.0.0
pandas==2.0.0
openpyxl==3.1.0
python-dotenv==1.0.0
```

### Data Processing

```txt
numpy==1.24.0
```

### Validation

```txt
pydantic==1.10.13
```

### Development

```txt
# No dev dependencies currently
# Future: pytest, black, flake8, mypy
```

---

## 📊 Performance Benchmarks

### Current Performance (as of v2.1)

**Event Operations:**
- Single event insert: < 500ms
- Bulk import (100 events): < 5 seconds
- Event query (100 records): < 1 second

**Excel Operations:**
- Structure export (100 items): < 2 seconds
- Event export (1000 events): < 5 seconds
- Excel parsing: < 3 seconds

**Page Load Times:**
- Login page: < 1 second
- Structure viewer (100 items): < 2 seconds
- Event entry form: < 1 second

### Optimization Targets

- Page load: < 2 seconds (all pages)
- Event creation: < 500ms
- Bulk import (1000 events): < 10 seconds
- Excel export (10,000 events): < 30 seconds

---

## 🔄 Recent Updates

### Version 2.2 (November 23, 2025)
- **Merged context documents** from v2.0 and v2.1
- Consolidated best practices from both versions
- Enhanced documentation structure
- Added comprehensive testing section
- Expanded performance considerations
- Improved code examples

### Version 2.1 (November 23, 2025)
- **Enhanced Structure Exporter:**
  - Headers moved to row 2 (row 1 blank for title)
  - Sort_Order repositioned to column C
  - Column D (Area) uses minimal width
  - Auto filter on all columns
  - Freeze panes changed to G3
  - Redesigned column grouping (B-C, F collapsed; H-M expanded)
  - All row groups collapsed by default
  - Help sheet added

### Version 2.0 (November 20, 2025)
- Refactored for better maintainability
- Removed hardcoded numbers from headings
- Improved anchor link structure
- Enhanced consistency in formatting

---

## 📞 Support and Resources

### Documentation
- **Streamlit:** https://docs.streamlit.io/
- **Supabase:** https://supabase.com/docs
- **pandas:** https://pandas.pydata.org/docs/
- **openpyxl:** https://openpyxl.readthedocs.io/

### Internal Documentation
- `INTEGRATION_SUMMARY.md` - Technical integration details
- `CHANGES_v2.1.md` - Recent changes documentation
- `QUICK_REFERENCE_v2.1.md` - Quick reference guide
- `BUGFIX_enhanced_exporter.md` - Bugfix documentation

### Project Information
- **Developer:** Events Tracker Team
- **Repository:** events-tracker
- **Deployment:** Streamlit Cloud
- **Database:** Supabase

### Troubleshooting

**For Issues:**
1. Check this context document (Common Issues section)
2. Review error logs in Streamlit Cloud
3. Check Supabase logs for database errors
4. Review recent commits for changes
5. Test with sample data in development environment

---

## 🎉 Conclusion

**Events Tracker** is a fully-functional, production-ready application for hierarchical event tracking with comprehensive Excel integration. The v2.1 Enhanced Structure Exporter provides professional-grade Excel files with smart grouping, validations, and help documentation.

This merged context document (v2.2) combines the best aspects of previous versions, providing:
- **Complete technical reference** for all modules and features
- **Comprehensive development guidelines** for consistent code quality
- **Detailed workflows and data flows** for understanding the system
- **Practical code examples** for common operations
- **Testing and deployment procedures** for production readiness

**Current Status:** ✅ Production Ready  
**Next Steps:** 
- User testing and feedback collection
- Performance optimization for large datasets
- Implementation of short-term enhancements

---

**Document Version:** 2.2 (Merged)  
**Last Updated:** 2025-11-23 12:00 UTC  
**Status:** Complete and production-ready ✅

**This document contains everything needed for AI-assisted development and maintenance of Events Tracker!**
