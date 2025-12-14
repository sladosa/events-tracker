# Events Tracker

> A flexible, hierarchical event tracking application with Entity-Attribute-Value (EAV) pattern for fully customizable metadata structures.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 Overview

**Events Tracker** is a web application that allows users to define their own hierarchical event structures and record events with dynamic, type-safe attributes. Built with Python and Streamlit, it uses Supabase (PostgreSQL) for secure, scalable data storage with Row Level Security (RLS).

> ⚠️ **Status:** In active development. Core features functional, but not yet production-ready.

**Use Cases:**
- Personal tracking (fitness, health, habits, finances)
- Workout logging with multi-session support (triathlete workflow)
- Research data collection
- Any scenario requiring flexible, user-defined metadata

---

## ✨ Key Features

### 🏗️ **Flexible Structure Management**

- **Hierarchical Categories** - Up to 10 levels deep (Area → Category → Subcategory → ...)
- **Custom Attributes** - Define your own data types: number, text, datetime, boolean, link, image
- **Excel-Based Editing** - Edit structure in familiar Excel format, upload changes
- **Interactive Visualizations** - Network graph, treemap, sunburst chart views
- **Structure Export/Import** - Full Excel round-trip with validation

### 📝 **Event Management**

- **Add Activity** - Mobile-optimized activity entry with photo attachments (NEW)
- **Multi-Session Support** - Track multiple training sessions per day
- **Single Event Entry** - Dynamic forms based on selected category
- **Bulk Import** - Import multiple events from Excel/CSV with validation
- **Export & Edit Workflow** - Export events to Excel, edit, and re-import with change detection

### 📷 **Attachments**

- **Photo Upload** - Attach images to activities (JPG, PNG, WebP)
- **Supabase Storage** - Secure file storage with user isolation
- **Session Preview** - See today's activities with attachment indicators

### 🔐 **Security & Multi-Tenancy**

- **User Authentication** - Email/password via Supabase Auth
- **Row Level Security (RLS)** - Users can ONLY access their own data
- **Storage Policies** - Users can only access their own files

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | Web UI and forms |
| **Backend** | Python 3.11 | Business logic |
| **Database** | Supabase (PostgreSQL) | Data storage with RLS |
| **Storage** | Supabase Storage | File/image attachments |
| **Authentication** | Supabase Auth | User management |
| **Excel Processing** | pandas, openpyxl | Template parsing and exports |

---

## 🗄️ Database Schema

**6 Active Tables:**

```
areas (top-level organization)
  └── categories (hierarchical, self-referencing, max 10 levels)
       └── attribute_definitions (typed metadata fields)

events (main records)
  ├── event_attributes (EAV storage for dynamic values)
  └── event_attachments (photos, files, links)
```

**Storage:**
- Bucket: `activity-attachments` (public, RLS-protected)

See [DATABASE.md](docs/DATABASE.md) for complete schema documentation.

---

## 📦 Module Overview

### **Core Modules** (`src/`)

| Module | Description | Version |
|--------|-------------|---------|
| **streamlit_app.py** | Main application entry point | 1.7.0 |
| **interactive_structure_viewer.py** | Excel-like structure editing | 1.12.10 |
| **add_activity.py** | Mobile-optimized activity entry | 1.2.0 |
| **structure_graph_viewer.py** | Visual graphs (network, treemap, sunburst) | 1.4.1 |
| **event_entry.py** | Single event entry form | ✅ |
| **bulk_import.py** | Bulk event import from Excel/CSV | ✅ |
| **view_data_export.py** | Export events to Excel | ✅ |
| **view_data_import.py** | Import edited Excel with change detection | ✅ |
| **auth.py** | User authentication | ✅ |

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Git
- Supabase account (free tier works)

### **Installation**

```bash
# 1. Clone repository
git clone https://github.com/sladosa/events-tracker.git
cd events-tracker

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your Supabase credentials
```

### **Supabase Setup**

1. Create new Supabase project
2. Copy URL and anon key to `.env`
3. Run SQL schema in Supabase SQL Editor
4. Create storage bucket: `activity-attachments` (public)
5. Apply RLS policies

### **Run Application**

```bash
streamlit run streamlit_app.py
```

Open browser to `http://localhost:8501`

---

## 📱 Mobile Usage

The Add Activity module is optimized for mobile devices:
- Touch-friendly inputs (48px minimum)
- Quick time presets
- Photo capture and upload
- Session preview

---

## 🔄 Recent Updates

### **Version 1.7.0** (2025-12-14)

**✅ New Features:**
- **Add Activity Module** - Mobile-optimized workout/activity entry
- **Photo Attachments** - Upload images to events via Supabase Storage
- **Multi-Session Support** - Track multiple training sessions per day
- **Session Preview** - See today's activities with timestamps

**🔧 Improvements:**
- Network graph tooltip fix (plain text instead of HTML)
- Upload Cancel button properly resets file uploader
- Numeric attributes now save correctly (0.0 handled)

**🗑️ Database Cleanup:**
- Removed unused tables: `templates`, `template_versions`, `name_change_history`
- Activated `event_attachments` table
- Added `session_start` column to events

### **Version 1.6.x** (2025-12)
- Interactive Structure Viewer with Excel upload
- Graph visualizations (network, treemap, sunburst)
- Enhanced Excel export with 3-color system

---

## 📁 Project Structure

```
events-tracker/
├── src/                      # Python modules
│   ├── add_activity.py       # Mobile activity entry (NEW)
│   ├── interactive_structure_viewer.py
│   ├── structure_graph_viewer.py
│   ├── event_entry.py
│   ├── bulk_import.py
│   ├── view_data_export.py
│   ├── view_data_import.py
│   ├── auth.py
│   └── ...
│
├── docs/                     # Documentation
│   ├── DATABASE.md           # Schema documentation
│   └── ...
│
├── streamlit_app.py          # Main application
├── requirements.txt          # Python dependencies
├── .python-version           # Python 3.11
└── README.md
```

---

## 🎯 Roadmap

**Completed:**
- [x] Hierarchical structure management
- [x] EAV pattern for flexible attributes
- [x] Excel import/export workflow
- [x] Interactive graph visualizations
- [x] Mobile-optimized activity entry
- [x] Photo attachments
- [x] Multi-session per day support

**In Progress:**
- [ ] Analytics dashboard with progression charts
- [ ] Session summary (auto-calculate totals)

**Planned:**
- [ ] Quick templates ("Copy yesterday's workout")
- [ ] Garmin/fitness tracker integration
- [ ] PWA support (installable on mobile)
- [ ] Multi-language support (i18n)

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
- Update documentation with changes

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Supabase](https://supabase.com)
- Excel processing with [pandas](https://pandas.pydata.org) & [openpyxl](https://openpyxl.readthedocs.io)
- Graph visualizations with [streamlit-agraph](https://github.com/ChrisDelClea/streamlit-agraph) & [Plotly](https://plotly.com)

---

**⭐ Star this repo if you find it useful!**

**Built with ❤️ for flexible event tracking**
