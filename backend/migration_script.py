"""
SQLite to MongoDB Migration Script
===================================

This script migrates user authentication data from SQLite to MongoDB.

What it does:
1. Reads all users from SQLite (auth.db)
2. Converts data to MongoDB format
3. Inserts into MongoDB users collection
4. Migrates subscriptions and payment data
5. Verifies migration success

Usage:
    python migration_script.py

IMPORTANT: Run this before switching to MongoDB in production!
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
import logging

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import SQLAlchemy models (old system)
from auth_models import User, UserSubscription, PaymentTransaction
from database import engine, SessionLocal

# Import MongoDB models (new system)
from mongodb_models import UserModel, UserSubscriptionModel, PaymentTransactionModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """
    Handles migration from SQLite to MongoDB
    """
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'threatwatch')
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_db = None
    
    async def connect_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.mongo_client = AsyncIOMotorClient(self.mongo_url)
            self.mongo_db = self.mongo_client[self.db_name]
            # Test connection
            await self.mongo_db.command('ping')
            logger.info("✅ Connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            return False
    
    def connect_sqlite(self):
        """Connect to SQLite"""
        try:
            self.sqlite_db = SessionLocal()
            logger.info("✅ Connected to SQLite")
            return True
        except Exception as e:
            logger.error(f"❌ SQLite connection failed: {str(e)}")
            return False
    
    async def migrate_users(self):
        """
        Migrate users from SQLite to MongoDB
        
        Converts SQLAlchemy User objects to Pydantic UserModel objects
        """
        logger.info("\n" + "="*60)
        logger.info("MIGRATING USERS")
        logger.info("="*60)
        
        try:
            # Get all users from SQLite
            users = self.sqlite_db.query(User).all()
            logger.info(f"📊 Found {len(users)} users in SQLite")
            
            if not users:
                logger.info("ℹ️  No users to migrate")
                return 0
            
            # Check if users already exist in MongoDB
            existing_count = await self.mongo_db.users.count_documents({})
            if existing_count > 0:
                logger.warning(f"⚠️  MongoDB already has {existing_count} users")
                response = input("Continue and update existing users? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Migration cancelled by user")
                    return 0
            
            migrated_count = 0
            for user in users:
                try:
                    # Convert SQLAlchemy User to dict for MongoDB
                    user_data = {
                        "id": str(user.id),  # Convert UUID to string
                        "email": user.email,
                        "full_name": user.full_name,
                        "hashed_password": user.hashed_password,
                        "is_active": user.is_active,
                        "created_at": user.created_at.replace(tzinfo=timezone.utc) if user.created_at else datetime.now(timezone.utc),
                        "last_login": user.last_login.replace(tzinfo=timezone.utc) if user.last_login else None,
                        "quick_scans_today": user.quick_scans_today,
                        "quick_scans_reset_date": user.quick_scans_reset_date.replace(tzinfo=timezone.utc) if user.quick_scans_reset_date else datetime.now(timezone.utc)
                    }
                    
                    # Validate with Pydantic model
                    user_model = UserModel(**user_data)
                    
                    # Upsert into MongoDB (insert or update if exists)
                    result = await self.mongo_db.users.update_one(
                        {"id": user_model.id},
                        {"$set": user_model.model_dump()},
                        upsert=True
                    )
                    
                    if result.upserted_id or result.modified_count:
                        migrated_count += 1
                        logger.info(f"  ✅ Migrated user: {user.email}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to migrate user {user.email}: {str(e)}")
            
            logger.info(f"\n🎉 Successfully migrated {migrated_count}/{len(users)} users")
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ User migration failed: {str(e)}")
            return 0
    
    async def migrate_subscriptions(self):
        """
        Migrate user subscriptions from SQLite to MongoDB
        """
        logger.info("\n" + "="*60)
        logger.info("MIGRATING SUBSCRIPTIONS")
        logger.info("="*60)
        
        try:
            # Get all subscriptions from SQLite
            subscriptions = self.sqlite_db.query(UserSubscription).all()
            logger.info(f"📊 Found {len(subscriptions)} subscriptions in SQLite")
            
            if not subscriptions:
                logger.info("ℹ️  No subscriptions to migrate")
                return 0
            
            migrated_count = 0
            for sub in subscriptions:
                try:
                    # Convert to dict for MongoDB
                    sub_data = {
                        "id": str(sub.id),
                        "user_id": str(sub.user_id),
                        "tier": sub.tier,
                        "status": sub.status,
                        "stripe_customer_id": sub.stripe_customer_id,
                        "stripe_subscription_id": sub.stripe_subscription_id,
                        "current_period_start": sub.current_period_start.replace(tzinfo=timezone.utc) if sub.current_period_start else None,
                        "current_period_end": sub.current_period_end.replace(tzinfo=timezone.utc) if sub.current_period_end else None,
                        "created_at": sub.created_at.replace(tzinfo=timezone.utc) if sub.created_at else datetime.now(timezone.utc),
                        "updated_at": sub.updated_at.replace(tzinfo=timezone.utc) if sub.updated_at else datetime.now(timezone.utc)
                    }
                    
                    # Validate with Pydantic
                    sub_model = UserSubscriptionModel(**sub_data)
                    
                    # Upsert into MongoDB
                    result = await self.mongo_db.user_subscriptions.update_one(
                        {"id": sub_model.id},
                        {"$set": sub_model.model_dump()},
                        upsert=True
                    )
                    
                    if result.upserted_id or result.modified_count:
                        migrated_count += 1
                        logger.info(f"  ✅ Migrated subscription for user: {sub.user_id}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to migrate subscription {sub.id}: {str(e)}")
            
            logger.info(f"\n🎉 Successfully migrated {migrated_count}/{len(subscriptions)} subscriptions")
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Subscription migration failed: {str(e)}")
            return 0
    
    async def migrate_payments(self):
        """
        Migrate payment transactions from SQLite to MongoDB
        """
        logger.info("\n" + "="*60)
        logger.info("MIGRATING PAYMENT TRANSACTIONS")
        logger.info("="*60)
        
        try:
            # Get all payments from SQLite
            payments = self.sqlite_db.query(PaymentTransaction).all()
            logger.info(f"📊 Found {len(payments)} payment transactions in SQLite")
            
            if not payments:
                logger.info("ℹ️  No payment transactions to migrate")
                return 0
            
            migrated_count = 0
            for payment in payments:
                try:
                    # Convert to dict for MongoDB
                    payment_data = {
                        "id": str(payment.id),
                        "user_id": str(payment.user_id),
                        "subscription_id": str(payment.subscription_id),
                        "stripe_payment_intent_id": payment.stripe_payment_intent_id,
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "status": payment.status,
                        "description": payment.description,
                        "created_at": payment.created_at.replace(tzinfo=timezone.utc) if payment.created_at else datetime.now(timezone.utc)
                    }
                    
                    # Validate with Pydantic
                    payment_model = PaymentTransactionModel(**payment_data)
                    
                    # Upsert into MongoDB
                    result = await self.mongo_db.payment_transactions.update_one(
                        {"id": payment_model.id},
                        {"$set": payment_model.model_dump()},
                        upsert=True
                    )
                    
                    if result.upserted_id or result.modified_count:
                        migrated_count += 1
                        logger.info(f"  ✅ Migrated payment: {payment.id}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to migrate payment {payment.id}: {str(e)}")
            
            logger.info(f"\n🎉 Successfully migrated {migrated_count}/{len(payments)} payment transactions")
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Payment migration failed: {str(e)}")
            return 0
    
    async def verify_migration(self):
        """
        Verify that migration was successful
        Compare counts between SQLite and MongoDB
        """
        logger.info("\n" + "="*60)
        logger.info("VERIFYING MIGRATION")
        logger.info("="*60)
        
        try:
            # Count SQLite records
            sqlite_users = self.sqlite_db.query(User).count()
            sqlite_subs = self.sqlite_db.query(UserSubscription).count()
            sqlite_payments = self.sqlite_db.query(PaymentTransaction).count()
            
            # Count MongoDB records
            mongo_users = await self.mongo_db.users.count_documents({})
            mongo_subs = await self.mongo_db.user_subscriptions.count_documents({})
            mongo_payments = await self.mongo_db.payment_transactions.count_documents({})
            
            logger.info(f"\n📊 Migration Verification:")
            logger.info(f"  Users:        SQLite={sqlite_users}, MongoDB={mongo_users}")
            logger.info(f"  Subscriptions: SQLite={sqlite_subs}, MongoDB={mongo_subs}")
            logger.info(f"  Payments:     SQLite={sqlite_payments}, MongoDB={mongo_payments}")
            
            if (mongo_users >= sqlite_users and 
                mongo_subs >= sqlite_subs and 
                mongo_payments >= sqlite_payments):
                logger.info("\n✅ Migration verification PASSED!")
                logger.info("   All data successfully migrated to MongoDB")
                return True
            else:
                logger.warning("\n⚠️  Migration verification FAILED!")
                logger.warning("   Some data may not have migrated correctly")
                return False
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {str(e)}")
            return False
    
    def close_connections(self):
        """Close all database connections"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("✅ Closed MongoDB connection")
        
        if self.sqlite_db:
            self.sqlite_db.close()
            logger.info("✅ Closed SQLite connection")


async def run_migration():
    """
    Main migration function
    """
    logger.info("\n" + "="*60)
    logger.info("THREATWATCH DATABASE MIGRATION")
    logger.info("SQLite → MongoDB")
    logger.info("="*60)
    
    migrator = DataMigrator()
    
    try:
        # Connect to databases
        logger.info("\n🔌 Connecting to databases...")
        mongo_ok = await migrator.connect_mongodb()
        sqlite_ok = migrator.connect_sqlite()
        
        if not mongo_ok or not sqlite_ok:
            logger.error("❌ Failed to connect to databases")
            return
        
        # Run migrations
        users_migrated = await migrator.migrate_users()
        subs_migrated = await migrator.migrate_subscriptions()
        payments_migrated = await migrator.migrate_payments()
        
        # Verify
        verification_ok = await migrator.verify_migration()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Users migrated: {users_migrated}")
        logger.info(f"✅ Subscriptions migrated: {subs_migrated}")
        logger.info(f"✅ Payments migrated: {payments_migrated}")
        logger.info(f"{'✅' if verification_ok else '⚠️ '} Verification: {'PASSED' if verification_ok else 'FAILED'}")
        
        if verification_ok:
            logger.info("\n🎉 Migration completed successfully!")
            logger.info("   You can now switch to MongoDB in your application")
            logger.info("   Remember to backup auth.db before deleting it!")
        else:
            logger.warning("\n⚠️  Migration completed with warnings")
            logger.warning("   Please review the logs and verify data manually")
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {str(e)}")
    
    finally:
        migrator.close_connections()


if __name__ == "__main__":
    # Check if auth.db exists
    db_path = Path(__file__).parent / "auth.db"
    if not db_path.exists():
        logger.warning("⚠️  auth.db not found - no data to migrate")
        logger.info("   This is normal for new installations")
        sys.exit(0)
    
    # Run migration
    asyncio.run(run_migration())
