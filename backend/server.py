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
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

class QuickScanRequest(BaseModel):
    query: str

class DiscoveredLink(BaseModel):
    title: str
    url: str
    snippet: str
    date: str
    severity: str

class QuickScanResult(BaseModel):
    query: str
    summary: str
    key_threats: List[str]
    sources: List[str]
    discovered_links: List[DiscoveredLink]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

@api_router.post("/quick-scan", response_model=QuickScanResult)
async def quick_scan(scan_request: QuickScanRequest):
    try:
        query = scan_request.query
        
        # Simulate web search results with actual discoverable links
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
            discovered_links.append(DiscoveredLink(
                title=result['title'],
                url=result['url'],
                snippet=result['snippet'],
                date=result['date'],
                severity=result['severity']
            ))
        
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
        
        return QuickScanResult(
            query=query,
            summary=llm_response,
            key_threats=key_threats[:5],  # Limit to 5 threats
            sources=sources,
            discovered_links=discovered_links
        )
        
    except Exception as e:
        logger.error(f"Quick scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick scan failed: {str(e)}")

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