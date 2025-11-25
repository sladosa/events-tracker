
## Code Development Guidelines

### Code Style

- Follow **PEP 8** for Python code
- Use **type hints** where applicable for function parameters and returns
- Add **docstrings** for all classes and public methods
- Use **f-strings** for string formatting
- Use **Pathlib** for file paths (where appropriate)
- Keep functions focused (single responsibility principle)
- Use meaningful variable names (avoid abbreviations)


### Naming Conventions

- **snake_case** for functions and variables
- **PascalCase** for classes
- **UPPER_CASE** for constants
- Descriptive names (avoid abbreviations unless standard)

**Examples:**
```python
# . Good
def calculate_event_duration(start_time, end_time):
    pass

class EventManager:
    pass

MAX_UPLOAD_SIZE = 10_000_000

# . Bad
def calc(s, e):
    pass

class evtMgr:
    pass

maxSize = 10000000
```

### Module Structure

Every module should follow this structure:

```python
"""
Module Name - Brief Description

Features:
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

Dependencies: streamlit, pandas, supabase

Last Modified: YYYY-MM-DD HH:MM UTC
"""

import streamlit as st
from typing import Optional, Dict, List
# . ... other imports

# . Constants
DEFAULT_PAGE_SIZE = 100
MAX_RETRIES = 3

def main_function(client, user_id: str) -> Optional[Dict]:
    """
    Main entry point for the module.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
        
    Returns:
        Dict with results or None on error
        
    Raises:
        ValueError: If user_id is invalid
    """
    try:
        # Implementation
        pass
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# . Helper functions below
def _helper_function(data: List) -> Dict:
    """Private helper function."""
    pass
```

### Documentation (.md files) numbering style

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
### Documentation

- Keep documentation (.md files) in numbering style described above
- Update "Last Modified" timestamp in generated programs and files when changing code (IMPORTANT)
- Include examples in docstrings where helpful
- Document complex algorithms or business logic
- Add inline comments for non-obvious code
## Performance Considerations

### Database Queries

**Optimization strategies:**
- Use `.select()` with specific columns when possible
- Use `.order()` for sorted results
- Use `.in_()` for batch lookups
- Avoid N+1 queries (use joins where possible)
- Limit result sets for large queries

**Example optimized query:**
```python
# . Good: Specific columns with join
events = client.table('events') \
    .select('id, event_date, category_id, categories(name)') \
    .eq('user_id', user_id) \
    .limit(100) \
    .execute()

# . Bad: Select all with N+1 queries
events = client.table('events').select('*').eq('user_id', user_id).execute()
for event in events.data:
    category = client.table('categories').select('*').eq('id', event['category_id']).execute()
```

### Memory Usage

**Typical loads:**
- DataFrame operations kept in memory
- Structure: ~300 bytes per row
- 1000 rows ≈ 300 KB (acceptable)
- Excel files: typically < 5 MB
- Large exports (10,000+ events): Use pagination or streaming

### Streamlit Performance

**Best practices:**
- Cache database clients with `@st.cache_resource`
- Use `st.spinner()` for user feedback during long operations
- Minimize re-runs with session state
- Use `st.rerun()` sparingly
- Lazy load heavy components (use tabs, expanders)

**Example caching:**
```python
@st.cache_resource
def get_supabase_client():
    """Cached Supabase client initialization."""
    return create_client(url, key)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_structure(_client, user_id):
    """Cached structure loading."""
    return fetch_areas_categories_attributes(_client, user_id)
```


## Useful Code Snippets

### Database Operations

**Query with RLS:**
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

**Join with EAV Pattern:**
```python
# . SELECT with JOIN - get events with attributes and definitions
events = client.table('events') \
    .select('*, event_attributes(*, attribute_definitions(*))') \
    .eq('user_id', user_id) \
    .eq('category_id', category_id) \
    .execute()
```

**Insert Event with Attributes:**
```python
# . INSERT event
new_event = {
    'user_id': user_id,
    'category_id': category_id,
    'event_date': '2025-11-20',
    'comment': 'Test'
}
result = client.table('events').insert(new_event).execute()
event_id = result.data[0]['id']

# . INSERT attributes (EAV)
for attr_def in attribute_definitions:
    attribute_data = {
        'event_id': event_id,
        'attribute_definition_id': attr_def['id'],
        'user_id': user_id,
        'value_number': form_data[attr_def['name']]  # or value_text, etc.
    }
    client.table('event_attributes').insert(attribute_data).execute()
```

**Update with RLS:**
```python
# . UPDATE event
client.table('events') \
    .update({'comment': 'Updated comment'}) \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

**Delete with CASCADE:**
```python
# . DELETE event (CASCADE deletes event_attributes automatically)
client.table('events') \
    .delete() \
    .eq('id', event_id) \
    .eq('user_id', user_id) \
    .execute()
```

### Streamlit UI Patterns

**Messages:**
```python
# . Success message
st.success("✅ Event saved successfully!")

# . Error message
st.error("❌ Failed to save event")

# . Warning message
st.warning("⚠️ This action cannot be undone")

# . Info message
st.info("ℹ️ Fill in all required fields")
```

**Spinner:**
```python
# . Show spinner during long operations
with st.spinner("Loading events..."):
    events = fetch_events(client, user_id)
```

**Form with Validation:**
```python
# . Streamlit form
with st.form("event_form"):
    date = st.date_input("Date", value=datetime.now())
    category = st.selectbox("Category", options)
    
    submitted = st.form_submit_button("Save Event")
    if submitted:
        if not category:
            st.error("Please select a category")
        else:
            save_event(date, category)
            st.success("Event saved!")
```

**Session State:**
```python
# . Initialize session state
if 'last_category' not in st.session_state:
    st.session_state.last_category = None

# . Use session state
st.session_state.last_category = selected_category
```

**Expanders:**
```python
# . Use expanders for optional details
with st.expander("Advanced Options", expanded=False):
    show_advanced_options()
```

### Error Handling

**Try-Catch Pattern:**
```python
try:
    result = client.table('events').insert(data).execute()
    st.success("✅ Event saved!")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    # Log error for debugging
    print(f"Error details: {str(e)}")
```

**Validation Pattern:**
```python
def validate_event_data(data):
    """Validate event data before insert."""
    errors = []
    
    if not data.get('event_date'):
        errors.append("Date is required")
    
    if not data.get('category_id'):
        errors.append("Category is required")
    
    # Check required attributes
    for attr in required_attributes:
        if not data.get(attr['name']):
            errors.append(f"{attr['name']} is required")
    
    return errors

# . Usage
errors = validate_event_data(form_data)
if errors:
    for error in errors:
        st.error(f"❌ {error}")
else:
    save_event(form_data)
```

---


### Error Handling

Always wrap database operations:

```python
try:
    result = client.table('events').insert(data).execute()
    st.success("✅ Event saved!")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    # Log error for debugging in production
    if DEBUG_MODE:
        print(f"Stack trace: {traceback.format_exc()}")
```

### RLS Requirements

**CRITICAL:** Every database query MUST include user_id:

```python
# . ✅ CORRECT
response = client.table('events') \
    .select('*') \
    .eq('user_id', user_id) \
    .execute()

# . ❌ WRONG - Will fail or return no data due to RLS
response = client.table('events').select('*').execute()
```

### Testing Approach

- **Test happy path** (valid data)
- **Test edge cases** (empty, null, invalid data)
- **Test RLS** (user isolation)
- **Test performance** (100+ records)
- **Verify error messages** are user-friendly
- **Test UI** (all buttons, forms, navigation)
