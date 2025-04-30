import React, { useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/lib/translations";

// Frontend URL for redirects
const FRONTEND_URL = "http://localhost:3000";

interface WorkflowStepProps {
  number: number;
  title: string;
  description: string;
  ctaText: string;
  ctaPath: string;
  color: 'indigo' | 'purple' | 'fuchsia';
  delay?: number;
  isVisible?: boolean;
}

export function WorkflowStep({ 
  number, 
  title, 
  description, 
  ctaText, 
  ctaPath,
  color,
  delay = 0,
  isVisible = true
}: WorkflowStepProps) {
  const handleNavigation = () => {
    window.location.href = `${FRONTEND_URL}${ctaPath}`;
  };
  
  const gradients = {
    indigo: 'from-indigo-500 to-blue-600',
    purple: 'from-purple-500 to-indigo-600',
    fuchsia: 'from-fuchsia-500 to-purple-600'
  };
  
  const hoverGradients = {
    indigo: 'hover:from-indigo-600 hover:to-blue-700',
    purple: 'hover:from-purple-600 hover:to-indigo-700',
    fuchsia: 'hover:from-fuchsia-600 hover:to-purple-700'
  };
  
  return (
    <div 
      className={`bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100 hover:shadow-xl transition-all duration-500 flex flex-col h-full transform hover:-translate-y-1 ${
        isVisible 
          ? 'opacity-100 translate-y-0' 
          : 'opacity-0 translate-y-12'
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className={`p-6 bg-gradient-to-r ${gradients[color]} text-white`}>
        <span className="flex items-center justify-center w-12 h-12 rounded-full bg-white/20 text-xl font-bold mb-4">
          {number}
        </span>
        <h3 className="text-xl font-bold mb-2">{title}</h3>
      </div>
      <div className="p-6 flex-grow">
        <p className="text-gray-600 mb-6">{description}</p>
      </div>
      <div className="px-6 pb-6">
        <Button 
          className={`w-full bg-gradient-to-r ${gradients[color]} ${hoverGradients[color]} text-white border-none shadow-md`}
          onClick={handleNavigation}
        >
          {ctaText} →
        </Button>
      </div>
    </div>
  );
}

export function WorkflowSection() {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    // Create an intersection observer to detect when section scrolls into view
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 }); // Trigger when 20% of element is visible
    
    // Observe the container element
    const element = document.getElementById('workflow-section');
    if (element) observer.observe(element);
    
    return () => {
      if (element) observer.unobserve(element);
    };
  }, []);
  
  const steps = [
    {
      number: 1,
      title: "Create Your Profile",
      description: "Fill in your professional details, work experience, education, and skills to create a comprehensive profile.",
      ctaText: t('home.getStarted'),
      ctaPath: "/login",
      color: 'indigo' as const,
      delay: 0
    },
    {
      number: 2,
      title: "Add Job Descriptions",
      description: "Paste job descriptions or provide URLs to job listings you're interested in. Our system will analyze the requirements automatically.",
      ctaText: "Add Jobs",
      ctaPath: "/login",
      color: 'purple' as const,
      delay: 200
    },
    {
      number: 3,
      title: "Generate & Export",
      description: "Our AI tailors your CV to emphasize relevant skills for each specific job. Download as PDF, ready to send to employers.",
      ctaText: "See Templates",
      ctaPath: "/login",
      color: 'fuchsia' as const,
      delay: 400
    }
  ];
  
  return (
    <div className="py-24 bg-gradient-to-b from-indigo-50 to-white relative overflow-hidden" id="workflow-section">
      {/* Decorative elements */}
      <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(99,102,241,0.05)_1px,transparent_1px)] bg-[length:16px_16px]"></div>
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-full max-w-6xl h-px bg-gradient-to-r from-transparent via-indigo-300 to-transparent"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <div className={`text-center max-w-2xl mx-auto mb-16 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent inline-block">
            {t('home.features.title')}
          </h2>
          <p className="text-gray-600 text-xl">
            Three simple steps to create the perfect CV for every job application
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <WorkflowStep 
              key={index} 
              {...step} 
              isVisible={isVisible}
            />
          ))}
        </div>
      </div>
    </div>
  );
}