# Cleanup Recommendations for Events Tracker

This document lists files and directories that can be safely removed from the repository to reduce clutter and maintain only actively used code.

## ✅ Recommended for Immediate Deletion

### 1. **Deprecated Python Modules**

**`src/structure_viewer.py`**
- Status: Explicitly marked as DEPRECATED in code header
- Reason: "⚠️ DEPRECATED: This module will be removed in next version. All functionality moved to Interactive Structure Viewer."
- Replacement: `interactive_structure_viewer.py`
- Action: **DELETE**

**`src/view_data_export.py`**
- Status: Functionality fully integrated elsewhere
- Reason: Export functionality now in `show_events.py` and `excel_events_io.py`
- Users access via: "Export to Excel" button in Show Events module
- Action: **DELETE**

**`src/view_data_import.py`**
- Status: Functionality fully integrated elsewhere
- Reason: Import functionality now in `show_events.py` and `excel_events_io.py`
- Users access via: "Import from Excel" button in Show Events module
- Action: **DELETE**

### 2. **Outdated Documentation**

**`Complete auth setup.txt`**
- Status: Likely outdated
- Reason: Authentication is well-documented in code comments and new README
- Action: **REVIEW** → Move any unique info to README → **DELETE**

### 3. **Development-Only Files**

**`requirements-dev.txt`**
- Status: Development dependencies
- Reason: Not needed for deployment, only for development environment
- Action: **DELETE** if not actively developing

**`Code_guidelines.md`**
- Status: May be redundant
- Reason: If coding standards are clear in code and README, this may be unnecessary
- Action: **REVIEW** → Merge with README if valuable → **DELETE**

## ⚠️ Conditional Deletion (Verify First)

### 1. **Potentially Obsolete Module**

**`src/excel_parser.py`**
- Status: Unclear if still used
- Reason: `excel_parser_new.py` exists and may be replacement
- Difference: 
  - `excel_parser.py` - UUID-based identifiers
  - `excel_parser_new.py` - Name-based identifiers (newer approach)
- Action: 
  1. Search codebase for `from src.excel_parser import` or `import excel_parser`
  2. If no imports found → **DELETE**
  3. If imports exist → Verify if can be replaced with `excel_parser_new.py`

**Command to check:**
```bash
grep -r "from.*excel_parser import\|import excel_parser" --include="*.py" src/ streamlit_app.py
```

### 2. **Test Directory**

**`tests/` directory**
- Status: Contains only `test_state_machine.py`
- Reason: If tests aren't actively maintained or run in CI/CD
- Action:
  1. Check if tests are passing: `python -m pytest tests/`
  2. If tests fail or aren't used → **DELETE**
  3. If actively testing → **KEEP**

## 📝 Keep for Active Use

### Essential Development Tools

**`src/generate_template.py`**
- **KEEP** - Useful for generating sample structures during development
- Used for creating test/demo data

**`src/sql_generator.py`**
- **KEEP** - Useful if schema needs to be regenerated
- Important for database schema updates

**`src/reverse_engineer.py`**
- **KEEP** - Core functionality for exporting structure to Excel
- Actively used by Interactive Structure Viewer

## 📊 Summary

### Immediate Actions (High Confidence)
```
DELETE: src/structure_viewer.py
DELETE: src/view_data_export.py
DELETE: src/view_data_import.py
```

### Review Then Delete
```
REVIEW → DELETE: Complete auth setup.txt
REVIEW → DELETE: Code_guidelines.md
```

### Conditional (Verify First)
```
VERIFY → DELETE: src/excel_parser.py (check for imports)
VERIFY → DELETE: requirements-dev.txt (if not developing)
VERIFY → DELETE: tests/ (if not used)
```

### Total Potential Reduction
- **3 Python modules** (structure_viewer.py, view_data_export.py, view_data_import.py)
- **2-3 documentation files** (Complete auth setup.txt, Code_guidelines.md)
- **1-2 additional files** (requirements-dev.txt, tests/)
- **Estimated cleanup:** 6-8 files/directories

## 🔍 How to Verify Before Deletion

1. **Check for imports:**
```bash
cd events-tracker-main
grep -r "structure_viewer\|view_data_export\|view_data_import" --include="*.py" .
```

2. **Check file usage history:**
```bash
git log --follow --oneline <filename>
```

3. **Test after deletion:**
```bash
# Remove file
git rm src/structure_viewer.py

# Run app
streamlit run streamlit_app.py

# Verify no errors
```

## ✅ Post-Cleanup Checklist

After removing files:
- [ ] Update `.gitignore` if needed
- [ ] Run full app test (all modules work)
- [ ] Update README if any references to deleted files
- [ ] Commit changes with clear message: "refactor: remove deprecated modules"

---

**Recommendation:** Start with the 3 deprecated Python modules (structure_viewer, view_data_export, view_data_import) as these are safest to remove.
