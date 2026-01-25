# Backend Deployment Troubleshooting Guide

## Why Your Backend Is Not Working

Your backend is likely failing for one of these reasons:

### 1. **Code Not Pushed to GitHub**
- **Problem**: Your local fixes haven't been uploaded to GitHub
- **Result**: Cloud platform is running old, broken code
- **Check**: Run `git status` - if you see uncommitted changes, this is the issue

### 2. **Environment Variables Missing**
- **Problem**: Railway/Cloud doesn't have `MONGO_URI` or `HF_TOKEN`
- **Result**: Backend crashes on startup
- **Check**: Look at Railway logs for "KeyError" or "Environment variable not found"

### 3. **Build Failure**
- **Problem**: Docker build failed during deployment
- **Result**: No backend server is running
- **Check**: Railway deployment logs show "Build failed" or "Error"

### 4. **Port Configuration**
- **Problem**: Backend listening on wrong port
- **Result**: Cloud platform can't connect to your app
- **Check**: Dockerfile should use `PORT` environment variable

---

## Step-by-Step Fix Instructions

### Step 1: Push Your Code to GitHub

```bash
# Check what needs to be committed
git status

# Add all changes
git add .

# Commit with a message
git commit -m "Fix backend deployment issues"

# Push to GitHub
git push origin main
```

**Wait 2-3 minutes** for Railway to detect the push and start rebuilding.

---

### Step 2: Check Railway Deployment Logs

1. Go to your **Railway Dashboard**
2. Click on your **Deep-detection** project
3. Click on the **Deployments** tab
4. Look at the latest deployment logs

**What to look for:**
- ✅ "Build successful" - Good!
- ❌ "Error" or "Build failed" - Go to Step 3
- ❌ "Application error" - Go to Step 4

---

### Step 3: Fix Build Errors

**Common Build Errors:**

#### Error: "No such file or directory: dist/index.html"
**Cause**: Frontend build failed
**Fix**: 
```bash
# Test locally first
npm run build

# If it works, commit and push
git add dist/
git commit -m "Add built frontend"
git push origin main
```

#### Error: "pip install failed"
**Cause**: Missing Python dependencies
**Fix**: Check `backend/requirements.txt` is correct and committed

---

### Step 4: Fix Runtime Errors

**Common Runtime Errors:**

#### Error: "KeyError: 'MONGO_URI'"
**Cause**: Environment variables not set
**Fix**:
1. Go to Railway → Your Project → **Variables** tab
2. Add these variables:
   - `MONGO_URI`: Your MongoDB connection string
   - `HF_TOKEN`: Your HuggingFace token
   - `MONGO_DB_NAME`: `sentinel_ai`
3. Click **Redeploy**

#### Error: "Connection refused" or "502 Bad Gateway"
**Cause**: Backend not listening on correct port
**Fix**: Already handled in our Dockerfile (uses PORT env var)

---

### Step 5: Test Your Deployment

1. Visit your Railway URL (e.g., `https://deep-detection-production.up.railway.app`)
2. Open browser console (F12)
3. Try uploading a video
4. Check console for errors

**If you see network errors:**
- Backend is not running
- Go back to Step 2 and check logs

**If you see "Failed to upload" with a specific error:**
- Backend is running but has an issue
- Share the error message for specific help

---

## Quick Diagnostic Commands

Run these locally to verify everything works:

```bash
# Test frontend build
npm run build

# Test Docker build (if you have Docker installed)
docker build -t test-app .

# Check git status
git status
```

---

## Still Not Working?

If you've followed all steps and it's still broken, check:

1. **Railway Service Logs** - Look for the actual error message
2. **Browser Console** (F12) - Check for network errors
3. **Railway Service Settings** - Ensure "Generate Domain" is enabled

The most common issue is **forgetting to push to GitHub**. Always run `git push origin main` after making changes!
