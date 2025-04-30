"use client";

import React from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/lib/translations';

// Frontend URL for redirects
const FRONTEND_URL = "http://localhost:3000";

export function Header() {
  const { t } = useTranslation();
  
  const handleLoginClick = () => {
    window.location.href = `${FRONTEND_URL}/login`;
  };
  
  return (
    <div className="absolute top-0 left-0 right-0 z-10">
      <div className="container mx-auto px-6 py-8">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <div className="relative">
              <div className="absolute -inset-1 bg-white/20 rounded-md blur"></div>
              <Image 
                src="/adaptivecv-logo.jpg" 
                alt="AdaptiveCV Logo" 
                width={76} 
                height={76} 
                className="rounded-md mr-3 relative"
              />
            </div>
            <span className="font-bold text-2xl text-white drop-shadow-sm bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
              {t('common.appName')}
            </span>
          </div>
          
          <Button 
            variant="outline"
            className="bg-white/10 hover:bg-white/20 text-white border-white/20 backdrop-blur-md px-5 py-2 rounded-xl flex items-center gap-1 shadow-lg"
            onClick={handleLoginClick}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14" />
            </svg>
            {t('auth.signIn')}
          </Button>
        </div>
      </div>
    </div>
  );
}