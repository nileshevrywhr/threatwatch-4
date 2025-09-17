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

# Enhanced quick scan with tier checking
@api_router.post("/quick-scan")
async def quick_scan(
    scan_request: QuickScanRequest,
    current_user: User = Depends(get_current_active_user),
    auth_db: Session = Depends(get_auth_db)
):
    """Perform quick scan with tier limits"""
    
    # Check if user can perform quick scan
    can_scan_check = SubscriptionService.can_perform_quick_scan(current_user)
    if not can_scan_check["can_scan"]:
        raise HTTPException(
            status_code=403,
            detail=f"Daily scan limit reached. Your {current_user.subscription_tier} plan allows {can_scan_check['scans_allowed']} scans per day. Upgrade for more scans."
        )
    
    # Increment usage
    SubscriptionService.increment_quick_scan_usage(auth_db, current_user)
    
    # Perform the actual scan (existing logic)
    query = scan_request.query
    
    # Mock search results with actual discoverable links
    mock_search_results = [
        {
            "title": f"Recent {query} Security Incident Analysis",
            "url": "https://www.cisa.gov/news-events/cybersecurity-advisories",
            "snippet": f"A comprehensive analysis of recent {query} incidents shows increasing sophistication in attack vectors. Security researchers have identified new patterns in threat actor behavior, suggesting coordinated campaigns targeting financial institutions and critical infrastructure.",
            "date": "2024-12-15",
            "severity": "Critical"
        },
        {
            "title": f"Industry Alert: {query} Threat Landscape Update",
            "url": "https://www.us-cert.gov/ncas/alerts",
            "snippet": f"The latest threat intelligence report indicates a 40% increase in {query}-related attacks over the past week. Organizations are advised to implement enhanced monitoring and update their security protocols immediately.",
            "date": "2024-12-14",
            "severity": "High"
        },
        {
            "title": f"Emergency Patch Released for {query} Vulnerability",
            "url": "https://nvd.nist.gov/vuln/search",
            "snippet": f"Critical security vulnerability discovered in systems vulnerable to {query} attacks. Emergency patches have been released by major vendors. CVE assigned and exploitation attempts detected in the wild.",
            "date": "2024-12-13",
            "severity": "Critical"
        },
        {
            "title": f"Global {query} Campaign Targets Healthcare Sector",
            "url": "https://www.hhs.gov/about/agencies/asa/ocio/cybersecurity/index.html",
            "snippet": f"A sophisticated {query} campaign has been identified targeting healthcare organizations worldwide. The attack vector utilizes social engineering combined with technical exploits to gain initial access to healthcare networks.",
            "date": "2024-12-12",
            "severity": "High"
        },
        {
            "title": f"New {query} Malware Variant Discovered",
            "url": "https://www.virustotal.com/gui/home/search",
            "snippet": f"Security researchers have identified a new variant of {query} malware with enhanced evasion capabilities. The malware demonstrates advanced persistence mechanisms and anti-analysis techniques.",
            "date": "2024-12-11",
            "severity": "Medium"
        },
        {
            "title": f"{query} IOCs and Threat Indicators Released",
            "url": "https://otx.alienvault.com/browse/global/pulses",
            "snippet": f"New indicators of compromise (IOCs) related to {query} activities have been published. These include file hashes, IP addresses, and domain names associated with recent attack campaigns.",
            "date": "2024-12-10",
            "severity": "Medium"
        },
        {
            "title": f"FBI Warning: {query} Attacks Targeting Small Businesses",
            "url": "https://www.ic3.gov/Home/IndustryAlert",
            "snippet": f"The FBI has issued a warning about increasing {query} attacks specifically targeting small and medium businesses. Attackers are exploiting common vulnerabilities in business applications and weak security practices.",
            "date": "2024-12-09",
            "severity": "High"
        },
        {
            "title": f"Technical Analysis: {query} Attack Chain Breakdown",
            "url": "https://attack.mitre.org/techniques",
            "snippet": f"Detailed technical analysis of the {query} attack chain reveals multi-stage deployment with sophisticated evasion techniques. The analysis includes MITRE ATT&CK framework mappings and detection strategies.",
            "date": "2024-12-08",
            "severity": "Medium"
        }
    ]
    
    # Prepare content for LLM analysis
    search_content = f"Query: {query}\n\nRecent Intelligence Findings:\n\n"
    sources = []
    discovered_links = []
    
    for i, result in enumerate(mock_search_results, 1):
        search_content += f"{i}. {result['title']} ({result['date']})\n"
        search_content += f"   {result['snippet']}\n\n"
        sources.append(f"{result['title']} - {result['url']}")
        
        # Add to discovered links
        discovered_links.append({
            "title": result['title'],
            "url": result['url'],
            "snippet": result['snippet'],
            "date": result['date'],
            "severity": result['severity']
        })
    
    # Initialize LLM chat
    chat = LlmChat(
        api_key=os.environ.get('EMERGENT_LLM_KEY'),
        session_id=f"quick-scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        system_message="You are a cybersecurity threat intelligence analyst. Your role is to analyze recent security incidents and provide actionable intelligence summaries for security professionals."
    ).with_model("openai", "gpt-4o-mini")
    
    # Create analysis prompt
    analysis_prompt = f"""Analyze the following recent cybersecurity intelligence related to "{query}" and provide:

1. A concise executive summary (2-3 sentences)
2. Key threats identified (3-5 specific threats)
3. Actionable recommendations for security teams

Intelligence Data:
{search_content}

Please format your response as:

EXECUTIVE SUMMARY:
[2-3 sentence summary of the threat landscape]

KEY THREATS:
• [Threat 1]
• [Threat 2] 
• [Threat 3]

RECOMMENDATIONS:
• [Actionable recommendation 1]
• [Actionable recommendation 2]
• [Actionable recommendation 3]"""

    user_message = UserMessage(text=analysis_prompt)
    
    # Get LLM analysis
    llm_response = await chat.send_message(user_message)
    
    # Extract key threats from the response
    key_threats = []
    lines = llm_response.split('\n')
    in_threats_section = False
    
    for line in lines:
        if 'KEY THREATS:' in line.upper():
            in_threats_section = True
            continue
        elif 'RECOMMENDATIONS:' in line.upper():
            in_threats_section = False
            continue
        elif in_threats_section and line.strip().startswith('•'):
            threat = line.strip().replace('•', '').strip()
            if threat:
                key_threats.append(threat)
    
    # If no key threats extracted, provide default ones
    if not key_threats:
        key_threats = [
            f"Increased {query} attack sophistication",
            f"Coordinated campaigns targeting critical infrastructure",
            f"New evasion techniques being deployed",
            f"Supply chain attacks incorporating {query} methods"
        ]
    
    return {
        "query": query,
        "summary": llm_response,
        "key_threats": key_threats[:5],  # Limit to 5 threats
        "sources": sources,
        "discovered_links": discovered_links,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "userEmail": current_user.email,
        "scans_remaining": can_scan_check["scans_allowed"] - can_scan_check["scans_used"] - 1
    }

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