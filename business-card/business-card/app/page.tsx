'use client';

import React from 'react';
import { HeroSection } from '@/components/home/HeroSection';
import { CreatorSection } from '@/components/home/CreatorSection';
import { JobAddSection } from '@/components/home/JobAddSection';
import { WorkflowSection } from '@/components/home/WorkflowSection';
import { FeaturesSection } from '@/components/home/FeaturesSection';
import { Footer } from '@/components/home/Footer';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/lib/translations';

// Frontend URL - bezpośredni adres do frontendu
const FRONTEND_URL = "http://localhost:5173";

export default function Home() {
  const { t } = useTranslation();
  
  // This is a minimal implementation with no authentication
  const isAuthenticated = false;
  
  return (
    <div className="relative overflow-hidden">
      {/* Full-screen hero section with integrated header/sign-in */}
      <HeroSection />
      
      {/* Other sections */}
      <CreatorSection />
      <JobAddSection isAuthenticated={isAuthenticated} />
      <WorkflowSection />
      <FeaturesSection />
      
      {/* Open Source Section */}
      <div className="py-24 bg-gradient-to-b from-slate-50 to-white relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-full max-w-6xl h-px bg-gradient-to-r from-transparent via-indigo-300 to-transparent"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[length:16px_16px]"></div>
        <div className="absolute top-40 left-20 w-72 h-72 rounded-full bg-gradient-to-tl from-purple-100 to-indigo-100 opacity-30 blur-3xl"></div>
        <div className="absolute bottom-40 right-20 w-72 h-72 rounded-full bg-gradient-to-tr from-indigo-100 to-purple-100 opacity-30 blur-3xl"></div>
        
        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center justify-center mb-10 p-3 rounded-2xl bg-gradient-to-r from-indigo-100 to-purple-100">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#github-gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600">
                <defs>
                  <linearGradient id="github-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#4F46E5" />
                    <stop offset="100%" stopColor="#9333EA" />
                  </linearGradient>
                </defs>
                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
                <path d="M9 18c-4.51 2-5-2-7-2"></path>
              </svg>
            </div>
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent inline-block">Built with Passion</h2>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              AdaptiveCV is a passion project created to solve real-world problems I faced during job hunting. 
              It combines modern technology with practical needs to streamline the CV creation process.
            </p>
            <div className="flex flex-wrap justify-center gap-3 mb-8">
              {['React', 'TypeScript', 'FastAPI', 'Python', 'PostgreSQL', 'OpenAI', 'LaTeX'].map((tech, index) => (
                <span 
                  key={index} 
                  className="bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 px-4 py-2 rounded-xl text-sm font-medium border border-indigo-100 shadow-sm"
                >
                  {tech}
                </span>
              ))}
            </div>
            <a href="https://github.com/maciejkasik" target="_blank" rel="noopener noreferrer">
              <Button 
                variant="outline"
                className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100 px-6 py-2 rounded-xl font-medium shadow-sm"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z" />
                </svg>
                View on GitHub
              </Button>
            </a>
          </div>
        </div>
      </div>
      
      {/* CTA Section - Updated to highlight open source and two usage modes */}
      <div className="bg-gradient-to-r from-emerald-700 via-teal-700 to-indigo-800 text-white py-24 relative overflow-hidden">
        {/* Decorative background elements */}
        <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[length:20px_20px] opacity-50"></div>
        <div className="absolute -top-40 -left-40 w-80 h-80 rounded-full bg-green-500/10 blur-3xl"></div>
        <div className="absolute -bottom-40 -right-40 w-80 h-80 rounded-full bg-blue-500/10 blur-3xl"></div>
        
        <div className="container mx-auto px-6 text-center relative z-10">
          <div className="inline-block mb-4 p-2 rounded-full bg-white/10 backdrop-blur-sm px-4 py-1.5 text-sm font-semibold">
            <span className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
              We Love Open Source
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 drop-shadow-sm">Ready to transform your job applications?</h2>
          
          <div className="max-w-4xl mx-auto mb-10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-2xl border border-white/20 hover:bg-white/15 transition-all hover:shadow-lg flex flex-col h-full">
                <div className="bg-emerald-500/30 rounded-full w-12 h-12 flex items-center justify-center mb-4 mx-auto">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-3">Self-Hosted Mode</h3>
                <p className="text-white/80 mb-4 flex-grow">
                  Download and run AdaptiveCV locally on your own device. Completely free and private - your data never leaves your computer.
                </p>
                <Button 
                  className="bg-emerald-600 hover:bg-emerald-700 text-white border-none"
                  onClick={() => window.location.href = `https://github.com/maciejkasik/adaptive-cv`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z" />
                  </svg>
                  Download Free
                </Button>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-2xl border border-white/20 hover:bg-white/15 transition-all hover:shadow-lg flex flex-col h-full">
                <div className="bg-indigo-500/30 rounded-full w-12 h-12 flex items-center justify-center mb-4 mx-auto">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-3">Cloud Service</h3>
                <p className="text-white/80 mb-4 flex-grow">
                  Use our fully managed cloud service with premium features, advanced AI models, and automatic updates. Subscription includes priority support.
                </p>
                <Button 
                  className="bg-indigo-600 hover:bg-indigo-700 text-white border-none"
                  onClick={() => window.location.href = `${FRONTEND_URL}/login`}
                >
                  Try Premium
                </Button>
              </div>
            </div>
          </div>
          
          <p className="text-white/70 italic">Both options respect your privacy and can be used without registration.</p>
        </div>
      </div>
      
      {/* Footer */}
      <Footer />
    </div>
  );
}
