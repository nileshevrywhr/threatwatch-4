#!/bin/bash

# ThreatWatch Deployment Preparation Script
# This script helps prepare your application for production deployment

set -e  # Exit on any error

echo "🚀 ThreatWatch Deployment Preparation"
echo "=================================="

# Check if required directories exist
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: frontend and backend directories must exist"
    exit 1
fi

echo "✅ Directory structure verified"

# Create production environment template
echo "📝 Creating production environment templates..."

# Backend production environment template
cat > backend/.env.production.template << EOF
# ==============================================
# ThreatWatch Production Environment Variables
# ==============================================

# 🗄️ Database Configuration
MONGO_URL=mongodb+srv://USERNAME:PASSWORD@CLUSTER.mongodb.net/threatwatch?retryWrites=true&w=majority
DB_NAME=threatwatch

# 🔐 Authentication
JWT_SECRET_KEY=GENERATE_SECURE_32_CHAR_SECRET_HERE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 🔍 Google Custom Search API
GOOGLE_API_KEY=AIzaSyAl7l21PEHK_McH2C7yCBsBE2Mtv7IAvew
GOOGLE_SEARCH_ENGINE_ID=c44646770ee284c79

# 🤖 AI Integration
EMERGENT_LLM_KEY=sk-emergent-887E98dE8781142254

# 📊 Analytics
POSTHOG_API_KEY=phc_YOUR_ACTUAL_POSTHOG_KEY_HERE
POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_SYNC_MODE=True
POSTHOG_DEBUG=False

# 💳 Payment Processing
STRIPE_API_KEY=sk_live_YOUR_STRIPE_LIVE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# 🌐 CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# 🏷️ Application Info
ENVIRONMENT=production
APP_VERSION=1.0.0
EOF

# Frontend production environment template
cat > frontend/.env.production.template << EOF
# ==============================================
# ThreatWatch Frontend Production Environment
# ==============================================

# 🖥️ Backend API URL (UPDATE WITH YOUR ACTUAL BACKEND URL)
REACT_APP_BACKEND_URL=https://your-backend-domain.railway.app

# 📊 Analytics
REACT_APP_POSTHOG_KEY=phc_YOUR_ACTUAL_POSTHOG_KEY_HERE
REACT_APP_POSTHOG_HOST=https://us.i.posthog.com
EOF

echo "✅ Environment templates created:"
echo "   - backend/.env.production.template"
echo "   - frontend/.env.production.template"

# Create Railway deployment configuration
echo "📝 Creating Railway configuration..."

cat > railway.toml << EOF
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd backend && uvicorn server:app --host 0.0.0.0 --port \$PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
EOF

echo "✅ Railway configuration created: railway.toml"

# Create Vercel configuration
echo "📝 Creating Vercel configuration..."

cat > frontend/vercel.json << EOF
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/\$1"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
EOF

echo "✅ Vercel configuration created: frontend/vercel.json"

# Update package.json scripts for production
echo "📝 Updating build scripts..."

# Update backend requirements.txt to include production dependencies
if ! grep -q "gunicorn" backend/requirements.txt; then
    echo "gunicorn==21.2.0" >> backend/requirements.txt
    echo "✅ Added gunicorn to requirements.txt"
fi

# Create deployment checklist
cat > DEPLOYMENT_CHECKLIST.md << EOF
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

\`\`\`bash
# Test backend health
curl https://your-backend.railway.app/health

# Test authentication
curl -X POST https://your-backend.railway.app/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@domain.com","full_name":"Test","password":"Test123","confirm_password":"Test123"}'

# Check Railway logs
railway logs

# Check Vercel deployment logs
vercel logs
\`\`\`
EOF

echo "✅ Deployment checklist created: DEPLOYMENT_CHECKLIST.md"

# Create environment variables helper script
cat > scripts/generate-jwt-secret.sh << 'EOF'
#!/bin/bash
# Generate secure JWT secret for production

echo "🔐 Generating secure JWT secret..."
JWT_SECRET=$(openssl rand -base64 32)
echo "Your secure JWT secret key:"
echo "JWT_SECRET_KEY=$JWT_SECRET"
echo ""
echo "⚠️  IMPORTANT: Save this secret securely and use it in your production environment!"
echo "   Do not commit this to version control."
EOF

chmod +x scripts/generate-jwt-secret.sh

echo "✅ JWT secret generator created: scripts/generate-jwt-secret.sh"

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: ./scripts/generate-jwt-secret.sh"
echo "2. Follow the deployment guide in DEPLOYMENT_GUIDE.md"
echo "3. Use the checklist in DEPLOYMENT_CHECKLIST.md"
echo "4. Configure environment variables using the templates created"
echo ""
echo "📂 Files created:"
echo "   - backend/.env.production.template"
echo "   - frontend/.env.production.template"
echo "   - railway.toml"
echo "   - frontend/vercel.json"
echo "   - DEPLOYMENT_CHECKLIST.md"
echo "   - scripts/generate-jwt-secret.sh"
echo ""
echo "🚀 Your ThreatWatch application is ready for deployment!"
EOF

chmod +x /app/scripts/prepare-deployment.sh