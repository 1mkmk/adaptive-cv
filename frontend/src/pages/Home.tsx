import React, { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import JobForm from '@/components/JobForm';
import { useAuth } from '@/context/AuthContext';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  
  // Check for pending job listings after login
  useEffect(() => {
    if (isAuthenticated) {
      // Handle any pending job listings saved in localStorage
      const pendingJobListing = localStorage.getItem('pendingJobListing');
      const pendingJobUrl = localStorage.getItem('pendingJobUrl');
      
      if (pendingJobListing || pendingJobUrl) {
        // Clear localStorage
        localStorage.removeItem('pendingJobListing');
        localStorage.removeItem('pendingJobUrl');
        
        // Navigate to jobs page
        navigate('/jobs');
      }
    }
  }, [isAuthenticated, navigate]);
  
  return (
    <>
      <div className="relative">
        {/* Hero Section with Background */}
        <div className="bg-gradient-to-r from-indigo-700 to-purple-700 text-white py-24">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-block mb-6 rounded-full bg-white/10 px-4 py-1.5 text-sm font-semibold">
                {t('footer.tagline')}
              </div>
              <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-6 drop-shadow-sm">
                AdaptiveCV
              </h1>
              <p className="text-xl md:text-2xl mb-10 leading-relaxed">
                {t('home.title')} {t('home.subtitle')}
              </p>
              <div className="flex flex-col sm:flex-row gap-5 justify-center">
                <Button 
                  size="lg" 
                  className="bg-white text-indigo-700 hover:bg-white/90 text-base font-semibold px-8"
                  onClick={() => navigate('/login')}
                >
                  {t('profile.profileDesc')}
                </Button>
                <Button 
                  size="lg" 
                  variant="outline"
                  className="bg-white/10 hover:bg-white/20 text-white border-white/50 text-base font-semibold px-8"
                  onClick={() => navigate('/login')}
                >
                  {t('jobs.generateCV')}
                </Button>
              </div>
            </div>
          </div>
          
          {/* Simple Divider Line */}
          <div className="absolute bottom-0 left-0 right-0">
            <div className="h-1 bg-white w-full"></div>
          </div>
        </div>
        
        {/* Creator Note Section */}
        <div className="container mx-auto px-6 py-12">
          <div className="max-w-4xl mx-auto bg-gradient-to-r from-indigo-50 to-purple-50 p-6 md:p-8 rounded-xl border border-purple-100">
            <div className="flex flex-col md:flex-row gap-6 items-center">
              <div className="w-24 h-24 shrink-0 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-3xl font-bold">
                MK
              </div>
              <div>
                <h3 className="text-xl font-medium text-gray-800 mb-2">From the creator</h3>
                <p className="text-gray-600 leading-relaxed">
                  AdaptiveCV was born from my own struggles with job applications. I found myself constantly rewriting my CV for different positions, trying to emphasize different skills based on job requirements. This project combines my passion for AI and practical problem-solving to create something that I hope makes the job search process easier for everyone.
                </p>
                <p className="text-indigo-600 mt-2 font-medium">– Maciej Kasik, Developer</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Quick Job Add Section */}
        <div className="container mx-auto px-6 py-12">
          <div className="max-w-4xl mx-auto bg-gradient-to-r from-indigo-50 to-purple-50 p-6 md:p-8 rounded-xl border border-purple-100">
            <h2 className="text-2xl font-bold mb-4 text-center">Try It Now</h2>
            <p className="text-gray-600 text-center mb-8">
              Paste a job description below and let our AI create a tailored CV for you.
              {!isAuthenticated && " You'll be prompted to log in to save your job."}
            </p>
            
            <JobForm />
          </div>
        </div>
        
        {/* How It Works Section */}
        <div className="container mx-auto py-16 px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">{t('home.features.title')}</h2>
            <p className="text-gray-600 text-lg">
              {t('home.features.aiTailoredDesc')}
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="border-t-4 border-t-indigo-500 hover:shadow-lg transition-shadow duration-300">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="h-10 w-10 rounded-full bg-indigo-500 text-white flex items-center justify-center mr-3 text-lg">1</div>
                  Create Your Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="text-gray-600">
                <p>
                  Fill in your professional details, work experience, education, and skills to create a comprehensive profile. Or simply upload your existing CV to import data automatically.
                </p>
              </CardContent>
              <CardFooter>
                <Button 
                  variant="ghost" 
                  className="text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50"
                  onClick={() => navigate('/login')}
                >
                  {t('home.getStarted')} →
                </Button>
              </CardFooter>
            </Card>
            
            <Card className="border-t-4 border-t-purple-500 hover:shadow-lg transition-shadow duration-300">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="h-10 w-10 rounded-full bg-purple-500 text-white flex items-center justify-center mr-3 text-lg">2</div>
                  Add Job Descriptions
                </CardTitle>
              </CardHeader>
              <CardContent className="text-gray-600">
                <p>
                  Paste job descriptions or provide URLs to job listings you're interested in. Our system will analyze the requirements and prepare your CV accordingly.
                </p>
              </CardContent>
              <CardFooter>
                <Button 
                  variant="ghost"
                  className="text-purple-600 hover:text-purple-800 hover:bg-purple-50"
                  onClick={() => navigate('/login')}
                >
                  Add Jobs →
                </Button>
              </CardFooter>
            </Card>
            
            <Card className="border-t-4 border-t-indigo-500 hover:shadow-lg transition-shadow duration-300">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="h-10 w-10 rounded-full bg-indigo-500 text-white flex items-center justify-center mr-3 text-lg">3</div>
                  Generate & Export
                </CardTitle>
              </CardHeader>
              <CardContent className="text-gray-600">
                <p>
                  Our AI automatically tailors your CV to emphasize relevant skills and experience for each specific job. Download as PDF, ready to send to employers.
                </p>
              </CardContent>
              <CardFooter>
                <Button 
                  variant="ghost"
                  className="text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50"
                  onClick={() => navigate('/login')}
                >
                  See Templates →
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
        
        {/* Features Section */}
        <div className="bg-slate-50 py-20">
          <div className="container mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-3xl font-bold mb-4">Key Features</h2>
              <p className="text-gray-600 text-lg">
                Tools designed to make your job application process smooth and effective
              </p>
            </div>
            
            <Tabs defaultValue="ai" className="max-w-4xl mx-auto">
              <TabsList className="grid grid-cols-3 mb-10 w-full md:w-2/3 mx-auto">
                <TabsTrigger value="ai" className="text-base">AI-Powered</TabsTrigger>
                <TabsTrigger value="templates" className="text-base">Beautiful Templates</TabsTrigger>
                <TabsTrigger value="tracking" className="text-base">Job Tracking</TabsTrigger>
              </TabsList>
              
              <TabsContent value="ai" className="p-8 bg-white rounded-xl shadow-md border border-gray-100">
                <h3 className="text-2xl font-bold mb-4 text-indigo-700">{t('home.features.aiTailored')}</h3>
                <p className="mb-6 text-gray-600 text-lg leading-relaxed">
                  {t('home.features.aiTailoredDesc')}
                </p>
                <ul className="list-disc pl-6 mb-6 space-y-3 text-gray-600">
                  <li>Matches your profile to job requirements using natural language processing</li>
                  <li>Highlights relevant skills and experiences based on job description keywords</li>
                  <li>Optimizes language for applicant tracking systems to increase visibility</li>
                  <li>Generates professional summaries tailored to each position's unique needs</li>
                </ul>
                <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-500">
                  <p className="italic text-indigo-800">
                    "The AI recommendations helped me emphasize skills I would have otherwise overlooked. It made a huge difference in my applications!"
                  </p>
                </div>
              </TabsContent>
              
              <TabsContent value="templates" className="p-8 bg-white rounded-xl shadow-md border border-gray-100">
                <h3 className="text-2xl font-bold mb-4 text-purple-700">{t('home.features.templates')}</h3>
                <p className="mb-6 text-gray-600 text-lg leading-relaxed">
                  {t('home.features.templatesDesc')}
                </p>
                <ul className="list-disc pl-6 mb-6 space-y-3 text-gray-600">
                  <li>Multiple layout options designed by professional CV writers</li>
                  <li>Industry-specific designs that match employer expectations</li>
                  <li>Clean, modern aesthetics with balanced typography</li>
                  <li>Export to multiple formats (PDF, LaTeX) with perfect formatting</li>
                </ul>
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <p className="italic text-purple-800">
                    "The templates are beautifully designed and professionally structured. They helped my CV stand out while maintaining a professional appearance."
                  </p>
                </div>
              </TabsContent>
              
              <TabsContent value="tracking" className="p-8 bg-white rounded-xl shadow-md border border-gray-100">
                <h3 className="text-2xl font-bold mb-4 text-indigo-700">Job Application Tracking</h3>
                <p className="mb-6 text-gray-600 text-lg leading-relaxed">
                  Keep track of all your job applications in one place and manage your tailored CVs for each position you've applied to.
                </p>
                <ul className="list-disc pl-6 mb-6 space-y-3 text-gray-600">
                  <li>Store and organize job descriptions in one convenient dashboard</li>
                  <li>Import jobs directly from URLs with automatic parsing</li>
                  <li>Track application status from submission to interview</li>
                  <li>Maintain a history of generated CVs for each application</li>
                </ul>
                <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-500">
                  <p className="italic text-indigo-800">
                    "The tracking system helped me stay organized during my job search. I no longer had to frantically search for which CV version I sent to which company."
                  </p>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
        
        {/* Open Source Section */}
        <div className="container mx-auto py-16 px-6">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-block mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600">
                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
                <path d="M9 18c-4.51 2-5-2-7-2"></path>
              </svg>
            </div>
            <h2 className="text-3xl font-bold mb-4">Built with Passion</h2>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              AdaptiveCV is a passion project created to solve real-world problems I faced during job hunting. 
              It combines modern technology with practical needs to streamline the CV creation process.
            </p>
            <div className="flex flex-wrap justify-center gap-3 mb-8">
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">React</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">TypeScript</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">FastAPI</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">Python</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">SQLite</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">OpenAI</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">LaTeX</span>
            </div>
            <a href="https://github.com/maciejkasik" target="_blank" rel="noopener noreferrer">
              <Button 
                variant="outline"
                className="border-indigo-300 text-indigo-700 hover:bg-indigo-50"
              >
                View on GitHub
              </Button>
            </a>
          </div>
        </div>
        
        {/* CTA Section */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-20">
          <div className="container mx-auto px-6 text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to transform your job applications?</h2>
            <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto leading-relaxed">
              Start creating tailored CVs that significantly increase your chances of landing interviews. 
              Your perfect job is waiting.
            </p>
            <Button 
              size="lg" 
              className="bg-white text-indigo-700 hover:bg-white/90 font-semibold text-lg px-8 py-6"
              onClick={() => navigate('/login')}
            >
              Get Started Now
            </Button>
            <p className="mt-6 text-white/70">No sign-up required. Your data stays on your device.</p>
          </div>
        </div>
        
        {/* Footer */}
        <footer className="bg-indigo-950 text-white py-10">
          <div className="container mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="mb-6 md:mb-0">
                <h3 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 text-transparent bg-clip-text">AdaptiveCV</h3>
                <p className="text-indigo-200 mt-1">Tailor your CV for every opportunity</p>
              </div>
              <div className="flex flex-col md:flex-row gap-6 md:gap-12 text-center md:text-left">
                <div>
                  <h4 className="font-semibold mb-2 text-indigo-300">{t('footer.navigation')}</h4>
                  <ul className="text-indigo-200">
                    <li className="mb-1"><button className="hover:text-white transition-colors" onClick={() => navigate('/')}>{t('navigation.home')}</button></li>
                    <li className="mb-1"><button className="hover:text-white transition-colors" onClick={() => navigate('/login')}>{t('navigation.profile')}</button></li>
                    <li className="mb-1"><button className="hover:text-white transition-colors" onClick={() => navigate('/login')}>{t('navigation.jobs')}</button></li>
                    <li><button className="hover:text-white transition-colors" onClick={() => navigate('/login')}>{t('navigation.templates')}</button></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2 text-indigo-300">Connect</h4>
                  <ul className="text-indigo-200">
                    <li className="mb-1"><a href="https://github.com/maciejkasik" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub</a></li>
                    <li><a href="mailto:contact@example.com" className="hover:text-white transition-colors">Contact</a></li>
                  </ul>
                </div>
              </div>
            </div>
            <Separator className="my-8 bg-indigo-800" />
            <div className="text-center text-indigo-300 text-sm">
              <p>© {new Date().getFullYear()} AdaptiveCV. A personal project by Maciej Kasik.</p>
              <p className="mt-1">{t('footer.madewith')} ❤️</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default Home;