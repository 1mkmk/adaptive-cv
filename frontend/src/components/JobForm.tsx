import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { createJob } from '@/services/jobService';
import { useAuth } from '@/context/AuthContext';

interface JobFormProps {
  onSuccess?: () => void;
  redirectOnLogin?: boolean;
}

const JobForm: React.FC<JobFormProps> = ({ onSuccess, redirectOnLogin = true }) => {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  const [jobListing, setJobListing] = useState('');
  const [jobUrl, setJobUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleJobListingChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJobListing(e.target.value);
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setJobUrl(e.target.value);
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      if (redirectOnLogin) {
        // Save job listing to localStorage before redirecting
        localStorage.setItem('pendingJobListing', jobListing);
        login();
        return;
      } else {
        setError('Please log in to add jobs');
        return;
      }
    }
    
    if (!jobListing.trim()) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      setSuccess('Processing job listing using AI...');
      
      const response = await createJob({
        title: '',
        company: '',
        location: 'Not specified',
        description: jobListing
      });
      
      if (response) {
        setSuccess('Job processed and added successfully with AI-extracted details!');
        setJobListing('');
        
        if (onSuccess) {
          onSuccess();
        } else {
          // Navigate to jobs page after 1 second
          setTimeout(() => {
            navigate('/jobs');
          }, 1000);
        }
      } else {
        throw new Error('Failed to add job');
      }
    } catch (err) {
      setError('Failed to add job. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      if (redirectOnLogin) {
        // Save job url to localStorage before redirecting
        localStorage.setItem('pendingJobUrl', jobUrl);
        login();
        return;
      } else {
        setError('Please log in to add jobs');
        return;
      }
    }
    
    if (!jobUrl) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await createJob({ 
        job_url: jobUrl,
        title: '',
        company: '',
        location: '',
        description: ''
      });
      
      if (response) {
        setSuccess('Job imported successfully!');
        setJobUrl('');
        
        if (onSuccess) {
          onSuccess();
        } else {
          // Navigate to jobs page after 1 second
          setTimeout(() => {
            navigate('/jobs');
          }, 1000);
        }
      } else {
        throw new Error('Failed to import job');
      }
    } catch (err) {
      setError('Failed to import job. Please check the URL and try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mb-10">
      <CardHeader>
        <CardTitle>Add Job Application</CardTitle>
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
          
          {/* Manual Entry Tab */}
          <TabsContent value="manual">
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="jobListing">Job Description</Label>
                <Textarea 
                  id="jobListing"
                  value={jobListing}
                  onChange={handleJobListingChange}
                  placeholder="Paste the entire job listing here..."
                  className="min-h-[250px]"
                  required
                />
                <p className="text-sm text-muted-foreground">
                  Paste the entire job description and requirements. This will be used to generate a tailored CV.
                </p>
              </div>
              
              <Button type="submit" disabled={loading}>
                {isAuthenticated 
                  ? (loading ? 'Adding...' : 'Add Job') 
                  : 'Login & Add Job'}
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
  );
};

export default JobForm;