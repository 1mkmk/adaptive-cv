import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import SubscriptionPlanDialog from './SubscriptionPlanDialog';
import subscriptionService from '@/services/subscriptionService';

interface SubscriptionManagerProps {
  children: React.ReactNode;
}

const SubscriptionManager: React.FC<SubscriptionManagerProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [showPlanDialog, setShowPlanDialog] = useState(false);
  const [hasCheckedSubscription, setHasCheckedSubscription] = useState(false);
  
  useEffect(() => {
    const checkSubscription = async () => {
      try {
        // Skip for guest users and when not authenticated
        if (!isAuthenticated || (user && user.is_guest)) {
          setHasCheckedSubscription(true);
          return;
        }
        
        // Check if user has a subscription plan selected
        const userHasPlanKey = `user_${user?.id}_has_plan`;
        const userHasPlan = localStorage.getItem(userHasPlanKey);
        
        if (userHasPlan) {
          setHasCheckedSubscription(true);
          return;
        }
        
        // Try to load subscription details
        const subscription = await subscriptionService.getSubscriptionDetails()
          .catch(() => null);
        
        if (subscription) {
          // User has a subscription, mark as having a plan
          localStorage.setItem(userHasPlanKey, 'true');
          setHasCheckedSubscription(true);
        } else {
          // User doesn't have a plan selected yet, show the dialog
          setShowPlanDialog(true);
          setHasCheckedSubscription(true);
        }
      } catch (error) {
        console.error('Error checking subscription status:', error);
        setHasCheckedSubscription(true);
      }
    };
    
    if (isAuthenticated && user && !hasCheckedSubscription) {
      checkSubscription();
    }
  }, [isAuthenticated, user, hasCheckedSubscription]);
  
  const handlePlanSelected = () => {
    if (user) {
      localStorage.setItem(`user_${user.id}_has_plan`, 'true');
    }
  };
  
  return (
    <>
      {children}
      
      {isAuthenticated && user && !user.is_guest && (
        <SubscriptionPlanDialog
          open={showPlanDialog}
          onOpenChange={setShowPlanDialog}
          onPlanSelected={handlePlanSelected}
        />
      )}
    </>
  );
};

export default SubscriptionManager;