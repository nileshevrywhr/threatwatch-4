# 🧪 Phase 1 Testing & Deployment Guide

## 🎉 What We've Built - Phase 1 Complete!

### ✅ Completed Components:

1. **MongoDB Models** - All data structures defined
2. **Database Layer** - MongoDB connection with automatic indexing
3. **Migration Script** - SQLite → MongoDB data migration
4. **Celery Configuration** - Background job processing setup
5. **Monitor Service** - CRUD operations for monitoring terms
6. **Alert Service** - Alert lifecycle management
7. **Monitor Engine** - Core threat scanning logic
8. **Celery Tasks** - Background scanning jobs
9. **API Endpoints** - Complete REST API for monitors and alerts
10. **Health Checks** - System monitoring endpoints

---

## 🔧 Local Testing (Before Deployment)

### Step 1: Test Health Endpoints

```bash
# Test backend health
curl http://localhost:8001/health

# Test MongoDB connection
curl http://localhost:8001/api/health/mongodb

# Test Redis connection
curl http://localhost:8001/api/health/redis

# Test system health (comprehensive)
curl http://localhost:8001/api/health/system
```

**Expected Results:**
- All should return `"status": "healthy"`
- MongoDB: `"connected": true`
- Redis: Should show Upstash URL
- System: Shows collection stats

### Step 2: Run Migration (If You Have Existing Users)

```bash
cd /app/backend
python migration_script.py
```

This will:
- Read all users from SQLite (auth.db)
- Convert to MongoDB format
- Insert into MongoDB users collection
- Migrate subscriptions and payments
- Verify migration success

**Note:** If you're starting fresh, no migration needed!

### Step 3: Test Authentication (Existing Endpoints)

```bash
# Register a test user
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@threatwatch.com",
    "password": "SecurePass123",
    "full_name": "Test User",
    "confirm_password": "SecurePass123"
  }'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@threatwatch.com",
    "password": "SecurePass123"
  }'

# Copy the access_token from response
TOKEN="your_access_token_here"
```

### Step 4: Test Monitor Endpoints

```bash
# Create a monitor
curl -X POST http://localhost:8001/api/monitors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "ransomware attacks",
    "description": "Monitor ransomware threats",
    "keywords": ["ransomware", "malware", "cyberattack"],
    "exclude_keywords": ["game", "movie"],
    "frequency": "daily",
    "severity_threshold": "medium"
  }'

# List monitors
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/monitors

# Get specific monitor (use ID from create response)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/monitors/MONITOR_ID

# Update monitor
curl -X PUT http://localhost:8001/api/monitors/MONITOR_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "active": true,
    "frequency": "hourly"
  }'

# Test monitor (trigger immediate scan)
curl -X POST http://localhost:8001/api/monitors/MONITOR_ID/test \
  -H "Authorization: Bearer $TOKEN"
```

### Step 5: Start Celery Worker (Required for Scans)

Open a new terminal:

```bash
cd /app/backend

# Start Celery worker
celery -A celery_app worker --loglevel=info
```

Keep this running. You should see:
```
[2024-10-04 10:00:00,000: INFO/MainProcess] Connected to redis://...
[2024-10-04 10:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### Step 6: Start Celery Beat (Scheduler)

Open another terminal:

```bash
cd /app/backend

# Start Celery beat
celery -A celery_app beat --loglevel=info
```

You should see periodic task schedules:
```
Scheduler: Sending due task scan-due-monitors-every-5-minutes
Scheduler: Sending due task health-check-every-10-minutes
```

### Step 7: Monitor Celery Tasks

Optional - Web UI for monitoring:

```bash
cd /app/backend

# Start Flower (Celery monitoring tool)
celery -A celery_app flower
```

Then open: http://localhost:5555

You'll see:
- Active workers
- Task history
- Task success/failure rates
- Real-time task monitoring

### Step 8: Test Manual Scan

```bash
# Trigger a test scan for your monitor
curl -X POST http://localhost:8001/api/monitors/MONITOR_ID/test \
  -H "Authorization: Bearer $TOKEN"
```

Watch the Celery worker terminal - you should see:
```
[INFO] 🔍 Scanning monitor: ransomware attacks (ID: xxx)
[INFO]   📡 Searching Google: 'ransomware attacks'
[INFO]   📊 Found 10 articles
[INFO]   ✅ 8 relevant articles after filtering
[INFO]   🤖 Analyzing articles with AI...
[INFO]   📈 Threat severity: high
[INFO]   🚨 Creating alert...
[INFO]   ✅ Alert created: alert-id
[INFO] ✅ Scan complete in 12.3s (Cost: $0.0105)
```

### Step 9: Check Alerts

```bash
# List all alerts
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/alerts

# Get monitor's alerts
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/monitors/MONITOR_ID/alerts

# Get specific alert
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/alerts/ALERT_ID

# Update alert status
curl -X PUT "http://localhost:8001/api/alerts/ALERT_ID/status?status=acknowledged" \
  -H "Authorization: Bearer $TOKEN"

# Get alert statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/alerts/statistics/summary
```

---

## 🚀 Railway Deployment

### Deployment Architecture

Railway will run 3 processes (defined in Procfile):
1. **web**: FastAPI server (port 8001)
2. **worker**: Celery worker (background tasks)
3. **beat**: Celery beat (scheduler)

### Step 1: Verify Environment Variables on Railway

Make sure these are set:

```
# Database
MONGO_URL=mongodb+srv://...
DB_NAME=threatwatch

# Redis (Upstash)
REDIS_URL=rediss://...
CELERY_BROKER_URL=rediss://...
CELERY_RESULT_BACKEND=rediss://...

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google APIs
GOOGLE_API_KEY=...
GOOGLE_SEARCH_ENGINE_ID=...

# AI Integration
EMERGENT_LLM_KEY=...

# Analytics
POSTHOG_API_KEY=...
POSTHOG_HOST=...

# CORS
CORS_ORIGINS=https://threatwatch-4.vercel.app,https://threatwatch.com

# Environment
ENVIRONMENT=production
```

### Step 2: Deploy to Railway

```bash
# If using Railway CLI
railway up

# Or push to GitHub (if Railway is connected to your repo)
git add .
git commit -m "Phase 1: Add monitoring feature"
git push origin main
```

### Step 3: Verify Deployment

Once deployed, check:

```bash
# Replace with your Railway URL
RAILWAY_URL="https://your-app.railway.app"

# Test health
curl $RAILWAY_URL/api/health/system

# Test API
curl -X POST $RAILWAY_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test","confirm_password":"Test123!"}'
```

### Step 4: Monitor Celery on Railway

Railway logs will show:
- Web process logs (FastAPI)
- Worker process logs (Celery tasks)
- Beat process logs (Scheduler)

Check logs:
```bash
# Via Railway CLI
railway logs

# Or view in Railway dashboard
```

---

## 🔍 Troubleshooting

### Issue: "Monitor limit reached"

**Cause:** Free tier users can only create 1 monitor

**Solution:** 
- Test with different user
- Upgrade subscription tier
- Or temporarily modify tier limits in code

### Issue: Celery workers not connecting to Redis

**Cause:** SSL configuration issue with Upstash

**Solution:** 
- Verify REDIS_URL starts with `rediss://` (with SSL)
- Check broker_use_ssl configuration in celery_app.py
- Test Redis connection: `python celery_app.py`

### Issue: Scans not running automatically

**Causes:**
1. Celery Beat not running
2. Monitor's next_scan time in future
3. Monitor is inactive

**Solutions:**
1. Start Celery Beat: `celery -A celery_app beat`
2. Trigger manual test: `POST /api/monitors/{id}/test`
3. Check monitor status: `GET /api/monitors/{id}`

### Issue: "No articles found" in scans

**Causes:**
1. Google API quota exceeded
2. Search term too specific
3. No recent news for that term

**Solutions:**
1. Check Google API quota in Google Cloud Console
2. Use broader search terms
3. Test with popular terms like "cybersecurity" or "ransomware"

### Issue: LLM analysis failing

**Causes:**
1. EMERGENT_LLM_KEY invalid
2. LLM quota exceeded
3. Network issues

**Solutions:**
1. Verify EMERGENT_LLM_KEY in environment
2. Check LLM usage in logs
3. Test with simple scan first

---

## 📊 Success Metrics

After deployment, you should see:

### Database Collections (MongoDB)
```bash
curl $RAILWAY_URL/api/health/system
```

Should show:
- users: > 0
- monitors: > 0 (after creating monitors)
- alerts: > 0 (after scans run)
- alert_history: > 0

### Celery Workers
```bash
curl $RAILWAY_URL/api/health/celery
```

Should show:
- worker_count: > 0
- status: "healthy"

### Scheduled Tasks Running

Check alert_history collection:
- Should have records every 5 minutes (when monitors are due)
- scan_timestamp should be recent
- success: true

---

## 🎓 What You've Learned

Congratulations! You've now learned:

1. **MongoDB with Python** - NoSQL database operations
2. **Async Python** - async/await patterns with Motor
3. **Celery** - Distributed task queues
4. **Redis** - Message broker and result backend
5. **Background Jobs** - Scheduling and processing
6. **FastAPI** - Advanced REST API development
7. **System Architecture** - Designing scalable monitoring systems

---

## 📝 Next Steps

Phase 1 is complete! Here's what comes next:

### Phase 2: Notifications (Week 4-6)
- Email notifications via SendGrid
- SMS notifications via Twilio
- Webhook integrations
- Daily/weekly digest emails

### Phase 3: Frontend (Week 7-9)
- Monitor management UI
- Alert dashboard
- Real-time updates
- Analytics visualizations

### Phase 4: Advanced Features (Week 10-12)
- Multi-source intelligence
- Team collaboration
- API access
- Enterprise features

---

## 🆘 Need Help?

### Check Logs
```bash
# Backend logs
tail -f /var/log/supervisor/backend.out.log

# Celery worker logs (if using supervisor)
tail -f /var/log/supervisor/celery-worker.out.log
```

### Test Individual Components
```bash
# Test Celery configuration
python celery_app.py

# Test monitor engine
python -c "from monitor_engine import MonitorEngine; print(MonitorEngine())"

# Test MongoDB connection
python -c "from database import check_mongodb_connection; import asyncio; print(asyncio.run(check_mongodb_connection()))"
```

### Common Commands
```bash
# Restart backend
sudo supervisorctl restart backend

# Check backend status
sudo supervisorctl status backend

# Start Celery worker
celery -A celery_app worker --loglevel=info

# Start Celery beat
celery -A celery_app beat --loglevel=info

# Monitor Celery
celery -A celery_app flower
```

---

**You're all set! 🎉**

Your monitoring system is now ready to detect threats 24/7 automatically!
