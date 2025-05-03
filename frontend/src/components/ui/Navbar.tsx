import React, { useState } from "react";
import { Link } from "react-router";
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { Button } from "@/components/ui/button";
import LanguageSelector from "@/components/ui/LanguageSelector";
import LogoutConfirmDialog from "@/components/ui/LogoutConfirmDialog";

const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const { user, isAuthenticated, logout } = useAuth();
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  
  // Funkcja generująca inicjały dla avatar placeholder
  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map(part => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };
  
  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4 container mx-auto">
        <div className="mr-6 flex items-center">
          <Link to={isAuthenticated ? "/jobs" : "/login"}>
            <img 
              src="/adaptivecv-logo.jpg" 
              alt="AdaptiveCV Logo" 
              className="h-10 w-auto mr-2 rounded-md" 
            />
          </Link>
          <span className="font-bold text-xl">{t('common.appName')}</span>
        </div>
        
        <NavigationMenu className="flex-1">
          <NavigationMenuList>
            {isAuthenticated && (
              <>
                <NavigationMenuItem>
                  <Link to="/jobs" className={navigationMenuTriggerStyle()}>
                    {t('navigation.jobs')}
                  </Link>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <Link to="/profile" className={navigationMenuTriggerStyle()}>
                    {t('navigation.profile')}
                  </Link>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <Link to="/templates" className={navigationMenuTriggerStyle()}>
                    {t('navigation.templates')}
                  </Link>
                </NavigationMenuItem>
              </>
            )}
          </NavigationMenuList>
        </NavigationMenu>
        
        {/* Right side - Language selector, user name and login */}
        <div className="flex items-center gap-4 ml-auto">
          <LanguageSelector />
          
          {isAuthenticated ? (
            <>
              {user && (
                <Link to="/account-settings" className="flex items-center mr-2 hover:opacity-80 transition-opacity group">
                  {user.picture ? (
                    <img 
                      src={user.picture} 
                      alt={user.name} 
                      className="h-8 w-8 rounded-full mr-2 group-hover:ring-2 group-hover:ring-indigo-400"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full mr-2 bg-indigo-600 flex items-center justify-center text-white text-xs font-medium group-hover:ring-2 group-hover:ring-indigo-400">
                      {getInitials(user.name || 'Guest User')}
                    </div>
                  )}
                  <div>
                    <span className="text-sm font-medium block">
                      {user.name}
                    </span>
                    <span className="text-xs text-gray-500 block">
                      {user.is_guest ? t('common.guestUser') : t('common.clickToSettings')}
                    </span>
                  </div>
                </Link>
              )}
              <Button 
                variant="outline" 
                onClick={() => setLogoutDialogOpen(true)}
              >
                {t('auth.signOut')}
              </Button>
              
              <LogoutConfirmDialog
                open={logoutDialogOpen}
                onOpenChange={setLogoutDialogOpen}
                onConfirm={logout}
              />
            </>
          ) : (
            <Button asChild variant="outline" className="bg-white text-indigo-700 hover:bg-indigo-50 border-indigo-300">
              <Link to="/login">{t('auth.signIn')}</Link>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Navbar;