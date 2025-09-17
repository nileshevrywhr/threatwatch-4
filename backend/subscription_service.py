from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from auth_models import User, UserSubscription
import uuid

# Subscription tier configurations
SUBSCRIPTION_TIERS = {
    "free": {
        "max_quick_scans_per_day": 3,
        "max_monitoring_terms": 0,
        "features": ["basic_quick_scan"]
    },
    "pro": {
        "max_quick_scans_per_day": 50,
        "max_monitoring_terms": 10,
        "features": ["unlimited_quick_scans", "email_alerts", "basic_monitoring"]
    },
    "enterprise": {
        "max_quick_scans_per_day": 200,
        "max_monitoring_terms": 50,
        "features": ["unlimited_quick_scans", "email_alerts", "sms_alerts", "advanced_monitoring", "priority_support"]
    }
}

class SubscriptionService:
    
    @staticmethod
    def can_perform_quick_scan(user: User) -> Dict[str, Any]:
        """Check if user can perform a quick scan"""
        tier_config = SUBSCRIPTION_TIERS.get(user.subscription_tier, SUBSCRIPTION_TIERS["free"])
        max_scans = tier_config["max_quick_scans_per_day"]
        
        # Reset daily counter if it's a new day
        today = datetime.utcnow().date()
        if user.last_login and user.last_login.date() != today:
            user.quick_scans_today = 0
        
        can_scan = user.quick_scans_today < max_scans
        
        return {
            "can_scan": can_scan,
            "scans_used": user.quick_scans_today,
            "scans_allowed": max_scans,
            "tier": user.subscription_tier
        }
    
    @staticmethod
    def can_create_monitoring_subscription(user: User) -> Dict[str, Any]:
        """Check if user can create a new monitoring subscription"""
        tier_config = SUBSCRIPTION_TIERS.get(user.subscription_tier, SUBSCRIPTION_TIERS["free"])
        max_terms = tier_config["max_monitoring_terms"]
        
        can_create = user.monitoring_terms_count < max_terms
        
        return {
            "can_create": can_create,
            "terms_used": user.monitoring_terms_count,
            "terms_allowed": max_terms,
            "tier": user.subscription_tier
        }
    
    @staticmethod
    def increment_quick_scan_usage(db: Session, user: User) -> User:
        """Increment user's quick scan count"""
        user.quick_scans_today += 1
        db.commit()
        return user
    
    @staticmethod
    def create_monitoring_subscription(
        db: Session, 
        user: User, 
        term: str
    ) -> Optional[UserSubscription]:
        """Create a new monitoring subscription"""
        
        # Check if user can create more subscriptions
        check_result = SubscriptionService.can_create_monitoring_subscription(user)
        if not check_result["can_create"]:
            return None
        
        # Check if subscription already exists
        existing = db.query(UserSubscription).filter(
            UserSubscription.user_id == user.id,
            UserSubscription.term == term,
            UserSubscription.is_active == True
        ).first()
        
        if existing:
            return existing
        
        # Create new subscription
        subscription = UserSubscription(
            user_id=user.id,
            term=term
        )
        
        db.add(subscription)
        
        # Update user's monitoring terms count
        user.monitoring_terms_count += 1
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def upgrade_user_subscription(
        db: Session,
        user: User,
        new_tier: str,
        stripe_customer_id: Optional[str] = None
    ) -> User:
        """Upgrade user's subscription tier"""
        
        if new_tier not in SUBSCRIPTION_TIERS:
            raise ValueError(f"Invalid subscription tier: {new_tier}")
        
        user.subscription_tier = new_tier
        user.subscription_status = "active"
        
        if stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
        
        # Set subscription period (monthly)
        user.current_period_end = datetime.utcnow() + timedelta(days=30)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_tier_features(tier: str) -> Dict[str, Any]:
        """Get features for a subscription tier"""
        return SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])
    
    @staticmethod
    def get_user_subscription_info(user: User) -> Dict[str, Any]:
        """Get comprehensive subscription information for user"""
        tier_config = SUBSCRIPTION_TIERS.get(user.subscription_tier, SUBSCRIPTION_TIERS["free"])
        
        return {
            "tier": user.subscription_tier,
            "status": user.subscription_status,
            "features": tier_config["features"],
            "limits": {
                "quick_scans_per_day": tier_config["max_quick_scans_per_day"],
                "monitoring_terms": tier_config["max_monitoring_terms"]
            },
            "usage": {
                "quick_scans_today": user.quick_scans_today,
                "monitoring_terms_count": user.monitoring_terms_count
            },
            "current_period_end": user.current_period_end,
            "can_quick_scan": SubscriptionService.can_perform_quick_scan(user)["can_scan"],
            "can_create_monitoring": SubscriptionService.can_create_monitoring_subscription(user)["can_create"]
        }