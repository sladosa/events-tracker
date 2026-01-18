"""
DEBUG VERSION - Authentication Module
Shows detailed info about secrets configuration
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
    
    def _debug_secrets_info(self) -> str:
        """
        🔍 DEBUG: Show detailed secrets configuration info
        """
        debug_info = []
        
        debug_info.append("=" * 60)
        debug_info.append("🔍 SECRETS DEBUG INFO")
        debug_info.append("=" * 60)
        
        # Check if secrets exist
        debug_info.append(f"\n1. st.secrets exists: {hasattr(st, 'secrets')}")
        
        if hasattr(st, 'secrets'):
            # List all available secrets (without showing values)
            try:
                available_keys = list(st.secrets.keys())
                debug_info.append(f"2. Available secret keys: {available_keys}")
            except:
                debug_info.append("2. Cannot list secret keys")
            
            # Check specific keys
            has_url = hasattr(st.secrets, 'SUPABASE_URL')
            has_key = hasattr(st.secrets, 'SUPABASE_KEY')
            has_service = hasattr(st.secrets, 'SUPABASE_SERVICE_KEY')
            
            debug_info.append(f"\n3. Has SUPABASE_URL: {has_url}")
            debug_info.append(f"4. Has SUPABASE_KEY: {has_key}")
            debug_info.append(f"5. Has SUPABASE_SERVICE_KEY: {has_service}")
            
            # Show partial values (first/last chars + length)
            if has_url:
                url = st.secrets.get("SUPABASE_URL", "")
                debug_info.append(f"\n6. SUPABASE_URL: {url[:30]}...{url[-10:] if len(url) > 40 else ''}")
            
            if has_key:
                key = st.secrets.get("SUPABASE_KEY", "")
                debug_info.append(f"\n7. SUPABASE_KEY:")
                debug_info.append(f"   Length: {len(key)} chars")
                debug_info.append(f"   First 20: {key[:20]}...")
                debug_info.append(f"   Last 15:  ...{key[-15:]}")
            
            if has_service:
                service_key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
                debug_info.append(f"\n8. SUPABASE_SERVICE_KEY:")
                debug_info.append(f"   Length: {len(service_key)} chars")
                debug_info.append(f"   First 20: {service_key[:20]}...")
                debug_info.append(f"   Last 15:  ...{service_key[-15:]}")
                
                # Compare with anon key
                if has_key:
                    anon_key = st.secrets.get("SUPABASE_KEY", "")
                    if service_key == anon_key:
                        debug_info.append(f"\n   ⚠️ WARNING: Service key is SAME as anon key!")
                        debug_info.append(f"   ⚠️ This is WRONG! They must be different!")
                    else:
                        debug_info.append(f"\n   ✅ Service key is DIFFERENT from anon key (Good!)")
            else:
                debug_info.append("\n⚠️ SUPABASE_SERVICE_KEY NOT FOUND!")
                debug_info.append("   This is why password reset fails!")
                
            # Check environment variables
            debug_info.append(f"\n9. ENV SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')[:30]}...")
            debug_info.append(f"10. ENV SUPABASE_KEY: {'SET' if os.getenv('SUPABASE_KEY') else 'NOT SET'}")
            debug_info.append(f"11. ENV SUPABASE_SERVICE_KEY: {'SET' if os.getenv('SUPABASE_SERVICE_KEY') else 'NOT SET'}")
            
        debug_info.append("\n" + "=" * 60)
        
        return "\n".join(debug_info)
    
    def _get_admin_client(self) -> Optional[Client]:
        """
        Create Supabase admin client using service role key.
        NOW WITH DETAILED DEBUG INFO!
        
        Returns:
            Admin client or None if service key not available
        """
        try:
            # 🔍 DEBUG: Log what we're checking
            st.info("🔍 Checking for SUPABASE_SERVICE_KEY...")
            
            # Check method 1: Direct attribute check
            has_service_key_attr = hasattr(st.secrets, 'SUPABASE_SERVICE_KEY')
            st.write(f"hasattr(st.secrets, 'SUPABASE_SERVICE_KEY'): {has_service_key_attr}")
            
            # Check method 2: Try to get it
            try:
                service_key_get = st.secrets.get("SUPABASE_SERVICE_KEY")
                st.write(f"st.secrets.get('SUPABASE_SERVICE_KEY'): {'Found' if service_key_get else 'None'}")
            except Exception as e:
                st.write(f"st.secrets.get() failed: {e}")
            
            # Check method 3: Dictionary access
            try:
                service_key_dict = st.secrets["SUPABASE_SERVICE_KEY"]
                st.write(f"st.secrets['SUPABASE_SERVICE_KEY']: Found")
            except Exception as e:
                st.write(f"st.secrets['...'] failed: {e}")
            
            # Try to get service role key from secrets
            if hasattr(st.secrets, 'SUPABASE_SERVICE_KEY'):
                st.success("✅ SUPABASE_SERVICE_KEY found!")
                
                supabase_url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
                service_key = st.secrets["SUPABASE_SERVICE_KEY"]
                
                # Show partial key for verification
                st.write(f"Service key (first 20 chars): {service_key[:20]}...")
                
                admin_client = create_client(supabase_url, service_key)
                st.success("✅ Admin client created successfully!")
                return admin_client
            else:
                st.error("❌ SUPABASE_SERVICE_KEY NOT FOUND in secrets!")
                st.write("Available keys:", list(st.secrets.keys()))
                return None
        except Exception as e:
            st.error(f"❌ Error creating admin client: {e}")
            st.exception(e)
            return None
    
    def _get_user_by_email(self, email: str) -> Optional[str]:
        """
        Get user ID by email using admin API.
        
        Args:
            email: User's email
            
        Returns:
            User ID or None if not found
        """
        admin_client = self._get_admin_client()
        if not admin_client:
            st.error("❌ Admin client not available - cannot get user by email")
            return None
        
        try:
            # Use admin API to list users and find by email
            response = admin_client.auth.admin.list_users()
            
            if response and hasattr(response, 'users'):
                for user in response.users:
                    if user.email == email:
                        st.success(f"✅ Found user: {user.id}")
                        return user.id
            
            st.warning(f"⚠️ User not found: {email}")
            return None
        except Exception as e:
            st.error(f"❌ Error getting user by email: {e}")
            st.exception(e)
            return None
    
    def _update_user_password_admin(self, user_id: str, new_password: str) -> bool:
        """
        Update user password using admin API.
        
        Args:
            user_id: User's UUID
            new_password: New password to set
            
        Returns:
            True if successful, False otherwise
        """
        admin_client = self._get_admin_client()
        if not admin_client:
            st.error("❌ Admin client not available - cannot update password")
            return False
        
        try:
            st.info(f"🔄 Updating password for user: {user_id}")
            
            response = admin_client.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            
            if response:
                st.success("✅ Password updated in Supabase!")
                return True
            else:
                st.error("❌ Password update returned no response")
                return False
        except Exception as e:
            st.error(f"❌ Error updating password: {e}")
            st.exception(e)
            return False
    
    def signup(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                return True, "✅ Account created! Please check your email to confirm."
            else:
                return False, "❌ Signup failed. Please try again."
        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                return False, "❌ Email already registered. Try logging in or resetting password."
            elif "invalid email" in error_msg.lower():
                return False, "❌ Invalid email format."
            elif "password" in error_msg.lower():
                return False, "❌ Password must be at least 6 characters."
            else:
                return False, f"❌ Signup error: {error_msg}"
    
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
                return True, f"✅ Welcome back, {email}!"
            else:
                return False, "❌ Login failed."
        except Exception as e:
            error_msg = str(e)
            if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
                return False, "❌ Invalid email or password."
            elif "email not confirmed" in error_msg.lower():
                return False, "❌ Please confirm your email first."
            else:
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
    
    def change_password(self, new_password: str) -> Tuple[bool, str]:
        """Change password for authenticated user."""
        if not self.is_authenticated():
            return False, "❌ You must be logged in to change password."
        
        try:
            response = self.client.auth.update_user({
                "password": new_password
            })
            
            if response:
                return True, "✅ Password changed successfully!"
            else:
                return False, "❌ Password change failed."
        except Exception as e:
            return False, f"❌ Error changing password: {str(e)}"
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Request password reset - generates reset code and link.
        NOW WITH DEBUG INFO AND FIXED URL!
        """
        try:
            # 🔍 SHOW DEBUG INFO
            st.code(self._debug_secrets_info())
            
            # Generate secure reset code
            reset_code = self._generate_reset_code()
            
            # Store code with email
            self._store_reset_code(reset_code, email)
            
            # Get current app URL - use session state
            app_url = st.session_state.get('app_url', 'https://events-tracker-test.streamlit.app')
            
            st.write(f"🔗 Using app URL: {app_url}")
            
            # Create reset link - SIMPLE format
            reset_link = f"{app_url}?reset_code={reset_code}"
            
            st.write(f"🔗 Generated reset link: {reset_link}")
            
            # 🚧 DEMO MODE: Show link in UI instead of sending email
            return True, (
                f"✅ Password reset requested!\n\n"
                f"**Reset Code:** `{reset_code}`\n\n"
                f"**Reset Link (copy this URL to a new tab):**\n\n"
                f"`{reset_link}`\n\n"
                f"💡 Copy the link above and paste it into a new browser tab.\n\n"
                f"💡 In production, this would be sent to {email}."
            )
            
        except Exception as e:
            st.error(f"Exception details: {e}")
            import traceback
            st.code(traceback.format_exc())
            return False, f"❌ Error requesting password reset: {str(e)}"
    
    def reset_password_with_code(self, reset_code: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset password using reset code.
        V2.5.2: NOW ACTUALLY UPDATES PASSWORD IN SUPABASE!
        """
        try:
            # Validate code
            valid, email, error_msg = self._validate_reset_code(reset_code)
            if not valid:
                return False, error_msg
            
            # 🔑 TRY TO GET ADMIN CLIENT (with debug info)
            admin_client = self._get_admin_client()
            if not admin_client:
                st.error("⚠️ Admin API not configured. Please contact administrator to complete password reset.")
                st.info("💡 For production: Add SUPABASE_SERVICE_KEY to Streamlit Secrets.")
                # Still mark code as used even if we can't update password
                self._invalidate_reset_code(reset_code)
                return True, f"✅ Reset code validated for {email}!"
            
            # ⭐ GET USER ID BY EMAIL
            st.info(f"🔍 Looking up user: {email}")
            user_id = self._get_user_by_email(email)
            if not user_id:
                return False, f"❌ Could not find user with email: {email}"
            
            # ⭐ UPDATE PASSWORD VIA ADMIN API
            st.info(f"🔄 Updating password via Admin API...")
            success = self._update_user_password_admin(user_id, new_password)
            
            if success:
                # Mark code as used
                self._invalidate_reset_code(reset_code)
                
                return True, (
                    f"✅ Password updated successfully for {email}!\n\n"
                    f"🎉 You can now login with your new password!"
                )
            else:
                return False, "❌ Failed to update password in Supabase."
            
        except Exception as e:
            return False, f"❌ Error resetting password: {str(e)}"
    
    def _detect_app_url(self):
        """
        Detect the current app URL for reset links.
        SIMPLIFIED: Use environment variable or default.
        """
        if 'app_url' not in st.session_state:
            # Try to get from environment first
            env_url = os.getenv('APP_URL')
            
            if env_url:
                st.session_state.app_url = env_url
            else:
                # Default to test-branch
                # User can override this in Streamlit Secrets if needed
                try:
                    custom_url = st.secrets.get('APP_URL')
                    if custom_url:
                        st.session_state.app_url = custom_url
                    else:
                        # Hardcoded default
                        st.session_state.app_url = "https://events-tracker-test.streamlit.app"
                except:
                    st.session_state.app_url = "https://events-tracker-test.streamlit.app"
    
    def _show_password_reset_form(self, reset_code: str, email: str):
        """Show password reset form after validating code."""
        st.title("🔐 Reset Your Password")
        
        st.success(f"✅ Reset code validated for: **{email}**")
        
        st.markdown("---")
        st.subheader("Set Your New Password")
        st.caption("Enter a new password for your account.")
        
        with st.form("reset_password_form"):
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
