# GCal Extractor - Solution Discussion

## Project Analysis

**Problem**: Psychology professional needs efficient patient consultation frequency analysis from Google Calendar events.

**Appetite**: 1 week ViebCoding

**Core Requirements**:
- Streamlit web app
- Google Calendar OAuth integration
- Excel report generation with dual sheets (totales/detalle)
- Patient name processing with "Padres de [Name]" handling
- Month/year filtering

## Proposed Architecture

### Technical Stack
- **Frontend**: Streamlit (simple, fast deployment)
- **Auth**: google-auth-oauthlib + google-api-python-client
- **Data Processing**: pandas
- **Output**: openpyxl for Excel generation
- **Storage**: Local JSON files (config.json, tokens.json)

### File Structure
```
├── streamlit_app.py          # Main UI
├── google_auth.py            # OAuth handling
├── calendar_service.py       # Google Calendar API
├── excel_generator.py        # Report generation
├── requirements.txt          # Dependencies
├── config.json              # Calendar selection (generated)
├── tokens.json              # OAuth tokens (generated)
└── reports/                 # Generated Excel files
```

## Proposed Scopes

### Scope 1: Authentication & Setup
- Google OAuth implementation
- Token management and refresh
- Calendar discovery and selection
- Configuration persistence

### Scope 2: Data Processing Core
- Calendar event fetching with date filtering
- Patient name processing and normalization
- "Padres de [Name]" logic implementation
- Data aggregation for reports

### Scope 3: Report Generation
- Excel file creation with dual sheets
- "totales" sheet with calendar/patient/count
- "detalle" sheet with patient columns and dates
- Date formatting (dd/mm/yyyy)

### Scope 4: Streamlit UI
- Authentication flow interface
- Main dashboard with calendar display
- Month/year selection
- Report generation and download
- Error handling and user feedback

## Key Implementation Considerations

### Patient Name Processing
- Normalize: capitalize, trim spaces
- "Padres de [Name]" → count for [Name] but show separately in detalle
- No fuzzy matching (exact string processing)

### Excel Output Format
**Sheet 1 "totales"**: calendario | nombre | total
**Sheet 2 "detalle"**: Patient columns grouped by calendar with dates

### Error Handling
- Network connectivity issues
- API rate limits
- Token expiration
- Invalid date ranges
- No events found

## Agreed Decisions
1. **Caching**: No caching - direct API calls for fresh data
2. **Performance**: No limits for now, handle large calendars as needed
3. **Excel Styling**: Basic formatting only
4. **Report Naming**: Yes, include timestamps (e.g., `report_2024_01_20250109_143022.xlsx`)
