# Events Tracker

Flexible event tracking system with customizable metadata structure using EAV (Entity-Attribute-Value) pattern. Perfect for tracking anything from fitness activities to project milestones.

## 🎯 Features

- **Fully Customizable Structure**: Define your own Areas, Categories, and Attributes via Excel
- **Hierarchical Organization**: Support for nested categories (unlimited levels)
- **UUID-Based Identity**: Rename anything without breaking relationships
- **Row Level Security**: Multi-user support with secure data isolation
- **Backup & Restore**: Automatic backups before any destructive changes
- **Change Preview**: See exactly what will change before applying
- **CASCADE Deletion**: Smart deletion that handles dependent records
- **Excel Templates**: Easy import/export of structure definitions
- **SQL Generation**: Auto-generate database schema from templates

## 📋 Project Structure

```
events-tracker/
├── streamlit_app.py              # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── templates/
│   └── garmin_fitness_template.xlsx   # Example template
├── src/
│   ├── generate_template.py     # Template generator script
│   ├── excel_parser.py          # Excel validation and parsing
│   ├── sql_generator.py         # SQL schema generation
│   ├── supabase_client.py       # Supabase operations wrapper
│   └── reverse_engineer.py      # Export structure to Excel
├── backups/                      # Auto-generated backups (gitignored)
├── exports/                      # Exported Excel files (gitignored)
└── docs/
    └── ARCHITECTURE.md           # Detailed architecture docs
```

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/sladosa/events-tracker.git
cd events-tracker
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in details:
   - **Name**: `events-tracker` (or your choice)
   - **Database Password**: Generate strong password
   - **Region**: Choose closest to you (e.g., `eu-central-1`)
4. Wait for project creation (~2 minutes)
5. Get credentials:
   - Click "Settings" → "API"
   - Copy **Project URL**
   - Copy **anon public** key

### 4. Configure Environment

**Option A: Streamlit Secrets (Recommended for Streamlit Cloud)**

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
```

**Option B: Environment Variables (Local Development)**

```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

### 5. Generate and Apply Database Schema

#### Method 1: Using Streamlit App (Easiest)

```bash
streamlit run streamlit_app.py
```

1. Go to "Generate SQL" page
2. Upload `templates/garmin_fitness_template.xlsx`
3. Download generated SQL file
4. Go to Supabase Dashboard → SQL Editor
5. Paste SQL and click "Run"

#### Method 2: Manual SQL Execution

```bash
# Generate SQL directly
python -c "
from src.excel_parser import ExcelParser
from src.sql_generator import SQLGenerator

parser = ExcelParser('templates/garmin_fitness_template.xlsx')
parser.parse()

generator = SQLGenerator(parser.areas, parser.categories, parser.attributes)
print(generator.generate_full_schema())
" > schema.sql
```

Then apply in Supabase SQL Editor.

### 6. Start Application

```bash
streamlit run streamlit_app.py
```

Application will open at `http://localhost:8501`

## 📊 Excel Template Format

### Areas Sheet

| uuid | name | icon | color | sort_order | description |
|------|------|------|-------|------------|-------------|
| uuid-v4 | Health | 🏥 | #4CAF50 | 1 | Daily health metrics |

### Categories Sheet

| uuid | area_uuid | parent_uuid | name | description | level | sort_order |
|------|-----------|-------------|------|-------------|-------|------------|
| uuid-v4 | area-uuid | NULL | Sleep | Sleep tracking | 1 | 1 |

### Attributes Sheet

| uuid | category_uuid | name | data_type | unit | is_required | default_value | validation_rules | sort_order |
|------|---------------|------|-----------|------|-------------|---------------|------------------|------------|
| uuid-v4 | cat-uuid | Total Sleep | number | hours | TRUE | NULL | {"min": 0, "max": 24} | 1 |

**Data Types:**
- `number` - Numeric values (integer or decimal)
- `text` - Text strings
- `datetime` - Date and time
- `boolean` - True/False
- `link` - URLs
- `image` - Image URLs (Supabase Storage)

## 🔧 Common Tasks

### Create New Template

```bash
# Edit the generator
nano src/generate_template.py

# Run generator
python src/generate_template.py

# Template created in templates/
```

### Export Current Structure

1. Open Streamlit app
2. Go to "Export Structure"
3. Enter your User ID
4. Click "Export to Excel"
5. Download and edit

### Update Structure

1. Export current structure (creates backup automatically)
2. Edit Excel file:
   - Add new rows (generate new UUIDs)
   - Update existing rows (keep same UUID)
   - Delete rows to remove items
3. Upload via "Upload Template"
4. Review changes preview
5. Click "Apply Changes"

### Generate UUIDs

```python
import uuid
print(uuid.uuid4())  # e.g., 550e8400-e29b-41d4-a716-446655440000
```

Or use online generator: [uuidgenerator.net](https://www.uuidgenerator.net/)

## 🔒 Security: Row Level Security

All tables use RLS to ensure users only access their own data:

```sql
-- Users can only view their own areas
CREATE POLICY "Users can view their own areas"
    ON areas FOR SELECT
    USING (user_id = auth.uid());
```

**Authentication Integration:**
- Currently using placeholder user_id
- TODO: Integrate with Supabase Auth
- Users will authenticate via email/password
- `auth.uid()` automatically returns logged-in user

## 📁 Database Schema

### Core Tables

- `templates` - Reusable structure definitions
- `areas` - Top-level organization
- `categories` - Hierarchical subcategories
- `attribute_definitions` - Metadata for what can be tracked
- `events` - Actual event records
- `event_attributes` - EAV storage for flexible data
- `event_attachments` - Files, images, links

### Relationships

```
templates (optional)
    ↓
areas (user-owned)
    ↓
categories (hierarchical, CASCADE delete)
    ↓
attribute_definitions (CASCADE delete)
    ↓
events (user-owned, CASCADE delete)
    ↓
event_attributes (CASCADE delete)
    ↓
event_attachments (CASCADE delete)
```

## 🎨 Example Use Cases

### Fitness Tracking (Garmin Integration)
- **Areas**: Health, Training
- **Categories**: Sleep, Daily Wellness, Cardio, Strength
- **Attributes**: Steps, HRV, Body Battery, Distance, HR

### Project Management
- **Areas**: Projects, Tasks, Resources
- **Categories**: Development, Design, Marketing
- **Attributes**: Hours, Status, Priority, Cost

### Finance Tracking
- **Areas**: Income, Expenses, Investments
- **Categories**: Salary, Groceries, Stocks
- **Attributes**: Amount, Currency, Date, Category

## 🐛 Troubleshooting

### "Connection failed" Error

```bash
# Check credentials
cat .streamlit/secrets.toml

# Test connection
python -c "
from supabase import create_client
import os

url = 'your-url'
key = 'your-key'
client = create_client(url, key)
print('Connection successful!')
"
```

### "Table does not exist" Error

→ Schema not applied. Follow "Generate and Apply Database Schema" steps.

### UUID Validation Errors

→ Ensure all UUIDs are valid v4 format. Use generator script or online tool.

### Changes Not Applying

1. Check Supabase Dashboard → Table Editor
2. Verify RLS policies allow your user
3. Check browser console for errors
4. Review backup files in `backups/`

## 🚧 Roadmap

- [ ] User authentication (Supabase Auth)
- [ ] Event entry interface
- [ ] Data visualization dashboard
- [ ] Bulk import/export (CSV)
- [ ] API endpoints
- [ ] Mobile app
- [ ] Garmin Connect integration
- [ ] Template marketplace

## 📝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/sladosa/events-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sladosa/events-tracker/discussions)
- **Email**: sladosa@example.com (replace with actual)

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Database by [Supabase](https://supabase.com)
- Inspired by flexible event tracking needs for fitness, projects, and life logging

---

**Made with ❤️ by the Events Tracker Team**
