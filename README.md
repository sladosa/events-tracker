# Events Tracker

> A flexible, hierarchical event tracking application with Entity-Attribute-Value (EAV) pattern for fully customizable metadata structures.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Module Overview](#module-overview)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**Events Tracker** is a NOT YET production-ready web application that allows users to define their own hierarchical event structures and record events with dynamic, type-safe attributes. Built with Python and Streamlit, it uses Supabase (PostgreSQL) for secure, scalable data storage with Row Level Security (RLS).

**Perfect for:**
- Personal tracking (fitness, health, habits, finances)
- Project management and time tracking
- Research data collection
- IoT device data logging
- Any scenario requiring flexible, user-defined metadata

---

## ✨ Key Features

### 🏗️ **Flexible Structure Management**

- **Hierarchical Categories** - Up to 10 levels deep (Area → Category → Subcategory → ...)
- **Custom Attributes** - Define your own data types: number, text, datetime, boolean, link, image
- **Excel-Based Templates** - Create and edit structure in familiar Excel format
- **Smart Rename Detection** - Prevents data loss when updating structure
- **Structure Backup & Restore** - Export/import complete metadata structure

### 📝 **Event Management**

- **Single Event Entry** - Dynamic forms based on selected category
- **Bulk Import** - Import multiple events from Excel/CSV with validation
- **Export & Edit Workflow** - Export events to Excel, edit, and re-import with change detection
- **Event Editing** - Modify past events with pre-filled forms (NEW as of 2025-11-16)
- **Soft Delete** - Mark events as deleted with restore capability

### 👁️ **Visualization & Reporting**

- **Structure Viewer** - Interactive tree view of your hierarchical structure
- **Analytics Dashboard** - Charts, statistics, and trends (IN PROGRESS)
- **Color-Coded Excel Exports** - Clear indication of editable vs read-only columns
- **Search & Filter** - Find events by category, date range, attributes

### 🔐 **Security & Multi-Tenancy**

- **User Authentication** - Email/password signup and login via Supabase Auth
- **Row Level Security (RLS)** - Users can ONLY access their own data (database-level enforcement)
- **Automatic Backups** - Before destructive changes
- **Audit Trail** - Name change history tracking

### 🔧 **Developer Features**

- **EAV Pattern** - Flexible data model for arbitrary attributes
- **Auto SQL Generation** - Generate complete schema from Excel templates
- **Comprehensive Validation** - Type checking, required fields, constraints
- **RESTful API Ready** - Supabase provides automatic API endpoints
- **Modular Architecture** - Clean separation of concerns

---

## 🏛️ Architecture

### **Tech Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | Web UI and forms |
| **Backend** | Python 3.11 | Business logic |
| **Database** | Supabase (PostgreSQL) | Data storage with RLS |
| **Authentication** | Supabase Auth | User management |
| **Excel Processing** | pandas, openpyxl | Template parsing and exports |

### **Database Pattern**

**Entity-Attribute-Value (EAV)** pattern enables flexible metadata:

```
events (main records)
  ├─ event_attributes (EAV storage)
  │    ├─ value_number
  │    ├─ value_text
  │    ├─ value_datetime
  │    ├─ value_boolean
  │    └─ value_json
  │
  └─ event_attachments (files, images, links)
```

**Hierarchical structure:**

```
areas (top-level)
  └─ categories (self-referencing, max 10 levels)
       └─ attribute_definitions (typed metadata fields)
```

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Git
- Supabase account (free tier works)

### **Installation (5 minutes)**

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/events-tracker.git
cd events-tracker

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env and add your Supabase credentials
```

### **Supabase Setup (10 minutes)**

1. Create new Supabase project
2. Copy URL and anon key to `.env`
3. Run SQL schema in Supabase SQL Editor:
   ```bash
   # Use SQL-schema-20251115.sql
   ```

### **Run Application**

```bash
streamlit run streamlit_app.py
```

Open browser to `http://localhost:8501`

**📖 Detailed setup:** See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** | Complete step-by-step installation |
| **[context-LATEST.md](docs/context-LATEST.md)** | Comprehensive technical documentation for AI-assisted development |
| **[quick-reference.md](docs/guides/quick-reference.md)** | Quick reference for View Data Export/Import |
| **[integration-testing.md](docs/testing/integration-testing.md)** | Testing guide for View Data modules |
| **[setup-checklist.md](docs/guides/setup-checklist.md)** | Setup checklist (7 phases) |

---

## 🗂️ Module Overview

### **Core Modules** (`src/`)

| Module | Description | Status |
|--------|-------------|--------|
| **auth.py** | User authentication (signup/login/logout) | ✅ Functional |
| **supabase_client.py** | Database connection management | ✅ Functional |
| **event_entry.py** | Single event entry form | ✅ Functional |
| **bulk_import.py** | Bulk event import from Excel/CSV | ✅ Functional |
| **structure_viewer.py** | Interactive hierarchical structure viewer | ✅ Functional |

### **Structure Management**

| Module | Description | Status |
|--------|-------------|--------|
| **sql_generator.py** | Generate SQL schema from Excel templates | ✅ Functional |
| **excel_parser_new.py** | Parse Excel templates | ✅ Functional |
| **reverse_engineer.py** | Export structure to Excel | ✅ Functional |
| **rename_detector.py** | Smart rename detection | ✅ Functional |

### **View Data (Export/Edit/Import)**

| Module | Description | Status |
|--------|-------------|--------|
| **view_data_export.py** | Export events to Excel with filters & color-coding | ✅ Functional (updated 2025-11-16) |
| **view_data_import.py** | Import edited Excel with change detection | ✅ Functional (updated 2025-11-16) |

---

## 🔬 Development

### **For AI-Assisted Development**

This project includes comprehensive context documentation for AI coding assistants (Claude, GPT, etc.):

📄 **[docs/context-LATEST.md](docs/context-LATEST.md)** - Complete project context including:
- Full database schema
- All module descriptions
- Key workflows
- Code snippets
- Testing instructions
- Deployment notes

**Usage:**
1. Open new AI chat session
2. Paste `docs/context-LATEST.md` content
3. Describe your task/issue
4. AI has full project context!

### **Updating Context Document**

When you add/modify features:

```bash
# Option 1: Auto-update (scans code automatically)
python update_context_doc.py --create-versioned

# Option 2: Manual update (use CHANGELOG template)
# Edit docs/templates/changelog-template.md
# Add to top of docs/context-LATEST.md
```

See [docs/templates/changelog-template.md](docs/templates/changelog-template.md) for structure.

### **Project Structure**

```
events-tracker/
├── src/                      # Python modules
│   ├── auth.py
│   ├── event_entry.py
│   ├── bulk_import.py
│   ├── view_data_export.py
│   ├── view_data_import.py
│   └── ...
│
├── docs/                     # Documentation
│   ├── context-LATEST.md     # AI development context
│   ├── SETUP_GUIDE.md
│   ├── guides/
│   ├── testing/
│   └── templates/
│
├── templates/                # Excel templates
│   └── garmin_fitness_template.xlsx
│
├── streamlit_app.py          # Main application
├── SQL-schema-20251115.sql   # Database schema
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Details

### **Database Schema Summary**

**Core Tables:**
- `templates` - Reusable configurations
- `areas` - Top-level organization
- `categories` - Hierarchical event types (self-referencing, max 10 levels)
- `attribute_definitions` - Define data types and constraints

**Data Tables:**
- `events` - Main event records
- `event_attributes` - EAV storage for dynamic attributes
- `event_attachments` - Files, images, links

**Audit:**
- `name_change_history` - Track renames
- `template_versions` - Version control for templates

**Security:**
- Row Level Security (RLS) policies on all tables
- CASCADE deletion for referential integrity

### **Key Workflows**

**1. Initial Setup**
```
Upload Excel Template → Parse → Generate SQL → Create Database Structure
```

**2. Single Event Entry**
```
Select Category → Dynamic Form Loads → Enter Values → Save to Database
```

**3. Bulk Import**
```
Download Template → Fill Excel → Upload → Validate → Preview → Import
```

**4. Export → Edit → Import**
```
Export to Excel (color-coded) → Edit BLUE columns → Re-import → 
Detect Changes → Preview Diff → Confirm → Apply Updates
```

---

## 🧪 Testing

Run integration tests:

```bash
# Test View Data Export/Import
pytest tests/test_view_data.py

# Test authentication
pytest tests/test_auth.py

# All tests
pytest
```

See [docs/testing/integration-testing.md](docs/testing/integration-testing.md) for detailed testing guide.

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

**Guidelines:**
- Follow PEP 8 style guide
- Add docstrings to new functions
- Update `docs/context-LATEST.md` with changes
- Add tests for new features

---

## 📝 Recent Updates

### **Version 1.1** (2025-11-16)

**✅ New Features:**
- Complete View Data Export/Import workflow
- Change detection engine with field-level diff
- Color-coded Excel exports (PINK = read-only, BLUE = editable)
- Advanced filtering (category, date range, attributes)

**🔧 Improvements:**
- Structure Viewer performance optimization
- Enhanced error handling in bulk import
- European date format support

**📚 Documentation:**
- New comprehensive context document for AI development
- Auto-update script for context maintenance
- CHANGELOG template system

See [docs/context-LATEST.md](docs/context-LATEST.md) for complete changelog.

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/events-tracker/issues)
- **Documentation:** [docs/](docs/)
- **Setup Help:** [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Supabase](https://supabase.com)
- Excel processing with [pandas](https://pandas.pydata.org) & [openpyxl](https://openpyxl.readthedocs.io)

---

## 🎯 Roadmap

**Planned Features:**

- [ ] Advanced analytics dashboard with Plotly charts
- [ ] Event editing UI (in progress)
- [ ] Bulk edit functionality
- [ ] Event change history/audit log
- [ ] Template marketplace (share structures)
- [ ] Mobile-responsive PWA
- [ ] Export analytics to PDF
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Docker deployment support
- [ ] Multi-language support (i18n)

**Vote on features:** [GitHub Discussions](https://github.com/YOUR_USERNAME/events-tracker/discussions)

---

**⭐ Star this repo if you find it useful!**

**Built with ❤️ for flexible event tracking**