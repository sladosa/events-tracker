# 🎯 ŠTO SADA NAPRAVITI - Brzi Vodič

## ✅ Preuzimanje i Početak

Download-ali ste: **migration-package.zip**

Ovaj paket sadrži **KOMPLETAN** sistem za:
1. Migraciju vaše baze na hybrid pristup (UUID + imena)
2. Python kod za rename detection
3. Excel validaciju i processing
4. Primjer template i workflow

## 📝 JEDNOSTAVNI KORACI

### 1. BACKUP (5 minuta) ⚠️ OBAVEZNO!

```bash
# U vašem projektu:
git add .
git commit -m "Pre-migration backup"
git tag pre-migration-backup
```

**TAKOĐER:**
- Supabase Dashboard → Settings → Database → Download Backup

### 2. SQL MIGRACIJA (20 minuta)

Otvorite Supabase Dashboard → SQL Editor i pokrenite **PO REDU**:

#### a) Prvo (5 min):
```
Kopirajte SVE iz: sql/migration_step1_add_columns.sql
Paste u SQL Editor
Execute

✓ Dodaje slug i path kolone
✓ Kreira audit tablice
✓ Postavlja constrainte
```

#### b) Drugo (10 min):
```
Kopirajte SVE iz: sql/migration_step2_add_triggers.sql
Paste u SQL Editor
Execute

✓ Kreira trigger funkcije
✓ Postavlja auto-generiranje slugova
✓ Popunjava paths
```

#### c) Treće (5 min):
```
Kopirajte SVE iz: sql/migration_step3_stored_procedures.sql
Paste u SQL Editor
Execute

✓ Kreira stored procedures
✓ Postavlja permissions
```

**VAŽNO:** Nakon svake skripte, provjerite output - trebao bi pisati "Migration Step X completed successfully!"

### 3. PYTHON KOD (30 minuta)

```bash
# U vašem projektu direktoriju:

# Kopirajte nove module:
cp migration-package/src/rename_detector.py src/
cp migration-package/src/validators.py src/
cp migration-package/src/excel_parser_new.py src/

# Update dependencies:
pip install numpy==1.24.0
```

### 4. UPDATE STREAMLIT APP (Najvažnije!)

U vašem `streamlit_app.py`, **zamijenite** stari upload flow s novim.

**UMJESTO:**
```python
parser = ExcelParser(excel_path)  # Staro
success, errors, warnings = parser.parse()
```

**KORISTITE:**
```python
# 1. Validacija
from src.validators import validate_template
is_valid, report, error_file = validate_template(excel_path)
if not is_valid:
    st.error(report)
    return

# 2. Parse
from src.excel_parser_new import ExcelTemplateParser, load_from_database
parser = ExcelTemplateParser(excel_path)
new_areas, new_categories, new_attributes = parser.parse()

# 3. Load iz baze
old_areas, old_categories, old_attributes = load_from_database(supabase_client, user_id)

# 4. Rename detection
from src.rename_detector import RenameDetector
detector = RenameDetector(confidence_threshold=0.65)
matches = detector.match_objects(old_areas, new_areas)
operations = detector.generate_operations()

# 5. Primijeni promjene
result = supabase_client.rpc('update_template_from_excel', {
    'p_user_id': user_id,
    'p_template_data': operations
}).execute()
```

**POTPUNI PRIMJER** vidi u: `src/example_workflow.py`

### 5. TEST (20 minuta)

#### Test 1: Jednostavan Rename
```bash
1. Download trenutnu strukturu (može preko SQL query)
2. Promijenite jedno ime u Excel-u
3. Upload natrag
4. Verificirajte da je rename detektiran
```

#### Test 2: Verifikacija Podataka
```sql
-- Provjeri da li eventi nisu izgubljeni:
SELECT COUNT(*) FROM events WHERE category_id IS NULL;
-- Trebalo bi biti 0

-- Provjeri audit log:
SELECT * FROM name_change_history ORDER BY changed_at DESC LIMIT 5;
-- Trebao bi vidjeti rename operacije
```

## 🎨 NOVI EXCEL FORMAT

**Prije:**
```
uuid (ručno kreiran)                      | name
123e4567-e89b-12d3-a456-426614174000     | Running
```

**Poslije:**
```
area_id (ostavi prazno) | area_name
                        | Fitness
                        | Nutrition
```

**Primjer template:** `templates/template_example.xlsx`

## ❓ ŠTO AKO NEŠTO NE RADI?

### SQL Error?
```sql
-- Provjeri da li su skripte uspješno pokrenute:
SELECT COUNT(*) FROM areas WHERE slug IS NOT NULL;
SELECT COUNT(*) FROM categories WHERE path IS NOT NULL;

-- Ako nešto nije u redu, rollback:
-- Restore iz backupa
```

### Python Error?
```bash
# Provjeri dependencies:
pip install -r migration-package/requirements.txt

# Provjeri import paths:
python -c "from src.rename_detector import RenameDetector; print('OK')"
```

### Rename Detection ne radi?
```python
# Smanjite threshold za agresivnije matching:
detector = RenameDetector(confidence_threshold=0.50)
```

## 📚 GDJE NAĆI VIŠE INFO?

1. **MIGRATION_GUIDE.md** - KOMPLETNE step-by-step upute (15+ stranica)
2. **README.md** - Pregled paketa
3. **src/example_workflow.py** - Radni primjer kompletan workflow-a
4. **templates/template_example.xlsx** - Primjer novog Excel formata

## 🚨 NAJVAŽNIJE STVARI

### ✅ DA:
- Napravite backup prije bilo čega
- Pokrenite SQL skripte PO REDU
- Testirajte na development bazi prvo
- Provjerite svaki korak prije nastavka

### ❌ NE:
- Preskočiti backup
- Pokrenuti SQL skripte odjednom (mogu biti konflikti)
- Testirati direktno na production-u
- Očekivati da sve radi bez testiranja

## 🎯 OČEKIVANI REZULTAT

Nakon uspješne migracije:

✅ Excel template-i koriste **imena umjesto UUID-ova**
✅ Sistem **automatski detektira rename** operacije
✅ **Svi eventi** su još uvijek povezani
✅ **Audit log** prati sve promjene
✅ **Brži query-i** kroz ltree paths

## 📞 SLJEDEĆI KORACI

1. **Ekstraktirajte ZIP**
2. **Pročitajte README.md** (5 min)
3. **Napravite BACKUP** (5 min)
4. **Pokrenite SQL migracije** (20 min)
5. **Update Python kod** (30 min)
6. **Testirajte** (20 min)

**UKUPNO VRIJEME:** ~1.5 sata

---

## 💡 SAVJET

Započnite s čitanjem **MIGRATION_GUIDE.md** - tamo je SVE detaljno objašnjeno s primjerima, troubleshooting-om, i best practices-ima.

**Sretno s migracijom! 🚀**

Ako naiđete na bilo kakve probleme, reference MIGRATION_GUIDE.md ima troubleshooting sekciju koja pokriva većinu slučajeva.
