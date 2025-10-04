"""
Database Configuration for ThreatWatch
======================================

This file manages database connections for the application.

MIGRATION NOTE:
- OLD: SQLAlchemy + SQLite for authentication
- NEW: Motor + MongoDB for all data (authentication, monitoring, alerts)

MongoDB Collections:
- users: User accounts and authentication
- user_subscriptions: Subscription tiers and billing
- payment_transactions: Payment history
- monitors: Monitoring terms and settings
- alerts: Detected threats
- alert_history: Scan history and analytics
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# MongoDB Configuration
# ============================================================================

# MongoDB connection (read from environment variables)
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'threatwatch')

# Global MongoDB client and database instances
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None


def get_mongodb_client() -> AsyncIOMotorClient:
    """
    Get MongoDB client instance
    
    What is Motor?
    - Motor is the async driver for MongoDB with Python
    - Allows non-blocking database operations
    - Perfect for FastAPI's async architecture
    
    Returns:
        AsyncIOMotorClient: MongoDB client for database operations
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(MONGO_URL)
        logger.info(f"✅ MongoDB client initialized: {DB_NAME}")
    return _mongo_client


def get_mongodb() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance
    
    This is the main database object you'll use to access collections.
    
    Example usage:
        db = get_mongodb()
        users_collection = db['users']
        user = await users_collection.find_one({"email": "user@example.com"})
    
    Returns:
        AsyncIOMotorDatabase: Database instance
    """
    global _mongo_db
    if _mongo_db is None:
        client = get_mongodb_client()
        _mongo_db = client[DB_NAME]
        logger.info(f"✅ MongoDB database connected: {DB_NAME}")
    return _mongo_db


async def close_mongodb():
    """
    Close MongoDB connection
    
    Called during application shutdown to clean up resources
    """
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("✅ MongoDB connection closed")


async def init_mongodb_indexes():
    """
    Initialize database indexes for optimal performance
    
    What are indexes?
    - Like a book's index - helps find data faster
    - Without indexes, MongoDB scans every document
    - With indexes, MongoDB jumps directly to relevant documents
    
    When to create indexes?
    - Fields you frequently search by (email, user_id, monitor_id)
    - Fields you sort by (created_at, next_scan)
    - Unique fields (email - prevent duplicates)
    """
    db = get_mongodb()
    
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True, name="email_unique_idx")
        await db.users.create_index("id", unique=True, name="user_id_idx")
        logger.info("✅ Created indexes for 'users' collection")
        
        # User subscriptions indexes
        await db.user_subscriptions.create_index("user_id", name="subscription_user_idx")
        await db.user_subscriptions.create_index("id", unique=True, name="subscription_id_idx")
        await db.user_subscriptions.create_index("stripe_customer_id", name="stripe_customer_idx")
        logger.info("✅ Created indexes for 'user_subscriptions' collection")
        
        # Monitors collection indexes
        await db.monitors.create_index("user_id", name="monitor_user_idx")
        await db.monitors.create_index("id", unique=True, name="monitor_id_idx")
        await db.monitors.create_index("next_scan", name="monitor_next_scan_idx")
        await db.monitors.create_index("active", name="monitor_active_idx")
        await db.monitors.create_index([("user_id", 1), ("active", 1)], name="monitor_user_active_idx")
        logger.info("✅ Created indexes for 'monitors' collection")
        
        # Alerts collection indexes
        await db.alerts.create_index("user_id", name="alert_user_idx")
        await db.alerts.create_index("monitor_id", name="alert_monitor_idx")
        await db.alerts.create_index("id", unique=True, name="alert_id_idx")
        await db.alerts.create_index("status", name="alert_status_idx")
        await db.alerts.create_index("created_at", name="alert_created_idx")
        await db.alerts.create_index([("user_id", 1), ("status", 1)], name="alert_user_status_idx")
        logger.info("✅ Created indexes for 'alerts' collection")
        
        # Alert history collection indexes
        await db.alert_history.create_index("monitor_id", name="history_monitor_idx")
        await db.alert_history.create_index("scan_timestamp", name="history_timestamp_idx")
        await db.alert_history.create_index([("monitor_id", 1), ("scan_timestamp", -1)], name="history_monitor_time_idx")
        logger.info("✅ Created indexes for 'alert_history' collection")
        
        # Payment transactions indexes
        await db.payment_transactions.create_index("user_id", name="payment_user_idx")
        await db.payment_transactions.create_index("id", unique=True, name="payment_id_idx")
        logger.info("✅ Created indexes for 'payment_transactions' collection")
        
        logger.info("🎉 All MongoDB indexes created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {str(e)}")
        raise


# ============================================================================
# Legacy SQLite Support (for migration period only)
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite setup - DEPRECATED, only used during migration
SQLITE_URL = "sqlite:///./auth.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_auth_db():
    """
    DEPRECATED: SQLite database session
    Only used during migration from SQLite to MongoDB
    Will be removed after migration completes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Utility Functions
# ============================================================================

async def check_mongodb_connection() -> bool:
    """
    Health check for MongoDB connection
    
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        db = get_mongodb()
        await db.command('ping')
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
        return False


async def get_collection_stats() -> dict:
    """
    Get statistics about all collections
    
    Useful for monitoring and debugging
    
    Returns:
        dict: Collection names and document counts
    """
    db = get_mongodb()
    stats = {}
    
    collections = ['users', 'user_subscriptions', 'monitors', 'alerts', 'alert_history', 'payment_transactions']
    
    for collection_name in collections:
        try:
            count = await db[collection_name].count_documents({})
            stats[collection_name] = count
        except Exception as e:
            stats[collection_name] = f"Error: {str(e)}"
    
    return stats