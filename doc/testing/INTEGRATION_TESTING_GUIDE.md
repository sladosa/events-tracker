# View Data Export/Import - Integration Guide

## 📦 Kreirani Fileovi

### 1. **view_data_export.py** 
Modul za export evenata u Excel sa filterima i color-coding.

**Lokacija:** `src/view_data_export.py`

**Funkcije:**
- `render_view_data_export(client, user_id)` - Main UI function
- `get_events_with_data()` - Fetch events with filters
- `create_excel_export()` - Generate Excel with color coding
- Filter by category, date range, attributes
- Export to Excel with PINK (read-only) and BLUE (editable) columns

---

### 2. **view_data_import.py**
Modul za import editiranog Excel-a sa change detection.

**Lokacija:** `src/view_data_import.py`

**Funkcije:**
- `render_view_data_import(client, user_id)` - Main UI function
- `parse_uploaded_excel()` - Parse Excel file
- `detect_changes()` - Detect what changed (diff)
- `apply_changes()` - Apply changes to database
- Upload → Parse → Diff → Confirm → Apply workflow

---

### 3. **streamlit_app.py** (Updated)
Main app sa integriranim View Data modulima.

**Novi menu items:**
- 🔍 View Data - Export
- 📤 View Data - Import

---

## 🔧 Integracija u Postojeći Projekt

### Korak 1: Copy Files

```bash
# Copy new modules to src/ folder
cp view_data_export.py your_project/src/
cp view_data_import.py your_project/src/

# Replace main app (or manually integrate)
cp streamlit_app.py your_project/streamlit_app.py
```

### Korak 2: Verify Imports

U `streamlit_app.py` provjeri da su importi OK:

```python
from src import view_data_export
from src import view_data_import
```

### Korak 3: Verify Dependencies

Potrebne biblioteke (dodaj u `requirements.txt` ako nemaš):

```
streamlit
supabase
pandas
openpyxl
```

---

## 🧪 Testiranje

### Test #1: View Data Export (5 min)

1. **Pokreni app:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Login sa svojim credentials**

3. **Navigate:** Sidebar → "🔍 View Data - Export"

4. **Test Export:**
   - Odaberi kategoriju (ili "All Categories")
   - Odaberi date range
   - Klikni "📥 Export to Excel"
   - Download file

5. **Provjeri Excel:**
   - Otvori file u Excel-u
   - Sheet 1: "Events" - vidi li podatke?
   - Sheet 2: "Instructions" - vidi li upute?
   - Color coding:
     * **PINK columns** = Event_ID, Category_Path, Date (READ-ONLY)
     * **BLUE columns** = Attribute values, Comment (EDITABLE)
   - Freeze panes: Header + prva 3 kolona

**Očekivani rezultat:** ✅ Excel file sa podacima, color-coded, frozen panes

---

### Test #2: Edit Excel File (2 min)

1. **U downloadanom Excel-u:**
   - Edit neki **BLUE** column (npr. promijeni vrijednost atributa)
   - Edit **Comment** column (dodaj/promijeni komentar)
   - **NE DIRAJ PINK** columns!

2. **Save Excel file**

**Očekivani rezultat:** ✅ Editirani Excel file spremljen

---

### Test #3: View Data Import (5 min)

1. **Navigate:** Sidebar → "📤 View Data - Import"

2. **Upload editirani Excel:**
   - Klikni "Upload Edited Excel File"
   - Odaberi tvoj editirani file

3. **Provjeri Parsing:**
   - Vidiš li "✅ Excel file parsed: X events found"?
   - Expand "Preview Uploaded Data" - vidi li podatke?

4. **Provjeri Change Detection:**
   - Vidiš li "📝 Changes Detected: X events"?
   - Expand "View Detailed Changes"
   - Vidiš li DIFF (Old Value → New Value)?

5. **Apply Changes:**
   - Klikni "🚀 Confirm & Apply Changes"
   - Vidiš li success message?
   - Balloons? 🎉

6. **Verify u bazi:**
   - Navigate natrag na "View Data - Export"
   - Export opet iste events
   - Provjeri da su vrijednosti updatane

**Očekivani rezultat:** ✅ Changes applied to database, data updated

---

## 🐛 Potencijalni Problemi i Rješenja

### Problem 1: Import greška "Module not found"

**Rješenje:**
```bash
# Provjeri da su fileovi u src/ folderu
ls src/view_data_export.py
ls src/view_data_import.py

# Provjeri __init__.py u src/
# Dodaj ako ne postoji:
touch src/__init__.py
```

### Problem 2: Excel parsing error

**Rješenje:**
- Provjeri da Excel ima "Events" sheet
- Provjeri da header columns nisu promijenjeni
- Provjeri da Event_ID column postoji i ima vrijednosti

### Problem 3: Change detection ne radi

**Rješenje:**
- Provjeri da si editirao **BLUE** columns, ne PINK
- Provjeri da su vrijednosti zaista promijenjene
- Empty cell = None = brisanje vrijednosti

### Problem 4: Apply changes fails

**Rješenje:**
- Provjeri error messages u "Error Details" expander
- Provjeri da su numeric fields zaista numerički (npr. "7.5" ne "seven")
- Provjeri da attribute još postoji u kategoriji

---

## 📊 Workflow Diagram

```
1. VIEW DATA EXPORT
   ├─ Select filters (category, date, attributes)
   ├─ Click "Export to Excel"
   ├─ Download Excel file
   └─ File has:
      ├─ Sheet "Events" (color-coded data)
      └─ Sheet "Instructions" (help)

2. EDIT IN EXCEL
   ├─ Open Excel file
   ├─ Edit BLUE columns only
   ├─ Save file
   └─ DO NOT edit PINK columns!

3. VIEW DATA IMPORT
   ├─ Upload edited Excel
   ├─ System parses file
   ├─ System detects changes (DIFF)
   ├─ Review changes (Old → New)
   ├─ Confirm & Apply
   └─ Changes saved to database ✅
```

---

## ✅ Checklist za Testiranje

- [ ] App se pokreće bez errora
- [ ] View Data Export stranica se učitava
- [ ] Export to Excel radi i downloaduje file
- [ ] Excel ima 2 sheets: "Events" i "Instructions"
- [ ] Events sheet ima PINK i BLUE color coding
- [ ] Mogao editirati BLUE columns u Excel-u
- [ ] View Data Import stranica se učitava
- [ ] Upload Excel file radi (parsing OK)
- [ ] Change detection radi (vidi DIFF)
- [ ] Apply changes radi (success message)
- [ ] Podatci su updatani u bazi (verify sa re-export)

---

## 🎯 Sljedeći Koraci

Ako sve radi:
1. ✅ Test sa većim datasetom
2. ✅ Test edge cases (empty values, invalid data)
3. ✅ Test sa različitim kategorijama
4. ✅ Test permissions (drugi user ne može vidjeti tvoje events)

Ako nešto ne radi:
1. ❌ Javi mi točan error message
2. ❌ Javi mi koji korak ne radi
3. ❌ Screenshot ako može
4. ❌ Nastavljamo debug zajedno!

---

## 📞 Feedback

Testiraj i javi:
1. **Što radi? ✅**
2. **Što ne radi? ❌**
3. **Što bi trebalo dodati/promijeniti? 💡**

Happy Testing! 🚀
