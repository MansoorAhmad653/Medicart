# MediCart Deployment Guide - Railway.app

## Overview
This guide will deploy your MediCart Django application to Railway.app with a PostgreSQL database.

**Estimated Time:** 15-20 minutes  
**Cost:** ~$5/month (Railway's starter plan with database)

---

## Step 1: Prerequisites ✅

Ensure you have:
- ✅ GitHub account with MediCart code pushed
- ✅ Supabase PostgreSQL database set up (already configured)
- ✅ Railway.app account (free)

**Your GitHub Repo:**
```
https://github.com/MansoorAhmad653/MediaCart
```

**Your Supabase Credentials (from .env):**
```
DB_HOST = aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT = 6543
DB_NAME = postgres
DB_USER = postgres.ugtawlcsphxjbgarowjm
DB_PASSWORD = phmarcy.web.302
SUPABASE_URL = https://ugtawlcsphxjbgarowjm.supabase.co
SUPABASE_KEY = [your-JWT-key]
```

---

## Step 2: Connect GitHub to Railway ✅

### 2.1 Create Railway Account
1. Go to **[railway.app](https://railway.app)**
2. Click **"Start Free"**
3. Click **"GitHub"** to authenticate
4. Authorize Railway to access your GitHub

### 2.2 Create New Project
1. Click **"New Project"**
2. Click **"Deploy from GitHub repo"**
3. Select your GitHub repository: **MediaCart**
4. Click **"Deploy Now"**

Railway will automatically detect that this is a Python/Django project.

---

## Step 3: Configure Environment Variables 🔧

After clicking "Deploy Now", you'll be taken to the project dashboard.

### 3.1 Go to Variables Tab
1. Click **"Variables"** tab
2. Click **"Raw Editor"**
3. Paste all these environment variables (replace values with your actual data):

```
DEBUG=False
ALLOWED_HOSTS=your-railway-app.up.railway.app,localhost
SECRET_KEY=django-insecure-your-secret-key-change-this-for-production-12345
USE_SUPABASE=True

# Database Configuration (Supabase Pooler)
DB_ENGINE=django.db.backends.postgresql
DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.ugtawlcsphxjbgarowjm
DB_PASSWORD=phmarcy.web.302

# Supabase Configuration
SUPABASE_URL=https://ugtawlcsphxjbgarowjm.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-actual-key

# Gmail OAuth (if using)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 3.2 Find Your Railway App URL
The URL will look like: `https://medicart-production-xxxx.up.railway.app`

1. Go to **"Settings"** tab
2. Copy your **Domain**
3. Update `ALLOWED_HOSTS` with this domain

---

## Step 4: Update Django Settings 🔐

The settings.py already includes environment variable support. Verify these are present:

**Key settings for Railway:**

```python
# In medicart/settings.py

# Should read from environment
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Database uses Supabase pooler on port 6543
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', '6543'),
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}
```

✅ **Already configured correctly in your project!**

---

## Step 5: Deploy on Railway 🚀

### 5.1 Automatic Deployment
Railway automatically deploys when you:
- Push to GitHub (main branch)
- Click "Deploy" in the dashboard

### 5.2 Manual Deployment (if needed)
1. In your Railway project dashboard
2. Click **"Deploy"** button
3. Select **"Deploy Latest Commit"**

### 5.3 View Deployment Logs
1. Click **"Build Logs"** to see build progress
2. Click **"Logs"** to see runtime errors
3. Wait for ✅ **"Build Successful"** message

**Expected Build Output:**
```
-----> Building Python app
-----> Installing dependencies
-----> Running Django migrations
-----> Collecting static files
-----> Build completed successfully
```

---

## Step 6: Verify Deployment ✅

### 6.1 Check if App is Running
1. Visit your Railway domain: `https://medicart-production-xxxx.up.railway.app`
2. You should see the MediCart home page

### 6.2 Check Admin Panel
1. Go to `/admin` on your Railway domain
2. Login with your superuser: **admin_user / ghost.302**
3. Verify database is connected

### 6.3 Run Initial Setup (First Time Only)
If this is first deployment, Railway automatically runs these commands:
```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

---

## Step 7: Post-Deployment Tasks 📋

### 7.1 Update Google OAuth Redirect URI
If using Gmail login:

1. Go to **[Google Cloud Console](https://console.cloud.google.com)**
2. Select your project
3. Go to **OAuth 2.0 Client IDs**
4. Add your Railway domain as authorized:
   ```
   https://medicart-production-xxxx.up.railway.app/users/auth-callback/
   https://medicart-production-xxxx.up.railway.app/auth/callback
   ```

### 7.2 Update Supabase OAuth Redirect URI
1. Go to **Supabase Dashboard** → **Authentication** → **URL Configuration**
2. Add your Railway domain:
   ```
   https://medicart-production-xxxx.up.railway.app
   ```

### 7.3 Test All Features
- [ ] Login with email
- [ ] Login with Gmail OAuth
- [ ] Send OTP to email
- [ ] Send OTP to phone
- [ ] Add non-prescription medicine to cart
- [ ] Upload prescription
- [ ] Admin approves prescription
- [ ] Add prescription medicine to cart
- [ ] View admin dashboard

---

## Step 8: Create Superuser on Railway 🔑

If you need to create a new admin user:

### Using Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Connect to your project
railway link

# Create superuser
railway run python manage.py createsuperuser
```

### Using Django Shell
```bash
railway run python manage.py shell
```

---

## Troubleshooting 🔧

### Issue: "Deployment Failed"
**Solution:** Check build logs
1. Click **"Build Logs"** in Railway dashboard
2. Look for Python/Django error messages
3. Common issues:
   - Missing `requirements.txt` entries
   - Syntax errors in code
   - Database connection timeout

### Issue: "502 Bad Gateway"
**Solution:** Database connection issue
- Verify `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` are correct
- Make sure Supabase is running
- Check if port 6543 (pooler) is being used, not 5432

### Issue: Static Files Not Loading
**Solution:** Might need to clear Railway cache
1. In Railway, go to **"Settings"**
2. Click **"Clear Build Cache"**
3. Redeploy

### Issue: Media Files Not Persisting
**Solution:** Railway doesn't have persistent storage by default
- Consider using Supabase Storage or AWS S3 for media files
- Or update to Railway's paid plan with persistent volumes

---

## Monitoring & Logs 📊

### View Real-Time Logs
```bash
railway logs -f
```

### Check Deployment Status
```bash
railway status
```

### Redeploy Latest Code
```bash
railway deploy
```

---

## Environment Variables Reference 📝

| Variable | Example | Notes |
|----------|---------|-------|
| `DEBUG` | `False` | Always False in production |
| `ALLOWED_HOSTS` | `medicart.up.railway.app` | Your Railway domain |
| `SECRET_KEY` | `django-insecure-...` | Change to a strong random value |
| `DB_HOST` | `aws-1-ap-northeast-2.pooler.supabase.com` | Supabase pooler endpoint |
| `DB_PORT` | `6543` | Must be 6543 (pooler), not 5432 |
| `DB_NAME` | `postgres` | Supabase database name |
| `DB_USER` | `postgres.xxxxxx` | Your Supabase user |
| `DB_PASSWORD` | `your-password` | Your Supabase password |
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | Your Supabase project URL |
| `SUPABASE_KEY` | `eyJhbG...` | Your Supabase JWT public key |

---

## Cost Estimation 💰

| Service | Cost | Notes |
|---------|------|-------|
| Railway App | ~$5/month | Includes compute |
| Supabase Database | FREE | For free tier (~500MB) |
| **Total** | **~$5/month** | Very affordable! |

---

## Next Steps 🎯

1. ✅ Push this deployment config to GitHub
2. ✅ Deploy on Railway
3. ✅ Test all features thoroughly
4. ✅ Set up monitoring/alerts (optional)
5. ✅ Document your Railway project settings

---

## Quick Commands

```bash
# View logs
railway logs -f

# SSH into Railway environment
railway shell

# Run Django commands
railway run python manage.py createsuperuser

# Deploy
railway deploy

# Set environment variable
railway variables set KEY=value
```

---

## Support & Resources

- **Railway Docs:** https://docs.railway.app
- **Django Deployment:** https://docs.djangoproject.com/en/stable/howto/deployment/
- **PostgreSQL on Railway:** https://docs.railway.app/databases/postgresql
- **Environment Variables:** https://docs.railway.app/guides/environment-variables

---

**Last Updated:** May 28, 2026  
**Status:** Production Ready ✅
