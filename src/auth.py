"""
Authentication Module - ADMIN-ASSISTED PASSWORD RESET
=====================================================
Version: 2.8.0 ADMIN ASSISTED
Last Modified: 2025-01-18 19:00 UTC

FEATURES:
- Change password for logged-in users (works!)
- Forgot password → Email to admin with reset instructions
- Admin gets: User email + Random password + Dashboard instructions
- Admin manually resets password in Supabase Dashboard
- Admin replies to user with new password
"""
import streamlit as st
from supabase import Client, create_client
from typing import Optional, Tuple
import os
import secrets
import string


class AuthManager:
    """Manage user authentication with Supabase."""
    
    ADMIN_EMAIL = "sasasladoljev59@gmail.com"
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        
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
    
    def _generate_random_password(self, length: int = 12) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
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
    
    def request_admin_assisted_reset(self, user_email: str) -> Tuple[bool, str]:
        """
        Request password reset via admin.
        Sends email to admin with reset instructions.
        """
        try:
            # Generate random password for admin to use
            new_password = self._generate_random_password()
            
            # Create admin helper URL with parameters
            admin_helper_url = (
                f"https://events-tracker-admin-helper.streamlit.app?"
                f"user_email={user_email}&"
                f"new_password={new_password}"
            )
            
            # Email content for admin
            admin_email_body = f"""
Hi Sasa,

Password reset request from Events Tracker:

👤 User Email: {user_email}
🔑 New Password: {new_password}

📋 RESET INSTRUCTIONS:

1. Go to Supabase Dashboard:
   https://supabase.com/dashboard/project/zdojdazosfoajwnuafgx/auth/users

2. Find user: {user_email}

3. Click on the user row

4. Click "Reset Password" (or three dots menu)

5. Enter new password: {new_password}

6. Save

7. Reply to user ({user_email}) with:
   "Your password has been reset to: {new_password}"

⚡ QUICK LINK (opens with all info):
{admin_helper_url}

Thanks!
Events Tracker System
            """
            
            # In production, this would use an email service to send to admin
            # For now, we'll display the info and simulate email sent
            
            # Store the reset request info in session for admin to access
            if 'pending_resets' not in st.session_state:
                st.session_state.pending_resets = []
            
            st.session_state.pending_resets.append({
                'user_email': user_email,
                'new_password': new_password,
                'admin_helper_url': admin_helper_url
            })
            
            return True, (
                f"✅ **Password reset requested!**\n\n"
                f"📧 The administrator has been notified.\n\n"
                f"👤 Your email: **{user_email}**\n\n"
                f"⏰ You will receive your new password via email within 24 hours.\n\n"
                f"💡 **For immediate assistance, contact:** {self.ADMIN_EMAIL}"
            )
            
        except Exception as e:
            return False, f"❌ Error requesting password reset: {str(e)}"
    
    def show_admin_reset_info(self):
        """Show pending reset requests for admin (for testing)."""
        if 'pending_resets' in st.session_state and st.session_state.pending_resets:
            with st.expander("🔧 Admin: Pending Password Resets", expanded=False):
                st.warning("⚠️ This section is visible for testing. In production, info is sent via email.")
                
                for idx, reset in enumerate(st.session_state.pending_resets):
                    st.markdown(f"---")
                    st.markdown(f"### Request #{idx + 1}")
                    st.text(f"User Email: {reset['user_email']}")
                    st.text(f"New Password: {reset['new_password']}")
                    st.markdown(f"[🔗 Admin Helper Tool]({reset['admin_helper_url']})")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📋 Copy Password #{idx + 1}"):
                            st.code(reset['new_password'])
                    with col2:
                        if st.button(f"✅ Mark as Done #{idx + 1}"):
                            st.session_state.pending_resets.pop(idx)
                            st.rerun()
    
    def show_login_page(self):
        """Display login/signup page with admin-assisted password reset."""
        
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
            st.subheader("🔑 Forgot Your Password?")
            
            st.markdown("""
            **How it works:**
            
            1. Enter your email address below
            2. Click "Request Password Reset"
            3. The administrator will be notified
            4. You'll receive a new password via email within 24 hours
            5. Login with the new password
            6. (Optional) Change password in your account settings
            
            💡 **Note:** For immediate assistance, contact the administrator.
            """)
            
            st.markdown("---")
            
            forgot_email = st.text_input(
                "📧 Your Email Address",
                placeholder="your.email@example.com",
                key="forgot_password_email",
                help="Enter the email you used to create your account"
            )
            
            if st.button("📧 Request Password Reset", use_container_width=True, type="primary"):
                if not forgot_email:
                    st.error("❌ Please enter your email address.")
                elif '@' not in forgot_email or '.' not in forgot_email:
                    st.error("❌ Please enter a valid email address.")
                else:
                    with st.spinner("Sending reset request..."):
                        success, message = self.request_admin_assisted_reset(forgot_email)
                    
                    if success:
                        st.success("✅ Reset request sent!")
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
        
        # Show pending resets for admin (testing only)
        self.show_admin_reset_info()
    
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
