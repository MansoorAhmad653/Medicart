# MediCart Deployment Guide - Render.com

## Quick Start

This guide will help you deploy MediCart to Render.com in 10 minutes.

---

## Prerequisites

✅ GitHub account (code already pushed)
✅ Supabase account (database already configured)
✅ Render.com account (free tier available)

---

## Step 1: Push to GitHub ✓ (Already Done!)

Your project is already on GitHub:
```
https://github.com/MansoorAhmad653/MediaCart
```

---

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Sign Up"**
3. Connect with GitHub
4. Select your **MediaCart** repository

---

## Step 3: Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Select your **MediaCart** repository
3. Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `medicart` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput` |
| **Start Command** | `gunicorn medicart.wsgi` |
| **Plan** | `Free` (0.05 USD/hour) |

---

## Step 4: Add Environment Variables

Click **"Environment"** and add these variables:

```
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this
ALLOWED_HOSTS=medicart.onrender.com
USE_SUPABASE=True
DB_ENGINE=django.db.backends.postgresql
DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.ugtawlcsphxjbgarowjm
DB_PASSWORD=phmarcy.web.302
SUPABASE_URL=https://ugtawlcsphxjbgarowjm.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndGF3bGNzcGh4amJnYXJvd2ptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk3MDk5MzgsImV4cCI6MjA5NTI4NTkzOH0.j2oGUVWjeLGea7CBwlRHeWxxkUDM2XghIM4b6rSXQHs
```

**⚠️ Replace:**
- `SECRET_KEY` with a random string (keep it secret!)
- `ALLOWED_HOSTS` with your actual Render domain (shown after first deploy)

---

## Step 5: Deploy!

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Your app will be live at: `https://medicart.onrender.com`

---

## Troubleshooting

### Build fails?
- Check build logs in Render dashboard
- Ensure all environment variables are set
- Verify `requirements.txt` has `gunicorn`

### Database connection error?
- Verify `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` in env vars
- Check Supabase is accessible from Render's IP (usually allowed)

### Static files missing?
- Run: `python manage.py collectstatic --noinput` (already in build command)

### Can't log in?
- Verify Supabase auth is enabled
- Check Google OAuth redirect URI includes your Render domain

---

## After Deployment

### Update Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Find your OAuth 2.0 Client ID
3. Add authorized redirect URI:
   ```
   https://ugtawlcsphxjbgarowjm.supabase.co/auth/v1/callback
   ```

### Update ALLOWED_HOSTS

1. Deploy once to get your Render domain (e.g., `medicart.onrender.com`)
2. Go back to Render dashboard
3. Update `ALLOWED_HOSTS` env var to your actual domain:
   ```
   medicart.onrender.com,www.medicart.onrender.com
   ```
4. Redeploy

---

## Monitoring

- **Logs**: View in Render dashboard → Logs tab
- **Performance**: Free tier has 0.5 GB RAM, will sleep after 15 min inactivity
- **Restarts**: Manual redeploy or auto-deploy on GitHub push

---

## Useful Commands

### Force Redeploy
```
Click "Deploys" → "Redeploy Latest" in Render dashboard
```

### Check Database
```
Use Supabase dashboard to view/manage data
```

### View Logs
```
Render dashboard → "Logs" tab
```

---

## Next Steps

After successful deployment:
1. ✅ Test login with Gmail
2. ✅ Test shopping features
3. ✅ Verify database connectivity
4. ✅ Check static files load
5. ✅ Monitor performance in Render logs

---

## Support

- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com
- **Supabase Docs**: https://supabase.com/docs

Happy deploying! 🚀
