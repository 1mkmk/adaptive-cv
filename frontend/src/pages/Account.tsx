import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import SubscriptionDetails from '@/components/subscription/SubscriptionDetails';
import BillingInfoForm from '@/components/subscription/BillingInfoForm';
import subscriptionService, { SubscriptionDetails as SubscriptionDetailsType } from '@/services/subscriptionService';

const Account: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [subscription, setSubscription] = useState<SubscriptionDetailsType | null>(null);
  const [isLoadingSubscription, setIsLoadingSubscription] = useState(true);
  
  const currentPlan = subscription?.plan_type === 'premium' ? 'Premium' : 'Free';
  
  // Function to generate initials for avatar placeholder
  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map(part => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  // Load subscription details on mount
  useEffect(() => {
    const loadSubscriptionDetails = async () => {
      try {
        setIsLoadingSubscription(true);
        const subscriptionData = await subscriptionService.getSubscriptionDetails();
        setSubscription(subscriptionData);
      } catch (error) {
        console.error('Error loading subscription details:', error);
        toast.error(t('account.errorLoadingSubscription'));
      } finally {
        setIsLoadingSubscription(false);
      }
    };

    if (user && !user.is_guest) {
      loadSubscriptionDetails();
    } else {
      setIsLoadingSubscription(false);
    }
  }, [user, t]);

  const handleSubscriptionUpdated = async () => {
    try {
      setIsLoadingSubscription(true);
      const subscriptionData = await subscriptionService.getSubscriptionDetails();
      setSubscription(subscriptionData);
      toast.success(t('account.subscriptionUpdated'));
    } catch (error) {
      console.error('Error refreshing subscription details:', error);
    } finally {
      setIsLoadingSubscription(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      toast.error("New passwords don't match. Please try again.");
      return;
    }
    
    setLoading(true);
    try {
      // This would be implemented via API
      await new Promise(resolve => setTimeout(resolve, 1000)); // Network delay simulation
      toast.success("Your password has been changed successfully.");
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      toast.error("Failed to change password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-10 max-w-4xl">
      <Card className="shadow-sm mb-8">
        <CardHeader className="pb-4 border-b">
          <CardTitle className="text-2xl text-indigo-800">{t('account.profile')}</CardTitle>
          <CardDescription>{t('account.manageYourProfile')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="flex flex-col items-center">
              {user?.picture ? (
                <img 
                  src={user.picture} 
                  alt={user.name} 
                  className="h-24 w-24 rounded-full border-2 border-indigo-200"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="h-24 w-24 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl font-medium shadow-md">
                  {getInitials(user?.name || 'Guest User')}
                </div>
              )}
              
              <div className="mt-4 flex flex-row gap-2 items-center">
                <Badge variant="outline" className={`${currentPlan === 'Premium' 
                  ? 'bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-700 border-emerald-200' 
                  : 'bg-gradient-to-r from-gray-50 to-slate-50 text-slate-700 border-slate-200'} px-3 py-1`}>
                  <span className={`w-2 h-2 rounded-full mr-1.5 inline-block ${currentPlan === 'Premium' ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                  {currentPlan} Plan
                </Badge>
                
                {user?.is_guest && (
                  <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 px-3 py-1">
                    Guest User
                  </Badge>
                )}
              </div>
            </div>
            
            <div className="flex-1 text-center sm:text-left">
              <h2 className="text-xl font-semibold mb-1">{user?.name}</h2>
              <p className="text-gray-500 mb-3">{user?.email}</p>
              
              <div className="bg-indigo-50 rounded-lg p-4 mt-2 border border-indigo-100">
                <h3 className="font-medium text-indigo-800 mb-2">Current Plan: {currentPlan}</h3>
                <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                  <div className="text-sm text-slate-600">
                    {currentPlan === 'Premium' ? (
                      <p>Your Premium plan is active. Enjoy all features!</p>
                    ) : (
                      <p>You're on the Free plan. Upgrade to Premium for more features.</p>
                    )}
                  </div>
                  <Button 
                    size="sm" 
                    variant={currentPlan === 'Premium' ? 'outline' : 'default'}
                    className={currentPlan === 'Premium' ? '' : 'bg-indigo-600 hover:bg-indigo-700'}
                    onClick={() => document.getElementById('subscription-tab')?.click()}
                  >
                    {currentPlan === 'Premium' ? 'Manage Subscription' : 'Upgrade Plan'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Tabs defaultValue="subscription" className="w-full">
        <TabsList className="grid grid-cols-3 mb-6 rounded-lg bg-slate-100 p-1">
          <TabsTrigger id="subscription-tab" value="subscription" className="rounded-md data-[state=active]:bg-white data-[state=active]:shadow-sm">
            {t('account.subscription')}
          </TabsTrigger>
          <TabsTrigger value="billing" className="rounded-md data-[state=active]:bg-white data-[state=active]:shadow-sm">
            {t('account.billing')}
          </TabsTrigger>
          <TabsTrigger value="security" className="rounded-md data-[state=active]:bg-white data-[state=active]:shadow-sm">
            {t('account.security')}
          </TabsTrigger>
        </TabsList>
        
        {/* Tab content - Subscription */}
        <TabsContent value="subscription">
          {isLoadingSubscription ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : (
            <>
              {user && !user.is_guest ? (
                <SubscriptionDetails 
                  subscription={subscription}
                  onSubscriptionUpdated={handleSubscriptionUpdated}
                />
              ) : (
                <Card className="shadow-sm">
                  <CardHeader className="pb-4 border-b">
                    <CardTitle className="text-xl text-indigo-800">{t('account.subscriptionPlans')}</CardTitle>
                    <CardDescription>{t('account.chooseYourPlan')}</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <div className="bg-amber-50 p-5 rounded-xl mb-6 text-amber-700 border border-amber-200 shadow-sm">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <h3 className="font-medium text-lg mb-3">{t('account.guestUserNotice')}</h3>
                      <p>{t('account.subscriptionUnavailable')}</p>
                    </div>
                    <Button 
                      className="bg-indigo-600 hover:bg-indigo-700 shadow-md px-8"
                      onClick={() => window.location.href = '/login'}
                    >
                      {t('account.switchToRegularAccount')}
                    </Button>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* Tab content - Billing Information */}
        <TabsContent value="billing">
          {isLoadingSubscription ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : (
            <>
              {user && !user.is_guest ? (
                <BillingInfoForm 
                  subscription={subscription}
                  onBillingInfoUpdated={handleSubscriptionUpdated}
                />
              ) : (
                <Card className="shadow-sm">
                  <CardHeader className="pb-4 border-b">
                    <CardTitle className="text-xl text-indigo-800">{t('account.billingInformation')}</CardTitle>
                    <CardDescription>{t('account.updateBillingDetails')}</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <div className="bg-amber-50 p-5 rounded-xl mb-6 text-amber-700 border border-amber-200 shadow-sm">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <h3 className="font-medium text-lg mb-3">{t('account.guestUserNotice')}</h3>
                      <p>{t('account.billingUnavailable')}</p>
                    </div>
                    <Button 
                      className="bg-indigo-600 hover:bg-indigo-700 shadow-md px-8"
                      onClick={() => window.location.href = '/login'}
                    >
                      {t('account.switchToRegularAccount')}
                    </Button>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
        
        {/* Tab content - Security and account settings */}
        <TabsContent value="security">
          <Card className="shadow-sm">
            <CardHeader className="pb-4 border-b">
              <CardTitle className="text-xl text-indigo-800">{t('account.security')}</CardTitle>
              <CardDescription>{t('account.manageYourSecurity')}</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {!user?.is_guest ? (
                <form onSubmit={handlePasswordChange} className="space-y-5 max-w-md mx-auto">
                  <div className="space-y-2">
                    <Label htmlFor="current-password" className="text-sm font-medium">
                      {t('account.currentPassword')}
                    </Label>
                    <Input 
                      id="current-password" 
                      type="password" 
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                      className="border-slate-200 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                    />
                  </div>
                  
                  <Separator className="my-4" />
                  
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="new-password" className="text-sm font-medium">
                        {t('account.newPassword')}
                      </Label>
                      <Input 
                        id="new-password" 
                        type="password" 
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        className="border-slate-200 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password" className="text-sm font-medium">
                        {t('account.confirmNewPassword')}
                      </Label>
                      <Input 
                        id="confirm-password" 
                        type="password" 
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="border-slate-200 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                      />
                    </div>
                  </div>
                  
                  <Button 
                    type="submit"
                    disabled={loading}
                    className="w-full mt-6 bg-indigo-600 hover:bg-indigo-700 shadow-md"
                  >
                    {loading ? t('common.loading') : t('account.changePassword')}
                  </Button>
                </form>
              ) : (
                <div className="text-center py-8 max-w-md mx-auto">
                  <div className="bg-amber-50 p-5 rounded-xl mb-6 text-amber-700 border border-amber-200 shadow-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="font-medium text-lg mb-3">{t('account.guestUserNotice')}</h3>
                    <p>{t('account.passwordChangeUnavailable')}</p>
                  </div>
                  <Button 
                    className="bg-indigo-600 hover:bg-indigo-700 shadow-md px-8"
                    onClick={() => window.location.href = '/login'}
                  >
                    {t('account.switchToRegularAccount')}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Account;