# 🚀 ThreatWatch Deployment Checklist

## Pre-Deployment Setup

### 📋 Accounts Required
- [ ] MongoDB Atlas account created
- [ ] Railway/Render account created  
- [ ] Vercel account created
- [ ] PostHog Cloud account created
- [ ] Domain registrar access (if using custom domain)

### 🔑 API Keys & Credentials
- [ ] MongoDB connection string obtained
- [ ] PostHog project API key obtained
- [ ] Google Custom Search API key verified
- [ ] Emergent LLM key verified
- [ ] Secure JWT secret generated (32+ chars)
- [ ] Stripe keys (if using payments)

## Deployment Steps

### 1. Database (MongoDB Atlas)
- [ ] Cluster created and configured
- [ ] Database user created with strong password
- [ ] Network access configured (0.0.0.0/0 or specific IPs)
- [ ] Connection string tested

### 2. Backend Deployment
- [ ] Railway/Render project created
- [ ] Repository connected
- [ ] Build configuration set
- [ ] Environment variables added
- [ ] First deployment successful
- [ ] Health endpoint responding

### 3. Frontend Deployment  
- [ ] Backend URL updated in frontend env
- [ ] Vercel project created
- [ ] Build configuration verified
- [ ] Environment variables added
- [ ] Deployment successful
- [ ] Site accessible

### 4. Integration Testing
- [ ] User registration working
- [ ] User login working
- [ ] Quick scan functionality working
- [ ] PDF generation working
- [ ] PDF download working
- [ ] Analytics events tracking
- [ ] Error handling working

### 5. Production Configuration
- [ ] Custom domains configured (if applicable)
- [ ] SSL certificates active
- [ ] CORS settings updated
- [ ] Rate limiting configured
- [ ] Monitoring alerts set up

## Post-Deployment

### 🔍 Monitoring Setup
- [ ] PostHog dashboards created
- [ ] Error tracking alerts configured
- [ ] Performance monitoring active
- [ ] Uptime monitoring configured

### 📊 Analytics Verification
- [ ] User signup events tracking
- [ ] Quick scan events tracking  
- [ ] PDF download events tracking
- [ ] Error events tracking
- [ ] Performance metrics collecting

### 🔒 Security Checklist
- [ ] All environment variables secured
- [ ] Database access restricted
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Rate limiting active

## Troubleshooting Commands

```bash
# Test backend health
curl https://your-backend.railway.app/health

# Test authentication
curl -X POST https://your-backend.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@domain.com","full_name":"Test","password":"Test123","confirm_password":"Test123"}'

# Check Railway logs
railway logs

# Check Vercel deployment logs
vercel logs
```
