# 🎯 View Data Export/Import - Quick Reference

## 📥 Files to Copy

```
src/view_data_export.py    → Export module
src/view_data_import.py    → Import module
streamlit_app.py           → Main app (updated)
```

---

## 🚀 Quick Start (3 Steps)

### 1. Copy Files
```bash
cp view_data_export.py your_project/src/
cp view_data_import.py your_project/src/
cp streamlit_app.py your_project/
```

### 2. Run App
```bash
streamlit run streamlit_app.py
```

### 3. Test Workflow
```
Export → Edit → Import → Confirm
```

---

## 🎨 Color Coding

| Color | Columns | Action |
|-------|---------|--------|
| 🟪 PINK | Event_ID, Category_Path, Date | **READ-ONLY** - Don't edit! |
| 🔵 BLUE | Attribute values, Comment | **EDITABLE** - Edit these! |

---

## ✅ Test Checklist (Quick)

**Export Test:**
- [ ] Navigate to "View Data - Export"
- [ ] Select filters → Export → Download
- [ ] Open Excel → See PINK and BLUE columns?

**Edit Test:**
- [ ] Edit some BLUE column values
- [ ] Save Excel file

**Import Test:**
- [ ] Navigate to "View Data - Import"
- [ ] Upload file → See DIFF?
- [ ] Confirm & Apply → Success? 🎉

---

## 🐛 Quick Troubleshooting

**Problem:** Module not found
```bash
# Check files are in src/
ls src/view_data_*.py
```

**Problem:** Excel parsing error
- Check "Events" sheet exists
- Check Event_ID column has values
- Check you didn't edit PINK columns

**Problem:** Changes not detected
- Edit BLUE columns only
- Save Excel file properly
- Check values actually changed

---

## 📞 Report Issues

When reporting bugs, include:
1. Which step failed?
2. Error message (exact text)
3. Screenshot (if helpful)

---

**Happy Testing!** 🚀
