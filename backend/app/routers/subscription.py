from fastapi import APIRouter, Depends, HTTPException, Request, Header, Body, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from app.database import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionResponse, SubscriptionCreate, 
    SubscriptionUpdate, BillingInfoUpdate,
    SubscriptionCheckResponse
)
from app.services.stripe_service import StripeService
from app.auth.deps import get_current_user

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)

# Routes for subscription management
@router.post("/select-plan", response_model=Dict[str, Any])
async def select_plan(
    plan_type: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Select a subscription plan (free or premium)
    """
    # User has now selected a plan
    current_user.has_selected_plan = True
    
    # Check if user already has a subscription
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        # Create new subscription
        subscription = Subscription(
            user_id=current_user.id,
            plan_type=plan_type,
            status="active" if plan_type == "free" else "incomplete"
        )
        db.add(subscription)
    else:
        # Update existing subscription
        subscription.plan_type = plan_type
        subscription.status = "active" if plan_type == "free" else "incomplete"
    
    db.commit()
    db.refresh(subscription)
    
    response = {"success": True, "plan_type": plan_type}
    
    # If premium plan selected, create Stripe customer and subscription
    if plan_type == "premium":
        if not subscription.stripe_customer_id:
            # Create Stripe customer
            customer_id = StripeService.create_customer(current_user.email, current_user.name or "")
            subscription.stripe_customer_id = customer_id
            db.commit()
        
        # Create Stripe subscription and get payment info
        subscription_data = StripeService.create_subscription(subscription.stripe_customer_id)
        
        # Update subscription with Stripe data
        subscription.stripe_subscription_id = subscription_data["subscription_id"]
        subscription.current_period_start = subscription_data["current_period_start"]
        subscription.current_period_end = subscription_data["current_period_end"]
        subscription.status = subscription_data["status"]
        db.commit()
        
        # Return client_secret for frontend checkout
        response["client_secret"] = subscription_data["client_secret"]
        response["subscription_id"] = subscription_data["subscription_id"]
    
    return response

@router.get("/check", response_model=SubscriptionCheckResponse)
async def check_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has already selected a subscription plan
    """
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        return {
            "has_selected_plan": current_user.has_selected_plan,
            "plan_type": "free",
            "status": None
        }
    
    return {
        "has_selected_plan": current_user.has_selected_plan,
        "plan_type": subscription.plan_type,
        "status": subscription.status
    }

@router.get("/details", response_model=SubscriptionResponse)
async def get_subscription_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed subscription information
    """
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # If premium subscription, update latest info from Stripe
    if subscription.plan_type == "premium" and subscription.stripe_subscription_id:
        try:
            sub_data = StripeService.get_subscription(subscription.stripe_subscription_id)
            subscription.status = sub_data["status"]
            subscription.current_period_start = sub_data["current_period_start"]
            subscription.current_period_end = sub_data["current_period_end"]
            subscription.cancel_at_period_end = sub_data["cancel_at_period_end"]
            db.commit()
            db.refresh(subscription)
        except HTTPException:
            # Continue with local data if Stripe API call fails
            pass
    
    return subscription

@router.post("/cancel", response_model=Dict[str, Any])
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel premium subscription (at period end)
    """
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.plan_type != "premium":
        raise HTTPException(status_code=400, detail="Only premium subscriptions can be canceled")
    
    if not subscription.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active Stripe subscription found")
    
    # Cancel subscription at Stripe
    result = StripeService.cancel_subscription(subscription.stripe_subscription_id)
    
    # Update local subscription
    subscription.cancel_at_period_end = result["cancel_at_period_end"]
    db.commit()
    
    return {
        "success": True,
        "message": "Subscription will be canceled at the end of the billing period"
    }

@router.post("/reactivate", response_model=Dict[str, Any])
async def reactivate_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reactivate a canceled subscription
    """
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if not subscription.cancel_at_period_end:
        raise HTTPException(status_code=400, detail="Subscription is not scheduled for cancellation")
    
    # Reactivate at Stripe
    result = StripeService.reactivate_subscription(subscription.stripe_subscription_id)
    
    # Update local subscription
    subscription.cancel_at_period_end = result["cancel_at_period_end"]
    db.commit()
    
    return {
        "success": True,
        "message": "Subscription has been reactivated"
    }

@router.put("/billing", response_model=Dict[str, Any])
async def update_billing_info(
    billing_info: BillingInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update billing information
    """
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if not subscription.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")
    
    # Update billing info at Stripe
    billing_dict = billing_info.dict(exclude_unset=True)
    result = StripeService.update_billing_information(subscription.stripe_customer_id, billing_dict)
    
    # Update local subscription with billing details
    if billing_info.name:
        subscription.billing_name = billing_info.name
    
    if billing_info.email:
        subscription.billing_email = billing_info.email
        
    if billing_info.line1:
        subscription.billing_address_line1 = billing_info.line1
        
    if billing_info.line2:
        subscription.billing_address_line2 = billing_info.line2
        
    if billing_info.city:
        subscription.billing_address_city = billing_info.city
        
    if billing_info.state:
        subscription.billing_address_state = billing_info.state
        
    if billing_info.postal_code:
        subscription.billing_address_postal_code = billing_info.postal_code
        
    if billing_info.country:
        subscription.billing_address_country = billing_info.country
    
    db.commit()
    
    return {
        "success": True,
        "message": "Billing information updated successfully"
    }

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def handle_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Handle Stripe webhook events
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_webhook_secret")
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature header")
    
    # Read the request body
    payload = await request.body()
    
    # Process the webhook
    event_data = StripeService.handle_webhook_event(payload, stripe_signature, webhook_secret)
    
    # Handle different webhook events
    if event_data["status"] in ["success", "created", "updated", "deleted"]:
        # Update subscription details based on the webhook
        if "subscription_id" in event_data:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == event_data["subscription_id"]
            ).first()
            
            if subscription:
                # Update from Stripe
                try:
                    sub_data = StripeService.get_subscription(subscription.stripe_subscription_id)
                    subscription.status = sub_data["status"]
                    subscription.current_period_start = sub_data["current_period_start"]
                    subscription.current_period_end = sub_data["current_period_end"]
                    subscription.cancel_at_period_end = sub_data["cancel_at_period_end"]
                    
                    # If subscription was deleted at Stripe, downgrade to free
                    if event_data["status"] == "deleted":
                        subscription.plan_type = "free"
                        subscription.stripe_subscription_id = None
                    
                    db.commit()
                except Exception:
                    # Continue even if update fails
                    pass
    
    return {"status": "success"}