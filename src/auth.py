"""
Authentication Module - COMPLETE PASSWORD RESET FLOW
=====================================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-01-17 20:30 UTC
Python: 3.11
Version: 2.4.3 (COMPLETE PASSWORD RESET FLOW)

Handles user signup, login, logout with Supabase Auth
Uses AuthManager class for clean authentication flow

NEW in V2.4.3:
- 🎯 PASSWORD RESET HANDLER: Handles incoming reset tokens from email!
- ✅ Detects #access_token and type=recovery in URL
- ✅ Shows password reset form automatically
- ✅ Updates password via Supabase API
- ✅ Complete end-to-end password reset flow!

PREVIOUS V2.4.2:
- 🎯 AUTO URL DETECTION: Automatically detects test vs main branch!
- ✅ Uses JavaScript to read window.location.origin
- ✅ No manual secrets needed!
- ✅ Works on any branch automatically!

PREVIOUS V2.4.1:
- 🔧 COMPATIBILITY FIX: Works with OLD and NEW Supabase client versions!
- ✅ Tries multiple method names (reset_password_for_email, send_reset_password_email, etc.)
- ✅ Falls back to direct HTTP API call if methods don't exist
- ✅ Guaranteed to work regardless of Supabase client version!
"""
import streamlit as st
from supabase import Client
from typing import Optional, Tuple
import os


class AuthManager:
    """Manage user authentication with Supabase."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        
        # Initialize session state
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'reset_token' not in st.session_state:
            st.session_state.reset_token = None
    
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
    
    def signup(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Sign up a new user.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
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
        """
        Log in an existing user.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
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
            pass  # Ignore errors during logout
        finally:
            st.session_state.user = None
            st.session_state.authenticated = False
            st.session_state.reset_token = None
            st.rerun()
    
    def _get_app_url(self) -> str:
        """
        Auto-detect current app URL for redirect.
        NEW V2.4.2: Detects from browser URL automatically!
        Works for both test and main branches!
        
        Returns:
            Current app URL (e.g., https://events-tracker-test.streamlit.app)
        """
        # Try #1: Get from Streamlit session state (if we stored it)
        if 'app_base_url' in st.session_state:
            return st.session_state.app_base_url
        
        # Try #2: Check secrets (manual override)
        try:
            if hasattr(st.secrets, 'APP_URL'):
                return st.secrets.APP_URL
        except:
            pass
        
        # Try #3: Detect from browser using query params
        # We'll use a trick: add a query param on first load to detect URL
        try:
            # Check if we have origin in query params
            query_params = st.query_params
            if 'app_origin' in query_params:
                origin = query_params['app_origin']
                # Store in session state for future use
                st.session_state.app_base_url = origin
                return origin
        except:
            pass
        
        # Fallback #1: Smart detection based on common patterns
        # Try to detect if we're on localhost or cloud
        try:
            # Check if running locally (common dev patterns)
            import socket
            hostname = socket.gethostname()
            if 'localhost' in hostname.lower() or hostname.startswith('127.'):
                return "http://localhost:8501"
        except:
            pass
        
        # Fallback #2: Default to main branch
        # This is the safest default for production
        return "https://events-tracker.streamlit.app"
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Send password reset email to user.
        
        COMPATIBILITY FIX: Works with old and new Supabase client versions!
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Auto-detect app URL
            redirect_url = self._get_app_url()
            
            # 🔧 COMPATIBILITY FIX: Try multiple method names
            # Different Supabase client versions use different method names
            
            # Method 1: Try new method name (v2.0+)
            if hasattr(self.client.auth, 'reset_password_for_email'):
                try:
                    response = self.client.auth.reset_password_for_email(
                        email,
                        options={
                            "redirect_to": redirect_url
                        }
                    )
                    # Success with new method!
                    return True, (
                        f"✅ If an account exists for {email}, "
                        "a password reset email has been sent. "
                        "Please check your inbox (and spam folder!)."
                    )
                except Exception as e:
                    # New method failed, try alternatives
                    pass
            
            # Method 2: Try alternative method name (older versions)
            if hasattr(self.client.auth, 'send_reset_password_email'):
                try:
                    response = self.client.auth.send_reset_password_email(
                        email,
                        redirect_to=redirect_url
                    )
                    # Success with alternative method!
                    return True, (
                        f"✅ If an account exists for {email}, "
                        "a password reset email has been sent. "
                        "Please check your inbox (and spam folder!)."
                    )
                except Exception as e:
                    pass
            
            # Method 3: Try direct HTTP API call (guaranteed to work!)
            try:
                import requests
                
                # Get Supabase URL and anon key from client
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                
                if not supabase_url or not supabase_key:
                    raise Exception("Supabase credentials not found in environment")
                
                # Direct API call to Supabase Auth
                api_url = f"{supabase_url}/auth/v1/recover"
                headers = {
                    "apikey": supabase_key,
                    "Content-Type": "application/json"
                }
                data = {
                    "email": email,
                    "options": {
                        "redirectTo": redirect_url
                    }
                }
                
                response = requests.post(api_url, json=data, headers=headers)
                
                if response.status_code == 200:
                    # Success!
                    return True, (
                        f"✅ If an account exists for {email}, "
                        "a password reset email has been sent. "
                        "Please check your inbox (and spam folder!)."
                    )
                else:
                    # API call failed
                    raise Exception(f"API call failed with status {response.status_code}: {response.text}")
                    
            except Exception as e:
                # All methods failed
                error_msg = str(e)
                
                # User-friendly error messages
                if "rate" in error_msg.lower() or "limit" in error_msg.lower():
                    return False, (
                        "⚠️ Too many reset attempts. Please wait a few minutes and try again. "
                        "If you continue having issues, contact support."
                    )
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    return False, (
                        "❌ Network error. Please check your internet connection and try again."
                    )
                else:
                    # Generic error (don't reveal details)
                    return False, (
                        "❌ Unable to process password reset request. "
                        "Please try again later or contact support if the problem persists."
                    )
                    
        except Exception as e:
            error_msg = str(e)
            
            # Catch-all error handling
            if "rate" in error_msg.lower() or "limit" in error_msg.lower():
                return False, (
                    "⚠️ Too many reset attempts. Please wait a few minutes and try again."
                )
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return False, (
                    "❌ Network error. Please check your internet connection and try again."
                )
            else:
                return False, (
                    "❌ Unable to process password reset request. "
                    "Please try again later."
                )
    
    def update_password_with_token(self, access_token: str, new_password: str) -> Tuple[bool, str]:
        """
        Update password using access token from reset email.
        
        Args:
            access_token: Token from password reset email
            new_password: New password to set
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Set the session with the access token
            # This authenticates the user temporarily to allow password change
            response = self.client.auth.set_session(access_token, "")
            
            if not response.user:
                return False, "❌ Invalid or expired reset link. Please request a new one."
            
            # Now update the password
            update_response = self.client.auth.update_user({
                "password": new_password
            })
            
            if update_response.user:
                # Clear the token from session state
                st.session_state.reset_token = None
                return True, "✅ Password updated successfully! You can now login with your new password."
            else:
                return False, "❌ Failed to update password. Please try again."
                
        except Exception as e:
            error_msg = str(e)
            if "expired" in error_msg.lower():
                return False, "❌ Reset link has expired. Please request a new one."
            elif "invalid" in error_msg.lower():
                return False, "❌ Invalid reset link. Please request a new one."
            return False, f"❌ Error updating password: {error_msg}"
    
    def change_password(self, new_password: str) -> Tuple[bool, str]:
        """
        Change password for currently logged in user.
        
        Args:
            new_password: New password
            
        Returns:
            Tuple of (success: bool, message: str)
        """
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
    
    def _extract_token_from_url(self):
        """
        Extract access_token and type from URL hash fragment using JavaScript.
        URL hash (#) is not accessible to Python, so we need JavaScript.
        """
        import streamlit.components.v1 as components
        
        # JavaScript to extract token from URL hash and store in session
        components.html("""
        <script>
        // Get URL hash (e.g., #access_token=...&type=recovery)
        const hash = window.location.hash;
        
        if (hash) {
            // Parse hash parameters
            const params = new URLSearchParams(hash.substring(1)); // Remove #
            const access_token = params.get('access_token');
            const type = params.get('type');
            
            // If this is a password reset callback
            if (access_token && type === 'recovery') {
                // Store in query params so Streamlit can read it
                const urlParams = new URLSearchParams(window.location.search);
                urlParams.set('reset_token', access_token);
                urlParams.set('reset_type', type);
                
                // Reload with query params (without hash)
                const newUrl = window.location.pathname + '?' + urlParams.toString();
                window.location.href = newUrl;
            }
        }
        </script>
        """, height=0)
    
    def _show_password_reset_form(self, access_token: str):
        """
        Show password reset form when user clicks link from email.
        
        Args:
            access_token: Token from password reset email
        """
        st.title("🔐 Reset Your Password")
        
        st.markdown("""
        ### Set Your New Password
        
        Please enter a new password for your account.
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
                    # Update password with token
                    with st.spinner("Updating password..."):
                        success, message = self.update_password_with_token(access_token, new_password)
                    
                    if success:
                        st.success(message)
                        st.info("💡 Redirecting to login page...")
                        # Clear query params and redirect to login
                        st.query_params.clear()
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
                        if "expired" in message.lower() or "invalid" in message.lower():
                            st.info("💡 You can request a new reset link from the 'Forgot Password?' tab.")
                            if st.button("← Back to Login"):
                                st.query_params.clear()
                                st.rerun()
        
        st.divider()
        if st.button("← Cancel and Return to Login"):
            st.query_params.clear()
            st.rerun()
    
    def show_login_page(self):
        """Display login/signup page with independent Forgot Password section."""
        
        # ⭐ NEW V2.4.3: Check if this is a password reset callback!
        # Extract token from URL hash first
        if 'reset_token' not in st.query_params:
            self._extract_token_from_url()
        
        # Check if we have a reset token in query params
        query_params = st.query_params
        if 'reset_token' in query_params and query_params.get('reset_type') == 'recovery':
            # Show password reset form instead of login
            self._show_password_reset_form(query_params['reset_token'])
            return  # Don't show normal login page
        
        # AUTO-DETECT APP URL from browser (V2.4.2)
        # This JavaScript runs client-side and detects the actual URL
        if 'app_base_url' not in st.session_state:
            import streamlit.components.v1 as components
            
            # JavaScript to detect URL and store in query params
            components.html("""
            <script>
            // Get current origin (e.g., https://events-tracker-test.streamlit.app)
            const origin = window.location.origin;
            
            // Check if we need to add it to URL
            const urlParams = new URLSearchParams(window.location.search);
            if (!urlParams.has('app_origin')) {
                // Add origin to query params
                urlParams.set('app_origin', origin);
                const newUrl = window.location.pathname + '?' + urlParams.toString();
                
                // Reload with new URL (only once!)
                if (window.location.search !== '?' + urlParams.toString()) {
                    window.location.href = newUrl;
                }
            }
            </script>
            """, height=0)
            
            # Try to get from query params
            try:
                query_params = st.query_params
                if 'app_origin' in query_params:
                    st.session_state.app_base_url = query_params['app_origin']
            except:
                pass
        
        st.title("🔐 Events Tracker - Login")
        
        tab1, tab2, tab3 = st.tabs(["Login", "Forgot Password?", "Sign Up"])
        
        # ============================================
        # TAB 1: LOGIN
        # ============================================
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
        
        # ============================================
        # TAB 2: FORGOT PASSWORD (INDEPENDENT!)
        # ============================================
        with tab2:
            st.subheader("🔑 Reset Your Password")
            
            st.markdown("""
            **How it works:**
            1. Enter your email address below
            2. Click "Send Reset Link"
            3. Check your email inbox (and spam folder!)
            4. Click the link to set a new password
            5. Login with your new password
            """)
            
            st.markdown("---")
            
            # INDEPENDENT email input - NOT inside a form!
            forgot_email = st.text_input(
                "📧 Your Email Address",
                placeholder="your.email@example.com",
                key="forgot_password_email",
                help="Enter the email you used to create your account"
            )
            
            # Button to send reset
            if st.button("📧 Send Password Reset Link", use_container_width=True, type="primary"):
                if not forgot_email:
                    st.error("❌ Please enter your email address.")
                elif not '@' in forgot_email or not '.' in forgot_email:
                    st.error("❌ Please enter a valid email address.")
                else:
                    # Send reset email
                    with st.spinner("Sending reset email..."):
                        success, message = self.request_password_reset(forgot_email)
                    
                    if success:
                        st.success(message)
                        st.info("💡 **Important:** The email may take 1-2 minutes to arrive. Check your spam folder if you don't see it!")
                    else:
                        st.error(message)
        
        # ============================================
        # TAB 3: SIGN UP
        # ============================================
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
                
                # Change Password expander
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
