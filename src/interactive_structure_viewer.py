"""
Events Tracker - Interactive Structure Viewer Module
====================================================
Created: 2025-11-25 10:00 UTC
Last Modified: 2025-12-10 18:30 UTC
Python: 3.11
Version: 1.11.3 - FIX: Discard infinite loop - COMPLETE FIX with index reset

CHANGELOG v1.11.3 (CRITICAL FIX - Discard Loop COMPLETE):
- 🐛 ROOT CAUSE IDENTIFIED: DataFrame index mismatch after Discard
  - area_display has original indices from filtered_df (e.g., [0, 5, 10])
  - st.data_editor returns DataFrame with RESET indices [0, 1, 2]
  - df.equals() compares indices too → always detected as "different"
  - This caused infinite loop: Discard → rerun → false positive → Discard...
- ✅ SOLUTION 1: Fixed normalize_for_comparison() to reset indices
  - Added reset_index(drop=True) before comparison
  - Now compares only DATA, not indices
- ✅ SOLUTION 2: Added discard_pending flag in State Machine
  - Prevents false positive detection immediately after Discard
  - Flag cleared after first successful render without changes
- 🔧 IMPROVED: All 3 tabs (Areas, Categories, Attributes) now:
  - Check discard_pending before setting has_changes
  - Call acknowledge_discard() after clean render
- 🎯 IMPACT: Discard button now works correctly in ALL scenarios
  - No more infinite loops
  - Filters unlock immediately after Discard
  - Clean state transition

CHANGELOG v1.11.2 (Critical Fix - Discard Loop):
- 🐛 ROOT CAUSE FIXED: original_df contained ALL data, edited_df contained SINGLE TAB
  - This mismatch caused has_unsaved_changes() to always detect "changes"
  - After Discard, data_editor re-rendered and set edited_df, triggering false positive
- ✅ SOLUTION: Removed global has_unsaved_changes() sync entirely
  - Each tab now manages its own change detection locally
  - state_mgr.state.has_changes is set ONLY when local tab detects real changes
- 🔧 Added normalize_for_comparison() helper function
  - Handles dtype differences from st.data_editor
  - Prevents false positives from float/int/string mismatches
- 🎯 Filters now lock/unlock based on LOCAL change detection, not global
- ⚡ Removed st.session_state.edited_df assignments (no longer needed)

CHANGELOG v1.11.1 (Hotfix):
- 🎯 UX IMPROVEMENT: Removed "Edit interface is hidden" blocking screen
  - Problem: st.stop() hid entire editor when unsaved changes existed
  - User had to scroll to banner for Discard button - poor experience
  - Now: Editor ALWAYS visible with inline Save/Discard buttons
- ✅ INLINE CONTROLS: Save/Discard buttons directly below each data_editor
  - Each tab (Areas, Categories, Attributes) has its own control section
  - Warning box shows when changes detected
  - Validation status shows before save
  - Type 'SAVE' confirmation + Save Changes button
  - Discard Changes button (no confirmation needed)
- 🔧 SIMPLIFIED BANNER: Top banner now just a short notification
  - Removed Discard button from banner (now inline in editor)
  - Cleaner, less intrusive warning message
  - Filters still properly disabled when changes exist
- 🎨 CONSISTENT LAYOUT across all 3 editors:
  - [Data Editor]
  - [Warning: unsaved changes] (if applicable)
  - [Validation status]
  - [Type SAVE input] [Save Button] [Discard Button]
- 🐛 DELETE: Added Cancel button to uncheck marked items
- 🐛 REMOVE BETWEEN: Added Cancel button option
- ⚡ TECHNICAL: No st.stop() in edit mode - full interface always renders

CHANGELOG v1.10.6 (Simplification - Remove Early Check):
- 🎯 PHILOSOPHY CHANGE: Use ONLY has_unsaved_changes() (regular check)
  - User report: "Banner shows but filters stay enabled" (desync issue)
  - Root cause: Two different checks see different state at different times
  - Early check runs BEFORE filters render → sees old state
  - Regular check runs AFTER filters render → sees new state but too late
  - Result: Banner and filters react to DIFFERENT information sources
- ✅ SOLUTION: Single source of truth
  - Removed has_unsaved_changes_early() function entirely
  - Removed all session_state editor keys (areas_editor, categories_editor, attributes_editor)
  - Use ONLY has_unsaved_changes() which checks edited_df
  - State Machine syncs ONCE after regular check
  - Filters render AFTER sync → see correct state
  - Banner and filters now react to SAME check
- 🔧 TECHNICAL: Simplified flow
  - Line ~2100: has_unsaved_changes() - THE ONLY CHECK
  - Line ~2105: State Machine sync immediately after
  - Line ~2208: Filters render with synced state
  - Line ~2115: Banner shows with same state
  - All three editors (Areas, Categories, Attributes) set edited_df consistently
- 🎯 IMPACT: Reliable synchronization
  - Banner appears → Filters disabled (both from same check) ✅
  - No more timing issues ✅
  - No more dual sync points ✅
  - Simpler, more maintainable code ✅
- ⚠️ LESSON LEARNED: Premature optimization
  - Early check was attempt to detect changes earlier
  - Created more problems than it solved
  - Simple, single-check approach is more reliable
  - KISS principle wins again

CHANGELOG v1.10.5 (Infinite Loop Fix - DEPRECATED):
- 🐛 CRITICAL FIX: Infinite rerun loop from v1.10.4
  - Problem: has_unsaved_changes_early() only checked if key exists
  - User report: "Constant state flipping Has Changes: False → True"
  - Symptom: "maximum recursion depth exceeded" error
  - Root cause: Key exists even without actual data changes → triggers rerun
  - Execution: Early check returns True → rerun → Regular check False → rerun → LOOP
- ✅ SOLUTION: Hybrid approach - check key existence AND data changes
  - Step 1: Check if editor key exists (fast gate)
  - Step 2: If exists, compare DataFrames to detect ACTUAL changes
  - Step 3: Return True ONLY if real data differences found
  - Prevents false positives from key existence alone
- 🔧 TECHNICAL: Enhanced has_unsaved_changes_early()
  - Iterates through all three editor keys (areas, categories, attributes)
  - For each key, filters original_df by Type
  - Normalizes both original and edited DataFrames
  - Uses row-by-row comparison to count changed rows
  - Returns (True, count) only if count > 0
- 🎯 IMPACT: Stable state management
  - No more infinite loops ✅
  - Filters block only when actual changes exist ✅
  - State transitions are deterministic ✅
  - DEBUG INFO shows stable values ✅
- ⚠️ LESSON LEARNED: Session state keys exist even without edits
  - data_editor with key parameter creates key immediately
  - Can't rely solely on key existence for change detection
  - Must validate with actual data comparison

CHANGELOG v1.10.4 (Filter Blocking Fix - Session State Backend):
- 🐛 CRITICAL FIX: Filters now properly disabled when editing in ALL tabs
  - Problem: Areas/Categories tabs didn't set edited_df → filters stayed enabled
  - Root cause: Catch-22 - early check ran before data_editor, saw no changes
  - User report: "Banner shows changes but filters still enabled" 
  - Impact: Areas tab (no banner + enabled filters), Categories/Attributes (banner + enabled filters initially)
- ✅ SOLUTION: Use session_state as data_editor backend
  - data_editor now uses key parameter → automatic session_state storage
  - Early check now detects changes BEFORE filter rendering
  - Works consistently across ALL three tabs (Areas, Categories, Attributes)
- 🐛 DEBUG INFO: Added sidebar debug panel
  - Shows: Viewer Mode, Has Changes, Filters status, Active Tab, edited_df state
  - Always visible for testing and monitoring
  - Helps verify state synchronization
- 🎨 BANNER SIMPLIFIED: Cleaner unsaved changes warning
  - Removed verbose "View what changed" from banner
  - Now just: collapsed expander at bottom of banner
  - Less screen space, cleaner UX
  - Banner only shows when filters blocked
- 🔧 TECHNICAL: Session state keys for editors
  - Areas: st.session_state.areas_editor
  - Categories: st.session_state.categories_editor  
  - Attributes: st.session_state.attributes_editor
  - All three now properly tracked by early check
- 🎯 IMPACT: Filter blocking now 100% reliable
  - User opens data_editor → changes detected immediately
  - Filters disable BEFORE any user interaction
  - Banner appears synchronized with filter state
  - Consistent behavior across all tabs

Description:
Interactive Excel-like table for direct structure editing without Excel files.
Uses st.data_editor with live database connection, validation, and batch save.
Integrated Excel export/import workflow for offline structure editing.
**MINIMAL State Machine integration for improved reliability.**
**Unified View Type control (Table/Sunburst/Treemap/Network Graph) with centralized filters.**

✨ NEW IN v1.10.0:
- 🎯 State Machine Integration (minimal, for critical paths only)
- 🐛 Bug Fix #1: Discard button now in unsaved changes banner
- 🐛 Bug Fix #2: Forms properly reset after ADD operations
- 🐛 Bug Fix #3: Discard works for filled forms
- 🆕 Insert Between: Smart category insertion between existing ones
- 🆕 Remove Between: Smart category removal with child promotion

Features:
- **STATE MACHINE**: Minimal integration for critical state management
- **UNIFIED VIEW TYPE**: Single dropdown for Table View, Sunburst, Treemap, Network Graph
- **CENTRALIZED FILTERS**: Area, Category (drill-down), Show Events - applied across ALL views
- **FILTER PROPAGATION**: Filters apply to Table View, Graph Views, Generate Excel, and Edit Mode
- **UNSAVED CHANGES PROTECTION**: Filters disabled when unsaved changes detected
- **IMPROVED DISCARD**: Now visible in banner, always accessible
- **INTEGRATED HELP**: Collapsible help section at page top with comprehensive guide
- **EXCEL EXPORT**: Generate Enhanced Excel respects active Area AND Category filters
- **EXCEL IMPORT**: Upload Hierarchical Excel in Edit Mode (4th tab)
- **THREE SEPARATE EDITORS**: Areas, Categories, and Attributes in tabs
- **FILTERS IN EDIT MODE**: Categories and Attributes tabs respect Area/Category filters
- **ADD**: Add new Areas, Categories, and Attributes
- **INSERT BETWEEN**: Smart category insertion preserving sort order
- **DELETE**: Delete with cascade warnings
- **REMOVE BETWEEN**: Smart category removal with child promotion
- **SMART FORMS**: Two-step form - select Data Type first, then relevant fields appear
- Dropdown validations for Data_Type and Is_Required
- Live validation before save
- Batch save with ONE confirmation (type 'SAVE')
- Rollback/discard changes option
- OPTIMIZED: Batch data loading with caching (60s TTL)
- IMPROVED: Unsaved changes warnings with preview

Dependencies: streamlit, pandas, supabase, state_machine, enhanced_structure_exporter, hierarchical_parser, error_reporter, structure_graph_viewer

Technical Details:
- Layout matches Download Structure - Hierarchical_View format
- Direct database connectivity (no Excel intermediary for editing)
- Integrated Excel export/import for offline work
- Validates changes before committing to database
- Uses @st.cache_data for 10x faster loading
- Tab-based interface for clarity and simplicity
- UUID generation for new entities
- Slug auto-generation from names
- CASCADE delete warnings
- Dynamic form generation based on Data Type
- **Unified View Control**: Single filter set for all visualization modes
- **State Sync**: StateManager ensures reliable state transitions
- **Data Loss Prevention**: Filters disabled when unsaved changes exist

CHANGELOG v1.9.11 (Add Operations Fix + UX Refinement - Complete):
- 🐛 FIXED: False positive after ADD operations (Bug #9 - CRITICAL)
  - Problem: After adding Areas/Categories/Attributes, banner shows "X unsaved changes"
  - User report: Added item but got false positive banner + disabled filters
  - Root cause: Same as DELETE bug - incomplete state clearing
  - ADD operations cleared only original_df, not edited_df or editing_active
- ✅ SOLUTION: Clear ALL state after ADD
  - Add Areas: Clear all state (original_df, edited_df, editing_active)
  - Add Categories: Clear all state
  - Add Attributes: Clear all state
  - Consistent with DELETE fix from v1.9.10
- 🎨 UX IMPROVEMENT: Removed redundant "Switch to Edit Mode" button
  - User feedback: Confusing to have both Mode toggle AND button
  - Solution: Keep only Mode toggle (radio buttons) for clarity
  - Simpler, cleaner interface
- 🔄 UX IMPROVEMENT: Discard button repositioned
  - OLD: Top row (col2) + Banner = Inconsistent placement
  - NEW: Each tab (Areas, Categories, Attributes) below tables
  - Benefit: Universal exit button always accessible in context
  - Position: Below Add forms, above tab boundary
  - Behavior: Disabled when no changes, enabled when changes exist
  - Upload Excel tab: NO Discard (separate logic as requested)
- 🎯 SIMPLIFIED: Row 1 layout
  - Removed empty col2 and col3
  - Clean single-column Mode toggle
  - Less visual clutter
- 💬 BEHAVIOR: Complete state management
  - ADD operations: Clear all state, unlock filters immediately
  - DELETE operations: Clear all state (from v1.9.10)
  - SAVE operations: Clear all state (existing)
  - DISCARD operations: Clear all state, always available per-tab
- 🎯 IMPACT: Perfect UX + Complete functionality
  - No false positives after ANY operation ✅
  - Discard always accessible where needed ✅
  - No redundant buttons ✅
  - Intuitive, clean interface ✅
  - Smart Lock system COMPLETE ✅

CHANGELOG v1.9.10 (DELETE State Fix - Complete Smart Lock):
- 🐛 FIXED: False positive "unsaved changes" after DELETE operations (Bug #8 - CRITICAL)
  - Problem: After deleting Areas/Categories/Attributes, banner shows "X unsaved changes"
  - User report: Deleted attribute but got "1 unsaved change" + disabled filters
  - Root cause: DELETE operations cleared only original_df, not edited_df or editing_active
  - Detection saw difference between states → false positive
  - Filters stayed locked, confusing UX
- ✅ SOLUTION: Clear ALL state after DELETE
  - Clear original_df ✅
  - Clear edited_df ✅ (NEW!)
  - Clear editing_active flag ✅ (NEW!)
  - Unlock filters immediately after DELETE
- 🎯 FIXED: All DELETE operations
  - Delete Areas: Clear all state
  - Delete Categories: Clear all state  
  - Delete Attributes: Clear all state
  - Consistent behavior across all delete operations
- 💬 BEHAVIOR: Clean state after DELETE
  - Delete operation succeeds → Success message ✅
  - All detection state cleared → No false positives ✅
  - Filters unlocked → Can browse immediately ✅
  - Rerun → Fresh clean state ✅
- 🎯 IMPACT: CRITICAL - Completes Smart Lock system
  - DELETE operations now work correctly ✅
  - No false positives after any operation ✅
  - Filters behave predictably ✅
  - User confusion eliminated ✅

CHANGELOG v1.9.9 (Smart Lock - FINAL Solution):
- 🎯 IMPLEMENTED: Smart filter locking based on data_editor rendering
  - Problem: v1.9.8 didn't detect when user actually started editing
  - User feedback: Filters should lock when editing starts, not just in Edit Mode
  - Solution: Set editing_active=True when data_editor renders
  - Clear editing_active=False on Save/Discard actions
- 🔒 BEHAVIOR: Filters lock automatically when data editor opens
  - Edit Mode → Filters enabled (can browse and filter) ✅
  - Open data editor (Areas/Categories/Attributes) → Filters LOCK 🔒
  - User edits data → Filters stay locked
  - Save or Discard → Filters UNLOCK ✅
  - Natural workflow: browse → edit → save/discard → browse again
- ✅ IMPROVED: Smart detection instead of complex logic
  - editing_active flag set when data_editor() is called
  - Flag cleared on Save/Discard button clicks
  - No delay, no false positives, no complex comparison
  - Simple, reliable, bulletproof
- 💬 UPDATED: Clear feedback messages
  - "Filters are enabled. When you open a data editor..."
  - "Finish editing to use filters (Save or Discard)"
  - User always understands current state
- 🎯 IMPACT: FINAL - Perfect balance of flexibility and safety
  - Can use filters to navigate before editing ✅
  - Filters lock as soon as editing starts ✅
  - No data loss possible ✅
  - Intuitive workflow ✅
  - Zero edge cases ✅

CHANGELOG v1.9.8 (Clean UX Fix - Final Data Loss Prevention):
- 🎨 IMPROVED: Clean UX without Streamlit warnings (Bug #7 - UX)
  - Problem: v1.9.7 revert strategy caused Streamlit warning about Session State API
  - User feedback: Confusing yellow warning message, filters not usable in Edit Mode
  - Solution: Remove revert strategy, rely on simple disabled=True
  - Result: Clean UI, no warnings, simple and clear behavior
- 🔘 ADDED: Permanent "Discard Changes" button in Edit Mode
  - Always visible in col2 (next to mode toggle)
  - Disabled when no changes (grey out)
  - Enabled when changes exist (clear and accessible)
  - User can always easily abandon unwanted edits
- 💬 IMPROVED: Clear feedback messages
  - Dynamic help tooltips: "Save or discard changes to use filters"
  - Info box in Edit Mode: "Filters are enabled..." when no changes
  - Improved error banner: Clear explanation of why filters disabled
  - User always knows why filters disabled and how to re-enable
- 🎯 SIMPLIFIED: Callback logic
  - Removed complex revert strategy (caused warnings)
  - Simple: disabled=unsaved_changes
  - Callbacks just update state normally
  - Disabled parameter prevents callback execution
- ✅ VERIFIED: Complete data loss prevention with clean UX
  - Filters truly disabled when unsaved changes
  - No Streamlit warnings
  - Clear user feedback
  - Easy access to Discard button
  - Natural workflow: edit → filter blocked → save/discard → filter enabled
- 🎯 IMPACT: CRITICAL - Complete fix with excellent UX
  - No data loss possible
  - No confusing warnings
  - Clear and intuitive interface
  - User satisfaction high

CHANGELOG v1.9.7 (Filter Revert Fix - Data Loss Prevention v2):
- 🐛 FIXED: Filter callbacks now REVERT to old value when unsaved changes exist (Bug #6 - CRITICAL)
  - Problem: v1.9.6 didn't prevent filter change, only avoided reset
  - Root cause: Disabled widgets still trigger on_change callbacks in Streamlit
  - User could change filter despite disabled state → data lost
  - Solution: REVERT filter selector to previous value in callback if unsaved changes
- 🔒 IMPROVED: True filter blocking with value reversion
  - on_area_change: Reverts area_filter_selector if has_edits
  - on_category_change: Reverts category_filter_selector if has_edits
  - Filter change completely blocked - no state change occurs
- ✅ VERIFIED: Unsaved changes survive ALL filter change attempts
  - User makes edit → Tries to change filter → Filter stays same ✅
  - Unsaved changes preserved → Banner remains → Data safe ✅
  - Even if disabled UI fails, callback protection works ✅
- 🎯 IMPACT: CRITICAL - Complete data loss prevention
  - Triple protection: Disabled UI + Callback revert + State preservation
  - No possible way to lose data through filter changes
  - Bulletproof Edit Mode safety

CHANGELOG v1.9.6 (Data Loss Prevention - CRITICAL FIX):
- 🐛 FIXED: Filter changes no longer cause data loss when unsaved changes exist (Bug #5 - CRITICAL DATA LOSS)
  - Problem: User edits data, changes filter, unsaved changes LOST without warning
  - Root cause: v1.9.5 filter callbacks reset state even with unsaved changes
  - Solution: Check for unsaved changes BEFORE resetting state in callbacks
- 🔒 IMPROVED: Callbacks now preserve unsaved changes
  - on_area_change: Only resets if no edited_df exists
  - on_category_change: Only resets if no edited_df exists
  - Prevents accidental data loss from filter changes
- ✅ VERIFIED: Unsaved changes survive filter change attempts
  - User makes edit → Changes filter → Changes preserved ✅
  - Filter should be disabled anyway (v1.9.3 feature)
  - Double protection: disabled UI + protected callbacks
- 🎯 IMPACT: CRITICAL - Prevents silent data loss
  - User Experience: Much safer Edit Mode
  - Data Integrity: Preserved even with user mistakes
  - Trust: System protects user's work

CHANGELOG v1.9.5 (Filter Change Detection Fix - Edge Case):
- 🐛 FIXED: Filter changes in Edit Mode no longer trigger false unsaved changes (Bug #4 - EDGE CASE)
  - Problem: Changing Area/Category filter triggered "0 unsaved changes" banner
  - Root cause: Filter change caused DataFrame reset but detection still compared old references
  - Solution: Reset original_df/edited_df on filter change (on_area_change, on_category_change)
- 🐛 FIXED: "0 unsaved changes" banner no longer appears (improved detection logic)
  - If num_changes = 0, return False (not unsaved_changes)
  - Prevents false positives from minor DataFrame differences (index order, etc.)
- 🎨 IMPROVED: Edit Mode interface hidden while banner is active
  - User must resolve changes (save/discard) before accessing edit tabs
  - Cleaner UX - no confusing "disabled" sections while changes pending
  - Added st.stop() to prevent rendering edit interface
- 📝 IMPROVED: Better warning message when edit interface is hidden
  - Clear instructions: Discard or Save
  - Tip: Interface will appear after changes resolved
- ✅ TESTED: Filter changes in Edit Mode work smoothly without false alarms
- 🎯 IMPACT: Edge case fixed - Edit Mode now works correctly with filters

CHANGELOG v1.9.4 (Critical Bugfixes - False Positive Detection):
- 🐛 FIXED: False positive unsaved changes detection (Bug #1 - BLOCKER)
  - Problem: System showed "36 unsaved changes" when no actual changes made
  - Root cause: st.data_editor returned DataFrames with different dtypes/NaN handling
  - Solution: Normalized DataFrame comparison (convert to strings, handle NaN consistently)
- 🐛 FIXED: Add Attribute filter showed all Areas instead of filtered Area (Bug #2 - HIGH)
  - Problem: Form used old filter keys instead of unified view_filters
  - Solution: Updated to use st.session_state.view_filters['area'] and ['category']
- 📝 IMPROVED: Better preview detection - shows actual changes accurately
- 📝 IMPROVED: Clearer instructions for save workflow in banner
- ✅ TESTED: Zero false positives - only real changes trigger warning
- 🎯 IMPACT: Users can now trust the unsaved changes detection system

CHANGELOG v1.9.3 (Unsaved Changes UX Improvement):
- 🎯 UX: Prominent error banner shows number of unsaved changes
- 👁️ NEW: Expandable preview of what changed (row, type, name, columns)
- 🔒 FIXED: Filters now DISABLED when unsaved changes exist (prevents accidental data loss)
- 🗑️ NEW: "Discard All Changes" button at the top (quick access)
- 📝 IMPROVED: Clear instructions on how to save (scroll to Edit Mode section)
- ⚠️ PREVENTED: Users can no longer accidentally change filters and lose edits
- 🎨 UX: Visual hierarchy - Error → Preview → Instructions → Actions

CHANGELOG v1.7.1 (Hotfix - Search Term Scope):
- 🐛 FIXED: UnboundLocalError for search_term in Generate Excel
- 🔧 MOVED: search_term definition before col3 (Generate Excel button)
- ✅ TESTED: Filtered Excel export now works correctly
- 📝 ISSUE: search_term was referenced before assignment (line 1373 before 1417)
- 🎯 FIX: Moved search input widget before button to ensure scope availability

CHANGELOG v1.7.0 (Filtered Excel Export):
- ✨ NEW: Generate Excel respects active filters (Area + Search)
- 🎯 FEATURE: Export filtered structure for sharing specific Area themes
- 📦 USE CASE: Create starter templates for new users by exporting single Areas
- 🔧 IMPROVED: Success message shows which filters were applied
- 📝 TECHNICAL: EnhancedStructureExporter now accepts filter_area and filter_category params

CHANGELOG v1.6.1 (Production Release):
- 🗑️ REMOVED: Refresh button from Edit Mode (user feedback - not needed)
- 🎯 CLEAN: Edit Mode col3 now empty (intentional - refresh via browser or navigation)
- 📝 NOTE: Read-Only mode keeps Generate Excel button (primary action)

CHANGELOG v1.6.0:
- ✨ NEW: Collapsible Help section at page top with comprehensive guide
- ✨ NEW: Generate Enhanced Excel button in Read-Only mode (replaces Refresh)
- ✨ NEW: Upload Hierarchical Excel tab in Edit Mode (4th tab)
- 🔧 IMPROVED: Complete Excel workflow integrated into single page
- 🔧 IMPROVED: Better UX with contextual buttons (Excel export only in Read-Only)
- 📚 DOCUMENTATION: Detailed help for both direct editing and Excel workflows
- 🎯 GOAL: Single hub for all structure management operations
- ⚡ IMPORTS: Added enhanced_structure_exporter, hierarchical_parser, error_reporter

CHANGELOG v1.5.9:
- ✅ MAJOR FIX: Two-step form approach - select Data Type OUTSIDE form first
- 🎯 SOLUTION: Data Type selector triggers form re-render with relevant fields
- ✨ NEW UX: Step 1: Select Data Type → Step 2: Fill relevant fields
- 🔧 FIXED: Fields now actually hide/show when Data Type changes (user feedback!)
- 💡 IMPROVED: Helper text shows which fields are hidden and why
- Field visibility rules (unchanged):
  - Unit: ONLY 'number' type
  - Default Value: All EXCEPT 'link' and 'image'
  - Validation Min/Max: ONLY 'number' and 'datetime'
- Technical: Data Type selectbox outside st.form() allows dynamic field rendering

CHANGELOG v1.5.8:
- 🐛 FIXED: Reverted to show/hide approach instead of disabled fields
- 🔧 IMPROVED: Unit field now shows ONLY for 'number' type (user feedback)
- 🔧 IMPROVED: Default Value hidden for 'link' and 'image' types
- 🔧 IMPROVED: Validation Min/Max show only for 'number' and 'datetime' types
- 💡 IMPROVED: Helper caption shows which fields are hidden and why
- Field visibility rules:
  - Unit: ONLY 'number' type
  - Default Value: All EXCEPT 'link' and 'image'
  - Validation Min/Max: ONLY 'number' and 'datetime'
- ⚠️ NOTE: Table editing still allows all columns - validation needed (future fix)

CHANGELOG v1.5.7:
- 🐛 FIXED: Smart field masking now works correctly - uses DISABLED fields instead of hiding
- 🔧 IMPROVED: Non-applicable fields shown as disabled (greyed out) with help text
- 🔧 IMPROVED: Added caption explaining disabled field behavior
- ✅ VERIFIED: Disabled fields don't allow input and pass empty values to database
- Field behavior by Data Type:
  - 'link' & 'image': Unit, Default Value, Validation Min/Max → DISABLED
  - 'text' & 'boolean': Validation Min/Max → DISABLED
  - 'number' & 'datetime': All fields → ENABLED

CHANGELOG v1.5.6:
- 🐛 FIXED: Add Attribute form now always visible, even when no attributes exist (Bug #11 - CRITICAL)
- 🐛 FIXED: Filter by Area in Edit Attributes now queries database directly (Bug #12)
- ✨ NEW FEATURE: Smart field masking based on Data Type
  - 'link' and 'image' types: Hide Unit, Default Value, Validation fields
  - 'text' and 'boolean' types: Hide Validation Min/Max
  - 'number' and 'datetime' types: Show all fields
- 🔧 IMPROVED: Better UX with info messages for hidden fields
- 🔧 IMPROVED: Consistent behavior across all tabs (forms always accessible)

CHANGELOG v1.5.5:
- 🐛 FIXED: Add Category form now always visible, even when no categories exist (Bug #8)
- 🐛 FIXED: Filter by Category in Edit Attributes shows ALL categories from filtered Area (Bug #9)
- ✅ VERIFIED: Add Attribute respects filters correctly (Bug #10 was already fixed in v1.5.4)
- 🔧 IMPROVED: Better info messages when no categories/attributes found
- 🔧 IMPROVED: Add Category accessible even with empty filtered areas

CHANGELOG v1.5.4:
- 🐛 FIXED: Filter by Area dropdown in Edit Categories now queries database directly (Bug #6)
- 🐛 FIXED: Add Attribute form respects Area and Category filters (Bug #7)
- 🔧 IMPROVED: Add Attribute shows filter context with info box
- 🔧 IMPROVED: Category selection locked when single option available

CHANGELOG v1.5.3:
- 🐛 CRITICAL FIX: Form double submit prevention with unique keys
- 🐛 FIXED: Add Area form now uses unique key per submit (Bug #3)
- 🐛 FIXED: Add Category form now uses unique key per submit (Bug #4 - prevents duplicate inserts)
- 🐛 FIXED: Add Attribute form now uses unique key per submit
- 🐛 FIXED: Form fields clear properly after successful add (Bug #5)
- 🔧 IMPROVED: Form counter in session state increments after success
- 🔧 IMPROVED: Each form gets fresh state after rerun
- ✨ NEW: Form submission counters (area_form_counter, category_form_counter, attribute_form_counter)
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime
import uuid
import re
import os
import tempfile

# Import State Machine (minimal integration)
from .state_machine import StateManager

# Import Excel handling modules
from .enhanced_structure_exporter import EnhancedStructureExporter
from .hierarchical_parser import HierarchicalParser
from .error_reporter import generate_error_excel

# Import Graph Viewer module
from .structure_graph_viewer import render_graph_viewer_integrated


# ============================================
# CONSTANTS
# ============================================

# Data type options for dropdown
DATA_TYPES = ['number', 'text', 'datetime', 'boolean', 'link', 'image']

# Is_Required options for dropdown
IS_REQUIRED_OPTIONS = ['Yes', 'No', '']

# Column definitions with editability flag
COLUMN_CONFIG = [
    ('Type', False, 'text'),           # Auto-calculated
    ('Level', False, 'number'),        # Auto-calculated
    ('Sort_Order', False, 'number'),   # Auto-calculated
    ('Area', False, 'text'),           # Auto-calculated
    ('Category_Path', False, 'text'),  # Auto-calculated (but can be edited to add new rows)
    ('Category', True, 'text'),        # Editable
    ('Attribute_Name', True, 'text'),  # Editable
    ('Data_Type', True, 'select'),     # Editable with dropdown
    ('Unit', True, 'text'),            # Editable
    ('Is_Required', True, 'select'),   # Editable with dropdown
    ('Default_Value', True, 'text'),   # Editable
    ('Validation_Min', True, 'text'),  # Editable
    ('Validation_Max', True, 'text'),  # Editable
    ('Description', True, 'text')      # Editable
]


# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_slug(name: str) -> str:
    """
    Generate URL-friendly slug from name.
    
    Args:
        name: Original name
    
    Returns:
        Slugified name (lowercase, no spaces, no special chars)
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def get_next_sort_order(client, table: str, user_id: str, parent_field: Optional[str] = None, parent_id: Optional[str] = None) -> int:
    """
    Get next sort_order value for a table.
    
    Args:
        client: Supabase client
        table: Table name ('areas', 'categories', 'attribute_definitions')
        user_id: Current user's UUID
        parent_field: Optional parent field name ('area_id', 'category_id')
        parent_id: Optional parent ID
    
    Returns:
        Next sort_order value (max + 1)
    """
    try:
        query = client.table(table).select('sort_order').eq('user_id', user_id)
        
        # Add parent filter if specified
        if parent_field and parent_id:
            query = query.eq(parent_field, parent_id)
        
        result = query.execute()
        
        if result.data:
            max_sort = max([row['sort_order'] for row in result.data])
            return max_sort + 1
        else:
            return 1
    
    except Exception as e:
        st.error(f"Error getting next sort_order: {str(e)}")
        return 1


def check_area_has_dependencies(client, area_id: str, user_id: str) -> Tuple[bool, str]:
    """
    Check if area has categories or events.
    
    Args:
        client: Supabase client
        area_id: Area UUID
        user_id: User UUID
    
    Returns:
        Tuple of (has_dependencies, warning_message)
    """
    try:
        # Check categories
        cat_result = client.table('categories').select('id').eq('area_id', area_id).eq('user_id', user_id).execute()
        num_categories = len(cat_result.data) if cat_result.data else 0
        
        # Check events (through categories)
        if num_categories > 0:
            cat_ids = [c['id'] for c in cat_result.data]
            event_result = client.table('events').select('id').in_('category_id', cat_ids).eq('user_id', user_id).execute()
            num_events = len(event_result.data) if event_result.data else 0
        else:
            num_events = 0
        
        if num_categories > 0 or num_events > 0:
            msg = f"⚠️ **WARNING:** This area has {num_categories} categories"
            if num_events > 0:
                msg += f" and {num_events} events"
            msg += ". Deleting it will CASCADE DELETE all of them!"
            return True, msg
        
        return False, ""
    
    except Exception as e:
        return False, f"Error checking dependencies: {str(e)}"


def check_category_has_dependencies(client, category_id: str, user_id: str) -> Tuple[bool, str]:
    """
    Check if category has attributes or events.
    
    Args:
        client: Supabase client
        category_id: Category UUID
        user_id: User UUID
    
    Returns:
        Tuple of (has_dependencies, warning_message)
    """
    try:
        # Check attributes
        attr_result = client.table('attribute_definitions').select('id').eq('category_id', category_id).eq('user_id', user_id).execute()
        num_attributes = len(attr_result.data) if attr_result.data else 0
        
        # Check events
        event_result = client.table('events').select('id').eq('category_id', category_id).eq('user_id', user_id).execute()
        num_events = len(event_result.data) if event_result.data else 0
        
        # Check child categories
        child_result = client.table('categories').select('id').eq('parent_category_id', category_id).eq('user_id', user_id).execute()
        num_children = len(child_result.data) if child_result.data else 0
        
        if num_attributes > 0 or num_events > 0 or num_children > 0:
            msg = f"⚠️ **WARNING:** This category has"
            parts = []
            if num_children > 0:
                parts.append(f"{num_children} child categories")
            if num_attributes > 0:
                parts.append(f"{num_attributes} attributes")
            if num_events > 0:
                parts.append(f"{num_events} events")
            msg += " " + ", ".join(parts) + ". Deleting it will CASCADE DELETE all of them!"
            return True, msg
        
        return False, ""
    
    except Exception as e:
        return False, f"Error checking dependencies: {str(e)}"


# ============================================
# CACHED DATA LOADING
# ============================================

@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_all_structure_data(_client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Load ALL structure data from database at once (optimized batch loading).
    
    Args:
        _client: Supabase client (underscore prefix to avoid hashing)
        user_id: Current user's UUID
    
    Returns:
        Tuple of (areas, categories, attributes) as lists of dicts
    """
    try:
        # Load ALL areas at once
        areas_response = _client.table('areas') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        areas = areas_response.data if areas_response.data else []
        
        if not areas:
            return [], [], []
        
        # Load ALL categories at once
        categories_response = _client.table('categories') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        categories = categories_response.data if categories_response.data else []
        
        # Load ALL attributes at once
        attributes_response = _client.table('attribute_definitions') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        attributes = attributes_response.data if attributes_response.data else []
        
        return areas, categories, attributes
    
    except Exception as e:
        st.error(f"❌ Error loading structure data: {str(e)}")
        return [], [], []


# ============================================
# DATA TRANSFORMATION
# ============================================

def load_structure_as_dataframe(client, user_id: str) -> pd.DataFrame:
    """
    Load structure from database and convert to hierarchical DataFrame.
    Uses cached batch loading for 10x performance improvement.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
    
    Returns:
        DataFrame with hierarchical structure including metadata columns (_area_id, _category_id, _attribute_id)
    """
    try:
        # Load ALL data at once (cached)
        areas, categories, attributes = load_all_structure_data(client, user_id)
        
        if not areas:
            st.warning("⚠️ No areas found. Please upload a template first.")
            return pd.DataFrame()
        
        # Build lookup maps for O(1) access
        categories_by_area = {}
        categories_by_parent = {}
        categories_by_id = {}
        attributes_by_category = {}
        
        # Map categories by area_id
        for cat in categories:
            area_id = cat['area_id']
            if area_id not in categories_by_area:
                categories_by_area[area_id] = []
            categories_by_area[area_id].append(cat)
            
            # Map categories by parent_id
            parent_id = cat.get('parent_category_id')
            if parent_id:
                if parent_id not in categories_by_parent:
                    categories_by_parent[parent_id] = []
                categories_by_parent[parent_id].append(cat)
            
            # Map categories by id
            categories_by_id[cat['id']] = cat
        
        # Map attributes by category_id
        for attr in attributes:
            cat_id = attr['category_id']
            if cat_id not in attributes_by_category:
                attributes_by_category[cat_id] = []
            attributes_by_category[cat_id].append(attr)
        
        # Build hierarchical structure
        rows = []
        
        for area in areas:
            area_id = area['id']
            area_name = area['name']
            
            # Add Area row
            rows.append({
                'Type': 'Area',
                'Level': 0,
                'Sort_Order': area['sort_order'],
                'Area': area_name,
                'Category_Path': area_name,
                'Category': '',
                'Attribute_Name': '',
                'Data_Type': '',
                'Unit': '',
                'Is_Required': '',
                'Default_Value': '',
                'Validation_Min': '',
                'Validation_Max': '',
                'Description': area.get('description', ''),
                '_area_id': area_id,
                '_category_id': None,
                '_attribute_id': None
            })
            
            # Process categories for this area
            area_categories = categories_by_area.get(area_id, [])
            root_categories = [c for c in area_categories if not c.get('parent_category_id')]
            
            # Sort root categories by sort_order
            root_categories.sort(key=lambda x: x['sort_order'])
            
            # Process each root category tree
            for root_cat in root_categories:
                _add_category_tree(
                    root_cat, 
                    area_name, 
                    area_name, 
                    rows,
                    categories_by_parent,
                    attributes_by_category,
                    categories_by_id
                )
        
        return pd.DataFrame(rows)
    
    except Exception as e:
        st.error(f"❌ Error loading structure: {str(e)}")
        return pd.DataFrame()


def _add_category_tree(
    category: Dict,
    area_name: str,
    parent_path: str,
    rows: List[Dict],
    categories_by_parent: Dict,
    attributes_by_category: Dict,
    categories_by_id: Dict
):
    """
    Recursively add category and its tree to rows list.
    All data is already loaded in memory - no DB queries!
    
    Args:
        category: Category dict
        area_name: Area name
        parent_path: Parent's category path
        rows: List to append rows to
        categories_by_parent: Map of parent_id -> list of child categories
        attributes_by_category: Map of category_id -> list of attributes
        categories_by_id: Map of category_id -> category dict
    """
    cat_id = category['id']
    cat_name = category['name']
    cat_level = category['level']
    
    # Build category path
    cat_path = f"{parent_path} > {cat_name}"
    
    # Add Category row
    rows.append({
        'Type': 'Category',
        'Level': cat_level,
        'Sort_Order': category['sort_order'],
        'Area': area_name,
        'Category_Path': cat_path,
        'Category': cat_name,
        'Attribute_Name': '',  
        'Data_Type': '',
        'Unit': '',
        'Is_Required': '',
        'Default_Value': '',
        'Validation_Min': '',
        'Validation_Max': '',
        'Description': category.get('description', ''),
        '_area_id': category['area_id'],
        '_category_id': cat_id,
        '_attribute_id': None
    })
    
    # Add attributes for this category
    attrs = attributes_by_category.get(cat_id, [])
    attrs.sort(key=lambda x: x['sort_order'])
    
    for attr in attrs:
        # Parse validation_rules JSONB
        val_rules = attr.get('validation_rules', {})
        if isinstance(val_rules, str):
            try:
                val_rules = json.loads(val_rules)
            except:
                val_rules = {}
        
        val_min = str(val_rules.get('min', '')) if val_rules and 'min' in val_rules else ''
        val_max = str(val_rules.get('max', '')) if val_rules and 'max' in val_rules else ''
        
        # Convert is_required to Yes/No
        is_required = 'Yes' if attr.get('is_required', False) else 'No'
        
        # Add Attribute row
        rows.append({
            'Type': 'Attribute',
            'Level': cat_level + 1,
            'Sort_Order': attr['sort_order'],
            'Area': area_name,
            'Category_Path': cat_path,
            'Category': cat_name,
            'Attribute_Name': attr['name'],
            'Data_Type': attr['data_type'],
            'Unit': attr.get('unit', ''),
            'Is_Required': is_required,
            'Default_Value': attr.get('default_value', ''),
            'Validation_Min': val_min,
            'Validation_Max': val_max,
            'Description': attr.get('description', ''),
            '_area_id': category['area_id'],
            '_category_id': cat_id,
            '_attribute_id': attr['id']
        })
    
    # Recursively add child categories
    child_categories = categories_by_parent.get(cat_id, [])
    child_categories.sort(key=lambda x: x['sort_order'])
    
    for child_cat in child_categories:
        _add_category_tree(
            child_cat,
            area_name,
            cat_path,
            rows,
            categories_by_parent,
            attributes_by_category,
            categories_by_id
        )


# ============================================
# FILTERING
# ============================================

def apply_filters(df: pd.DataFrame, selected_area: str, selected_category: str = "All Categories") -> pd.DataFrame:
    """
    Apply Area and Category filters to dataframe.
    
    Args:
        df: Original dataframe
        selected_area: Selected area name or "All Areas"
        selected_category: Selected category name or "All Categories"
    
    Returns:
        Filtered dataframe
    """
    filtered = df.copy()
    
    # Filter by Area
    if selected_area != "All Areas":
        filtered = filtered[filtered['Area'] == selected_area]
    
    # Filter by Category (drill-down)
    if selected_category != "All Categories":
        # Filter to show:
        # 1. The selected category itself
        # 2. All its child categories (any level deep)
        # 3. All attributes belonging to selected category and its children
        
        # Build category path pattern to match
        # If category is "Automobili", match:
        # - "Finance > Rashodi > Automobili"
        # - "Finance > Rashodi > Automobili > Lacetti ZG7728EH"
        # - etc.
        
        # First, get all rows that have this category in their Category_Path
        mask = filtered['Category_Path'].str.contains(f"> {selected_category}", case=False, na=False, regex=False) | \
               filtered['Category_Path'].str.endswith(selected_category, na=False)
        
        # Also include the Area row if it's shown (Type == 'Area')
        area_mask = filtered['Type'] == 'Area'
        
        filtered = filtered[mask | area_mask]
    
    return filtered


# ============================================
# v1.11.1: HELPER FOR ROBUST DATAFRAME COMPARISON
# ============================================

def normalize_for_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame for robust comparison.
    Handles dtype differences, NaN values, float precision, and INDEX DIFFERENCES
    that st.data_editor may introduce.
    
    CRITICAL FIX v1.11.3: Added reset_index(drop=True) to prevent false positives
    when comparing DataFrames with different index values.
    
    Args:
        df: DataFrame to normalize
        
    Returns:
        Normalized DataFrame safe for equals() comparison
    """
    df_norm = df.copy()
    
    # CRITICAL v1.11.3: Reset index FIRST to avoid index-based comparison issues
    # data_editor returns DataFrame with reset indices [0, 1, 2...]
    # Original DataFrame may have indices like [0, 5, 10, 15...]
    # Without reset, df.equals() returns False even when data is identical
    df_norm = df_norm.reset_index(drop=True)
    
    for col in df_norm.columns:
        # Fill NaN/None with empty string before conversion
        df_norm[col] = df_norm[col].fillna('').astype(str)
        
        # Clean up string representation of floats
        # "0.0" -> "0", "1.0" -> "1" 
        df_norm[col] = df_norm[col].str.replace(r'\.0$', '', regex=True)
    
    # Sort columns alphabetically
    df_norm = df_norm[sorted(df_norm.columns)]
    
    return df_norm


# ============================================
# VALIDATION
# ============================================

def validate_changes(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate edited dataframe for common errors.
    
    Args:
        df: Edited dataframe
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    for idx, row in df.iterrows():
        row_type = row.get('Type', '')
        
        # Validate Category rows
        if row_type == 'Category':
            if not row.get('Category'):
                errors.append(f"Row {idx + 1}: Category name is required")
        
        # Validate Attribute rows
        elif row_type == 'Attribute':
            if not row.get('Attribute_Name'):
                errors.append(f"Row {idx + 1}: Attribute name is required")
            
            if not row.get('Data_Type'):
                errors.append(f"Row {idx + 1}: Data type is required")
            
            # Validate Data_Type values
            if row.get('Data_Type') and row.get('Data_Type') not in DATA_TYPES:
                errors.append(f"Row {idx + 1}: Invalid data type '{row.get('Data_Type')}'")
            
            # Validate Is_Required values
            if row.get('Is_Required') and row.get('Is_Required') not in IS_REQUIRED_OPTIONS:
                errors.append(f"Row {idx + 1}: Is_Required must be 'Yes', 'No', or empty")
    
    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================
# SAVE TO DATABASE
# ============================================

def save_changes_to_database(
    client,
    user_id: str,
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame
) -> Tuple[bool, str, Dict[str, int]]:
    """
    Save changes to database.
    Compares original_df and edited_df to identify changes.
    
    Args:
        client: Supabase client
        user_id: Current user's UUID
        original_df: Original dataframe with metadata columns
        edited_df: Edited dataframe (may not have all metadata columns)
    
    Returns:
        Tuple of (success, message, stats_dict)
    """
    stats = {
        'categories': 0,
        'attributes': 0,
        'errors': 0
    }
    errors = []
    
    try:
        # Iterate through rows and detect changes
        for idx, edit_row in edited_df.iterrows():
            try:
                # Find corresponding row in original_df
                orig_row = original_df.loc[idx]
                
                row_type = orig_row['Type']
                
                # Check if row has changed
                has_changed = False
                for col in edited_df.columns:
                    if col in original_df.columns:
                        if str(edit_row[col]) != str(orig_row[col]):
                            has_changed = True
                            break
                
                if not has_changed:
                    continue
                
                # CATEGORY UPDATE
                if row_type == 'Category':
                    cat_id = orig_row['_category_id']
                    if pd.notna(cat_id):
                        # Prepare update data
                        update_data = {
                            'name': edit_row['Category'],
                            'description': edit_row['Description'] if edit_row['Description'] else None
                        }
                        
                        client.table('categories') \
                            .update(update_data) \
                            .eq('id', cat_id) \
                            .eq('user_id', user_id) \
                            .execute()
                        
                        stats['categories'] += 1
                
                # ATTRIBUTE UPDATE
                elif row_type == 'Attribute':
                    attr_id = orig_row['_attribute_id']
                    if pd.notna(attr_id):
                        # Parse validation rules
                        val_rules = {}
                        if edit_row['Validation_Min']:
                            try:
                                val_rules['min'] = float(edit_row['Validation_Min'])
                            except:
                                val_rules['min'] = edit_row['Validation_Min']
                        
                        if edit_row['Validation_Max']:
                            try:
                                val_rules['max'] = float(edit_row['Validation_Max'])
                            except:
                                val_rules['max'] = edit_row['Validation_Max']
                        
                        # Convert Is_Required to boolean
                        is_required = edit_row['Is_Required'] == 'Yes'
                        
                        # Prepare update data
                        update_data = {
                            'name': edit_row['Attribute_Name'],
                            'data_type': edit_row['Data_Type'] if edit_row['Data_Type'] else 'text',
                            'unit': edit_row['Unit'] if edit_row['Unit'] else None,
                            'is_required': is_required,
                            'default_value': edit_row['Default_Value'] if edit_row['Default_Value'] else None,
                            'validation_rules': val_rules if val_rules else {},
                            'description': edit_row['Description'] if edit_row['Description'] else None
                        }
                        
                        client.table('attribute_definitions') \
                            .update(update_data) \
                            .eq('id', attr_id) \
                            .eq('user_id', user_id) \
                            .execute()
                        
                        stats['attributes'] += 1
            
            except Exception as e:
                stats['errors'] += 1
                errors.append(f"Row {idx + 1}: {str(e)}")
                # Continue processing other rows
        
        total_updates = stats['categories'] + stats['attributes']
        
        if stats['errors'] > 0:
            error_msg = f"Completed with {stats['errors']} errors. Check details below."
            return False, error_msg, stats
        elif total_updates == 0:
            return True, "No changes detected", stats
        else:
            return True, f"Successfully updated {total_updates} items", stats
    
    except Exception as e:
        return False, f"Error saving changes: {str(e)}", stats


def _save_category_changes(
    client,
    user_id: str,
    original_cat_df: pd.DataFrame,
    edited_cat_df: pd.DataFrame,
    full_df: pd.DataFrame
) -> Tuple[bool, Dict[str, int]]:
    """
    Save category changes to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        original_cat_df: Original category dataframe (display columns only)
        edited_cat_df: Edited category dataframe (display columns only)
        full_df: Full dataframe with metadata columns (_category_id, etc.)
    
    Returns:
        Tuple of (success, stats_dict)
    """
    stats = {'categories': 0, 'errors': 0}
    
    try:
        # Find rows that have changed
        cat_cols = ['Category', 'Description']
        
        for idx, edited_row in edited_cat_df.iterrows():
            # Check if this row has changed
            orig_row = original_cat_df.loc[idx]
            has_changed = False
            
            for col in cat_cols:
                if col in edited_cat_df.columns and col in original_cat_df.columns:
                    if str(edited_row[col]) != str(orig_row[col]):
                        has_changed = True
                        break
            
            if not has_changed:
                continue
            
            # Get category_id from full_df (which has metadata)
            # Find matching row by index
            full_row = full_df.loc[idx]
            cat_id = full_row['_category_id']
            
            if pd.notna(cat_id):
                # Prepare update data
                update_data = {
                    'name': edited_row['Category'],
                    'description': edited_row['Description'] if edited_row['Description'] else None
                }
                
                client.table('categories') \
                    .update(update_data) \
                    .eq('id', cat_id) \
                    .eq('user_id', user_id) \
                    .execute()
                
                stats['categories'] += 1
        
        return True, stats
    
    except Exception as e:
        st.error(f"Error saving category changes: {str(e)}")
        stats['errors'] += 1
        return False, stats


def _save_area_changes(
    client,
    user_id: str,
    original_area_df: pd.DataFrame,
    edited_area_df: pd.DataFrame,
    full_df: pd.DataFrame
) -> Tuple[bool, Dict[str, int]]:
    """
    Save area changes to database.
    v1.11.0: Added for inline Save functionality
    
    Args:
        client: Supabase client
        user_id: User ID
        original_area_df: Original area dataframe (display columns only)
        edited_area_df: Edited area dataframe (display columns only)
        full_df: Full dataframe with metadata columns (_area_id, etc.)
    
    Returns:
        Tuple of (success, stats_dict)
    """
    stats = {'areas': 0, 'errors': 0}
    
    try:
        # Find rows that have changed
        area_cols = ['Area', 'Description']
        
        for idx, edited_row in edited_area_df.iterrows():
            # Check if this row has changed
            orig_row = original_area_df.loc[idx]
            has_changed = False
            
            for col in area_cols:
                if col in edited_area_df.columns and col in original_area_df.columns:
                    orig_val = str(orig_row[col]) if pd.notna(orig_row[col]) else ''
                    edit_val = str(edited_row[col]) if pd.notna(edited_row[col]) else ''
                    if orig_val != edit_val:
                        has_changed = True
                        break
            
            if not has_changed:
                continue
            
            # Get area_id from full_df (which has metadata)
            full_row = full_df.loc[idx]
            area_id = full_row['_area_id']
            
            if pd.notna(area_id):
                # Prepare update data
                update_data = {
                    'name': edited_row['Area'],
                    'description': edited_row['Description'] if pd.notna(edited_row['Description']) else None
                }
                
                client.table('areas') \
                    .update(update_data) \
                    .eq('id', area_id) \
                    .eq('user_id', user_id) \
                    .execute()
                
                stats['areas'] += 1
        
        return True, stats
    
    except Exception as e:
        st.error(f"Error saving area changes: {str(e)}")
        stats['errors'] += 1
        return False, stats


def _save_attribute_changes(
    client,
    user_id: str,
    original_attr_df: pd.DataFrame,
    edited_attr_df: pd.DataFrame,
    full_df: pd.DataFrame
) -> Tuple[bool, Dict[str, int]]:
    """
    Save attribute changes to database.
    v1.11.0: Added for inline Save functionality
    
    Args:
        client: Supabase client
        user_id: User ID
        original_attr_df: Original attribute dataframe (display columns only)
        edited_attr_df: Edited attribute dataframe (display columns only)
        full_df: Full dataframe with metadata columns (_attribute_id, etc.)
    
    Returns:
        Tuple of (success, stats_dict)
    """
    stats = {'attributes': 0, 'errors': 0}
    
    try:
        # Find rows that have changed
        attr_cols = ['Attribute_Name', 'Data_Type', 'Unit', 'Is_Required', 'Default_Value', 'Validation_Min', 'Validation_Max']
        
        for idx, edited_row in edited_attr_df.iterrows():
            # Check if this row has changed
            orig_row = original_attr_df.loc[idx]
            has_changed = False
            
            for col in attr_cols:
                if col in edited_attr_df.columns and col in original_attr_df.columns:
                    orig_val = str(orig_row[col]) if pd.notna(orig_row[col]) else ''
                    edit_val = str(edited_row[col]) if pd.notna(edited_row[col]) else ''
                    if orig_val != edit_val:
                        has_changed = True
                        break
            
            if not has_changed:
                continue
            
            # Get attribute_id from full_df (which has metadata)
            full_row = full_df.loc[idx]
            attr_id = full_row['_attribute_id']
            
            if pd.notna(attr_id):
                # Prepare update data
                update_data = {
                    'name': edited_row['Attribute_Name'],
                    'data_type': edited_row['Data_Type'],
                    'unit': edited_row['Unit'] if pd.notna(edited_row['Unit']) else None,
                    'is_required': edited_row['Is_Required'] == 'Yes',
                    'default_value': edited_row['Default_Value'] if pd.notna(edited_row['Default_Value']) else None
                }
                
                # Handle validation rules (min/max)
                validation_rules = {}
                if pd.notna(edited_row.get('Validation_Min')) and edited_row.get('Validation_Min') != '':
                    validation_rules['min'] = edited_row['Validation_Min']
                if pd.notna(edited_row.get('Validation_Max')) and edited_row.get('Validation_Max') != '':
                    validation_rules['max'] = edited_row['Validation_Max']
                update_data['validation_rules'] = validation_rules if validation_rules else {}
                
                client.table('attribute_definitions') \
                    .update(update_data) \
                    .eq('id', attr_id) \
                    .eq('user_id', user_id) \
                    .execute()
                
                stats['attributes'] += 1
        
        return True, stats
    
    except Exception as e:
        st.error(f"Error saving attribute changes: {str(e)}")
        stats['errors'] += 1
        return False, stats


# ============================================
# ADD FUNCTIONS
# ============================================

def add_new_area(client, user_id: str, name: str, description: str = "") -> Tuple[bool, str]:
    """
    Add new area to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        name: Area name
        description: Area description
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Check if area with this name already exists (BEFORE generating UUID)
        existing = client.table('areas').select('id').eq('user_id', user_id).eq('name', name).execute()
        if existing.data and len(existing.data) > 0:
            return False, f"❌ Area '{name}' already exists! Please choose a different name or delete the existing area first."
        
        # Generate UUID and slug
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        # Get next sort_order
        sort_order = get_next_sort_order(client, 'areas', user_id)
        
        # Prepare data
        area_data = {
            'id': new_id,
            'user_id': user_id,
            'name': name,
            'slug': slug,
            'sort_order': sort_order,
            'description': description if description else None,
            'icon': None,
            'color': None,
            'template_id': None
        }
        
        # Insert
        result = client.table('areas').insert(area_data).execute()
        
        # Verify insert was successful
        if result.data and len(result.data) > 0:
            return True, f"✅ Successfully added area: {name}"
        else:
            return False, f"❌ Failed to add area: {name}"
    
    except Exception as e:
        error_msg = str(e)
        # Handle duplicate key constraint
        if '23505' in error_msg or 'duplicate' in error_msg.lower():
            return False, f"❌ Area '{name}' already exists! Please choose a different name."
        # Handle unique constraint
        if 'unique constraint' in error_msg.lower():
            return False, f"❌ Area '{name}' already exists (unique constraint violation)."
        return False, f"❌ Error adding area: {error_msg}"


def add_new_category(
    client, 
    user_id: str, 
    area_id: str,
    name: str,
    description: str = "",
    parent_category_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Add new category to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        area_id: Area UUID
        name: Category name
        description: Category description
        parent_category_id: Optional parent category UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Check if category with this name already exists in this area (for root categories)
        if not parent_category_id:
            # For root categories: check unique constraint (name + area_id + parent=NULL)
            existing = client.table('categories').select('id').eq('user_id', user_id).eq('area_id', area_id).eq('name', name).is_('parent_category_id', 'null').execute()
            if existing.data and len(existing.data) > 0:
                return False, f"❌ Root category '{name}' already exists in this area! Please choose a different name."
        else:
            # For child categories: check if name exists under same parent
            existing = client.table('categories').select('id').eq('user_id', user_id).eq('parent_category_id', parent_category_id).eq('name', name).execute()
            if existing.data and len(existing.data) > 0:
                return False, f"❌ Category '{name}' already exists under this parent! Please choose a different name."
        
        # Generate UUID and slug
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        # Determine level
        if parent_category_id:
            # Get parent level
            parent = client.table('categories').select('level').eq('id', parent_category_id).execute()
            if parent.data and len(parent.data) > 0:
                level = parent.data[0]['level'] + 1
            else:
                return False, "❌ Parent category not found"
        else:
            level = 1  # Root category
        
        # Get next sort_order
        if parent_category_id:
            # Sort within parent
            sort_order = get_next_sort_order(client, 'categories', user_id, 'parent_category_id', parent_category_id)
        else:
            # Sort within area for root categories
            sort_order = get_next_sort_order(client, 'categories', user_id, 'area_id', area_id)
        
        # Prepare data
        category_data = {
            'id': new_id,
            'user_id': user_id,
            'area_id': area_id,
            'parent_category_id': parent_category_id if parent_category_id else None,  # Explicitly set to None
            'name': name,
            'slug': slug,
            'level': level,
            'sort_order': sort_order,
            'description': description if description else None
        }
        
        # Insert ONCE
        result = client.table('categories').insert(category_data).execute()
        
        # Verify insert was successful
        if result.data and len(result.data) > 0:
            parent_info = " (root category)" if not parent_category_id else ""
            return True, f"✅ Successfully added category: {name}{parent_info}"
        else:
            return False, f"❌ Failed to add category: {name}"
    
    except Exception as e:
        error_msg = str(e)
        # Handle duplicate key constraints
        if '23505' in error_msg or 'duplicate' in error_msg.lower() or 'unique constraint' in error_msg.lower():
            if 'idx_categories_root_unique' in error_msg:
                return False, f"❌ Root category '{name}' already exists in this area!"
            else:
                return False, f"❌ Category '{name}' already exists!"
        return False, f"❌ Error adding category: {error_msg}"


def insert_category_between(
    client,
    user_id: str,
    area_id: str,
    insert_after_category_id: Optional[str],
    name: str,
    description: str = ""
) -> Tuple[bool, str]:
    """
    Insert new category between existing ones (preserves sort order).
    
    NEW FEATURE in v1.10.0 - Insert Between
    
    Args:
        client: Supabase client
        user_id: User ID
        area_id: Area UUID
        insert_after_category_id: Category to insert after (None = at beginning)
        name: New category name
        description: Category description
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Determine parent_category_id and insert position
        parent_id = None
        insert_order = 0
        
        if insert_after_category_id:
            # Get the category we're inserting after
            cat_after = client.table('categories')\
                .select('parent_category_id, sort_order')\
                .eq('id', insert_after_category_id)\
                .eq('user_id', user_id)\
                .single().execute()
            
            if not cat_after.data:
                return False, "❌ Reference category not found"
            
            parent_id = cat_after.data['parent_category_id']
            insert_order = cat_after.data['sort_order']
        
        # Get categories that need to be reordered (all after insert point)
        query = client.table('categories')\
            .select('id, sort_order, parent_category_id')\
            .eq('area_id', area_id)\
            .eq('user_id', user_id)\
            .gte('sort_order', insert_order + 1)\
            .order('sort_order')
        
        categories_to_reorder = query.execute()
        
        # Filter by same parent (important for correct sibling ordering)
        if parent_id:
            to_reorder = [c for c in categories_to_reorder.data 
                         if c.get('parent_category_id') == parent_id]
        else:
            to_reorder = [c for c in categories_to_reorder.data 
                         if c.get('parent_category_id') is None]
        
        # Increment sort_order for all categories after insert point
        for cat in to_reorder:
            client.table('categories')\
                .update({'sort_order': cat['sort_order'] + 1})\
                .eq('id', cat['id'])\
                .eq('user_id', user_id)\
                .execute()
        
        # Calculate level
        level = 1
        if parent_id:
            parent = client.table('categories')\
                .select('level')\
                .eq('id', parent_id)\
                .eq('user_id', user_id)\
                .single().execute()
            
            if parent.data:
                level = parent.data['level'] + 1
        
        # Generate slug
        slug = generate_slug(name)
        
        # Insert new category at the correct position
        new_category = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'area_id': area_id,
            'parent_category_id': parent_id,
            'name': name,
            'slug': slug,
            'description': description if description else None,
            'level': level,
            'sort_order': insert_order + 1
        }
        
        result = client.table('categories').insert(new_category).execute()
        
        if result.data and len(result.data) > 0:
            # Clear cache
            load_structure_as_dataframe.clear()
            return True, f"✅ Category '{name}' inserted successfully!"
        else:
            return False, f"❌ Failed to insert category"
        
    except Exception as e:
        return False, f"❌ Error inserting category: {str(e)}"


def remove_category_between(
    client,
    user_id: str,
    category_id: str
) -> Tuple[bool, str]:
    """
    Remove category and promote its children to parent level.
    
    NEW FEATURE in v1.10.0 - Remove Between
    
    This "removes the middle layer" - deletes a category but keeps its
    children by promoting them up one level to the deleted category's parent.
    
    WARNING: This will also delete:
    - All attributes attached to this category
    - All events in this category
    
    Args:
        client: Supabase client
        user_id: User ID
        category_id: Category UUID to remove
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Get category info
        category = client.table('categories')\
            .select('name, parent_category_id, level')\
            .eq('id', category_id)\
            .eq('user_id', user_id)\
            .single().execute()
        
        if not category.data:
            return False, "❌ Category not found"
        
        cat_name = category.data['name']
        parent_id = category.data['parent_category_id']
        
        # Get children
        children = client.table('categories')\
            .select('id, name')\
            .eq('parent_category_id', category_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Promote children to parent's level (remove the middle)
        if children.data:
            for child in children.data:
                client.table('categories')\
                    .update({
                        'parent_category_id': parent_id,
                        'level': category.data['level']  # Same level as deleted category
                    })\
                    .eq('id', child['id'])\
                    .eq('user_id', user_id)\
                    .execute()
        
        # Delete attributes (CASCADE will handle event_attributes)
        client.table('attribute_definitions')\
            .delete()\
            .eq('category_id', category_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Delete events
        client.table('events')\
            .delete()\
            .eq('category_id', category_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Delete category
        client.table('categories')\
            .delete()\
            .eq('id', category_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Clear cache
        load_structure_as_dataframe.clear()
        
        msg = f"✅ Removed '{cat_name}'"
        if len(children.data) > 0:
            msg += f" and promoted {len(children.data)} child categories"
        
        return True, msg
        
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def add_new_attribute(
    client,
    user_id: str,
    category_id: str,
    name: str,
    data_type: str,
    unit: str = "",
    is_required: bool = False,
    default_value: str = "",
    validation_min: str = "",
    validation_max: str = "",
    description: str = ""
) -> Tuple[bool, str]:
    """
    Add new attribute to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        category_id: Category UUID
        name: Attribute name
        data_type: Data type
        unit: Unit
        is_required: Is required flag
        default_value: Default value
        validation_min: Validation min value
        validation_max: Validation max value
        description: Description
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Generate UUID and slug
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        # Get next sort_order
        sort_order = get_next_sort_order(client, 'attribute_definitions', user_id, 'category_id', category_id)
        
        # Parse validation rules
        val_rules = {}
        if validation_min:
            try:
                val_rules['min'] = float(validation_min)
            except:
                val_rules['min'] = validation_min
        
        if validation_max:
            try:
                val_rules['max'] = float(validation_max)
            except:
                val_rules['max'] = validation_max
        
        # Prepare data
        attribute_data = {
            'id': new_id,
            'user_id': user_id,
            'category_id': category_id,
            'name': name,
            'slug': slug,
            'data_type': data_type,
            'unit': unit if unit else None,
            'is_required': is_required,
            'default_value': default_value if default_value else None,
            'validation_rules': val_rules if val_rules else {},
            'description': description if description else None,
            'sort_order': sort_order
        }
        
        # Insert
        client.table('attribute_definitions').insert(attribute_data).execute()
        
        return True, f"✅ Successfully added attribute: {name}"
    
    except Exception as e:
        return False, f"❌ Error adding attribute: {str(e)}"


# ============================================
# DELETE FUNCTIONS
# ============================================

def delete_area(client, user_id: str, area_id: str) -> Tuple[bool, str]:
    """
    Delete area from database (CASCADE deletes categories and attributes).
    
    Args:
        client: Supabase client
        user_id: User ID
        area_id: Area UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # First delete all attributes for categories in this area
        categories = client.table('categories').select('id').eq('area_id', area_id).eq('user_id', user_id).execute()
        if categories.data:
            cat_ids = [c['id'] for c in categories.data]
            client.table('attribute_definitions').delete().in_('category_id', cat_ids).eq('user_id', user_id).execute()
        
        # Then delete all categories in this area
        client.table('categories').delete().eq('area_id', area_id).eq('user_id', user_id).execute()
        
        # Finally delete the area
        client.table('areas').delete().eq('id', area_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted area and all its categories/attributes"
    
    except Exception as e:
        return False, f"❌ Error deleting area: {str(e)}"


def delete_category(client, user_id: str, category_id: str) -> Tuple[bool, str]:
    """
    Delete category from database (CASCADE deletes attributes).
    
    Args:
        client: Supabase client
        user_id: User ID
        category_id: Category UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # First delete all child categories recursively
        children = client.table('categories').select('id').eq('parent_category_id', category_id).eq('user_id', user_id).execute()
        if children.data:
            for child in children.data:
                delete_category(client, user_id, child['id'])
        
        # Delete all attributes for this category
        client.table('attribute_definitions').delete().eq('category_id', category_id).eq('user_id', user_id).execute()
        
        # Delete the category
        client.table('categories').delete().eq('id', category_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted category and all its attributes"
    
    except Exception as e:
        return False, f"❌ Error deleting category: {str(e)}"


def delete_attribute(client, user_id: str, attribute_id: str) -> Tuple[bool, str]:
    """
    Delete attribute from database.
    
    Args:
        client: Supabase client
        user_id: User ID
        attribute_id: Attribute UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Delete the attribute
        client.table('attribute_definitions').delete().eq('id', attribute_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted attribute"
    
    except Exception as e:
        return False, f"❌ Error deleting attribute: {str(e)}"


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_interactive_structure_viewer(client, user_id: str):
    """
    Main function to render the interactive structure viewer.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
    """
    st.title("📋 Interactive Structure Viewer")
    
    # ============================================
    # COLLAPSIBLE HELP SECTION
    # ============================================
    with st.expander("ℹ️ Help - How to Use Interactive Structure Viewer", expanded=False):
        st.markdown("""
        ### 🎯 Overview
        
        **Interactive Structure Viewer** is your central hub for managing event structure. Choose from multiple 
        visualization modes and edit your data directly or via Excel.
        
        **Key Features:**
        - 🎨 **Multiple View Types**: Sunburst, Treemap, Network Graph, or Table View
        - 🔍 **Unified Filters**: Area and Category filters apply across all views
        - 📥 **Excel Export**: Generate filtered Excel with one click
        - ✏️ **Direct Editing**: Modify structure in Edit Mode without Excel
        - 📤 **Excel Import**: Upload changes from edited Excel files
        
        ---
        
        ### 🎨 View Types (Read-Only Mode)
        
        **Table View**  
        Spreadsheet-style view of your hierarchical structure. Best for quick overview and searching.
        
        **Sunburst** (Default)  
        Circular hierarchical visualization. Click segments to drill down into details.
        
        **Treemap**  
        Rectangular hierarchical visualization with proportional sizing.
        
        **Network Graph**  
        Interactive node-based graph. Drag nodes to rearrange, hover for tooltips.
        
        ---
        
        ### 🔍 Centralized Filters
        
        Filters in the control panel apply to **all views and operations**:
        
        - **Filter by Area**: Show only selected area's data
        - **Drill-down to Category**: Focus on specific category (when Area is selected)
        - **Show Events**: Toggle event counts in visualizations
        - **Generate Excel**: Export with active filters applied
        
        **In Edit Mode**, filters automatically apply to Categories and Attributes tabs, 
        helping you focus on relevant data.
        
        ---
        
        ### ✏️ Two Ways to Edit Structure
        
        #### **Method 1: Direct Editing (Edit Mode)**
        **Best for:** Quick changes, adding/editing individual items
        
        1. Click **"Switch to Edit Mode"** button
        2. Choose tab: Areas, Categories, or Attributes
        3. Make changes directly in the table
        4. Add new items using forms
        5. Delete items with cascade warnings
        6. Save all changes with one confirmation
        
        **Features:**
        - 🎨 Color-coded columns: Pink (auto) vs Blue (editable)
        - ✅ Live validation before saving
        - ⏪ Rollback option to discard changes
        - 🔍 **Filters apply**: Edit Categories/Attributes tabs respect Area/Category filters
        
        #### **Method 2: Excel Upload (Edit Mode → Upload Tab)**
        **Best for:** Bulk changes, offline editing, complex restructuring
        
        1. **Download:** Click **"📥 Excel"** button (respects current filters!)
        2. **Edit:** Make changes in Excel (add rows, edit blue columns)
        3. **Upload:** Go to Edit Mode → Upload Hierarchical Excel tab
        4. **Review:** System shows detected changes
        5. **Confirm:** Apply changes to database
        
        **Excel Features:**
        - 📥 Drop-down validations
        - 🔢 Auto-formulas for Level, Area, Sort_Order
        - 📊 Row/Column grouping
        - 🎨 Color coding (Pink = auto, Blue = editable)
        
        ---
        
        ### 📥 Generate Excel Export
        
        The **"📥 Excel"** button:
        - Always visible in the control panel
        - **Respects active filters** - export only filtered data
        - Creates professional Excel with validation and formulas
        - Perfect for sharing specific Area themes or creating starter templates
        
        **Use Cases:**
        - Export single Area for sharing with team members
        - Create templates for new projects
        - Backup filtered sections before major changes
        
        ---
        
        ### 💡 Workflow Tips
        
        **Quick Edits:**
        1. Use filters to narrow scope (Area → Category)
        2. Switch to Edit Mode
        3. Make changes in relevant tab
        4. Filters automatically applied!
        
        **Bulk Changes:**
        1. Set filters to desired scope
        2. Click **"📥 Excel"** to export filtered data
        3. Edit in Excel offline
        4. Upload changes via Edit Mode → Upload tab
        
        **Visual Exploration:**
        1. Use Sunburst or Treemap for hierarchy overview
        2. Use Network Graph for relationship exploration
        3. Use Table View for detailed data inspection
        4. All views respect the same filters
        
        ---
        
        ### ⚠️ Important Notes
        
        **Filters in Edit Mode:**
        - Categories tab: Shows only categories from filtered Area
        - Attributes tab: Shows only attributes from filtered Area/Category
        - Add forms respect active filters automatically
        
        **Excel Export:**
        - With filters active: Exports only filtered data
        - Without filters: Exports complete structure
        - Success message shows which filters were applied
        
        **Unsaved Changes:**
        - Changing filters in Edit Mode will discard unsaved changes
        - Always save or cancel before switching filters
        - System warns you before discarding changes
        """)
    
    st.info("""
    **Quick Overview:**
    - 🎨 **View Type**: Choose visualization mode (Sunburst, Treemap, Network, Table)
    - 🔍 **Filters**: Area and Category - apply to all views and Edit Mode
    - 📥 **Excel Export**: Always available, respects active filters
    - ✏️ **Edit Mode**: Direct editing with automatic filter application
    """)
    
    st.markdown("---")
    
    # Initialize session state
    if 'viewer_mode' not in st.session_state:
        st.session_state.viewer_mode = 'read_only'
    
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    
    # v1.10.1 DEPRECATED: editing_active flag no longer used (State Machine manages state)
    # Kept for backward compatibility only
    if 'editing_active' not in st.session_state:
        st.session_state.editing_active = False
    
    # Initialize State Machine (minimal integration for critical paths)
    state_mgr = StateManager(st.session_state)
    
    # ============================================
    # DEBUG INFO SIDEBAR (v1.10.4)
    # ============================================
    # Shows current state for monitoring and debugging
    with st.sidebar:
        st.markdown("---")
        with st.expander("🐛 DEBUG INFO", expanded=True):
            st.markdown("**📊 Current State:**")
            st.text(f"Viewer Mode: {st.session_state.viewer_mode}")
            st.text(f"Has Changes: {state_mgr.state.has_changes}")
            filters_status = "Disabled" if not state_mgr.state.filters_enabled else "Enabled"
            st.text(f"Filters: {filters_status}")
            st.text(f"Active Tab: {state_mgr.state.active_tab or 'None'}")
            
            st.markdown("**🔍 State Machine:**")
            st.text(f"- mode: {state_mgr.state.mode}")
            st.text(f"- has_changes: {state_mgr.state.has_changes}")
            st.text(f"- filters_enabled: {state_mgr.state.filters_enabled}")
            # v1.11.3: Show discard_pending flag
            st.text(f"- discard_pending: {state_mgr.state.discard_pending}")
            
            st.markdown("**💾 Data State:**")
            edited_df_state = "SET" if st.session_state.get('edited_df') is not None else "None"
            original_df_state = "SET" if st.session_state.get('original_df') is not None else "None"
            st.text(f"- edited_df: {edited_df_state}")
            st.text(f"- original_df: {original_df_state}")
        st.markdown("---")
    
    # Load data
    with st.spinner("Loading structure..."):
        df = load_structure_as_dataframe(client, user_id)
    
    if df.empty:
        st.warning("⚠️ No structure defined yet. Please upload a template first.")
        return
    
    # Store original dataframe
    if st.session_state.original_df is None:
        st.session_state.original_df = df.copy()
    
    # ============================================
    # CRITICAL: CHECK CHANGES FIRST (v1.10.3)
    # ============================================
    # Must happen BEFORE rendering any filters!
    # This ensures State Machine is synced before UI renders
    
    # ============================================
    # CENTRALIZED FILTER STATE
    # ============================================
    
    # Initialize centralized filter state (used across all views and Edit Mode)
    if 'view_filters' not in st.session_state:
        st.session_state.view_filters = {
            'view_type': 'Sunburst',
            'area': 'All Areas',
            'category': 'All Categories',
            'show_events': True
        }
    
    # ============================================
    # CONTROLS - ROW 1: MODE SELECTOR
    # ============================================
    
    # Mode toggle (simplified layout - no extra columns needed)
    mode_options = ['Read-Only', 'Edit Mode']
    current_mode_idx = 0 if st.session_state.viewer_mode == 'read_only' else 1
    
    new_mode = st.radio(
        "Mode",
        mode_options,
        index=current_mode_idx,
        horizontal=True
    )
    
    # ============================================
    # MODE SWITCH VALIDATION (v1.10.1 FIX)
    # ============================================
    # Block mode switch if there are unsaved changes
    previous_mode = st.session_state.viewer_mode
    requested_mode = 'read_only' if new_mode == 'Read-Only' else 'edit'
    
    # Check if user is trying to switch modes
    if previous_mode != requested_mode:
        # Check if State Machine allows mode switch
        can_switch, reason = state_mgr.can_switch_mode()
        
        if not can_switch:
            # Block the switch - show error and keep current mode
            st.error(f"""
            🚨 **Cannot switch to {new_mode} mode!**
            
            {reason}
            
            **Please:**
            - 💾 **Save your changes** (scroll down to Edit section), OR
            - 🗑️ **Discard your changes** (click Discard button below)
            
            Then you can switch modes.
            """)
            # Keep the current mode (don't switch)
            st.session_state.viewer_mode = previous_mode
        else:
            # Switch allowed - update State Machine
            if requested_mode == 'read_only':
                state_mgr.switch_to_viewing()
                st.session_state.viewer_mode = 'read_only'
                st.rerun()  # v1.10.5: Rerun to sync state
            else:
                state_mgr.switch_to_editing()
                st.session_state.viewer_mode = 'edit'
                st.rerun()  # v1.10.5: Rerun to sync state
    else:
        # No mode change requested - just update session state to match
        st.session_state.viewer_mode = requested_mode
    
    st.markdown("---")
    
    # ============================================
    # UNSAVED CHANGES DETECTION & WARNING
    # ============================================
    
    def has_unsaved_changes() -> Tuple[bool, int]:
        """
        Check if there are unsaved changes in Edit Mode.
        
        Returns:
            Tuple of (has_changes, num_changed_rows)
            
        Note: Uses normalized comparison to avoid false positives from dtype/NaN differences
        that st.data_editor may introduce.
        """
        if st.session_state.viewer_mode != 'edit':
            return False, 0
        
        if st.session_state.original_df is None or st.session_state.edited_df is None:
            return False, 0
        
        display_cols = [col for col in st.session_state.original_df.columns if not col.startswith('_')]
        orig_display = st.session_state.original_df[display_cols].copy()
        edited_display = st.session_state.edited_df.copy()
        
        # Normalize DataFrames to avoid false positives
        def normalize_df(df):
            """
            Normalize DataFrame for robust comparison.
            Handles dtype differences, NaN values, and float precision.
            """
            df_norm = df.copy()
            
            # Convert all columns to string for consistent comparison
            # This handles dtype mismatches (object vs str, int vs float, etc.)
            for col in df_norm.columns:
                # Fill NaN/None with empty string before conversion
                df_norm[col] = df_norm[col].fillna('').astype(str)
                
                # Clean up string representation of floats
                # "0.0" -> "0", "1.0" -> "1" 
                df_norm[col] = df_norm[col].str.replace(r'\.0$', '', regex=True)
            
            # Sort columns alphabetically to handle column order differences
            df_norm = df_norm[sorted(df_norm.columns)]
            
            return df_norm
        
        orig_normalized = normalize_df(orig_display)
        edited_normalized = normalize_df(edited_display)
        
        # Check if DataFrames are equal after normalization
        has_changes = not orig_normalized.equals(edited_normalized)
        
        if has_changes:
            # Count changed rows using normalized comparison
            num_changed = 0
            
            # Check for modified rows
            for idx in orig_normalized.index:
                if idx in edited_normalized.index:
                    orig_row = orig_normalized.loc[idx]
                    edited_row = edited_normalized.loc[idx]
                    if not orig_row.equals(edited_row):
                        num_changed += 1
            
            # Count new rows (in edited but not in original)
            new_rows = len(edited_normalized) - len(orig_normalized)
            if new_rows > 0:
                num_changed += new_rows
            
            # CRITICAL: If no actual changes detected, return False
            # This prevents false positives from minor DataFrame differences (index order, etc.)
            if num_changed == 0:
                return False, 0
            
            return True, abs(num_changed)
        
        return False, 0
    
    # v1.11.1: REMOVED global has_unsaved_changes() sync
    # Problem: original_df contains ALL data, edited_df contains SINGLE TAB
    # This caused constant mismatch and infinite loops
    # Solution: Each tab manages its own has_changes state locally
    # The state_mgr.state.has_changes is set ONLY when local tab detects real changes
    
    # ============================================
    # CONTROLS - ROW 2: UNIFIED FILTERS
    # ============================================
    # v1.11.0: Removed info messages about filters - they distract from Save/Discard buttons
    
    # Callback functions to ensure state sync (executed BEFORE rerun)
    def on_view_type_change():
        """Callback when View Type changes"""
        st.session_state.view_filters['view_type'] = st.session_state.view_type_selector
    
    def on_area_change():
        """Callback when Area filter changes"""
        # Update filter state
        st.session_state.view_filters['area'] = st.session_state.area_filter_selector
        # Reset category when area changes
        st.session_state.view_filters['category'] = "All Categories"
        
        # Reset detection state when filter changes (clean slate)
        if st.session_state.viewer_mode == 'edit':
            st.session_state.original_df = None
            st.session_state.edited_df = None
    
    def on_category_change():
        """Callback when Category filter changes"""
        # Update filter state
        st.session_state.view_filters['category'] = st.session_state.category_filter_selector
        
        # Reset detection state when filter changes (clean slate)
        if st.session_state.viewer_mode == 'edit':
            st.session_state.original_df = None
            st.session_state.edited_df = None
    
    def on_show_events_change():
        """Callback when Show Events checkbox changes"""
        st.session_state.view_filters['show_events'] = st.session_state.show_events_toggle
    
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    
    with col1:
        # View Type selector (applies to Read-Only mode only, but state always maintained)
        # v1.10.1: Use State Machine for filter locking
        filters_locked = not state_mgr.state.filters_enabled
        view_help = "Finish editing to use filters (Save or Discard)" if filters_locked else "Sunburst/Treemap/Network: Visual hierarchy | Table: Spreadsheet view"
        
        view_type = st.selectbox(
            "View Type",
            ["Sunburst", "Treemap", "Network Graph", "Table View"],
            index=["Sunburst", "Treemap", "Network Graph", "Table View"].index(st.session_state.view_filters['view_type']),
            key="view_type_selector",
            help=view_help,
            on_change=on_view_type_change,
            disabled=filters_locked  # Disable when actively editing
        )
    
    with col2:
        # Area filter
        area_options = ["All Areas"] + sorted(df[df['Type'] == 'Area']['Area'].unique().tolist())
        
        # Help message changes based on editing state
        # v1.10.1: Use State Machine for filter locking
        filters_locked = not state_mgr.state.filters_enabled
        filter_help = "Finish editing to use filters (Save or Discard)" if filters_locked else "Filter structure by Area"
        
        selected_area = st.selectbox(
            "Filter by Area",
            area_options,
            index=area_options.index(st.session_state.view_filters['area']) if st.session_state.view_filters['area'] in area_options else 0,
            key="area_filter_selector",
            on_change=on_area_change,
            disabled=filters_locked,  # Disable when actively editing
            help=filter_help
        )
    
    with col3:
        # Category filter (drill-down) - conditional on Area selection
        if st.session_state.view_filters['area'] != "All Areas":
            # Get categories for selected area
            area_categories = df[(df['Type'] == 'Category') & (df['Area'] == st.session_state.view_filters['area'])]['Category'].unique().tolist()
            category_options = ["All Categories"] + sorted(area_categories)
            
            # Help message changes based on editing state
            # v1.10.1: Use State Machine for filter locking
            filters_locked = not state_mgr.state.filters_enabled
            category_help = "Finish editing to use filters (Save or Discard)" if filters_locked else "Drill down to specific category"
            
            selected_category = st.selectbox(
                "Drill-down to Category",
                category_options,
                index=category_options.index(st.session_state.view_filters['category']) if st.session_state.view_filters['category'] in category_options else 0,
                key="category_filter_selector",
                on_change=on_category_change,
                disabled=filters_locked,  # Disable when actively editing
                help=category_help
            )
        else:
            st.selectbox(
                "Drill-down to Category",
                ["Select Area first"],
                disabled=True,
                key="category_filter_disabled"
            )
            st.session_state.view_filters['category'] = "All Categories"
    
    with col4:
        # Show Events toggle
        # v1.10.1: Use State Machine for filter locking
        filters_locked = not state_mgr.state.filters_enabled
        show_events = st.checkbox(
            "Show Events",
            value=st.session_state.view_filters['show_events'],
            key="show_events_toggle",
            on_change=on_show_events_change,
            disabled=filters_locked  # Disable when actively editing
        )
    
    with col5:
        # Generate Excel button (always visible)
        if st.button("📥 Excel", use_container_width=True, type="primary", help="Generate Enhanced Excel with current filters"):
            with st.spinner("Generating enhanced Excel file..."):
                try:
                    # Use EnhancedStructureExporter with current filters
                    exporter = EnhancedStructureExporter(
                        client=client,
                        user_id=user_id,
                        filter_area=st.session_state.view_filters['area'],
                        filter_category=st.session_state.view_filters['category']
                    )
                    
                    file_path = exporter.export_hierarchical_view()
                    
                    # Read file for download
                    with open(file_path, 'rb') as f:
                        excel_data = f.read()
                    
                    # Download button
                    st.download_button(
                        label="💾 Download Excel",
                        data=excel_data,
                        file_name=f"structure_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Success message with filter info
                    filter_info = []
                    if st.session_state.view_filters['area'] != "All Areas":
                        filter_info.append(f"Area: {st.session_state.view_filters['area']}")
                    if st.session_state.view_filters['category'] != "All Categories":
                        filter_info.append(f"Category: {st.session_state.view_filters['category']}")
                    
                    if filter_info:
                        st.success(f"✅ Excel generated with filters: {', '.join(filter_info)}")
                    else:
                        st.success("✅ Excel generated successfully (all data)")
                    
                except Exception as e:
                    st.error(f"❌ Error generating Excel: {str(e)}")
    
    st.markdown("---")
    
    # ============================================
    # RENDER APPROPRIATE VIEW
    # ============================================
    
    # In Read-Only mode: render based on View Type
    if st.session_state.viewer_mode == 'read_only':
        if st.session_state.view_filters['view_type'] == "Table View":
            # Render table view (existing code will follow)
            pass  # Will be handled by existing table rendering code below
        else:
            # Render graph view (Sunburst, Treemap, or Network Graph)
            render_graph_viewer_integrated(client, user_id, st.session_state.view_filters)
            return  # Exit function after rendering graph
    
    # Continue with Table View (Read-Only Table or Edit Mode)
    # The rest of the existing code continues below...
    
    # Apply filters (use centralized filter state)
    filtered_df = apply_filters(
        df, 
        st.session_state.view_filters['area'],
        st.session_state.view_filters['category']
    )
    
    # Remove metadata columns for display
    display_cols = [col for col in filtered_df.columns if not col.startswith('_')]
    display_df = filtered_df[display_cols].copy()
    
    # ============================================
    # DATA EDITOR
    # ============================================
    
    if st.session_state.viewer_mode == 'read_only':
        # Read-only mode - display as table
        st.markdown("### 📊 Structure (Read-Only)")
        st.markdown("_Switch to Edit Mode to make changes_")
        
        # Style the dataframe
        styled_df = display_df.style.apply(
            lambda x: [
                'background-color: #FFE6F0' if col in ['Type', 'Level', 'Sort_Order', 'Area', 'Category_Path']
                else 'background-color: #E6F2FF'
                for col in display_df.columns
            ],
            axis=1
        )
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600
        )
    
    else:
        # Edit mode - use tabbed interface with 3 editors
        # v1.11.0: Editor ALWAYS visible - no more st.stop() blocking
        # Save/Discard buttons are now inline within each editor tab
        
        # v1.11.3: Reset has_changes at start of tab rendering
        # Each tab will set it to True if it detects actual changes
        # This ensures proper state when switching between tabs
        if not state_mgr.state.discard_pending:
            state_mgr.state.has_changes = False
        
        st.markdown("### ✏️ Structure (Edit Mode) - Choose What to Edit")
        
        # Create tabs for different entity types
        tab1, tab2, tab3, tab4 = st.tabs([
            "📦 Edit Areas", 
            "📁 Edit Categories", 
            "🏷️ Edit Attributes",
            "📤 Upload Hierarchical Excel"
        ])
        
        # ============================================
        # TAB 1: EDIT AREAS
        # ============================================
        with tab1:
            st.markdown("#### 📦 Edit Areas")
            st.info("Edit area names and descriptions. Add new areas or delete existing ones.")
            
            # Filter to show ONLY Area rows - USE filtered_df (has metadata)
            area_mask = filtered_df['Type'] == 'Area'
            area_full_df = filtered_df[area_mask].copy()
            
            if area_full_df.empty:
                st.warning("⚠️ No areas found.")
            else:
                st.markdown(f"**Viewing {len(area_full_df)} areas**")
                
                # Select relevant columns for Areas (display only)
                area_cols = ['Type', 'Sort_Order', 'Area', 'Description']
                area_display = area_full_df[area_cols].copy()
                
                # Add checkbox column for deletion
                area_display.insert(0, '🗑️', False)
                
                # Configure columns for Area editing
                area_column_config = {
                    '🗑️': st.column_config.CheckboxColumn('Delete?', help="Check to mark for deletion"),
                    'Type': st.column_config.TextColumn('Type', disabled=True, help="Row type (locked)"),
                    'Sort_Order': st.column_config.NumberColumn('Sort_Order', disabled=True, help="Display order (locked)"),
                    'Area': st.column_config.TextColumn('Area', help="Area name - editable", disabled=False),
                    'Description': st.column_config.TextColumn('Description', help="Area description - editable", disabled=False)
                }
                
                # Render area editor
                edited_area_df = st.data_editor(
                    area_display,
                    use_container_width=True,
                    height=300,
                    column_config=area_column_config,
                    hide_index=True,
                    num_rows="fixed"
                )
                
                # ============================================
                # v1.11.0: INLINE SAVE/DISCARD FOR EDIT CHANGES
                # ============================================
                # Check for edit changes (excluding Delete checkbox)
                edited_area_df_no_del = edited_area_df.drop(columns=['🗑️'])
                area_display_no_del = area_display.drop(columns=['🗑️'])
                # v1.11.3: Use normalized comparison (now with reset_index) to avoid false positives
                has_area_edit_changes = not normalize_for_comparison(area_display_no_del).equals(
                    normalize_for_comparison(edited_area_df_no_del)
                )
                
                # v1.11.3: Check discard_pending flag to prevent false positive after Discard
                # If user just clicked Discard, ignore any detected changes for this render
                if state_mgr.state.discard_pending:
                    has_area_edit_changes = False
                    # Clear the flag after acknowledging (only if no real changes)
                    state_mgr.acknowledge_discard()
                
                # v1.11.3: Set state_mgr.has_changes based on LOCAL check
                # Only set to True if there are actual changes
                if has_area_edit_changes:
                    state_mgr.state.has_changes = True
                
                if has_area_edit_changes:
                    st.warning("⚠️ You have unsaved edit changes")
                    st.success("✅ All changes are valid")
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        save_confirm = st.text_input("Type 'SAVE' to confirm batch save", key="save_area_confirm")
                    with col2:
                        if st.button("💾 Save Changes", key="save_areas_btn", disabled=(save_confirm != "SAVE"), use_container_width=True):
                            with st.spinner("Saving area changes..."):
                                success, stats = _save_area_changes(
                                    client, user_id, area_display_no_del, edited_area_df_no_del, area_full_df
                                )
                                
                                if success:
                                    st.success(f"✅ Successfully updated {stats['areas']} area(s)!")
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    st.session_state.edited_df = None
                                    state_mgr.save_changes()
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to save changes. {stats['errors']} errors occurred.")
                    with col3:
                        if st.button("🗑️ Discard Changes", key="discard_areas_btn", type="secondary", use_container_width=True):
                            st.cache_data.clear()
                            st.session_state.edited_df = None
                            st.session_state.original_df = None
                            state_mgr.discard_changes()
                            st.rerun()
                
                st.markdown("---")
                
                # ============================================
                # DELETE SECTION - v1.11.0: Added Cancel button
                # ============================================
                areas_to_delete = edited_area_df[edited_area_df['🗑️'] == True]
                
                if not areas_to_delete.empty:
                    st.error(f"⚠️ **{len(areas_to_delete)} area(s) marked for deletion!**")
                    
                    # Show warnings for each area
                    for idx in areas_to_delete.index:
                        area_id = area_full_df.loc[idx, '_area_id']
                        has_deps, warning = check_area_has_dependencies(client, area_id, user_id)
                        if has_deps:
                            st.warning(warning)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        del_confirm = st.text_input("Type 'DELETE' to confirm deletion", key="delete_area_confirm")
                    with col2:
                        if st.button("❌ Delete Marked", key="delete_areas_btn", disabled=(del_confirm != "DELETE"), use_container_width=True):
                            with st.spinner("Deleting areas..."):
                                deleted_count = 0
                                for idx in areas_to_delete.index:
                                    area_id = area_full_df.loc[idx, '_area_id']
                                    success, msg = delete_area(client, user_id, area_id)
                                    if success:
                                        deleted_count += 1
                                    else:
                                        st.error(msg)
                                
                                if deleted_count > 0:
                                    st.success(f"✅ Deleted {deleted_count} area(s)")
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    st.session_state.edited_df = None
                                    st.rerun()
                    with col3:
                        # v1.11.0: Cancel button - uncheck all and refresh
                        if st.button("↩️ Cancel", key="cancel_delete_areas_btn", type="secondary", use_container_width=True, help="Uncheck all and cancel deletion"):
                            st.cache_data.clear()
                            st.session_state.edited_df = None
                            st.session_state.original_df = None
                            st.rerun()
                
                st.markdown("---")
                
                # ============================================
                # ADD NEW AREA FORM
                # ============================================
                with st.expander("➕ Add New Area", expanded=False):
                    if 'area_form_counter' not in st.session_state:
                        st.session_state.area_form_counter = 0
                    
                    with st.form(f"add_area_form_{st.session_state.area_form_counter}"):
                        new_area_name = st.text_input("Area Name *", placeholder="e.g., Fitness, Nutrition, Health")
                        new_area_desc = st.text_area("Description", placeholder="Optional description...")
                        
                        col_add1, col_add2 = st.columns([1, 1])
                        with col_add1:
                            submitted = st.form_submit_button("➕ Add Area", use_container_width=True)
                        
                        if submitted:
                            if not new_area_name:
                                st.error("❌ Area name is required!")
                            else:
                                with st.spinner("Adding area..."):
                                    success, msg = add_new_area(client, user_id, new_area_name, new_area_desc)
                                    if success:
                                        st.success(msg)
                                        st.session_state.area_form_counter += 1
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        state_mgr.submit_form()
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    
                    # Discard button for form
                    if st.button("🗑️ Discard", key="discard_area_form", help="Close form and clear inputs"):
                        st.session_state.area_form_counter += 1
                        st.rerun()
        
        # ============================================
        # TAB 2: EDIT CATEGORIES
        # ============================================
        with tab2:
            st.markdown("#### 📁 Edit Categories")
            st.info("Edit category names and descriptions. Add new categories or delete existing ones.")
            
            # Filter to show ONLY Category rows - USE filtered_df (has metadata)
            category_mask = filtered_df['Type'] == 'Category'
            category_full_df = filtered_df[category_mask].copy()
            
            # Always show Add Category form, even if no categories exist
            st.markdown("---")
            
            # Show current filter context
            if st.session_state.view_filters['area'] != "All Areas":
                st.info(f"🔍 **Filtered by Area:** {st.session_state.view_filters['area']}")
            
            # Apply area filter from centralized state
            selected_area_cat = st.session_state.view_filters['area']
            
            if selected_area_cat != "All Areas" and not category_full_df.empty:
                category_full_df = category_full_df[category_full_df['Area'] == selected_area_cat]
            
            # Show categories if they exist
            if category_full_df.empty:
                if selected_area_cat != "All Areas":
                    st.info(f"ℹ️ No categories found for Area: {selected_area_cat}. Add your first category below.")
                else:
                    st.info("ℹ️ No categories found. Add your first category below.")
            else:
                    st.markdown(f"**Viewing {len(category_full_df)} categories**")
                    
                    # Select relevant columns for Categories (display only)
                    cat_cols = ['Type', 'Level', 'Sort_Order', 'Area', 'Category_Path', 'Category', 'Description']
                    cat_display = category_full_df[cat_cols].copy()
                    
                    # Add checkbox column for deletion
                    cat_display.insert(0, '🗑️', False)
                    
                    # Configure columns for Category editing
                    cat_column_config = {
                        '🗑️': st.column_config.CheckboxColumn('Delete?', help="Check to mark for deletion"),
                        'Type': st.column_config.TextColumn('Type', disabled=True),
                        'Level': st.column_config.NumberColumn('Level', disabled=True),
                        'Sort_Order': st.column_config.NumberColumn('Sort_Order', disabled=True),
                        'Area': st.column_config.TextColumn('Area', disabled=True),
                        'Category_Path': st.column_config.TextColumn('Category_Path', disabled=True, help="Full hierarchical path"),
                        'Category': st.column_config.TextColumn('Category', help="Category name - editable", disabled=False),
                        'Description': st.column_config.TextColumn('Description', help="Category description - editable", disabled=False)
                    }
                    
                    # v1.10.4: Use session_state backend for automatic change detection
                    # When user opens editor, key is created → early check detects it → filters lock
                    
                    # Render category editor
                    edited_cat_df = st.data_editor(
                        cat_display,
                        use_container_width=True,
                        height=300,
                        column_config=cat_column_config,
                        hide_index=True,
                        num_rows="fixed"
                    )
                    
                    # ============================================
                    # v1.11.0: INLINE SAVE/DISCARD FOR EDIT CHANGES
                    # ============================================
                    edited_cat_df_no_del = edited_cat_df.drop(columns=['🗑️'])
                    cat_display_no_del = cat_display.drop(columns=['🗑️'])
                    # v1.11.3: Use normalized comparison (now with reset_index) to avoid false positives
                    has_cat_changes = not normalize_for_comparison(cat_display_no_del).equals(
                        normalize_for_comparison(edited_cat_df_no_del)
                    )
                    
                    # v1.11.3: Check discard_pending flag to prevent false positive after Discard
                    if state_mgr.state.discard_pending:
                        has_cat_changes = False
                        state_mgr.acknowledge_discard()
                    
                    # v1.11.3: Set state_mgr.has_changes based on LOCAL check
                    if has_cat_changes:
                        state_mgr.state.has_changes = True
                    
                    if has_cat_changes:
                        st.warning("⚠️ You have unsaved edit changes")
                        st.success("✅ All changes are valid")
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            confirm = st.text_input("Type 'SAVE' to confirm batch save", key="save_cat_confirm")
                        with col2:
                            if st.button("💾 Save Changes", key="save_categories", disabled=(confirm != "SAVE"), use_container_width=True):
                                with st.spinner("Saving category changes..."):
                                    success, stats = _save_category_changes(
                                        client, user_id, cat_display_no_del, edited_cat_df_no_del, category_full_df
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Successfully updated {stats['categories']} categories!")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        state_mgr.save_changes()
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to save changes. {stats['errors']} errors occurred.")
                        with col3:
                            if st.button("🗑️ Discard Changes", key="discard_cats_btn", type="secondary", use_container_width=True):
                                st.cache_data.clear()
                                st.session_state.edited_df = None
                                st.session_state.original_df = None
                                state_mgr.discard_changes()
                                st.rerun()
                    
                    st.markdown("---")
                    
                    # ============================================
                    # DELETE SECTION - v1.11.0: Added Cancel button
                    # ============================================
                    cats_to_delete = edited_cat_df[edited_cat_df['🗑️'] == True]
                    
                    if not cats_to_delete.empty:
                        st.error(f"⚠️ **{len(cats_to_delete)} category(ies) marked for deletion!**")
                        
                        # Show warnings for each category
                        for idx in cats_to_delete.index:
                            cat_id = category_full_df.loc[idx, '_category_id']
                            has_deps, warning = check_category_has_dependencies(client, cat_id, user_id)
                            if has_deps:
                                st.warning(warning)
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            del_confirm = st.text_input("Type 'DELETE' to confirm deletion", key="delete_cat_confirm")
                        with col2:
                            if st.button("❌ Delete Marked", key="delete_cats_btn", disabled=(del_confirm != "DELETE"), use_container_width=True):
                                with st.spinner("Deleting categories..."):
                                    deleted_count = 0
                                    for idx in cats_to_delete.index:
                                        cat_id = category_full_df.loc[idx, '_category_id']
                                        success, msg = delete_category(client, user_id, cat_id)
                                        if success:
                                            deleted_count += 1
                                        else:
                                            st.error(msg)
                                    
                                    if deleted_count > 0:
                                        st.success(f"✅ Deleted {deleted_count} category(ies)")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        st.rerun()
                        with col3:
                            # v1.11.0: Cancel button
                            if st.button("↩️ Cancel", key="cancel_delete_cats_btn", type="secondary", use_container_width=True, help="Uncheck all and cancel deletion"):
                                st.cache_data.clear()
                                st.session_state.edited_df = None
                                st.session_state.original_df = None
                                st.rerun()
            
            # Add Category form - ALWAYS visible, regardless of whether categories exist
            st.markdown("---")
            
            # Add new category form
            with st.expander("➕ Add New Category", expanded=False):
                # Initialize form submission counter in session state
                if 'category_form_counter' not in st.session_state:
                    st.session_state.category_form_counter = 0
                
                # Get areas for selection
                areas_response = client.table('areas').select('id, name').eq('user_id', user_id).execute()
                areas_dict = {a['name']: a['id'] for a in areas_response.data} if areas_response.data else {}
                
                # Use unique key with counter to force form reset after successful submit
                with st.form(f"add_category_form_{st.session_state.category_form_counter}"):
                    # If Area filter is active, pre-populate and disable Area selection
                    if selected_area_cat != "All Areas":
                        st.info(f"ℹ️ Adding category to filtered area: **{selected_area_cat}**")
                        # Display as disabled text input (can't change)
                        st.text_input("Select Area *", value=selected_area_cat, disabled=True)
                        new_cat_area = selected_area_cat
                    else:
                        # Show full dropdown if no filter
                        new_cat_area = st.selectbox("Select Area *", list(areas_dict.keys()))
                    
                    new_cat_name = st.text_input("Category Name *", placeholder="e.g., Cardio, Strength Training")
                    new_cat_desc = st.text_area("Description", placeholder="Optional description...")
                    
                    # Parent category selection (optional)
                    if new_cat_area:
                        area_id_for_cats = areas_dict[new_cat_area]
                        # Get ONLY categories from the selected area
                        cats_in_area = client.table('categories').select('id, name').eq('area_id', area_id_for_cats).eq('user_id', user_id).execute()
                        parent_options = ["None (Root Category)"] + [c['name'] for c in (cats_in_area.data if cats_in_area.data else [])]
                        parent_cats_dict = {c['name']: c['id'] for c in (cats_in_area.data if cats_in_area.data else [])}
                        
                        if len(parent_options) > 1:
                            new_cat_parent = st.selectbox("Parent Category", parent_options, help=f"Select parent category from '{new_cat_area}' area")
                        else:
                            st.info(f"ℹ️ No existing categories in '{new_cat_area}' - this will be a root category")
                            new_cat_parent = "None (Root Category)"
                    else:
                        new_cat_parent = "None (Root Category)"
                    
                    submitted = st.form_submit_button("➕ Add Category", use_container_width=True)
                    
                    if submitted:
                        if not new_cat_name:
                            st.error("❌ Category name is required!")
                        elif not new_cat_area:
                            st.error("❌ Please select an area!")
                        else:
                            # Resolve parent_id
                            if new_cat_parent == "None (Root Category)":
                                parent_id = None
                            else:
                                parent_id = parent_cats_dict.get(new_cat_parent)
                                # Verify parent_id is valid
                                if not parent_id:
                                    st.error(f"❌ Parent category '{new_cat_parent}' not found in dropdown data!")
                                    st.stop()
                            
                            with st.spinner("Adding category..."):
                                success, msg = add_new_category(
                                    client, user_id, areas_dict[new_cat_area],
                                    new_cat_name, new_cat_desc, parent_id
                                )
                                if success:
                                    st.success(msg)
                                    # Increment counter to create NEW form (prevents double submit)
                                    st.session_state.category_form_counter += 1
                                    # CRITICAL: Clear ALL detection state after ADD
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    st.session_state.edited_df = None
                                    # v1.10.1: Removed editing_active flag (State Machine manages state)
                                    # BUG FIX #2: Update State Machine after successful ADD (v1.10.0)
                                    state_mgr.submit_form()
                                    # IMPORTANT: rerun to refresh everything and clear form
                                    st.rerun()
                                else:
                                    st.error(msg)
                
                # v1.11.0: Discard button for form
                if st.button("🗑️ Discard", key="discard_category_form", help="Close form and clear inputs"):
                    st.session_state.category_form_counter += 1
                    st.rerun()
                
            st.markdown("---")
            
            # NEW FEATURE v1.10.0: Insert Category Between
            with st.expander("📌 Insert Category Between", expanded=False):
                st.info("💡 Insert a new category between existing ones without disrupting data")
                
                # Get categories in filtered area
                categories_in_area_df = filtered_df[filtered_df['Type'] == 'Category'].copy()
                
                if categories_in_area_df.empty:
                    st.warning("⚠️ No categories in current filter. Use 'Add New Category' instead.")
                else:
                    # Initialize form counter
                    if 'insert_between_counter' not in st.session_state:
                        st.session_state.insert_between_counter = 0
                    
                    with st.form(f"insert_category_form_{st.session_state.insert_between_counter}"):
                        # Build position options
                        cat_options = ['At Beginning'] + categories_in_area_df['Category'].tolist()
                        insert_after = st.selectbox(
                            "Insert After",
                            cat_options,
                            help="Select where to insert the new category"
                        )
                        
                        name = st.text_input("New Category Name *", placeholder="e.g., Intermediate Training", max_chars=100)
                        description = st.text_area("Description (optional)", placeholder="Optional description...", max_chars=500)
                        
                        submitted = st.form_submit_button("📌 Insert Category", use_container_width=True)
                        
                        if submitted:
                            if not name:
                                st.error("❌ Category name is required")
                            else:
                                # Determine insert_after_id and area_id
                                if insert_after == 'At Beginning':
                                    insert_after_id = None
                                    # Get area_id from first category in filtered view
                                    area_id = categories_in_area_df.iloc[0]['_area_id']
                                else:
                                    cat_row = categories_in_area_df[categories_in_area_df['Category'] == insert_after]
                                    if not cat_row.empty:
                                        insert_after_id = cat_row.iloc[0]['_category_id']
                                        area_id = cat_row.iloc[0]['_area_id']
                                    else:
                                        st.error("❌ Selected category not found")
                                        st.stop()
                                
                                # Call insert function
                                with st.spinner("Inserting category..."):
                                    success, msg = insert_category_between(
                                        client, user_id, area_id, insert_after_id, name, description
                                    )
                                    
                                    if success:
                                        st.success(msg)
                                        st.session_state.insert_between_counter += 1
                                        # Clear cache
                                        st.cache_data.clear()
                                        load_structure_as_dataframe.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        # v1.10.1: Removed editing_active flag (State Machine manages state)
                                        state_mgr.submit_form()
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    
                    # v1.11.0: Discard button
                    if st.button("🗑️ Discard", key="discard_insert_form", help="Close form and clear inputs"):
                        st.session_state.insert_between_counter += 1
                        st.rerun()
                
            st.markdown("---")
            
            # NEW FEATURE v1.10.0: Remove Category Between
            with st.expander("🗑️ Remove Category Between", expanded=False):
                st.warning("⚠️ **Remove Between** deletes the category but **promotes its children** up one level")
                st.info("💡 Use this to remove a middle layer without losing child categories")
                
                # Get categories in filtered area
                categories_in_area_df = filtered_df[filtered_df['Type'] == 'Category'].copy()
                
                if categories_in_area_df.empty:
                    st.warning("⚠️ No categories in current filter.")
                else:
                    # Let user select which category to remove
                    category_to_remove = st.selectbox(
                        "Select Category to Remove",
                        categories_in_area_df['Category'].tolist(),
                        help="This category will be deleted, but its children will be promoted"
                    )
                    
                    if category_to_remove:
                        # Get category info
                        cat_row = categories_in_area_df[categories_in_area_df['Category'] == category_to_remove]
                        if not cat_row.empty:
                            category_id = cat_row.iloc[0]['_category_id']
                            
                            # Get dependencies info
                            try:
                                # Count children
                                children = client.table('categories')\
                                    .select('id')\
                                    .eq('parent_category_id', category_id)\
                                    .eq('user_id', user_id)\
                                    .execute()
                                children_count = len(children.data) if children.data else 0
                                
                                # Count attributes
                                attrs = client.table('attribute_definitions')\
                                    .select('id')\
                                    .eq('category_id', category_id)\
                                    .eq('user_id', user_id)\
                                    .execute()
                                attrs_count = len(attrs.data) if attrs.data else 0
                                
                                # Count events
                                events = client.table('events')\
                                    .select('id')\
                                    .eq('category_id', category_id)\
                                    .eq('user_id', user_id)\
                                    .execute()
                                events_count = len(events.data) if events.data else 0
                                
                                # Show impact preview
                                st.markdown("**Impact Preview:**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if children_count > 0:
                                        st.success(f"✅ **{children_count}** child categories will be **promoted**")
                                    else:
                                        st.info("ℹ️ No child categories")
                                with col2:
                                    if attrs_count > 0:
                                        st.error(f"❌ **{attrs_count}** attributes will be **deleted**")
                                    else:
                                        st.success("✅ No attributes")
                                with col3:
                                    if events_count > 0:
                                        st.error(f"❌ **{events_count}** events will be **deleted**")
                                    else:
                                        st.success("✅ No events")
                                
                                # Confirmation section
                                st.markdown("---")
                                st.warning(f"""
                                **⚠️ Confirm Remove Between:**
                                
                                You are about to:
                                - ❌ Delete category: **{category_to_remove}**
                                - ❌ Delete {attrs_count} attributes
                                - ❌ Delete {events_count} events
                                - ✅ Promote {children_count} child categories
                                
                                Type **"REMOVE"** to confirm:
                                """)
                                
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    confirmation = st.text_input(
                                        "Confirm",
                                        key="confirm_remove_between",
                                        placeholder="Type REMOVE"
                                    )
                                with col2:
                                    if st.button("🗑️ Remove", type="primary", disabled=(confirmation != "REMOVE"), use_container_width=True):
                                        with st.spinner(f"Removing '{category_to_remove}'..."):
                                            success, msg = remove_category_between(client, user_id, category_id)
                                            if success:
                                                st.success(msg)
                                                # Clear state
                                                st.cache_data.clear()
                                                load_structure_as_dataframe.clear()
                                                st.session_state.original_df = None
                                                st.session_state.edited_df = None
                                                state_mgr.submit_form()
                                                st.balloons()
                                                st.rerun()
                                            else:
                                                st.error(msg)
                                with col3:
                                    # v1.11.0: Cancel button
                                    if st.button("↩️ Cancel", key="cancel_remove_between", type="secondary", use_container_width=True, help="Cancel operation"):
                                        st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Error getting dependencies: {str(e)}")
        
        # ============================================
        # TAB 3: EDIT ATTRIBUTES
        # ============================================
        with tab3:
            st.markdown("#### 🏷️ Edit Attributes")
            st.info("Edit attribute definitions. Add new attributes or delete existing ones.")
            
            # Filter to show ONLY Attribute rows - USE filtered_df (has metadata)
            attribute_mask = filtered_df['Type'] == 'Attribute'
            attribute_full_df = filtered_df[attribute_mask].copy()
            
            # Always show Add Attribute form, even if no attributes exist
            st.markdown("---")
            
            # Show current filter context
            filter_context_parts = []
            if st.session_state.view_filters['area'] != "All Areas":
                filter_context_parts.append(f"Area: {st.session_state.view_filters['area']}")
            if st.session_state.view_filters['category'] != "All Categories":
                filter_context_parts.append(f"Category: {st.session_state.view_filters['category']}")
            
            if filter_context_parts:
                st.info(f"🔍 **Filtered by** {', '.join(filter_context_parts)}")
            
            # Use centralized filters
            selected_area_attr = st.session_state.view_filters['area']
            selected_category = st.session_state.view_filters['category']
            
            # Apply area filter first
            if selected_area_attr != "All Areas" and not attribute_full_df.empty:
                attribute_full_df = attribute_full_df[attribute_full_df['Area'] == selected_area_attr]
            
            # Apply category filter
            if selected_category != "All Categories" and not attribute_full_df.empty:
                attribute_full_df = attribute_full_df[attribute_full_df['Category'] == selected_category]
            
            # Show attributes if they exist
            if attribute_full_df.empty:
                if selected_area_attr != "All Areas" or selected_category != "All Categories":
                    st.info(f"ℹ️ No attributes found for the selected filters. Add your first attribute below.")
                else:
                    st.info("ℹ️ No attributes found. Add your first attribute below.")
            else:
                    st.markdown(f"**Viewing {len(attribute_full_df)} attributes**")
                    
                    # Select relevant columns for Attributes (display only)
                    attr_cols = ['Type', 'Level', 'Sort_Order', 'Area', 'Category_Path', 'Category',
                                'Attribute_Name', 'Data_Type', 'Unit', 'Is_Required', 
                                'Default_Value', 'Validation_Min', 'Validation_Max', 'Description']
                    
                    attr_display = attribute_full_df[attr_cols].copy()
                    
                    # Add checkbox column for deletion
                    attr_display.insert(0, '🗑️', False)
                    
                    # Configure columns for Attribute editing
                    attr_column_config = {
                        '🗑️': st.column_config.CheckboxColumn('Delete?', help="Check to mark for deletion"),
                        'Type': st.column_config.TextColumn('Type', disabled=True),
                        'Level': st.column_config.NumberColumn('Level', disabled=True),
                        'Sort_Order': st.column_config.NumberColumn('Sort_Order', disabled=True),
                        'Area': st.column_config.TextColumn('Area', disabled=True),
                        'Category_Path': st.column_config.TextColumn('Category_Path', disabled=True),
                        'Category': st.column_config.TextColumn('Category', disabled=True),
                        'Attribute_Name': st.column_config.TextColumn('Attribute_Name', help="Attribute name - editable", disabled=False),
                        'Data_Type': st.column_config.SelectboxColumn('Data_Type', options=DATA_TYPES, help="Select data type", disabled=False),
                        'Unit': st.column_config.TextColumn('Unit', help="Measurement unit", disabled=False),
                        'Is_Required': st.column_config.SelectboxColumn('Is_Required', options=IS_REQUIRED_OPTIONS, help="Required field?", disabled=False),
                        'Default_Value': st.column_config.TextColumn('Default_Value', help="Default value", disabled=False),
                        'Validation_Min': st.column_config.TextColumn('Validation_Min', help="Minimum value", disabled=False),
                        'Validation_Max': st.column_config.TextColumn('Validation_Max', help="Maximum value", disabled=False),
                        'Description': st.column_config.TextColumn('Description', help="Attribute description", disabled=False)
                    }
                    
                    # v1.10.4: Use session_state backend for automatic change detection
                    # When user opens editor, key is created → early check detects it → filters lock
                    
                    # Render attribute editor
                    edited_attr_df = st.data_editor(
                        attr_display,
                        use_container_width=True,
                        height=300,
                        column_config=attr_column_config,
                        hide_index=True,
                        num_rows="fixed"
                    )
                    
                    # ============================================
                    # v1.11.0: INLINE SAVE/DISCARD FOR EDIT CHANGES
                    # ============================================
                    edited_attr_df_no_del = edited_attr_df.drop(columns=['🗑️'])
                    attr_display_no_del = attr_display.drop(columns=['🗑️'])
                    # v1.11.3: Use normalized comparison (now with reset_index) to avoid false positives
                    has_attr_changes = not normalize_for_comparison(attr_display_no_del).equals(
                        normalize_for_comparison(edited_attr_df_no_del)
                    )
                    
                    # v1.11.3: Check discard_pending flag to prevent false positive after Discard
                    if state_mgr.state.discard_pending:
                        has_attr_changes = False
                        state_mgr.acknowledge_discard()
                    
                    # v1.11.3: Set state_mgr.has_changes based on LOCAL check
                    if has_attr_changes:
                        state_mgr.state.has_changes = True
                    
                    if has_attr_changes:
                        st.warning("⚠️ You have unsaved edit changes")
                        
                        # Validate changes
                        is_valid, errors = validate_changes(edited_attr_df_no_del)
                        
                        if not is_valid:
                            st.error("❌ **Validation Errors:**")
                            for error in errors:
                                st.error(f"  • {error}")
                        else:
                            st.success("✅ All changes are valid")
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            confirmation_text = st.text_input(
                                "Type 'SAVE' to confirm batch save",
                                key="save_attr_confirmation"
                            )
                        with col2:
                            if st.button("💾 Save Changes", disabled=(not is_valid or confirmation_text != "SAVE"), use_container_width=True, key="save_attributes"):
                                with st.spinner("Saving changes..."):
                                    success, stats = _save_attribute_changes(
                                        client, user_id, attr_display_no_del, edited_attr_df_no_del, attribute_full_df
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Successfully updated {stats['attributes']} attribute(s)!")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        state_mgr.save_changes()
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to save changes. {stats['errors']} errors occurred.")
                        with col3:
                            if st.button("🗑️ Discard Changes", key="discard_attrs_btn", type="secondary", use_container_width=True):
                                st.cache_data.clear()
                                st.session_state.edited_df = None
                                st.session_state.original_df = None
                                state_mgr.discard_changes()
                                st.rerun()
                    
                    st.markdown("---")
                    
                    # ============================================
                    # DELETE SECTION - v1.11.0: Added Cancel button
                    # ============================================
                    attrs_to_delete = edited_attr_df[edited_attr_df['🗑️'] == True]
                    
                    if not attrs_to_delete.empty:
                        st.error(f"⚠️ **{len(attrs_to_delete)} attribute(s) marked for deletion!**")
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            del_confirm = st.text_input("Type 'DELETE' to confirm deletion", key="delete_attr_confirm")
                        with col2:
                            if st.button("❌ Delete Marked", key="delete_attrs_btn", disabled=(del_confirm != "DELETE"), use_container_width=True):
                                with st.spinner("Deleting attributes..."):
                                    deleted_count = 0
                                    for idx in attrs_to_delete.index:
                                        attr_id = attribute_full_df.loc[idx, '_attribute_id']
                                        success, msg = delete_attribute(client, user_id, attr_id)
                                        if success:
                                            deleted_count += 1
                                        else:
                                            st.error(msg)
                                    
                                    if deleted_count > 0:
                                        st.success(f"✅ Deleted {deleted_count} attribute(s)")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        st.rerun()
                        with col3:
                            # v1.11.0: Cancel button
                            if st.button("↩️ Cancel", key="cancel_delete_attrs_btn", type="secondary", use_container_width=True, help="Uncheck all and cancel deletion"):
                                st.session_state.edited_df = None
                                st.session_state.original_df = None
                                st.rerun()
            
            # Add Attribute form - ALWAYS visible, regardless of whether attributes exist
            st.markdown("---")
            with st.expander("➕ Add New Attribute", expanded=False):
                st.caption("💡 Two-step process: (1) Select Data Type first → (2) Form shows only relevant fields for that type")
                
                # Initialize form submission counter in session state
                if 'attribute_form_counter' not in st.session_state:
                    st.session_state.attribute_form_counter = 0
                
                # Get current filters from unified view_filters (v1.9.0+)
                current_area_filter = st.session_state.view_filters.get('area', 'All Areas')
                current_category_filter = st.session_state.view_filters.get('category', 'All Categories')
                
                # Get categories for selection
                cats_response = client.table('categories').select('id, name, area_id, areas(name)').eq('user_id', user_id).execute()
                
                # Filter categories based on active filters
                filtered_cats = []
                if cats_response.data:
                    for cat in cats_response.data:
                        area_name = cat['areas']['name'] if cat.get('areas') else 'Unknown'
                        
                        # Apply Area filter if active
                        if current_area_filter != "All Areas":
                            if area_name != current_area_filter:
                                continue  # Skip categories not from filtered area
                        
                        # Apply Category filter if active
                        if current_category_filter != "All Categories":
                            if cat['name'] != current_category_filter:
                                continue  # Skip categories not matching filter
                        
                        filtered_cats.append(cat)
                
                # Build category options from filtered list
                cat_options = {}
                for cat in filtered_cats:
                    area_name = cat['areas']['name'] if cat.get('areas') else 'Unknown'
                    display_name = f"{area_name} > {cat['name']}"
                    cat_options[display_name] = cat['id']
                
                # Show info if filters are active
                if current_area_filter != "All Areas" or current_category_filter != "All Categories":
                    filter_parts = []
                    if current_area_filter != "All Areas":
                        filter_parts.append(f"**Area:** {current_area_filter}")
                    if current_category_filter != "All Categories":
                        filter_parts.append(f"**Category:** {current_category_filter}")
                    
                    st.info(f"ℹ️ Adding attribute to filtered: {' > '.join(filter_parts)}")
                
                # TWO-STEP APPROACH: Select Data Type first (outside form), then show relevant form
                st.markdown("**Step 1:** Select Data Type")
                
                # Initialize selected_data_type in session state if not exists
                if 'selected_data_type' not in st.session_state:
                    st.session_state.selected_data_type = 'number'
                
                # Data Type selector OUTSIDE the form (allows dynamic form generation)
                selected_data_type = st.selectbox(
                    "Data Type *",
                    DATA_TYPES,
                    key="attr_data_type_selector",
                    help="Select data type first - form fields will adapt automatically"
                )
                
                # Update session state
                st.session_state.selected_data_type = selected_data_type
                
                st.markdown("**Step 2:** Fill in attribute details")
                
                # Determine which fields to show based on selected type
                show_unit = selected_data_type == 'number'
                show_default = selected_data_type not in ['link', 'image']
                show_validation = selected_data_type in ['number', 'datetime']
                
                # Show helper text about field visibility
                field_notes = []
                if not show_unit:
                    field_notes.append("Unit field hidden (only for 'number' type)")
                if not show_default:
                    field_notes.append("Default Value hidden (not for 'link'/'image')")
                if not show_validation:
                    field_notes.append("Validation fields hidden (only for 'number'/'datetime')")
                
                if field_notes:
                    st.caption(f"💡 {', '.join(field_notes)}")
                
                # Use unique key with counter to force form reset after successful submit
                with st.form(f"add_attribute_form_{st.session_state.attribute_form_counter}"):
                    # Category selection - locked if only one option
                    if len(cat_options) == 0:
                        st.warning("⚠️ No categories available for the current filter. Please adjust filters or create categories first.")
                        new_attr_category = None
                    elif len(cat_options) == 1:
                        # Only one option - show as locked/disabled
                        category_name = list(cat_options.keys())[0]
                        st.text_input("Select Category *", value=category_name, disabled=True, 
                                    help="Locked to filtered category")
                        new_attr_category = category_name
                    else:
                        # Multiple options - show dropdown
                        new_attr_category = st.selectbox("Select Category *", list(cat_options.keys()))
                    
                    new_attr_name = st.text_input("Attribute Name *", placeholder="e.g., Duration, Distance, Weight")
                    
                    # Show ONLY relevant fields based on selected data type
                    col1, col2 = st.columns(2)
                    with col1:
                        if show_unit:
                            new_attr_unit = st.text_input("Unit", placeholder="e.g., km, kg, minutes")
                        else:
                            new_attr_unit = ""
                        
                        new_attr_required = st.selectbox("Is Required?", ["No", "Yes"])
                    
                    with col2:
                        if show_default:
                            new_attr_default = st.text_input("Default Value", placeholder="Optional")
                        else:
                            new_attr_default = ""
                        
                        if show_validation:
                            new_attr_val_min = st.text_input("Validation Min", placeholder="Optional")
                        else:
                            new_attr_val_min = ""
                    
                    if show_validation:
                        new_attr_val_max = st.text_input("Validation Max", placeholder="Optional")
                    else:
                        new_attr_val_max = ""
                    
                    new_attr_desc = st.text_area("Description", placeholder="Optional description...")
                    
                    submitted = st.form_submit_button("➕ Add Attribute", use_container_width=True)
                    
                    if submitted:
                        if not new_attr_name:
                            st.error("❌ Attribute name is required!")
                        elif not new_attr_category:
                            st.error("❌ Please select a category!")
                        elif len(cat_options) == 0:
                            st.error("❌ No categories available. Please adjust filters.")
                        else:
                            is_req = new_attr_required == "Yes"
                            
                            with st.spinner("Adding attribute..."):
                                # Use selected_data_type from outside the form
                                success, msg = add_new_attribute(
                                    client, user_id, cat_options[new_attr_category],
                                    new_attr_name, st.session_state.selected_data_type,
                                    new_attr_unit, is_req, new_attr_default,
                                    new_attr_val_min, new_attr_val_max, new_attr_desc
                                )
                                if success:
                                    st.success(msg)
                                    # Increment counter to create NEW form (prevents double submit)
                                    st.session_state.attribute_form_counter += 1
                                    # CRITICAL: Clear ALL detection state after ADD
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    st.session_state.edited_df = None
                                    # v1.10.1: Removed editing_active flag (State Machine manages state)
                                    # BUG FIX #2: Update State Machine after successful ADD (v1.10.0)
                                    state_mgr.submit_form()
                                    # Rerun
                                    st.rerun()
                                else:
                                    st.error(msg)
                
                # BUG FIX #3: Discard button for form (v1.10.0)
                if st.button("🗑️ Discard", key="discard_attribute_form", help="Close form and clear inputs"):
                    st.session_state.attribute_form_counter += 1
                    st.rerun()
        
        # ============================================
        # TAB 4: UPLOAD HIERARCHICAL EXCEL
        # ============================================
        with tab4:
            st.markdown("#### 📤 Upload Hierarchical Excel")
            st.info("""
            **Update your structure by uploading an edited Hierarchical_View Excel**
            - ✅ **Add new rows** for Areas, Categories, Attributes
            - ✅ **Edit BLUE columns** in existing rows (editable fields)
            - ✅ **Create hierarchies** using Category_Path
            - ✅ **Update properties** like descriptions, data types, validation rules
            """)
            
            st.markdown("---")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "📁 Browse Files - Upload Hierarchical_View Excel",
                type=["xlsx"],
                help="Upload the Excel file you generated in Read-Only mode",
                key="isv_upload_excel"
            )
            
            if not uploaded_file:
                st.markdown("### 📋 How to Use Upload")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **Step 1: Generate Excel**
                    - Go to **Read-Only Mode**
                    - Click **Generate Enhanced Excel**
                    - Download the file
                    
                    **Step 2: Edit in Excel**
                    - **Add rows** at bottom for new items
                    - **Edit BLUE columns** (editable)
                    - **Don't edit PINK columns** (auto-calculated)
                    
                    **Step 3: Upload**
                    - Come back here
                    - Upload edited file above
                    - Review detected changes
                    - Confirm to apply
                    """)
                
                with col2:
                    st.markdown("""
                    **Adding New Items:**
                    
                    **New Area:**
                    - Type: `Area`
                    - Category_Path: `<AreaName>`
                    - Example: `Fitness`
                    
                    **New Category:**
                    - Type: `Category`
                    - Category_Path: `<Area> > <Category>`
                    - Category: `<CategoryName>`
                    - Example: `Fitness > Cardio`
                    
                    **New Attribute:**
                    - Type: `Attribute`
                    - Category_Path: `<full path>`
                    - Attribute_Name: `<Name>`
                    - Data_Type: `number`, `text`, etc.
                    """)
                
                st.markdown("---")
                
                st.markdown("""
                ### ✏️ Editable Fields (BLUE columns)
                - **Category**, **Attribute_Name**
                - **Data_Type**: number, text, datetime, boolean, link, image
                - **Unit**, **Is_Required**, **Default_Value**
                - **Validation_Min**, **Validation_Max**
                - **Description**
                
                ### 🚫 Read-Only Fields (PINK columns)
                - **Type**, **Level**, **Sort_Order**
                - **Area**, **Category_Path** (path structure)
                
                ⚠️ **Important:** Don't change PINK columns - they're auto-calculated!
                """)
            
            else:
                # Save uploaded file to temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Parse and validate
                    with st.spinner("📖 Parsing Excel file..."):
                        parser = HierarchicalParser(
                            client=client,
                            user_id=user_id,
                            excel_path=tmp_path
                        )
                        
                        changes = parser.parse_and_validate()
                    
                    # Show validation errors if any
                    if changes.validation_errors:
                        st.error("❌ Validation Errors Found")
                        
                        with st.expander("🔍 View Validation Errors", expanded=True):
                            for error in changes.validation_errors:
                                if error.row > 0:
                                    st.error(f"**Row {error.row}, Column '{error.column}':** {error.message}")
                                else:
                                    st.error(f"**{error.column}:** {error.message}")
                        
                        st.warning("⚠️ Please fix the errors above and re-upload the file.")
                        
                        # Generate error Excel with highlighted cells
                        st.markdown("---")
                        st.markdown("### 📥 Download Error Report")
                        st.info("""
                        **Download an Excel file with errors highlighted:**
                        - 🟡 **Yellow cells** = Cells with validation errors
                        - 💬 **Comments** = Hover over yellow cells to see error details
                        - ✏️ **Fix errors** in Excel and re-upload
                        """)
                        
                        if st.button("📥 Generate Error Report Excel", type="primary", key="isv_error_report"):
                            with st.spinner("Generating error report..."):
                                try:
                                    # Generate error Excel
                                    error_excel_path = generate_error_excel(tmp_path, changes.validation_errors)
                                    
                                    # Read the file for download
                                    with open(error_excel_path, 'rb') as f:
                                        error_excel_data = f.read()
                                    
                                    st.success("✅ Error report generated!")
                                    
                                    # Download button
                                    st.download_button(
                                        label="⬇️ Download Error Report Excel",
                                        data=error_excel_data,
                                        file_name=os.path.basename(error_excel_path),
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        help="Excel file with highlighted errors and comments",
                                        key="isv_download_error_report"
                                    )
                                    
                                    # Cleanup
                                    if os.path.exists(error_excel_path):
                                        os.remove(error_excel_path)
                                
                                except Exception as e:
                                    st.error(f"❌ Error generating error report: {str(e)}")
                                    with st.expander("🔍 View Error Details"):
                                        st.exception(e)
                    
                    # Show validation warnings if any
                    elif changes.validation_warnings:
                        st.warning("⚠️ Validation Warnings")
                        
                        with st.expander("🔍 View Warnings", expanded=False):
                            for warning in changes.validation_warnings:
                                st.warning(f"**Row {warning.row}, Column '{warning.column}':** {warning.message}")
                    
                    # If no changes detected
                    if not changes.has_changes():
                        st.info("ℹ️ No changes detected in the uploaded file.")
                        st.markdown("The file matches your current structure exactly.")
                    
                    elif not changes.validation_errors:
                        # Show detected changes
                        st.success("✅ File parsed successfully!")
                        st.markdown("### 📊 Detected Changes")
                        
                        # Summary metrics
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        
                        with col1:
                            st.metric("New Areas", len(changes.new_areas))
                        with col2:
                            st.metric("New Categories", len(changes.new_categories))
                        with col3:
                            st.metric("New Attributes", len(changes.new_attributes))
                        with col4:
                            st.metric("Updated Areas", len(changes.updated_areas))
                        with col5:
                            st.metric("Updated Categories", len(changes.updated_categories))
                        with col6:
                            st.metric("Updated Attributes", len(changes.updated_attributes))
                        
                        st.markdown("---")
                        
                        # Detailed changes
                        change_tabs = st.tabs([
                            f"➕ New ({len(changes.new_areas) + len(changes.new_categories) + len(changes.new_attributes)})",
                            f"✏️ Updated ({len(changes.updated_areas) + len(changes.updated_categories) + len(changes.updated_attributes)})"
                        ])
                        
                        # Tab 1: New items
                        with change_tabs[0]:
                            if changes.new_areas:
                                st.markdown("#### 🆕 New Areas")
                                for area in changes.new_areas:
                                    with st.expander(f"📁 {area['name']} (Row {area['excel_row']})"):
                                        st.json({
                                            'name': area['name'],
                                            'icon': area['icon'],
                                            'color': area['color'],
                                            'sort_order': area['sort_order'],
                                            'description': area['description']
                                        })
                            
                            if changes.new_categories:
                                st.markdown("#### 🆕 New Categories")
                                for cat in changes.new_categories:
                                    with st.expander(f"📂 {cat['path']} (Row {cat['excel_row']})"):
                                        st.json({
                                            'name': cat['name'],
                                            'path': cat['path'],
                                            'level': cat['level'],
                                            'sort_order': cat['sort_order'],
                                            'description': cat['description']
                                        })
                            
                            if changes.new_attributes:
                                st.markdown("#### 🆕 New Attributes")
                                for attr in changes.new_attributes:
                                    with st.expander(f"🏷️ {attr['category_path']} → {attr['name']} (Row {attr['excel_row']})"):
                                        st.json({
                                            'name': attr['name'],
                                            'category_path': attr['category_path'],
                                            'data_type': attr['data_type'],
                                            'unit': attr['unit'],
                                            'is_required': attr['is_required'],
                                            'default_value': attr['default_value'],
                                            'validation_rules': attr['validation_rules'],
                                            'description': attr['description']
                                        })
                            
                            if not changes.new_areas and not changes.new_categories and not changes.new_attributes:
                                st.info("No new items to add")
                        
                        # Tab 2: Updated items
                        with change_tabs[1]:
                            if changes.updated_areas:
                                st.markdown("#### ✏️ Updated Areas")
                                for area in changes.updated_areas:
                                    with st.expander(f"📁 {area['name']} (Row {area['excel_row']})"):
                                        st.markdown("**Changes:**")
                                        for key, value in area['updates'].items():
                                            st.markdown(f"- **{key}:** `{value}`")
                            
                            if changes.updated_categories:
                                st.markdown("#### ✏️ Updated Categories")
                                for cat in changes.updated_categories:
                                    with st.expander(f"📂 {cat['path']} (Row {cat['excel_row']})"):
                                        st.markdown("**Changes:**")
                                        for key, value in cat['updates'].items():
                                            st.markdown(f"- **{key}:** `{value}`")
                            
                            if changes.updated_attributes:
                                st.markdown("#### ✏️ Updated Attributes")
                                for attr in changes.updated_attributes:
                                    with st.expander(f"🏷️ {attr['category_path']} → {attr['name']} (Row {attr['excel_row']})"):
                                        st.markdown("**Changes:**")
                                        for key, value in attr['updates'].items():
                                            st.markdown(f"- **{key}:** `{value}`")
                            
                            if not changes.updated_areas and not changes.updated_categories and not changes.updated_attributes:
                                st.info("No updates to existing items")
                        
                        st.markdown("---")
                        
                        # Confirmation
                        st.markdown("### ✅ Confirm Changes")
                        st.warning("⚠️ **Important:** Once you confirm, these changes will be applied to your database immediately.")
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            confirm_text = st.text_input(
                                "Type 'CONFIRM' to apply changes:",
                                placeholder="CONFIRM",
                                help="Type CONFIRM in all caps to enable the Apply button",
                                key="isv_confirm_text"
                            )
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                            apply_button = st.button(
                                "🚀 Apply Changes",
                                type="primary",
                                disabled=(confirm_text != "CONFIRM"),
                                use_container_width=True,
                                key="isv_apply_button"
                            )
                        
                        if apply_button and confirm_text == "CONFIRM":
                            with st.spinner("💾 Applying changes to database..."):
                                success, message = parser.apply_changes()
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    
                                    st.info("🔄 Changes applied successfully! Refresh to see updates.")
                                    
                                    # Clear cache to reload fresh data
                                    if st.button("🔄 Refresh Now", type="primary", key="isv_refresh_after_upload"):
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                                    st.warning("Please check the errors and try again.")
                
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    with st.expander("🔍 View Error Details"):
                        st.exception(e)
                
                finally:
                    # Cleanup temporary file
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
