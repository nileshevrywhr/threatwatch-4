from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    email: EmailStr
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubscriptionCreate(BaseModel):
    term: str
    email: EmailStr
    phone: Optional[str] = None

class IntelligenceMatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    incident_title: str
    source: str
    date: datetime
    severity: str
    user_email: EmailStr

class UserStatus(BaseModel):
    subscriptions: List[Subscription]
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

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key in ['created_at', 'date'] and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
    return item

# API Routes
@api_router.get("/")
async def root():
    return {"message": "OSINT Threat Monitoring API"}

@api_router.post("/subscribe", response_model=Subscription)
async def subscribe(subscription_data: SubscriptionCreate):
    try:
        subscription = Subscription(**subscription_data.dict())
        subscription_dict = prepare_for_mongo(subscription.dict())
        
        # Check if user already subscribed to this term
        existing = await db.subscriptions.find_one({
            "email": subscription.email,
            "term": subscription.term
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Already subscribed to this term")
        
        await db.subscriptions.insert_one(subscription_dict)
        return subscription
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/status", response_model=UserStatus)
async def get_status(email: str = Query(..., description="User email address")):
    try:
        # Get user subscriptions
        subscriptions_data = await db.subscriptions.find({"email": email}).to_list(1000)
        subscriptions = [Subscription(**parse_from_mongo(sub)) for sub in subscriptions_data]
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()