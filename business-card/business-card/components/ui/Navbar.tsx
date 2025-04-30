"use client"

import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { Button } from "@/components/ui/button";
import LanguageSelector from "@/components/ui/LanguageSelector";

// Frontend URL - change this to the actual URL of your frontend app
const FRONTEND_URL = "http://localhost:3000";

const Navbar: React.FC = () => {
  // Mock translation function, replace with proper i18n in a real app
  const t = (key: string) => {
    const translations: { [key: string]: string } = {
      'common.appName': 'AdaptiveCV',
      'navigation.home': 'Home',
      'auth.signIn': 'Sign In'
    };
    return translations[key] || key;
  };
  
  const handleLoginClick = () => {
    // Redirect to the frontend app's login page
    window.location.href = `${FRONTEND_URL}/login`;
  };
  
  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4 container mx-auto">
        <div className="mr-6 flex items-center">
          <Link href="/">
            <div className="flex items-center">
              <Image 
                src="/adaptivecv-logo.jpg" 
                alt="AdaptiveCV Logo" 
                width={64}
                height={64}
                className="rounded-xs mr-2"
              />
              <span className="font-bold text-xl">{t('common.appName')}</span>
            </div>
          </Link>
        </div>
        
        <NavigationMenu className="flex-1">
          <NavigationMenuList>
            {/* Only Home tab displayed */}
            <NavigationMenuItem>
              <Link href="/" className={navigationMenuTriggerStyle()}>
                {t('navigation.home')}
              </Link>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
        
        {/* Right side - Language selector and login button */}
        <div className="flex items-center gap-4 ml-auto">
          <LanguageSelector />
          
          <Button 
            variant="outline" 
            className="bg-white text-indigo-700 hover:bg-indigo-50 border-indigo-300"
            onClick={handleLoginClick}
          >
            {t('auth.signIn')}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Navbar;