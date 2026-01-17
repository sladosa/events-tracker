"""
Authentication Module - ADMIN API PASSWORD UPDATE
==================================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-01-17 22:00 UTC
Python: 3.11
Version: 2.5.2 (ADMIN API - ACTUALLY UPDATES PASSWORD!)

Handles user signup, login, logout with Supabase Auth
Uses AuthManager class for clean authentication flow

NEW in V2.5.2:
- 🔧 ADMIN API: Actually updates password in Supabase!
- ✅ Uses Service Role Key for password updates
- ✅ Password reset WORKS end-to-end!
- ✅ User can login with new password immediately!

FIXED from V2.5.1:
- Password was validated but NOT updated
- Now uses admin API to actually update password!
"""
import streamlit as st
from supabase import Client, create_client
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
        """Load reset codes from file with file locking."""
        try:
            if not os.path.exists(self.RESET_CODES_FILE):
                return {}
            
            with open(self.RESET_CODES_FILE, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    for code_data in data.values():
                        code_data['expires'] = datetime.fromisoformat(code_data['expires'])
                        code_data['created'] = datetime.fromisoformat(code_data['created'])
                    return data
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            return {}
    
    def _save_codes(self, codes: Dict):
        """Save reset codes to file with file locking."""
        try:
            serializable_codes = {}
            for code, data in codes.items():
                serializable_codes[code] = {
                    'email': data['email'],
                    'expires': data['expires'].isoformat(),
                    'used': data['used'],
                    'created': data['created'].isoformat()
                }
            
            with open(self.RESET_CODES_FILE, 'w') as f:
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
        """Generate a secure random reset code."""
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        code = ''.join(secrets.choice(alphabet) for _ in range(12))
        return code
    
    def _store_reset_code(self, code: str, email: str):
        """Store reset code with expiration time in persistent file."""
        codes = self._load_codes()
        expiration = datetime.now() + timedelta(hours=1)
        codes[code] = {
            'email': email,
            'expires': expiration,
            'used': False,
            'created': datetime.now()
        }
        self._cleanup_expired_codes_dict(codes)
        self._save_codes(codes)
    
    def _cleanup_expired_codes_dict(self, codes: Dict):
        """Remove expired codes from dictionary (in-place)."""
        now = datetime.now()
        expired_codes = [
            code for code, data in codes.items()
            if data['expires'] < now
        ]
        for code in expired_codes:
            del codes[code]
    
    def _validate_reset_code(self, code: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate reset code from persistent storage."""
        codes = self._load_codes()
        self._cleanup_expired_codes_dict(codes)
        
        if code not in codes:
            return False, None, "Invalid reset code. Please request a new password reset."
        
        code_data = codes[code]
        
        if code_data['used']:
            return False, None, "This reset code has already been used. Please request a new one."
        
        if code_data['expires'] < datetime.now():
            return False, None, "Reset code has expired. Please request a new password reset."
        
        return True, code_data['email'], None
    
    def _invalidate_reset_code(self, code: str):
        """Mark reset code as used in persistent storage."""
        codes = self._load_codes()
        if code in codes:
            codes[code]['used'] = True
            self._save_codes(codes)
    
    def _get_admin_client(self) -> Optional[Client]:
        """
        Create Supabase admin client using service role key.
        
        Returns:
            Admin client or None if service key not available
        """
        try:
            # Try to get service role key from secrets
            if hasattr(st.secrets, 'SUPABASE_SERVICE_KEY'):
                supabase_url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
                service_key = st.secrets["SUPABASE_SERVICE_KEY"]
                
                admin_client = create_client(supabase_url, service_key)
                return admin_client
            else:
                return None
        except Exception as e:
            return None
    
    def _get_user_by_email(self, email: str) -> Optional[str]:
        """
        Get user ID by email using admin API.
        
        Args:
            email: User's email
            
        Returns:
            User ID or None
        """
        try:
            admin_client = self._get_admin_client()
            if not admin_client:
                return None
            
            # List all users and find by email
            response = admin_client.auth.admin.list_users()
            
            if hasattr(response, 'users'):
                users = response.users
            elif isinstance(response, list):
                users = response
            else:
                return None
            
            for user in users:
                if user.email == email:
                    return user.id
            
            return None
            
        except Exception as e:
            return None
    
    def _update_user_password_admin(self, user_id: str, new_password: str) -> bool:
        """
        Update user password using admin API.
        
        Args:
            user_id: User's ID
            new_password: New password
            
        Returns:
            Success boolean
        """
        try:
            admin_client = self._get_admin_client()
            if not admin_client:
                return False
            
            # Update user password
            response = admin_client.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            
            return response is not None
            
        except Exception as e:
            return False
    
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
        """Send password reset email with custom reset code."""
        try:
            reset_code = self._generate_reset_code()
            self._store_reset_code(reset_code, email)
            app_url = self._get_app_url()
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
        NOW ACTUALLY UPDATES PASSWORD using admin API!
        
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
            
            # ⭐ NEW: Get user ID by email
            user_id = self._get_user_by_email(email)
            
            if not user_id:
                # Admin API not available or user not found
                # Mark code as used anyway
                self._invalidate_reset_code(code)
                
                return True, (
                    f"✅ Reset code validated for {email}!\n\n"
                    f"⚠️ Admin API not configured. Please contact administrator to complete password reset.\n\n"
                    f"💡 **For production:** Add SUPABASE_SERVICE_KEY to Streamlit Secrets."
                )
            
            # ⭐ NEW: Update password using admin API!
            success = self._update_user_password_admin(user_id, new_password)
            
            if not success:
                return False, (
                    f"❌ Failed to update password. Please try again or contact support."
                )
            
            # Mark code as used
            self._invalidate_reset_code(code)
            
            return True, (
                f"✅ Password updated successfully for {email}!\n\n"
                f"🎉 You can now login with your new password!"
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
        """Show password reset form with validated code."""
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
                    # ⭐ Reset password with code (NOW ACTUALLY UPDATES!)
                    with st.spinner("Updating password..."):
                        success, message = self.reset_password_with_code(reset_code, new_password)
                    
                    if success:
                        st.success(message)
                        
                        # Only redirect if password was actually updated
                        if "successfully" in message.lower():
                            st.info("💡 Redirecting to login page...")
                            st.query_params.clear()
                            import time
                            time.sleep(3)
                            st.rerun()
                        else:
                            # Admin API not configured
                            st.warning("Please contact administrator to complete password reset.")
                    else:
                        st.error(message)
        
        st.divider()
        if st.button("← Cancel and Return to Login"):
            st.query_params.clear()
            st.rerun()
    
    def show_login_page(self):
        """Display login/signup page with password reset handling."""
        
        self._detect_app_url()
        
        query_params = st.query_params
        
        if 'reset_code' in query_params:
            reset_code = query_params['reset_code']
            valid, email, error_msg = self._validate_reset_code(reset_code)
            
            if valid:
                self._show_password_reset_form(reset_code, email)
                return
            else:
                st.error(f"❌ {error_msg}")
                st.info("💡 Please request a new password reset below.")
        
        st.title("🔐 Events Tracker - Login")
        
        tab1, tab2, tab3 = st.tabs(["Login", "Forgot Password?", "Sign Up"])
        
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
        
        with tab2:
            st.subheader("🔑 Reset Your Password")
            
            st.markdown("""
            **How it works:**
            1. Enter your email address below
            2. Click "Send Reset Code"
            3. You'll receive a **reset code** and **reset link**
            4. Click the link to set your new password
            5. Login with your new password
            
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
