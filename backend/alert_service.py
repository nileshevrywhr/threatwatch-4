"""
Alert Service - Manage Threat Alerts
====================================

This service handles alert lifecycle management.

What is an Alert?
----------------
An alert is a detected threat that matches a monitoring term.
Generated when scanning finds relevant cybersecurity news.

Alert Lifecycle:
--------------
NEW → ACKNOWLEDGED → RESOLVED (or FALSE_POSITIVE)

Operations:
----------
- Create alerts from scan results
- List user's alerts
- Update alert status
- Get alert statistics
- Cleanup old alerts
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from mongodb_models import (
    AlertModel,
    AlertResponse,
    AlertStatus,
    AlertSource,
    ThreatIndicators,
    SeverityLevel
)

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for managing threat alerts
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize alert service
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.alerts
    
    async def create_alert(
        self,
        monitor_id: str,
        user_id: str,
        title: str,
        summary: str,
        severity: SeverityLevel,
        sources: List[Dict],
        confidence_score: float = 0.0,
        threat_indicators: Optional[Dict] = None
    ) -> AlertModel:
        """
        Create a new threat alert
        
        Called by monitor scanning engine when threats are detected
        
        Args:
            monitor_id: Which monitor generated this alert
            user_id: Alert owner
            title: Alert headline
            summary: AI-generated threat summary
            severity: Threat severity level
            sources: List of news sources
            confidence_score: How confident we are (0-1)
            threat_indicators: Extracted threat intelligence
        
        Returns:
            Created AlertModel
        """
        try:
            # Convert source dicts to AlertSource objects
            alert_sources = []
            for source in sources:
                alert_sources.append(AlertSource(**source))
            
            # Create threat indicators
            indicators = ThreatIndicators(**(threat_indicators or {}))
            
            # Create alert
            alert = AlertModel(
                monitor_id=monitor_id,
                user_id=user_id,
                title=title,
                summary=summary,
                severity=severity,
                confidence_score=confidence_score,
                source_count=len(alert_sources),
                sources=alert_sources,
                threat_indicators=indicators
            )
            
            # Check for duplicates (same title in last 24 hours)
            is_duplicate = await self._is_duplicate_alert(
                user_id=user_id,
                monitor_id=monitor_id,
                title=title,
                hours=24
            )
            
            if is_duplicate:
                logger.info(f"⚠️  Skipping duplicate alert: {title}")
                return None
            
            # Insert into database
            result = await self.collection.insert_one(alert.model_dump())
            
            if result.inserted_id:
                logger.info(f"✅ Created alert: {alert.id} (Severity: {severity.value})")
                return alert
            else:
                raise Exception("Failed to insert alert into database")
                
        except Exception as e:
            logger.error(f"❌ Error creating alert: {str(e)}")
            raise
    
    async def get_alert(self, alert_id: str, user_id: str) -> Optional[AlertModel]:
        """
        Get a specific alert by ID
        
        Security: User can only access their own alerts
        
        Args:
            alert_id: Alert ID
            user_id: User requesting the alert
        
        Returns:
            AlertModel if found, None otherwise
        """
        try:
            alert_data = await self.collection.find_one({
                "id": alert_id,
                "user_id": user_id
            })
            
            if alert_data:
                return AlertModel(**alert_data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting alert {alert_id}: {str(e)}")
            return None
    
    async def list_user_alerts(
        self,
        user_id: str,
        monitor_id: Optional[str] = None,
        status: Optional[AlertStatus] = None,
        severity: Optional[SeverityLevel] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AlertModel]:
        """
        List alerts for a user with filters
        
        Args:
            user_id: User whose alerts to list
            monitor_id: Filter by specific monitor (optional)
            status: Filter by status (optional)
            severity: Filter by severity (optional)
            skip: Pagination offset
            limit: Max results to return
        
        Returns:
            List of AlertModel objects
        """
        try:
            # Build query
            query = {"user_id": user_id}
            
            if monitor_id:
                query["monitor_id"] = monitor_id
            if status:
                query["status"] = status.value
            if severity:
                query["severity"] = severity.value
            
            # Execute query with pagination
            # Sort by created_at descending (newest first)
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            
            alerts = []
            async for alert_data in cursor:
                alerts.append(AlertModel(**alert_data))
            
            logger.info(f"📋 Listed {len(alerts)} alerts for user: {user_id}")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error listing alerts: {str(e)}")
            return []
    
    async def update_alert_status(
        self,
        alert_id: str,
        user_id: str,
        new_status: AlertStatus,
        user_feedback: Optional[str] = None
    ) -> Optional[AlertModel]:
        """
        Update alert status (acknowledge, resolve, mark false positive)
        
        Args:
            alert_id: Alert to update
            user_id: User making the update
            new_status: New status
            user_feedback: Optional feedback from user
        
        Returns:
            Updated AlertModel if successful
        """
        try:
            update_data = {
                "status": new_status.value,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if user_feedback:
                update_data["user_feedback"] = user_feedback
            
            result = await self.collection.update_one(
                {"id": alert_id, "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated alert {alert_id} status to {new_status.value}")
                return await self.get_alert(alert_id, user_id)
            else:
                logger.warning(f"⚠️  Alert {alert_id} not found or not modified")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error updating alert status: {str(e)}")
            return None
    
    async def mark_notification_sent(
        self,
        alert_id: str,
        sent_at: Optional[datetime] = None
    ) -> bool:
        """
        Mark that notification was sent for this alert
        
        Args:
            alert_id: Alert ID
            sent_at: When notification was sent (defaults to now)
        
        Returns:
            True if updated successfully
        """
        try:
            if sent_at is None:
                sent_at = datetime.now(timezone.utc)
            
            result = await self.collection.update_one(
                {"id": alert_id},
                {"$set": {
                    "notification_sent": True,
                    "notification_sent_at": sent_at
                }}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error marking notification sent: {str(e)}")
            return False
    
    async def get_alert_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get alert statistics for a user
        
        Returns counts by status, severity, and time period
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with statistics
        """
        try:
            # Total alerts
            total = await self.collection.count_documents({"user_id": user_id})
            
            # By status
            new_count = await self.collection.count_documents({
                "user_id": user_id,
                "status": AlertStatus.NEW.value
            })
            
            acknowledged_count = await self.collection.count_documents({
                "user_id": user_id,
                "status": AlertStatus.ACKNOWLEDGED.value
            })
            
            resolved_count = await self.collection.count_documents({
                "user_id": user_id,
                "status": AlertStatus.RESOLVED.value
            })
            
            # By severity
            critical_count = await self.collection.count_documents({
                "user_id": user_id,
                "severity": SeverityLevel.CRITICAL.value
            })
            
            high_count = await self.collection.count_documents({
                "user_id": user_id,
                "severity": SeverityLevel.HIGH.value
            })
            
            # Recent alerts (last 24 hours)
            last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_count = await self.collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": last_24h}
            })
            
            return {
                "total_alerts": total,
                "by_status": {
                    "new": new_count,
                    "acknowledged": acknowledged_count,
                    "resolved": resolved_count
                },
                "by_severity": {
                    "critical": critical_count,
                    "high": high_count
                },
                "last_24_hours": recent_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting alert statistics: {str(e)}")
            return {}
    
    async def cleanup_old_alerts(
        self,
        user_id: str,
        days_to_keep: int = 30
    ) -> int:
        """
        Delete alerts older than specified days
        
        Used for data retention based on subscription tier
        - Free: 7 days
        - Professional: 30 days
        - Enterprise: 365 days
        
        Args:
            user_id: User whose alerts to clean up
            days_to_keep: Number of days to retain
        
        Returns:
            Number of alerts deleted
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = await self.collection.delete_many({
                "user_id": user_id,
                "created_at": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                logger.info(f"🗑️  Cleaned up {result.deleted_count} old alerts for user {user_id}")
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up alerts: {str(e)}")
            return 0
    
    async def get_unsent_alerts(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AlertModel]:
        """
        Get alerts that haven't had notifications sent yet
        
        Used by notification system to send pending alerts
        
        Args:
            user_id: Filter by user (optional)
            limit: Max alerts to return
        
        Returns:
            List of unsent alerts
        """
        try:
            query = {"notification_sent": False}
            if user_id:
                query["user_id"] = user_id
            
            cursor = self.collection.find(query).limit(limit).sort("created_at", 1)
            
            alerts = []
            async for alert_data in cursor:
                alerts.append(AlertModel(**alert_data))
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error getting unsent alerts: {str(e)}")
            return []
    
    async def _is_duplicate_alert(
        self,
        user_id: str,
        monitor_id: str,
        title: str,
        hours: int = 24
    ) -> bool:
        """
        Check if alert with same title exists recently
        
        Prevents duplicate alerts from being created
        
        Args:
            user_id: User ID
            monitor_id: Monitor ID
            title: Alert title to check
            hours: Time window to check (default 24h)
        
        Returns:
            True if duplicate found
        """
        try:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            existing = await self.collection.find_one({
                "user_id": user_id,
                "monitor_id": monitor_id,
                "title": title,
                "created_at": {"$gte": since}
            })
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"❌ Error checking duplicate: {str(e)}")
            return False
    
    def to_response(self, alert: AlertModel) -> AlertResponse:
        """
        Convert AlertModel to API response format
        
        Args:
            alert: Alert model
        
        Returns:
            AlertResponse for API
        """
        return AlertResponse(
            id=alert.id,
            monitor_id=alert.monitor_id,
            title=alert.title,
            summary=alert.summary,
            severity=alert.severity.value,
            confidence_score=alert.confidence_score,
            source_count=alert.source_count,
            created_at=alert.created_at,
            status=alert.status.value,
            sources=alert.sources,
            threat_indicators=alert.threat_indicators
        )
