# Complete Setup Guide for Events Tracker

This guide walks you through setting up the Events Tracker system from scratch.

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- GitHub account (optional, for version control)
- Supabase account (free tier works)

## Part 1: Local Setup

### Step 1: Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `events-tracker`
3. Description: "Flexible event tracking system"
4. Choose Public or Private
5. ✅ Add a README file
6. Click "Create repository"

### Step 2: Clone and Setup Locally

```bash
# Clone your new repository
git clone https://github.com/YOUR_USERNAME/events-tracker.git
cd events-tracker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# You should see (venv) in your prompt
```

### Step 3: Copy Project Files

Copy all files from the generated project into your repository:

```
events-tracker/
├── streamlit_app.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── .streamlit/
│   └── secrets.toml.example
├── src/
│   ├── generate_template.py
│   ├── excel_parser.py
│   ├── sql_generator.py
│   ├── supabase_client.py
│   └── reverse_engineer.py
└── templates/
    └── garmin_fitness_template.xlsx
```

### Step 4: Install Dependencies

```bash
# Make sure you're in the project directory with venv activated
pip install -r requirements.txt

# This will install:
# - streamlit (web framework)
# - supabase (database client)
# - pandas (data manipulation)
# - openpyxl (Excel handling)
# - python-dotenv (environment variables)
# - pydantic (data validation)
```

### Step 5: Commit Initial Files

```bash
# Add all files
git add .

# Commit
git commit -m "Initial project setup"

# Push to GitHub
git push origin main
```

## Part 2: Supabase Setup

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project" → Sign in with GitHub
3. Click "New Project" button
4. Fill in project details:
   - **Organization**: Create new or use existing
   - **Project Name**: `events-tracker-prod` (or your choice)
   - **Database Password**: Click "Generate password" and SAVE IT!
   - **Region**: Choose closest (e.g., `Europe (Frankfurt)` for EU)
   - **Pricing Plan**: Free (sufficient for testing)
5. Click "Create new project"
6. Wait 2-3 minutes for provisioning

### Step 2: Get API Credentials

1. In your project dashboard, click "Settings" (gear icon, bottom left)
2. Click "API" in settings menu
3. Find and copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: Long string starting with `eyJ...`
4. **Save these somewhere safe!** You'll need them in Step 3.

### Step 3: Configure Local Secrets

```bash
# Create secrets file
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit with your values
nano .streamlit/secrets.toml
# Or use any text editor
```

Replace the placeholders:

```toml
SUPABASE_URL = "https://your-actual-project-id.supabase.co"
SUPABASE_KEY = "your-actual-anon-key-eyJhbGc..."
```

Save and close.

**Important**: This file is in `.gitignore` and will NOT be committed to GitHub!

### Step 4: Test Connection

```bash
# Test Supabase connection
python -c "
from supabase import create_client

# Read from secrets (manual for testing)
url = 'https://your-project-id.supabase.co'
key = 'your-anon-key'

client = create_client(url, key)
print('✅ Connection successful!')
"
```

If you see "✅ Connection successful!" - you're good!

If errors, double-check:
- URL format is correct (https://...)
- Anon key is complete (very long string)
- No extra spaces in secrets.toml

## Part 3: Database Schema Setup

### Step 1: Generate SQL

```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Browser should open automatically at localhost:8501
# If not, manually open: http://localhost:8501
```

### Step 2: Generate SQL via UI

1. In Streamlit app, click "📄 Generate SQL" in sidebar
2. Upload `templates/garmin_fitness_template.xlsx`
3. Wait for validation to complete
4. Click "⬇️ Download SQL File"
5. Save as `schema.sql` to your project folder

### Step 3: Apply SQL in Supabase

1. Go to your Supabase Dashboard
2. Click "SQL Editor" in left sidebar
3. Click "New query"
4. Open your `schema.sql` file in a text editor
5. Copy ALL the SQL
6. Paste into Supabase SQL Editor
7. Click "Run" (bottom right)
8. Wait for completion (should take ~5 seconds)
9. You should see "Success. No rows returned" - this is correct!

### Step 4: Verify Tables Created

1. Click "Table Editor" in left sidebar
2. You should see these tables:
   - `templates`
   - `areas`
   - `categories`
   - `attribute_definitions`
   - `events`
   - `event_attributes`
   - `event_attachments`

3. Click on `areas` table
4. You should see 2 rows:
   - Health
   - Training

**If you see these, SUCCESS!** 🎉

## Part 4: First Run

### Step 1: Test in Streamlit

1. Make sure app is still running (`streamlit run streamlit_app.py`)
2. Go to sidebar → "📤 Upload Template"
3. You should see:
   - ✅ Connection Status: "Connection successful"
   - No errors

### Step 2: Test Export

1. In sidebar, click "📥 Export Structure"
2. User ID: use `00000000-0000-0000-0000-000000000000` (test user)
3. Click "📥 Export to Excel"
4. You should see:
   ```
   Exported successfully:
     - 2 Areas
     - 5 Categories
     - 15 Attributes
   ```
5. Download the file
6. Open in Excel to verify structure

### Step 3: Test Upload/Modify

1. Open downloaded Excel file
2. Make a small change (e.g., rename "Health" to "Wellness")
3. Save the file
4. Go to "📤 Upload Template" in app
5. Upload your modified file
6. Review changes preview
7. Click "🚀 Apply Changes"
8. Verify change in Supabase Table Editor

## Part 5: Troubleshooting

### Issue: "Module not found" errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Connection failed"

Check these in order:
1. Secrets file exists: `.streamlit/secrets.toml`
2. Values are correct (no quotes inside quotes)
3. Project is not paused (check Supabase dashboard)
4. Internet connection is working

```bash
# Test credentials manually
python -c "
from supabase import create_client
import toml

secrets = toml.load('.streamlit/secrets.toml')
client = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_KEY'])
print('✅ Connection works!')
"
```

### Issue: "Table does not exist"

SQL schema wasn't applied correctly:

1. Go to Supabase → SQL Editor
2. Re-run the schema.sql file
3. Check for any error messages
4. If errors, copy error message and check documentation

### Issue: UUID validation errors in Excel

UUIDs must be valid v4 format. Generate new ones:

```python
import uuid
for i in range(5):
    print(uuid.uuid4())
```

Or use: [uuidgenerator.net](https://www.uuidgenerator.net/)

### Issue: Port 8501 already in use

```bash
# Kill existing Streamlit process
pkill -f streamlit

# Or use different port
streamlit run streamlit_app.py --server.port 8502
```

## Part 6: Next Steps

### Add User Authentication

Currently using test user ID. To add real auth:

1. Supabase Dashboard → Authentication → Providers
2. Enable Email provider
3. Create test user
4. Modify streamlit_app.py to use Supabase Auth
5. Replace placeholder user_id with `auth.uid()`

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Add secrets in deployment settings
5. Deploy!

### Create Custom Templates

1. Copy `src/generate_template.py`
2. Modify Areas, Categories, Attributes
3. Run script to generate new template
4. Upload via UI

### Add Event Entry Interface

(Coming soon - will be added to roadmap)

## 📞 Getting Help

If stuck:

1. Check [README.md](README.md) for common issues
2. Review code comments (everything is documented)
3. Open GitHub Issue with:
   - Error message
   - Steps to reproduce
   - What you've tried
4. Check Supabase logs: Dashboard → Logs

## ✅ Setup Complete Checklist

- [ ] GitHub repository created
- [ ] Local project cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Supabase project created
- [ ] API credentials saved
- [ ] `.streamlit/secrets.toml` configured
- [ ] Connection test passed
- [ ] SQL schema generated
- [ ] SQL applied in Supabase
- [ ] Tables visible in Table Editor
- [ ] Streamlit app runs locally
- [ ] Export test successful
- [ ] Upload test successful

If all checked ✅ → **You're ready to start tracking!** 🎉

---

**Questions? Improvements?** Open an issue or PR on GitHub!
