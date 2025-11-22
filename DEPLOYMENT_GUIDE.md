# FJC Pizza - Render Deployment Guide

## Overview
This guide walks you through deploying the FJC Pizza application to Render.com with automatic GitHub integration and free PostgreSQL database.

## Prerequisites
- ✅ Render account (free)
- ✅ GitHub repository with code pushed
- ✅ All files in repository (including render.yaml)

## Deployment Options

### Option A: Using render.yaml (Recommended)
Render will automatically provision the web service and PostgreSQL database based on the `render.yaml` file.

### Option B: Manual Setup (Dashboard)
Manually create the web service and database through the Render dashboard.

---

## Option A: Automated Deployment (render.yaml)

### Step 1: Ensure render.yaml is pushed to GitHub
```bash
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 2: Create Render Account & Project
1. Go to https://render.com/
2. Sign in with GitHub account
3. Click "New +"
4. Select "Blueprint" (or "Web Service")
5. Connect your GitHub repository

### Step 3: Deploy from Blueprint
1. Click "Deploy from YAML"
2. Select the FJC-Pizza repository
3. Select `render.yaml`
4. Click "Create"
5. Render will automatically:
   - Create web service
   - Create PostgreSQL database
   - Run migrations
   - Deploy application

### Step 4: Configure Environment Variables
1. Go to Web Service Settings
2. Click "Environment"
3. Add missing variables:
   ```
   SECRET_KEY=<your-secret-key>
   ```

### Step 5: Wait for Deployment
- Initial build: 5-10 minutes
- Watch build logs in dashboard
- URL will be: `https://fjc-pizza-app.onrender.com`

---

## Option B: Manual Dashboard Setup

### Step 1: Create PostgreSQL Database
1. Dashboard → "New +" → "PostgreSQL"
2. Name: `fjc-pizza-db`
3. Region: Choose closest to you
4. PostgreSQL Version: 15
5. Plan: Free
6. Click "Create Database"
7. Copy the connection string (Internal Database URL)

### Step 2: Create Web Service
1. Dashboard → "New +" → "Web Service"
2. Connect GitHub repository
3. Name: `fjc-pizza-app`
4. Runtime: Python 3.11
5. Build Command:
   ```bash
   pip install -r requirements.txt
   python sales_inventory_system/manage.py migrate
   python sales_inventory_system/manage.py collectstatic --no-input
   ```
6. Start Command:
   ```bash
   gunicorn sales_inventory_system.sales_inventory.wsgi:application --bind 0.0.0.0:$PORT
   ```
7. Plan: Free
8. Click "Create Web Service"

### Step 3: Add Environment Variables
1. Go to Web Service Settings → Environment
2. Add these variables:
   ```
   DEBUG=False
   SECRET_KEY=<generate-secure-key>
   ALLOWED_HOSTS=<your-render-url>
   DATABASE_URL=<from-postgresql-internal-url>
   PYTHONUNBUFFERED=1
   ```

### Step 4: Deploy
1. Render will automatically deploy from GitHub main branch
2. Wait 5-10 minutes for build and deployment
3. Check build logs for any errors
4. Once successful, app will be live!

---

## Environment Variables Reference

| Variable | Value | Notes |
|----------|-------|-------|
| `DEBUG` | `False` | Never True in production |
| `SECRET_KEY` | Random string (50+ chars) | Generate: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'` |
| `ALLOWED_HOSTS` | `fjc-pizza-app.onrender.com` | Your Render URL |
| `DATABASE_URL` | From PostgreSQL service | Render provides automatically |
| `PYTHONUNBUFFERED` | `1` | Ensures real-time logs |

---

## Generating SECRET_KEY

Run this locally to generate a secure secret key:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and set it in Render environment variables.

---

## After Deployment

### Check Application
1. Visit: `https://<your-app-name>.onrender.com`
2. You should see the login page
3. Default admin credentials (if you created superuser):
   - Username: admin
   - Password: (from seed data or your setup)

### Create Admin User (if needed)
1. Use Render Shell to run:
   ```bash
   python sales_inventory_system/manage.py createsuperuser
   ```
2. Enter username, email, password when prompted
3. Access admin at: `/admin/`

### View Logs
1. Dashboard → Select Web Service
2. Click "Logs" tab
3. Watch real-time logs as you use the app

### Verify Database
1. Dashboard → Select PostgreSQL
2. Click "Connections"
3. Verify connection is active

---

## Automatic Redeployment

When you push code to GitHub main branch:
1. Render automatically detects the change
2. Triggers build process
3. Runs migrations
4. Deploys new version
5. Takes 3-5 minutes

To disable auto-deploy:
- Settings → Auto-Deploy: Toggle off

---

## Free Tier Limitations

### What You Get
- 750 hours/month compute time (free tier = ~all month)
- PostgreSQL database (250 MB)
- Free SSL/HTTPS certificate
- Automatic backups

### Limitations
- Auto-sleep after 15 minutes of inactivity
- Limited database size (250 MB)
- Shared CPU resources
- No scheduled jobs

### Solution: Upgrade
If you need always-on:
1. Dashboard → Plan
2. Choose "Starter" or higher
3. Pay per hour (~$10/month)

---

## Troubleshooting

### Build Fails
**Error:** `ModuleNotFoundError`
- Check `requirements.txt` includes all packages
- Verify Python version (3.11)
- Check for syntax errors in code

**Solution:**
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Database Connection Error
**Error:** `could not translate host name "db" to address`
- `DATABASE_URL` environment variable not set
- Incorrect connection string format

**Solution:**
1. Check PostgreSQL service is created
2. Copy internal database URL to `DATABASE_URL`
3. Restart web service

### Static Files Not Loading
**Error:** CSS/images not displaying
- `collectstatic` didn't run
- WhiteNoise not configured

**Solution:**
- Already configured in settings.py
- If still broken, run:
  ```bash
  python sales_inventory_system/manage.py collectstatic --no-input
  ```

### Application Crashes on Load
**Error:** 500 Internal Server Error
- Check logs: Dashboard → Logs tab
- Common causes:
  - Missing environment variables
  - Database not migrated
  - Syntax errors

**Solution:**
1. Read error logs carefully
2. Fix issue locally
3. Commit and push to GitHub
4. Render redeploys automatically

---

## Custom Domain (Optional)

To use your own domain:
1. Buy domain (GoDaddy, Namecheap, etc.)
2. Render → Settings → Custom Domain
3. Add your domain
4. Follow DNS setup instructions
5. SSL certificate auto-generated

---

## Monitoring & Maintenance

### Check Health
- Dashboard → Service → Health tab
- Should show "Live"

### View Metrics
- Dashboard → Service → Metrics tab
- Monitor CPU, memory, bandwidth

### Database Backup
- Dashboard → PostgreSQL → Backups
- Free tier: 7-day retention
- Automatic daily backups

---

## Deploy New Version

### Simple Process
1. Make code changes locally
2. Test thoroughly
3. Commit changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
4. Render automatically deploys (3-5 minutes)
5. Check logs to confirm success

---

## Performance Tips

### For Free Tier
1. Minimize database queries
2. Use pagination for large lists
3. Cache where possible
4. Optimize images/static files
5. Keep database small

### Monitor Usage
- Dashboard → Metrics
- Keep eye on CPU, memory, disk
- Upgrade if approaching limits

---

## Support & Help

### Render Documentation
- https://render.com/docs
- Deployment guides
- Troubleshooting

### Django Deployment
- https://docs.djangoproject.com/en/5.2/howto/deployment/

### Common Issues
- Check application logs first
- Read error messages carefully
- Search Render documentation
- Contact Render support (paid plans)

---

## Success Checklist

Before going live:
- [ ] Code pushed to GitHub
- [ ] render.yaml in repository
- [ ] SECRET_KEY set in environment
- [ ] DATABASE_URL configured
- [ ] ALLOWED_HOSTS set correctly
- [ ] Debug mode is False
- [ ] Static files collect properly
- [ ] Database migrations run
- [ ] Admin user created
- [ ] Login page loads correctly
- [ ] Dashboard displays data
- [ ] All features tested

---

## Next Steps

After successful deployment:
1. Verify all features work on live site
2. Test authentication/authorization
3. Monitor logs for errors
4. Configure domain (if needed)
5. Set up email (if needed)
6. Share URL with team
7. Monitor performance metrics
8. Plan for paid tier if needed (in future)

---

**Deployment Date:** ___________
**Live URL:** ___________
**Database:** ___________

Good luck! 🚀
