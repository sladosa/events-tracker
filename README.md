# Events Tracker

> A flexible, hierarchical event tracking system with Entity-Attribute-Value (EAV) pattern for fully customizable metadata structures.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.35+-FF4B4B.svg)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)

---

## 🎯 Overview

**Events Tracker** enables users to define custom hierarchical event structures and record events with dynamic, type-safe attributes. Built with Python and Streamlit, using Supabase (PostgreSQL) for secure data storage with Row Level Security (RLS).

**Key Features:**
- **Hierarchical Structure** - Areas → Categories (up to 10 levels) → Attributes → Events
- **Excel-Based Workflow** - Import/export structure and events via Excel templates
- **EAV Pattern** - Flexible metadata with typed attributes (number, text, datetime, boolean, link, image)
- **Multi-Session Support** - Track multiple activities per day with timestamps
- **Photo Attachments** - Upload images via Supabase Storage
- **Interactive Visualizations** - Network graph, Treemap, Sunburst charts

---

## 🗄️ Database Schema

**6 Active Tables:**

```
areas                    - Top-level organization (e.g., "Health", "Training")
categories               - Hierarchical structure (self-referencing, max 10 levels)
attribute_definitions    - Typed metadata fields for categories
events                   - Main event records with date + session_start timestamp
event_attributes         - EAV storage for dynamic attribute values
event_attachments        - Photos, files, links attached to events
```

**Additional Tables:**
- `activity_presets` - Shortcuts for filtering (⚠️ **KNOWN ISSUE**: Cannot add new shortcuts)
- `data_shares` - Data sharing between users

See `SQL schema_V2.sql` for complete schema.

---

## 📦 Python Modules Reference

### **Main Application**

| Module | Version | Description |
|--------|---------|-------------|
| **streamlit_app.py** | v2.4.0 | Main entry point with authentication, navigation, and page routing. Includes password reset support (⚠️ admin dashboard not implemented). |

### **Core Modules** (`src/`)

| Module | Version | Purpose |
|--------|---------|---------|
| **interactive_structure_viewer.py** | v1.13.3 | **Primary hub** for structure management. Excel-like viewer with Read-only/Edit modes. Manages Areas, Categories, Attributes. Features: bulk operations, Excel import/export, validation, auto-bootstrap for empty DB. |
| **add_activity.py** | v2.4.0 | Mobile-optimized activity entry form. Filter-first design (Area → Category drill-down). Multi-session support, photo attachments, Bootstrap integration. ⚠️ **KNOWN ISSUE**: Shortcuts system doesn't work - cannot add new shortcuts. |
| **show_events.py** | v2.6.6 | View/edit/delete events with table UI. Filters: Area + Category (downstream) + Date range. Bulk delete, sort order (newest/oldest). Integrated Excel export/import. Parent-child event grouping. |
| **excel_events_io.py** | v2.5.8 | Unified Excel export/import for events. Features: LEGEND-based import, session merging, change detection, 3-color formatting. Exports events with full attribute hierarchy. |
| **bulk_import.py** | - | Bulk event import from Excel/CSV. Supports mixed categories, duplicate detection, comprehensive validation. Uses `>` separator for hierarchical paths. |
| **view_data_export.py** | - | **DEPRECATED** - Export functionality now integrated into `show_events.py` and `excel_events_io.py`. |
| **view_data_import.py** | - | **DEPRECATED** - Import functionality now integrated into `show_events.py` and `excel_events_io.py`. |

### **Structure Management**

| Module | Purpose |
|--------|---------|
| **enhanced_structure_exporter.py** | Advanced Excel export with 3-color system (Pink=read-only, Yellow=identifiers, Blue=editable). Includes formulas, validation dropdowns, grouping, header comments. |
| **hierarchical_parser.py** | Parse `Hierarchical_View` Excel sheet. Detects new/updated Areas/Categories/Attributes from Category_Path column. Batch inserts, validation with common mistake detection. |
| **structure_viewer.py** | **DEPRECATED** - Tree navigation UI. All functionality moved to `interactive_structure_viewer.py`. **Can be removed**. |
| **structure_graph_viewer.py** | v1.4.1 | Interactive visualizations: Treemap, Sunburst, Network Graph. Drill-down by Area/Category, filter Events, tooltips with entity details. |
| **structure_graph_viewer_agraph.py** | v1.0.0 | Obsidian-style network graph (force-directed). Click to expand/collapse, drag nodes, zoom/pan. Uses `streamlit-agraph`. |

### **Excel Processing**

| Module | Purpose |
|--------|---------|
| **excel_parser.py** | Reads/validates Excel templates with UUID-based identifiers. Uses Pydantic models for validation. **May be obsolete** - check if `excel_parser_new.py` replaces it. |
| **excel_parser_new.py** | Parses Excel templates using **names** as identifiers (instead of UUIDs). Creates `TemplateObject` structures for rename detection. |
| **excel_validators.py** | Validates Excel templates. Detects uniqueness violations within hierarchical scopes, highlights errors in Excel with comments. |
| **error_reporter.py** | Generates Excel files with validation errors highlighted in yellow + error comments. Used for user feedback on import failures. |
| **generate_template.py** | Generates sample Excel templates with UUIDs. Creates Garmin Fitness tracking example structure. **For development/testing**. |

### **Helper Modules**

| Module | Purpose |
|--------|---------|
| **auth.py** | v2.4.2 | User authentication (signup, login, logout). Handles password reset with email (via Supabase Auth). Auto-detects URL for test/main branches. ⚠️ **KNOWN ISSUE**: Admin dashboard for password reset requests not implemented. |
| **rename_detector.py** | Multi-signal algorithm for detecting renamed vs new objects. Uses name similarity, hierarchy position, metadata matching. Prevents duplicate creation on structure imports. |
| **reverse_engineer.py** | Exports Supabase structure back to Excel template. Integrates with `EnhancedStructureExporter` for advanced formatting. |
| **sql_generator.py** | Generates PostgreSQL/Supabase SQL schema from Excel template. Creates tables, RLS policies, CASCADE deletion, indexes. |
| **supabase_client.py** | Manages Supabase database operations. Connection testing, backup/rollback capabilities (placeholder - raw SQL via Supabase dashboard). |
| **state_machine.py** | v1.2.0 | State management for Interactive Structure Viewer. Dataclass-based state (read_only/edit modes), clear transitions, filter management, form tracking. |

---

## 📁 Excel Templates

### **Structure Export/Import** (`structure_export_*.xlsx`)

Template for managing database organization (Areas → Categories → Attributes).

**Sheets:**
- **Hierarchical_View** - Main editing sheet with color-coded columns:
  - 🟪 **Pink** (read-only): Type, Level, Area (auto-calculated)
  - 🟨 **Yellow** (identifiers): UUID, Category_Path
  - 🟦 **Blue** (editable): Name, Description, Data_Type, Unit, Is_Required, Sort_Order
- **Help** - Comprehensive guide with common scenarios and mistakes to avoid

**Workflow:**
1. Export structure from Interactive Structure Viewer
2. Edit in Excel (add/modify rows in blue columns)
3. Re-import - system detects changes and validates
4. Review diff, confirm changes

**Features:**
- Drop-down validation for Type, Data_Type, Is_Required
- Auto-calculated formulas for Level, Area
- Row grouping (collapsible by Area/Category)
- Header comments explaining each column

### **Events Export/Import** (`events_export_*.xlsx`)

Template for bulk event management with full attribute data.

**Sheets:**
- **Events** - Main data sheet with:
  - **ATTRIBUTE LEGEND** - First row maps column letters to attribute names
  - Fixed columns: Event_Date, Event_Time, Comment, Category_Path
  - Dynamic columns: One column per attribute (varies by category)
  - Color-coded: Pink (read-only IDs), Blue (editable data)
- **Help** - Detailed import/export guide (v2.5.0)

**Workflow:**
1. Export events from Show Events module
2. Edit data (or add new events) in Excel
3. Re-import - system uses LEGEND to map columns to attributes
4. Change detection: New events inserted, modified events updated

**Features:**
- Session merging: Parent-child events with same timestamp merge into single row
- Supports multi-level hierarchies
- Type-safe attribute handling (number, text, datetime, boolean, link)
- Respects sort order (newest/oldest first)

---

## ⚠️ Known Issues

### **1. Shortcuts System (Add Activity)**
**Status:** Not functional  
**Issue:** Cannot add new shortcuts via the shortcuts panel  
**Impact:** Users cannot save frequently-used filter combinations  
**Workaround:** Manually select Area + Category each time  
**Location:** `add_activity.py` + `activity_presets` table

### **2. Password Reset (Authentication)**
**Status:** Partially implemented  
**Issue:** User receives reset email and can reset password, BUT admin has no dashboard to view/manage reset requests  
**Impact:** No way for administrators to monitor password reset activity  
**Workaround:** Users can reset independently via email link  
**Location:** `auth.py` v2.4.2

---

## 🗑️ Files That Can Be Removed

### **Recommended for Deletion:**

1. **`src/structure_viewer.py`**  
   - **Reason:** Explicitly marked as DEPRECATED in code  
   - **Replacement:** All functionality moved to `interactive_structure_viewer.py`

2. **`src/view_data_export.py`**  
   - **Reason:** Export functionality now integrated into `show_events.py` and `excel_events_io.py`  
   - **Replacement:** Use "Export to Excel" button in Show Events module

3. **`src/view_data_import.py`**  
   - **Reason:** Import functionality now integrated into `show_events.py` and `excel_events_io.py`  
   - **Replacement:** Use "Import from Excel" button in Show Events module

4. **`Complete auth setup.txt`**  
   - **Reason:** Outdated documentation (likely superseded by code comments and README)  
   - **Action:** Review content, move any relevant info to README, then delete

5. **`Code_guidelines.md`**  
   - **Reason:** If well-documented in code and README, may be redundant  
   - **Action:** Review and merge with README if needed, or keep if actively maintained

6. **`requirements-dev.txt`**  
   - **Reason:** Development dependencies not essential for deployment  
   - **Action:** Keep if actively developing, otherwise safe to remove

7. **`tests/` directory** (if not actively used)  
   - **Reason:** Only contains `test_state_machine.py` - verify if tests are maintained  
   - **Action:** If tests aren't run regularly, consider removing

8. **`src/excel_parser.py`** (conditional)  
   - **Reason:** May be obsolete if `excel_parser_new.py` fully replaces it  
   - **Action:** Verify no imports of `excel_parser.py` in codebase, then remove

### **Optional - Keep for Reference:**

- **`generate_template.py`** - Useful for generating sample structures during development
- **`sql_generator.py`** - Useful if schema needs to be regenerated
- **`reverse_engineer.py`** - Core functionality still in use

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Supabase account (free tier works)

### **Installation**

```bash
# Clone repository
git clone https://github.com/sladosa/events-tracker.git
cd events-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your Supabase credentials:
# SUPABASE_URL=your-project-url
# SUPABASE_KEY=your-anon-key
```

### **Supabase Setup**

1. Create new Supabase project at [supabase.com](https://supabase.com)
2. Go to **Project Settings** → **API** → Copy:
   - Project URL → `SUPABASE_URL` in `.env`
   - Anon/Public key → `SUPABASE_KEY` in `.env`
3. Go to **SQL Editor** → Paste contents of `SQL schema_V2.sql` → Run
4. Go to **Storage** → Create bucket: `activity-attachments` (public, with RLS policies)

### **Run Application**

```bash
streamlit run streamlit_app.py
```

Open browser to `http://localhost:8501`

---

## 📊 Typical Workflow

### **1. First-Time Setup**
1. Create account (Sign Up)
2. System auto-creates default structure (Bootstrap)
3. Go to **Interactive Structure Viewer** → Edit structure or import Excel template

### **2. Structure Management**
1. **Interactive Structure Viewer** (main hub):
   - Read-only mode: Browse Areas → Categories → Attributes
   - Edit mode: Add/Edit/Delete entities with validation
   - Excel workflow: Export → Edit → Import → Review diff → Apply changes
2. **Graph Viewer**: Visualize structure (Network/Treemap/Sunburst)

### **3. Event Tracking**
1. **Add Activity**: Mobile-optimized quick entry (Area → Category filter → Fill attributes → Upload photo)
2. **Show Events**: View table, filter by Area/Category/Date, sort by newest/oldest
3. **Bulk Operations**:
   - Export to Excel → Edit multiple events → Re-import
   - Bulk delete: Select rows → Delete button

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit (Python web framework) |
| **Backend** | Python 3.11 |
| **Database** | Supabase (PostgreSQL with RLS) |
| **Storage** | Supabase Storage (file attachments) |
| **Auth** | Supabase Auth (email/password) |
| **Excel** | pandas, openpyxl |
| **Visualizations** | Plotly, streamlit-agraph |

---

## 📄 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

Built with [Streamlit](https://streamlit.io) | Powered by [Supabase](https://supabase.com) | Excel processing: [pandas](https://pandas.pydata.org) & [openpyxl](https://openpyxl.readthedocs.io)

---

**⭐ Star this repo if you find it useful!**
