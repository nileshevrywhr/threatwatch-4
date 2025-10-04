"""
MongoDB Models for ThreatWatch
===============================

This file contains all MongoDB model schemas using Pydantic for validation.
Unlike SQLAlchemy (used for SQLite), MongoDB with Motor uses Pydantic models
for data validation before storing in the database.

Key Concepts:
- Pydantic models: Define data structure and validation rules
- UUID: Universal unique identifier - ensures unique IDs across distributed systems
- ISODate: ISO 8601 datetime format for consistency
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============================================================================
# ENUMS - Predefined choices for fields
# ============================================================================

class SubscriptionTier(str, Enum):
    """User subscription tiers with different limits"""
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS = "enterprise_plus"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class MonitorFrequency(str, Enum):
    """How often to scan for threats"""
    HOURLY = "hourly"      # Every hour (Professional+)
    DAILY = "daily"        # Once per day (Free+)
    WEEKLY = "weekly"      # Once per week


class SeverityLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert lifecycle status"""
    NEW = "new"                      # Just created
    ACKNOWLEDGED = "acknowledged"     # User has seen it
    RESOLVED = "resolved"            # Threat addressed
    FALSE_POSITIVE = "false_positive" # Not a real threat


# ============================================================================
# USER MODELS - Authentication and Profile
# ============================================================================

class UserModel(BaseModel):
    """
    User account model - replaces SQLAlchemy User model
    
    Changes from SQLite:
    - id is now string (UUID) instead of UUID object
    - uses datetime objects with timezone awareness
    - MongoDB will use _id field for the id value
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    
    # Quick scan rate limiting
    quick_scans_today: int = 0
    quick_scans_reset_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "quick_scans_today": 2
            }
        }


class UserSubscriptionModel(BaseModel):
    """
    User subscription details
    Links to Stripe for payment processing
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # References UserModel.id
    tier: SubscriptionTier = SubscriptionTier.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Stripe integration fields
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Billing cycle
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "sub-uuid",
                "user_id": "user-uuid",
                "tier": "professional",
                "status": "active"
            }
        }


class PaymentTransactionModel(BaseModel):
    """
    Record of payment transactions
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_id: str
    
    # Payment details
    stripe_payment_intent_id: Optional[str] = None
    amount: float
    currency: str = "usd"
    status: str  # succeeded, failed, pending
    
    # Metadata
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# MONITORING MODELS - Long-term threat monitoring
# ============================================================================

class NotificationSettings(BaseModel):
    """
    How users want to be notified about threats
    """
    email: bool = True
    sms: bool = False
    webhook: Optional[str] = None  # URL for webhook notifications
    
    # Alert priority settings
    immediate_alerts: bool = True   # High/Critical alerts sent immediately
    daily_summary: bool = True      # Daily digest email
    weekly_report: bool = False     # Weekly summary report


class MonitorModel(BaseModel):
    """
    Monitoring Term - Defines what threats to track
    
    Example: Track "ransomware attacks on healthcare" 
    - System will scan Google for relevant news daily
    - Generate alerts when new threats detected
    - Send notifications based on user preferences
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Owner of this monitor
    
    # What to monitor
    term: str = Field(..., min_length=3, max_length=200)  # Main search term
    description: Optional[str] = Field(None, max_length=500)
    keywords: List[str] = Field(default_factory=list)  # Additional keywords
    exclude_keywords: List[str] = Field(default_factory=list)  # Terms to exclude
    
    # Monitoring settings
    frequency: MonitorFrequency = MonitorFrequency.DAILY
    severity_threshold: SeverityLevel = SeverityLevel.MEDIUM  # Only alert for this severity+
    active: bool = True  # Can pause monitoring
    
    # Scheduling info
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_scan: Optional[datetime] = None
    next_scan: Optional[datetime] = None
    
    # Statistics
    scan_count: int = 0
    alert_count: int = 0
    
    # Notification preferences
    notification_settings: NotificationSettings = Field(default_factory=NotificationSettings)
    
    @field_validator('term')
    @classmethod
    def term_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Monitor term cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "monitor-uuid",
                "user_id": "user-uuid",
                "term": "ransomware attacks healthcare",
                "description": "Monitor ransomware targeting healthcare sector",
                "keywords": ["ransomware", "healthcare", "hospital"],
                "frequency": "daily",
                "severity_threshold": "medium",
                "active": True
            }
        }


# ============================================================================
# ALERT MODELS - Detected threats
# ============================================================================

class AlertSource(BaseModel):
    """
    Individual news article or source that triggered an alert
    """
    title: str
    url: str
    domain: str
    published: Optional[datetime] = None
    snippet: Optional[str] = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)  # 0-1 score


class ThreatIndicators(BaseModel):
    """
    Extracted threat intelligence from sources
    """
    attack_vectors: List[str] = Field(default_factory=list)  # phishing, malware, etc.
    affected_sectors: List[str] = Field(default_factory=list)  # healthcare, finance, etc.
    geographical_scope: List[str] = Field(default_factory=list)  # US, EU, global, etc.
    threat_actors: List[str] = Field(default_factory=list)  # APT groups, ransomware names


class AlertModel(BaseModel):
    """
    Alert - A detected threat that matches a monitoring term
    
    Created when scanning finds relevant threat intelligence
    User can acknowledge, resolve, or mark as false positive
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    monitor_id: str  # Which monitor generated this alert
    user_id: str  # Alert owner
    
    # Alert content
    title: str
    summary: str  # AI-generated summary of the threat
    severity: SeverityLevel
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)  # How confident are we?
    
    # Sources
    source_count: int = 0
    sources: List[AlertSource] = Field(default_factory=list)
    
    # Threat intelligence
    threat_indicators: ThreatIndicators = Field(default_factory=ThreatIndicators)
    
    # Alert lifecycle
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AlertStatus = AlertStatus.NEW
    user_feedback: Optional[str] = None
    
    # Notifications
    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None
    
    # PDF report
    pdf_report_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert-uuid",
                "monitor_id": "monitor-uuid",
                "user_id": "user-uuid",
                "title": "New Ransomware Campaign Targets Healthcare",
                "summary": "Multiple hospitals affected...",
                "severity": "high",
                "confidence_score": 0.87,
                "source_count": 15,
                "status": "new"
            }
        }


# ============================================================================
# ALERT HISTORY MODELS - Scan tracking and analytics
# ============================================================================

class APICosts(BaseModel):
    """
    Track API costs for each scan
    """
    google_search_queries: int = 0
    llm_tokens: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    total_cost: float = 0.0


class ScanMetadata(BaseModel):
    """
    Details about how the scan was performed
    """
    query_variations: List[str] = Field(default_factory=list)
    timeframe: str = "last 24 hours"
    sources_scanned: List[str] = Field(default_factory=lambda: ["news", "blogs"])


class AlertHistoryModel(BaseModel):
    """
    Alert History - Record of each monitoring scan
    
    Used for:
    - Analytics: Show scan performance over time
    - Cost tracking: Monitor API usage
    - Debugging: Identify scan issues
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    monitor_id: str  # Which monitor was scanned
    
    # Scan timing
    scan_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scan_duration: float = 0.0  # seconds
    
    # Scan results
    articles_processed: int = 0
    alerts_generated: int = 0
    
    # Cost tracking
    api_costs: APICosts = Field(default_factory=APICosts)
    
    # Scan details
    scan_metadata: ScanMetadata = Field(default_factory=ScanMetadata)
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    success: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "history-uuid",
                "monitor_id": "monitor-uuid",
                "scan_timestamp": "2024-01-15T15:30:00Z",
                "scan_duration": 45.5,
                "articles_processed": 127,
                "alerts_generated": 3,
                "success": True
            }
        }


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class CreateMonitorRequest(BaseModel):
    """Request body for creating a new monitor"""
    term: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)
    frequency: MonitorFrequency = MonitorFrequency.DAILY
    severity_threshold: SeverityLevel = SeverityLevel.MEDIUM
    notification_settings: Optional[NotificationSettings] = None


class UpdateMonitorRequest(BaseModel):
    """Request body for updating a monitor"""
    term: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    frequency: Optional[MonitorFrequency] = None
    severity_threshold: Optional[SeverityLevel] = None
    active: Optional[bool] = None
    notification_settings: Optional[NotificationSettings] = None


class MonitorResponse(BaseModel):
    """API response for monitor operations"""
    id: str
    user_id: str
    term: str
    description: Optional[str]
    frequency: str
    severity_threshold: str
    active: bool
    created_at: datetime
    last_scan: Optional[datetime]
    next_scan: Optional[datetime]
    scan_count: int
    alert_count: int
    notification_settings: NotificationSettings


class AlertResponse(BaseModel):
    """API response for alert operations"""
    id: str
    monitor_id: str
    title: str
    summary: str
    severity: str
    confidence_score: float
    source_count: int
    created_at: datetime
    status: str
    sources: List[AlertSource]
    threat_indicators: ThreatIndicators
