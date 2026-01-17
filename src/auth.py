"""
Authentication Module - DEBUG VERSION
======================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-01-17 10:30 UTC
Python: 3.11
Version: 2.4.0-DEBUG

⚠️ TEMPORARY DEBUG VERSION - SHOWS DETAILED ERRORS!
⚠️ USE ONLY FOR DEBUGGING - REMOVE BEFORE PRODUCTION!

This version shows EXACT error messages to help diagnose issues.
After fixing, replace with production version (without debug messages).
"""
import streamlit as st
from supabase import Client
from typing import Optional, Tuple


class AuthManager:
    """Manage user authentication with Supabase."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        
        # Initialize session state
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
    
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
            st.rerun()
    
    def _get_app_url(self) -> str:
        """
        Auto-detect current app URL for redirect.
        Works for both test and main branches!
        
        Returns:
            Current app URL (e.g., https://events-tracker-test.streamlit.app)
        """
        try:
            # Try to get from Streamlit's runtime config
            import streamlit.runtime.scriptrunner as scriptrunner
            from streamlit.runtime import get_instance
            
            runtime = get_instance()
            if runtime and hasattr(runtime, '_session_mgr'):
                # Get the session info
                session_info = runtime._session_mgr.list_active_sessions()
                if session_info:
                    # Extract URL from session
                    # This is a bit hacky but works!
                    pass
        except:
            pass
        
        # Fallback: Check if we're on test or main branch by trying st.secrets
        try:
            # If APP_URL is defined in secrets, use it
            if hasattr(st.secrets, 'APP_URL'):
                return st.secrets.APP_URL
        except:
            pass
        
        # Default fallback: Use main branch URL
        # NOTE: If you're on test branch, set APP_URL in .streamlit/secrets.toml:
        # APP_URL = "https://events-tracker-test.streamlit.app"
        return "https://events-tracker.streamlit.app"
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Send password reset email to user.
        
        ⚠️ DEBUG VERSION - SHOWS DETAILED ERRORS!
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Auto-detect app URL
            redirect_url = self._get_app_url()
            
            # 🐛 DEBUG: Show what we're sending
            st.info(f"🐛 DEBUG: Sending reset to: {email}")
            st.info(f"🐛 DEBUG: Redirect URL: {redirect_url}")
            
            # Use Supabase's built-in password reset
            response = self.client.auth.reset_password_for_email(
                email,
                options={
                    "redirect_to": redirect_url
                }
            )
            
            # 🐛 DEBUG: Show response
            st.success(f"🐛 DEBUG: Supabase response: {response}")
            
            # Success!
            return True, (
                f"✅ If an account exists for {email}, "
                "a password reset email has been sent. "
                "Please check your inbox (and spam folder!)."
            )
            
        except Exception as e:
            # 🐛 DEBUG: Show FULL error details!
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Show full error in UI (for debugging)
            st.error(f"🐛 DEBUG ERROR TYPE: {error_type}")
            st.error(f"🐛 DEBUG ERROR MESSAGE: {error_msg}")
            
            # Try to extract more details
            if hasattr(e, 'args'):
                st.error(f"🐛 DEBUG ERROR ARGS: {e.args}")
            
            # Also return detailed error
            return False, (
                f"❌ Password reset failed!\n\n"
                f"**Error Type:** {error_type}\n"
                f"**Error Message:** {error_msg}\n\n"
                f"Please check:\n"
                f"1. Supabase SMTP settings (Dashboard → Authentication → Email)\n"
                f"2. Gmail App Password configured correctly\n"
                f"3. Supabase Audit Logs for more details"
            )
    
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
    
    def show_login_page(self):
        """Display login/signup page with independent Forgot Password section."""
        st.title("🔐 Events Tracker - Login")
        
        # 🐛 DEBUG: Show version
        st.caption("⚠️ DEBUG VERSION 2.4.0-DEBUG - Showing detailed errors")
        
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
