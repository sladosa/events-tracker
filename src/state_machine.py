"""
State Machine - Simplified State Management for Interactive Structure Viewer

Features:
- Single source of truth (AppState dataclass)
- Clear state transitions
- Separation of concerns (viewing/editing/modifying/adding)
- Filter management based on state
- Form state tracking
- v1.1.0: Added discard_pending flag to prevent false positive detection after discard

Dependencies: dataclasses, typing

Last Modified: 2025-12-10 19:00 UTC
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple


@dataclass
class AppState:
    """Single source of truth for application state"""
    mode: str = 'read_only'  # 'read_only' or 'edit'
    operation: Optional[str] = None  # None, 'edit', 'add', 'delete'
    has_changes: bool = False
    active_tab: Optional[str] = None
    form_data: Dict[str, Any] = field(default_factory=dict)
    # v1.1.0: Flag to prevent false positive detection immediately after discard
    # This flag persists for ONE full render cycle, then is cleared at the end
    discard_pending: bool = False
    
    @property
    def is_viewing(self) -> bool:
        """In read-only viewing mode"""
        return self.mode == 'read_only'
    
    @property
    def is_editing(self) -> bool:
        """In edit mode but no changes"""
        return self.mode == 'edit' and not self.has_changes
    
    @property
    def is_modifying(self) -> bool:
        """In edit mode with unsaved changes"""
        return self.mode == 'edit' and self.has_changes
    
    @property
    def is_adding(self) -> bool:
        """Form is open for adding"""
        return self.mode == 'edit' and self.operation == 'add'
    
    @property
    def filters_enabled(self) -> bool:
        """Filters enabled unless modifying data"""
        return not self.is_modifying
    
    def transition_to_viewing(self):
        """Clean transition to viewing state"""
        self.mode = 'read_only'
        self.operation = None
        self.has_changes = False
        self.active_tab = None
        self.form_data = {}
        self.discard_pending = False
    
    def transition_to_editing(self):
        """Clean transition to editing state"""
        self.mode = 'edit'
        self.operation = None
        self.has_changes = False
        self.form_data = {}
        # Don't clear discard_pending here - it's cleared at end of render cycle
    
    def transition_to_modifying(self, tab: str):
        """Transition when user opens data editor"""
        self.mode = 'edit'
        self.operation = 'edit'
        self.has_changes = True
        self.active_tab = tab
        self.discard_pending = False
    
    def transition_to_adding(self, tab: str):
        """Transition when user opens add form"""
        self.mode = 'edit'
        self.operation = 'add'
        self.has_changes = False
        self.active_tab = tab
        self.form_data = {}
        self.discard_pending = False


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
        if self.state.has_changes:
            return False, "You have unsaved changes. Save or discard first."
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
    
    def save_changes(self) -> Tuple[bool, str]:
        """Save operation completed"""
        self.state.transition_to_editing()
        self._clear_editor_state()
        return True, "Changes saved successfully"
    
    def discard_changes(self) -> Tuple[bool, str]:
        """
        Discard operation.
        Sets discard_pending flag to prevent false positive detection on next render.
        The flag will be cleared at the END of the next render cycle (after all tabs).
        """
        self.state.transition_to_editing()
        self.state.discard_pending = True  # Persists for ONE full render cycle
        self._clear_editor_state()
        return True, "Changes discarded"
    
    def submit_form(self) -> Tuple[bool, str]:
        """Form submitted successfully"""
        self.state.transition_to_editing()
        self.state.form_data = {}
        return True, "Item added successfully"
    
    def _clear_editor_state(self):
        """Clear all editor-related state variables"""
        # Clear old state variables (backward compatibility)
        if hasattr(self.session_state, 'original_df'):
            self.session_state.original_df = None
        if hasattr(self.session_state, 'edited_df'):
            self.session_state.edited_df = None
        if hasattr(self.session_state, 'editing_active'):
            self.session_state.editing_active = False
