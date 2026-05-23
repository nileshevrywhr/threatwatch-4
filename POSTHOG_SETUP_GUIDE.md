# PostHog Analytics Setup Guide for SignalCanary

## 🎯 Overview
I've implemented comprehensive PostHog analytics tracking for your SignalCanary application to monitor the 5 key metrics you specified:

1. **Signups** → How many register, free vs. paid
2. **Searches per user** → Are they running 1 search or 50?  
3. **Report downloads** → Do they actually consume results?
4. **Drop-off points** → Are they searching but not downloading? Signing up but not searching?
5. **Revenue Tracking** → Subscription conversions, API cost monitoring

## 🔧 PostHog Cloud Setup (Required)

### Step 1: Create PostHog Cloud Account
1. Go to https://app.posthog.com/signup
2. Sign up for a new account (free tier includes 1M events/month)
3. Create a new project for "SignalCanary"
4. Choose your data region (US or EU based on your users)

### Step 2: Get Your API Keys
1. In your PostHog dashboard, go to **Project Settings**
2. Copy your **Project API Key** (starts with `phc_`)
3. Go to your **Personal API Keys** section
4. Create a **Personal API Key** for dashboard access

### Step 3: Update Environment Variables
Update your environment files with the actual PostHog keys:

#### Backend (.env):
```bash
# Replace this placeholder with your actual PostHog Project API Key
POSTHOG_API_KEY=phc_your_actual_project_api_key_here
POSTHOG_HOST=https://us.i.posthog.com  # or https://eu.i.posthog.com for EU
POSTHOG_SYNC_MODE=False
POSTHOG_DEBUG=False
```

#### Frontend (.env):
```bash
# Replace this placeholder with your actual PostHog Project API Key  
REACT_APP_POSTHOG_KEY=phc_your_actual_project_api_key_here
REACT_APP_POSTHOG_HOST=https://us.i.posthog.com  # or https://eu.i.posthog.com for EU
```

### Step 4: Restart Services
```bash
sudo supervisorctl restart all
```

## 📊 Analytics Implementation Summary

### ✅ Backend Analytics Implemented:
- **User Registration** → Tracks signups with plan type (Key Metric #1)
- **User Login** → Session tracking and user identification
- **Quick Scan Initiation** → Search behavior tracking (Key Metric #2)  
- **Quick Scan Completion** → Performance metrics, token usage, costs
- **PDF Generation** → Report creation tracking
- **PDF Downloads** → Consumption metrics (Key Metric #3)
- **Error Tracking** → Technical issues and API failures

### ✅ Frontend Analytics Implemented:
- **Page Views** → User navigation tracking
- **Authentication Events** → Login/registration success/failure
- **Quick Scan UI** → User interactions, form submissions
- **PDF Interactions** → Generate clicks, download attempts
- **Funnel Tracking** → Drop-off analysis (Key Metric #4)
- **Error Tracking** → Frontend errors and API failures

## 📈 Key Dashboards to Create in PostHog

### 1. Business Metrics Dashboard
**Events to track:**
- `user_signup` → Filter by `plan_type` to see free vs paid
- `quick_scan_initiated` → Count per user to see search frequency
- `pdf_report_downloaded` → Measure actual consumption
- `subscription_change` → Revenue tracking

### 2. User Journey Funnel
**Create funnels for:**
- **Signup Funnel:** Page view → Auth modal → Registration → Success
- **Scan-to-Download Funnel:** Scan initiated → Scan completed → PDF generated → PDF downloaded
- **Conversion Funnel:** Signup → First scan → Limit reached → Upgrade → Payment

### 3. Drop-off Analysis Dashboard
**Track these funnel steps:**
- `funnel_scan_to_download_scan_initiated`
- `funnel_scan_to_download_scan_completed`  
- `funnel_scan_to_download_pdf_generated`
- `funnel_scan_to_download_pdf_downloaded`

### 4. Performance & Error Dashboard
**Monitor:**
- `api_performance` → Response times, error rates
- `frontend_error` → JavaScript errors
- `backend_exception` → Server-side errors

## 🔍 Real-time Insights Available

Once PostHog is configured, you'll have access to:

### Key Metrics (Your Top 5):
1. **Signup Analytics:** Daily/weekly registrations, free vs paid breakdown
2. **Search Behavior:** Searches per user, popular queries, search frequency  
3. **Download Rates:** PDF generation vs download completion rates
4. **Drop-off Points:** Where users abandon the scan-to-download flow
5. **Revenue Tracking:** Subscription upgrades, cost per user, API usage costs

### User Behavior Insights:
- **Session Analysis:** Time on site, pages per session, bounce rate
- **Feature Adoption:** Which features are used most/least
- **Geographic Distribution:** Where your users are located
- **Device & Browser Analysis:** Technical user demographics

### Business Intelligence:
- **Conversion Rates:** Signup to first scan, scan to download, free to paid
- **User Retention:** Daily/weekly/monthly active users
- **Feature Performance:** Which queries generate the most downloads
- **Cost Analysis:** API costs per user, token efficiency metrics

## 📋 Testing Your Analytics

### 1. Backend Testing
```bash
# Check backend logs for analytics events
tail -f /var/log/supervisor/backend.out.log | grep -i posthog
```

### 2. Frontend Testing  
- Open browser developer tools
- Look for PostHog debug messages in console (if debug mode enabled)
- Check Network tab for analytics requests

### 3. PostHog Dashboard
- Go to your PostHog project dashboard
- Check "Live Events" to see real-time event tracking
- Verify user identification is working

## ⚠️ Important Notes

### Data Privacy
- User emails are tracked for identification
- All analytics include proper user consent handling
- Error messages are truncated to avoid sensitive data leakage

### Performance Impact
- Analytics are designed to be non-blocking
- Events are batched to minimize performance impact
- Fallback handling prevents analytics failures from breaking app functionality

### Cost Management
- PostHog free tier: 1M events/month, 5K session recordings/month  
- Backend events are prioritized (authentication, scans, downloads)
- Frontend events capture user interactions and errors

## 🚀 Next Steps

1. **Set up PostHog account and get API keys**
2. **Update environment variables with real keys**
3. **Restart services to activate analytics**
4. **Create dashboards in PostHog for your key metrics**
5. **Monitor and optimize based on real user data**

## 📞 Support

If you need help setting up PostHog or configuring dashboards, the analytics framework is already implemented and ready to start collecting data as soon as you provide the API keys!