import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import subscriptionService, { SubscriptionDetails, BillingInfo } from '@/services/subscriptionService';

interface BillingInfoFormProps {
  subscription: SubscriptionDetails | null;
  onBillingInfoUpdated: () => void;
}

const BillingInfoForm: React.FC<BillingInfoFormProps> = ({ subscription, onBillingInfoUpdated }) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [billingInfo, setBillingInfo] = useState<BillingInfo>({
    name: '',
    email: '',
    line1: '',
    city: '',
    country: '',
  });

  useEffect(() => {
    // Populate form with existing billing info if available
    if (subscription) {
      setBillingInfo({
        name: subscription.billing_name || '',
        email: subscription.billing_email || '',
        line1: subscription.billing_address_line1 || '',
        line2: subscription.billing_address_line2,
        city: subscription.billing_address_city || '',
        state: subscription.billing_address_state,
        postal_code: subscription.billing_address_postal_code,
        country: subscription.billing_address_country || '',
      });
    }
  }, [subscription]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setBillingInfo(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await subscriptionService.updateBillingInfo(billingInfo);
      toast.success(t('billing.updateSuccess'));
      onBillingInfoUpdated();
    } catch (error) {
      console.error('Failed to update billing info:', error);
      toast.error(t('billing.updateError'));
    } finally {
      setLoading(false);
    }
  };

  if (!subscription) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('billing.information')}</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{t('billing.noSubscriptionFound')}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('billing.information')}</CardTitle>
        <CardDescription>
          {t('billing.updateDetails')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">{t('billing.fullName')}</Label>
                <Input
                  id="name"
                  name="name"
                  value={billingInfo.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">{t('billing.email')}</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={billingInfo.email}
                  onChange={handleInputChange}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="line1">{t('billing.addressLine1')}</Label>
              <Input
                id="line1"
                name="line1"
                value={billingInfo.line1}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="line2">{t('billing.addressLine2')}</Label>
              <Input
                id="line2"
                name="line2"
                value={billingInfo.line2 || ''}
                onChange={handleInputChange}
              />
              <p className="text-sm text-muted-foreground">{t('common.optional')}</p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="city">{t('billing.city')}</Label>
                <Input
                  id="city"
                  name="city"
                  value={billingInfo.city}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="state">{t('billing.state')}</Label>
                <Input
                  id="state"
                  name="state"
                  value={billingInfo.state || ''}
                  onChange={handleInputChange}
                />
                <p className="text-sm text-muted-foreground">{t('common.optional')}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="postal_code">{t('billing.postalCode')}</Label>
                <Input
                  id="postal_code"
                  name="postal_code"
                  value={billingInfo.postal_code || ''}
                  onChange={handleInputChange}
                />
                <p className="text-sm text-muted-foreground">{t('common.optional')}</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">{t('billing.country')}</Label>
                <Input
                  id="country"
                  name="country"
                  value={billingInfo.country}
                  onChange={handleInputChange}
                  required
                />
              </div>
            </div>
          </div>

          <Button 
            type="submit" 
            disabled={loading} 
            className="w-full sm:w-auto"
          >
            {loading ? t('common.saving') : t('billing.saveInformation')}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default BillingInfoForm;