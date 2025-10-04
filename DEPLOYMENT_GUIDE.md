# ThreatWatch Production Deployment Guide

## 🏗️ Architecture Overview

Your ThreatWatch application consists of three main components that need separate deployment:

1. **Frontend (React)** → **Vercel** ✅ (Recommended)
2. **Backend (FastAPI)** → **Railway/Render/DigitalOcean** ✅ 
3. **Database (MongoDB)** → **MongoDB Atlas** ✅

## 📋 Pre-Deployment Checklist

### ✅ Required Accounts & API Keys
- [ ] Vercel account (for frontend)
- [ ] Railway/Render account (for backend) 
- [ ] MongoDB Atlas account (for database)
- [ ] PostHog Cloud account (analytics)
- [ ] Google Cloud account (Custom Search API)
- [ ] Emergent LLM key (AI integration)

---

## 🗄️ **STEP 1: Database Deployment (MongoDB Atlas)**

### 1.1 Create MongoDB Atlas Cluster
```bash
# Go to https://cloud.mongodb.com/
# Sign up for free account (512MB free tier)
```

### 1.2 Setup Instructions
1. **Create New Project**: Name it "ThreatWatch"
2. **Build Database**: Choose "Free Shared" (M0 Sandbox)
3. **Cloud Provider**: Choose your preferred region
4. **Cluster Name**: `threatwatch-cluster`
5. **Create Database User**: 
   - Username: `threatwatch-admin`
   - Password: Generate secure password (save it!)
6. **Network Access**: Add `0.0.0.0/0` (allow from anywhere)
7. **Connect**: Choose "Connect your application"
8. **Driver**: Python, Version 3.12 or later
9. **Copy Connection String**: 
   ```
   mongodb+srv://threatwatch-admin:FBKz2ZM3xU90arFM@threatwatch-cluster.kqkappu.mongodb.net/?retryWrites=true&w=majority&appName=threatwatch-cluster
   ```

### 1.3 Database Setup
```bash
# Your connection string will look like:
MONGO_URL=mongodb+srv://threatwatch-admin:YOUR_PASSWORD@threatwatch-cluster.xxxxx.mongodb.net/threatwatch?retryWrites=true&w=majority
```

---

## 🖥️ **STEP 2: Backend Deployment**

### Option A: Railway (Recommended - Easy Setup)

#### 2.1 Railway Setup
```bash
# Go to https://railway.app/
# Sign up with GitHub account
# Install Railway CLI (optional)
npm install -g @railway/cli
```

#### 2.2 Deploy Backend to Railway
1. **Create New Project** → "Deploy from GitHub repo"
2. **Connect Repository** → Select your ThreatWatch repo
3. **Add Service** → "GitHub Repo" → Select backend folder
4. **Configure Build**:
   - **Root Directory**: `/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

#### 2.3 Environment Variables (Railway)
Add these in Railway dashboard → Settings → Environment:
```bash
# Database
MONGO_URL=mongodb+srv://threatwatch-admin:PASSWORD@threatwatch-cluster.xxxxx.mongodb.net/threatwatch?retryWrites=true&w=majority
DB_NAME=threatwatch

# Authentication
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-for-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google APIs
GOOGLE_API_KEY=AIzaSyAl7l21PEHK_McH2C7yCBsBE2Mtv7IAvew
GOOGLE_SEARCH_ENGINE_ID=c44646770ee284c79

# AI Integration
EMERGENT_LLM_KEY=sk-emergent-887E98dE8781142254

# Analytics
POSTHOG_API_KEY=phc_your_actual_posthog_key_here
POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_SYNC_MODE=True
POSTHOG_DEBUG=False

# Payment (if using Stripe)
STRIPE_API_KEY=your-stripe-live-api-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# CORS - Important!
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://threatwatch.com

# Environment
ENVIRONMENT=production
APP_VERSION=1.0.0
```

#### 2.4 Custom Domain (Railway)
1. **Settings** → **Networking** → **Custom Domain**
2. Add: `api.threatwatch.com` (or your preferred subdomain)
3. Configure DNS: Add CNAME record pointing to Railway domain

### Option B: Render (Alternative)

#### 2.1 Render Setup
```bash
# Go to https://render.com/
# Sign up with GitHub account
```

#### 2.2 Deploy to Render
1. **New** → **Web Service**
2. **Connect Repository** → Select your ThreatWatch repo
3. **Configuration**:
   - **Name**: `threatwatch-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free tier (512MB RAM)

### Option C: DigitalOcean App Platform

#### 2.1 DigitalOcean Setup
1. Go to https://cloud.digitalocean.com/
2. Create new App → GitHub repository
3. **Component Type**: Web Service
4. **Source Directory**: `/backend`
5. **Auto-deploy**: Yes

---

## 🌐 **STEP 3: Frontend Deployment (Vercel)**

### 3.1 Prepare Frontend for Production

#### Update package.json (if needed)
```json
{
  "scripts": {
    "build": "react-scripts build",
    "start": "serve -s build"
  }
}
```

### 3.2 Deploy to Vercel

#### Method 1: Vercel Dashboard (Recommended)
1. **Go to https://vercel.com/**
2. **Sign up with GitHub**
3. **New Project** → **Import Git Repository**
4. **Select your ThreatWatch repository**
5. **Configure Project**:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `yarn build`
   - **Output Directory**: `build`
   - **Install Command**: `yarn install`

#### Method 2: Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend directory
cd frontend

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: threatwatch-frontend
# - Directory: ./
```

### 3.3 Environment Variables (Vercel)
In Vercel Dashboard → Settings → Environment Variables:
```bash
# Backend API URL - UPDATE THIS!
REACT_APP_BACKEND_URL=https://your-backend-domain.railway.app

# Analytics
REACT_APP_POSTHOG_KEY=phc_your_actual_posthog_key_here
REACT_APP_POSTHOG_HOST=https://us.i.posthog.com
```

### 3.4 Custom Domain (Vercel)
1. **Settings** → **Domains**
2. **Add Domain**: `threatwatch.com` and `www.threatwatch.com`
3. **Configure DNS**: Add A and CNAME records as instructed

---

## 🔧 **STEP 4: Configuration Updates**

### 4.1 Update CORS Settings
In your backend environment variables, update:
```bash
CORS_ORIGINS=https://threatwatch.com,https://www.threatwatch.com,https://your-app.vercel.app
```

### 4.2 Update Frontend API URL
In Vercel environment variables:
```bash
REACT_APP_BACKEND_URL=https://api.threatwatch.com
# OR
REACT_APP_BACKEND_URL=https://your-backend.railway.app
```

### 4.3 PostHog Configuration
Update PostHog settings for production:
```bash
# Backend
POSTHOG_SYNC_MODE=True  # Important for serverless
POSTHOG_DEBUG=False

# Frontend
REACT_APP_POSTHOG_KEY=phc_your_production_key_here
```

---

## 📊 **STEP 5: Database Migration & Setup**

### 5.1 Test Database Connection
```bash
# Test your MongoDB Atlas connection
# The FastAPI app will automatically create collections on first run
```

### 5.2 Create Initial Indexes (Optional)
```javascript
// Connect to MongoDB Atlas via Compass or mongosh
// Create indexes for better performance:

// Users collection
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "id": 1 }, { unique: true })

// Quick scans collection (if you add scan history)
db.scans.createIndex({ "user_id": 1 })
db.scans.createIndex({ "created_at": -1 })
```

---

## 🚀 **STEP 6: Deployment Process**

### 6.1 Deployment Order
1. **Deploy Database** → MongoDB Atlas ✅
2. **Deploy Backend** → Railway/Render ✅
3. **Update Frontend Config** → Backend URL ✅
4. **Deploy Frontend** → Vercel ✅
5. **Test Integration** → Full E2E testing ✅

### 6.2 Post-Deployment Testing
```bash
# Test backend health
curl https://your-backend-url.railway.app/health

# Test authentication
curl -X POST https://your-backend-url.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","full_name":"Test User","password":"Test123","confirm_password":"Test123"}'

# Test frontend
# Visit https://your-app.vercel.app and test:
# - User registration
# - Quick scan
# - PDF download
```

---

## 💰 **Cost Estimates (Monthly)**

### Free Tier (Recommended for MVP)
- **MongoDB Atlas**: Free (512MB)
- **Railway**: $5/month (512MB RAM, 500GB transfer)
- **Vercel**: Free (100GB bandwidth, unlimited deployments)
- **PostHog**: Free (1M events/month)
- **Total**: ~$5/month

### Production Tier
- **MongoDB Atlas**: $9/month (2GB RAM, 10GB storage)
- **Railway**: $20/month (2GB RAM, 100GB transfer)
- **Vercel Pro**: $20/month (1TB bandwidth, advanced analytics)
- **PostHog**: $0-450/month (based on usage)
- **Total**: ~$50-500/month (scales with usage)

---

## 🔒 **Security Checklist**

### Production Security
- [ ] Use strong JWT secret keys (32+ characters)
- [ ] Enable HTTPS only (Vercel/Railway provide SSL)
- [ ] Configure proper CORS origins
- [ ] Use environment variables for all secrets
- [ ] Enable MongoDB Atlas network restrictions
- [ ] Set up rate limiting in production
- [ ] Configure PostHog data retention policies

### Environment Variables Security
```bash
# Generate secure JWT secret
openssl rand -base64 32
# Example: 8f2a4b6c9d1e3f5g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z

# Update in production:
JWT_SECRET_KEY=your-super-secure-32-character-secret-key-here
```

---

## 🔧 **Troubleshooting Common Issues**

### Backend Issues
```bash
# Check Railway logs
railway logs

# Check Render logs
# Go to Render Dashboard → Service → Logs

# Common fixes:
# 1. Port binding: Ensure uvicorn uses $PORT
# 2. Requirements: Make sure all dependencies in requirements.txt
# 3. Path issues: Use absolute imports in FastAPI
```

### Frontend Issues
```bash
# Check Vercel build logs
# Go to Vercel Dashboard → Deployments → View Build Logs

# Common fixes:
# 1. Build command: yarn build (not npm)
# 2. Environment variables: REACT_APP_ prefix required
# 3. API URL: Must include https:// and no trailing slash
```

### Database Issues
```bash
# MongoDB Atlas connection test:
# 1. Check IP whitelist (0.0.0.0/0 for development)
# 2. Verify username/password
# 3. Test connection string format
# 4. Check network access settings
```

---

## 📞 **Support Resources**

### Platform Documentation
- **Vercel**: https://vercel.com/docs
- **Railway**: https://docs.railway.app/
- **Render**: https://render.com/docs
- **MongoDB Atlas**: https://docs.atlas.mongodb.com/
- **PostHog**: https://posthog.com/docs

### ThreatWatch Specific Help
- Check `/app/POSTHOG_SETUP_GUIDE.md` for analytics setup
- Review `/app/test_result.md` for testing protocols
- All environment variables documented in `/app/backend/.env.example`

---

## 🎯 **Quick Start Commands**

```bash
# 1. Deploy Database (MongoDB Atlas)
# → Follow web interface setup

# 2. Deploy Backend (Railway)
railway login
railway new
railway add
railway deploy

# 3. Deploy Frontend (Vercel)
cd frontend
vercel
vercel --prod

# 4. Test deployment
curl https://your-backend.railway.app/health
```

Your ThreatWatch application will be production-ready with this setup! 🚀