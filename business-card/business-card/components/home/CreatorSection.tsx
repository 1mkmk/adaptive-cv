import React, { useEffect, useState } from 'react';

export function CreatorSection() {
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    // Create an intersection observer to detect when elements scroll into view
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 }); // Trigger when 20% of element is visible
    
    // Observe the container element
    const element = document.getElementById('creator-section');
    if (element) observer.observe(element);
    
    return () => {
      if (element) observer.unobserve(element);
    };
  }, []);
  
  return (
    <div className="py-20 bg-gradient-to-b from-slate-100 to-white relative overflow-hidden">
      {/* Colorful background elements */}
      <div className="absolute -top-24 -right-24 w-64 h-64 rounded-full bg-gradient-to-br from-fuchsia-200 to-indigo-200 opacity-30 blur-3xl"></div>
      <div className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full bg-gradient-to-tr from-cyan-200 to-purple-200 opacity-30 blur-3xl"></div>
      
      <div className="container mx-auto px-6 relative z-10" id="creator-section">
        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Creator card with slide-in animation */}
          <div 
            className={`bg-white p-8 md:p-12 rounded-3xl shadow-xl border border-indigo-100 transition-all duration-1000 ease-out ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-12'}`}
          >
            <div className="flex flex-col md:flex-row gap-8 items-center">
              <div className="w-28 h-28 shrink-0 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-4xl font-bold shadow-lg">
                MK
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-3 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">From the creator</h3>
                <p className="text-gray-600 leading-relaxed text-lg">
                  AdaptiveCV was born from my own struggles with job applications. I found myself constantly rewriting my CV for different positions, trying to emphasize different skills based on job requirements. This project combines my passion for AI and practical problem-solving to create something that I hope makes the job search process easier for everyone.
                </p>
                <p className="text-indigo-600 mt-3 font-semibold">– Maciej Kasik, Developer</p>
              </div>
            </div>
          </div>
          
          {/* Testimonial card with slide-in animation - Wiktor Wróblewski */}
          <div 
            className={`bg-white p-8 md:p-12 rounded-3xl shadow-xl border border-indigo-100 transition-all duration-1000 ease-out delay-300 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-12'}`}
          >
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xl font-bold shadow-md">
                  WW
                </div>
                <div>
                  <h4 className="text-xl font-bold text-gray-800">Wiktor Wróblewski</h4>
                  <p className="text-gray-500">Senior Tech Recruiter</p>
                </div>
              </div>
              <div>
                <svg className="w-10 h-10 text-indigo-200 mb-3" fill="currentColor" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 8c-2.209 0-4 1.791-4 4v10c0 2.209 1.791 4 4 4h10c2.209 0 4-1.791 4-4v-10c0-2.209-1.791-4-4-4h-10zM9.773 18.273c0.928 0 1.682 0.754 1.682 1.682s-0.754 1.682-1.682 1.682-1.682-0.754-1.682-1.682 0.754-1.682 1.682-1.682zM14.5 18.273c0.928 0 1.682 0.754 1.682 1.682s-0.754 1.682-1.682 1.682-1.682-0.754-1.682-1.682 0.754-1.682 1.682-1.682zM9.773 13.545c0.928 0 1.682 0.754 1.682 1.682s-0.754 1.682-1.682 1.682-1.682-0.754-1.682-1.682 0.754-1.682 1.682-1.682zM14.5 13.545c0.928 0 1.682 0.754 1.682 1.682s-0.754 1.682-1.682 1.682-1.682-0.754-1.682-1.682 0.754-1.682 1.682-1.682z"></path>
                </svg>
                <p className="text-gray-600 leading-relaxed text-lg italic">
                  As a recruiter, I've seen thousands of CVs. AdaptiveCV stands out by helping candidates create truly targeted applications. The customization capabilities are impressive, and the AI actually understands what matters for specific roles. I now recommend it to all job seekers I work with.
                </p>
                <div className="flex items-center mt-4 text-amber-500">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                      <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                    </svg>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}