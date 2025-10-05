from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Request, BackgroundTasks
from fastapi.responses import FileResponse
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
import time

# Authentication and Payment imports
from database import Base, get_auth_db, engine, get_mongodb
from auth_models import User, UserSubscription, PaymentTransaction
from auth_service import AuthService
from auth_service_mongodb import MongoDBAuthService
from auth_schemas import *
from subscription_service import SubscriptionService, SUBSCRIPTION_TIERS
from mongodb_models import UserModel
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    from llm_fallback import LlmChat, UserMessage
    EMERGENT_AVAILABLE = False
    print("⚠️ Using LLM fallback - emergentintegrations not available")
from cost_tracker import CostTracker
from analytics_service import analytics
import stripe
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database setup (using get_mongodb() from database.py for consistent connection management)
# This is imported from database module - no need to create separate connection

# Create all tables
Base.metadata.create_all(bind=engine)

# Security
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserModel:
    """
    Get current authenticated user from JWT token (MongoDB version)
    
    This replaces SQLAlchemy user lookup with MongoDB
    """
    
    payload = MongoDBAuthService.verify_token(credentials.credentials)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
    
    # Get MongoDB connection
    db = get_mongodb()
    auth_service = MongoDBAuthService(db)
    
    # Get user from MongoDB
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    return user

async def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
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
    user_data: UserCreate
):
    """
    Register a new user account (MongoDB version)
    
    Creates user and default free subscription in MongoDB
    """
    
    try:
        # Get MongoDB connection
        db = get_mongodb()
        auth_service = MongoDBAuthService(db)
        
        # Create user (this handles validation and duplicate check)
        new_user = await auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        # Track user registration analytics - Key Metric #1: Signups
        try:
            analytics.track_user_signup(
                user_id=new_user.id,
                email=new_user.email,
                plan_type='free',
                signup_method='email'
            )
        except Exception as e:
            logger.warning(f"Failed to track signup analytics: {e}")
        
        logger.info(f"✅ User registered: {new_user.email}")
        
        # Return user info (excluding sensitive data like password)
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            is_verified=True,
            created_at=new_user.created_at,
            last_login=new_user.last_login,
            subscription_tier="free",
            subscription_status="active",
            monitoring_terms_count=0,
            quick_scans_today=new_user.quick_scans_today
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@auth_router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: UserLogin
):
    """
    Authenticate user and return access token (MongoDB version)
    """
    
    try:
        # Get MongoDB connection
        db = get_mongodb()
        auth_service = MongoDBAuthService(db)
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is deactivated")
        
        # Track user login analytics
        try:
            analytics.track_user_login(
                user_id=user.id,
                email=user.email,
                login_method='password'
            )
        except Exception as e:
            logger.warning(f"Failed to track login analytics: {e}")
        
        # Create access token
        access_token_expires = timedelta(minutes=1440)  # 24 hours
        access_token = MongoDBAuthService.create_access_token(
            data={"sub": str(user.id), "email": user.email, "tier": "free"},
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ User logged in: {user.email}")
        
        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=1440 * 60,  # 24 hours in seconds
            user_id=user.id
        )
        
        # Create UserResponse from UserModel
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=True,
            created_at=user.created_at,
            last_login=user.last_login,
            subscription_tier="free",
            subscription_status="active",
            monitoring_terms_count=0,
            quick_scans_today=user.quick_scans_today
        )
        
        return LoginResponse(
            user=user_response,
            token=token_response,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserModel = Depends(get_current_active_user)):
    """Get current user profile (MongoDB version)"""
    # Return user info (excluding sensitive data like password)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=True,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        subscription_tier="free",
        subscription_status="active",
        monitoring_terms_count=0,
        quick_scans_today=current_user.quick_scans_today
    )

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
    
    # Track Quick Scan initiated - Key Metric #2: Searches per user
    scan_start_time = time.time()
    try:
        analytics.track_quick_scan_initiated(
            user_id=current_user.id,
            query=query,
            user_plan=current_user.subscription_tier or 'free',
            scans_remaining=can_scan_check["scans_allowed"] - can_scan_check["scans_used"]
        )
    except Exception as e:
        logger.warning(f"Failed to track scan initiation analytics: {e}")
    
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
        
        # Initialize cost tracker for API usage tracking
        cost_tracker = CostTracker()
        
        # Calculate Google API costs
        api_usage = search_results.get('api_usage', {})
        google_usage = cost_tracker.calculate_google_api_cost(
            queries_made=api_usage.get('queries_made', 1),
            total_results_returned=api_usage.get('results_returned', 0),
            api_calls_count=api_usage.get('api_calls_made', 1)
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
        
        # Get AI analysis with usage tracking
        llm_response = await chat.send_message(user_message)
        
        # Get token usage from the chat session for cost tracking
        # Note: This is a placeholder - actual token tracking depends on Emergent LLM implementation
        # We'll estimate tokens for now and update when precise tracking is available
        input_text = analysis_prompt
        output_text = llm_response
        estimated_input_tokens = len(input_text.split()) * 1.3  # Rough token estimation
        estimated_output_tokens = len(output_text.split()) * 1.3
        
        # Calculate LLM costs (cost_tracker already initialized above)
        llm_usage = cost_tracker.calculate_llm_cost(
            model="gpt-4o",
            input_tokens=int(estimated_input_tokens),
            output_tokens=int(estimated_output_tokens)
        )
        
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
        
        # Generate comprehensive cost summary
        cost_summary = cost_tracker.get_cost_summary(llm_usage, google_usage)
        
        # Track Quick Scan completion analytics
        scan_duration = time.time() - scan_start_time
        try:
            analytics.track_quick_scan_completed(
                user_id=current_user.id,
                query=query,
                scan_duration=scan_duration,
                articles_found=len(discovered_articles),
                llm_tokens_used=llm_usage.total_tokens,
                total_cost=float(cost_summary.get('total_cost', '$0.00').replace('$', '')),
                success=True
            )
        except Exception as e:
            logger.warning(f"Failed to track scan completion analytics: {e}")
        
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
            "cost_breakdown": cost_summary,
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

# PDF Report Generation endpoints
@api_router.post("/generate-report")
async def generate_pdf_report(
    scan_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Generate PDF report from Quick Scan results"""
    try:
        from pdf_generator import ThreatWatchPDFGenerator
        
        # Generate PDF report
        pdf_start_time = time.time()
        pdf_generator = ThreatWatchPDFGenerator()
        pdf_path = pdf_generator.generate_report(scan_data)
        
        # Get user-friendly filename
        public_filename = pdf_generator.get_public_filename(scan_data)
        
        # Track PDF generation analytics
        try:
            pdf_size_kb = Path(pdf_path).stat().st_size / 1024  # Size in KB
            generation_time = time.time() - pdf_start_time
            
            analytics.track_pdf_report_generated(
                user_id=current_user.id,
                query=scan_data.get('query', 'unknown'),
                report_size_kb=pdf_size_kb,
                generation_time=generation_time
            )
        except Exception as e:
            logger.warning(f"Failed to track PDF generation analytics: {e}")
        
        return {
            "status": "success",
            "message": "PDF report generated successfully",
            "download_url": f"/api/download-report/{Path(pdf_path).stem}",
            "filename": public_filename,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )

@api_router.get("/download-report/{report_id}")
async def download_pdf_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download generated PDF report"""
    try:
        from pdf_generator import ThreatWatchPDFGenerator
        
        # Initialize PDF generator to get cache directory
        pdf_generator = ThreatWatchPDFGenerator()
        pdf_path = pdf_generator.cache_dir / f"{report_id}.pdf"
        
        # Check if file exists and is valid
        if not pdf_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Report not found or has expired"
            )
        
        # Check if file is recent (within 48 hours)
        if not pdf_generator._is_cache_valid(pdf_path):
            # Clean up expired file
            pdf_path.unlink()
            raise HTTPException(
                status_code=404,
                detail="Report has expired. Please generate a new report."
            )
        
        # Generate appropriate filename for download
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"ThreatWatch_Report_{timestamp}.pdf"
        
        # Track PDF download analytics - Key Metric #3: Report downloads
        try:
            # Extract query from filename for analytics (format: ThreatWatch_Report_query_date.pdf)
            query_match = filename.replace('ThreatWatch_Report_', '').split('_')
            query_for_analytics = '_'.join(query_match[:-1]) if len(query_match) > 1 else 'unknown'
            
            analytics.track_pdf_report_downloaded(
                user_id=current_user.id,
                query=query_for_analytics,
                report_id=report_id,
                download_method='browser'
            )
        except Exception as e:
            logger.warning(f"Failed to track PDF download analytics: {e}")
        
        return FileResponse(
            path=str(pdf_path),
            filename=filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF download failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download PDF report: {str(e)}"
        )

@api_router.delete("/cleanup-reports")
async def cleanup_old_reports(
    current_user: User = Depends(get_current_active_user)
):
    """Cleanup old PDF reports (Admin only or background task)"""
    try:
        from pdf_generator import ThreatWatchPDFGenerator
        
        pdf_generator = ThreatWatchPDFGenerator()
        pdf_generator.cleanup_old_reports()
        
        return {
            "status": "success",
            "message": "Old reports cleaned up successfully"
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup reports: {str(e)}"
        )

# ============================================================================
# MONITORING ENDPOINTS - Phase 1
# ============================================================================

# Import monitoring services
from monitor_service import MonitorService
from alert_service import AlertService
from monitor_engine import MonitorEngine
from mongodb_models import (
    CreateMonitorRequest,
    UpdateMonitorRequest,
    MonitorResponse,
    AlertResponse,
    AlertStatus,
    MonitorModel
)
from celery_tasks import scan_monitor_task
from celery_app import check_celery_health, check_redis_health

# Create monitoring router
monitoring_router = APIRouter(prefix="/monitors", tags=["Monitoring"])

@monitoring_router.post("", response_model=MonitorResponse, status_code=201)
async def create_monitor(
    request: CreateMonitorRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new monitoring term
    
    This sets up automatic scanning for specific threats.
    Example: Monitor "ransomware attacks healthcare" to get alerts when new threats are detected.
    """
    try:
        monitor_service = MonitorService(mongo_db)
        
        # Check monitor limit based on subscription tier
        current_count = await monitor_service.get_monitor_count(str(current_user.id))
        tier_limits = {
            'free': 1,
            'professional': 5,
            'enterprise': 50,
            'enterprise_plus': 999999
        }
        
        user_tier = getattr(current_user, 'subscription_tier', 'free')
        limit = tier_limits.get(user_tier, 1)
        
        if current_count >= limit:
            raise HTTPException(
                status_code=403,
                detail=f"Monitor limit reached for {user_tier} tier. Upgrade to create more monitors."
            )
        
        # Create monitor
        monitor = await monitor_service.create_monitor(
            user_id=str(current_user.id),
            request=request
        )
        
        logger.info(f"✅ Monitor created: {monitor.id} by user {current_user.email}")
        
        return monitor_service.to_response(monitor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create monitor: {str(e)}")


@monitoring_router.get("", response_model=List[MonitorResponse])
async def list_monitors(
    active_only: bool = Query(False, description="Only return active monitors"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all monitors for the current user
    """
    try:
        monitor_service = MonitorService(mongo_db)
        
        monitors = await monitor_service.list_user_monitors(
            user_id=str(current_user.id),
            active_only=active_only,
            skip=skip,
            limit=limit
        )
        
        return [monitor_service.to_response(m) for m in monitors]
        
    except Exception as e:
        logger.error(f"❌ Failed to list monitors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list monitors: {str(e)}")


@monitoring_router.get("/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(
    monitor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific monitor
    """
    try:
        monitor_service = MonitorService(mongo_db)
        
        monitor = await monitor_service.get_monitor(monitor_id, str(current_user.id))
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        return monitor_service.to_response(monitor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitor: {str(e)}")


@monitoring_router.put("/{monitor_id}", response_model=MonitorResponse)
async def update_monitor(
    monitor_id: str,
    request: UpdateMonitorRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update monitor settings
    """
    try:
        monitor_service = MonitorService(mongo_db)
        
        updated_monitor = await monitor_service.update_monitor(
            monitor_id=monitor_id,
            user_id=str(current_user.id),
            request=request
        )
        
        if not updated_monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        logger.info(f"✅ Monitor updated: {monitor_id}")
        
        return monitor_service.to_response(updated_monitor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update monitor: {str(e)}")


@monitoring_router.delete("/{monitor_id}", status_code=204)
async def delete_monitor(
    monitor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a monitor
    """
    try:
        monitor_service = MonitorService(mongo_db)
        
        deleted = await monitor_service.delete_monitor(monitor_id, str(current_user.id))
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        logger.info(f"✅ Monitor deleted: {monitor_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete monitor: {str(e)}")


@monitoring_router.post("/{monitor_id}/test")
async def test_monitor(
    monitor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Test a monitor by running an immediate scan
    
    This triggers a manual scan without waiting for the scheduled time.
    Useful for testing monitor configuration.
    """
    try:
        monitor_service = MonitorService(mongo_db)
        
        # Get monitor
        monitor = await monitor_service.get_monitor(monitor_id, str(current_user.id))
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Trigger scan task
        task = scan_monitor_task.delay(monitor_id)
        
        logger.info(f"✅ Test scan triggered for monitor: {monitor_id} (Task ID: {task.id})")
        
        return {
            "status": "success",
            "message": "Scan triggered successfully",
            "monitor_id": monitor_id,
            "task_id": task.id,
            "note": "Scan is running in the background. Check alerts in a few minutes."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to test monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test monitor: {str(e)}")


@monitoring_router.get("/{monitor_id}/alerts", response_model=List[AlertResponse])
async def get_monitor_alerts(
    monitor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get alerts for a specific monitor
    """
    try:
        # Verify monitor belongs to user
        monitor_service = MonitorService(mongo_db)
        monitor = await monitor_service.get_monitor(monitor_id, str(current_user.id))
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Get alerts
        alert_service = AlertService(mongo_db)
        alerts = await alert_service.list_user_alerts(
            user_id=str(current_user.id),
            monitor_id=monitor_id,
            skip=skip,
            limit=limit
        )
        
        return [alert_service.to_response(a) for a in alerts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get monitor alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================

alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])

@alerts_router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all alerts for the current user
    """
    try:
        alert_service = AlertService(mongo_db)
        
        # Parse filters
        status_filter = AlertStatus(status) if status else None
        from mongodb_models import SeverityLevel
        severity_filter = SeverityLevel(severity) if severity else None
        
        alerts = await alert_service.list_user_alerts(
            user_id=str(current_user.id),
            status=status_filter,
            severity=severity_filter,
            skip=skip,
            limit=limit
        )
        
        return [alert_service.to_response(a) for a in alerts]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to list alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list alerts: {str(e)}")


@alerts_router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific alert
    """
    try:
        alert_service = AlertService(mongo_db)
        
        alert = await alert_service.get_alert(alert_id, str(current_user.id))
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return alert_service.to_response(alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")


@alerts_router.put("/{alert_id}/status")
async def update_alert_status(
    alert_id: str,
    status: str = Query(..., description="New status (new, acknowledged, resolved, false_positive)"),
    feedback: Optional[str] = Query(None, description="Optional user feedback"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update alert status
    
    Statuses:
    - acknowledged: User has seen the alert
    - resolved: Threat has been addressed
    - false_positive: Not a real threat
    """
    try:
        alert_service = AlertService(mongo_db)
        
        # Parse status
        try:
            new_status = AlertStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in AlertStatus]}"
            )
        
        # Update alert
        updated_alert = await alert_service.update_alert_status(
            alert_id=alert_id,
            user_id=str(current_user.id),
            new_status=new_status,
            user_feedback=feedback
        )
        
        if not updated_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        logger.info(f"✅ Alert {alert_id} status updated to {status}")
        
        return alert_service.to_response(updated_alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update alert status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update alert: {str(e)}")


@alerts_router.get("/statistics/summary")
async def get_alert_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get alert statistics for the current user
    """
    try:
        alert_service = AlertService(mongo_db)
        
        stats = await alert_service.get_alert_statistics(str(current_user.id))
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get alert statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

health_router = APIRouter(prefix="/health", tags=["Health"])

@health_router.get("/celery")
async def celery_health():
    """Check Celery worker status"""
    try:
        health = check_celery_health()
        return health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@health_router.get("/redis")
async def redis_health():
    """Check Redis connection status"""
    try:
        health = check_redis_health()
        return health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@health_router.get("/mongodb")
async def mongodb_health():
    """Check MongoDB connection status"""
    try:
        from database import check_mongodb_connection
        connected = await check_mongodb_connection()
        return {
            "status": "healthy" if connected else "unhealthy",
            "connected": connected
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@health_router.get("/system")
async def system_health():
    """
    Complete system health check
    
    Checks:
    - MongoDB connection
    - Redis connection
    - Celery workers
    - Recent monitoring activity
    """
    try:
        from database import check_mongodb_connection, get_collection_stats
        
        # Check MongoDB
        mongo_ok = await check_mongodb_connection()
        
        # Check Redis
        redis_health = check_redis_health()
        redis_ok = redis_health['status'] == 'healthy'
        
        # Check Celery
        celery_health = check_celery_health()
        celery_ok = celery_health['worker_count'] > 0
        
        # Get collection stats
        stats = await get_collection_stats()
        
        overall_status = "healthy" if (mongo_ok and redis_ok) else "degraded"
        if not mongo_ok:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "mongodb": {
                "status": "healthy" if mongo_ok else "unhealthy",
                "collections": stats
            },
            "redis": redis_health,
            "celery": celery_health,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Include all routers
api_router.include_router(auth_router)
api_router.include_router(payment_router)
api_router.include_router(monitoring_router)
api_router.include_router(alerts_router)
api_router.include_router(health_router)
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

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        logger.info("🚀 Application starting...")
        
        # Initialize MongoDB indexes
        from database import init_mongodb_indexes
        await init_mongodb_indexes()
        
        logger.info("✅ Application startup complete!")
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("🛑 Application shutting down...")
        
        # Close MongoDB connection
        from database import close_mongodb
        await close_mongodb()
        
        logger.info("✅ Application shutdown complete!")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")


@app.get("/")
async def root():
    return {"message": "OSINT Threat Monitoring Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}