import React from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { Separator } from "@/components/ui/separator";

const Footer: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  return (
    <footer className="bg-indigo-950 text-white py-12 mt-auto">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <h3 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 text-transparent bg-clip-text mb-2">
              AdaptiveCV
            </h3>
            <p className="text-indigo-200 mb-4 max-w-md">
              {t('footer.tagline')}
            </p>
            <div className="flex gap-4">
              <a 
                href="#" 
                className="h-10 w-10 rounded-full bg-indigo-800 flex items-center justify-center hover:bg-indigo-700 transition-colors"
                aria-label="GitHub"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
                  <path d="M9 18c-4.51 2-5-2-7-2"></path>
                </svg>
              </a>
              <a 
                href="#" 
                className="h-10 w-10 rounded-full bg-indigo-800 flex items-center justify-center hover:bg-indigo-700 transition-colors"
                aria-label="Twitter"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
                </svg>
              </a>
              <a 
                href="#" 
                className="h-10 w-10 rounded-full bg-indigo-800 flex items-center justify-center hover:bg-indigo-700 transition-colors"
                aria-label="LinkedIn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                  <rect x="2" y="9" width="4" height="12"></rect>
                  <circle cx="4" cy="4" r="2"></circle>
                </svg>
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4 text-indigo-300 text-lg">{t('footer.navigation')}</h4>
            <ul className="space-y-2 text-indigo-200">
              <li>
                <button 
                  className="hover:text-white transition-colors" 
                  onClick={() => navigate('/')}
                >
                  {t('navigation.home')}
                </button>
              </li>
              <li>
                <button 
                  className="hover:text-white transition-colors" 
                  onClick={() => navigate('/login')}
                >
                  {t('navigation.profile')}
                </button>
              </li>
              <li>
                <button 
                  className="hover:text-white transition-colors" 
                  onClick={() => navigate('/login')}
                >
                  {t('navigation.jobs')}
                </button>
              </li>
              <li>
                <button 
                  className="hover:text-white transition-colors" 
                  onClick={() => navigate('/login')}
                >
                  {t('navigation.templates')}
                </button>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4 text-indigo-300 text-lg">{t('footer.support')}</h4>
            <ul className="space-y-2 text-indigo-200">
              <li>
                <a 
                  href="mailto:support@adaptivecv.app" 
                  className="hover:text-white transition-colors"
                >
                  {t('footer.contact')}
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  className="hover:text-white transition-colors"
                >
                  {t('footer.privacy')}
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  className="hover:text-white transition-colors"
                >
                  {t('footer.terms')}
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  className="hover:text-white transition-colors"
                >
                  {t('footer.faq')}
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <Separator className="my-8 bg-indigo-800" />
        
        <div className="flex flex-col md:flex-row justify-between items-center text-indigo-300 text-sm">
          <p>© {new Date().getFullYear()} AdaptiveCV. {t('footer.copyright')}</p>
          <p className="mt-2 md:mt-0">{t('footer.madewith')} ❤️</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;