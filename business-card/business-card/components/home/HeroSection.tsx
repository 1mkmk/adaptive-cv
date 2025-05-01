"use client";

import { Button } from "@/components/ui/button";
import { useTranslation } from "@/lib/translations";
import { Header } from "./Header";
import { useEffect, useState } from "react";

// Frontend URL - bezpośredni adres do frontendu
const FRONTEND_URL = "http://localhost:5173";

export function HeroSection() {
  const { t } = useTranslation();
  // Stan do śledzenia pozycji scrollowania dla efektu parallax
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      // Wykorzystanie requestAnimationFrame dla lepszej wydajności
      window.requestAnimationFrame(() => {
        setScrollY(window.scrollY);
      });
    };

    // Dodanie event listenera dla scrollowania
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Usunięcie event listenera przy czyszczeniu
    return () => window.removeEventListener('scroll', handleScroll);
  }, []); // Pusta tablica zależności oznacza, że ten useEffect działa tylko raz przy montowaniu komponentu

  const handleButtonClick = (path: string) => {
    window.location.href = `${FRONTEND_URL}${path}`;
  };

  return (
    <div className="bg-gradient-to-r from-indigo-900 via-purple-800 to-fuchsia-700 text-white py-32 min-h-[100vh] flex flex-col relative overflow-hidden">
      {/* Enhanced background with overlay effects */}
      <div 
        className="absolute inset-0 bg-[radial-gradient(circle,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[length:20px_20px] opacity-50"
        style={{
          transform: `translateY(${scrollY * 0.05}px)`
        }}
      ></div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/30"></div>
      
      {/* Animated background dots with parallax effect */}
      <div className="absolute inset-0">
        <div 
          className="absolute top-20 left-20 w-32 h-32 bg-white/10 rounded-full blur-3xl"
          style={{
            transform: `translate(${scrollY * -0.07}px, ${scrollY * 0.05}px)`
          }}
        ></div>
        <div 
          className="absolute top-1/4 right-1/3 w-48 h-48 bg-pink-500/10 rounded-full blur-3xl"
          style={{
            transform: `translate(${scrollY * 0.05}px, ${scrollY * -0.08}px)`
          }}
        ></div>
        <div 
          className="absolute bottom-1/3 left-1/3 w-56 h-56 bg-indigo-500/10 rounded-full blur-3xl"
          style={{
            transform: `translate(${scrollY * -0.04}px, ${scrollY * 0.06}px)`
          }}
        ></div>
      </div>
      
      <Header />
      
      <div className="container mx-auto px-6 flex-grow flex items-center relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Improved tagline styling and alignment with subtle parallax */}
          <div 
            className="flex justify-center mb-6"
            style={{
              transform: `translateY(${scrollY * -0.1}px)`
            }}
          >
            <div className="rounded-full bg-white/20 backdrop-blur-sm px-6 py-2 flex items-center shadow-lg border border-white/10">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
              <span className="text-sm font-medium">{t('footer.tagline')}</span>
            </div>
          </div>
          
          {/* Resume icon added above the title with parallax effect */}
          <div 
            className="flex justify-center mb-6"
            style={{
              transform: `translateY(${scrollY * -0.15}px)`
            }}
          >
            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-xl">
              <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="url(#resume-gradient)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <defs>
                  <linearGradient id="resume-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#10B981" /> {/* emerald-500 */}
                    <stop offset="50%" stopColor="#14B8A6" /> {/* teal-500 */}
                    <stop offset="100%" stopColor="#06B6D4" /> {/* cyan-500 */}
                  </linearGradient>
                </defs>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <line x1="10" y1="9" x2="8" y2="9" />
              </svg>
            </div>
          </div>
          
          {/* Title with parallax effect */}
          <h1 
            className="text-5xl md:text-7xl font-bold tracking-tight mb-6 drop-shadow-md bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-purple-200"
            style={{
              transform: `translateY(${scrollY * -0.2}px)`
            }}
          >
            AdaptiveCV
          </h1>
          
          {/* Subtitle with parallax effect */}
          <p 
            className="text-xl md:text-2xl mb-10 leading-relaxed text-white/90"
            style={{
              transform: `translateY(${scrollY * -0.18}px)`
            }}
          >
            {t('home.title')} {t('home.subtitle')}
          </p>
          
          {/* Get Started button with enhanced parallax effect */}
          <div 
            className="flex justify-center"
            style={{
              transform: `translateY(${scrollY * -0.15}px)`
            }}
          >
            <Button 
              size="lg" 
              className="bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-600 hover:via-teal-600 hover:to-cyan-600 text-white text-lg font-semibold px-12 py-7 rounded-xl shadow-lg shadow-purple-900/20 border border-white/10 transition-all duration-300 transform hover:scale-105 animate-pulse-slow"
              onClick={() => handleButtonClick('/login')}
            >
              {t('home.getStarted')}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Button>
          </div>
        </div>
      </div>
      
      {/* Enhanced divider with glow effect and subtle parallax */}
      <div 
        className="absolute bottom-0 left-0 right-0"
        style={{
          transform: `translateY(${scrollY * 0.05}px)`
        }}
      >
        <div className="h-0.5 bg-gradient-to-r from-transparent via-white/70 to-transparent w-full shadow-glow"></div>
      </div>
    </div>
  );
}