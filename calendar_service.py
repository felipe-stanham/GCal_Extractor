"""
Google Calendar service module for GCal Extractor.
Handles calendar discovery, selection, and configuration persistence.
"""

import json
import os
from typing import List, Dict, Optional
import streamlit as st
from google_auth import GoogleAuth

CONFIG_FILE = 'config.json'


class CalendarService:
    """Handles Google Calendar operations and configuration."""
    
    def __init__(self, auth: GoogleAuth):
        self.auth = auth
        self.selected_calendars = []
        self.load_config()
    
    def load_config(self):
        """Load calendar configuration from config file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.selected_calendars = config.get('selected_calendars', [])
                return True
            except Exception as e:
                st.error(f"Error loading configuration: {e}")
                return False
        return False
    
    def save_config(self):
        """Save calendar configuration to config file."""
        try:
            config = {
                'selected_calendars': self.selected_calendars
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving configuration: {e}")
            return False
    
    def get_available_calendars(self) -> Optional[List[Dict]]:
        """Get list of available calendars from Google Calendar."""
        service = self.auth.get_calendar_service()
        if not service:
            return None
        
        try:
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            # Format calendar data for easier handling
            formatted_calendars = []
            for calendar in calendars:
                formatted_calendars.append({
                    'id': calendar['id'],
                    'name': calendar.get('summary', 'Unnamed Calendar'),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'access_role': calendar.get('accessRole', 'reader')
                })
            
            return formatted_calendars
        except Exception as e:
            st.error(f"Error fetching calendars: {e}")
            return None
    
    def update_selected_calendars(self, calendar_ids: List[str], available_calendars: List[Dict]):
        """Update selected calendars and save configuration."""
        try:
            # Create mapping of calendar IDs to names
            calendar_map = {cal['id']: cal['name'] for cal in available_calendars}
            
            # Update selected calendars with both ID and name
            self.selected_calendars = [
                {
                    'id': cal_id,
                    'name': calendar_map.get(cal_id, 'Unknown Calendar')
                }
                for cal_id in calendar_ids
            ]
            
            # Save configuration
            return self.save_config()
        except Exception as e:
            st.error(f"Error updating selected calendars: {e}")
            return False
    
    def get_selected_calendars(self) -> List[Dict]:
        """Get currently selected calendars."""
        return self.selected_calendars
    
    def has_selected_calendars(self) -> bool:
        """Check if any calendars are selected."""
        return len(self.selected_calendars) > 0
    
    def clear_configuration(self):
        """Clear calendar configuration."""
        try:
            self.selected_calendars = []
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            return True
        except Exception as e:
            st.error(f"Error clearing configuration: {e}")
            return False
    
    def render_calendar_selection_ui(self):
        """Render calendar selection interface in Streamlit."""
        st.subheader("📅 Calendar Selection")
        
        # Get available calendars
        available_calendars = self.get_available_calendars()
        if not available_calendars:
            st.error("Unable to fetch calendars. Please check your connection and try again.")
            return False
        
        if not available_calendars:
            st.warning("No calendars found in your Google account.")
            return False
        
        # Create multiselect for calendar selection
        calendar_options = {cal['id']: f"{cal['name']}" for cal in available_calendars}
        
        # Get currently selected calendar IDs
        current_selection = [cal['id'] for cal in self.selected_calendars]
        
        st.write("Select the calendars you want to include in your reports:")
        
        selected_ids = st.multiselect(
            "Available Calendars",
            options=list(calendar_options.keys()),
            default=current_selection,
            format_func=lambda x: calendar_options[x],
            help="Choose one or more calendars to analyze for patient consultations"
        )
        
        # Update configuration if selection changed
        if selected_ids != current_selection:
            if self.update_selected_calendars(selected_ids, available_calendars):
                st.success("Calendar selection updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update calendar selection.")
        
        return len(selected_ids) > 0
    
    def render_selected_calendars_display(self):
        """Render read-only display of selected calendars."""
        if not self.has_selected_calendars():
            st.warning("No calendars selected. Please configure your calendar selection.")
            return
        
        st.subheader("📅 Selected Calendars")
        
        for calendar in self.selected_calendars:
            st.write(f"• **{calendar['name']}**")
        
        st.write(f"*Total: {len(self.selected_calendars)} calendar(s) selected*")
    
    def get_calendar_display_names(self) -> Dict[str, str]:
        """Get mapping of calendar IDs to display names."""
        return {cal['id']: cal['name'] for cal in self.selected_calendars}
