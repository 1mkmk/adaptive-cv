// filepath: /Users/maciejkasik/Desktop/adaptive-cv/business-card/business-card/components/ui/LanguageSelector.tsx
"use client"

import React from 'react';
import { Button } from "@/components/ui/button";

// This is a simplified version of the LanguageSelector for the business-card project
// In a real app, you'd integrate this with i18n

const LanguageSelector: React.FC = () => {
  // Mock function to switch languages
  const changeLanguage = (lng: string) => {
    console.log(`Language changed to: ${lng}`);
    // Here would be the actual language change logic with i18n
  };

  return (
    <div className="flex gap-1">
      <Button 
        variant="ghost" 
        size="sm" 
        className="w-8 h-8 p-0 rounded-full" 
        onClick={() => changeLanguage('en')}
      >
        EN
      </Button>
      <Button 
        variant="ghost" 
        size="sm" 
        className="w-8 h-8 p-0 rounded-full" 
        onClick={() => changeLanguage('pl')}
      >
        PL
      </Button>
    </div>
  );
};

export default LanguageSelector;