# Quick Deployment Checklist

## ✅ Pre-Deployment (Do These First)

- [ ] App works locally with OAuth (`streamlit run app.py`)
- [ ] Authenticated successfully (browser opened, clicked Allow)
- [ ] `token.pickle` file exists in your project folder
- [ ] Tested uploading a file - it appears in your Google Drive
- [ ] Installed ffmpeg on your system (for video validation)

## ✅ Extract Token Data

Run this command:
```bash
python get_token_for_secrets.py
```

**Save the output** - you'll paste it into Streamlit Cloud secrets!

## ✅ Prepare for GitHub

1. **Create `.gitignore`** (already provided)
2. **Verify these files are in `.gitignore`:**
   - `oauth_credentials.json`
   - `token.pickle`
   - `service_account_credentials.json`

3. **Check `.gitignore` is working:**
   ```bash
   git status
   ```
   You should NOT see the above files listed!

## ✅ Push to GitHub

```bash
git init
git add .
git commit -m "Initial deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sudan-mm-2025-app.git
git push -u origin main
```

## ✅ Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your repository
4. Click **Advanced settings**
5. Paste your secrets (see DEPLOYMENT_GUIDE.md for format)
6. Click **Deploy!**

## ✅ Get Your URL

After deployment (~5 minutes):
- URL will be: `https://YOUR_APP_NAME.streamlit.app`
- Share this with your teammates!

## ✅ Test Deployed App

1. Open the URL
2. Try uploading an image
3. Check your Google Drive - file should be there!
4. Check your Google Sheet - metadata should be logged!

## 🔄 When Token Expires (~7 days)

```bash
python refresh_token.py
```

Then update the `[token]` section in Streamlit Cloud secrets.

---

## 📁 Files Overview

### Core App Files (deploy these)
- `app.py` - Main application
- `drive_api.py` - Google Drive integration
- `sheets_api.py` - Google Sheets integration  
- `media_validator.py` - File validation
- `config.json` - Configuration
- `requirements.txt` - Dependencies
- `.gitignore` - Protect secrets

### Helper Scripts (keep local, don't deploy)
- `get_token_for_secrets.py` - Extract token for deployment
- `refresh_token.py` - Refresh expired token

### Documentation
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `secrets.toml.example` - Template for Streamlit secrets

### DO NOT DEPLOY (keep local only)
- `oauth_credentials.json` - OAuth credentials (goes in Streamlit secrets)
- `token.pickle` - Token file (extract data for Streamlit secrets)
- `service_account_credentials.json` - Old file (not needed anymore)

---

## 🎉 Success Indicators

You'll know it's working when:
- ✅ App loads at your Streamlit Cloud URL
- ✅ No errors in the interface
- ✅ You can upload a file
- ✅ File appears in your Google Drive
- ✅ Metadata appears in your Google Sheet
- ✅ Teammates can access the same URL and upload

---

## 🆘 Quick Troubleshooting

**Error: "Token expired"**
→ Run `python refresh_token.py` and update secrets

**Error: "Secrets not found"**
→ Check secrets formatting in Streamlit Cloud

**Error: "Module not found"**
→ Make sure `requirements.txt` is in your repo

**Files not in Drive**
→ Check your Google Drive storage quota

**App won't start**
→ Check logs in Streamlit Cloud (⚙️ → Logs)

---

**Ready to deploy? Follow the DEPLOYMENT_GUIDE.md for step-by-step instructions!**
