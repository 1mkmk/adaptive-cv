import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import subscriptionService, { SubscriptionDetails as SubscriptionDetailsType } from '@/services/subscriptionService';

interface SubscriptionDetailsProps {
  subscription: SubscriptionDetailsType | null;
  onSubscriptionUpdated: () => void;
}

const SubscriptionDetails: React.FC<SubscriptionDetailsProps> = ({ 
  subscription, 
  onSubscriptionUpdated 
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    action: 'cancel' | 'reactivate' | null;
  }>({
    open: false,
    action: null
  });
  
  const isPremium = subscription?.plan_type === 'premium';
  const isCanceled = subscription?.cancel_at_period_end;
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };

  const handleCancelSubscription = async () => {
    try {
      setLoading(true);
      await subscriptionService.cancelSubscription();
      toast.success(t('subscription.cancelSuccess'));
      onSubscriptionUpdated();
      setConfirmDialog({ open: false, action: null });
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast.error(t('subscription.cancelError'));
    } finally {
      setLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      setLoading(true);
      await subscriptionService.reactivateSubscription();
      toast.success(t('subscription.reactivateSuccess'));
      onSubscriptionUpdated();
      setConfirmDialog({ open: false, action: null });
    } catch (error) {
      console.error('Failed to reactivate subscription:', error);
      toast.error(t('subscription.reactivateError'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubscription = async () => {
    try {
      setLoading(true);
      await subscriptionService.createSubscription('premium');
      toast.success(t('subscription.upgradeSuccess'));
      onSubscriptionUpdated();
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast.error(t('subscription.upgradeError'));
    } finally {
      setLoading(false);
    }
  };
  
  const premiumFeatures = [
    'Unlimited CV generations',
    'All templates access',
    'Advanced AI optimization',
    'Priority support',
    'Ad-free experience'
  ];
  
  const freeFeatures = [
    'Basic CV generation',
    'Limited template selection',
    'Basic support'
  ];

  return (
    <>
      <Card className="shadow-sm">
        <CardHeader className="pb-4 border-b">
          <CardTitle className="text-xl text-indigo-800">{t('account.subscriptionPlans')}</CardTitle>
          <CardDescription>{t('account.chooseYourPlan')}</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-6">
            {/* Free Plan */}
            <div className={`rounded-lg p-6 border ${!isPremium ? 'border-slate-200 bg-slate-50 ring-1 ring-slate-200' : 'border-slate-100 bg-white'}`}>
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-lg">Free Plan</h3>
                    {!isPremium && (
                      <Badge className="bg-slate-500">Current Plan</Badge>
                    )}
                  </div>
                  <p className="text-slate-500 font-medium text-2xl mt-2">$0/month</p>
                  <p className="text-slate-600 mt-1">Basic features to get started</p>
                </div>
              </div>
              
              <Separator className="my-4" />
              
              <ul className="grid gap-2 mb-4">
                {freeFeatures.map((feature, index) => (
                  <li key={index} className="flex items-center">
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
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Premium Plan */}
            <div className={`rounded-lg p-6 border ${isPremium ? 'border-indigo-200 bg-gradient-to-r from-indigo-50 to-purple-50 ring-1 ring-indigo-200' : 'border-indigo-100 bg-white'}`}>
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-lg text-indigo-700">Premium Plan</h3>
                    {isPremium && (
                      <Badge className="bg-indigo-500">Current Plan</Badge>
                    )}
                  </div>
                  <p className="text-indigo-600 font-medium text-2xl mt-2">$5/month</p>
                  <p className="text-indigo-600 mt-1">{t('account.unlockAllFeatures')}</p>
                </div>
              </div>
              
              <Separator className="my-4" />
              
              <ul className="grid gap-2 mb-6">
                {premiumFeatures.map((feature, index) => (
                  <li key={index} className="flex items-center">
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
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <div>
                {isPremium ? (
                  <>
                    {isCanceled ? (
                      <div className="space-y-4">
                        <div className="bg-amber-50 p-3 rounded-md border border-amber-200 text-amber-800 text-sm">
                          {t('subscription.canceledInfo', { date: formatDate(subscription?.current_period_end) })}
                        </div>
                        <Button 
                          variant="outline" 
                          className="w-full border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                          onClick={() => setConfirmDialog({ open: true, action: 'reactivate' })}
                          disabled={loading}
                        >
                          {loading ? t('common.loading') : t('subscription.reactivate')}
                        </Button>
                      </div>
                    ) : (
                      <Button 
                        variant="outline" 
                        className="w-full border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                        onClick={() => setConfirmDialog({ open: true, action: 'cancel' })}
                        disabled={loading}
                      >
                        {loading ? t('common.loading') : t('subscription.cancel')}
                      </Button>
                    )}
                  </>
                ) : (
                  <Button 
                    className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 shadow-md hover:shadow-lg"
                    onClick={handleCreateSubscription}
                    disabled={loading}
                  >
                    {loading ? t('common.loading') : t('subscription.upgrade')}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="text-sm text-gray-500 bg-slate-50 rounded-b-lg border-t p-4">
          <p>{t('account.subscriptionDisclaimer')}</p>
        </CardFooter>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => setConfirmDialog({ ...confirmDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmDialog.action === 'cancel' 
                ? t('subscription.confirmCancelTitle') 
                : t('subscription.confirmReactivateTitle')}
            </DialogTitle>
            <DialogDescription>
              {confirmDialog.action === 'cancel' 
                ? t('subscription.confirmCancelDescription', { date: formatDate(subscription?.current_period_end) })
                : t('subscription.confirmReactivateDescription')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setConfirmDialog({ open: false, action: null })}
            >
              {t('common.cancel')}
            </Button>
            <Button 
              variant={confirmDialog.action === 'cancel' ? 'destructive' : 'default'}
              onClick={confirmDialog.action === 'cancel' ? handleCancelSubscription : handleReactivateSubscription}
              disabled={loading}
            >
              {loading 
                ? t('common.loading') 
                : confirmDialog.action === 'cancel'
                  ? t('subscription.confirmCancel')
                  : t('subscription.confirmReactivate')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default SubscriptionDetails;