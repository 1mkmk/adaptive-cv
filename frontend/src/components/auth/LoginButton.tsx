import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { Link } from 'react-router';

const LoginButton: React.FC = () => {
  const { t } = useTranslation();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  
  if (isLoading) {
    return (
      <Button variant="ghost" disabled>
        {t('common.loading')}
      </Button>
    );
  }
  
  if (isAuthenticated && user) {
    return (
      <div className="flex items-center gap-2">
        {user.picture && (
          <img
            src={user.picture}
            alt={user.name}
            className="w-8 h-8 rounded-full"
          />
        )}
        <div className="flex flex-col">
          <span className="text-sm font-semibold">{user.name}</span>
          <Button 
            variant="link" 
            className="p-0 h-auto text-xs" 
            onClick={logout}
          >
            {t('auth.signOut')}
          </Button>
        </div>
      </div>
    );
  }
  
  return (
    <Button asChild variant="outline" className="bg-white text-indigo-700 hover:bg-indigo-50 border-indigo-300">
      <Link to="/login">{t('auth.signIn')}</Link>
    </Button>
  );
};

export default LoginButton;