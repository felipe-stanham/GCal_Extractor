"""
Data processing module for GCal Extractor.
Handles patient name normalization, event processing, and data aggregation.
"""

from typing import List, Dict, Tuple
import re
from datetime import datetime
import streamlit as st


class DataProcessor:
    """Handles processing of calendar events into patient consultation data."""
    
    def __init__(self):
        pass
    
    def normalize_patient_name(self, name: str) -> str:
        """Normalize patient name by capitalizing and trimming spaces."""
        if not name:
            return ""
        
        # Remove leading/trailing spaces and capitalize
        normalized = name.strip().title()
        
        # Handle multiple spaces between words
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def extract_patient_name(self, event_title: str) -> Tuple[str, bool]:
        """
        Extract patient name from event title.
        Returns (patient_name, is_parent_session).
        
        Handles "Padres de [Name]" logic:
        - "Padres de Sofia M" returns ("Sofia M", True)
        - "Juan Perez" returns ("Juan Perez", False)
        """
        if not event_title:
            return "", False
        
        # Check for "Padres de [Name]" pattern
        padres_pattern = r'^Padres\s+de\s+(.+)$'
        match = re.match(padres_pattern, event_title, re.IGNORECASE)
        
        if match:
            # Extract the patient name from "Padres de [Name]"
            patient_name = match.group(1)
            return self.normalize_patient_name(patient_name), True
        else:
            # Regular patient session
            return self.normalize_patient_name(event_title), False
    
    def process_events(self, events: List[Dict]) -> Dict[str, Dict]:
        """
        Process calendar events into structured patient data.
        
        Returns:
        {
            'calendar_id': {
                'calendar_name': 'Calendar Name',
                'patients': {
                    'Patient Name': {
                        'total_sessions': int,
                        'sessions': [
                            {
                                'date': 'dd/mm/yyyy',
                                'title': 'Event Title',
                                'is_parent_session': bool
                            }
                        ]
                    }
                }
            }
        }
        """
        processed_data = {}
        
        for event in events:
            # Skip events without titles
            if 'summary' not in event:
                continue
            
            event_title = event['summary']
            calendar_id = event['calendar_id']
            calendar_name = event['calendar_name']
            
            # Extract start date
            start = event.get('start', {})
            if 'dateTime' in start:
                # Full datetime event
                event_date = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            elif 'date' in start:
                # All-day event
                event_date = datetime.strptime(start['date'], '%Y-%m-%d')
            else:
                continue  # Skip events without valid dates
            
            # Format date as dd/mm/yyyy
            formatted_date = event_date.strftime('%d/%m/%Y')
            
            # Extract patient name and check if it's a parent session
            patient_name, is_parent_session = self.extract_patient_name(event_title)
            
            if not patient_name:
                continue  # Skip events without valid patient names
            
            # Initialize calendar data if not exists
            if calendar_id not in processed_data:
                processed_data[calendar_id] = {
                    'calendar_name': calendar_name,
                    'patients': {}
                }
            
            # Initialize patient data if not exists
            if patient_name not in processed_data[calendar_id]['patients']:
                processed_data[calendar_id]['patients'][patient_name] = {
                    'total_sessions': 0,
                    'sessions': []
                }
            
            # Add session data
            session_data = {
                'date': formatted_date,
                'title': event_title,
                'is_parent_session': is_parent_session
            }
            
            processed_data[calendar_id]['patients'][patient_name]['sessions'].append(session_data)
            processed_data[calendar_id]['patients'][patient_name]['total_sessions'] += 1
        
        return processed_data
    
    def generate_totales_data(self, processed_data: Dict) -> List[Dict]:
        """
        Generate data for 'totales' sheet.
        
        Returns list of dictionaries with:
        - calendario: calendar name
        - nombre: patient name
        - total: total consultation count
        """
        totales_data = []
        
        for calendar_id, calendar_data in processed_data.items():
            calendar_name = calendar_data['calendar_name']
            
            for patient_name, patient_data in calendar_data['patients'].items():
                totales_data.append({
                    'calendario': calendar_name,
                    'nombre': patient_name,
                    'total': patient_data['total_sessions']
                })
        
        # Sort by calendar name, then by patient name
        totales_data.sort(key=lambda x: (x['calendario'], x['nombre']))
        
        return totales_data
    
    def generate_detalle_data(self, processed_data: Dict) -> Dict[str, List[Dict]]:
        """
        Generate data for 'detalle' sheet organized by calendar.
        
        Returns:
        {
            'calendar_name': [
                {
                    'patient_name': 'Patient Name',
                    'dates': ['dd/mm/yyyy', 'dd/mm/yyyy', ...]
                },
                {
                    'patient_name': 'Padres de Patient Name',
                    'dates': ['dd/mm/yyyy', 'dd/mm/yyyy', ...]
                }
            ]
        }
        """
        detalle_data = {}
        
        for calendar_id, calendar_data in processed_data.items():
            calendar_name = calendar_data['calendar_name']
            detalle_data[calendar_name] = []
            
            for patient_name, patient_data in calendar_data['patients'].items():
                # Separate regular sessions from parent sessions
                regular_sessions = []
                parent_sessions = []
                
                for session in patient_data['sessions']:
                    if session['is_parent_session']:
                        parent_sessions.append(session['date'])
                    else:
                        regular_sessions.append(session['date'])
                
                # Add regular sessions if any
                if regular_sessions:
                    regular_sessions.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
                    detalle_data[calendar_name].append({
                        'patient_name': patient_name,
                        'dates': regular_sessions
                    })
                
                # Add parent sessions if any (show as "Padres de [Name]")
                if parent_sessions:
                    parent_sessions.sort(key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
                    detalle_data[calendar_name].append({
                        'patient_name': f'Padres de {patient_name}',
                        'dates': parent_sessions
                    })
            
            # Sort patients by name within each calendar
            detalle_data[calendar_name].sort(key=lambda x: x['patient_name'])
        
        return detalle_data
