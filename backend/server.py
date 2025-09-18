from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Request, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import asyncio
import json

# Authentication and Payment imports
from database import Base, get_auth_db, engine
from auth_models import User, UserSubscription, PaymentTransaction
from auth_service import AuthService
from auth_schemas import *
from subscription_service import SubscriptionService, SUBSCRIPTION_TIERS
from emergentintegrations.llm.chat import LlmChat, UserMessage
import stripe
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database setup
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# MongoDB connection
mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client[DB_NAME]

# Create all tables
Base.metadata.create_all(bind=engine)

# Security
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_db: Session = Depends(get_auth_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    payload = AuthService.verify_token(credentials.credentials)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
    
    # Convert string UUID to UUID object for database query
    try:
        import uuid as uuid_module
        user_uuid = uuid_module.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID format"
        )
    
    user = auth_db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Create the main app without a prefix
app = FastAPI(title="OSINT Threat Monitoring Platform", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Auth router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    user_data: UserCreate,
    auth_db: Session = Depends(get_auth_db)
):
    """Register a new user account"""
    
    # Check if user already exists
    existing_user = auth_db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    strength_check = AuthService.validate_password_strength(user_data.password)
    if strength_check["strength"] == "very_weak":
        raise HTTPException(
            status_code=400, 
            detail="Password is too weak. Please include uppercase, lowercase, and numbers."
        )
    
    # Create new user
    hashed_password = AuthService.get_password_hash(user_data.password)
    
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=True,  # Auto-verify for demo
        subscription_tier="free",
        subscription_status="active"
    )
    
    auth_db.add(new_user)
    auth_db.commit()
    auth_db.refresh(new_user)
    
    return new_user

@auth_router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: UserLogin,
    auth_db: Session = Depends(get_auth_db)
):
    """Authenticate user and return access token"""
    
    # Fetch user from database
    user = auth_db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not AuthService.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    
    # Reset daily quick scan counter if it's a new day
    today = datetime.utcnow().date()
    if user.last_login and user.last_login.date() != today:
        user.quick_scans_today = 0
    
    auth_db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=1440)  # 24 hours
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email, "tier": user.subscription_tier},
        expires_delta=access_token_expires
    )
    
    token_response = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=1440 * 60,  # 24 hours in seconds
        user_id=user.id
    )
    
    return LoginResponse(
        user=user,
        token=token_response,
        message="Login successful"
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user

@auth_router.get("/subscription-info")
async def get_subscription_info(current_user: User = Depends(get_current_active_user)):
    """Get detailed subscription information"""
    return SubscriptionService.get_user_subscription_info(current_user)

# Payment router
payment_router = APIRouter(prefix="/payments", tags=["Payments"])

@payment_router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    auth_db: Session = Depends(get_auth_db)
):
    """Create Stripe checkout session"""
    
    # Validate plan
    if checkout_data.plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    # Get plan pricing
    price_ids = {
        "pro": "price_1S8SalSLY9CgDyaNVEkzzCQz",
        "enterprise": "price_1S8SbbSLY9CgDyaNlfMhrvhm"
    }
    
    price_amounts = {
        "pro": 9.00,
        "enterprise": 29.00
    }
    
    stripe_price_id = price_ids[checkout_data.plan]
    amount = price_amounts[checkout_data.plan]
    
    # Set Stripe API key
    stripe.api_key = os.environ.get('STRIPE_API_KEY')
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',  # Use subscription mode for recurring payments
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
            customer_email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "subscription_tier": checkout_data.plan,
                "amount": str(amount)
            }
        )
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            user_id=current_user.id,
            session_id=checkout_session.id,
            stripe_price_id=stripe_price_id,
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            payment_status="pending",
            transaction_status="initiated",
            subscription_tier=checkout_data.plan,
            transaction_metadata=json.dumps({
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "subscription_tier": checkout_data.plan,
                "amount": str(amount)
            })
        )
        
        auth_db.add(transaction)
        auth_db.commit()
        
        return CheckoutResponse(
            url=checkout_session.url,
            session_id=checkout_session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@payment_router.get("/status/{session_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    auth_db: Session = Depends(get_auth_db)
):
    """Get payment status for a checkout session"""
    
    # Find transaction
    transaction = auth_db.query(PaymentTransaction).filter(
        PaymentTransaction.session_id == session_id,
        PaymentTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Set Stripe API key
    stripe.api_key = os.environ.get('STRIPE_API_KEY')
    
    try:
        # Get checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Update transaction status based on payment status
        payment_status = "paid" if checkout_session.payment_status == "paid" else "pending"
        transaction.payment_status = payment_status
        
        if payment_status == "paid" and transaction.transaction_status != "completed":
            # Upgrade user subscription
            SubscriptionService.upgrade_user_subscription(
                auth_db,
                current_user,
                transaction.subscription_tier,
                checkout_session.customer
            )
            transaction.transaction_status = "completed"
            
        auth_db.commit()
        
        return PaymentStatusResponse(
            status=checkout_session.status,
            payment_status=payment_status,
            subscription_tier=transaction.subscription_tier if payment_status == "paid" else None,
            message="Payment completed successfully" if payment_status == "paid" else "Payment pending"
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return PaymentStatusResponse(
            status="error",
            payment_status="unknown",
            subscription_tier=None,
            message=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Payment status error: {str(e)}")
        return PaymentStatusResponse(
            status="error",
            payment_status="unknown",
            subscription_tier=None,
            message=f"Error checking payment status: {str(e)}"
        )

# Webhook endpoint removed - using direct payment status checking instead

# Enhanced subscription endpoint with tier checking
@api_router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    auth_db: Session = Depends(get_auth_db)
):
    """Create monitoring subscription with tier limits"""
    
    # Check if user can create more subscriptions
    can_create_check = SubscriptionService.can_create_monitoring_subscription(current_user)
    if not can_create_check["can_create"]:
        raise HTTPException(
            status_code=403,
            detail=f"Subscription limit reached. Your {current_user.subscription_tier} plan allows {can_create_check['terms_allowed']} monitoring terms. Upgrade to monitor more threats."
        )
    
    # Create subscription
    subscription = SubscriptionService.create_monitoring_subscription(
        auth_db,
        current_user,
        subscription_data.term
    )
    
    if not subscription:
        raise HTTPException(status_code=400, detail="Could not create subscription")
    
    return subscription

# QuickScanRequest model
class QuickScanRequest(BaseModel):
    query: str

# Enhanced quick scan with Google Custom Search API and tier checking
@api_router.post("/quick-scan")
async def quick_scan(
    scan_request: QuickScanRequest,
    current_user: User = Depends(get_current_active_user),
    auth_db: Session = Depends(get_auth_db)
):
    """Perform enhanced quick scan with real Google search results and AI analysis"""
    
    # Check if user can perform quick scan
    can_scan_check = SubscriptionService.can_perform_quick_scan(current_user)
    if not can_scan_check["can_scan"]:
        raise HTTPException(
            status_code=403,
            detail=f"Daily scan limit reached. Your {current_user.subscription_tier} plan allows {can_scan_check['scans_allowed']} scans per day. Upgrade for more scans."
        )
    
    # Increment usage
    SubscriptionService.increment_quick_scan_usage(auth_db, current_user)
    
    query = scan_request.query
    logger.info(f"Starting enhanced quick scan for user {current_user.email}: query='{query}'")
    
    try:
        # Import and initialize Google Custom Search client
        from google_search_client import GoogleCustomSearchClient
        search_client = GoogleCustomSearchClient()
        
        # Phase 1: Search Google for recent news articles
        logger.info("Phase 1: Searching Google for recent news articles...")
        search_results = await search_client.search_news_articles(
            query=query,
            num_results=10,
            days_back=7
        )
        
        # Extract structured article data
        discovered_articles = search_client.extract_article_data(search_results)
        
        if not discovered_articles:
            logger.warning("No articles found in Google search results")
            raise HTTPException(
                status_code=404, 
                detail="No recent news articles found for this query. Try a different search term."
            )
        
        logger.info(f"Found {len(discovered_articles)} articles from Google search")
        
        # Phase 2: Prepare content for LLM analysis
        logger.info("Phase 2: Preparing content for AI analysis...")
        search_content = f"Query: {query}\n\nRecent News Articles (Past Week):\n\n"
        sources = []
        discovered_links = []
        
        for i, article in enumerate(discovered_articles, 1):
            search_content += f"{i}. {article['title']} ({article['published_date']})\n"
            search_content += f"   Source: {article['source']}\n"
            search_content += f"   {article['snippet']}\n\n"
            
            sources.append(f"{article['title']} - {article['url']}")
            
            # Add to discovered links with enhanced data
            discovered_links.append({
                "title": article['title'],
                "url": article['url'],
                "snippet": article['snippet'],
                "date": article['published_date'],
                "severity": article['severity'],
                "source": article['source']
            })
        
        # Phase 3: AI-powered analysis using latest GPT model
        logger.info("Phase 3: Generating AI-powered analysis...")
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"quick-scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            system_message="You are an expert cybersecurity threat intelligence analyst. Analyze recent news articles and provide actionable intelligence summaries for security professionals. Focus on identifying real threats, vulnerabilities, and security implications."
        ).with_model("openai", "gpt-4o")  # Using latest GPT model
        
        # Create enhanced analysis prompt
        analysis_prompt = f"""Analyze the following recent news articles related to "{query}" and provide a comprehensive threat intelligence report:

ARTICLES TO ANALYZE:
{search_content}

Please provide:

1. EXECUTIVE SUMMARY (2-3 sentences highlighting the most critical findings)
2. KEY THREATS IDENTIFIED (3-5 specific, actionable threats)
3. SECURITY IMPLICATIONS (potential impact on organizations)
4. ACTIONABLE RECOMMENDATIONS (immediate steps security teams should take)

Format your response as:

EXECUTIVE SUMMARY:
[2-3 sentence summary of the most critical threat landscape findings]

KEY THREATS:
• [Specific threat 1 with details]
• [Specific threat 2 with details]
• [Specific threat 3 with details]

SECURITY IMPLICATIONS:
• [Impact 1]
• [Impact 2]

RECOMMENDATIONS:
• [Immediate action 1]
• [Immediate action 2]
• [Immediate action 3]

Focus on real, actionable intelligence that security professionals can use immediately."""

        user_message = UserMessage(text=analysis_prompt)
        
        # Get AI analysis
        llm_response = await chat.send_message(user_message)
        
        # Extract key threats from the response
        key_threats = []
        lines = llm_response.split('\n')
        in_threats_section = False
        
        for line in lines:
            if 'KEY THREATS:' in line.upper():
                in_threats_section = True
                continue
            elif 'SECURITY IMPLICATIONS:' in line.upper() or 'RECOMMENDATIONS:' in line.upper():
                in_threats_section = False
                continue
            elif in_threats_section and line.strip().startswith('•'):
                threat = line.strip().replace('•', '').strip()
                if threat:
                    key_threats.append(threat)
        
        # Fallback if no threats extracted
        if not key_threats:
            key_threats = [
                f"Emerging {query}-related security incidents require monitoring",
                f"Potential attack vectors identified in recent reports",
                f"Organizations should review {query} security controls"
            ]
        
        logger.info("Enhanced quick scan completed successfully")
        
        return {
            "query": query,
            "summary": llm_response,
            "key_threats": key_threats[:5],
            "sources": sources,
            "discovered_links": discovered_links,
            "search_metadata": {
                "total_results": search_results.get("searchInformation", {}).get("totalResults", "0"),
                "search_time": search_results.get("searchInformation", {}).get("searchTime", 0),
                "articles_analyzed": len(discovered_articles)
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "userEmail": current_user.email,
            "scans_remaining": can_scan_check["scans_allowed"] - can_scan_check["scans_used"] - 1,
            "scan_type": "enhanced_google_search"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like quota exceeded)
        raise
    except Exception as e:
        logger.error(f"Enhanced quick scan failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick scan failed: {str(e)}"
        )

# Original models for existing functionality

class IntelligenceMatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    incident_title: str
    source: str
    date: datetime
    severity: str
    user_email: EmailStr

class UserStatus(BaseModel):
    subscriptions: List[SubscriptionResponse]
    intelligence_matches: List[IntelligenceMatch]

# Mock intelligence data
mock_intelligence_data = [
    {
        "term": "ATM fraud",
        "incident_title": "Sophisticated ATM Skimming Operation Discovered in Eastern Europe",
        "source": "CyberSecurity News",
        "date": datetime(2024, 12, 15, 14, 30, tzinfo=timezone.utc),
        "severity": "High"
    },
    {
        "term": "POS malware", 
        "incident_title": "New POS Malware Variant Targets Retail Chains",
        "source": "Threat Intelligence Report",
        "date": datetime(2024, 12, 14, 9, 15, tzinfo=timezone.utc),
        "severity": "Critical"
    },
    {
        "term": "NCR",
        "incident_title": "NCR Systems Vulnerability Patched After Security Advisory",
        "source": "Security Advisory",
        "date": datetime(2024, 12, 13, 16, 45, tzinfo=timezone.utc),
        "severity": "Medium"
    },
    {
        "term": "banking malware",
        "incident_title": "Emerging Banking Trojan Targets Mobile Banking Apps",
        "source": "Malware Analysis",
        "date": datetime(2024, 12, 12, 11, 20, tzinfo=timezone.utc),
        "severity": "High"
    },
    {
        "term": "ransomware",
        "incident_title": "Healthcare Sector Hit by New Ransomware Campaign",
        "source": "Industry Alert",
        "date": datetime(2024, 12, 11, 8, 30, tzinfo=timezone.utc),
        "severity": "Critical"
    }
]

@api_router.get("/status", response_model=UserStatus)
async def get_status(
    email: str = Query(..., description="User email address"),
    current_user: User = Depends(get_current_active_user),
    auth_db: Session = Depends(get_auth_db)
):
    """Get user's subscriptions and intelligence matches"""
    
    # Verify email matches current user
    if email != current_user.email:
        raise HTTPException(status_code=403, detail="Cannot access other user's data")
    
    # Get user subscriptions
    subscriptions = auth_db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.is_active == True
    ).all()
    
    # Get matching intelligence based on user's subscribed terms
    user_terms = [sub.term.lower() for sub in subscriptions]
    intelligence_matches = []
    
    for mock_data in mock_intelligence_data:
        for term in user_terms:
            if term in mock_data["term"].lower() or term in mock_data["incident_title"].lower():
                match = IntelligenceMatch(
                    term=mock_data["term"],
                    incident_title=mock_data["incident_title"],
                    source=mock_data["source"],
                    date=mock_data["date"],
                    severity=mock_data["severity"],
                    user_email=email
                )
                intelligence_matches.append(match)
                break
    
    return UserStatus(
        subscriptions=subscriptions,
        intelligence_matches=intelligence_matches
    )

@api_router.get("/health/google-search")
async def google_search_health():
    """Health check for Google Custom Search API integration"""
    try:
        from google_search_client import GoogleCustomSearchClient
        search_client = GoogleCustomSearchClient()
        health_status = await search_client.health_check()
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(payment_router)
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "OSINT Threat Monitoring Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@api_router.get("/health/google-search")
async def google_search_health():
    """Health check for Google Custom Search API integration"""
    try:
        from google_search_client import GoogleCustomSearchClient
        search_client = GoogleCustomSearchClient()
        health_status = await search_client.health_check()
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }