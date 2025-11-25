# 1 Events Tracker - Complete Context Document


> **⚠️ INSTRUCTIONS FOR AI TOOLS - Preserving Automatic Chapter Numbering**
> 
> This document uses **automatic chapter numbering**. All chapters (except the main title and TOC) have numbers (1, 1.1, 1.1.1...).
> 
> **RULES:**
> - Main title `# Events Tracker...` - **NO number**
> - TOC `## 📑 Table of Contents` - **NO number**  
> - All other `##` chapters - **HAVE numbers** (1, 2, 3...)
> - Sub-chapters `###` - numbers like 1.1, 1.2, 2.1...
> - Sub-sub-chapters `####` - numbers like 1.1.1, 1.1.2...
> 
> **WHEN EDITING THE DOCUMENT:**
> 1. **Adding:** Add number according to hierarchy, update TOC
> 2. **Deleting:** Renumber following entries to be consecutive, remove from TOC  
> 3. **Moving:** Renumber according to new order, update TOC
> 4. **TOC links:** Format `[Number. Title](#anchor-lowercase-with-number)`
> 5. **Testing:** Verify all numbers are consecutive and all TOC links work
> 
> Read the complete instructions section in the document for details.



> Comprehensive technical documentation for Events Tracker project. Use this document when starting development sessions with Claude, GPT, or other AI coding assistants.

**Version:** 2.2 (Merged)  
**Last Updated:** November 23, 2025  
**Status:** Production Ready ✅

---

## 1.1 📑 Table of Contents

- [1. 📋 Project Overview](#1-project-overview)
  - [1.1. What It Does](#11-what-it-does)
  - [1.2. Perfect For](#12-perfect-for)
- [2. 🏗️ Architecture and Technologies](#2-architecture-and-technologies)
  - [2.1. Tech Stack](#21-tech-stack)
  - [2.2. Project Structure](#22-project-structure)
  - [2.3. Database Pattern](#23-database-pattern)
- [3. 🗄️ Database Schema](#3-database-schema)
  - [3.1. Core Tables](#31-core-tables)
    - [3.1.1. areas](#311-areas)
    - [3.1.2. categories](#312-categories)
    - [3.1.3. attribute_definitions](#313-attribute-definitions)
  - [3.2. Data Tables](#32-data-tables)
    - [3.2.1. events](#321-events)
    - [3.2.2. event_attributes](#322-event-attributes)
  - [3.3. Security: Row Level Security (RLS)](#33-security-row-level-security-rls)
- [4. 🔧 Python Modules and Functionality](#4-python-modules-and-functionality)
  - [4.1. Authentication Module](#41-authentication-module)
  - [4.2. Database Connection](#42-database-connection)
  - [4.3. Structure Viewer](#43-structure-viewer)
  - [4.4. Single Event Entry](#44-single-event-entry)
  - [4.5. Bulk Import](#45-bulk-import)
  - [4.6. View Data - Export](#46-view-data---export)
  - [4.7. View Data - Import](#47-view-data---import)
  - [4.8. Enhanced Structure Exporter](#48-enhanced-structure-exporter)
  - [4.9. Structure Export (Legacy)](#49-structure-export-legacy)
  - [4.10. Template Parsing](#410-template-parsing)
  - [4.11. Smart Rename Detection](#411-smart-rename-detection)
  - [4.12. SQL Generator](#412-sql-generator)
  - [4.13. Excel Validators](#413-excel-validators)
  - [4.14. Template Generator](#414-template-generator)
- [5. 🎨 User Interface](#5-user-interface)
  - [5.1. Main Pages](#51-main-pages)
    - [5.1.1. 1. **Login/Signup** (auth.py)](#511-1-loginsignup-authpy)
    - [5.1.2. 2. **View Structure** (structure_viewer.py)](#512-2-view-structure-structure-viewerpy)
    - [5.1.3. 3. **Add Event** (event_entry.py)](#513-3-add-event-event-entrypy)
    - [5.1.4. 4. **Bulk Import** (bulk_import.py)](#514-4-bulk-import-bulk-importpy)
    - [5.1.5. 5. **View Data - Export** (view_data_export.py)](#515-5-view-data---export-view-data-exportpy)
    - [5.1.6. 6. **View Data - Import** (view_data_import.py)](#516-6-view-data---import-view-data-importpy)
    - [5.1.7. 7. **Download Structure** (enhanced_structure_exporter.py)](#517-7-download-structure-enhanced-structure-exporterpy)
    - [5.1.8. 8. **Upload Template** (excel_parser_new.py)](#518-8-upload-template-excel-parser-newpy)
    - [5.1.9. 9. **Help**](#519-9-help)
- [6. 🔄 Key Workflows](#6-key-workflows)
  - [6.1. User Registration and Login](#61-user-registration-and-login)
  - [6.2. Creating Event Structure](#62-creating-event-structure)
  - [6.3. Recording Events](#63-recording-events)
  - [6.4. Viewing and Editing Events](#64-viewing-and-editing-events)
  - [6.5. Managing Structure](#65-managing-structure)
- [7. 📊 Data Flow](#7-data-flow)
  - [7.1. Event Creation Flow](#71-event-creation-flow)
  - [7.2. Bulk Import Flow](#72-bulk-import-flow)
  - [7.3. Structure Export Flow](#73-structure-export-flow)
  - [7.4. View Data Export/Import Flow](#74-view-data-exportimport-flow)
- [8. 📄 Excel Integration](#8-excel-integration)
  - [8.1. Enhanced Structure Export Format (v2.1)](#81-enhanced-structure-export-format-v21)
  - [8.2. Event Import Template](#82-event-import-template)
  - [8.3. Event Export Format (for editing)](#83-event-export-format-for-editing)
- [9. 🔐 Security](#9-security)
  - [9.1. Row Level Security (RLS)](#91-row-level-security-rls)
  - [9.2. Credentials Management](#92-credentials-management)
  - [9.3. Input Validation](#93-input-validation)
  - [9.4. RLS Requirements in Code](#94-rls-requirements-in-code)
- [. ✅ CORRECT - Always include user_id](#-correct---always-include-user-id)
- [. ❌ WRONG - Missing user_id (RLS violation!)](#-wrong---missing-user-id-rls-violation)
- [1. ⚡ Performance Considerations](#1-performance-considerations)
  - [1.1. Database Queries](#11-database-queries)
- [. Good: Specific columns with join](#-good-specific-columns-with-join)
- [. Bad: Select all with N+1 queries](#-bad-select-all-with-n1-queries)
  - [0.1. Memory Usage](#01-memory-usage)
  - [0.2. Streamlit Performance](#02-streamlit-performance)
- [1. ✅ Testing Instructions](#1-testing-instructions)
  - [1.1. Manual Testing Checklist](#11-manual-testing-checklist)
  - [1.2. Test Data](#12-test-data)
- [2. 🚀 Deployment Notes](#2-deployment-notes)
  - [2.1. Streamlit Cloud Setup](#21-streamlit-cloud-setup)
  - [2.2. Environment Variables](#22-environment-variables)
  - [2.3. Database Setup](#23-database-setup)
  - [2.4. Deployment Checklist](#24-deployment-checklist)
  - [2.5. Git Workflow](#25-git-workflow)
- [. Commit message format](#-commit-message-format)
- [. Push to GitHub](#-push-to-github)
- [. Streamlit Cloud auto-deploys from GitHub](#-streamlit-cloud-auto-deploys-from-github)
- [. Configure secrets in Streamlit Cloud dashboard](#-configure-secrets-in-streamlit-cloud-dashboard)
- [1. 🐛 Common Issues and Solutions](#1-common-issues-and-solutions)
  - [1.1. Database Connection Issues](#11-database-connection-issues)
  - [1.2. Excel Processing Issues](#12-excel-processing-issues)
  - [1.3. Data Import Issues](#13-data-import-issues)
  - [1.4. Performance Issues](#14-performance-issues)
  - [1.5. Authentication Issues](#15-authentication-issues)
- [2. 💻 Useful Code Snippets](#2-useful-code-snippets)
  - [2.1. Database Operations](#21-database-operations)
- [. ✅ CORRECT - Always include user_id](#-correct---always-include-user-id)
- [. ❌ WRONG - Missing user_id (RLS violation!)](#-wrong---missing-user-id-rls-violation)
- [. SELECT with JOIN - get events with attributes and definitions](#-select-with-join---get-events-with-attributes-and-definitions)
- [. INSERT event](#-insert-event)
- [. INSERT attributes (EAV)](#-insert-attributes-eav)
- [. UPDATE event](#-update-event)
- [. DELETE event (CASCADE deletes event_attributes automatically)](#-delete-event-cascade-deletes-event-attributes-automatically)
  - [0.1. Streamlit UI Patterns](#01-streamlit-ui-patterns)
- [. Success message](#-success-message)
- [. Error message](#-error-message)
- [. Warning message](#-warning-message)
- [. Info message](#-info-message)
- [. Show spinner during long operations](#-show-spinner-during-long-operations)
- [. Streamlit form](#-streamlit-form)
- [. Initialize session state](#-initialize-session-state)
- [. Use session state](#-use-session-state)
- [. Use expanders for optional details](#-use-expanders-for-optional-details)
  - [0.1. Error Handling](#01-error-handling)
- [. Usage](#-usage)
- [1. 📐 Development Guidelines](#1-development-guidelines)
  - [1.1. Code Style](#11-code-style)
  - [1.2. Naming Conventions](#12-naming-conventions)
- [. Good](#-good)
- [. Bad](#-bad)
  - [0.1. Module Structure](#01-module-structure)
- [. ... other imports](#-other-imports)
- [. Constants](#-constants)
- [. Helper functions below](#-helper-functions-below)
  - [0.1. Documentation](#01-documentation)
  - [0.2. Error Handling](#02-error-handling)
  - [0.3. RLS Requirements](#03-rls-requirements)
- [. ✅ CORRECT](#-correct)
- [. ❌ WRONG - Will fail or return no data due to RLS](#-wrong---will-fail-or-return-no-data-due-to-rls)
  - [0.1. Testing Approach](#01-testing-approach)
  - [0.2. Git Workflow](#02-git-workflow)
- [1. 🚀 Quick Start for New Sessions](#1-quick-start-for-new-sessions)
  - [1.1. Example Session Starters](#11-example-session-starters)
- [2. 🎯 Future Enhancements](#2-future-enhancements)
  - [2.1. Short-term (Next 1-3 months)](#21-short-term-next-1-3-months)
  - [2.2. Medium-term (3-6 months)](#22-medium-term-3-6-months)
  - [2.3. Long-term (6-12 months)](#23-long-term-6-12-months)
- [3. 📦 Dependencies](#3-dependencies)
  - [3.1. Core Dependencies](#31-core-dependencies)
  - [3.2. Data Processing](#32-data-processing)
  - [3.3. Validation](#33-validation)
  - [3.4. Development](#34-development)
- [. No dev dependencies currently](#-no-dev-dependencies-currently)
- [. Future: pytest, black, flake8, mypy](#-future-pytest-black-flake8-mypy)
- [1. 📊 Performance Benchmarks](#1-performance-benchmarks)
  - [1.1. Current Performance (as of v2.1)](#11-current-performance-as-of-v21)
  - [1.2. Optimization Targets](#12-optimization-targets)
- [2. 🔄 Recent Updates](#2-recent-updates)
  - [2.1. Version 2.2 (November 23, 2025)](#21-version-22-november-23-2025)
  - [2.2. Version 2.1 (November 23, 2025)](#22-version-21-november-23-2025)
  - [2.3. Version 2.0 (November 20, 2025)](#23-version-20-november-20-2025)
- [3. 📞 Support and Resources](#3-support-and-resources)
  - [3.1. Documentation](#31-documentation)
  - [3.2. Internal Documentation](#32-internal-documentation)
  - [3.3. Project Information](#33-project-information)
  - [3.4. Troubleshooting](#34-troubleshooting)
- [4. 🎉 Conclusion](#4-conclusion)

---

## 1.2 📋 Project Overview

**Application Name:** Events Tracker  
**Description:** A comprehensive, hierarchical event tracking system using Entity-Attribute-Value (EAV) pattern  
**Purpose:** Allow users to define custom event structures and record events with dynamic attributes

### 1.2.1 What It Does

**Events Tracker** enables users to:
- Define hierarchical structure (Areas → Categories → Attributes)
- Record events with custom attributes
- Export/import data for offline editing
- Manage structure through Excel templates
- View and analyze tracked events

### 1.2.2 Perfect For

- Personal tracking (fitness, health, habits, finances)
- Project management and time tracking
- Research data collection
- IoT device data logging
- Any scenario requiring flexible, user-defined metadata

---

## 1.3 🏗️ Architecture and Technologies

### 1.3.1 Tech Stack

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

### 1.3.2 Project Structure

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

### 1.3.3 Database Pattern

- **EAV (Entity-Attribute-Value)** pattern for flexible data structure
- **Row Level Security (RLS)** for multi-tenant security
- **Hierarchical Categories** with up to 10 levels of nesting
- **UUID-based identity** management

---

## 1.4 🗄️ Database Schema

### 1.4.1 Core Tables

#### 1.4.1.1 areas
Top-level organization
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `name` (text)
- `icon` (text)
- `color` (text)
- `sort_order` (integer)
- `description` (text)
- `created_at`, `updated_at` (timestamp)

#### 1.4.1.2 categories
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

#### 1.4.1.3 attribute_definitions
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

### 1.4.2 Data Tables

#### 1.4.2.1 events
Main event records
- `id` (uuid, PK)
- `user_id` (uuid, FK → auth.users)
- `category_id` (uuid, FK → categories)
- `event_date` (date, NOT NULL)
- `comment` (text, nullable)
- `created_at`, `edited_at` (timestamp)

#### 1.4.2.2 event_attributes
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

### 1.4.3 Security: Row Level Security (RLS)

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

## 1.5 🔧 Python Modules and Functionality

### 1.5.1 Authentication Module

**File:** `src/auth.py`  
**Status:** Fully Functional ✅  

**Features:**
- AuthManager class for Supabase Auth integration
- signup(), login(), logout() methods
- is_authenticated() - Check auth status
- get_user_id(), get_user_email() - User info
- show_login_page(), show_user_info_sidebar() - Streamlit UI

### 1.5.2 Database Connection

**File:** `src/supabase_client.py`  
**Status:** Active ✅  
**Purpose:** Manages Supabase client initialization and connection

### 1.5.3 Structure Viewer

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

### 1.5.4 Single Event Entry

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

### 1.5.5 Bulk Import

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

### 1.5.6 View Data - Export

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

### 1.5.7 View Data - Import

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

### 1.5.8 Enhanced Structure Exporter

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

### 1.5.9 Structure Export (Legacy)

**File:** `src/reverse_engineer.py`  
**Status:** Functional ✅  

**Features:**
- ReverseEngineer class
- export_to_excel() - Save structure to Excel file
- export_to_bytes() - Generate in-memory Excel for download
- Converts Supabase structure back to template format
- Creates timestamped backup filenames

### 1.5.10 Template Parsing

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

### 1.5.11 Smart Rename Detection

**File:** `src/rename_detector.py`  
**Status:** Functional ✅  

**Features:**
- TemplateObject dataclass for tracking objects
- Detects renames vs. new objects when re-uploading Excel
- Compares names, UUIDs, hierarchical paths
- Prevents data loss during structure updates
- Maintains referential integrity

### 1.5.12 SQL Generator

**File:** `src/sql_generator.py`  
**Status:** Fully Functional ✅  

**Features:**
- SQLGenerator class
- generate_full_schema() - Complete SQL with RLS, indexes
- _generate_core_tables(), _generate_data_tables()
- _generate_rls_policies(), _generate_indexes()
- Supports CASCADE deletion
- Generates INSERT statements from Excel data

### 1.5.13 Excel Validators

**File:** `src/excel_validators.py`  
**Status:** Functional ✅  

**Features:**
- Validation utilities for Excel processing
- Data type validation
- Required field checks
- Format validation

### 1.5.14 Template Generator

**File:** `src/generate_template.py`  
**Status:** Functional ✅  

**Features:**
- Generate sample Excel templates
- Useful for testing and onboarding

---

## 1.6 🎨 User Interface

### 1.6.1 Main Pages

#### 1.6.1.1 **Login/Signup** (auth.py)
- Email + password authentication
- User registration with email confirmation
- Session management
- Remember me functionality

#### 1.6.1.2 **View Structure** (structure_viewer.py)
- Interactive tree view of Areas → Categories → Attributes
- Expandable/collapsible hierarchy
- Shows attribute properties (data type, unit, required, default, validation rules)
- Search and filter functionality
- Statistics dashboard

#### 1.6.1.3 **Add Event** (event_entry.py)
- Single event creation form
- Hierarchical category selection
- Dynamic attribute inputs based on category
- "Sticky" last-used category for quick entry
- Validation of required fields
- Comment field

#### 1.6.1.4 **Bulk Import** (bulk_import.py)
- Import multiple events from Excel/CSV
- Download template with current structure
- Validation and preview before import
- Error reporting with line numbers
- Duplicate handling options

#### 1.6.1.5 **View Data - Export** (view_data_export.py)
- Export events to Excel for viewing/editing
- Filters: category, date range, specific attributes
- Color-coded columns:
  - **PINK:** Read-only (Event_ID, Category_Path, Date)
  - **BLUE:** Editable (attribute values, comment)
- Includes Instructions sheet

#### 1.6.1.6 **View Data - Import** (view_data_import.py)
- Import edited Excel file with change detection
- Shows detailed diff (old vs new values)
- Validation before applying changes
- Updates only changed values
- Full error reporting

#### 1.6.1.7 **Download Structure** (enhanced_structure_exporter.py)
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

#### 1.6.1.8 **Upload Template** (excel_parser_new.py)
- Parse Excel template with name-based references
- Smart rename detection
- Show detected changes before applying
- Validation and error reporting

#### 1.6.1.9 **Help**
- Comprehensive usage guide
- Feature descriptions
- Best practices

---

## 1.7 🔄 Key Workflows

### 1.7.1 User Registration and Login

1. User navigates to app
2. If not authenticated, show login/signup form
3. On signup: Create user in Supabase Auth → Auto-login
4. On login: Validate credentials → Store session
5. Set user_id in session state for all operations

### 1.7.2 Creating Event Structure

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

### 1.7.3 Recording Events

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

### 1.7.4 Viewing and Editing Events

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

### 1.7.5 Managing Structure

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

## 1.8 📊 Data Flow

### 1.8.1 Event Creation Flow
```
User → Add Event Form → Validation → Database
                            ↓
                      Event record created
                            ↓
                   Attribute values saved (EAV)
                            ↓
                      Success message
```

### 1.8.2 Bulk Import Flow
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

### 1.8.3 Structure Export Flow
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

### 1.8.4 View Data Export/Import Flow
```
EXPORT:
User applies filters → Query database → Build DataFrame → 
Format Excel (colors, validations) → Download

IMPORT:
User uploads edited Excel → Parse file → Detect changes →
Show diff (old vs new) → User confirms → Apply updates → Report results
```

---

## 1.9 📄 Excel Integration

### 1.9.1 Enhanced Structure Export Format (v2.1)

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

### 1.9.2 Event Import Template

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

### 1.9.3 Event Export Format (for editing)

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

## 1.10 🔐 Security

### 1.10.1 Row Level Security (RLS)

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

### 1.10.2 Credentials Management

- **Never commit** secrets to Git
- Use `.env` for local development
- Use Streamlit secrets for cloud deployment
- Rotate API keys if exposed (e.g., GitGuardian incidents)

### 1.10.3 Input Validation

- Validate all user inputs
- Sanitize file uploads
- Check data types before database insert
- Use Pydantic models for structured validation
- Validate Excel files before processing

### 1.10.4 RLS Requirements in Code

Every database query MUST include user_id:

```python
# . ✅ CORRECT - Always include user_id
user_id = st.session_state.auth.get_user_id()
response = client.table('events') \
    .select('*') \
    .eq('user_id', user_id) \
    .execute()

# . ❌ WRONG - Missing user_id (RLS violation!)
response = client.table('events') \
    .select('*') \
    .execute()
```

---


---

## 1.12 ✅ Testing Instructions

### 1.12.1 Manual Testing Checklist

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

### 1.12.2 Test Data

Use `src/generate_template.py` to create sample structure:
- 2 Areas (Health, Training)
- 5 Categories (Sleep, Wellness, Cardio, Strength, Upper Body)
- 15 Attributes (various types)

---

## 1.13 🚀 Deployment Notes

### 1.13.1 Streamlit Cloud Setup

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

### 1.13.2 Environment Variables

**Required secrets:**
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon/public key

**Optional:**
- `DEBUG_MODE`: Enable additional logging

### 1.13.3 Database Setup

1. Create Supabase project
2. Run schema.sql to create tables
3. Enable RLS on all tables
4. Verify policies are active
5. Test with dummy user account
6. Check CASCADE deletion rules

### 1.13.4 Deployment Checklist

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

### 1.13.5 Git Workflow

```bash
# . Commit message format
git commit -m "feat: Add event editing functionality

- Created src/event_edit.py
- Updated streamlit_app.py menu
- Added RLS validation

Last Modified: 2025-11-23 12:00 UTC"

# . Push to GitHub
git add .
git commit -m "feature: description"
git push origin main

# . Streamlit Cloud auto-deploys from GitHub
# . Configure secrets in Streamlit Cloud dashboard
```

---

## 1.14 🐛 Common Issues and Solutions

### 1.14.1 Database Connection Issues

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

### 1.14.2 Excel Processing Issues

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

### 1.14.3 Data Import Issues

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

### 1.14.4 Performance Issues

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

### 1.14.5 Authentication Issues

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

### 1.16.8 Git Workflow

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

## 1.17 🚀 Quick Start for New Sessions

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

### 1.17.1 Example Session Starters

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

## 1.18 🎯 Future Enhancements

### 1.18.1 Short-term (Next 1-3 months)

- [ ] **Event Editing:** Edit existing events inline or in a form
- [ ] **Event Deletion:** Delete events with confirmation
- [ ] **Batch Operations:** Delete/update multiple events at once
- [ ] **Export Structure to Multiple Sheets:** Separate sheets for Areas, Categories, Attributes
- [ ] **Advanced Search:** Filter events by multiple criteria
- [ ] **Data Validation:** Enhanced validation rules (regex, ranges, dependencies)

### 1.18.2 Medium-term (3-6 months)

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

### 1.18.3 Long-term (6-12 months)

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

## 1.19 📦 Dependencies

### 1.19.1 Core Dependencies

```txt
streamlit==1.28.0
supabase==2.0.0
pandas==2.0.0
openpyxl==3.1.0
python-dotenv==1.0.0
```

### 1.19.2 Data Processing

```txt
numpy==1.24.0
```

### 1.19.3 Validation

```txt
pydantic==1.10.13
```

### 1.19.4 Development

```txt
# . No dev dependencies currently
# . Future: pytest, black, flake8, mypy
```

---

## 1.20 📊 Performance Benchmarks

### 1.20.1 Current Performance (as of v2.1)

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

### 1.20.2 Optimization Targets

- Page load: < 2 seconds (all pages)
- Event creation: < 500ms
- Bulk import (1000 events): < 10 seconds
- Excel export (10,000 events): < 30 seconds

---

## 1.21 🔄 Recent Updates

### 1.21.1 Version 2.2 (November 23, 2025)
- **Merged context documents** from v2.0 and v2.1
- Consolidated best practices from both versions
- Enhanced documentation structure
- Added comprehensive testing section
- Expanded performance considerations
- Improved code examples

### 1.21.2 Version 2.1 (November 23, 2025)
- **Enhanced Structure Exporter:**
  - Headers moved to row 2 (row 1 blank for title)
  - Sort_Order repositioned to column C
  - Column D (Area) uses minimal width
  - Auto filter on all columns
  - Freeze panes changed to G3
  - Redesigned column grouping (B-C, F collapsed; H-M expanded)
  - All row groups collapsed by default
  - Help sheet added

### 1.21.3 Version 2.0 (November 20, 2025)
- Refactored for better maintainability
- Removed hardcoded numbers from headings
- Improved anchor link structure
- Enhanced consistency in formatting

---

## 1.22 📞 Support and Resources

### 1.22.1 Documentation
- **Streamlit:** https://docs.streamlit.io/
- **Supabase:** https://supabase.com/docs
- **pandas:** https://pandas.pydata.org/docs/
- **openpyxl:** https://openpyxl.readthedocs.io/

### 1.22.2 Internal Documentation
- `INTEGRATION_SUMMARY.md` - Technical integration details
- `CHANGES_v2.1.md` - Recent changes documentation
- `QUICK_REFERENCE_v2.1.md` - Quick reference guide
- `BUGFIX_enhanced_exporter.md` - Bugfix documentation

### 1.22.3 Project Information
- **Developer:** Events Tracker Team
- **Repository:** events-tracker
- **Deployment:** Streamlit Cloud
- **Database:** Supabase

### 1.22.4 Troubleshooting

**For Issues:**
1. Check this context document (Common Issues section)
2. Review error logs in Streamlit Cloud
3. Check Supabase logs for database errors
4. Review recent commits for changes
5. Test with sample data in development environment

---

## 1.23 🎉 Conclusion

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
