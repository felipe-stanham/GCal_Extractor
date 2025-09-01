"""
Google OAuth 2.0 authentication module for GCal Extractor.
Handles OAuth flow, token management, and automatic refresh.
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import streamlit as st

# OAuth 2.0 scopes for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# OAuth client configuration file
CREDENTIALS_FILE = 'credentials.json'

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
    
    def load_client_config(self):
        """Load OAuth client configuration from credentials file."""
        if not os.path.exists(CREDENTIALS_FILE):
            st.error(f"Credentials file '{CREDENTIALS_FILE}' not found. Please follow the setup guide.")
            return None
        
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                import json
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading credentials file: {e}")
            return None
    
    def authenticate_desktop(self):
        """Perform desktop OAuth authentication flow."""
        try:
            client_config = self.load_client_config()
            if not client_config:
                return False
            
            # Use InstalledAppFlow for desktop authentication
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            
            # Run local server for OAuth callback
            self.credentials = flow.run_local_server(port=0)
            
            # Save credentials
            if self.save_credentials():
                st.success("Authentication successful!")
                return True
            else:
                st.error("Failed to save credentials")
                return False
                
        except Exception as e:
            st.error(f"Error during authentication: {e}")
            import traceback
            st.error(f"Full error: {traceback.format_exc()}")
            return False
    
    def handle_oauth_callback(self, authorization_code):
        """Handle OAuth callback and exchange code for tokens."""
        try:
            if 'oauth_flow' not in st.session_state:
                st.error("OAuth flow not found. Please restart authentication.")
                return False
            
            flow = st.session_state['oauth_flow']
            
            # Debug information
            st.write(f"Debug - Authorization code received: {authorization_code[:20]}...")
            
            flow.fetch_token(code=authorization_code)
            
            self.credentials = flow.credentials
            
            # Debug: Check if credentials are valid
            st.write(f"Debug - Credentials valid: {self.credentials.valid}")
            st.write(f"Debug - Token exists: {bool(self.credentials.token)}")
            
            if self.save_credentials():
                st.success("Credentials saved successfully!")
            else:
                st.error("Failed to save credentials")
                return False
            
            # Clean up session state
            del st.session_state['oauth_flow']
            
            return True
        except Exception as e:
            st.error(f"Error handling OAuth callback: {e}")
            import traceback
            st.error(f"Full error: {traceback.format_exc()}")
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
