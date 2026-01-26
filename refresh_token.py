"""
Token Refresh Script
Run this script when your deployed app shows "Token expired" error.
It will refresh your token and show you the new data to paste into Streamlit secrets.
"""

import pickle
import json
from google.auth.transport.requests import Request

def refresh_token():
    """Refresh the OAuth token and display new credentials."""
    try:
        # Load existing token
        with open('token.pickle', 'rb') as token_file:
            creds = pickle.load(token_file)
        
        print("Current token status:")
        print(f"  Valid: {creds.valid}")
        print(f"  Expired: {creds.expired}")
        
        if creds and creds.expired and creds.refresh_token:
            print("\nRefreshing token...")
            creds.refresh(Request())
            
            # Save refreshed token
            with open('token.pickle', 'wb') as token_file:
                pickle.dump(creds, token_file)
            
            print("✅ Token refreshed successfully!")
            
            # Display new token data
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': list(creds.scopes)
            }
            
            print("\n" + "=" * 60)
            print("NEW TOKEN DATA FOR STREAMLIT CLOUD")
            print("=" * 60)
            print("\nUpdate the [token] section in Streamlit Cloud secrets with:")
            print("\n[token]")
            print(f'token = "{token_data["token"]}"')
            print(f'refresh_token = "{token_data["refresh_token"]}"')
            print(f'token_uri = "{token_data["token_uri"]}"')
            print(f'client_id = "{token_data["client_id"]}"')
            print(f'client_secret = "{token_data["client_secret"]}"')
            print(f'scopes = {json.dumps(token_data["scopes"])}')
            print("\n" + "=" * 60)
            print("\nSteps to update Streamlit Cloud:")
            print("1. Go to your app on share.streamlit.io")
            print("2. Click the ⚙️ menu → Settings → Secrets")
            print("3. Replace the [token] section with the above data")
            print("4. Click 'Save'")
            print("5. Restart your app")
            
        else:
            print("❌ Token cannot be refreshed (no refresh token available)")
            print("\nYou need to re-authenticate:")
            print("  1. Delete token.pickle")
            print("  2. Run: streamlit run app.py")
            print("  3. Complete OAuth authentication")
            print("  4. Run: python get_token_for_secrets.py")
            print("  5. Update secrets in Streamlit Cloud")
        
    except FileNotFoundError:
        print("❌ ERROR: token.pickle not found!")
        print("\nPlease run the app locally first:")
        print("  streamlit run app.py")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\nYou may need to re-authenticate:")
        print("  1. Delete token.pickle")
        print("  2. Run: streamlit run app.py")

if __name__ == "__main__":
    print("=" * 60)
    print("OAUTH TOKEN REFRESH TOOL")
    print("=" * 60)
    print()
    refresh_token()
