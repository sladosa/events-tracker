"""
State Machine - Simplified State Management for Interactive Structure Viewer

Features:

- Single source of truth (AppState dataclass)
- Clear state transitions
- Separation of concerns (viewing/editing/modifying/adding/deleting/inserting/removing)
- Filter management based on state
- Form state tracking
- Operation lifecycle management

Dependencies: dataclasses, typing

Version: 1.2.0 - Enhanced State Management
Last Modified: 2025-12-10 12:00 UTC

CHANGELOG v1.2.0:
- 🐛 Enhanced lifecycle management for all operations
- ✅ Added methods: start_deleting_items(), start_inserting_item(), start_removing_item()
- ✅ Added methods: cancel_operation(), complete_operation()
- ✅ Added properties: is_deleting, is_inserting, is_removing
- ✅ Improved filter management based on operation state
- ✅ Better state cleanup with comprehensive _clear_editor_state()
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple

@dataclass
class AppState:
    """Single source of truth for application state"""
    
    mode: str = 'read_only'  # 'read_only' or 'edit'
    operation: Optional[str] = None  # None, 'edit', 'add', 'delete', 'insert', 'remove'
    has_changes: bool = False
    active_tab: Optional[str] = None
    form_data: Dict[str, Any] = field(default_factory=dict)
    operation_in_progress: str = ""  # Current operation name for UI feedback
    
    @property
    def is_viewing(self) -> bool:
        """In read-only viewing mode"""
        return self.mode == 'read_only'
    
    @property
    def is_editing(self) -> bool:
        """In edit mode but no changes"""
        return self.mode == 'edit' and not self.has_changes and self.operation is None
    
    @property
    def is_modifying(self) -> bool:
        """In edit mode with unsaved changes or active operation"""
        return self.mode == 'edit' and (self.has_changes or self.operation is not None)
    
    @property
    def is_adding(self) -> bool:
        """Form is open for adding"""
        return self.mode == 'edit' and self.operation == 'add'
    
    @property
    def is_deleting(self) -> bool:
        """Delete operation in progress"""
        return self.mode == 'edit' and self.operation == 'delete'
    
    @property
    def is_inserting(self) -> bool:
        """Insert operation in progress"""
        return self.mode == 'edit' and self.operation == 'insert'
    
    @property
    def is_removing(self) -> bool:
        """Remove operation in progress"""
        return self.mode == 'edit' and self.operation == 'remove'
    
    @property
    def filters_enabled(self) -> bool:
        """Filters enabled unless operation in progress"""
        return not self.is_modifying
    
    def transition_to_viewing(self):
        """Clean transition to viewing state"""
        self.mode = 'read_only'
        self.operation = None
        self.has_changes = False
        self.active_tab = None
        self.form_data = {}
        self.operation_in_progress = ""
    
    def transition_to_editing(self):
        """Clean transition to editing state"""
        self.mode = 'edit'
        self.operation = None
        self.has_changes = False
        self.form_data = {}
        self.operation_in_progress = ""
    
    def transition_to_modifying(self, tab: str):
        """Transition when user opens data editor"""
        self.mode = 'edit'
        self.operation = 'edit'
        self.has_changes = True
        self.active_tab = tab
        self.operation_in_progress = f"Editing {tab}"
    
    def transition_to_adding(self, tab: str):
        """Transition when user opens add form"""
        self.mode = 'edit'
        self.operation = 'add'
        self.has_changes = False  # Adding doesn't count as changes until saved
        self.active_tab = tab
        self.form_data = {}
        self.operation_in_progress = f"Adding to {tab}"
    
    def transition_to_deleting(self, tab: str):
        """Transition when user starts delete operation"""
        self.mode = 'edit'
        self.operation = 'delete'
        self.active_tab = tab
        self.operation_in_progress = f"Deleting from {tab}"
    
    def transition_to_inserting(self, tab: str):
        """Transition when user starts insert operation"""
        self.mode = 'edit'
        self.operation = 'insert'
        self.active_tab = tab
        self.operation_in_progress = f"Inserting into {tab}"
    
    def transition_to_removing(self, tab: str):
        """Transition when user starts remove operation"""
        self.mode = 'edit'
        self.operation = 'remove'
        self.active_tab = tab
        self.operation_in_progress = f"Removing from {tab}"

class StateManager:
    """Manages state transitions and validation"""
    
    def __init__(self, session_state):
        self.session_state = session_state
        
        # Initialize state if needed
        if 'app_state' not in session_state:
            session_state.app_state = AppState()
    
    @property
    def state(self) -> AppState:
        """Get current application state"""
        return self.session_state.app_state
    
    def can_switch_mode(self) -> Tuple[bool, str]:
        """Check if mode switch is allowed"""
        if self.state.has_changes or self.state.operation is not None:
            return False, "You have unsaved changes or an operation in progress. Save or discard first."
        return True, ""
    
    def switch_to_viewing(self, force: bool = False) -> Tuple[bool, str]:
        """Switch to viewing mode"""
        if not force:
            can_switch, reason = self.can_switch_mode()
            if not can_switch:
                return False, reason
        
        self.state.transition_to_viewing()
        self._clear_editor_state()
        return True, "Switched to Read-Only mode"
    
    def switch_to_editing(self) -> Tuple[bool, str]:
        """Switch to editing mode"""
        self.state.transition_to_editing()
        return True, "Switched to Edit mode"
    
    def start_editing_data(self, tab: str) -> Tuple[bool, str]:
        """User opened data editor"""
        self.state.transition_to_modifying(tab)
        return True, f"Editing {tab}"
    
    def start_adding_item(self, tab: str) -> Tuple[bool, str]:
        """User opened add form"""
        self.state.transition_to_adding(tab)
        return True, f"Adding to {tab}"
    
    def start_deleting_items(self, tab: str) -> Tuple[bool, str]:
        """User started delete operation"""
        self.state.transition_to_deleting(tab)
        return True, f"Ready to delete from {tab}"
    
    def start_inserting_item(self, tab: str) -> Tuple[bool, str]:
        """User started insert operation"""
        self.state.transition_to_inserting(tab)
        return True, f"Inserting into {tab}"
    
    def start_removing_item(self, tab: str) -> Tuple[bool, str]:
        """User started remove operation"""
        self.state.transition_to_removing(tab)
        return True, f"Removing from {tab}"
    
    def save_changes(self) -> Tuple[bool, str]:
        """Save operation completed"""
        self.state.transition_to_editing()
        self._clear_editor_state()
        return True, "Changes saved successfully"
    
    def discard_changes(self) -> Tuple[bool, str]:
        """Discard changes operation"""
        self.state.transition_to_editing()
        self._clear_editor_state()
        return True, "Changes discarded"
    
    def cancel_operation(self) -> Tuple[bool, str]:
        """Cancel current operation (delete/insert/remove/add)"""
        self.state.transition_to_editing()
        self._clear_editor_state()
        return True, f"Operation cancelled"
    
    def submit_form(self) -> Tuple[bool, str]:
        """Form submitted successfully"""
        self.state.transition_to_editing()
        self.state.form_data = {}
        return True, "Item added successfully"
    
    def complete_operation(self) -> Tuple[bool, str]:
        """Operation completed successfully"""
        self.state.transition_to_editing()
        self._clear_editor_state()
        return True, "Operation completed successfully"
    
    def _clear_editor_state(self):
        """Clear all editor-related state variables"""
        # Clear data editor state
        if hasattr(self.session_state, 'original_df'):
            self.session_state.original_df = None
        
        if hasattr(self.session_state, 'edited_df'):
            self.session_state.edited_df = None
        
        if hasattr(self.session_state, 'editing_active'):
            self.session_state.editing_active = False
        
        # Clear editor-specific state
        if hasattr(self.session_state, 'areas_editor'):
            self.session_state.areas_editor = None
        
        if hasattr(self.session_state, 'categories_editor'):
            self.session_state.categories_editor = None
        
        if hasattr(self.session_state, 'attributes_editor'):
            self.session_state.attributes_editor = None
        
        # Clear delete/insert/remove state
        if hasattr(self.session_state, 'deleting_active'):
            self.session_state.deleting_active = False
        
        if hasattr(self.session_state, 'inserting_active'):
            self.session_state.inserting_active = False
        
        if hasattr(self.session_state, 'removing_active'):
            self.session_state.removing_active = False
        
        if hasattr(self.session_state, 'delete_items_selected'):
            self.session_state.delete_items_selected = []
        
        if hasattr(self.session_state, 'insert_category_between_active'):
            self.session_state.insert_category_between_active = False
        
        if hasattr(self.session_state, 'remove_category_between_active'):
            self.session_state.remove_category_between_active = False
