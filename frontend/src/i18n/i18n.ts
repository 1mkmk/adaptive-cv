import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import all locale files
import en from './locales/en.json';
import pl from './locales/pl.json';
import de from './locales/de.json';
import fr from './locales/fr.json';
import es from './locales/es.json';

// Resources object with translations
const resources = {
  en: { translation: en },
  pl: { translation: pl },
  de: { translation: de },
  fr: { translation: fr },
  es: { translation: es }
};

// Initialize i18next
i18n
  .use(LanguageDetector) // Detect language from browser
  .use(initReactI18next) // Initialize react-i18next
  .init({
    resources,
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    interpolation: {
      escapeValue: false, // React already safes from XSS
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;