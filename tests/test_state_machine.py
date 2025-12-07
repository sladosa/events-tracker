"""
Tests for State Machine

Tests:
- AppState initialization
- State properties (is_viewing, is_editing, etc.)
- State transitions
- Filter enable/disable logic
- StateManager methods

Dependencies: pytest

Last Modified: 2025-12-07 09:00 UTC
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from state_machine import AppState, StateManager


class MockSessionState:
    """Mock Streamlit session state for testing"""
    def __init__(self):
        self.data = {}
    
    def __setattr__(self, name, value):
        if name == 'data':
            super().__setattr__(name, value)
        else:
            self.data[name] = value
    
    def __getattr__(self, name):
        if name == 'data':
            return super().__getattribute__(name)
        return self.data.get(name)
    
    def __contains__(self, name):
        return name in self.data


class TestAppState:
    """Test AppState dataclass"""
    
    def test_default_initialization(self):
        """Test default state values"""
        state = AppState()
        
        assert state.mode == 'read_only'
        assert state.operation is None
        assert state.has_changes is False
        assert state.active_tab is None
        assert state.form_data == {}
    
    def test_is_viewing_property(self):
        """Test is_viewing property"""
        state = AppState(mode='read_only')
        assert state.is_viewing is True
        
        state.mode = 'edit'
        assert state.is_viewing is False
    
    def test_is_editing_property(self):
        """Test is_editing property (edit mode, no changes)"""
        state = AppState(mode='edit', has_changes=False)
        assert state.is_editing is True
        
        state.has_changes = True
        assert state.is_editing is False
    
    def test_is_modifying_property(self):
        """Test is_modifying property (edit mode with changes)"""
        state = AppState(mode='edit', has_changes=True)
        assert state.is_modifying is True
        
        state.has_changes = False
        assert state.is_modifying is False
    
    def test_is_adding_property(self):
        """Test is_adding property (form open)"""
        state = AppState(mode='edit', operation='add')
        assert state.is_adding is True
        
        state.operation = None
        assert state.is_adding is False
    
    def test_filters_enabled_property(self):
        """Test filters_enabled logic"""
        # Viewing - filters enabled
        state = AppState(mode='read_only')
        assert state.filters_enabled is True
        
        # Editing (clean) - filters enabled
        state = AppState(mode='edit', has_changes=False)
        assert state.filters_enabled is True
        
        # Modifying - filters DISABLED
        state = AppState(mode='edit', has_changes=True)
        assert state.filters_enabled is False
    
    def test_transition_to_viewing(self):
        """Test transition to viewing state"""
        state = AppState(
            mode='edit',
            operation='edit',
            has_changes=True,
            active_tab='categories',
            form_data={'test': 'data'}
        )
        
        state.transition_to_viewing()
        
        assert state.mode == 'read_only'
        assert state.operation is None
        assert state.has_changes is False
        assert state.active_tab is None
        assert state.form_data == {}
    
    def test_transition_to_editing(self):
        """Test transition to editing state"""
        state = AppState(
            mode='read_only',
            has_changes=True,
            form_data={'test': 'data'}
        )
        
        state.transition_to_editing()
        
        assert state.mode == 'edit'
        assert state.operation is None
        assert state.has_changes is False
        assert state.form_data == {}
    
    def test_transition_to_modifying(self):
        """Test transition to modifying state"""
        state = AppState()
        
        state.transition_to_modifying('categories')
        
        assert state.mode == 'edit'
        assert state.operation == 'edit'
        assert state.has_changes is True
        assert state.active_tab == 'categories'
    
    def test_transition_to_adding(self):
        """Test transition to adding state"""
        state = AppState()
        
        state.transition_to_adding('attributes')
        
        assert state.mode == 'edit'
        assert state.operation == 'add'
        assert state.has_changes is False
        assert state.active_tab == 'attributes'
        assert state.form_data == {}


class TestStateManager:
    """Test StateManager class"""
    
    def test_initialization(self):
        """Test StateManager initialization"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        assert 'app_state' in session
        assert isinstance(mgr.state, AppState)
    
    def test_state_property(self):
        """Test state property access"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        assert mgr.state == session.app_state
    
    def test_can_switch_mode_no_changes(self):
        """Test mode switch allowed when no changes"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        can_switch, msg = mgr.can_switch_mode()
        
        assert can_switch is True
        assert msg == ""
    
    def test_can_switch_mode_with_changes(self):
        """Test mode switch blocked when has changes"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.has_changes = True
        
        can_switch, msg = mgr.can_switch_mode()
        
        assert can_switch is False
        assert "unsaved changes" in msg.lower()
    
    def test_switch_to_viewing_success(self):
        """Test successful switch to viewing"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.mode = 'edit'
        
        success, msg = mgr.switch_to_viewing()
        
        assert success is True
        assert mgr.state.is_viewing is True
    
    def test_switch_to_viewing_blocked(self):
        """Test switch blocked by unsaved changes"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.mode = 'edit'
        mgr.state.has_changes = True
        
        success, msg = mgr.switch_to_viewing()
        
        assert success is False
        assert mgr.state.is_viewing is False
    
    def test_switch_to_viewing_force(self):
        """Test forced switch ignores changes"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.mode = 'edit'
        mgr.state.has_changes = True
        
        success, msg = mgr.switch_to_viewing(force=True)
        
        assert success is True
        assert mgr.state.is_viewing is True
    
    def test_switch_to_editing(self):
        """Test switch to editing mode"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        success, msg = mgr.switch_to_editing()
        
        assert success is True
        assert mgr.state.is_editing is True
    
    def test_start_editing_data(self):
        """Test start editing data"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        success, msg = mgr.start_editing_data('categories')
        
        assert success is True
        assert mgr.state.is_modifying is True
        assert mgr.state.active_tab == 'categories'
    
    def test_start_adding_item(self):
        """Test start adding item"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        success, msg = mgr.start_adding_item('attributes')
        
        assert success is True
        assert mgr.state.is_adding is True
        assert mgr.state.active_tab == 'attributes'
    
    def test_save_changes(self):
        """Test save changes transitions to clean editing"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.transition_to_modifying('categories')
        
        success, msg = mgr.save_changes()
        
        assert success is True
        assert mgr.state.is_editing is True
        assert mgr.state.has_changes is False
    
    def test_discard_changes(self):
        """Test discard changes transitions to clean editing"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.transition_to_modifying('categories')
        
        success, msg = mgr.discard_changes()
        
        assert success is True
        assert mgr.state.is_editing is True
        assert mgr.state.has_changes is False
    
    def test_submit_form(self):
        """Test form submission clears form data"""
        session = MockSessionState()
        mgr = StateManager(session)
        mgr.state.transition_to_adding('categories')
        mgr.state.form_data = {'name': 'Test', 'description': 'Test desc'}
        
        success, msg = mgr.submit_form()
        
        assert success is True
        assert mgr.state.form_data == {}
        assert mgr.state.is_editing is True
    
    def test_clear_editor_state_backward_compatibility(self):
        """Test _clear_editor_state handles old session state variables"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Set old state variables
        session.original_df = "some_dataframe"
        session.edited_df = "edited_dataframe"
        session.editing_active = True
        
        mgr._clear_editor_state()
        
        assert session.original_df is None
        assert session.edited_df is None
        assert session.editing_active is False


# Integration Tests
class TestStateTransitions:
    """Test complete state transition scenarios"""
    
    def test_viewing_to_editing_to_viewing(self):
        """Test round-trip: viewing → editing → viewing"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Start in viewing
        assert mgr.state.is_viewing
        
        # Switch to editing
        mgr.switch_to_editing()
        assert mgr.state.is_editing
        
        # Switch back to viewing
        mgr.switch_to_viewing()
        assert mgr.state.is_viewing
    
    def test_edit_modify_save_flow(self):
        """Test: edit mode → modify data → save → back to clean edit"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Start editing
        mgr.switch_to_editing()
        assert mgr.state.is_editing
        
        # Start modifying
        mgr.start_editing_data('categories')
        assert mgr.state.is_modifying
        assert not mgr.state.filters_enabled
        
        # Save changes
        mgr.save_changes()
        assert mgr.state.is_editing
        assert mgr.state.filters_enabled
    
    def test_edit_modify_discard_flow(self):
        """Test: edit mode → modify data → discard → back to clean edit"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Start editing
        mgr.switch_to_editing()
        
        # Start modifying
        mgr.start_editing_data('areas')
        assert mgr.state.has_changes
        
        # Discard changes
        mgr.discard_changes()
        assert mgr.state.is_editing
        assert not mgr.state.has_changes
    
    def test_add_form_flow(self):
        """Test: edit mode → open form → submit → back to clean edit"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Start editing
        mgr.switch_to_editing()
        
        # Open add form
        mgr.start_adding_item('categories')
        assert mgr.state.is_adding
        assert mgr.state.filters_enabled  # Forms don't block filters
        
        # Fill form
        mgr.state.form_data = {'name': 'New Category', 'description': 'Test'}
        
        # Submit form
        mgr.submit_form()
        assert mgr.state.is_editing
        assert mgr.state.form_data == {}
    
    def test_cannot_switch_mode_with_unsaved_changes(self):
        """Test: blocking mode switch when has unsaved changes"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Start editing and modify
        mgr.switch_to_editing()
        mgr.start_editing_data('categories')
        assert mgr.state.has_changes
        
        # Try to switch to viewing (should fail)
        success, msg = mgr.switch_to_viewing()
        assert not success
        assert mgr.state.is_modifying
    
    def test_force_switch_with_unsaved_changes(self):
        """Test: force switch discards unsaved changes"""
        session = MockSessionState()
        mgr = StateManager(session)
        
        # Start editing and modify
        mgr.switch_to_editing()
        mgr.start_editing_data('categories')
        assert mgr.state.has_changes
        
        # Force switch (discards changes)
        success, msg = mgr.switch_to_viewing(force=True)
        assert success
        assert mgr.state.is_viewing
        assert not mgr.state.has_changes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
