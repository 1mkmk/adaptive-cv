import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/lib/translations";
import { ChevronLeft, ChevronRight } from "lucide-react"; 

interface FeatureSlideProps {
  title: string;
  description: string;
  bulletPoints: string[];
  testimonial: string;
  color: 'indigo' | 'purple' | 'fuchsia';
  isActive: boolean;
  index: number;
  currentIndex: number;
}

function FeatureSlide({
  title,
  description,
  bulletPoints,
  testimonial,
  color,
  isActive,
  index,
  currentIndex
}: FeatureSlideProps) {
  const gradients = {
    indigo: 'from-indigo-600 to-blue-600',
    purple: 'from-purple-600 to-indigo-600',
    fuchsia: 'from-fuchsia-600 to-purple-600'
  };
  
  const lightGradients = {
    indigo: 'from-indigo-50 to-blue-50',
    purple: 'from-purple-50 to-indigo-50',
    fuchsia: 'from-fuchsia-50 to-purple-50'
  };
  
  const borders = {
    indigo: 'border-indigo-500',
    purple: 'border-purple-500',
    fuchsia: 'border-fuchsia-500'
  };
  
  const texts = {
    indigo: 'text-indigo-700',
    purple: 'text-purple-700',
    fuchsia: 'text-fuchsia-700'
  };

  // Calculate position and opacity based on the difference between current index and this slide's index
  let position = "translate-x-0";
  let opacity = "opacity-100";
  let scale = "scale-100";
  let zIndex = "z-10";
  
  const diff = index - currentIndex;
  
  if (diff < 0) {
    // Slide is to the left of current
    position = "translate-x-[-100%]";
    opacity = "opacity-0";
    scale = "scale-95";
    zIndex = "z-0";
  } else if (diff > 0) {
    // Slide is to the right of current
    position = "translate-x-[100%]";
    opacity = "opacity-0";
    scale = "scale-95";
    zIndex = "z-0";
  }

  return (
    <div 
      className={`absolute top-0 left-0 w-full transition-all duration-500 ease-in-out ${position} ${opacity} ${scale} ${zIndex}`}
      aria-hidden={!isActive}
    >
      <div className="rounded-2xl overflow-hidden shadow-xl bg-white">
        <div className={`p-8 bg-gradient-to-r ${gradients[color]} text-white`}>
          <h3 className="text-2xl font-bold tracking-tight">{title}</h3>
          <p className="text-white/90 mt-2 text-lg">
            {description}
          </p>
        </div>
        
        <div className="p-8">
          <ul className="space-y-4 mb-8">
            {bulletPoints.map((point, index) => (
              <li key={index} className="flex items-start">
                <span className={`mr-3 mt-1 flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-r ${gradients[color]} text-white text-xs`}>✓</span>
                <span className="text-gray-600">{point}</span>
              </li>
            ))}
          </ul>
          
          <div className={`p-5 rounded-xl bg-gradient-to-r ${lightGradients[color]} border-l-4 ${borders[color]}`}>
            <p className={`italic ${texts[color]}`}>
              {testimonial}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function FeaturesSection() {
  const { t } = useTranslation();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [autoplayPaused, setAutoplayPaused] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const sliderRef = useRef<HTMLDivElement | null>(null);
  
  const featureSlides = [
    {
      id: 'ai',
      label: 'AI-Powered',
      content: {
        title: t('home.features.aiTailored'),
        description: t('home.features.aiTailoredDesc'),
        bulletPoints: [
          'Matches your profile to job requirements using natural language processing',
          'Highlights relevant skills and experiences based on job description keywords',
          'Optimizes language for applicant tracking systems to increase visibility',
          'Generates professional summaries tailored to each position\'s unique needs'
        ],
        testimonial: '"The AI recommendations helped me emphasize skills I would have otherwise overlooked. It made a huge difference in my applications!"',
        color: 'indigo' as const
      }
    },
    {
      id: 'templates',
      label: 'Beautiful Templates',
      content: {
        title: t('home.features.templates'),
        description: t('home.features.templatesDesc'),
        bulletPoints: [
          'Multiple layout options designed by professional CV writers',
          'Industry-specific designs that match employer expectations',
          'Clean, modern aesthetics with balanced typography',
          'Export to multiple formats (PDF, LaTeX) with perfect formatting'
        ],
        testimonial: '"The templates are beautifully designed and professionally structured. They helped my CV stand out while maintaining a professional appearance."',
        color: 'purple' as const
      }
    },
    {
      id: 'tracking',
      label: 'Job Tracking',
      content: {
        title: 'Job Application Tracking',
        description: 'Keep track of all your job applications in one place and manage your tailored CVs for each position.',
        bulletPoints: [
          'Store and organize job descriptions in one convenient dashboard',
          'Import jobs directly from URLs with automatic parsing',
          'Track application status from submission to interview',
          'Maintain a history of generated CVs for each application'
        ],
        testimonial: '"The tracking system helped me stay organized during my job search. I no longer had to frantically search for which CV version I sent to which company."',
        color: 'fuchsia' as const
      }
    }
  ];

  const goToSlide = useCallback((index: number) => {
    // Handle wrapping around
    if (index < 0) {
      setCurrentSlide(featureSlides.length - 1);
    } else if (index >= featureSlides.length) {
      setCurrentSlide(0);
    } else {
      setCurrentSlide(index);
    }
  }, [featureSlides.length]);

  const nextSlide = useCallback(() => {
    goToSlide(currentSlide + 1);
  }, [currentSlide, goToSlide]);

  const prevSlide = useCallback(() => {
    goToSlide(currentSlide - 1);
  }, [currentSlide, goToSlide]);

  // Set up autoplay
  useEffect(() => {
    if (!autoplayPaused) {
      timerRef.current = setInterval(() => {
        nextSlide();
      }, 5000); // Change slide every 5 seconds
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [nextSlide, autoplayPaused]);

  // Pause autoplay on hover or focus
  const pauseAutoplay = () => setAutoplayPaused(true);
  const resumeAutoplay = () => setAutoplayPaused(false);
  
  // Touch handling
  const touchStartX = useRef<number | null>(null);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    pauseAutoplay();
  };
  
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current !== null) {
      const touchEndX = e.changedTouches[0].clientX;
      const diff = touchStartX.current - touchEndX;
      
      if (diff > 50) { // Swiped left
        nextSlide();
      } else if (diff < -50) { // Swiped right
        prevSlide();
      }
      
      touchStartX.current = null;
      resumeAutoplay();
    }
  };

  return (
    <div className="py-24 bg-gradient-to-b from-white to-slate-50 relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-full max-w-6xl h-px bg-gradient-to-r from-transparent via-indigo-300 to-transparent"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(79,70,229,0.03)_1px,transparent_1px)] bg-[length:20px_20px]"></div>
      <div className="absolute -top-40 right-0 w-96 h-96 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 opacity-30 blur-3xl"></div>
      <div className="absolute -bottom-40 left-0 w-96 h-96 rounded-full bg-gradient-to-tr from-blue-100 to-indigo-100 opacity-30 blur-3xl"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent inline-block">Key Features</h2>
          <p className="text-gray-600 text-xl">
            Tools designed to make your job application process smooth and effective
          </p>
        </div>
        
        {/* Feature navigation */}
        <div className="flex justify-center gap-4 mb-8">
          {featureSlides.map((slide, index) => (
            <button
              key={slide.id}
              onClick={() => goToSlide(index)}
              className={`py-2 px-4 rounded-lg transition-all duration-300 ${
                currentSlide === index
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                  : 'bg-white text-gray-700 border border-gray-200 hover:border-indigo-300'
              }`}
              aria-pressed={currentSlide === index}
            >
              {slide.label}
            </button>
          ))}
        </div>
        
        {/* Slider container */}
        <div 
          className="max-w-4xl mx-auto relative h-[600px]" 
          ref={sliderRef}
          onMouseEnter={pauseAutoplay}
          onMouseLeave={resumeAutoplay}
          onFocus={pauseAutoplay}
          onBlur={resumeAutoplay}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {featureSlides.map((slide, index) => (
            <FeatureSlide 
              key={slide.id} 
              {...slide.content} 
              isActive={currentSlide === index}
              index={index}
              currentIndex={currentSlide}
            />
          ))}
          
          {/* Navigation arrows */}
          <button
            onClick={prevSlide}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-6 bg-white rounded-full p-2 shadow-lg border border-gray-100 hover:bg-gray-50 z-20"
            aria-label="Previous slide"
          >
            <ChevronLeft className="h-6 w-6 text-indigo-600" />
          </button>
          
          <button
            onClick={nextSlide}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-6 bg-white rounded-full p-2 shadow-lg border border-gray-100 hover:bg-gray-50 z-20"
            aria-label="Next slide"
          >
            <ChevronRight className="h-6 w-6 text-indigo-600" />
          </button>
          
          {/* Indicator dots */}
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 flex gap-2 pb-4">
            {featureSlides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-3 h-3 rounded-full transition-all ${
                  currentSlide === index 
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 w-6' 
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}