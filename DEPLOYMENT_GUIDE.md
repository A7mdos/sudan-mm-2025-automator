# Deployment Guide - Streamlit Cloud (FREE)

This guide will help you deploy your Sudan-MM-2025 app to Streamlit Cloud so your teammates can access it via a web URL.

---

## Prerequisites

✅ App working locally with OAuth  
✅ GitHub account  
✅ Streamlit Cloud account (free at share.streamlit.io)

---

## Phase 1: Prepare Locally

### Step 1: Test Your App Locally

Make sure everything works:

```bash
streamlit run app.py
```

Complete OAuth authentication if you haven't already. This creates `token.pickle`.

### Step 2: Extract Token Data

Run this script to get your token data for Streamlit secrets:

```bash
python get_token_for_secrets.py
```

**Save the output** - you'll need it for Streamlit Cloud!

### Step 3: Get OAuth Credentials Content

Open `oauth_credentials.json` and **copy its entire contents**. You'll paste this into Streamlit secrets.

---

## Phase 2: Push to GitHub

### Step 1: Create .gitignore

Make sure these files are in `.gitignore`:

```
oauth_credentials.json
token.pickle
service_account_credentials.json
.streamlit/secrets.toml
__pycache__/
*.pyc
```

### Step 2: Create GitHub Repository

1. Go to GitHub.com
2. Click **New Repository**
3. Name it: `sudan-mm-2025-app`
4. Keep it **Private** (recommended)
5. Click **Create repository**

### Step 3: Push Your Code

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sudan-mm-2025-app.git
git push -u origin main
```

**Important:** Make sure you did NOT commit `oauth_credentials.json` or `token.pickle`!

---

## Phase 3: Deploy to Streamlit Cloud

### Step 1: Sign Up/Login

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Authorize Streamlit to access your repositories

### Step 2: Deploy the App

1. Click **New app**
2. Select:
   - **Repository:** `YOUR_USERNAME/sudan-mm-2025-app`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Click **Advanced settings...**

### Step 3: Configure Secrets

In the **Secrets** section, paste this structure with YOUR actual data:

```toml
# Config section
[config]
team_name = "Zamanna"
spreadsheet_name = "Sudan-MM-Submission-Zamanna"
parent_folder_name = "Sudan-MM-Submission-Zamanna"
parent_folder_id = ""
oauth_credentials_file = "oauth_credentials.json"

# OAuth credentials section
[oauth_credentials]
# Paste ENTIRE contents of oauth_credentials.json here
# It should look something like:
installed.client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
installed.client_secret = "YOUR_CLIENT_SECRET"
installed.project_id = "your-project-id"
installed.auth_uri = "https://accounts.google.com/o/oauth2/auth"
installed.token_uri = "https://oauth2.googleapis.com/token"
installed.redirect_uris = ["http://localhost"]

# Token section (from get_token_for_secrets.py output)
[token]
token = "YOUR_ACCESS_TOKEN"
refresh_token = "YOUR_REFRESH_TOKEN"
token_uri = "https://oauth2.googleapis.com/token"
client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
scopes = ["https://www.googleapis.com/auth/drive.file"]
```

### Step 4: Deploy!

1. Click **Deploy!**
2. Wait for the app to build (2-5 minutes)
3. Once deployed, you'll get a URL like: `https://your-app.streamlit.app`

---

## Phase 4: Share with Team

### Your App URL

Share this URL with your teammates:
```
https://YOUR_APP_NAME.streamlit.app
```

They can now:
- Open the URL in any browser
- Upload images/videos immediately
- All files go to YOUR Google Drive

### What Your Teammates See

- ✅ Clean web interface
- ✅ No installation needed
- ✅ No authentication required (they use your token)
- ✅ Simple upload form

---

## Maintenance

### When Token Expires (~7 days)

If you see "Token expired" error:

1. **Run locally:**
   ```bash
   python refresh_token.py
   ```

2. **Copy the new token data** from the output

3. **Update Streamlit secrets:**
   - Go to your app on share.streamlit.io
   - Click ⚙️ → **Settings** → **Secrets**
   - Replace the `[token]` section
   - Click **Save**

4. **Restart the app:**
   - Click **Reboot app** in the app menu

### Update App Code

When you make changes:

```bash
git add .
git commit -m "Your update message"
git push
```

Streamlit Cloud will automatically redeploy!

---

## Important Notes

### Storage Limits
- All uploads use **YOUR Google Drive storage**
- Free Google accounts: 15GB
- Need more? Upgrade to Google One (~$2/month for 100GB)

### Streamlit Cloud Limits (Free Tier)
- 1 private app
- 1GB RAM
- App sleeps after 7 days of inactivity (wakes up instantly when accessed)
- Unlimited views/users

### Security
- App runs under YOUR Google account
- Teammates upload files, but don't have direct access to your Google account
- Keep your `oauth_credentials.json` and token data secure
- Never commit secrets to GitHub

---

## Troubleshooting

### "Token expired" Error
→ Run `python refresh_token.py` and update secrets

### "No module named 'X'" Error
→ Make sure `requirements.txt` is in your repo

### App Won't Start
→ Check Streamlit Cloud logs (click "Manage app" → "Logs")

### Files Not Uploading
→ Check your Google Drive storage quota

### "Secrets not found" Error
→ Make sure secrets are properly formatted in Streamlit Cloud settings

---

## Cost Summary

| Item | Cost |
|------|------|
| Streamlit Cloud (free tier) | FREE ✅ |
| Google Drive storage (15GB) | FREE ✅ |
| OAuth credentials | FREE ✅ |
| **Total** | **$0/month** 🎉 |

Optional upgrades:
- More storage: Google One (~$2/month for 100GB)
- Private repo: GitHub Pro (~$4/month) - optional

---

## Support

If you run into issues:
1. Check the logs in Streamlit Cloud
2. Review the troubleshooting section
3. Make sure secrets are correctly formatted
4. Verify token hasn't expired

---

**You're all set!** Your app is now live and your teammates can start uploading! 🚀
