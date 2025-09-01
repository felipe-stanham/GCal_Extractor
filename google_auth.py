"""
Google OAuth 2.0 authentication module for GCal Extractor.
Handles OAuth flow, token management, and automatic refresh.
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import streamlit as st

# OAuth 2.0 scopes for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# OAuth client configuration (will be set up later)
CLIENT_CONFIG = {
    "web": {
        "client_id": "your_client_id_here",
        "client_secret": "your_client_secret_here",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8501"]
    }
}

TOKEN_FILE = 'tokens.json'


class GoogleAuth:
    """Handles Google OAuth authentication and token management."""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        
    def load_credentials(self):
        """Load existing credentials from token file."""
        if os.path.exists(TOKEN_FILE):
            try:
                self.credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                return True
            except Exception as e:
                st.error(f"Error loading credentials: {e}")
                return False
        return False
    
    def save_credentials(self):
        """Save credentials to token file."""
        if self.credentials:
            try:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(self.credentials.to_json())
                return True
            except Exception as e:
                st.error(f"Error saving credentials: {e}")
                return False
        return False
    
    def refresh_credentials(self):
        """Refresh expired credentials."""
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                self.save_credentials()
                return True
            except Exception as e:
                st.error(f"Error refreshing credentials: {e}")
                return False
        return False
    
    def is_authenticated(self):
        """Check if user is authenticated with valid credentials."""
        if not self.credentials:
            self.load_credentials()
        
        if not self.credentials:
            return False
        
        if self.credentials.expired:
            if not self.refresh_credentials():
                return False
        
        return self.credentials.valid
    
    def get_authorization_url(self):
        """Get OAuth authorization URL for user authentication."""
        try:
            flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
            flow.redirect_uri = "http://localhost:8501"
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store flow in session state for later use
            st.session_state['oauth_flow'] = flow
            
            return auth_url
        except Exception as e:
            st.error(f"Error generating authorization URL: {e}")
            return None
    
    def handle_oauth_callback(self, authorization_code):
        """Handle OAuth callback and exchange code for tokens."""
        try:
            if 'oauth_flow' not in st.session_state:
                st.error("OAuth flow not found. Please restart authentication.")
                return False
            
            flow = st.session_state['oauth_flow']
            flow.fetch_token(code=authorization_code)
            
            self.credentials = flow.credentials
            self.save_credentials()
            
            # Clean up session state
            del st.session_state['oauth_flow']
            
            return True
        except Exception as e:
            st.error(f"Error handling OAuth callback: {e}")
            return False
    
    def logout(self):
        """Logout user by removing stored credentials."""
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            self.credentials = None
            self.service = None
            
            # Clear session state
            if 'oauth_flow' in st.session_state:
                del st.session_state['oauth_flow']
            
            return True
        except Exception as e:
            st.error(f"Error during logout: {e}")
            return False
    
    def get_calendar_service(self):
        """Get authenticated Google Calendar service."""
        if not self.is_authenticated():
            return None
        
        try:
            if not self.service:
                self.service = build('calendar', 'v3', credentials=self.credentials)
            return self.service
        except Exception as e:
            st.error(f"Error creating calendar service: {e}")
            return None
    
    def get_user_info(self):
        """Get basic user information."""
        if not self.is_authenticated():
            return None
        
        try:
            service = self.get_calendar_service()
            if service:
                # Get primary calendar to extract user email
                calendar = service.calendars().get(calendarId='primary').execute()
                return {
                    'email': calendar.get('id', 'Unknown'),
                    'summary': calendar.get('summary', 'Primary Calendar')
                }
        except Exception as e:
            st.error(f"Error getting user info: {e}")
        
        return None
