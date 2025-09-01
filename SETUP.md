# GCal Extractor Setup Guide

## Google OAuth 2.0 Setup

To use the GCal Extractor, you need to set up Google OAuth credentials. Follow these steps:

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select an existing project
3. Note your project ID

### 2. Enable Google Calendar API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add your email to test users
4. For Application type, select "Desktop application"
5. Click "Create"
6. Download the JSON file or copy the Client ID and Client Secret

### 4. Configure the Application

Create a file named `credentials.json` in the project root with your OAuth credentials:

```json
{
  "installed": {
    "client_id": "your_client_id_here.apps.googleusercontent.com",
    "client_secret": "your_client_secret_here",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

**Important**: Never commit `credentials.json` to version control. It's already in `.gitignore`.

### 5. Run the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

### 6. First Time Authentication

1. Click "Connect to Google Calendar"
2. A browser window will automatically open for Google authentication
3. Sign in and grant permissions
4. The browser will show a success message
5. Return to the Streamlit app - you should now be connected
6. Select your calendars and start generating reports

## Troubleshooting

### "Error 401: invalid_client"
- Check that your `credentials.json` file exists and has correct values
- Verify the redirect URI matches exactly: `http://localhost:8501`
- Ensure the Google Calendar API is enabled in your project

### "Access blocked: Authorization Error"
- Add your email to test users in the OAuth consent screen
- Make sure the app is in testing mode if using external user type

### "Redirect URI mismatch"
- Verify the redirect URI in your OAuth credentials matches `http://localhost:8501`
- Check that you're accessing the app via `localhost:8501` not `127.0.0.1:8501`

## Security Notes

- Keep your `credentials.json` file secure and never share it
- The `tokens.json` file will be created automatically after first authentication
- Both files are excluded from git via `.gitignore`
