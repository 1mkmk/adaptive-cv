from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan_type = Column(String, default="free")  # free, premium
    status = Column(String, default="active")  # active, canceled, past_due
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    # Billing related information
    billing_name = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)
    billing_address_line1 = Column(String, nullable=True)
    billing_address_line2 = Column(String, nullable=True)
    billing_address_city = Column(String, nullable=True)
    billing_address_state = Column(String, nullable=True)
    billing_address_postal_code = Column(String, nullable=True)
    billing_address_country = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Subscription {self.id} - User: {self.user_id} - Plan: {self.plan_type}>"