import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import subscriptionService from '@/services/subscriptionService';

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY || 'pk_test_your_stripe_public_key');

interface CheckoutFormProps {
  clientSecret: string;
  onSuccess: () => void;
  onCancel: () => void;
}

const CheckoutForm: React.FC<CheckoutFormProps> = ({ clientSecret, onSuccess, onCancel }) => {
  const { t } = useTranslation();
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const cardElement = elements.getElement(CardElement);
      
      if (!cardElement) {
        throw new Error('Card element not found');
      }

      const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
        payment_method: { card: cardElement }
      });

      if (error) {
        setError(error.message || 'Payment failed');
        toast.error(error.message || 'Payment failed');
      } else if (paymentIntent && paymentIntent.status === 'succeeded') {
        toast.success('Payment successful!');
        onSuccess();
      } else {
        setError('Something went wrong with the payment');
        toast.error('Something went wrong with the payment');
      }
    } catch (err) {
      setError('An error occurred while processing payment');
      toast.error('An error occurred while processing payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <label className="block text-sm font-medium">
          {t('payment.cardDetails')}
        </label>
        <div className="border rounded-md p-4 bg-white">
          <CardElement 
            options={{
              style: {
                base: {
                  fontSize: '16px',
                  color: '#424770',
                  '::placeholder': {
                    color: '#aab7c4',
                  },
                },
                invalid: {
                  color: '#9e2146',
                },
              },
            }}
          />
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </div>

      <div className="flex space-x-4 pt-2">
        <Button 
          type="button" 
          variant="outline" 
          onClick={onCancel}
          disabled={loading}
          className="flex-1"
        >
          {t('common.cancel')}
        </Button>
        <Button 
          type="submit" 
          disabled={!stripe || loading}
          className="flex-1 bg-indigo-600 hover:bg-indigo-700"
        >
          {loading ? t('common.processing') : t('payment.payNow')}
        </Button>
      </div>
    </form>
  );
};

interface PlanSelectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPlanSelected: () => void;
}

const PlanSelectionDialog: React.FC<PlanSelectionDialogProps> = ({ 
  open, 
  onOpenChange,
  onPlanSelected
}) => {
  const { t } = useTranslation();
  const [selectedPlan, setSelectedPlan] = useState<'free' | 'premium' | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelectPlan = async (plan: 'free' | 'premium') => {
    setSelectedPlan(plan);
    
    if (plan === 'free') {
      setLoading(true);
      try {
        await subscriptionService.selectPlan('free');
        toast.success(t('subscription.freePlanSelected'));
        onPlanSelected();
        onOpenChange(false);
      } catch (error) {
        toast.error(t('subscription.errorSelectingPlan'));
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(true);
      try {
        const response = await subscriptionService.selectPlan('premium');
        if (response.success && response.client_secret) {
          setClientSecret(response.client_secret);
        } else {
          throw new Error('No client secret received');
        }
      } catch (error) {
        toast.error(t('subscription.errorSelectingPlan'));
        setSelectedPlan(null);
      } finally {
        setLoading(false);
      }
    }
  };

  const handlePaymentSuccess = () => {
    toast.success(t('subscription.premiumActivated'));
    onPlanSelected();
    onOpenChange(false);
  };

  const handleCancelPayment = () => {
    setSelectedPlan(null);
    setClientSecret(null);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-2xl">{t('subscription.choosePlan')}</DialogTitle>
          <DialogDescription>
            {t('subscription.choosePlanDescription')}
          </DialogDescription>
        </DialogHeader>

        {!selectedPlan || (selectedPlan === 'premium' && !clientSecret) ? (
          <div className="grid gap-6 mt-4">
            {/* Free Plan */}
            <div className="rounded-lg p-6 border hover:border-indigo-300 transition-colors cursor-pointer bg-white">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg">Free Plan</h3>
                  <p className="text-slate-500 font-medium text-2xl mt-2">$0/month</p>
                  <p className="text-slate-600 mt-1">Basic features to get started</p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={() => handleSelectPlan('free')}
                  disabled={loading}
                >
                  {loading && selectedPlan === 'free' ? t('common.loading') : t('subscription.selectPlan')}
                </Button>
              </div>
              
              <Separator className="my-4" />
              
              <ul className="grid gap-2">
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-slate-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Basic CV generation</span>
                </li>
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-slate-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Limited template selection</span>
                </li>
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-slate-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Basic support</span>
                </li>
              </ul>
            </div>

            {/* Premium Plan */}
            <div className="rounded-lg p-6 border-2 border-indigo-500 hover:border-indigo-600 transition-colors cursor-pointer bg-gradient-to-r from-indigo-50 to-purple-50 shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-lg text-indigo-700">Premium Plan</h3>
                    <span className="bg-indigo-100 text-indigo-800 text-xs font-medium px-2.5 py-0.5 rounded">
                      Recommended
                    </span>
                  </div>
                  <p className="text-indigo-600 font-medium text-2xl mt-2">$5/month</p>
                  <p className="text-indigo-600 mt-1">{t('subscription.unlockAllFeatures')}</p>
                </div>
                <Button 
                  onClick={() => handleSelectPlan('premium')}
                  disabled={loading}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  {loading && selectedPlan === 'premium' ? t('common.loading') : t('subscription.selectPlan')}
                </Button>
              </div>
              
              <Separator className="my-4" />
              
              <ul className="grid gap-2">
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-emerald-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Unlimited CV generations</span>
                </li>
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-emerald-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>All templates access</span>
                </li>
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-emerald-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Advanced AI optimization</span>
                </li>
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-emerald-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Priority support</span>
                </li>
                <li className="flex items-center">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-emerald-500 mr-2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Ad-free experience</span>
                </li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {selectedPlan === 'premium' && clientSecret && (
              <div className="mt-4">
                <h3 className="font-semibold text-lg mb-4">{t('payment.completePayment')}</h3>
                <Elements stripe={stripePromise} options={{ clientSecret }}>
                  <CheckoutForm 
                    clientSecret={clientSecret} 
                    onSuccess={handlePaymentSuccess} 
                    onCancel={handleCancelPayment} 
                  />
                </Elements>
              </div>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default PlanSelectionDialog;