import React from 'react';
import Image from 'next/image';
import { Separator } from "@/components/ui/separator";
import { useTranslation } from "@/lib/translations";

// Frontend URL for redirects - zaktualizowane do naszego proxy
const FRONTEND_URL = "http://localhost:3001/app";

export function Footer() {
  const { t } = useTranslation();
  
  const handleNavigation = (path: string) => {
    window.location.href = `${FRONTEND_URL}${path}`;
  };
  
  return (
    <footer className="bg-gradient-to-b from-indigo-900 to-slate-900 text-white pt-16 pb-8 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Cpath d=%22M1 1h2v2H1z%22 fill=%22%23fff%22 opacity=%22.05%22/%3E%3C/svg%3E')] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>
      <div className="absolute -top-24 right-0 w-96 h-96 rounded-full bg-purple-600/10 blur-3xl"></div>
      <div className="absolute -bottom-20 left-20 w-72 h-72 rounded-full bg-indigo-600/10 blur-3xl"></div>
      
      <div className="container mx-auto px-6 relative">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-8 md:mb-0">
            <div className="flex items-center mb-3">
              <div className="relative mr-3">
                <div className="absolute -inset-1 bg-white/10 rounded-md blur"></div>
                <Image 
                  src="/adaptivecv-logo.jpg" 
                  alt="AdaptiveCV Logo" 
                  width={80} 
                  height={80} 
                  className="rounded-md relative"
                />
              </div>
              <h3 className="text-2xl font-bold">
                <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">AdaptiveCV</span>
              </h3>
            </div>
            <p className="text-indigo-200">Tailor your CV for every opportunity</p>
          </div>
          <div className="flex gap-8 text-indigo-200">
            <button 
              onClick={() => handleNavigation('/login')} 
              className="hover:text-white transition-colors flex items-center gap-1 hover:underline"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14" />
              </svg>
              Sign In
            </button>
            <a 
              href="https://github.com/maciejkasik" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="hover:text-white transition-colors flex items-center gap-1 hover:underline"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z" />
              </svg>
              GitHub
            </a>
            <a 
              href="mailto:contact@example.com" 
              className="hover:text-white transition-colors flex items-center gap-1 hover:underline"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Contact
            </a>
          </div>
        </div>
        <Separator className="my-8 bg-indigo-800/50" />
        <div className="text-center text-indigo-300/70 text-sm">
          <p>© {new Date().getFullYear()} AdaptiveCV. A personal project by Maciej Kasik.</p>
          <p className="mt-2 flex justify-center items-center gap-1">
            {t('footer.madewith')} <span className="text-red-400 animate-pulse">❤️</span> 
            <span className="text-indigo-300/40 mx-2">|</span> 
            <span className="flex items-center gap-1">
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Powered by AI</span>
            </span>
          </p>
        </div>
      </div>
    </footer>
  );
}