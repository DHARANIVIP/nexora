---
description: Deploy Deep-detection to Render (Step-by-Step)
---

# 🚀 Render Deployment Guide

This workflow guides you through deploying the Deep-detection application to Render.

## Prerequisites

- GitHub account with your code pushed to a repository
- Render account (sign up at https://render.com - free tier available)
- MongoDB Atlas account (optional, for database features)

---

## Step 1: Prepare Your Repository

1. **Ensure all changes are committed and pushed to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Verify these files exist in your repository:**
   - ✅ `render.yaml` (deployment configuration)
   - ✅ `build.sh` (build script)
   - ✅ `backend/requirements.txt` (Python dependencies)
   - ✅ `package.json` (Node.js dependencies)

---

## Step 2: Create Render Account

1. Go to https://render.com
2. Click **"Get Started"** or **"Sign Up"**
3. Sign up with your GitHub account (recommended for easier integration)
4. Authorize Render to access your GitHub repositories

---

## Step 3: Create New Web Service

1. From Render Dashboard, click **"New +"** button
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - If not connected, click **"Connect GitHub"**
   - Find and select your `Deep-detection` repository
   - Click **"Connect"**

---

## Step 4: Configure Web Service

Render will auto-detect your `render.yaml` file. Configure the following:

### Basic Settings:
- **Name:** `deepfake-detection` (or your preferred name)
- **Region:** Choose closest to your users (e.g., Oregon, Frankfurt)
- **Branch:** `main` (or your default branch)
- **Runtime:** Python 3.10.0 (auto-detected from render.yaml)

### Build & Deploy:
- **Build Command:** `./build.sh` ✅ (auto-filled from render.yaml)
- **Start Command:** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1` ✅ (auto-filled)

### Instance Type:
- **Plan:** Free ✅ (sufficient for testing and small projects)

---

## Step 5: Configure Environment Variables

Click on **"Environment"** tab and add these variables:

### Required Variables:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.10.0` | Auto-filled from render.yaml |
| `NODE_VERSION` | `20.11.0` | Auto-filled from render.yaml |
| `ENVIRONMENT` | `production` | Auto-filled from render.yaml |
| `LOG_LEVEL` | `INFO` | Auto-filled from render.yaml |

### Optional (if using MongoDB):

| Key | Value | Notes |
|-----|-------|-------|
| `MONGODB_URI` | `mongodb+srv://user:pass@cluster.mongodb.net/dbname` | Get from MongoDB Atlas |

**To get MongoDB URI:**
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster (M0 tier)
3. Create database user
4. Whitelist IP: `0.0.0.0/0` (allow from anywhere)
5. Click "Connect" → "Connect your application"
6. Copy connection string and replace `<password>` with your password

---

## Step 6: Configure Persistent Storage

The `render.yaml` already configures a 1GB disk for uploaded files:

- **Disk Name:** `deepfake-storage`
- **Mount Path:** `/opt/render/project/src/storage`
- **Size:** 1 GB (free tier limit)

This ensures uploaded videos/images persist across deployments.

---

## Step 7: Deploy!

1. Review all settings
2. Click **"Create Web Service"** button
3. Render will start building your application

### Build Process (5-10 minutes):
- ⏳ Installing system dependencies (OpenCV libraries)
- ⏳ Installing Node.js dependencies
- ⏳ Building React frontend
- ⏳ Installing Python dependencies
- ⏳ Creating storage directories

**Watch the build logs** for any errors. The build script provides detailed progress indicators.

---

## Step 8: Verify Deployment

Once deployment completes:

1. **Get your app URL:** `https://deepfake-detection-xxxx.onrender.com`
2. **Test the health check:** Visit `https://your-app.onrender.com/api/scans`
   - Should return `[]` (empty array) or existing scans
3. **Test the frontend:** Visit `https://your-app.onrender.com`
   - Should load the React application
4. **Test file upload:**
   - Upload a test image or video
   - Verify analysis runs successfully

---

## Step 9: Configure Auto-Deploy (Optional)

Auto-deploy is already enabled in `render.yaml`:

```yaml
autoDeploy: true
```

This means:
- ✅ Every push to `main` branch triggers automatic deployment
- ✅ No manual intervention needed
- ✅ Build logs available in Render dashboard

**To disable auto-deploy:**
- Go to Settings → Build & Deploy
- Uncheck "Auto-Deploy"

---

## Step 10: Monitor Your Application

### View Logs:
1. Go to Render Dashboard
2. Click on your service
3. Click **"Logs"** tab
4. View real-time application logs

### Check Metrics:
- **CPU Usage**
- **Memory Usage**
- **Request Count**
- **Response Times**

### Health Checks:
Render automatically monitors `/api/scans` endpoint every 30 seconds.

---

## Troubleshooting

### Build Fails - System Dependencies
**Error:** `libgl1 not found` or similar

**Solution:** The build script already installs OpenCV dependencies. If issues persist:
1. Check build logs for specific missing package
2. Add to `build.sh` under system dependencies section

### Build Fails - Out of Memory
**Error:** `JavaScript heap out of memory`

**Solution:** Already optimized in `vite.config.ts` with chunk splitting. If still failing:
- Upgrade to paid plan with more memory
- Or reduce bundle size by removing unused dependencies

### App Spins Down (Free Tier)
**Behavior:** First request after 15 minutes takes 30-60 seconds

**Solutions:**
- Upgrade to paid plan ($7/month) for always-on service
- Use external monitoring service to ping every 10 minutes
- Accept the limitation for development/testing

### Upload Files Disappear
**Issue:** Files lost after redeployment

**Solution:** Verify disk is configured in render.yaml (already done):
```yaml
disk:
  name: deepfake-storage
  mountPath: /opt/render/project/src/storage
  sizeGB: 1
```

### MongoDB Connection Fails
**Error:** `MongoServerError: Authentication failed`

**Solutions:**
1. Verify `MONGODB_URI` environment variable is set correctly
2. Check MongoDB Atlas IP whitelist includes `0.0.0.0/0`
3. Verify database user credentials
4. Ensure connection string format: `mongodb+srv://user:pass@cluster.mongodb.net/dbname`

### CORS Errors
**Issue:** Frontend can't connect to backend

**Solution:** Already configured in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Optimization Tips

### 1. Enable Caching
Add to `render.yaml`:
```yaml
buildFilter:
  paths:
    - backend/**
    - frontend/**
    - package.json
    - requirements.txt
```

### 2. Use CDN for Assets
Consider using Cloudflare or similar CDN for static assets.

### 3. Optimize Images
Use WebP format and compression for uploaded images.

### 4. Database Indexing
Create indexes on frequently queried fields in MongoDB.

---

## Updating Your Deployment

### Method 1: Git Push (Recommended)
```bash
git add .
git commit -m "Update feature X"
git push origin main
```
Render auto-deploys within 1-2 minutes.

### Method 2: Manual Deploy
1. Go to Render Dashboard
2. Click your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## Cost Breakdown

### Free Tier (Current Setup):
- ✅ 750 hours/month (enough for 24/7 operation)
- ✅ 1 GB persistent disk
- ✅ Automatic SSL certificates
- ✅ Custom domains supported
- ⚠️ Spins down after 15 minutes inactivity
- ⚠️ 512 MB RAM limit

### Paid Tier ($7/month):
- ✅ Always-on (no spin-down)
- ✅ 2 GB RAM
- ✅ Faster builds
- ✅ Priority support

---

## Next Steps

1. ✅ **Set up custom domain** (optional)
   - Go to Settings → Custom Domain
   - Add your domain and configure DNS

2. ✅ **Enable monitoring**
   - Set up UptimeRobot or similar service
   - Monitor uptime and response times

3. ✅ **Configure backups**
   - MongoDB Atlas provides automatic backups
   - Export important data regularly

4. ✅ **Set up CI/CD**
   - Already configured with auto-deploy
   - Consider adding GitHub Actions for testing

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **MongoDB Atlas Docs:** https://docs.atlas.mongodb.com
- **Project Issues:** Create issue in your GitHub repository

---

## Summary Checklist

- [ ] GitHub repository set up and pushed
- [ ] Render account created
- [ ] Web service created and configured
- [ ] Environment variables set (including MONGODB_URI if needed)
- [ ] First deployment successful
- [ ] Health check endpoint responding
- [ ] Frontend loads correctly
- [ ] File upload works
- [ ] Deepfake detection functions properly
- [ ] Auto-deploy enabled
- [ ] Monitoring set up (optional)
- [ ] Custom domain configured (optional)

**Congratulations! Your Deep-detection app is now live on Render! 🎉**
