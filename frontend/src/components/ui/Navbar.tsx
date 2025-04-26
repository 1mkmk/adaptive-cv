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
  
  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4 container mx-auto">
        <div className="mr-6 flex items-center">
          <Link to="/">
            <img 
              src="/adaptivecv-logo.jpg" 
              alt="AdaptiveCV Logo" 
              className="h-8 w-auto mr-2" 
            />
          </Link>
          <span className="font-bold text-xl">{t('common.appName')}</span>
        </div>
        
        <NavigationMenu className="flex-1">
          <NavigationMenuList>
            <NavigationMenuItem>
              <Link to="/" className={navigationMenuTriggerStyle()}>
                {t('navigation.home')}
              </Link>
            </NavigationMenuItem>
            
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
                <div className="flex items-center mr-2">
                  {user.picture && (
                    <img 
                      src={user.picture} 
                      alt={user.name} 
                      className="h-8 w-8 rounded-full mr-2"
                      referrerPolicy="no-referrer"
                    />
                  )}
                  <span className="text-sm font-medium">
                    {user.name}
                  </span>
                </div>
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