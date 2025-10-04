"""
Monitor Service - CRUD Operations for Monitoring Terms
=======================================================

This service handles all database operations for monitors (monitoring terms).

What is a Monitor?
-----------------
A monitor is a saved search term that automatically scans for threats.
Example: "ransomware attacks on healthcare" scans Google daily for matching news.

Operations:
----------
- Create: Add new monitor
- Read: Get monitor details, list all monitors
- Update: Change monitor settings
- Delete: Remove monitor
- Schedule: Calculate next scan time
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from mongodb_models import (
    MonitorModel,
    CreateMonitorRequest,
    UpdateMonitorRequest,
    MonitorResponse,
    MonitorFrequency,
    NotificationSettings
)

logger = logging.getLogger(__name__)


class MonitorService:
    """
    Service for managing monitoring terms
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize monitor service with database connection
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.monitors
    
    async def create_monitor(
        self,
        user_id: str,
        request: CreateMonitorRequest
    ) -> MonitorModel:
        """
        Create a new monitoring term
        
        Steps:
        1. Create monitor object
        2. Calculate next scan time based on frequency
        3. Save to database
        
        Args:
            user_id: Owner of the monitor
            request: Monitor creation request data
        
        Returns:
            MonitorModel: Created monitor
        
        Raises:
            Exception: If database operation fails
        """
        try:
            # Create monitor model
            monitor = MonitorModel(
                user_id=user_id,
                term=request.term,
                description=request.description,
                keywords=request.keywords,
                exclude_keywords=request.exclude_keywords,
                frequency=request.frequency,
                severity_threshold=request.severity_threshold,
                notification_settings=request.notification_settings or NotificationSettings()
            )
            
            # Calculate next scan time
            monitor.next_scan = self._calculate_next_scan(monitor.frequency)
            
            # Insert into database
            result = await self.collection.insert_one(monitor.model_dump())
            
            if result.inserted_id:
                logger.info(f"✅ Created monitor: {monitor.id} for user: {user_id}")
                return monitor
            else:
                raise Exception("Failed to insert monitor into database")
                
        except Exception as e:
            logger.error(f"❌ Error creating monitor: {str(e)}")
            raise
    
    async def get_monitor(self, monitor_id: str, user_id: str) -> Optional[MonitorModel]:
        """
        Get a specific monitor by ID
        
        Security: Ensures user can only access their own monitors
        
        Args:
            monitor_id: Monitor ID to retrieve
            user_id: User requesting the monitor
        
        Returns:
            MonitorModel if found, None otherwise
        """
        try:
            monitor_data = await self.collection.find_one({
                "id": monitor_id,
                "user_id": user_id  # Security: User can only access their monitors
            })
            
            if monitor_data:
                return MonitorModel(**monitor_data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting monitor {monitor_id}: {str(e)}")
            return None
    
    async def list_user_monitors(
        self,
        user_id: str,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[MonitorModel]:
        """
        List all monitors for a user
        
        Args:
            user_id: User whose monitors to list
            active_only: If True, only return active monitors
            skip: Number of records to skip (pagination)
            limit: Maximum records to return
        
        Returns:
            List of MonitorModel objects
        """
        try:
            # Build query
            query = {"user_id": user_id}
            if active_only:
                query["active"] = True
            
            # Execute query with pagination
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            
            monitors = []
            async for monitor_data in cursor:
                monitors.append(MonitorModel(**monitor_data))
            
            logger.info(f"📋 Listed {len(monitors)} monitors for user: {user_id}")
            return monitors
            
        except Exception as e:
            logger.error(f"❌ Error listing monitors: {str(e)}")
            return []
    
    async def update_monitor(
        self,
        monitor_id: str,
        user_id: str,
        request: UpdateMonitorRequest
    ) -> Optional[MonitorModel]:
        """
        Update monitor settings
        
        Only updates fields that are provided (not None)
        
        Args:
            monitor_id: Monitor to update
            user_id: User making the update
            request: Fields to update
        
        Returns:
            Updated MonitorModel if successful, None otherwise
        """
        try:
            # Build update dict (only include non-None values)
            update_data = {}
            
            if request.term is not None:
                update_data["term"] = request.term
            if request.description is not None:
                update_data["description"] = request.description
            if request.keywords is not None:
                update_data["keywords"] = request.keywords
            if request.exclude_keywords is not None:
                update_data["exclude_keywords"] = request.exclude_keywords
            if request.frequency is not None:
                update_data["frequency"] = request.frequency
                # Recalculate next scan if frequency changed
                update_data["next_scan"] = self._calculate_next_scan(request.frequency)
            if request.severity_threshold is not None:
                update_data["severity_threshold"] = request.severity_threshold
            if request.active is not None:
                update_data["active"] = request.active
            if request.notification_settings is not None:
                update_data["notification_settings"] = request.notification_settings.model_dump()
            
            # Always update the updated_at timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update in database
            result = await self.collection.update_one(
                {"id": monitor_id, "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                # Fetch and return updated monitor
                updated_monitor = await self.get_monitor(monitor_id, user_id)
                logger.info(f"✅ Updated monitor: {monitor_id}")
                return updated_monitor
            else:
                logger.warning(f"⚠️  Monitor {monitor_id} not found or not modified")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error updating monitor {monitor_id}: {str(e)}")
            return None
    
    async def delete_monitor(self, monitor_id: str, user_id: str) -> bool:
        """
        Delete a monitor
        
        Note: This is a hard delete. Consider soft delete (set active=False) for production
        
        Args:
            monitor_id: Monitor to delete
            user_id: User requesting deletion
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one({
                "id": monitor_id,
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted monitor: {monitor_id}")
                return True
            else:
                logger.warning(f"⚠️  Monitor {monitor_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting monitor {monitor_id}: {str(e)}")
            return False
    
    async def get_due_monitors(self) -> List[MonitorModel]:
        """
        Get all monitors that are due for scanning
        
        A monitor is due if:
        - It's active
        - next_scan time has passed
        
        Returns:
            List of monitors ready to scan
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Query for active monitors where next_scan <= now
            query = {
                "active": True,
                "next_scan": {"$lte": now}
            }
            
            cursor = self.collection.find(query)
            
            due_monitors = []
            async for monitor_data in cursor:
                due_monitors.append(MonitorModel(**monitor_data))
            
            if due_monitors:
                logger.info(f"📊 Found {len(due_monitors)} monitors due for scanning")
            
            return due_monitors
            
        except Exception as e:
            logger.error(f"❌ Error getting due monitors: {str(e)}")
            return []
    
    async def update_scan_status(
        self,
        monitor_id: str,
        scan_timestamp: datetime,
        next_scan: datetime,
        increment_scan_count: bool = True,
        increment_alert_count: int = 0
    ) -> bool:
        """
        Update monitor after a scan completes
        
        Args:
            monitor_id: Monitor that was scanned
            scan_timestamp: When the scan occurred
            next_scan: When to scan next
            increment_scan_count: Whether to increment scan counter
            increment_alert_count: Number of alerts generated (to add to counter)
        
        Returns:
            True if updated successfully
        """
        try:
            update_data = {
                "last_scan": scan_timestamp,
                "next_scan": next_scan,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Increment counters
            increment_data = {}
            if increment_scan_count:
                increment_data["scan_count"] = 1
            if increment_alert_count > 0:
                increment_data["alert_count"] = increment_alert_count
            
            # Build update operations
            operations = {"$set": update_data}
            if increment_data:
                operations["$inc"] = increment_data
            
            result = await self.collection.update_one(
                {"id": monitor_id},
                operations
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating scan status for {monitor_id}: {str(e)}")
            return False
    
    async def get_monitor_count(self, user_id: str) -> int:
        """
        Get total number of monitors for a user
        
        Useful for enforcing subscription tier limits
        
        Args:
            user_id: User to count monitors for
        
        Returns:
            Number of monitors
        """
        try:
            count = await self.collection.count_documents({"user_id": user_id})
            return count
        except Exception as e:
            logger.error(f"❌ Error counting monitors: {str(e)}")
            return 0
    
    def _calculate_next_scan(self, frequency: MonitorFrequency) -> datetime:
        """
        Calculate when the next scan should occur
        
        Frequency mapping:
        - HOURLY: 1 hour from now
        - DAILY: 24 hours from now
        - WEEKLY: 7 days from now
        
        Args:
            frequency: Scan frequency
        
        Returns:
            Datetime for next scan
        """
        now = datetime.now(timezone.utc)
        
        if frequency == MonitorFrequency.HOURLY:
            return now + timedelta(hours=1)
        elif frequency == MonitorFrequency.DAILY:
            return now + timedelta(days=1)
        elif frequency == MonitorFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        else:
            # Default to daily
            return now + timedelta(days=1)
    
    def to_response(self, monitor: MonitorModel) -> MonitorResponse:
        """
        Convert MonitorModel to API response format
        
        Args:
            monitor: Monitor model
        
        Returns:
            MonitorResponse for API
        """
        return MonitorResponse(
            id=monitor.id,
            user_id=monitor.user_id,
            term=monitor.term,
            description=monitor.description,
            frequency=monitor.frequency.value,
            severity_threshold=monitor.severity_threshold.value,
            active=monitor.active,
            created_at=monitor.created_at,
            last_scan=monitor.last_scan,
            next_scan=monitor.next_scan,
            scan_count=monitor.scan_count,
            alert_count=monitor.alert_count,
            notification_settings=monitor.notification_settings
        )
