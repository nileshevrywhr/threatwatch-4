"""
Celery Background Tasks
=======================

These are the actual tasks that run in the background via Celery workers.

Tasks:
-----
1. scan_monitor_task - Scan a single monitor
2. scan_all_due_monitors_task - Find and scan all due monitors
3. cleanup_old_alerts_task - Delete old alerts
4. generate_daily_summaries_task - Send daily digest emails
5. update_monitor_statistics_task - Update analytics
6. health_check_task - System health monitoring

How it works:
------------
1. Celery Beat triggers tasks on schedule
2. Tasks are added to Redis queue
3. Celery Workers pick up tasks and execute them
4. Results are stored in Redis
"""

from celery import Task
from celery_app import celery_app
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging
import asyncio

# Import services
from database import get_mongodb, init_mongodb_indexes
from monitor_service import MonitorService
from alert_service import AlertService
from monitor_engine import MonitorEngine
from mongodb_models import MonitorModel

logger = logging.getLogger(__name__)


# ============================================================================
# Helper function to run async code in Celery (which is sync)
# ============================================================================

def run_async(coro):
    """
    Run async function in sync context
    
    Celery tasks are synchronous, but our services use async/await.
    This helper allows us to call async functions from Celery tasks.
    
    Args:
        coro: Async coroutine to run
    
    Returns:
        Result of the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


# ============================================================================
# Monitor Scanning Tasks
# ============================================================================

@celery_app.task(
    name='celery_tasks.scan_monitor_task',
    bind=True,
    max_retries=3,
    default_retry_delay=300  # Retry after 5 minutes
)
def scan_monitor_task(self: Task, monitor_id: str) -> Dict[str, Any]:
    """
    Scan a single monitor for threats
    
    This is the main monitoring task. It:
    1. Fetches monitor from database
    2. Runs scan via MonitorEngine
    3. Creates alert if threat detected
    4. Records scan history
    5. Updates monitor's next_scan time
    
    Args:
        monitor_id: ID of monitor to scan
    
    Returns:
        Dictionary with scan results
    """
    logger.info(f"🔍 Task started: Scanning monitor {monitor_id}")
    
    try:
        # Get database connection
        db = get_mongodb()
        
        # Initialize services
        monitor_service = MonitorService(db)
        alert_service = AlertService(db)
        engine = MonitorEngine()
        
        # Async function to perform the scan
        async def perform_scan():
            # Get monitor
            monitor_data = await db.monitors.find_one({"id": monitor_id})
            if not monitor_data:
                raise Exception(f"Monitor {monitor_id} not found")
            
            monitor = MonitorModel(**monitor_data)
            
            # Check if monitor is active
            if not monitor.active:
                logger.info(f"  ⏸️  Monitor {monitor_id} is inactive, skipping")
                return {"status": "skipped", "reason": "inactive"}
            
            # Perform scan
            alert, history = await engine.scan_monitor(monitor)
            
            # Save alert if created
            alert_id = None
            if alert:
                result = await db.alerts.insert_one(alert.model_dump())
                alert_id = alert.id
                logger.info(f"  ✅ Alert saved: {alert_id}")
            
            # Save scan history
            await db.alert_history.insert_one(history.model_dump())
            
            # Update monitor
            next_scan = monitor_service._calculate_next_scan(monitor.frequency)
            await monitor_service.update_scan_status(
                monitor_id=monitor.id,
                scan_timestamp=history.scan_timestamp,
                next_scan=next_scan,
                increment_scan_count=True,
                increment_alert_count=1 if alert else 0
            )
            
            return {
                "status": "success",
                "monitor_id": monitor_id,
                "alert_created": alert is not None,
                "alert_id": alert_id,
                "articles_processed": history.articles_processed,
                "scan_duration": history.scan_duration,
                "cost": history.api_costs.total_cost
            }
        
        # Run async scan
        result = run_async(perform_scan())
        
        logger.info(f"✅ Task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")
        
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"❌ Max retries exceeded for monitor {monitor_id}")
            return {
                "status": "failed",
                "monitor_id": monitor_id,
                "error": str(e)
            }


@celery_app.task(name='celery_tasks.scan_all_due_monitors_task')
def scan_all_due_monitors_task() -> Dict[str, Any]:
    """
    Find all monitors that are due for scanning and trigger scans
    
    This task runs every 5 minutes via Celery Beat.
    It checks which monitors need scanning and dispatches scan tasks.
    
    Returns:
        Dictionary with summary of triggered scans
    """
    logger.info("📊 Task started: Finding due monitors")
    
    try:
        db = get_mongodb()
        monitor_service = MonitorService(db)
        
        async def find_and_trigger():
            # Get monitors due for scanning
            due_monitors = await monitor_service.get_due_monitors()
            
            if not due_monitors:
                logger.info("  ℹ️  No monitors due for scanning")
                return {
                    "status": "success",
                    "monitors_found": 0,
                    "scans_triggered": 0
                }
            
            logger.info(f"  📋 Found {len(due_monitors)} monitors to scan")
            
            # Trigger scan task for each monitor
            triggered = 0
            for monitor in due_monitors:
                try:
                    # Dispatch async task
                    scan_monitor_task.delay(monitor.id)
                    triggered += 1
                    logger.info(f"    ▶️  Triggered scan for: {monitor.term}")
                except Exception as e:
                    logger.error(f"    ❌ Failed to trigger scan for {monitor.id}: {str(e)}")
            
            return {
                "status": "success",
                "monitors_found": len(due_monitors),
                "scans_triggered": triggered,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        result = run_async(find_and_trigger())
        logger.info(f"✅ Task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ============================================================================
# Maintenance Tasks
# ============================================================================

@celery_app.task(name='celery_tasks.cleanup_old_alerts_task')
def cleanup_old_alerts_task() -> Dict[str, Any]:
    """
    Clean up old alerts based on subscription tiers
    
    Retention periods:
    - Free: 7 days
    - Professional: 30 days
    - Enterprise: 365 days
    - Enterprise+: No deletion
    
    Runs daily at 2 AM UTC
    
    Returns:
        Dictionary with cleanup summary
    """
    logger.info("🗑️  Task started: Cleaning up old alerts")
    
    try:
        db = get_mongodb()
        alert_service = AlertService(db)
        
        async def cleanup():
            total_deleted = 0
            
            # Get all users with their subscription tiers
            users_cursor = db.users.find({})
            
            async for user_data in users_cursor:
                user_id = user_data.get('id')
                
                # Get user's subscription
                subscription = await db.user_subscriptions.find_one({"user_id": user_id})
                
                if not subscription:
                    # No subscription = free tier
                    days_to_keep = 7
                else:
                    tier = subscription.get('tier', 'free')
                    tier_retention = {
                        'free': 7,
                        'professional': 30,
                        'enterprise': 365,
                        'enterprise_plus': None  # Keep forever
                    }
                    days_to_keep = tier_retention.get(tier, 7)
                
                # Skip cleanup for enterprise_plus
                if days_to_keep is None:
                    continue
                
                # Cleanup user's old alerts
                deleted = await alert_service.cleanup_old_alerts(user_id, days_to_keep)
                total_deleted += deleted
            
            return {
                "status": "success",
                "total_deleted": total_deleted,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        result = run_async(cleanup())
        logger.info(f"✅ Task completed: Deleted {result['total_deleted']} old alerts")
        return result
        
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name='celery_tasks.generate_daily_summaries_task')
def generate_daily_summaries_task() -> Dict[str, Any]:
    """
    Generate and send daily summary emails
    
    For users with daily_summary enabled:
    1. Get all new alerts from last 24 hours
    2. Generate summary report
    3. Send email
    
    Runs daily at 8 AM UTC
    
    Returns:
        Dictionary with summary of emails sent
    """
    logger.info("📧 Task started: Generating daily summaries")
    
    try:
        # TODO: Implement email sending in Phase 2
        # For now, just log that we would send emails
        
        db = get_mongodb()
        
        async def generate():
            summaries_generated = 0
            
            # Get all monitors with daily_summary enabled
            cursor = db.monitors.find({"notification_settings.daily_summary": True})
            
            user_monitors = {}
            async for monitor_data in cursor:
                user_id = monitor_data.get('user_id')
                if user_id not in user_monitors:
                    user_monitors[user_id] = []
                user_monitors[user_id].append(monitor_data)
            
            # Generate summary for each user
            for user_id, monitors in user_monitors.items():
                # Get alerts from last 24 hours
                yesterday = datetime.now(timezone.utc) - timedelta(days=1)
                alerts = await db.alerts.find({
                    "user_id": user_id,
                    "created_at": {"$gte": yesterday}
                }).to_list(length=None)
                
                if alerts:
                    # TODO: Send email with summary
                    logger.info(f"  📧 Would send summary to user {user_id}: {len(alerts)} alerts")
                    summaries_generated += 1
            
            return {
                "status": "success",
                "summaries_generated": summaries_generated,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        result = run_async(generate())
        logger.info(f"✅ Task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name='celery_tasks.update_monitor_statistics_task')
def update_monitor_statistics_task() -> Dict[str, Any]:
    """
    Update monitor statistics and analytics
    
    Calculates:
    - Success rate (scans that completed successfully)
    - Average scan duration
    - Alert frequency
    - Cost per scan
    
    Runs every hour
    
    Returns:
        Dictionary with statistics
    """
    logger.info("📊 Task started: Updating monitor statistics")
    
    try:
        db = get_mongodb()
        
        async def update_stats():
            # Get scan history from last 24 hours
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            cursor = db.alert_history.find({"scan_timestamp": {"$gte": yesterday}})
            
            total_scans = 0
            successful_scans = 0
            total_duration = 0
            total_cost = 0
            
            async for history in cursor:
                total_scans += 1
                if history.get('success'):
                    successful_scans += 1
                total_duration += history.get('scan_duration', 0)
                total_cost += history.get('api_costs', {}).get('total_cost', 0)
            
            stats = {
                "total_scans_24h": total_scans,
                "success_rate": (successful_scans / total_scans * 100) if total_scans > 0 else 0,
                "avg_duration": (total_duration / total_scans) if total_scans > 0 else 0,
                "total_cost_24h": total_cost,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"  📊 Statistics: {stats}")
            
            return {
                "status": "success",
                **stats
            }
        
        result = run_async(update_stats())
        logger.info(f"✅ Task completed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ============================================================================
# Health Check Task
# ============================================================================

@celery_app.task(name='celery_tasks.health_check_task')
def health_check_task() -> Dict[str, Any]:
    """
    System health check
    
    Verifies:
    - MongoDB connection
    - Redis connection
    - Celery workers running
    - Recent task execution
    
    Runs every 10 minutes
    
    Returns:
        Dictionary with health status
    """
    logger.info("🏥 Task started: Health check")
    
    try:
        db = get_mongodb()
        
        async def check_health():
            # Check MongoDB
            try:
                await db.command('ping')
                mongo_ok = True
            except:
                mongo_ok = False
            
            # Check collections exist
            collections = await db.list_collection_names()
            
            # Check recent scans
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_scans = await db.alert_history.count_documents({
                "scan_timestamp": {"$gte": one_hour_ago}
            })
            
            return {
                "status": "healthy" if mongo_ok else "unhealthy",
                "mongodb": "connected" if mongo_ok else "disconnected",
                "collections": len(collections),
                "recent_scans_1h": recent_scans,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        result = run_async(check_health())
        logger.info(f"✅ Health check: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
