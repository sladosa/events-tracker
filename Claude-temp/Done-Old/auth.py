"""
Authentication Module
Handles user signup, login, logout with Supabase Auth
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
    
    def show_login_page(self):
        """Display login/signup page."""
        st.title("🔐 Events Tracker - Login")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login to Your Account")
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your.email@example.com")
                password = st.text_input("Password", type="password")
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
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
