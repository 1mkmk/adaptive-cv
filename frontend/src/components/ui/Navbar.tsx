import React from "react";
import { Link } from "react-router";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { cn } from "@/lib/utils";

const Navbar: React.FC = () => {
  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4 container mx-auto">
        <div className="mr-6 flex items-center">
          <img 
            src="/adaptivecv-logo.jpg" 
            alt="AdaptiveCV Logo" 
            className="h-8 w-auto mr-2" 
          />
          <span className="font-bold text-xl">AdaptiveCV</span>
        </div>
        
        <NavigationMenu>
          <NavigationMenuList>
            <NavigationMenuItem>
              <Link to="/" className={navigationMenuTriggerStyle()}>
                Home
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Link to="/jobs" className={navigationMenuTriggerStyle()}>
                Jobs
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Link to="/profile" className={navigationMenuTriggerStyle()}>
                Profile
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Link to="/templates" className={navigationMenuTriggerStyle()}>
                Templates
              </Link>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
      </div>
    </div>
  );
};

export default Navbar;