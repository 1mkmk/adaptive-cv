import stripe
import os
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.models.user import User
from typing import Dict, Any, Optional

# Initialize Stripe with the API key
stripe.api_key = os.getenv("STRIPE_API_KEY", "sk_test_your_stripe_test_key")
PREMIUM_PRICE_ID = os.getenv("STRIPE_PREMIUM_PRICE_ID", "price_your_premium_price_id")

class StripeService:
    @staticmethod
    def create_customer(email: str, name: str) -> str:
        """Create a new customer in Stripe"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error creating Stripe customer: {str(e)}")
    
    @staticmethod
    def create_subscription(customer_id: str, price_id: str = PREMIUM_PRICE_ID) -> Dict[str, Any]:
        """Create a subscription for a customer"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
                "status": subscription.status,
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error creating subscription: {str(e)}")
    
    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """Get a subscription by ID"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error retrieving subscription: {str(e)}")
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription (at period end)"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return {
                "id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error canceling subscription: {str(e)}")
    
    @staticmethod
    def reactivate_subscription(subscription_id: str) -> Dict[str, Any]:
        """Reactivate a subscription that was set to cancel at period end"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return {
                "id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error reactivating subscription: {str(e)}")
    
    @staticmethod
    def update_billing_information(customer_id: str, billing_info: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Update billing information for a customer"""
        try:
            # Extract billing details
            address = {
                "line1": billing_info.get("line1"),
                "line2": billing_info.get("line2"),
                "city": billing_info.get("city"),
                "state": billing_info.get("state"),
                "postal_code": billing_info.get("postal_code"),
                "country": billing_info.get("country"),
            }
            
            # Remove None values
            address = {k: v for k, v in address.items() if v is not None}
            
            update_data = {}
            if address:
                update_data["address"] = address
            
            if billing_info.get("name"):
                update_data["name"] = billing_info.get("name")
            
            if billing_info.get("email"):
                update_data["email"] = billing_info.get("email")
                
            customer = stripe.Customer.modify(
                customer_id,
                **update_data
            )
            
            return {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "address": customer.address
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error updating billing information: {str(e)}")
    
    @staticmethod
    def create_payment_intent(amount: int, currency: str = "usd") -> Dict[str, Any]:
        """Create a payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
            )
            return {
                "client_secret": intent.client_secret,
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error creating payment intent: {str(e)}")
    
    @staticmethod
    def handle_webhook_event(payload: bytes, sig_header: str, webhook_secret: str) -> Dict[str, Any]:
        """Handle webhook events from Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle the event
            if event["type"] == "invoice.paid":
                # Handle successful payment
                invoice = event["data"]["object"]
                return {"status": "success", "invoice_id": invoice["id"]}
            elif event["type"] == "invoice.payment_failed":
                # Handle failed payment
                invoice = event["data"]["object"]
                return {"status": "failed", "invoice_id": invoice["id"]}
            elif event["type"] == "customer.subscription.created":
                # Handle subscription created
                subscription = event["data"]["object"]
                return {"status": "created", "subscription_id": subscription["id"]}
            elif event["type"] == "customer.subscription.updated":
                # Handle subscription updated
                subscription = event["data"]["object"]
                return {"status": "updated", "subscription_id": subscription["id"]}
            elif event["type"] == "customer.subscription.deleted":
                # Handle subscription canceled
                subscription = event["data"]["object"]
                return {"status": "deleted", "subscription_id": subscription["id"]}
                
            # Return event information for unhandled events    
            return {"status": "unhandled", "type": event["type"], "id": event["id"]}
            
        except (stripe.error.SignatureVerificationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid webhook signature: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")