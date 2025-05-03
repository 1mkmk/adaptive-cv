import { fetchApi } from './api';

export interface SubscriptionDetails {
  id: string;
  status: string;
  plan_type: 'free' | 'premium';
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  billing_name?: string;
  billing_email?: string;
  billing_address_line1?: string;
  billing_address_line2?: string;
  billing_address_city?: string;
  billing_address_state?: string;
  billing_address_postal_code?: string;
  billing_address_country?: string;
}

export interface BillingInfo {
  name: string;
  email: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postal_code?: string;
  country: string;
}

const subscriptionService = {
  /**
   * Get current subscription details for the user
   */
  getSubscriptionDetails: async (): Promise<SubscriptionDetails> => {
    return await fetchApi('/subscriptions/current');
  },

  /**
   * Create a new subscription for the user
   */
  createSubscription: async (planId: string): Promise<SubscriptionDetails> => {
    return await fetchApi('/subscriptions/create', {
      method: 'POST',
      body: JSON.stringify({ planId }),
    });
  },
  
  /**
   * Cancel the user's current subscription at the end of the billing period
   */
  cancelSubscription: async (): Promise<SubscriptionDetails> => {
    return await fetchApi('/subscriptions/cancel', {
      method: 'POST',
    });
  },
  
  /**
   * Reactivate a canceled subscription that hasn't yet expired
   */
  reactivateSubscription: async (): Promise<SubscriptionDetails> => {
    return await fetchApi('/subscriptions/reactivate', {
      method: 'POST',
    });
  },
  
  /**
   * Update the billing information for the subscription
   */
  updateBillingInfo: async (billingInfo: BillingInfo): Promise<void> => {
    await fetchApi('/subscriptions/billing-info', {
      method: 'PUT',
      body: JSON.stringify(billingInfo),
    });
  },
};

export default subscriptionService;