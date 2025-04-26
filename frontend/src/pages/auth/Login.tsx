import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/context/AuthContext';
import LanguageSelector from '@/components/ui/LanguageSelector';

const Login: React.FC = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const [environment, setEnvironment] = useState<'local' | 'production'>('production');
  
  useEffect(() => {
    // Get environment from Vite environment variables
    const env = import.meta.env.VITE_ENV || 'production';
    console.log("Current environment:", env);
    setEnvironment(env as 'local' | 'production');
  }, []);
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="absolute top-4 right-4">
        <LanguageSelector />
      </div>
      
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-6">
            <img
              src="/adaptivecv-logo.jpg"
              alt="AdaptiveCV Logo"
              className="h-16 w-auto"
            />
          </div>
          <CardTitle className="text-2xl font-bold">{t('auth.signIn')}</CardTitle>
          <CardDescription>
            {t('auth.signInDesc')}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {/* W środowisku produkcyjnym pokazuj Google + opcja gościa */}
          {environment === 'production' && (
            <>
              <Button 
                className="w-full" 
                size="lg" 
                onClick={login}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 48 48"
                  width="24px"
                  height="24px"
                  className="mr-2"
                >
                  <path
                    fill="#FFC107"
                    d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"
                  />
                  <path
                    fill="#FF3D00"
                    d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"
                  />
                  <path
                    fill="#4CAF50"
                    d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"
                  />
                  <path
                    fill="#1976D2"
                    d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"
                  />
                </svg>
                {t('auth.signInWithGoogle')}
              </Button>
              
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-muted-foreground">
                    {t('auth.or')}
                  </span>
                </div>
              </div>
            </>
          )}
          
          {/* Pokazuj opcję gościa w obu środowiskach */}
          <Button
            variant="default"
            className="w-full bg-green-600 hover:bg-green-700"
            onClick={() => {
              // Bezpośrednio przekieruj na endpoint gościa
              window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:3001/api'}/auth/guest`;
            }}
          >
            {t('auth.guestMode')}
          </Button>
        </CardContent>
        <CardFooter className="justify-center text-center text-sm text-gray-500">
          <p>{t('auth.disclaimer')}</p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Login;