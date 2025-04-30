import React from 'react';
import { useTranslation } from "@/lib/translations";

interface JobAddSectionProps {
  isAuthenticated: boolean;
}

export function JobAddSection({ isAuthenticated }: JobAddSectionProps) {
  const { t } = useTranslation();

  return (
    <div className="py-24 bg-gradient-to-b from-white to-indigo-50 relative overflow-hidden">
      {/* Colorful background elements */}
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-full max-w-6xl h-px bg-gradient-to-r from-transparent via-indigo-300 to-transparent"></div>
      <div className="absolute top-40 right-20 w-72 h-72 rounded-full bg-gradient-to-tl from-pink-200 to-blue-200 opacity-20 blur-3xl"></div>
      <div className="absolute bottom-20 left-10 w-60 h-60 rounded-full bg-gradient-to-tr from-purple-200 to-indigo-200 opacity-20 blur-3xl"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent inline-block">Try It Now</h2>
            <p className="text-gray-600 text-xl max-w-2xl mx-auto">
              Paste a job description below and let our AI create a tailored CV for you.
              {!isAuthenticated && " You'll be prompted to log in to save your job."}
            </p>
          </div>
          
          {/* JobForm component placeholder with improved design */}
          <div className="bg-white rounded-2xl shadow-xl border border-indigo-100 overflow-hidden">
            <div className="p-8 bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
              <h3 className="text-xl font-semibold mb-1">Job Description Parser</h3>
              <p className="opacity-90">We'll analyze the text to highlight skills and experience that match this job.</p>
            </div>
            <div className="p-8 bg-white">
              <div className="bg-gray-50 p-6 rounded-xl border border-gray-100 text-center">
                <textarea 
                  className="w-full h-32 p-4 text-gray-700 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all mb-4" 
                  placeholder="Paste job description here..."
                ></textarea>
                <button className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md">
                  Generate Tailored CV
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}