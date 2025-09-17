from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from server import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Subscription fields
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    subscription_status = Column(String(50), default="active")  # active, cancelled, expired
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Usage limits
    quick_scans_today = Column(Integer, default=0)
    monitoring_terms_count = Column(Integer, default=0)
    
    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    payment_transactions = relationship("PaymentTransaction", back_populates="user", cascade="all, delete-orphan")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    term = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User", back_populates="subscriptions")

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Stripe details
    session_id = Column(String(255), unique=True, nullable=False)
    payment_intent_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=False)
    
    # Transaction details
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(10), default="usd")
    
    # Status tracking
    payment_status = Column(String(50), default="pending")  # pending, paid, failed, cancelled
    transaction_status = Column(String(50), default="initiated")  # initiated, completed, failed
    
    # Metadata
    subscription_tier = Column(String(50), nullable=False)  # pro, enterprise
    metadata = Column(Text, nullable=True)  # JSON storage for additional data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="payment_transactions")