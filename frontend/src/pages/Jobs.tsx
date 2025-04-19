import React, { useState, useEffect } from 'react';
import Navbar from "@/components/ui/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { API_BASE_URL, fetchApi } from '@/services/api';
import { getDownloadCvUrl, getDownloadLatexUrl } from '@/services/cvService';
import { generatePdfCV, downloadCV, Template, getTemplates } from '@/services/templateService';
import { useLocation } from 'react-router';

// Interface for job type
interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  source_url?: string;
  created_at: string;
  cv?: string; // Generated CV content
  cv_format?: 'markdown' | 'pdf'; // Format of the generated CV
}

const Jobs: React.FC = () => {
  const location = useLocation();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [generatingCv, setGeneratingCv] = useState(false);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    location.state?.selectedTemplateId || null
  );
  
  // URL form state
  const [jobUrl, setJobUrl] = useState('');
  
  // Manual entry state - single textarea for job listing
  const [jobListing, setJobListing] = useState('');
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCompany, setFilterCompany] = useState<string>('');
  const [companies, setCompanies] = useState<string[]>([]);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [jobsPerPage] = useState(5);
  
  // Language model selection
  const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');
  const languageModels = [
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
    { id: 'gpt-4', name: 'GPT-4' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' }
  ];
  
  // Custom context for CV generation
  const [customContext, setCustomContext] = useState('');

  // Load jobs and templates on component mount
  useEffect(() => {
    fetchJobs();
    fetchTemplates();
  }, []);
  
  const fetchTemplates = async () => {
    try {
      const templatesData = await getTemplates();
      setTemplates(templatesData);
      
      // If we have a selected template ID from navigation, make sure it exists
      if (selectedTemplateId && !templatesData.some(t => t.id === selectedTemplateId)) {
        setSelectedTemplateId(templatesData.length > 0 ? templatesData[0].id : null);
      } else if (!selectedTemplateId && templatesData.length > 0) {
        // Auto-select first template if none selected
        setSelectedTemplateId(templatesData[0].id);
      }
    } catch (err) {
      console.error('Error loading templates:', err);
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const data = await fetchApi('/jobs');
      setJobs(data);
      
      // Extract unique companies for filtering
      const uniqueCompanies = Array.from(new Set(data.map((job: Job) => job.company)));
      setCompanies(uniqueCompanies);
    } catch (err) {
      setError('Error loading jobs. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle job listing textarea change
  const handleJobListingChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJobListing(e.target.value);
  };

  // Handle URL input change
  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setJobUrl(e.target.value);
  };

  // Submit job from URL
  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobUrl) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const formData = new FormData();
      formData.append('job_url', jobUrl);
      
      const response = await fetch(`${API_BASE_URL}/jobs/create`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Failed to import job');
      }
      
      const data = await response.json();
      setSuccess('Job imported successfully!');
      setJobUrl('');
      fetchJobs(); // Refresh job list
    } catch (err) {
      setError('Failed to import job. Please check the URL and try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Submit manual job entry
  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobListing.trim()) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      // Extract basic info from the prompt for display purposes
      const lines = jobListing.split('\n').filter(line => line.trim());
      
      // We'll let the backend extract job details using OpenAI
      setSuccess('Processing job listing using AI...');
      
      const formData = new FormData();
      // Don't send title or company - let the backend extract them with OpenAI
      formData.append('location', 'Not specified');
      formData.append('description', jobListing);
      
      const response = await fetch(`${API_BASE_URL}/jobs/create`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Failed to add job');
      }
      
      setSuccess('Job processed and added successfully with AI-extracted details!');
      setJobListing('');
      fetchJobs(); // Refresh job list
    } catch (err) {
      setError('Failed to add job. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Job-specific template mapping
  const [jobTemplates, setJobTemplates] = useState<Record<string, string>>({});
  
  // Load default template from localStorage on mount
  useEffect(() => {
    const defaultTemplate = localStorage.getItem('defaultTemplateId');
    if (defaultTemplate) {
      setSelectedTemplateId(defaultTemplate);
    }
  }, []);
  
  // Set template for a specific job
  const setJobTemplate = (jobId: string, templateId: string) => {
    setJobTemplates(prev => ({
      ...prev,
      [jobId]: templateId
    }));
  };
  
  // Get template for a specific job (or use selected/default)
  const getJobTemplate = (jobId: string) => {
    // First check if there's a job-specific template
    if (jobTemplates[jobId]) {
      return jobTemplates[jobId];
    }
    
    // Then check if there's a selected template
    if (selectedTemplateId) {
      return selectedTemplateId;
    }
    
    // Finally fall back to the default template from localStorage
    return localStorage.getItem('defaultTemplateId') || '';
  };
  
  // Generate CV for a specific job using the template for that job or the selected template
  const generateCv = async (job: Job) => {
    setSelectedJob(job);
    setGeneratingCv(true);
    setError(null);
    
    // Get template ID for this specific job
    const templateId = getJobTemplate(job.id);
    
    try {
      // Include the selected model and custom context in the message
      const modelInfo = selectedModel ? ` with ${languageModels.find(m => m.id === selectedModel)?.name}` : '';
      setSuccess(`Generating PDF CV using ${getTemplateNameById(templateId)}${modelInfo}. This might take up to 30 seconds...`);
      
      // Prepare additional parameters for CV generation
      const params: any = {
        templateId: templateId || undefined,
        model: selectedModel,
      };
      
      // Add custom context if provided
      if (customContext && customContext.trim()) {
        params.customContext = customContext.trim();
      }
      
      const response = await generatePdfCV(parseInt(job.id), params);
      
      if (!response) {
        // For PDF generation failures, offer direct download link as fallback
        setError('PDF generation via API timed out. Click the "Download PDF" button below to get your PDF directly.');
        
        // Create updated job with placeholder CV
        const updatedJob = {
          ...job,
          cv: "placeholder", // Just a placeholder to indicate that direct download is available
          cv_format: 'pdf' as const
        };
        
        // Update the jobs array
        const updatedJobs = jobs.map(j => {
          if (j.id === job.id) {
            return updatedJob;
          }
          return j;
        });
        
        // Update both jobs list and selected job
        setJobs(updatedJobs);
        setSelectedJob(updatedJob); // Important: This ensures the UI updates
        setGeneratingCv(false);
        return; // Exit early
      }
      
      // Create updated job object with CV data
      const updatedJob = {
        ...job,
        cv: response.result,
        cv_format: 'pdf' as const
      };
      
      // Update the jobs array
      const updatedJobs = jobs.map(j => {
        if (j.id === job.id) {
          return updatedJob;
        }
        return j;
      });
      
      // Update both the jobs list and the selected job
      setJobs(updatedJobs);
      setSelectedJob(updatedJob); // Important: This ensures the UI shows the CV is ready
      setSuccess('PDF CV successfully generated!');
      
      // Auto-hide success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('PDF generation timed out. Try downloading directly.');
      console.error(err);
    } finally {
      setGeneratingCv(false);
    }
  };
  
  // Helper to get template name by ID
  const getTemplateNameById = (templateId: string | null) => {
    if (!templateId) return "default template";
    const template = templates.find(t => t.id === templateId);
    return template?.name || "selected template";
  };

  return (
    <>
      <Navbar />
      <div className="container mx-auto py-10">
        <h1 className="text-3xl font-bold mb-2">Job Applications</h1>
        <p className="text-muted-foreground mb-4">
          Add jobs you've applied to and generate tailored CVs for each position.
        </p>
        
        {/* Profile reminder notification */}
        <Card className="bg-primary/10 mb-8">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <div className="shrink-0 text-primary text-xl">ℹ️</div>
              <div>
                <h3 className="font-semibold mb-1">Important Reminder</h3>
                <p className="text-sm text-muted-foreground">
                  Make sure your <a href="/profile" className="font-semibold text-primary underline">Profile</a> is complete with skills, experience, and education before generating CVs. 
                  Your profile data is used to create personalized CVs for each job application.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Add New Job Form */}
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Add New Job Application</CardTitle>
            <CardDescription>
              Add a job posting you've applied to or plan to apply for.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="manual" className="w-full">
              <TabsList className="mb-4">
                <TabsTrigger value="manual">Manual Entry</TabsTrigger>
                <TabsTrigger value="url">Import from URL</TabsTrigger>
              </TabsList>
              
              {/* Manual Entry Tab - simplified with a single textarea */}
              <TabsContent value="manual">
                <form onSubmit={handleManualSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="jobListing">Job Description</Label>
                    <Textarea 
                      id="jobListing"
                      value={jobListing}
                      onChange={handleJobListingChange}
                      placeholder="Paste the entire job listing here..."
                      className="min-h-[300px]"
                      required
                    />
                    <p className="text-sm text-muted-foreground">
                      Paste the entire job description and requirements. This will be used to generate a tailored CV.
                    </p>
                  </div>
                  
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Adding...' : 'Add Job'}
                  </Button>
                </form>
              </TabsContent>
              
              {/* URL Import Tab */}
              <TabsContent value="url">
                <div className="p-6 bg-secondary/10 rounded-lg text-center">
                  <h3 className="text-lg font-semibold mb-2">Coming Soon!</h3>
                  <p className="text-muted-foreground mb-3">
                    Automatic job import from LinkedIn, Indeed, and other job boards will be available soon.
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Use the Manual Entry option for now to paste job descriptions directly.
                  </p>
                </div>
                
                {/* Hidden form for future implementation */}
                <form onSubmit={handleUrlSubmit} className="space-y-4 hidden">
                  <div className="space-y-2">
                    <Label htmlFor="job_url">Job Posting URL</Label>
                    <Input 
                      id="job_url"
                      value={jobUrl} 
                      onChange={handleUrlChange} 
                      placeholder="https://example.com/job-posting" 
                    />
                  </div>
                </form>
              </TabsContent>
            </Tabs>
            
            {/* Status messages */}
            {error && (
              <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md">
                {error}
              </div>
            )}
            
            {success && (
              <div className="mt-4 p-3 bg-primary/10 text-primary rounded-md">
                {success}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Job Listings and Generated CVs */}
        <h2 className="text-2xl font-semibold mb-4">Your Job Applications</h2>
        
        {/* Search and Filter Controls */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="search" className="mb-2 block">Search Jobs</Label>
                <Input
                  id="search"
                  placeholder="Search by title or company..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="company-filter" className="mb-2 block">Filter by Company</Label>
                <select
                  id="company-filter"
                  className="w-full p-2 border rounded-md"
                  value={filterCompany}
                  onChange={(e) => setFilterCompany(e.target.value)}
                >
                  <option value="">All Companies</option>
                  {companies.map(company => (
                    <option key={company} value={company}>{company}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex items-end">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setSearchTerm('');
                    setFilterCompany('');
                    setCurrentPage(1);
                  }}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {loading && !jobs.length ? (
          <div className="text-center py-10">
            <p>Loading jobs...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-muted-foreground">No job applications yet. Add your first job above.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left column: Job list */}
            <div className="lg:col-span-1">
              <h3 className="text-xl font-medium mb-3">Job Listings</h3>
              
              {/* Filtered jobs display */}
              <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-2">
                {/* Filter the jobs based on search and company filter */}
                {jobs
                  .filter(job => {
                    const matchesSearch = searchTerm === '' || 
                      job.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                      job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      job.description.toLowerCase().includes(searchTerm.toLowerCase());
                    
                    const matchesCompany = filterCompany === '' || job.company === filterCompany;
                    
                    return matchesSearch && matchesCompany;
                  })
                  // Pagination: slice the array to only show the current page
                  .slice((currentPage - 1) * jobsPerPage, currentPage * jobsPerPage)
                  .map(job => (
                    <Card 
                      key={job.id} 
                      className={`cursor-pointer ${selectedJob?.id === job.id ? 'ring-2 ring-primary' : ''} hover:bg-muted/20 transition-colors`}
                      onClick={() => setSelectedJob(job)}
                    >
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">
                          {job.title} - {job.company}
                        </CardTitle>
                        <CardDescription className="text-xs">{job.location || 'No location specified'}</CardDescription>
                      </CardHeader>
                      <CardContent className="pb-2">
                        <p className="line-clamp-2 text-sm text-muted-foreground">
                          {job.description.substring(0, 120)}...
                        </p>
                      </CardContent>
                      <CardFooter className="flex-col gap-2">
                        <div className="flex w-full justify-between items-center">
                          <div className="text-xs text-muted-foreground">
                            {(() => {
                              const templateId = getJobTemplate(job.id);
                              const defaultId = localStorage.getItem('defaultTemplateId');
                              
                              if (!templateId) {
                                return <>Using default template</>;
                              }
                              
                              if (templateId === defaultId) {
                                return <>Default: {getTemplateNameById(templateId)}</>;
                              }
                              
                              return <>Template: {getTemplateNameById(templateId)}</>;
                            })()}
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={(e) => {
                              e.stopPropagation();
                              // First select the job to show its details
                              setSelectedJob(job);
                              // Then generate the CV
                              generateCv(job);
                            }}
                            disabled={generatingCv && selectedJob?.id === job.id}
                            className="h-7 px-2 py-0 text-xs"
                          >
                            {generatingCv && selectedJob?.id === job.id ? 'Generating...' : 'Generate'}
                          </Button>
                        </div>
                      </CardFooter>
                    </Card>
                  ))}
              </div>
              
              {/* Pagination controls */}
              {jobs
                .filter(job => {
                  const matchesSearch = searchTerm === '' || 
                    job.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                    job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    job.description.toLowerCase().includes(searchTerm.toLowerCase());
                  
                  const matchesCompany = filterCompany === '' || job.company === filterCompany;
                  
                  return matchesSearch && matchesCompany;
                }).length > jobsPerPage && (
                <div className="flex justify-center mt-4 space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  
                  <span className="flex items-center px-3 text-sm">
                    Page {currentPage} of {Math.ceil(jobs
                      .filter(job => {
                        const matchesSearch = searchTerm === '' || 
                          job.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          job.description.toLowerCase().includes(searchTerm.toLowerCase());
                        
                        const matchesCompany = filterCompany === '' || job.company === filterCompany;
                        
                        return matchesSearch && matchesCompany;
                      }).length / jobsPerPage)}
                  </span>
                  
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setCurrentPage(prev => 
                      Math.min(prev + 1, Math.ceil(jobs
                        .filter(job => {
                          const matchesSearch = searchTerm === '' || 
                            job.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                            job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            job.description.toLowerCase().includes(searchTerm.toLowerCase());
                          
                          const matchesCompany = filterCompany === '' || job.company === filterCompany;
                          
                          return matchesSearch && matchesCompany;
                        }).length / jobsPerPage))
                    )}
                    disabled={currentPage === Math.ceil(jobs
                      .filter(job => {
                        const matchesSearch = searchTerm === '' || 
                          job.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          job.description.toLowerCase().includes(searchTerm.toLowerCase());
                        
                        const matchesCompany = filterCompany === '' || job.company === filterCompany;
                        
                        return matchesSearch && matchesCompany;
                      }).length / jobsPerPage)}
                  >
                    Next
                  </Button>
                </div>
              )}
            </div>
            
            {/* Right column: Selected job details & CV */}
            <div className="lg:col-span-2">
              <h3 className="text-xl font-medium mb-3">Tailored CV</h3>
              <Card className="h-[calc(100%-2rem)]">
                {!selectedJob ? (
                  <div className="flex items-center justify-center h-full p-6 text-center">
                    <p className="text-muted-foreground">Select a job to view or generate a tailored CV</p>
                  </div>
                ) : (
                  <>
                    <CardHeader>
                      <CardTitle>CV for {selectedJob.title} - {selectedJob.company}</CardTitle>
                      <CardDescription>{selectedJob.location || 'No location specified'}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {selectedJob.cv ? (
                        <div className="space-y-4">
                          {/* Options for already generated CV */}
                          <div className="space-y-4">
                            {/* Template selector */}
                            {templates.length > 0 && (
                              <div>
                                <Label htmlFor="regenerate-template-select" className="block text-left mb-2">
                                  Template
                                </Label>
                                <select
                                  id="regenerate-template-select"
                                  value={getJobTemplate(selectedJob.id)}
                                  onChange={(e) => setJobTemplate(selectedJob.id, e.target.value)}
                                  className="w-full p-2 border rounded-md"
                                >
                                  {templates.map(template => {
                                    const isDefault = template.id === (localStorage.getItem('defaultTemplateId') || '');
                                    return (
                                      <option key={template.id} value={template.id}>
                                        {isDefault ? `${template.name} (Default)` : template.name}
                                      </option>
                                    );
                                  })}
                                </select>
                              </div>
                            )}
                            
                            {/* Language Model selection */}
                            <div>
                              <Label htmlFor="regenerate-model-select" className="block text-left mb-2">
                                Language Model
                              </Label>
                              <select
                                id="regenerate-model-select"
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                className="w-full p-2 border rounded-md"
                              >
                                {languageModels.map(model => (
                                  <option key={model.id} value={model.id}>
                                    {model.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                            
                            {/* Custom Context input */}
                            <div>
                              <Label htmlFor="regenerate-custom-context" className="block text-left mb-2">
                                Custom Context
                              </Label>
                              <Textarea
                                id="regenerate-custom-context"
                                placeholder="Add additional instructions or context for CV generation..."
                                value={customContext}
                                onChange={(e) => setCustomContext(e.target.value)}
                                className="w-full p-2 border rounded-md min-h-[80px]"
                              />
                            </div>
                            
                            <Button 
                              onClick={() => {
                                // First update the selected job to clear the existing CV
                                // This forces the component to show the generating state
                                setSelectedJob({
                                  ...selectedJob,
                                  cv: undefined,
                                  cv_format: undefined
                                });
                                // Then generate the new CV
                                generateCv(selectedJob);
                              }}
                              disabled={generatingCv}
                              className="w-full"
                            >
                              {generatingCv ? 'Regenerating...' : 'Regenerate CV'}
                            </Button>
                          </div>

                          <div className="flex justify-end space-x-2">
                            {/* Download buttons */}
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => {
                                // Check if user has modified any generation parameters
                                const isUsingCustomParams = (
                                  selectedModel !== 'gpt-3.5-turbo' || // If not using default model
                                  customContext.trim() !== '' // If custom context is specified
                                );
                                
                                if (isUsingCustomParams) {
                                  // If custom params are set, use them to generate a new PDF
                                  setSuccess("Generating customized PDF with your parameters...");
                                  downloadCV(
                                    parseInt(selectedJob.id), 
                                    getJobTemplate(selectedJob.id) || undefined,
                                    selectedModel,
                                    customContext.trim() || undefined
                                  );
                                } else {
                                  // Use cached version if available by not passing model or context
                                  setSuccess("Downloading cached PDF (faster)...");
                                  downloadCV(
                                    parseInt(selectedJob.id),
                                    getJobTemplate(selectedJob.id) || undefined
                                  );
                                }
                                
                                // Auto-hide success message after 3 seconds
                                setTimeout(() => setSuccess(null), 3000);
                              }}
                            >
                              Download PDF
                            </Button>
                            {/* LaTeX options dropdown */}
                            <div className="relative inline-block">
                              <Button 
                                variant="outline" 
                                size="sm"
                                className="flex items-center gap-1"
                                onClick={() => {
                                  // Get the dropdown element
                                  const dropdown = document.getElementById(`latex-options-dropdown-${selectedJob.id}`);
                                  if (dropdown) {
                                    // Toggle the dropdown visibility
                                    dropdown.classList.toggle('hidden');
                                  }
                                }}
                              >
                                LaTeX Options
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <path d="M6 9l6 6 6-6"/>
                                </svg>
                              </Button>
                              
                              {/* Dropdown menu */}
                              <div 
                                id={`latex-options-dropdown-${selectedJob.id}`}
                                className="hidden absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10"
                                onBlur={() => {
                                  const dropdown = document.getElementById(`latex-options-dropdown-${selectedJob.id}`);
                                  if (dropdown) {
                                    dropdown.classList.add('hidden');
                                  }
                                }}
                              >
                                <div className="py-1">
                                  {/* Download LaTeX option */}
                                  <button
                                    className="w-full text-left block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    onClick={() => {
                                      // Download LaTeX source file
                                      const jobTemplateId = getJobTemplate(selectedJob.id);
                                      
                                      // Hide dropdown
                                      const dropdown = document.getElementById(`latex-options-dropdown-${selectedJob.id}`);
                                      if (dropdown) {
                                        dropdown.classList.add('hidden');
                                      }
                                      
                                      // Import and use our improved function
                                      import('@/services/templateService').then(({ downloadLatexSource }) => {
                                        downloadLatexSource(parseInt(selectedJob.id), jobTemplateId);
                                        setSuccess("Downloading LaTeX source file...");
                                        setTimeout(() => setSuccess(null), 3000);
                                      });
                                    }}
                                  >
                                    Download LaTeX Source
                                  </button>
                                  
                                  {/* Edit in Overleaf option */}
                                  <button
                                    className="w-full text-left block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    onClick={() => {
                                      // Hide dropdown
                                      const dropdown = document.getElementById(`latex-options-dropdown-${selectedJob.id}`);
                                      if (dropdown) {
                                        dropdown.classList.add('hidden');
                                      }
                                      
                                      // Import and use our new function
                                      import('@/services/templateService').then(({ editLatexOnline }) => {
                                        setSuccess("Opening LaTeX in Overleaf editor...");
                                        
                                        editLatexOnline(
                                          parseInt(selectedJob.id), 
                                          getJobTemplate(selectedJob.id),
                                          selectedJob.title,
                                          selectedJob.company
                                        );
                                        
                                        setTimeout(() => setSuccess(null), 5000);
                                      });
                                    }}
                                  >
                                    Edit in Overleaf
                                  </button>
                                  
                                  {/* Divider */}
                                  <div className="border-t border-gray-200 my-1"></div>
                                  
                                  {/* Header for recommended editors */}
                                  <div className="px-4 py-1 text-xs text-gray-500">
                                    Recommended LaTeX Editors
                                  </div>
                                  
                                  {/* List of recommended editors */}
                                  {[
                                    { name: 'Overleaf', url: 'https://www.overleaf.com' },
                                    { name: 'Papeeria', url: 'https://papeeria.com' },
                                    { name: 'TeXmaker (Desktop)', url: 'https://www.xm1math.net/texmaker/' }
                                  ].map(editor => (
                                    <a
                                      key={editor.name}
                                      href={editor.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="block px-4 py-2 text-xs text-gray-700 hover:bg-gray-100"
                                      onClick={() => {
                                        // Hide dropdown
                                        const dropdown = document.getElementById(`latex-options-dropdown-${selectedJob.id}`);
                                        if (dropdown) {
                                          dropdown.classList.add('hidden');
                                        }
                                      }}
                                    >
                                      {editor.name}
                                    </a>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Informacja o wygenerowanym PDF */}
                          <div className="mt-4 text-center">
                            <p className="text-muted-foreground mb-4">PDF CV has been generated using {getTemplateNameById(getJobTemplate(selectedJob.id))}.</p>
                            
                            {selectedJob.cv === "placeholder" ? (
                              // Direct download buttons for when the API times out
                              <div className="flex flex-col items-center gap-3">
                                <p className="text-amber-600 text-sm">API generation timed out. Try downloading directly.</p>
                              </div>
                            ) : (
                              // Pokazuj informację o pomyślnym wygenerowaniu
                              <p className="text-green-600 text-sm">CV successfully generated!</p>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-6">
                          <p className="text-muted-foreground mb-4">No CV generated yet</p>
                          
                          {/* Generation options */}
                          <div className="space-y-4">
                            {/* Template selector */}
                            {templates.length > 0 && (
                              <div>
                                <Label htmlFor="template-select" className="block text-left mb-2">
                                  Select Template
                                </Label>
                                <select
                                  id="template-select"
                                  value={getJobTemplate(selectedJob.id)}
                                  onChange={(e) => setJobTemplate(selectedJob.id, e.target.value)}
                                  className="w-full p-2 border rounded-md"
                                >
                                  {templates.map(template => {
                                    const isDefault = template.id === (localStorage.getItem('defaultTemplateId') || '');
                                    return (
                                      <option key={template.id} value={template.id}>
                                        {isDefault ? `${template.name} (Default)` : template.name}
                                      </option>
                                    );
                                  })}
                                </select>
                              </div>
                            )}
                            
                            {/* Language Model selection */}
                            <div>
                              <Label htmlFor="model-select" className="block text-left mb-2">
                                Language Model
                              </Label>
                              <select
                                id="model-select"
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                className="w-full p-2 border rounded-md"
                              >
                                {languageModels.map(model => (
                                  <option key={model.id} value={model.id}>
                                    {model.name}
                                  </option>
                                ))}
                              </select>
                              <p className="text-xs text-muted-foreground mt-1">
                                Select the AI model that will tailor your CV content to this job listing.
                              </p>
                            </div>
                            
                            {/* Custom Context input */}
                            <div>
                              <Label htmlFor="custom-context" className="block text-left mb-2">
                                Custom Context
                              </Label>
                              <Textarea
                                id="custom-context"
                                placeholder="Add additional instructions or context for CV generation..."
                                value={customContext}
                                onChange={(e) => setCustomContext(e.target.value)}
                                className="w-full p-2 border rounded-md min-h-[100px]"
                              />
                              <p className="text-xs text-muted-foreground mt-1">
                                Optional: Add specific instructions for how to tailor your CV to this job.
                              </p>
                            </div>
                            
                            {/* Import from URL - coming soon */}
                            <div className="mt-4 p-3 bg-secondary/10 text-secondary rounded-md">
                              <h4 className="font-semibold text-sm">Coming Soon</h4>
                              <p className="text-xs">
                                Import job data directly from LinkedIn, Indeed, and other job boards with a single click.
                              </p>
                            </div>
                          </div>
                          
                          <Button 
                            onClick={() => generateCv(selectedJob)}
                            disabled={generatingCv}
                            className="mt-4 w-full"
                          >
                            {generatingCv ? 'Generating...' : 'Generate PDF CV'}
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </>
                )}
              </Card>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Jobs;