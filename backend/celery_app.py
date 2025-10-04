"""
Celery Configuration for ThreatWatch
====================================

What is Celery?
--------------
Celery is a distributed task queue system for Python. It allows you to:
- Run time-consuming tasks in the background
- Schedule tasks to run at specific times (like cron jobs)
- Distribute work across multiple workers
- Retry failed tasks automatically

Why do we need it?
-----------------
For long-term monitoring, we need to:
1. Scan monitors every hour/day/week automatically
2. Process multiple monitors concurrently
3. Handle failures gracefully
4. Not block the main API

Components:
----------
1. Broker (Redis): Message queue where tasks are stored
2. Worker: Processes that execute tasks
3. Beat: Scheduler that triggers periodic tasks
4. Backend (Redis): Stores task results

Architecture:
------------
    FastAPI API                    Redis                      Celery Worker
    -----------                    -----                      -------------
         |                           |                              |
         | 1. Create task            |                              |
         |-------------------------->|                              |
         |                           | 2. Queue task                |
         |                           |----------------------------->|
         |                           |                              |
         |                           |      3. Process task         |
         |                           |                        (scan monitor)
         |                           |                              |
         |                           | 4. Store result              |
         |                           |<-----------------------------|
         | 5. Get result             |                              |
         |<--------------------------|                              |


Usage:
------
# Start Celery worker (in terminal):
celery -A celery_app worker --loglevel=info

# Start Celery beat scheduler (in separate terminal):
celery -A celery_app beat --loglevel=info

# Monitor tasks with Flower (web UI):
celery -A celery_app flower
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============================================================================
# Celery Configuration
# ============================================================================

# Redis connection URLs
# Format: redis://[username]:[password]@[host]:[port]/[db_number]
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL)

# Create Celery application
celery_app = Celery(
    'threatwatch',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['celery_tasks']  # Import tasks from celery_tasks.py
)

# ============================================================================
# Celery Settings
# ============================================================================

celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone settings
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,  # Track when tasks start
    task_time_limit=600,      # 10 minutes max per task
    task_soft_time_limit=540, # Soft limit at 9 minutes (warning)
    
    # Result backend settings
    result_expires=3600,      # Results expire after 1 hour
    result_persistent=True,   # Store results even after restart
    
    # Worker settings
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    
    # Task routing (can define different queues for different priorities)
    task_routes={
        'celery_tasks.scan_monitor_task': {'queue': 'monitoring'},
        'celery_tasks.scan_all_due_monitors_task': {'queue': 'monitoring'},
        'celery_tasks.cleanup_old_alerts_task': {'queue': 'maintenance'},
    },
    
    # Rate limiting
    task_annotations={
        'celery_tasks.scan_monitor_task': {'rate_limit': '10/m'},  # Max 10 scans per minute
    },
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion (enables retry on failure)
    task_reject_on_worker_lost=True,  # Reject task if worker crashes
)

# ============================================================================
# Celery Beat Schedule (Periodic Tasks)
# ============================================================================

"""
What is Celery Beat?
-------------------
Celery Beat is a scheduler that triggers periodic tasks automatically.
Like a cron job, but integrated with Celery.

Schedule Syntax:
---------------
1. crontab(minute='*/30'): Every 30 minutes
2. crontab(hour='*/6'): Every 6 hours  
3. crontab(hour=9, minute=0): Every day at 9:00 AM
4. crontab(day_of_week='monday', hour=9): Every Monday at 9:00 AM

Our Schedules:
-------------
1. Scan monitors: Every 5 minutes (check which monitors need scanning)
2. Cleanup old alerts: Daily at 2:00 AM (delete alerts older than retention period)
3. Generate daily summaries: Daily at 8:00 AM (send digest emails)
4. Update monitor statistics: Every hour (calculate scan success rates)
"""

celery_app.conf.beat_schedule = {
    # Main monitoring task - runs every 5 minutes
    # Checks which monitors are due for scanning and executes them
    'scan-due-monitors-every-5-minutes': {
        'task': 'celery_tasks.scan_all_due_monitors_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {
            'expires': 240,  # Task expires after 4 minutes if not executed
        }
    },
    
    # Cleanup old alerts - runs daily at 2:00 AM UTC
    # Removes alerts older than retention period based on subscription tier
    'cleanup-old-alerts-daily': {
        'task': 'celery_tasks.cleanup_old_alerts_task',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC daily
    },
    
    # Generate daily summaries - runs daily at 8:00 AM UTC
    # Sends digest emails to users with daily_summary enabled
    'generate-daily-summaries': {
        'task': 'celery_tasks.generate_daily_summaries_task',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM UTC daily
    },
    
    # Update monitor statistics - runs every hour
    # Calculates success rates, average scan times, etc.
    'update-monitor-statistics-hourly': {
        'task': 'celery_tasks.update_monitor_statistics_task',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Health check - runs every 10 minutes
    # Ensures Celery and Redis are working properly
    'health-check-every-10-minutes': {
        'task': 'celery_tasks.health_check_task',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}

# ============================================================================
# Utility Functions
# ============================================================================

def get_celery_app():
    """
    Get Celery application instance
    
    Returns:
        Celery: Configured Celery application
    """
    return celery_app


def check_celery_health():
    """
    Check if Celery workers are running
    
    Returns:
        dict: Status information about Celery
    """
    try:
        # Check if workers are available
        inspect = celery_app.control.inspect()
        
        # Get active workers
        active_workers = inspect.active()
        
        # Get scheduled tasks
        scheduled_tasks = inspect.scheduled()
        
        # Get worker statistics
        stats = inspect.stats()
        
        return {
            "status": "healthy" if active_workers else "no_workers",
            "active_workers": list(active_workers.keys()) if active_workers else [],
            "worker_count": len(active_workers) if active_workers else 0,
            "scheduled_tasks": len(scheduled_tasks) if scheduled_tasks else 0,
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_redis_health():
    """
    Check if Redis is accessible
    
    Returns:
        dict: Redis connection status
    """
    try:
        # Test Redis connection
        result = celery_app.backend.client.ping()
        
        return {
            "status": "healthy" if result else "unhealthy",
            "redis_url": CELERY_BROKER_URL.split('@')[-1] if '@' in CELERY_BROKER_URL else CELERY_BROKER_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# Worker Signals (for logging and monitoring)
# ============================================================================

from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun, task_failure

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Called when worker is ready to accept tasks"""
    print("✅ Celery worker is ready and waiting for tasks")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Called when worker is shutting down"""
    print("🛑 Celery worker is shutting down")


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, kwargs=None, **extra):
    """Called before task execution"""
    print(f"▶️  Starting task: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, state=None, retval=None, **kwargs):
    """Called after task execution"""
    print(f"✅ Completed task: {task.name} (ID: {task_id}) - State: {state}")


@task_failure.connect
def task_failure_handler(task_id=None, exception=None, traceback=None, **kwargs):
    """Called when task fails"""
    print(f"❌ Task failed (ID: {task_id}): {str(exception)}")


# ============================================================================
# CLI Commands (for testing)
# ============================================================================

if __name__ == '__main__':
    """
    Test Celery configuration
    
    Run: python celery_app.py
    """
    print("\n" + "="*60)
    print("CELERY CONFIGURATION TEST")
    print("="*60)
    
    print(f"\n📋 Configuration:")
    print(f"  Broker URL: {CELERY_BROKER_URL}")
    print(f"  Backend URL: {CELERY_RESULT_BACKEND}")
    print(f"  Task modules: {celery_app.conf.include}")
    
    print(f"\n⏰ Scheduled Tasks:")
    for name, schedule in celery_app.conf.beat_schedule.items():
        print(f"  - {name}")
        print(f"    Task: {schedule['task']}")
        print(f"    Schedule: {schedule['schedule']}")
    
    print(f"\n🏥 Health Checks:")
    redis_health = check_redis_health()
    print(f"  Redis: {redis_health['status']}")
    
    celery_health = check_celery_health()
    print(f"  Celery Workers: {celery_health['status']}")
    print(f"  Active Workers: {celery_health['worker_count']}")
    
    print("\n" + "="*60)
    print("To start Celery worker:")
    print("  celery -A celery_app worker --loglevel=info")
    print("\nTo start Celery beat:")
    print("  celery -A celery_app beat --loglevel=info")
    print("\nTo monitor with Flower:")
    print("  celery -A celery_app flower")
    print("="*60 + "\n")
