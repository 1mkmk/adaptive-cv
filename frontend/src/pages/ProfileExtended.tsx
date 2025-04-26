import React, { useState, useEffect, useRef } from 'react';
import Navbar from "@/components/ui/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { getProfile, saveProfile, importCVProfile, uploadProfilePhoto, CandidateProfile } from '@/services/profileService';

// Define additional types for new sections
interface Address {
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postalCode?: string;
  country: string;
}

interface Interest {
  type: 'professional' | 'personal';
  description: string;
}

interface Award {
  title: string;
  date: string;
  issuer: string;
  description: string;
}

interface Presentation {
  title: string;
  date: string;
  venue: string;
  description: string;
}

interface Project {
  name: string;
  description: string;
  url?: string;
  start_date?: string;
  end_date?: string;
}

interface SkillCategory {
  name: string;
  skills: string[];
}

// Extended profile type
interface ExtendedProfile extends CandidateProfile {
  job_title?: string;
  address?: Address;
  interests?: Interest[];
  awards?: Award[];
  presentations?: Presentation[];
  projects?: Project[];
  skill_categories?: SkillCategory[];
}

const ProfileExtended: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Basic form state (from existing Profile component)
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [summary, setSummary] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [location, setLocation] = useState('');
  const [linkedin, setLinkedin] = useState('');
  const [website, setWebsite] = useState('');
  
  // New extended fields
  const [jobTitle, setJobTitle] = useState('');
  const [address, setAddress] = useState<Address>({
    line1: '',
    line2: '',
    city: '',
    state: '',
    postalCode: '',
    country: ''
  });
  
  // Skill categories 
  const [skillCategories, setSkillCategories] = useState<SkillCategory[]>([
    { name: 'Programming Languages', skills: [] },
    { name: 'Frameworks & Libraries', skills: [] },
    { name: 'Tools & Technologies', skills: [] },
    { name: 'Soft Skills', skills: [] }
  ]);
  
  // Interests
  const [interests, setInterests] = useState<Interest[]>([
    { type: 'professional', description: 'Data analysis, web development, AI, cloud computing' },
    { type: 'personal', description: 'Reading, hiking, photography, playing piano' }
  ]);
  
  // Awards
  const [awards, setAwards] = useState<Award[]>([{
    title: '',
    date: '',
    issuer: '',
    description: ''
  }]);
  
  // Presentations/Communication Skills
  const [presentations, setPresentations] = useState<Presentation[]>([{
    title: '',
    date: '',
    venue: '',
    description: ''
  }]);
  
  // Projects with URLs
  const [projects, setProjects] = useState<Project[]>([{
    name: '',
    description: '',
    url: '',
    start_date: '',
    end_date: ''
  }]);

  // Experience and Education (from existing Profile)
  const [experiences, setExperiences] = useState([{
    company: '',
    position: '',
    start_date: '',
    end_date: '',
    current: false,
    description: ''
  }]);
  
  const [educations, setEducations] = useState([{
    institution: '',
    degree: '',
    field: '',
    start_date: '',
    end_date: '',
    current: false
  }]);

  // Load profile data on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profileData = await getProfile();
        if (profileData) {
          // Populate form with existing data
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
          
          // Set extended fields if they exist
          const extendedData = profileData as ExtendedProfile;
          if (extendedData.job_title) setJobTitle(extendedData.job_title);
          if (extendedData.address) setAddress(extendedData.address);
          if (extendedData.skill_categories) setSkillCategories(extendedData.skill_categories);
          if (extendedData.interests && extendedData.interests.length > 0) setInterests(extendedData.interests);
          if (extendedData.awards && extendedData.awards.length > 0) setAwards(extendedData.awards);
          if (extendedData.presentations && extendedData.presentations.length > 0) setPresentations(extendedData.presentations);
          if (extendedData.projects && extendedData.projects.length > 0) setProjects(extendedData.projects);
          
          // Set experience and education (from existing Profile)
          setExperiences(profileData.experience || [{ 
            company: '',
            position: '',
            start_date: '',
            end_date: '',
            current: false,
            description: ''
          }]);
          
          setEducations(profileData.education || [{
            institution: '',
            degree: '',
            field: '',
            start_date: '',
            end_date: '',
            current: false
          }]);
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
      }
    };
    
    loadProfile();
  }, []);

  // Handle photo change (from existing Profile)
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

  // Import CV (from existing Profile)
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
          
          // Extended fields would be imported if they exist in the future
          
          setSuccess("Successfully imported CV data! Please review and save your profile.");
        }
      } catch (err) {
        console.error("Error importing CV:", err);
        setError("Failed to import CV. Please try again or fill the form manually.");
      } finally {
        setImportLoading(false);
        
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    }
  };

  // Submit the form (extended to include new fields)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      // Create extended profile data object
      const profileData: ExtendedProfile = {
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
        job_title: jobTitle,
        address: address,
        interests: interests,
        awards: awards,
        presentations: presentations,
        projects: projects,
        skill_categories: skillCategories
      };
      
      // Use the existing saveProfile function - the backend would need to be updated to handle the new fields
      await saveProfile(profileData);
      setSuccess('Profile saved successfully!');
    } catch (err) {
      setError('Failed to save profile. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Helper functions for updating arrays 
  
  // Add/Update skill category
  const updateSkillCategory = (index: number, field: 'name' | 'skills', value: string | string[]) => {
    const updatedCategories = [...skillCategories];
    if (field === 'name') {
      updatedCategories[index].name = value as string;
    } else {
      updatedCategories[index].skills = value as string[];
    }
    setSkillCategories(updatedCategories);
  };
  
  // Add a new skill category
  const addSkillCategory = () => {
    setSkillCategories([...skillCategories, { name: '', skills: [] }]);
  };
  
  // Update address fields
  const updateAddress = (field: keyof Address, value: string) => {
    setAddress({
      ...address,
      [field]: value
    });
  };
  
  // Update interests
  const updateInterest = (index: number, field: keyof Interest, value: any) => {
    const updatedInterests = [...interests];
    updatedInterests[index] = {
      ...updatedInterests[index],
      [field]: value
    };
    setInterests(updatedInterests);
  };
  
  const addInterest = () => {
    setInterests([...interests, { type: 'personal', description: '' }]);
  };
  
  // Update awards
  const updateAward = (index: number, field: keyof Award, value: string) => {
    const updatedAwards = [...awards];
    updatedAwards[index] = {
      ...updatedAwards[index],
      [field]: value
    };
    setAwards(updatedAwards);
  };
  
  const addAward = () => {
    setAwards([...awards, { title: '', date: '', issuer: '', description: '' }]);
  };
  
  // Update presentations
  const updatePresentation = (index: number, field: keyof Presentation, value: string) => {
    const updatedPresentations = [...presentations];
    updatedPresentations[index] = {
      ...updatedPresentations[index],
      [field]: value
    };
    setPresentations(updatedPresentations);
  };
  
  const addPresentation = () => {
    setPresentations([...presentations, { title: '', date: '', venue: '', description: '' }]);
  };
  
  // Update projects
  const updateProject = (index: number, field: keyof Project, value: string) => {
    const updatedProjects = [...projects];
    updatedProjects[index] = {
      ...updatedProjects[index],
      [field]: value
    };
    setProjects(updatedProjects);
  };
  
  const addProject = () => {
    setProjects([...projects, { name: '', description: '', url: '', start_date: '', end_date: '' }]);
  };
  
  // Functions for experience and education from existing Profile
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

  const updateExperience = (index: number, field: string, value: string | boolean) => {
    const updatedExperiences = [...experiences];
    updatedExperiences[index] = {
      ...updatedExperiences[index],
      [field]: value
    };
    setExperiences(updatedExperiences);
  };

  const updateEducation = (index: number, field: string, value: string | boolean) => {
    const updatedEducations = [...educations];
    updatedEducations[index] = {
      ...updatedEducations[index],
      [field]: value
    };
    setEducations(updatedEducations);
  };

  return (
    <>
      <Navbar />
      <div className="container mx-auto py-10">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Your CV Profile</h1>
          <div>
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
              {importLoading ? 'Importing...' : 'Import from CV'}
            </Button>
          </div>
        </div>
        
        <p className="text-muted-foreground mb-8">
          Fill out the form below to create your comprehensive CV or import data from an existing CV.
          This profile includes additional fields to fully support both FAANG and Wenneker CV templates.
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
                          <p className="text-primary font-medium mt-2">Wenneker CV template displays this photo prominently</p>
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
                        required 
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

                    {/* New: Address fields */}
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
                      <p className="text-xs text-muted-foreground">Used in Wenneker CV as "About Me" and in FAANG template as part of the "Objective"</p>
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
                          placeholder="Describe your responsibilities and key achievements in this role. Use bullet points by starting lines with - " 
                          className="min-h-[120px]"
                          required
                        />
                        <p className="text-xs text-muted-foreground">
                          Tip: Use bullet points by starting lines with "-" for better formatting in both templates
                        </p>
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

            {/* Projects - Enhanced with URL */}
            <AccordionItem value="projects">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Projects</h2>
              </AccordionTrigger>
              <AccordionContent>
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
                      Both templates support categorized skills. Add different skill categories and list skills for each.
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

            {/* New: Awards Section */}
            <AccordionItem value="awards">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Awards & Achievements</h2>
              </AccordionTrigger>
              <AccordionContent>
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

            {/* New: Presentations / Communication Skills */}
            <AccordionItem value="presentations">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Presentations & Communication Skills</h2>
              </AccordionTrigger>
              <AccordionContent>
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

            {/* New: Interests Section */}
            <AccordionItem value="interests">
              <AccordionTrigger>
                <h2 className="text-xl font-semibold">Interests & Hobbies</h2>
              </AccordionTrigger>
              <AccordionContent>
                <Card>
                  <CardHeader>
                    <CardTitle>Professional & Personal Interests</CardTitle>
                    <CardDescription>
                      The Wenneker CV template includes a section for your interests and hobbies.
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

export default ProfileExtended;