import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import subscriptionService from '@/services/subscriptionService';

interface SubscriptionPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPlanSelected: () => void;
}

const SubscriptionPlanDialog: React.FC<SubscriptionPlanDialogProps> = ({
  open,
  onOpenChange,
  onPlanSelected
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<'free' | 'premium'>('free');

  const handleSelectPlan = async () => {
    try {
      setLoading(true);
      
      if (selectedPlan === 'premium') {
        await subscriptionService.createSubscription('premium');
        toast.success(t('subscription.premiumPlanActivated'));
      } else {
        // No action needed for free plan, just close the dialog
        toast.success(t('subscription.freePlanActivated'));
      }
      
      onPlanSelected();
      onOpenChange(false);
    } catch (error) {
      console.error('Error selecting plan:', error);
      toast.error(t('subscription.errorSelectingPlan'));
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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-xl text-center">{t('subscription.choosePlan')}</DialogTitle>
          <DialogDescription className="text-center">
            {t('subscription.choosePlanDescription')}
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-6">
          {/* Free Plan */}
          <div 
            className={`rounded-lg p-5 border cursor-pointer transition-all ${
              selectedPlan === 'free' 
                ? 'border-slate-300 bg-slate-50 ring-2 ring-slate-300 shadow-md' 
                : 'border-slate-200 hover:border-slate-300'
            }`}
            onClick={() => setSelectedPlan('free')}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-lg">Free Plan</h3>
                  <Badge className="bg-slate-500">Basic</Badge>
                </div>
                <p className="text-slate-500 font-bold text-2xl mt-2">$0/month</p>
                <p className="text-slate-600 mt-1 mb-3">Basic features to get started</p>
              </div>
            </div>
            
            <Separator className="my-3" />
            
            <ul className="grid gap-2 mt-3">
              {freeFeatures.map((feature, index) => (
                <li key={index} className="flex items-center text-sm">
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
          <div 
            className={`rounded-lg p-5 border cursor-pointer transition-all ${
              selectedPlan === 'premium' 
                ? 'border-indigo-300 bg-gradient-to-r from-indigo-50 to-purple-50 ring-2 ring-indigo-400 shadow-md' 
                : 'border-indigo-200 hover:border-indigo-300 bg-white'
            }`}
            onClick={() => setSelectedPlan('premium')}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-lg text-indigo-700">Premium Plan</h3>
                  <Badge className="bg-indigo-500">Recommended</Badge>
                </div>
                <p className="text-indigo-600 font-bold text-2xl mt-2">$5/month</p>
                <p className="text-indigo-600 mt-1 mb-3">{t('subscription.unlockAllFeatures')}</p>
              </div>
            </div>
            
            <Separator className="my-3" />
            
            <ul className="grid gap-2 mt-3">
              {premiumFeatures.map((feature, index) => (
                <li key={index} className="flex items-center text-sm">
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
          </div>
        </div>
        
        <DialogFooter>
          <div className="w-full flex flex-col sm:flex-row gap-3 justify-end">
            <Button 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="sm:order-1"
            >
              {t('common.decideLater')}
            </Button>
            <Button 
              onClick={handleSelectPlan}
              disabled={loading}
              className={
                selectedPlan === 'premium' 
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700' 
                  : ''
              }
            >
              {loading 
                ? t('common.loading') 
                : selectedPlan === 'premium' 
                  ? t('subscription.activatePremium') 
                  : t('subscription.startWithFree')}
            </Button>
          </div>
        </DialogFooter>
        <p className="text-xs text-center text-gray-500 mt-4">
          {t('subscription.dialogDisclaimer')}
        </p>
      </DialogContent>
    </Dialog>
  );
};

export default SubscriptionPlanDialog;