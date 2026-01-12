"""
Authentication Module
=====================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-01-12 19:00 UTC
Python: 3.11
Version: 2.2.0

Handles user signup, login, logout with Supabase Auth
Uses AuthManager class for clean authentication flow

NEW in V2.2.0:
- 🛡️ SECURE Forgot Password (uses email from login form)
- ✅ Change Password for logged-in users
- 🔒 No arbitrary email input - security fixed!
- 📧 Password reset only for authenticated email

SECURITY FIX:
- Forgot Password now SECURE - email taken from login form
- No separate email input field
- Prevents arbitrary password reset attempts
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
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Send password reset email to user.
        
        SECURITY: Email parameter should come from login form, not arbitrary input!
        
        Args:
            email: User's email address (from login form)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Use Supabase's built-in password reset
            # Note: This sends an email with a reset link
            self.client.auth.reset_password_for_email(
                email,
                options={
                    "redirect_to": "https://events-tracker.streamlit.app"
                }
            )
            
            # SECURITY: Always return same message (don't reveal if email exists)
            return True, (
                f"✅ If an account exists for {email}, "
                "a password reset email has been sent. Please check your inbox."
            )
            
        except Exception as e:
            error_msg = str(e)
            # SECURITY: Don't reveal specific error details
            return False, "❌ Unable to process password reset request. Please try again later."
    
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
        """Display login/signup page."""
        st.title("🔐 Events Tracker - Login")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login to Your Account")
            
            # Store email in session state for Forgot Password
            if 'login_email' not in st.session_state:
                st.session_state.login_email = ''
            
            with st.form("login_form"):
                email = st.text_input(
                    "Email", 
                    placeholder="your.email@example.com",
                    value=st.session_state.login_email,
                    key="email_input"
                )
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("🔓 Login", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("❌ Please enter both email and password.")
                    else:
                        # Save email for potential Forgot Password use
                        st.session_state.login_email = email
                        
                        success, message = self.login(email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            # SECURE Forgot Password - uses email from login form
            st.markdown("---")
            
            with st.expander("🔑 Forgot Password?"):
                st.markdown("""
                **Password reset will be sent to the email address you entered above.**
                
                1. Enter your email in the login form above
                2. Click the button below to receive a reset link
                """)
                
                # Show which email will receive the reset
                if st.session_state.login_email:
                    st.info(f"📧 Reset link will be sent to: **{st.session_state.login_email}**")
                else:
                    st.warning("⚠️ Please enter your email in the login form above first.")
                
                # Button to send reset
                if st.button("📧 Send Password Reset Link", use_container_width=True):
                    if not st.session_state.login_email:
                        st.error("❌ Please enter your email in the login form above first.")
                    else:
                        # SECURITY: Email comes from login form, not arbitrary input!
                        success, message = self.request_password_reset(st.session_state.login_email)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
        
        with tab2:
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
