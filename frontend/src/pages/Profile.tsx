import React, { useState, useEffect, useRef } from 'react';
import Navbar from "@/components/ui/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { getProfile, saveProfile, importCVProfile, uploadProfilePhoto, generateProfileFromPrompt, CandidateProfile, Experience, Education, ProfileGenerationPrompt } from '@/services/profileService';

const Profile: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [generatingProfile, setGeneratingProfile] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Generation form states
  const [prompt, setPrompt] = useState('');
  // Creativity levels for CV generation (not for profile generation)
  const [creativityLevels, setCreativityLevels] = useState({
    personal_info: 5,
    summary: 5,
    experience: 5,
    education: 5,
    skills: 5,
    projects: 5,
    awards: 5,
    presentations: 5,
    interests: 5
  });
  
  // Form state - Basic fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [summary, setSummary] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [location, setLocation] = useState('');
  const [linkedin, setLinkedin] = useState('');
  const [website, setWebsite] = useState('');
  
  // Experience state 
  const [experiences, setExperiences] = useState([{
    company: '',
    position: '',
    start_date: '',
    end_date: '',
    current: false,
    description: ''
  }]);
  
  // Education state
  const [educations, setEducations] = useState([{
    institution: '',
    degree: '',
    field: '',
    start_date: '',
    end_date: '',
    current: false
  }]);
  
  // Extended fields from all templates
  const [jobTitle, setJobTitle] = useState('');
  const [address, setAddress] = useState<{
    line1: string;
    line2?: string;
    city: string;
    state?: string;
    postalCode?: string;
    country: string;
  }>({
    line1: '',
    line2: '',
    city: '',
    state: '',
    postalCode: '',
    country: ''
  });
  
  // Skills categories
  const [skillCategories, setSkillCategories] = useState<{
    name: string;
    skills: string[];
  }[]>([
    { name: 'Programming Languages', skills: [] },
    { name: 'Frameworks & Libraries', skills: [] },
    { name: 'Tools & Technologies', skills: [] },
    { name: 'Soft Skills', skills: [] }
  ]);
  
  // Interests
  const [interests, setInterests] = useState<{
    type: 'professional' | 'personal';
    description: string;
  }[]>([
    { type: 'professional', description: '' },
    { type: 'personal', description: '' }
  ]);
  
  // Awards
  const [awards, setAwards] = useState<{
    title: string;
    date: string;
    issuer: string;
    description: string;
  }[]>([{
    title: '',
    date: '',
    issuer: '',
    description: ''
  }]);
  
  // Presentations
  const [presentations, setPresentations] = useState<{
    title: string;
    date: string;
    venue: string;
    description: string;
  }[]>([{
    title: '',
    date: '',
    venue: '',
    description: ''
  }]);
  
  // Projects
  const [projects, setProjects] = useState<{
    name: string;
    description: string;
    url?: string;
    start_date?: string;
    end_date?: string;
  }[]>([{
    name: '',
    description: '',
    url: '',
    start_date: '',
    end_date: ''
  }]);

  // Load profile data on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profileData = await getProfile();
        if (profileData) {
          // Populate basic form fields with existing data
          setName(profileData.name || '');
          setEmail(profileData.email || '');
          setPhone(profileData.phone || '');
          setSummary(profileData.summary || '');
          setSkills(profileData.skills || []);
          setLocation(profileData.location || '');
          setLinkedin(profileData.linkedin || '');
          setWebsite(profileData.website || '');
          if (profileData.photo) {
            setPhotoPreview(profileData.photo);
          }
          
          // Set experience and education
          setExperiences(profileData.experience?.length ? profileData.experience : [{ 
            company: '',
            position: '',
            start_date: '',
            end_date: '',
            current: false,
            description: ''
          }]);
          
          setEducations(profileData.education?.length ? profileData.education : [{
            institution: '',
            degree: '',
            field: '',
            start_date: '',
            end_date: '',
            current: false
          }]);
          
          // Set extended fields
          if (profileData.job_title) setJobTitle(profileData.job_title);
          if (profileData.address) setAddress(profileData.address);
          
          // Set skill categories if available
          if (profileData.skill_categories && profileData.skill_categories.length > 0) {
            setSkillCategories(profileData.skill_categories);
          }
          
          // Set interests if available
          if (profileData.interests && profileData.interests.length > 0) {
            setInterests(profileData.interests);
          }
          
          // Set awards if available
          if (profileData.awards && profileData.awards.length > 0) {
            setAwards(profileData.awards);
          }
          
          // Set presentations if available
          if (profileData.presentations && profileData.presentations.length > 0) {
            setPresentations(profileData.presentations);
          }
          
          // Set projects if available
          if (profileData.projects && profileData.projects.length > 0) {
            setProjects(profileData.projects);
          }
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
      }
    };
    
    loadProfile();
  }, []);
  
  const handlePhotoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.type.match('image.*')) {
        alert('Please select an image file');
        return;
      }
      
      // Show local preview immediately
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target && event.target.result) {
          setPhotoPreview(event.target.result.toString());
        }
      };
      reader.readAsDataURL(file);
      
      try {
        // Upload to server
        setLoading(true);
        setError(null);
        const updatedProfile = await uploadProfilePhoto(file);
        if (updatedProfile && updatedProfile.photo) {
          setPhotoPreview(updatedProfile.photo);
          setSuccess("Photo uploaded successfully");
        }
      } catch (err) {
        console.error("Error uploading photo:", err);
        setError("Failed to upload photo. Please try again.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCVImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImportLoading(true);
      setError(null);
      setSuccess(null);
      
      try {
        const importedProfile = await importCVProfile(file);
        
        // Update form with imported data
        if (importedProfile) {
          // Check if this is a placeholder CV (from a PDF that couldn't be parsed)
          const isPlaceholder = importedProfile.summary && 
            importedProfile.summary.includes("placeholder CV created because the original PDF could not be parsed");
          
          // Basic fields
          setName(importedProfile.name || '');
          setEmail(importedProfile.email || '');
          setPhone(importedProfile.phone || '');
          setSummary(importedProfile.summary || '');
          setSkills(importedProfile.skills || []);
          setLocation(importedProfile.location || '');
          setLinkedin(importedProfile.linkedin || '');
          setWebsite(importedProfile.website || '');
          
          // Experience and education
          setExperiences(importedProfile.experience && importedProfile.experience.length > 0 
            ? importedProfile.experience 
            : [{ 
                company: '',
                position: '',
                start_date: '',
                end_date: '',
                current: false,
                description: ''
              }]);
          
          setEducations(importedProfile.education && importedProfile.education.length > 0 
            ? importedProfile.education 
            : [{
                institution: '',
                degree: '',
                field: '',
                start_date: '',
                end_date: '',
                current: false
              }]);
          
          // Extended fields
          if (importedProfile.job_title) {
            setJobTitle(importedProfile.job_title);
          }
          
          if (importedProfile.address) {
            setAddress(importedProfile.address);
          }
          
          if (importedProfile.projects && importedProfile.projects.length > 0) {
            setProjects(importedProfile.projects);
          }
          
          if (importedProfile.skill_categories && importedProfile.skill_categories.length > 0) {
            setSkillCategories(importedProfile.skill_categories);
          }
          
          if (importedProfile.awards && importedProfile.awards.length > 0) {
            setAwards(importedProfile.awards);
          }
          
          if (importedProfile.presentations && importedProfile.presentations.length > 0) {
            setPresentations(importedProfile.presentations);
          }
          
          if (importedProfile.interests && importedProfile.interests.length > 0) {
            setInterests(importedProfile.interests);
          }
          
          if (isPlaceholder) {
            setSuccess("Your PDF was processed, but full text extraction wasn't possible. We've created a placeholder profile that you should edit with your actual information.");
          } else {
            setSuccess("Successfully imported CV data! Please review all sections and save your profile.");
          }
        }
      } catch (err: any) {
        console.error("Error importing CV:", err);
        
        // Extract API error message if available
        let errorMessage = "Failed to import CV. Please try again or fill the form manually.";
        
        if (err.message && err.message.includes("scanned or protected")) {
          errorMessage = "The PDF appears to be scanned or protected. Text extraction failed. Please try uploading a different file format.";
        } else if (err.message) {
          // Get details from error message if available
          errorMessage = `CV import failed: ${err.message}`;
        }
        
        setError(errorMessage);
      } finally {
        setImportLoading(false);
        
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      console.log("Submitting profile form...");
      
      // Create profile data object with all fields
      const profileData: CandidateProfile = {
        // Basic fields
        name,
        email,
        phone,
        summary,
        location,
        linkedin,
        website,
        photo: photoPreview || undefined,
        skills: skills.length ? skills : summary.split(',').map(s => s.trim()),
        experience: experiences,
        education: educations,
        
        // Extended fields
        job_title: jobTitle,
        address: address,
        interests: interests,
        awards: awards,
        presentations: presentations,
        projects: projects,
        skill_categories: skillCategories,
        creativity_levels: creativityLevels
      };
      
      console.log("Profile data prepared, sending to API...");
      const response = await saveProfile(profileData);
      console.log("Profile saved response:", response);
      setSuccess('Profile saved successfully!');
    } catch (err) {
      setError('Failed to save profile. Please try again.');
      console.error("Error in handleSubmit:", err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleGenerateProfileFromPrompt = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt to generate a profile.');
      return;
    }
    
    setGeneratingProfile(true);
    setError(null);
    setSuccess(null);
    
    try {
      const generationData: ProfileGenerationPrompt = {
        prompt: prompt
      };
      
      const generatedProfile = await generateProfileFromPrompt(generationData);
      
      if (generatedProfile) {
        // Update all form fields with generated data
        setName(generatedProfile.name || '');
        setEmail(generatedProfile.email || '');
        setPhone(generatedProfile.phone || '');
        setSummary(generatedProfile.summary || '');
        setSkills(generatedProfile.skills || []);
        setLocation(generatedProfile.location || '');
        setLinkedin(generatedProfile.linkedin || '');
        setWebsite(generatedProfile.website || '');
        
        // Update experience and education
        if (generatedProfile.experience && generatedProfile.experience.length > 0) {
          setExperiences(generatedProfile.experience);
        }
        
        if (generatedProfile.education && generatedProfile.education.length > 0) {
          setEducations(generatedProfile.education);
        }
        
        // Update extended fields
        if (generatedProfile.job_title) {
          setJobTitle(generatedProfile.job_title);
        }
        
        if (generatedProfile.address) {
          setAddress(generatedProfile.address);
        }
        
        if (generatedProfile.projects && generatedProfile.projects.length > 0) {
          setProjects(generatedProfile.projects);
        }
        
        if (generatedProfile.skill_categories && generatedProfile.skill_categories.length > 0) {
          setSkillCategories(generatedProfile.skill_categories);
        }
        
        if (generatedProfile.awards && generatedProfile.awards.length > 0) {
          setAwards(generatedProfile.awards);
        }
        
        if (generatedProfile.presentations && generatedProfile.presentations.length > 0) {
          setPresentations(generatedProfile.presentations);
        }
        
        if (generatedProfile.interests && generatedProfile.interests.length > 0) {
          setInterests(generatedProfile.interests);
        }
        
        setSuccess('Profile generated successfully! Please review all sections and save your profile.');
      }
    } catch (err: any) {
      console.error('Error generating profile:', err);
      
      let errorMessage = 'Failed to generate profile. Please try again.';
      if (err.message) {
        errorMessage = `Profile generation failed: ${err.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setGeneratingProfile(false);
    }
  };

  // Add more experience form entry
  const addExperience = () => {
    setExperiences([
      ...experiences,
      {
        company: '',
        position: '',
        start_date: '',
        end_date: '',
        current: false,
        description: ''
      }
    ]);
  };

  // Add more education form entry
  const addEducation = () => {
    setEducations([
      ...educations,
      {
        institution: '',
        degree: '',
        field: '',
        start_date: '',
        end_date: '',
        current: false
      }
    ]);
  };

  // Update experience item field
  const updateExperience = (index: number, field: string, value: string | boolean) => {
    const updatedExperiences = [...experiences];
    updatedExperiences[index] = {
      ...updatedExperiences[index],
      [field]: value
    };
    setExperiences(updatedExperiences);
  };

  // Update education item field
  const updateEducation = (index: number, field: string, value: string | boolean) => {
    const updatedEducations = [...educations];
    updatedEducations[index] = {
      ...updatedEducations[index],
      [field]: value
    };
    setEducations(updatedEducations);
  };
  
  // Helper functions for additional fields
  
  // Update address fields
  const updateAddress = (field: keyof typeof address, value: string) => {
    setAddress({
      ...address,
      [field]: value
    });
  };
  
  // Update skill category
  const updateSkillCategory = (index: number, field: 'name' | 'skills', value: string | string[]) => {
    const updatedCategories = [...skillCategories];
    if (field === 'name') {
      updatedCategories[index] = {
        ...updatedCategories[index],
        name: value as string
      };
    } else {
      updatedCategories[index] = {
        ...updatedCategories[index],
        skills: value as string[]
      };
    }
    setSkillCategories(updatedCategories);
  };
  
  // Add a new skill category
  const addSkillCategory = () => {
    setSkillCategories([...skillCategories, { name: '', skills: [] }]);
  };
  
  // Update interest
  const updateInterest = (index: number, field: keyof typeof interests[0], value: any) => {
    const updatedInterests = [...interests];
    updatedInterests[index] = {
      ...updatedInterests[index],
      [field]: value
    };
    setInterests(updatedInterests);
  };
  
  // Add new interest
  const addInterest = () => {
    setInterests([...interests, { type: 'personal', description: '' }]);
  };
  
  // Update award
  const updateAward = (index: number, field: keyof typeof awards[0], value: string) => {
    const updatedAwards = [...awards];
    updatedAwards[index] = {
      ...updatedAwards[index],
      [field]: value
    };
    setAwards(updatedAwards);
  };
  
  // Add new award
  const addAward = () => {
    setAwards([...awards, { title: '', date: '', issuer: '', description: '' }]);
  };
  
  // Update presentation
  const updatePresentation = (index: number, field: keyof typeof presentations[0], value: string) => {
    const updatedPresentations = [...presentations];
    updatedPresentations[index] = {
      ...updatedPresentations[index],
      [field]: value
    };
    setPresentations(updatedPresentations);
  };
  
  // Add new presentation
  const addPresentation = () => {
    setPresentations([...presentations, { title: '', date: '', venue: '', description: '' }]);
  };
  
  // Update project
  const updateProject = (index: number, field: keyof typeof projects[0], value: string) => {
    const updatedProjects = [...projects];
    updatedProjects[index] = {
      ...updatedProjects[index],
      [field]: value
    };
    setProjects(updatedProjects);
  };
  
  // Add new project
  const addProject = () => {
    setProjects([...projects, { name: '', description: '', url: '', start_date: '', end_date: '' }]);
  };
  
  // Update creativity level for a section - used for CV generation
  const updateCreativityLevel = (section: keyof typeof creativityLevels, value: number) => {
    setCreativityLevels({
      ...creativityLevels,
      [section]: value
    });
  };

  return (
    <>
      <Navbar />
      <div className="container mx-auto py-10">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Your CV Profile</h1>
          <div className="flex gap-2">
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,.doc,.docx,.txt"
              className="hidden"
              onChange={handleCVImport}
            />
            <Button 
              type="button" 
              variant="outline" 
              disabled={importLoading}
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              {importLoading ? 'Importing...' : 'Import from CV (.pdf, .txt)'}
            </Button>
          </div>
        </div>
        
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Generate Profile from Prompt</CardTitle>
            <CardDescription>
              Generate a complete CV profile using AI. Describe the profile you want.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <Label htmlFor="prompt">Profile Description</Label>
                <Textarea 
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe the profile you want to generate, e.g.: 'A software developer with 5 years of experience in React and Node.js, who graduated from MIT and worked at Google'"
                  className="min-h-[100px]"
                />
              </div>
              
              
              <Button 
                type="button" 
                onClick={handleGenerateProfileFromPrompt}
                disabled={generatingProfile || !prompt.trim()}
                className="w-full"
              >
                {generatingProfile ? 'Generating...' : 'Generate Profile'}
              </Button>
            </div>
          </CardContent>
        </Card>
        
        <p className="text-muted-foreground mb-8">
          Fill out the form below to create your comprehensive CV, import data from an existing CV, or use the generator above.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-md">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-primary/10 text-primary rounded-md">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <Accordion type="single" collapsible className="w-full mb-6" defaultValue="personal-info">
            {/* Personal Information */}
            <AccordionItem value="personal-info">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Personal Information</h2>
              </AccordionTrigger>
              <AccordionContent>
                <Card>
                  <CardHeader>
                    <CardTitle>Personal Information</CardTitle>
                    <CardDescription>
                      <div className="space-y-2">
                        <p>Adjust how creative the AI should be when generating CV for this section</p>
                        <div className="flex items-center gap-2">
                          <Label htmlFor="creativity-personal_info">Creativity Level:</Label>
                          <span className="text-muted-foreground ml-auto">{creativityLevels.personal_info}/10</span>
                        </div>
                        <input 
                          id="creativity-personal_info"
                          type="range" 
                          min="0" 
                          max="10" 
                          value={creativityLevels.personal_info}
                          onChange={(e) => updateCreativityLevel('personal_info', parseInt(e.target.value))}
                          className="w-full"
                        />
                      </div>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    {/* Photo Upload Section */}
                    <div className="mb-6">
                      <Label htmlFor="profile-photo" className="block mb-2">Profile Photo</Label>
                      <div className="flex items-center gap-4">
                        <div className="flex flex-col items-center gap-2">
                          <Avatar className="w-24 h-24">
                            {photoPreview ? (
                              <AvatarImage src={photoPreview} alt="Profile preview" />
                            ) : (
                              <AvatarFallback>
                                <span className="text-2xl">+</span>
                              </AvatarFallback>
                            )}
                          </Avatar>
                          <div className="flex gap-2">
                            <Button 
                              type="button" 
                              variant="outline" 
                              size="sm"
                              onClick={() => document.getElementById('profile-photo')?.click()}
                            >
                              Upload
                            </Button>
                            {photoPreview && (
                              <Button 
                                type="button" 
                                variant="outline" 
                                size="sm"
                                onClick={() => setPhotoPreview(null)}
                              >
                                Remove
                              </Button>
                            )}
                          </div>
                          <input
                            id="profile-photo"
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={handlePhotoChange}
                          />
                        </div>
                        <div className="text-sm text-muted-foreground">
                          <p>Upload a professional photo for your CV.</p>
                          <p>Recommended: square format, high resolution.</p>
                          <p>Max size: 5MB</p>
                        </div>
                      </div>
                    </div>
                    <Separator className="my-6" />

                    <div className="space-y-2 mb-4">
                      <Label htmlFor="name">Full Name *</Label>
                      <Input 
                        id="name" 
                        value={name} 
                        onChange={(e) => setName(e.target.value)} 
                        placeholder="Enter your full name" 
                        required 
                      />
                    </div>
                    
                    {/* New: Job Title field */}
                    <div className="space-y-2 mb-4">
                      <Label htmlFor="jobTitle">Current Position / Job Title *</Label>
                      <Input 
                        id="jobTitle" 
                        value={jobTitle} 
                        onChange={(e) => setJobTitle(e.target.value)} 
                        placeholder="Software Engineer, Project Manager, etc." 
                      />
                      <p className="text-xs text-muted-foreground">Required for Wenneker CV template</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div className="space-y-2">
                        <Label htmlFor="email">Email *</Label>
                        <Input 
                          id="email" 
                          type="email" 
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="email@example.com" 
                          required 
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone Number *</Label>
                        <Input 
                          id="phone" 
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+1 (555) 000-0000" 
                          required 
                        />
                      </div>
                    </div>

                    {/* Address fields */}
                    <div className="mb-4">
                      <Label className="block mb-2">Address *</Label>
                      <Card>
                        <CardContent className="pt-6">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="addressLine1">Address Line 1</Label>
                              <Input 
                                id="addressLine1" 
                                value={address.line1}
                                onChange={(e) => updateAddress('line1', e.target.value)}
                                placeholder="123 Main St" 
                              />
                            </div>
                            
                            <div className="space-y-2">
                              <Label htmlFor="addressLine2">Address Line 2 (Optional)</Label>
                              <Input 
                                id="addressLine2" 
                                value={address.line2 || ''}
                                onChange={(e) => updateAddress('line2', e.target.value)}
                                placeholder="Apt 4B" 
                              />
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label htmlFor="city">City</Label>
                                <Input 
                                  id="city" 
                                  value={address.city}
                                  onChange={(e) => updateAddress('city', e.target.value)}
                                  placeholder="New York" 
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor="state">State/Province</Label>
                                <Input 
                                  id="state" 
                                  value={address.state || ''}
                                  onChange={(e) => updateAddress('state', e.target.value)}
                                  placeholder="NY" 
                                />
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label htmlFor="postalCode">Postal Code</Label>
                                <Input 
                                  id="postalCode" 
                                  value={address.postalCode || ''}
                                  onChange={(e) => updateAddress('postalCode', e.target.value)}
                                  placeholder="10001" 
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor="country">Country</Label>
                                <Input 
                                  id="country" 
                                  value={address.country}
                                  onChange={(e) => updateAddress('country', e.target.value)}
                                  placeholder="United States" 
                                />
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                      <p className="text-xs text-muted-foreground mt-1">Required for Wenneker CV template</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div className="space-y-2">
                        <Label htmlFor="location">Location (City, Country)</Label>
                        <Input 
                          id="location" 
                          value={location}
                          onChange={(e) => setLocation(e.target.value)}
                          placeholder="New York, USA" 
                        />
                        <p className="text-xs text-muted-foreground">Used in the FAANG template</p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="linkedin">LinkedIn Profile</Label>
                        <Input 
                          id="linkedin" 
                          value={linkedin}
                          onChange={(e) => setLinkedin(e.target.value)}
                          placeholder="linkedin.com/in/yourprofile" 
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="website">Personal Website/Portfolio</Label>
                      <Input 
                        id="website" 
                        value={website}
                        onChange={(e) => setWebsite(e.target.value)}
                        placeholder="https://yourwebsite.com" 
                      />
                    </div>
                  </CardContent>
                </Card>
              </AccordionContent>
            </AccordionItem>
               
            {/* Professional Summary */}
            <AccordionItem value="professional-summary">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Professional Summary</h2>
              </AccordionTrigger>
              <AccordionContent>
                <Card>
                  <CardHeader>
                    <CardTitle>Professional Summary</CardTitle>
                    <CardDescription>
                      <div className="space-y-2">
                        <p>Adjust how creative the AI should be when generating CV for this section</p>
                        <div className="flex items-center gap-2">
                          <Label htmlFor="creativity-summary">Creativity Level:</Label>
                          <span className="text-muted-foreground ml-auto">{creativityLevels.summary}/10</span>
                        </div>
                        <input 
                          id="creativity-summary"
                          type="range" 
                          min="0" 
                          max="10" 
                          value={creativityLevels.summary}
                          onChange={(e) => updateCreativityLevel('summary', parseInt(e.target.value))}
                          className="w-full"
                        />
                      </div>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <div className="space-y-2">
                      <Label htmlFor="summary">Professional Summary *</Label>
                      <Textarea 
                        id="summary"
                        value={summary}
                        onChange={(e) => setSummary(e.target.value)} 
                        placeholder="Write a concise summary of your professional background, key skills, and career goals (150-200 words recommended)"
                        className="min-h-[120px]"
                        required
                      />
                    </div>
                  </CardContent>
                </Card>
              </AccordionContent>
            </AccordionItem>

            {/* Work Experience */}
            <AccordionItem value="work-experience">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Work Experience</h2>
              </AccordionTrigger>
              <AccordionContent>
                <div className="mb-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Work Experience</CardTitle>
                      <CardDescription>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-experience">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.experience}/10</span>
                          </div>
                          <input 
                            id="creativity-experience"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.experience}
                            onChange={(e) => updateCreativityLevel('experience', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </div>
                {experiences.map((exp, index) => (
                  <Card className="mb-4" key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">Experience {index + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`jobTitle${index}`}>Job Title *</Label>
                          <Input 
                            id={`jobTitle${index}`}
                            value={exp.position}
                            onChange={(e) => updateExperience(index, 'position', e.target.value)}
                            placeholder="Software Developer" 
                            required 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`company${index}`}>Company *</Label>
                          <Input 
                            id={`company${index}`}
                            value={exp.company}
                            onChange={(e) => updateExperience(index, 'company', e.target.value)}
                            placeholder="Company Name" 
                            required 
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`startDate${index}`}>Start Date *</Label>
                          <Input 
                            id={`startDate${index}`}
                            value={exp.start_date}
                            onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                            type="month" 
                            required 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`endDate${index}`}>End Date</Label>
                          <Input 
                            id={`endDate${index}`}
                            value={exp.end_date}
                            onChange={(e) => updateExperience(index, 'end_date', e.target.value)}
                            type="month"
                            disabled={exp.current}
                          />
                          <div className="flex items-center mt-2">
                            <input 
                              type="checkbox" 
                              id={`currentJob${index}`} 
                              className="mr-2"
                              checked={exp.current}
                              onChange={(e) => updateExperience(index, 'current', e.target.checked)}
                            />
                            <Label htmlFor={`currentJob${index}`}>I currently work here</Label>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`jobDescription${index}`}>Job Description & Achievements *</Label>
                        <Textarea 
                          id={`jobDescription${index}`}
                          value={exp.description}
                          onChange={(e) => updateExperience(index, 'description', e.target.value)}
                          placeholder="Describe your responsibilities and key achievements in this role" 
                          className="min-h-[120px]"
                          required
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Button variant="outline" className="w-full" onClick={addExperience}>
                  + Add Another Work Experience
                </Button>
              </AccordionContent>
            </AccordionItem>

            {/* Education */}
            <AccordionItem value="education">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Education</h2>
              </AccordionTrigger>
              <AccordionContent>
                <div className="mb-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Education</CardTitle>
                      <CardDescription>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-education">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.education}/10</span>
                          </div>
                          <input 
                            id="creativity-education"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.education}
                            onChange={(e) => updateCreativityLevel('education', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </div>
                {educations.map((edu, index) => (
                  <Card className="mb-4" key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">Education {index + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`degree${index}`}>Degree/Certificate *</Label>
                          <Input 
                            id={`degree${index}`}
                            value={edu.degree}
                            onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                            placeholder="Bachelor of Science in Computer Science" 
                            required 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`institution${index}`}>Institution *</Label>
                          <Input 
                            id={`institution${index}`}
                            value={edu.institution}
                            onChange={(e) => updateEducation(index, 'institution', e.target.value)}
                            placeholder="University Name" 
                            required 
                          />
                        </div>
                      </div>

                      <div className="space-y-2 mb-4">
                        <Label htmlFor={`field${index}`}>Field of Study *</Label>
                        <Input 
                          id={`field${index}`}
                          value={edu.field}
                          onChange={(e) => updateEducation(index, 'field', e.target.value)}
                          placeholder="Computer Science" 
                          required 
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`eduStartDate${index}`}>Start Date *</Label>
                          <Input 
                            id={`eduStartDate${index}`}
                            value={edu.start_date}
                            onChange={(e) => updateEducation(index, 'start_date', e.target.value)}
                            type="month" 
                            required 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`eduEndDate${index}`}>End Date</Label>
                          <Input 
                            id={`eduEndDate${index}`}
                            value={edu.end_date}
                            onChange={(e) => updateEducation(index, 'end_date', e.target.value)}
                            type="month"
                            disabled={edu.current}
                          />
                          <div className="flex items-center mt-2">
                            <input 
                              type="checkbox" 
                              id={`currentEdu${index}`} 
                              className="mr-2"
                              checked={edu.current}
                              onChange={(e) => updateEducation(index, 'current', e.target.checked)}
                            />
                            <Label htmlFor={`currentEdu${index}`}>I'm currently studying here</Label>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Button variant="outline" className="w-full" onClick={addEducation}>
                  + Add Another Education
                </Button>
              </AccordionContent>
            </AccordionItem>

            {/* Projects - New Section */}
            <AccordionItem value="projects">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Projects</h2>
              </AccordionTrigger>
              <AccordionContent>
                <div className="mb-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Projects</CardTitle>
                      <CardDescription>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-projects">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.projects}/10</span>
                          </div>
                          <input 
                            id="creativity-projects"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.projects}
                            onChange={(e) => updateCreativityLevel('projects', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </div>
                {projects.map((project, index) => (
                  <Card className="mb-4" key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">Project {index + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 mb-4">
                        <Label htmlFor={`projectName${index}`}>Project Name *</Label>
                        <Input 
                          id={`projectName${index}`}
                          value={project.name}
                          onChange={(e) => updateProject(index, 'name', e.target.value)}
                          placeholder="Web App Dashboard" 
                          required 
                        />
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        <Label htmlFor={`projectUrl${index}`}>Project URL</Label>
                        <Input 
                          id={`projectUrl${index}`}
                          value={project.url || ''}
                          onChange={(e) => updateProject(index, 'url', e.target.value)}
                          placeholder="https://github.com/yourusername/project" 
                        />
                        <p className="text-xs text-muted-foreground">Both templates support project URLs/links</p>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`projectStart${index}`}>Start Date</Label>
                          <Input 
                            id={`projectStart${index}`}
                            value={project.start_date || ''}
                            onChange={(e) => updateProject(index, 'start_date', e.target.value)}
                            type="month" 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`projectEnd${index}`}>End Date</Label>
                          <Input 
                            id={`projectEnd${index}`}
                            value={project.end_date || ''}
                            onChange={(e) => updateProject(index, 'end_date', e.target.value)}
                            type="month"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`projectDescription${index}`}>Project Description *</Label>
                        <Textarea 
                          id={`projectDescription${index}`}
                          value={project.description}
                          onChange={(e) => updateProject(index, 'description', e.target.value)}
                          placeholder="Describe the project, technologies used, and your contribution" 
                          className="min-h-[100px]"
                          required
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Button variant="outline" className="w-full" onClick={addProject}>
                  + Add Another Project
                </Button>
              </AccordionContent>
            </AccordionItem>

            {/* Skills - Enhanced with Categories */}
            <AccordionItem value="skills">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Skills</h2>
              </AccordionTrigger>
              <AccordionContent>
                <Card>
                  <CardHeader>
                    <CardTitle>Categorized Skills</CardTitle>
                    <CardDescription>
                      <div className="space-y-4">
                        <p>Both templates support categorized skills. Add different skill categories and list skills for each.</p>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-skills">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.skills}/10</span>
                          </div>
                          <input 
                            id="creativity-skills"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.skills}
                            onChange={(e) => updateCreativityLevel('skills', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </div>
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {skillCategories.map((category, index) => (
                      <div key={index} className="mb-6">
                        <div className="space-y-2 mb-3">
                          <Label htmlFor={`categoryName${index}`}>Category Name *</Label>
                          <Input 
                            id={`categoryName${index}`}
                            value={category.name}
                            onChange={(e) => updateSkillCategory(index, 'name', e.target.value)}
                            placeholder="Technical Skills, Soft Skills, etc." 
                            required 
                          />
                        </div>
                        
                        <div className="space-y-2 mb-2">
                          <Label htmlFor={`categorySkills${index}`}>Skills in this Category *</Label>
                          <Textarea 
                            id={`categorySkills${index}`}
                            value={category.skills.join(', ')}
                            onChange={(e) => updateSkillCategory(
                              index, 
                              'skills', 
                              e.target.value.split(',').map(s => s.trim())
                            )}
                            placeholder="List skills separated by commas: JavaScript, React, TypeScript" 
                            className="min-h-[80px]"
                            required
                          />
                        </div>
                        
                        <Separator className="my-4" />
                      </div>
                    ))}
                    
                    <Button variant="outline" className="w-full" onClick={addSkillCategory}>
                      + Add Another Skill Category
                    </Button>
                    
                    <Separator className="my-4" />
                    
                    {/* Maintain backward compatibility with single skill list */}
                    <div className="space-y-2 mt-6">
                      <Label htmlFor="technicalSkills">All Skills (Combined) *</Label>
                      <Textarea 
                        id="technicalSkills" 
                        placeholder="List all your skills (e.g., Programming languages, tools, software)"
                        className="min-h-[100px]"
                        required
                        value={skills.join(', ')}
                        onChange={(e) => setSkills(e.target.value.split(',').map(s => s.trim()))}
                      />
                      <p className="text-xs text-muted-foreground">
                        This is a combined list of all your skills. The categories above will be used for 
                        template display if available, otherwise this list will be used.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </AccordionContent>
            </AccordionItem>
            
            {/* Awards & Achievements Section */}
            <AccordionItem value="awards">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Awards & Achievements</h2>
              </AccordionTrigger>
              <AccordionContent>
                <div className="mb-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Awards & Achievements</CardTitle>
                      <CardDescription>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-awards">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.awards}/10</span>
                          </div>
                          <input 
                            id="creativity-awards"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.awards}
                            onChange={(e) => updateCreativityLevel('awards', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </div>
                {awards.map((award, index) => (
                  <Card className="mb-4" key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">Award {index + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 mb-4">
                        <Label htmlFor={`awardTitle${index}`}>Award Title *</Label>
                        <Input 
                          id={`awardTitle${index}`}
                          value={award.title}
                          onChange={(e) => updateAward(index, 'title', e.target.value)}
                          placeholder="Employee of the Year" 
                          required 
                        />
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`awardDate${index}`}>Date Received *</Label>
                          <Input 
                            id={`awardDate${index}`}
                            value={award.date}
                            onChange={(e) => updateAward(index, 'date', e.target.value)}
                            placeholder="2023" 
                            required 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`awardIssuer${index}`}>Issuing Organization *</Label>
                          <Input 
                            id={`awardIssuer${index}`}
                            value={award.issuer}
                            onChange={(e) => updateAward(index, 'issuer', e.target.value)}
                            placeholder="Company Name, University, etc." 
                            required 
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`awardDescription${index}`}>Description</Label>
                        <Textarea 
                          id={`awardDescription${index}`}
                          value={award.description}
                          onChange={(e) => updateAward(index, 'description', e.target.value)}
                          placeholder="Brief description of the award and why you received it" 
                          className="min-h-[80px]"
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Button variant="outline" className="w-full" onClick={addAward}>
                  + Add Another Award
                </Button>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  This section will be used in the Wenneker CV template
                </p>
              </AccordionContent>
            </AccordionItem>

            {/* Presentations / Communication Skills */}
            <AccordionItem value="presentations">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Presentations & Communication Skills</h2>
              </AccordionTrigger>
              <AccordionContent>
                <div className="mb-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Presentations & Communication Skills</CardTitle>
                      <CardDescription>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-presentations">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.presentations}/10</span>
                          </div>
                          <input 
                            id="creativity-presentations"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.presentations}
                            onChange={(e) => updateCreativityLevel('presentations', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </div>
                {presentations.map((presentation, index) => (
                  <Card className="mb-4" key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">Presentation {index + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 mb-4">
                        <Label htmlFor={`presentationTitle${index}`}>Presentation Title *</Label>
                        <Input 
                          id={`presentationTitle${index}`}
                          value={presentation.title}
                          onChange={(e) => updatePresentation(index, 'title', e.target.value)}
                          placeholder="The Future of AI in Business" 
                          required 
                        />
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label htmlFor={`presentationDate${index}`}>Date *</Label>
                          <Input 
                            id={`presentationDate${index}`}
                            value={presentation.date}
                            onChange={(e) => updatePresentation(index, 'date', e.target.value)}
                            placeholder="June 2023" 
                            required 
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`presentationVenue${index}`}>Venue / Event *</Label>
                          <Input 
                            id={`presentationVenue${index}`}
                            value={presentation.venue}
                            onChange={(e) => updatePresentation(index, 'venue', e.target.value)}
                            placeholder="Conference name, Company event, etc." 
                            required 
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`presentationDescription${index}`}>Description</Label>
                        <Textarea 
                          id={`presentationDescription${index}`}
                          value={presentation.description}
                          onChange={(e) => updatePresentation(index, 'description', e.target.value)}
                          placeholder="Brief description of your presentation and its impact" 
                          className="min-h-[80px]"
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <Button variant="outline" className="w-full" onClick={addPresentation}>
                  + Add Another Presentation
                </Button>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  This section will be used in the Wenneker CV template's "Communication Skills" section
                </p>
              </AccordionContent>
            </AccordionItem>

            {/* Interests Section */}
            <AccordionItem value="interests">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Interests & Hobbies</h2>
              </AccordionTrigger>
              <AccordionContent>
                <Card>
                  <CardHeader>
                    <CardTitle>Professional & Personal Interests</CardTitle>
                    <CardDescription>
                      <div className="space-y-4">
                        <p>The Wenneker CV template includes a section for your interests and hobbies.</p>
                        <div className="space-y-2">
                          <p>Adjust how creative the AI should be when generating CV for this section</p>
                          <div className="flex items-center gap-2">
                            <Label htmlFor="creativity-interests">Creativity Level:</Label>
                            <span className="text-muted-foreground ml-auto">{creativityLevels.interests}/10</span>
                          </div>
                          <input 
                            id="creativity-interests"
                            type="range" 
                            min="0" 
                            max="10" 
                            value={creativityLevels.interests}
                            onChange={(e) => updateCreativityLevel('interests', parseInt(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </div>
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {interests.map((interest, index) => (
                      <div key={index} className="mb-4">
                        <div className="space-y-2 mb-3">
                          <Label htmlFor={`interestType${index}`}>Interest Type *</Label>
                          <Select 
                            value={interest.type}
                            onValueChange={(value) => updateInterest(
                              index, 
                              'type', 
                              value as 'professional' | 'personal'
                            )}
                          >
                            <SelectTrigger id={`interestType${index}`}>
                              <SelectValue placeholder="Select interest type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="professional">Professional</SelectItem>
                              <SelectItem value="personal">Personal</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-2 mb-2">
                          <Label htmlFor={`interestDescription${index}`}>Description *</Label>
                          <Textarea 
                            id={`interestDescription${index}`}
                            value={interest.description}
                            onChange={(e) => updateInterest(index, 'description', e.target.value)}
                            placeholder={interest.type === 'professional' 
                              ? "Data analysis, web design, software architecture, etc."
                              : "Piano, chess, cooking, hiking, photography, etc."
                            }
                            className="min-h-[80px]"
                            required
                          />
                        </div>
                        
                        <Separator className="my-4" />
                      </div>
                    ))}
                    
                    <Button variant="outline" className="w-full" onClick={addInterest}>
                      + Add Another Interest Category
                    </Button>
                  </CardContent>
                </Card>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  This section will be used in the Wenneker CV template
                </p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Separator className="my-6" />

          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => window.location.href = '/templates'}>
              Go to Templates
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : 'Save Profile'}
            </Button>
          </div>
        </form>
      </div>
    </>
  );
};

export default Profile;