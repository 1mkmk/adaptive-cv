from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BillingAddressBase(BaseModel):
    name: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class SubscriptionBase(BaseModel):
    plan_type: str = "free"

class SubscriptionCreate(SubscriptionBase):
    user_id: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
class BillingInfoUpdate(BillingAddressBase):
    email: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    plan_type: Optional[str] = None
    status: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_state: Optional[str] = None
    billing_address_postal_code: Optional[str] = None
    billing_address_country: Optional[str] = None

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_type: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Billing information
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_state: Optional[str] = None
    billing_address_postal_code: Optional[str] = None
    billing_address_country: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class SubscriptionCheckResponse(BaseModel):
    has_selected_plan: bool
    plan_type: Optional[str] = "free"
    status: Optional[str] = None