"""
Supabase authentication module for multi-tenant CV generator.
Handles user registration, login, logout, and session management.
"""

import os
import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SupabaseAuth:
    """Handles authentication with Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
    
    def register_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with success status and user data or error message
        """
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                logger.info(f"User registered successfully: {email}")
                return {
                    "success": True,
                    "user": response.user,
                    "message": "Registration successful! Please check your email for verification."
                }
            else:
                return {
                    "success": False,
                    "error": "Registration failed"
                }
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with success status and user data or error message
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                logger.info(f"User logged in successfully: {email}")
                return {
                    "success": True,
                    "user": response.user,
                    "session": response.session,
                    "user_id": response.user.id
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def logout_user(self) -> Dict[str, Any]:
        """
        Logout the current user.
        
        Returns:
            Dictionary with success status
        """
        try:
            response = self.supabase.auth.sign_out()
            logger.info("User logged out successfully")
            return {
                "success": True,
                "message": "Logged out successfully"
            }
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current authenticated user.
        
        Returns:
            User data if authenticated, None otherwise
        """
        try:
            response = self.supabase.auth.get_user()
            if response.user:
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at
                }
            return None
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return None
    
    def refresh_session(self) -> Dict[str, Any]:
        """
        Refresh the current session.
        
        Returns:
            Dictionary with success status and new session data
        """
        try:
            response = self.supabase.auth.refresh_session()
            if response.session:
                return {
                    "success": True,
                    "session": response.session
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to refresh session"
                }
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class StreamlitAuth:
    """Streamlit-specific authentication wrapper."""
    
    def __init__(self):
        self.auth = SupabaseAuth()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state for authentication."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'user_email' not in st.session_state:
            st.session_state.user_email = None
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
    
    def show_login_page(self):
        """Display the login/registration page."""
        st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1 style="color: #2c3e50; margin-bottom: 30px;">🎯 Grounded CV Generator</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin-bottom: 40px;">
                AI-powered CV generation with evidence-based matching
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for login and registration
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            self._show_login_form()
        
        with tab2:
            self._show_registration_form()
    
    def _show_login_form(self):
        """Display the login form."""
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if email and password:
                    with st.spinner("Logging in..."):
                        result = self.auth.login_user(email, password)
                    
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_email = result["user"].email
                        st.session_state.session_token = result["session"].access_token
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result['error']}")
                else:
                    st.error("Please enter both email and password")
    
    def _show_registration_form(self):
        """Display the registration form."""
        st.subheader("Create New Account")
        
        with st.form("registration_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        with st.spinner("Creating account..."):
                            result = self.auth.register_user(email, password)
                        
                        if result["success"]:
                            st.success(result["message"])
                            st.info("Please check your email and verify your account before logging in.")
                        else:
                            st.error(f"Registration failed: {result['error']}")
                else:
                    st.error("Please fill in all fields")
    
    def show_user_info(self):
        """Display user information and logout option."""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"👤 Logged in as: **{st.session_state.user_email}**")
        
        with col2:
            if st.button("Logout"):
                self.logout()
    
    def logout(self):
        """Logout the current user."""
        result = self.auth.logout_user()
        
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.session_token = None
        
        st.success("Logged out successfully!")
        st.rerun()
    
    def require_authentication(self) -> Optional[str]:
        """
        Require authentication for the current page.
        
        Returns:
            User ID if authenticated, None otherwise
        """
        self.initialize_session_state()
        
        if not st.session_state.authenticated:
            self.show_login_page()
            return None
        
        return st.session_state.user_id
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        self.initialize_session_state()
        return st.session_state.authenticated
