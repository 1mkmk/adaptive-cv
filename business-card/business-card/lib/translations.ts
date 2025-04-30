// filepath: /Users/maciejkasik/Desktop/adaptive-cv/business-card/business-card/lib/translations.ts
import { useState, useMemo } from 'react';

// Simple translations helper since we don't have full i18n setup
const translations = {
  en: {
    'common.appName': 'AdaptiveCV',
    'footer.tagline': 'Tailored CVs for every job',
    'home.title': 'AI-Powered CV Generation',
    'home.subtitle': 'Tailored to Every Job Application',
    'profile.profileDesc': 'Create Profile',
    'jobs.generateCV': 'Generate CV',
    'home.features.title': 'How It Works',
    'home.features.aiTailored': 'AI-Tailored CVs',
    'home.features.aiTailoredDesc': 'Our AI analyzes job descriptions and matches your skills perfectly.',
    'home.features.templates': 'Beautiful Templates',
    'home.features.templatesDesc': 'Choose from professionally designed CV templates that stand out.',
    'home.getStarted': 'Get Started',
    'footer.navigation': 'Navigation',
    'navigation.home': 'Home',
    'navigation.profile': 'Profile',
    'navigation.jobs': 'Jobs',
    'navigation.templates': 'Templates',
    'footer.madewith': 'Made with',
    'auth.signIn': 'Sign In'
  },
  // Add other languages here if needed
};

export type LanguageCode = keyof typeof translations;
export type TranslationKey = keyof typeof translations['en'];

export function useTranslation(lang: LanguageCode = 'en') {
  const [language] = useState<LanguageCode>(lang);

  const t = useMemo(() => {
    return (key: string) => {
      return translations[language][key as TranslationKey] || key;
    };
  }, [language]);

  return { t, language };
}