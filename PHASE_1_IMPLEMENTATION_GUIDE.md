# 🚀 Phase 1: Foundation Implementation Guide

## Overview
Phase 1 transforms ThreatWatch authentication from SQLite to MongoDB and adds the foundation for long-term monitoring with background job processing.

---

## 📋 Implementation Checklist

### Part A: Database Migration (Weeks 1)
- [ ] Create MongoDB models for User, UserSubscription, PaymentTransaction
- [ ] Create MongoDB models for Monitor, Alert, AlertHistory
- [ ] Write migration script to move existing SQLite data to MongoDB
- [ ] Update auth_service.py to use MongoDB
- [ ] Test authentication flow with MongoDB
- [ ] Remove SQLite dependencies

### Part B: Core API Endpoints (Week 1-2)
- [ ] POST /api/monitors - Create a new monitoring term
- [ ] GET /api/monitors - List user's monitors
- [ ] GET /api/monitors/{id} - Get specific monitor details
- [ ] PUT /api/monitors/{id} - Update monitor settings
- [ ] DELETE /api/monitors/{id} - Delete monitor
- [ ] POST /api/monitors/{id}/test - Test monitor configuration
- [ ] GET /api/monitors/{id}/alerts - Get alerts for a monitor

### Part C: Job Scheduling System (Week 2-3)
- [ ] Install Celery and Redis dependencies
- [ ] Configure Celery with Redis broker
- [ ] Create celery_app.py configuration
- [ ] Create monitoring tasks (scan_monitor_task)
- [ ] Set up Celery Beat for scheduling
- [ ] Create health check endpoints for Celery
- [ ] Test background job execution

### Part D: Basic Monitoring Engine (Week 3)
- [ ] Create monitor_engine.py with scanning logic
- [ ] Implement keyword-based search using existing Google Search client
- [ ] Add LLM analysis for threat assessment
- [ ] Create alert generation logic
- [ ] Implement alert deduplication
- [ ] Add monitoring frequency logic (hourly, daily, weekly)

---

## 🗄️ Database Schema Details

### **Users Collection** (Migrated from SQLite)
```javascript
{
  "_id": "uuid-string",
  "email": "user@example.com",
  "full_name": "John Doe",
  "hashed_password": "bcrypt_hash",
  "is_active": true,
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "last_login": ISODate("2024-01-15T10:00:00Z"),
  "quick_scans_today": 0,
  "quick_scans_reset_date": ISODate("2024-01-15T00:00:00Z")
}
```

### **User Subscriptions Collection**
```javascript
{
  "_id": "uuid-string",
  "user_id": "user-uuid",
  "tier": "free", // free, professional, enterprise, enterprise_plus
  "status": "active", // active, cancelled, expired
  "stripe_customer_id": "cus_xxx",
  "stripe_subscription_id": "sub_xxx",
  "current_period_start": ISODate("2024-01-15T00:00:00Z"),
  "current_period_end": ISODate("2024-02-15T00:00:00Z"),
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "updated_at": ISODate("2024-01-15T10:00:00Z")
}
```

### **Monitors Collection** (NEW)
```javascript
{
  "_id": "uuid-string",
  "user_id": "user-uuid",
  "term": "ransomware attacks healthcare",
  "description": "Monitor ransomware targeting healthcare sector",
  "keywords": ["ransomware", "healthcare", "hospital", "medical"],
  "exclude_keywords": ["games", "entertainment"],
  "frequency": "daily", // hourly, daily, weekly
  "severity_threshold": "medium", // low, medium, high, critical
  "active": true,
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "updated_at": ISODate("2024-01-15T10:00:00Z"),
  "last_scan": ISODate("2024-01-15T15:30:00Z"),
  "next_scan": ISODate("2024-01-16T15:30:00Z"),
  "scan_count": 45,
  "alert_count": 12,
  "notification_settings": {
    "email": true,
    "sms": false,
    "webhook": null,
    "immediate_alerts": true,
    "daily_summary": true,
    "weekly_report": false
  }
}
```

### **Alerts Collection** (NEW)
```javascript
{
  "_id": "uuid-string",
  "monitor_id": "monitor-uuid",
  "user_id": "user-uuid",
  "title": "New Ransomware Campaign Targets Healthcare",
  "summary": "AI-generated threat summary...",
  "severity": "high", // low, medium, high, critical
  "confidence_score": 0.87,
  "source_count": 15,
  "sources": [
    {
      "title": "Major Hospital Chain Hit by Ransomware",
      "url": "https://news.com/article",
      "domain": "reuters.com",
      "published": ISODate("2024-01-15T14:30:00Z"),
      "snippet": "Article preview...",
      "relevance_score": 0.92
    }
  ],
  "threat_indicators": {
    "attack_vectors": ["phishing", "rdp"],
    "affected_sectors": ["healthcare"],
    "geographical_scope": ["US", "Europe"],
    "threat_actors": ["unknown"]
  },
  "created_at": ISODate("2024-01-15T15:00:00Z"),
  "status": "new", // new, acknowledged, resolved, false_positive
  "user_feedback": null,
  "notification_sent": false,
  "pdf_report_id": null
}
```

### **Alert History Collection** (NEW)
```javascript
{
  "_id": "uuid-string",
  "monitor_id": "monitor-uuid",
  "scan_timestamp": ISODate("2024-01-15T15:30:00Z"),
  "scan_duration": 45.5, // seconds
  "articles_processed": 127,
  "alerts_generated": 3,
  "api_costs": {
    "google_search_queries": 8,
    "llm_tokens": 15420,
    "total_cost": 0.12
  },
  "scan_metadata": {
    "query_variations": ["ransomware healthcare", "hospital cyber attack"],
    "timeframe": "last 24 hours",
    "sources_scanned": ["news", "blogs"]
  },
  "errors": [] // Any errors during scanning
}
```

---

## 🔌 Environment Variables Needed

### **For MongoDB** (Already configured)
```bash
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=threatwatch
```

### **For Redis/Celery** (You'll need to add these)
```bash
# Upstash Redis URL (from Upstash dashboard)
REDIS_URL=redis://default:password@redis-host:port

# Celery configuration
CELERY_BROKER_URL=redis://default:password@redis-host:port
CELERY_RESULT_BACKEND=redis://default:password@redis-host:port
```

### **For Google Search & LLM** (Already configured)
```bash
GOOGLE_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_id
EMERGENT_LLM_KEY=your_key
```

---

## 📦 New Dependencies to Install

Add to `requirements.txt`:
```
celery==5.3.4
redis==5.0.1
celery-beat==2.6.0
flower==2.0.1  # Optional: Web UI for monitoring Celery
```

---

## 🏗️ File Structure After Phase 1

```
/app/backend/
├── server.py                    # Main FastAPI app (updated)
├── database.py                  # MongoDB connection (updated)
├── auth_models.py              # Remove (replaced by mongodb_models.py)
├── auth_service.py             # Updated for MongoDB
├── mongodb_models.py           # NEW - All MongoDB models
├── monitor_service.py          # NEW - Monitor CRUD operations
├── alert_service.py            # NEW - Alert management
├── celery_app.py               # NEW - Celery configuration
├── celery_tasks.py             # NEW - Background tasks
├── monitor_engine.py           # NEW - Scanning logic
├── migration_script.py         # NEW - SQLite to MongoDB migration
├── google_search_client.py     # Existing (reused)
├── cost_tracker.py             # Existing (reused)
└── requirements.txt            # Updated with new dependencies
```

---

## 🎯 Success Criteria for Phase 1

### **Authentication Migration**
- ✅ All existing users migrated to MongoDB
- ✅ Login/Register works with MongoDB
- ✅ JWT tokens work correctly
- ✅ Subscription data intact

### **Monitor Management**
- ✅ Create monitor via API
- ✅ List all user monitors
- ✅ Update monitor settings
- ✅ Delete monitor
- ✅ Test monitor returns results

### **Background Jobs**
- ✅ Celery worker starts successfully
- ✅ Celery Beat scheduler running
- ✅ Test job executes and completes
- ✅ Monitor scans run on schedule
- ✅ Alerts generated and saved

### **Health & Monitoring**
- ✅ `/api/health/celery` endpoint works
- ✅ `/api/health/redis` endpoint works
- ✅ Monitor scan logs available
- ✅ Error handling for failed scans

---

## 📝 Testing Strategy

### **Manual Testing**
1. Test user authentication with MongoDB
2. Create a test monitor via API
3. Trigger manual scan
4. Verify alert creation
5. Check Celery task execution

### **API Testing** (using curl)
```bash
# 1. Register/Login
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'

# 2. Create Monitor
curl -X POST http://localhost:8001/api/monitors \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"term":"ransomware healthcare","frequency":"daily"}'

# 3. Test Monitor
curl -X POST http://localhost:8001/api/monitors/{id}/test \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🚨 Common Issues & Solutions

### **Issue: Celery worker won't start**
**Solution**: Check Redis connection, verify CELERY_BROKER_URL

### **Issue: MongoDB connection fails**
**Solution**: Verify MONGO_URL, check IP whitelist in MongoDB Atlas

### **Issue: Tasks not executing**
**Solution**: Ensure Celery Beat is running, check task scheduling

### **Issue: Railway deployment fails**
**Solution**: Verify Procfile has both web and worker processes

---

## 📊 Next Steps After Phase 1

Once Phase 1 is complete and tested:
1. Phase 2: Add notification system (Email via SendGrid)
2. Phase 3: Build frontend dashboard for monitors
3. Phase 4: Add advanced features (multi-source, webhooks)
4. Phase 5: Production optimization

---

**Estimated Time**: 2-3 weeks for Phase 1
**Prerequisites**: MongoDB, Redis (Upstash), Railway deployment
**Skills Learned**: MongoDB, Celery, Background Jobs, Task Scheduling
