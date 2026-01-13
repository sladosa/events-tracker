"""
Events Tracker - Main Application
==================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-01-13 15:10 UTC
Python: 3.11
Version: 2.2.6 - UX Improvements

Description:
Main Streamlit application with authentication and multiple pages.
Core modules: Interactive Structure Viewer (main hub), Add Activity,
Show Events (with integrated Excel Export/Import).

NEW in v2.2.6:
- 🎯 MAJOR UX IMPROVEMENTS:
  - ✅ UI Sort: Parent-child events properly grouped (Cardio always above Running)
  - ✅ Export Sort: Respects UI sort order (newest/oldest first)
  - ✅ Export Structure: Session-based merging (cleaner Excel output)
    • Events with same timestamp merge into ONE row (leaf event + all attributes)
    • Example: 11 rows (Cardio + Running separate) → 6 rows (Running with merged attrs)
    • Only leaf events exported, but with parent attributes populated
    • Dramatically cleaner export format! 🎉

PREVIOUS v2.2.5:
- 🐛 CRITICAL BUGFIX V2.5.4: UPDATE path multi-level support
  - ✅ UPDATE existing event + populate parent attrs → creates parent events
  - ✅ Example: Update "Running" + add Cardio data → creates Cardio event
  - ✅ Parent event shares SAME session_start timestamp
  - ✅ Full multi-level workflow now works for BOTH CREATE and UPDATE
  - ✅ Previously: UPDATE ignored parent attributes (only modified child)

PREVIOUS v2.2.4:
- 🐛 CRITICAL BUGFIX V2.5.3: session_start default and multi-level import
  - ✅ session_start now properly defaults to 09:00 (not NULL)
  - ✅ Empty time field correctly creates 09:00 timestamp
  - ✅ One Excel row can create MULTIPLE events (hierarchy levels)
  - ✅ Events with BAREM 1 populated attribute get created
  - ✅ All events from same row share SAME session_start timestamp
  - ✅ Enables true activity/session grouping by timestamp
- 🧹 UI CLEANUP: Export state properly cleared after actions
  - ✅ Export UI removed after Edit/Delete/Import/Filter changes
  - ✅ No more stale "Export ready" messages
- ✨ NEW: Sort order selection in Show Events
  - ✅ User can choose: Newest first ⬇️ or Oldest first ⬆️
  - ✅ Useful for viewing activity sessions chronologically

PREVIOUS v2.2.3.1:
- 🔧 HOTFIX: Change Password now visible in sidebar
  - Fixed: streamlit_app.py now calls auth_manager.show_user_info_sidebar()
  - Users can now access Change Password expander in User section
  - Previously was missing due to direct sidebar rendering

PREVIOUS v2.2.3:
- 🐛 CRITICAL BUGFIX V2.5.3: TIME import now works correctly
  - ✅ Default "09:00" no longer becomes NULL
  - ✅ All time values properly stored in database
  - ✅ Both CREATE and UPDATE paths fixed
- 🛡️ SECURITY FIX: Removed Forgot Password feature (security vulnerability)
  - Prevented arbitrary email reset attempts
  - Users can change password when logged in (secure alternative)

PREVIOUS v2.2.2:
- 🐛 CRITICAL FIXES V2.5.2:
  - ✅ Parent attributes NOW ACTUALLY BLUE (fixed missing field)
  - ✅ Hierarchical sort PERFECT (matches Structure Viewer exactly)
  - ✅ All Categories export: proper tree order maintained

PREVIOUS v2.2.1:
- 🐛 BUGFIXES V2.5.1: Critical fixes for Excel Export/Import
  - ✅ Filter now works correctly (only selected branch exported)
  - ✅ Parent attributes now BLUE (not orange) for child events  
  - ✅ Hierarchical sorting fixed (no branch mixing)

PREVIOUS v2.2.0:
- 📊 EXCEL EXPORT/IMPORT V2.5.0: Major improvements
  - ⏰ TIME column added (session_start, default 09:00)
  - 🌳 Parent category attributes included (e.g., Cardio attrs for Running events)
  - 🏷️ Clear attribute names with "(Category)" suffix in headers
  - 📈 Hierarchical sorting (parents before children)
  - ✅ All inherited attributes are editable (blue)
- 🎨 Improved Excel format clarity and consistency

CHANGELOG:
- v2.2.6: UX improvements (UI sort, export sort, session merging)
- v2.2.5: UPDATE multi-level fix (parent events created from UPDATE rows)
- v2.2.4: Multi-level import, session_start fix, UI cleanup, sort order
- v2.2.3.1: HOTFIX - Change Password visible in sidebar
- v2.2.3: TIME import fix + Forgot Password removed
- v2.2.2: Parent attributes BLUE + hierarchical sort fix
- v2.2.1: Filter fix + parent attributes colors
- v2.2.0: TIME column + parent category attributes
- v2.1.3: HOTFIX - Text input state issue (CONFIRM/DELETE)
- v2.1.2: Last Area deletion prompt (user control)
- v2.1.1: HOTFIX - Fixed time import namespace conflict
- v2.1.0: Bootstrap system for empty database UX
- v2.0.0: Unified Excel Export/Import, removed obsolete pages
- v1.9.0: Add Activity Workflow + Show Events Table View
- v1.8.0: Show Events + Remove Add Event
- v1.7.0: Add Activity module (mobile-optimized)

Modules:
- auth: User authentication
- interactive_structure_viewer: Excel-like editing interface (main hub)
- add_activity: Mobile-optimized activity entry with shortcuts
- show_events: View, edit, delete events + Excel Export/Import
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Import local modules
from src.auth import AuthManager
from src import supabase_client
from src.interactive_structure_viewer import render_interactive_structure_viewer
from src.add_activity import render_add_activity
from src.show_events import render_show_events


# Page configuration
st.set_page_config(
    page_title="Events Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()


@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Missing Supabase credentials. Please check your secrets.")
        st.stop()
    
    return supabase_client.SupabaseManager(url, key)


def main():
    """Main application logic"""
    
    # Initialize Supabase
    supabase = init_supabase()
    
    # Initialize AuthManager
    auth_manager = AuthManager(supabase.client)
    
    # Check authentication
    if not auth_manager.is_authenticated():
        auth_manager.show_login_page()
        return
    
    # Get user info
    user_id = auth_manager.get_user_id()
    user_email = auth_manager.get_user_email()
    
    # Sidebar navigation
    st.sidebar.title("🗂️ Events Tracker")
    st.sidebar.markdown("---")
    
    # Navigation menu
    page = st.sidebar.radio(
        "Navigation",
        [
            "📋 Interactive Structure Viewer",
            "🏋️ Add Activity",
            "📊 Show Events",
            "ℹ️ Help"
        ],
        label_visibility="collapsed"
    )
    
    
    # User info with Change Password
    auth_manager.show_user_info_sidebar()
    
    # Connection status
    with st.sidebar.expander("🔌 Connection Status", expanded=False):
        success, message = supabase.test_connection()
        if success:
            st.success("✅ Connected to Supabase")
        else:
            st.error(f"❌ {message}")
    
    # Main content area styling
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Route to appropriate page
    if page == "📋 Interactive Structure Viewer":
        render_interactive_structure_viewer(supabase.client, user_id)
    
    elif page == "🏋️ Add Activity":
        render_add_activity(supabase.client, user_id)
    
    elif page == "📊 Show Events":
        render_show_events(supabase.client, user_id)
    
    elif page == "ℹ️ Help":
        render_help_page()


def render_help_page():
    """Render the help page with basic application concepts only"""
    st.title("ℹ️ Help & Documentation")
    
    st.markdown("""
    ## 📚 Events Tracker - Basic Concepts
    
    ### 🎯 What is Events Tracker?
    
    Events Tracker helps you organize and track events using a **hierarchical structure**:
    
    - **Areas** → Top-level organization (e.g., Health, Work, Finance)
    - **Categories** → Specific event types (e.g., Sleep, Exercise, Meetings)  
    - **Attributes** → Data fields you want to track (e.g., Duration, Amount, Quality)
    
    This flexible structure allows you to:
    - Track any type of event (health, work, finance, personal, etc.)
    - Define custom attributes for each category
    - Maintain relationships and hierarchies
    - Export and analyze your data
    
    ---
    
    ### 📊 Core Components
    
    **1. Structure Management**
    - Define your hierarchical structure (Areas → Categories → Attributes)
    - Edit structure directly or via Excel templates
    - Add/modify/delete items with validation
    
    **2. Event Entry**
    - **Add Activity**: Mobile-optimized activity entry with shortcuts
    - **Show Events > Import**: Import events from Excel
    - Link events to categories with automatic attribute capture
    
    **3. Data Management**
    - **Show Events**: View, edit, and delete your events
    - **Export to Excel**: Download filtered events for editing
    - **Import from Excel**: Create new or update existing events
    - Filter and search capabilities
    
    ---
    
    ### 🗺️ Application Navigation
    
    **Interactive Structure Viewer** 🌟
    - **Main hub** for structure management
    - Two modes: Read-Only (view/export) and Edit (modify/upload)
    - Detailed help available within the page
    
    **Add Activity** 🏋️
    - Mobile-optimized event entry
    - Filter by Area → Category drill-down
    - Save shortcuts for frequently used categories
    - Photo attachments support
    
    **Show Events** 📊
    - View all your events with filters
    - Edit event details and attributes
    - Delete events with confirmation
    - **Export**: Download filtered events to Excel
    - **Import**: Upload Excel to create/update events
    - Color-coded Excel: PINK (read-only) / BLUE (editable)
    
    ---
    
    ### 💡 Getting Started
    
    **New to Events Tracker?**
    
    1. **Define your structure** using Interactive Structure Viewer
       - Start with a few Areas (e.g., "Health", "Work")
       - Add Categories under each Area
       - Define Attributes for each Category
    
    2. **Add some events**
       - Use "Add Activity" for quick entry
       - Or use "Show Events > Import" for multiple events from Excel
    
    3. **Review and manage your data**
       - Use "Show Events" to view, edit, export, and import
    
    ---
    
    ### 🔧 Data Types
    
    When defining attributes, you can choose from:
    
    - **number** - Numeric values (e.g., duration, amount, quantity)
    - **text** - Free text (e.g., notes, descriptions)
    - **datetime** - Date and time values
    - **boolean** - Yes/No or True/False
    - **link** - URLs and web links
    - **image** - Image file paths or URLs
    
    ---
    
    ### 🎨 Color Coding Convention
    
    Throughout the application, you'll see color-coded columns:
    
    - 🟪 **PINK columns** = AUTO-CALCULATED (read-only)
      - System-generated values
      - Don't edit these manually
    
    - 🔵 **BLUE columns** = EDITABLE
      - Your data and properties
      - Safe to modify
    
    ---
    
    
    ### 📥📤 Excel Import/Export Best Practices
    
    **Understanding the Excel Format:**
    
    When you export events, you get an Excel file with TWO main sections:
    
    1. **ATTRIBUTE LEGEND** (top) - Defines column mapping
       - Shows which Excel column (J, K, L...) contains which attribute
       - Example: "Col K | Fitness | Cardio > Running | duration"
       - 🎯 **This is the SOURCE OF TRUTH for import!**
    
    2. **EVENT DATA** (bottom) - Your actual event data
       - Contains events with their dates, comments, and attributes
       - Column headers match attributes from your structure
    
    ---
    
    **✅ Editing Excel - CORRECT Way:**
    
    **Option 1: Delete Attributes by Removing Legend Rows**
    ```
    1. Open ATTRIBUTE LEGEND section
    2. DELETE entire ROW for unwanted attribute
    3. Save Excel
    4. Import → Attribute is ignored ✅
    ```
    
    **Option 2: Delete Columns and Update Legend**
    ```
    1. DELETE unwanted columns from EVENT DATA
    2. Excel automatically shifts remaining columns left
    3. UPDATE the 'Col' letters in ATTRIBUTE LEGEND to match new positions
    4. Save Excel
    5. Import → Works perfectly! ✅
    ```
    
    **Example:**
    - Original: Col K = duration, Col L = pace, Col M = type
    - You delete Col K (duration)
    - Excel shifts: L→K, M→L
    - Update Legend: Change "Col L | pace" to "Col K | pace"
    - Import succeeds with correct mapping!
    
    ---
    
    **❌ Common Mistake:**
    
    ❌ **DON'T:** Delete columns WITHOUT updating Legend
    - Excel shifts columns but Legend still shows old positions
    - Import will be REJECTED with error message
    - You'll see: "Column headers don't match ATTRIBUTE LEGEND!"
    
    ---
    
    **🔧 Fixing Mismatch Errors:**
    
    If you see "Cannot import: Column headers don't match ATTRIBUTE LEGEND":
    
    1. Open the Excel file
    2. Look at ATTRIBUTE LEGEND section
    3. For each mismatched column, either:
       - **UPDATE** the 'Col' letter to match current position, OR
       - **DELETE** the entire legend row if you don't want that attribute
    4. Save and import again
    
    ---
    
    **💡 Key Principles:**
    
    ✅ **ATTRIBUTE LEGEND = SOURCE OF TRUTH**
    - Import uses Legend to know which column contains which attribute
    - Always keep Legend synchronized with your EVENT DATA columns
    
    ✅ **You CAN delete columns** - just update Legend accordingly
    
    ✅ **You CAN delete legend rows** - import will ignore those attributes
    
    ✅ **Maximum flexibility** - organize your Excel however you want, as long as Legend is correct!
    
    ---
    
    ### ⚠️ Important Notes
    
    **Data Safety:**
    - Always review changes before confirming
    - Download backups before major structural changes
    - Check validation messages carefully
    - Use CONFIRM dialogs for destructive operations
    
    **Best Practices:**
    - Start small - add complexity gradually
    - Use meaningful names for Areas, Categories, and Attributes
    - Add descriptions to document your structure
    - Test with sample data before bulk operations
    
    ---
    
    ### 🎉 Happy Tracking!
    
    Remember: Events Tracker is designed to be flexible. Start with basics and expand as you discover what works for your tracking needs.
    """)
    
    # Version info
    st.markdown("---")
    st.caption("Version: 2.2.6 | 2025-01-13 | Python: 3.11 | Streamlit: 1.28.0")


if __name__ == "__main__":
    main()
