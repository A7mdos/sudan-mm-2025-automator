"""
Helper script to extract token data for Streamlit Cloud secrets.
Run this after authenticating locally to get the token data.
"""

import pickle
import json

def get_token_data():
    """Extract token data from token.pickle file."""
    try:
        with open('token.pickle', 'rb') as token_file:
            creds = pickle.load(token_file)
        
        # Check for required scopes
        required_scopes = {
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/spreadsheets'
        }
        token_scopes = set(creds.scopes) if creds.scopes else set()
        
        if not required_scopes.issubset(token_scopes):
            missing = required_scopes - token_scopes
            print("⚠️  WARNING: Token is missing required scopes!")
            print(f"   Missing: {missing}")
            print(f"   Current: {token_scopes}")
            print("\nYou need to re-authenticate:")
            print("  1. Delete token.pickle")
            print("  2. Run: streamlit run app.py")
            print("  3. Run this script again")
            print()
        
        if not creds.refresh_token:
            print("⚠️  WARNING: Token has no refresh_token!")
            print("The deployed app will fail when the access token expires (~1 hour).")
            print("\nYou need to re-authenticate:")
            print("  1. Delete token.pickle")
            print("  2. Run: streamlit run app.py")
            print("  3. Run this script again")
            return None
        
        # Convert credentials to dict format for Streamlit secrets
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes)
        }
        
        print("=" * 60)
        print("COPY THIS TOKEN DATA TO STREAMLIT CLOUD SECRETS")
        print("=" * 60)
        print("\nPaste this into the [token] section of your secrets:\n")
        print('[token]')
        print(f'token = "{token_data["token"]}"')
        print(f'refresh_token = "{token_data["refresh_token"]}"')
        print(f'token_uri = "{token_data["token_uri"]}"')
        print(f'client_id = "{token_data["client_id"]}"')
        print(f'client_secret = "{token_data["client_secret"]}"')
        print(f'scopes = {json.dumps(token_data["scopes"])}')
        print("\n" + "=" * 60)
        
        return token_data
        
    except FileNotFoundError:
        print("ERROR: token.pickle not found!")
        print("\nPlease run the app locally first to generate the token:")
        print("  streamlit run app.py")
        print("\nThen run this script again.")
        return None
    except Exception as e:
        print(f"ERROR: Failed to read token: {str(e)}")
        return None

if __name__ == "__main__":
    print("Token Extraction Tool for Streamlit Cloud Deployment")
    print("=" * 60)
    get_token_data()
