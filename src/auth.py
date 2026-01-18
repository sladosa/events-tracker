"""
Authentication Module - NATIVE SUPABASE PASSWORD RESET
======================================================
Version: 2.7.0 NATIVE
Last Modified: 2025-01-18 17:00 UTC
Python: 3.11

FEATURES:
- Native Supabase password reset with email
- NO admin API needed!
- Professional email flow
- Production-ready
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
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        self._init_app_url()
    
    def _init_app_url(self):
        """Initialize app URL from secrets or use default."""
        if 'app_url' not in st.session_state:
            env_url = os.getenv('APP_URL')
            if env_url:
                st.session_state.app_url = env_url
                return
            
            try:
                secret_url = st.secrets.get('APP_URL')
                if secret_url:
                    st.session_state.app_url = secret_url
                    return
            except:
                pass
            
            st.session_state.app_url = "https://events-tracker-test.streamlit.app"
    
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
    
    def request_password_reset_native(self, email: str) -> Tuple[bool, str]:
        """
        Request password reset using Supabase's native flow.
        Sends email with magic link - NO ADMIN API NEEDED!
        """
        try:
            # Get app URL for redirect
            app_url = st.session_state.get('app_url', 'https://events-tracker-test.streamlit.app')
            
            # Construct redirect URL
            redirect_url = f"{app_url}?password_reset=true"
            
            # Request password reset email from Supabase
            response = self.client.auth.reset_password_for_email(
                email,
                {
                    'redirect_to': redirect_url
                }
            )
            
            return True, (
                f"✅ Password reset email sent!\n\n"
                f"📧 **Check your inbox for:** {email}\n\n"
                f"📬 **Look for an email from Supabase**\n\n"
                f"💡 Click the link in the email to reset your password.\n\n"
                f"⏰ The link will expire in 1 hour.\n\n"
                f"💌 **Didn't receive it?** Check your spam folder!"
            )
            
        except Exception as e:
            error_msg = str(e)
            if "user not found" in error_msg.lower():
                return False, f"❌ No account found with email: {email}"
            elif "rate limit" in error_msg.lower():
                return False, "❌ Too many requests. Please wait a moment and try again."
            else:
                return False, f"❌ Error sending reset email: {error_msg}"
    
    def handle_password_reset_callback(self) -> bool:
        """
        Handle the callback after user clicks email link.
        Returns True if callback was handled, False otherwise.
        """
        query_params = st.query_params
        
        # Check if this is a password reset callback
        if 'password_reset' not in query_params:
            return False
        
        # Check for access token (from email link)
        if 'access_token' in query_params:
            access_token = query_params['access_token']
            
            try:
                # Set the session with the access token
                response = self.client.auth.set_session(access_token, query_params.get('refresh_token', ''))
                
                if response and response.user:
                    # Show password update form
                    st.title("🔐 Set Your New Password")
                    st.success(f"✅ Email verified for: **{response.user.email}**")
                    
                    st.markdown("---")
                    
                    with st.form("set_new_password_form"):
                        new_password = st.text_input(
                            "New Password",
                            type="password",
                            help="Minimum 6 characters"
                        )
                        confirm_password = st.text_input(
                            "Confirm New Password",
                            type="password"
                        )
                        
                        submit = st.form_submit_button(
                            "✅ Set New Password",
                            use_container_width=True,
                            type="primary"
                        )
                        
                        if submit:
                            if not new_password or not confirm_password:
                                st.error("❌ Please fill in both fields.")
                            elif new_password != confirm_password:
                                st.error("❌ Passwords do not match.")
                            elif len(new_password) < 6:
                                st.error("❌ Password must be at least 6 characters.")
                            else:
                                # Update password
                                try:
                                    update_response = self.client.auth.update_user({
                                        "password": new_password
                                    })
                                    
                                    if update_response:
                                        st.success("✅ Password updated successfully!")
                                        st.balloons()
                                        st.info("💡 Redirecting to login...")
                                        
                                        # Clear query params and redirect
                                        st.query_params.clear()
                                        import time
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update password.")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error updating password: {str(e)}")
                    
                    st.divider()
                    if st.button("← Cancel and Return to Login"):
                        st.query_params.clear()
                        st.rerun()
                    
                    return True
                else:
                    st.error("❌ Invalid or expired reset link.")
                    st.info("💡 Please request a new password reset.")
                    
                    if st.button("← Return to Login"):
                        st.query_params.clear()
                        st.rerun()
                    
                    return True
                    
            except Exception as e:
                st.error(f"❌ Error processing reset link: {str(e)}")
                
                if st.button("← Return to Login"):
                    st.query_params.clear()
                    st.rerun()
                
                return True
        else:
            # Waiting for user to click email link
            st.info("📧 Waiting for email verification...")
            st.markdown("""
            **Please check your email and click the reset link.**
            
            💡 After clicking the link in your email, you'll be redirected here to set your new password.
            
            📬 Didn't receive the email?
            - Check your spam/junk folder
            - Make sure you entered the correct email address
            - Request a new reset link below
            """)
            
            if st.button("← Return to Login"):
                st.query_params.clear()
                st.rerun()
            
            return True
    
    def show_login_page(self):
        """Display login/signup page with native password reset support."""
        
        # First, check if this is a password reset callback
        if self.handle_password_reset_callback():
            return
        
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
            2. Click "Send Reset Email"
            3. Check your email inbox
            4. Click the link in the email
            5. Set your new password
            6. Login with your new password
            
            💡 **Note:** The reset link will expire in 1 hour.
            """)
            
            st.markdown("---")
            
            forgot_email = st.text_input(
                "📧 Your Email Address",
                placeholder="your.email@example.com",
                key="forgot_password_email",
                help="Enter the email you used to create your account"
            )
            
            if st.button("📧 Send Reset Email", use_container_width=True, type="primary"):
                if not forgot_email:
                    st.error("❌ Please enter your email address.")
                elif '@' not in forgot_email or '.' not in forgot_email:
                    st.error("❌ Please enter a valid email address.")
                else:
                    with st.spinner("Sending reset email..."):
                        success, message = self.request_password_reset_native(forgot_email)
                    
                    if success:
                        st.success("✅ Reset email sent!")
                        st.markdown(message)
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
