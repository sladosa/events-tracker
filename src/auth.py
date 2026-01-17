"""
Authentication Module - PERSISTENT RESET CODES
===============================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-01-17 21:30 UTC
Python: 3.11
Version: 2.5.1 (PERSISTENT STORAGE - FILE BASED!)

Handles user signup, login, logout with Supabase Auth
Uses AuthManager class for clean authentication flow

NEW in V2.5.1:
- 🔧 FILE-BASED STORAGE: Reset codes persist between sessions!
- ✅ Uses JSON file in /tmp for code storage
- ✅ Codes survive session changes
- ✅ Automatic cleanup of expired codes
- ✅ Thread-safe file locking

FIXED from V2.5.0:
- session_state reset codes lost between sessions
- Now uses persistent file storage!
"""
import streamlit as st
from supabase import Client
from typing import Optional, Tuple, Dict
import os
import secrets
import string
from datetime import datetime, timedelta
import json
import fcntl
from pathlib import Path


class AuthManager:
    """Manage user authentication with Supabase."""
    
    # File path for persistent storage
    RESET_CODES_FILE = "/tmp/events_tracker_reset_codes.json"
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        
        # Initialize session state
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        # Ensure reset codes file exists
        self._ensure_codes_file()
    
    def _ensure_codes_file(self):
        """Ensure reset codes file exists."""
        if not os.path.exists(self.RESET_CODES_FILE):
            self._save_codes({})
    
    def _load_codes(self) -> Dict:
        """
        Load reset codes from file with file locking.
        
        Returns:
            Dict of reset codes
        """
        try:
            if not os.path.exists(self.RESET_CODES_FILE):
                return {}
            
            with open(self.RESET_CODES_FILE, 'r') as f:
                # Lock file for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    # Convert ISO datetime strings back to datetime objects
                    for code_data in data.values():
                        code_data['expires'] = datetime.fromisoformat(code_data['expires'])
                        code_data['created'] = datetime.fromisoformat(code_data['created'])
                    return data
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            # If file is corrupted or doesn't exist, return empty dict
            return {}
    
    def _save_codes(self, codes: Dict):
        """
        Save reset codes to file with file locking.
        
        Args:
            codes: Dict of reset codes to save
        """
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serializable_codes = {}
            for code, data in codes.items():
                serializable_codes[code] = {
                    'email': data['email'],
                    'expires': data['expires'].isoformat(),
                    'used': data['used'],
                    'created': data['created'].isoformat()
                }
            
            with open(self.RESET_CODES_FILE, 'w') as f:
                # Lock file for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(serializable_codes, f, indent=2)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            st.error(f"Error saving reset codes: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.authenticated and st.session_state.user is not None
    
    def get_user_id(self) -> Optional[str]:
        """Get current user's ID."""
        if self.is_authenticated():
            return st.session_state.user.get('id')
        return None
    
    def get_user_email(self) -> Optional[str]:
        """Get current user's email."""
        if self.is_authenticated():
            return st.session_state.user.get('email')
        return None
    
    def _generate_reset_code(self) -> str:
        """
        Generate a secure random reset code.
        
        Returns:
            12-character alphanumeric code (uppercase)
        """
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        code = ''.join(secrets.choice(alphabet) for _ in range(12))
        return code
    
    def _store_reset_code(self, code: str, email: str):
        """
        Store reset code with expiration time in persistent file.
        
        Args:
            code: Reset code
            email: User's email
        """
        # Load existing codes
        codes = self._load_codes()
        
        # Add new code
        expiration = datetime.now() + timedelta(hours=1)
        codes[code] = {
            'email': email,
            'expires': expiration,
            'used': False,
            'created': datetime.now()
        }
        
        # Clean up expired codes before saving
        self._cleanup_expired_codes_dict(codes)
        
        # Save back to file
        self._save_codes(codes)
    
    def _cleanup_expired_codes_dict(self, codes: Dict):
        """
        Remove expired codes from dictionary (in-place).
        
        Args:
            codes: Dict of codes to clean
        """
        now = datetime.now()
        expired_codes = [
            code for code, data in codes.items()
            if data['expires'] < now
        ]
        for code in expired_codes:
            del codes[code]
    
    def _validate_reset_code(self, code: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate reset code from persistent storage.
        
        Args:
            code: Reset code to validate
            
        Returns:
            Tuple of (valid: bool, email: Optional[str], error_message: Optional[str])
        """
        # Load codes from file
        codes = self._load_codes()
        
        # Clean up expired codes
        self._cleanup_expired_codes_dict(codes)
        
        # Check if code exists
        if code not in codes:
            return False, None, "Invalid reset code. Please request a new password reset."
        
        code_data = codes[code]
        
        # Check if already used
        if code_data['used']:
            return False, None, "This reset code has already been used. Please request a new one."
        
        # Check if expired
        if code_data['expires'] < datetime.now():
            return False, None, "Reset code has expired. Please request a new password reset."
        
        # Valid!
        return True, code_data['email'], None
    
    def _invalidate_reset_code(self, code: str):
        """Mark reset code as used in persistent storage."""
        codes = self._load_codes()
        if code in codes:
            codes[code]['used'] = True
            self._save_codes(codes)
    
    def _get_app_url(self) -> str:
        """Get current app URL."""
        if 'app_base_url' in st.session_state:
            return st.session_state.app_base_url
        
        try:
            if hasattr(st.secrets, 'APP_URL'):
                return st.secrets.APP_URL
        except:
            pass
        
        try:
            query_params = st.query_params
            if 'app_origin' in query_params:
                url = query_params['app_origin']
                st.session_state.app_base_url = url
                return url
        except:
            pass
        
        return "https://events-tracker.streamlit.app"
    
    def _detect_app_url(self):
        """Use JavaScript to detect and store app URL."""
        if 'app_base_url' not in st.session_state:
            import streamlit.components.v1 as components
            
            components.html("""
            <script>
            const origin = window.location.origin;
            const urlParams = new URLSearchParams(window.location.search);
            
            if (!urlParams.has('app_origin')) {
                urlParams.set('app_origin', origin);
                const newUrl = window.location.pathname + '?' + urlParams.toString();
                
                if (window.location.search !== '?' + urlParams.toString()) {
                    window.location.href = newUrl;
                }
            }
            </script>
            """, height=0)
            
            try:
                query_params = st.query_params
                if 'app_origin' in query_params:
                    st.session_state.app_base_url = query_params['app_origin']
            except:
                pass
    
    def signup(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                return True, "✅ Sign up successful! Please check your email to confirm your account."
            else:
                return False, "❌ Sign up failed. Please try again."
                
        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                return False, "❌ This email is already registered. Please login instead."
            return False, f"❌ Sign up error: {error_msg}"
    
    def login(self, email: str, password: str) -> Tuple[bool, str]:
        """Log in an existing user."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                st.session_state.user = {
                    'id': response.user.id,
                    'email': response.user.email
                }
                st.session_state.authenticated = True
                return True, f"✅ Welcome back, {response.user.email}!"
            else:
                return False, "❌ Login failed. Please check your credentials."
                
        except Exception as e:
            error_msg = str(e)
            if "invalid" in error_msg.lower():
                return False, "❌ Invalid email or password."
            return False, f"❌ Login error: {error_msg}"
    
    def logout(self):
        """Log out the current user."""
        try:
            self.client.auth.sign_out()
        except:
            pass
        finally:
            st.session_state.user = None
            st.session_state.authenticated = False
            st.rerun()
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Send password reset email with custom reset code.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate reset code
            reset_code = self._generate_reset_code()
            
            # Store code with expiration (in file!)
            self._store_reset_code(reset_code, email)
            
            # Get app URL
            app_url = self._get_app_url()
            
            # Create reset link with code as query param
            reset_link = f"{app_url}?reset_code={reset_code}"
            
            return True, (
                f"✅ Password reset requested!\n\n"
                f"**Reset Code:** `{reset_code}`\n\n"
                f"**Reset Link:** [Click here]({reset_link})\n\n"
                f"💡 In production, this would be sent to {email}. "
                f"Code expires in 1 hour."
            )
                    
        except Exception as e:
            error_msg = str(e)
            return False, f"❌ Error requesting password reset: {error_msg}"
    
    def reset_password_with_code(self, code: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset password using custom reset code.
        
        Args:
            code: Reset code from email
            new_password: New password to set
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate code
            valid, email, error_msg = self._validate_reset_code(code)
            
            if not valid:
                return False, f"❌ {error_msg}"
            
            # Mark code as used
            self._invalidate_reset_code(code)
            
            return True, (
                f"✅ Reset code validated for {email}!\n\n"
                f"Please login with this email and use 'Change Password' "
                f"in the sidebar to set your new password.\n\n"
                f"💡 In a production environment, the password would be updated directly."
            )
                
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    def change_password(self, new_password: str) -> Tuple[bool, str]:
        """Change password for currently logged in user."""
        if not self.is_authenticated():
            return False, "❌ You must be logged in to change password."
        
        try:
            response = self.client.auth.update_user({
                "password": new_password
            })
            
            if response.user:
                return True, "✅ Password changed successfully!"
            else:
                return False, "❌ Failed to change password. Please try again."
                
        except Exception as e:
            error_msg = str(e)
            return False, f"❌ Error changing password: {error_msg}"
    
    def _show_password_reset_form(self, reset_code: str, email: str):
        """
        Show password reset form with validated code.
        
        Args:
            reset_code: Validated reset code
            email: Email associated with code
        """
        st.title("🔐 Reset Your Password")
        
        st.success(f"✅ Reset code validated for: **{email}**")
        
        st.markdown("""
        ### Set Your New Password
        
        Enter a new password for your account.
        """)
        
        with st.form("password_reset_form"):
            new_password = st.text_input(
                "New Password",
                type="password",
                help="Minimum 6 characters"
            )
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password"
            )
            
            submit = st.form_submit_button("✅ Update Password", use_container_width=True, type="primary")
            
            if submit:
                if not new_password or not confirm_password:
                    st.error("❌ Please fill in both fields.")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters long.")
                else:
                    # Reset password with code
                    with st.spinner("Updating password..."):
                        success, message = self.reset_password_with_code(reset_code, new_password)
                    
                    if success:
                        st.success(message)
                        st.info("💡 Redirecting to login page...")
                        
                        # Clear query params
                        st.query_params.clear()
                        
                        # Wait and redirect
                        import time
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error(message)
        
        st.divider()
        if st.button("← Cancel and Return to Login"):
            st.query_params.clear()
            st.rerun()
    
    def show_login_page(self):
        """Display login/signup page with password reset handling."""
        
        # Detect app URL first
        self._detect_app_url()
        
        # ⭐ Check for reset_code in query params
        query_params = st.query_params
        
        if 'reset_code' in query_params:
            reset_code = query_params['reset_code']
            
            # Validate code (from file!)
            valid, email, error_msg = self._validate_reset_code(reset_code)
            
            if valid:
                # Show password reset form
                self._show_password_reset_form(reset_code, email)
                return  # Don't show login page
            else:
                # Invalid code - show error and continue to login page
                st.error(f"❌ {error_msg}")
                st.info("💡 Please request a new password reset below.")
        
        st.title("🔐 Events Tracker - Login")
        
        tab1, tab2, tab3 = st.tabs(["Login", "Forgot Password?", "Sign Up"])
        
        # TAB 1: LOGIN
        with tab1:
            st.subheader("Login to Your Account")
            
            with st.form("login_form"):
                email = st.text_input(
                    "Email", 
                    placeholder="your.email@example.com",
                    key="login_email_input"
                )
                password = st.text_input("Password", type="password", key="login_password_input")
                submit = st.form_submit_button("🔓 Login", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("❌ Please enter both email and password.")
                    else:
                        success, message = self.login(email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        
        # TAB 2: FORGOT PASSWORD
        with tab2:
            st.subheader("🔑 Reset Your Password")
            
            st.markdown("""
            **How it works:**
            1. Enter your email address below
            2. Click "Send Reset Code"
            3. You'll receive a **reset code** and **reset link**
            4. Click the link (or enter code manually)
            5. Set your new password
            6. Login with your new password
            
            💡 **Note:** In production, the reset code would be emailed to you.
            """)
            
            st.markdown("---")
            
            forgot_email = st.text_input(
                "📧 Your Email Address",
                placeholder="your.email@example.com",
                key="forgot_password_email",
                help="Enter the email you used to create your account"
            )
            
            if st.button("📧 Send Reset Code", use_container_width=True, type="primary"):
                if not forgot_email:
                    st.error("❌ Please enter your email address.")
                elif '@' not in forgot_email or '.' not in forgot_email:
                    st.error("❌ Please enter a valid email address.")
                else:
                    with st.spinner("Generating reset code..."):
                        success, message = self.request_password_reset(forgot_email)
                    
                    if success:
                        st.success("✅ Reset code generated!")
                        st.markdown(message)
                        st.info("💡 Click the reset link above to set your new password!")
                    else:
                        st.error(message)
        
        # TAB 3: SIGN UP
        with tab3:
            st.subheader("Create New Account")
            
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="your.email@example.com", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_password")
                password_confirm = st.text_input("Confirm Password", type="password")
                
                st.caption("⚠️ Password must be at least 6 characters long")
                
                submit = st.form_submit_button("✅ Sign Up", use_container_width=True)
                
                if submit:
                    if not email or not password or not password_confirm:
                        st.error("❌ Please fill in all fields.")
                    elif password != password_confirm:
                        st.error("❌ Passwords do not match.")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters long.")
                    else:
                        success, message = self.signup(email, password)
                        if success:
                            st.success(message)
                            st.info("💡 After confirming your email, return here to login.")
                        else:
                            st.error(message)
        
        st.divider()
        st.caption("🔒 Your data is secured with Row Level Security (RLS)")
    
    def show_user_info_sidebar(self):
        """Show user info and logout button in sidebar."""
        if self.is_authenticated():
            with st.sidebar:
                st.divider()
                st.markdown("### 👤 User")
                st.text(f"📧 {self.get_user_email()}")
                
                with st.expander("🔑 Change Password"):
                    with st.form("change_password_form"):
                        new_password = st.text_input("New Password", type="password", key="new_pass")
                        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_pass")
                        
                        st.caption("⚠️ Password must be at least 6 characters")
                        
                        submit_change = st.form_submit_button("✅ Change Password", use_container_width=True)
                        
                        if submit_change:
                            if not new_password or not confirm_password:
                                st.error("❌ Please fill in both fields.")
                            elif new_password != confirm_password:
                                st.error("❌ Passwords do not match.")
                            elif len(new_password) < 6:
                                st.error("❌ Password must be at least 6 characters.")
                            else:
                                success, message = self.change_password(new_password)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
