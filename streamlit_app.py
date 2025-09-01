"""
GCal Extractor - Main Streamlit Application
Psychology consultation frequency analyzer for Google Calendar events.
"""

import streamlit as st
from google_auth import GoogleAuth
from calendar_service import CalendarService
from data_processor import DataProcessor
from excel_generator import ExcelGenerator

# Page configuration
st.set_page_config(
    page_title="GCal Extractor",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize session state variables."""
    if 'auth' not in st.session_state:
        st.session_state.auth = GoogleAuth()
    if 'calendar_service' not in st.session_state:
        st.session_state.calendar_service = CalendarService(st.session_state.auth)
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    if 'excel_generator' not in st.session_state:
        st.session_state.excel_generator = ExcelGenerator()

def render_header():
    """Render application header."""
    st.title("📅 GCal Extractor")
    st.markdown("*Psychology consultation frequency analyzer*")
    st.divider()

def render_authentication_section():
    """Render authentication status and controls."""
    auth = st.session_state.auth
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if auth.is_authenticated():
            user_info = auth.get_user_info()
            if user_info:
                st.success(f"✅ Connected to Google Calendar: {user_info['email']}")
            else:
                st.success("✅ Connected to Google Calendar")
        else:
            st.error("❌ Not connected to Google Calendar")
    
    with col2:
        if auth.is_authenticated():
            if st.button("🚪 Logout", type="secondary"):
                if auth.logout():
                    st.session_state.calendar_service.clear_configuration()
                    st.success("Logged out successfully!")
                    st.rerun()
                else:
                    st.error("Error during logout")

def render_oauth_flow():
    """Render OAuth authentication flow."""
    st.subheader("🔐 Google Calendar Authentication")
    
    st.markdown("""
    To generate consultation reports, you need to connect to your Google Calendar account.
    
    **What we'll access:**
    - Read-only access to your calendar events
    - Calendar names and basic information
    
    **What we won't access:**
    - Your personal information beyond calendar data
    - Ability to modify or delete calendar events
    """)
    
    auth = st.session_state.auth
    
    # Show connect button for desktop OAuth flow
    if st.button("🔗 Connect to Google Calendar", type="primary", use_container_width=True):
        with st.spinner("Opening browser for authentication..."):
            st.info("A browser window will open for Google authentication. Please complete the authorization process.")
            if auth.authenticate_desktop():
                st.experimental_rerun()
            else:
                st.error("Authentication failed. Please try again.")

def render_calendar_setup():
    """Render calendar selection and configuration."""
    calendar_service = st.session_state.calendar_service
    
    # Show current selection if any
    if calendar_service.has_selected_calendars():
        calendar_service.render_selected_calendars_display()
        
        # Option to reconfigure
        with st.expander("🔧 Reconfigure Calendar Selection"):
            calendar_service.render_calendar_selection_ui()
    else:
        st.info("Please select the calendars you want to analyze.")
        calendar_service.render_calendar_selection_ui()

def render_main_interface():
    """Render main application interface when authenticated."""
    calendar_service = st.session_state.calendar_service
    data_processor = st.session_state.data_processor
    excel_generator = st.session_state.excel_generator
    
    # Calendar configuration section
    render_calendar_setup()
    
    st.divider()
    
    # Report generation section
    st.subheader("📊 Generate Report")
    
    if not calendar_service.has_selected_calendars():
        st.warning("Please select at least one calendar to generate reports.")
        return
    
    # Month/Year selection
    col1, col2 = st.columns(2)
    
    with col1:
        month = st.selectbox(
            "Month",
            options=list(range(1, 13)),
            format_func=lambda x: [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ][x-1],
            index=0
        )
    
    with col2:
        year = st.selectbox(
            "Year",
            options=list(range(2020, 2026)),
            index=4  # Default to 2024
        )
    
    # Generate button
    if st.button("📈 Generate Report", type="primary", use_container_width=True):
        with st.spinner("Fetching calendar events..."):
            # Fetch events
            events = calendar_service.fetch_events(year, month)
            
            if not events:
                st.error("No events found for the selected period or error fetching events.")
                return
            
            if len(events) == 0:
                st.warning(f"No consultation events found for {month:02d}/{year}.")
                return
            
            st.success(f"Found {len(events)} events. Processing data...")
        
        with st.spinner("Processing patient data..."):
            # Process events into structured data
            processed_data = data_processor.process_events(events)
            
            if not processed_data:
                st.warning("No valid patient consultations found in the events.")
                return
            
            # Generate report data
            totales_data = data_processor.generate_totales_data(processed_data)
            detalle_data = data_processor.generate_detalle_data(processed_data)
            
            st.success("Data processed successfully!")
        
        with st.spinner("Generating Excel report..."):
            # Generate Excel file
            filepath = excel_generator.generate_excel_report(
                totales_data, detalle_data, year, month
            )
            
            if filepath:
                st.success("Excel report generated successfully!")
                
                # Show report summary
                summary = excel_generator.get_report_summary(totales_data, detalle_data)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Patients", summary['total_patients'])
                with col2:
                    st.metric("Total Sessions", summary['total_sessions'])
                with col3:
                    st.metric("Calendars", summary['calendars_count'])
                
                # Calendar breakdown
                st.subheader("📋 Report Summary")
                for calendar_name, stats in summary['calendar_stats'].items():
                    st.write(f"**{calendar_name}**: {stats['patients']} patients, {stats['sessions']} sessions")
                
                # Download button
                with open(filepath, 'rb') as file:
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=file.read(),
                        file_name=filepath.split('/')[-1],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                
                st.info(f"Report saved as: `{filepath}`")
            else:
                st.error("Failed to generate Excel report.")

def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    
    # Authentication status
    render_authentication_section()
    
    st.divider()
    
    # Main content based on authentication status
    if st.session_state.auth.is_authenticated():
        render_main_interface()
    else:
        render_oauth_flow()
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        **GCal Extractor** helps psychology professionals analyze patient consultation frequency from Google Calendar events.
        
        **Features:**
        - 🔐 Secure Google OAuth authentication
        - 📅 Multi-calendar support
        - 📊 Excel report generation
        - 👥 Patient name processing
        - 📈 Consultation frequency analysis
        """)
        
        st.header("🛠️ Status")
        auth = st.session_state.auth
        calendar_service = st.session_state.calendar_service
        
        st.write("**Authentication:**", "✅ Connected" if auth.is_authenticated() else "❌ Not connected")
        st.write("**Calendars:**", f"{len(calendar_service.get_selected_calendars())} selected")
        
        if auth.is_authenticated() and calendar_service.has_selected_calendars():
            st.success("Ready to generate reports!")
        else:
            st.warning("Setup required")

if __name__ == "__main__":
    main()
