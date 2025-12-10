# Ryanair Flight Bot Deployment

## 🚀 Deploy to Railway (Free - Recommended)

### Step 1: Create GitHub Repository

```bash
cd /home/none/ryanair
git init
git add .
git commit -m "Initial commit - Ryanair flight bot"
```

Then create a repo on GitHub and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/ryanair-bot.git
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account
5. Select your `ryanair-bot` repository
6. Railway will auto-detect the Python project

### Step 3: Add Environment Variables

In Railway dashboard:
1. Click on your project
2. Go to **Variables** tab
3. Add your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

### Step 4: Done! 🎉

Your bot will start automatically and run 24/7!

---

## 🔄 Alternative: Render.com

1. Go to [render.com](https://render.com)
2. Create account → New → **Background Worker**
3. Connect GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python telegram_bot.py`
5. Add environment variable: `TELEGRAM_BOT_TOKEN`

---

## 📁 Files Created for Deployment

- `Procfile` - Tells hosting service how to run the bot
- `runtime.txt` - Specifies Python version
- `requirements.txt` - Python dependencies

---

## ⚠️ Important Notes

- **Railway Free Tier:** 500 hours/month (~21 days). Upgrade if needed ($5/month)
- **Render Free Tier:** Spins down after 15min inactivity, wakes on webhook
- Keep your `.env` file LOCAL - never push it to GitHub!

---

## 🔒 Create .gitignore

Make sure sensitive files aren't pushed:

```
.env
venv/
__pycache__/
*.pyc
```
