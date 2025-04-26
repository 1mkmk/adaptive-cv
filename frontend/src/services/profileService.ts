import { API_BASE_URL, fetchApi } from './api';

export interface Experience {
  company: string;
  position: string;
  start_date: string;
  end_date?: string;
  current: boolean;
  description: string;
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  start_date: string;
  end_date?: string;
  current: boolean;
}

export interface Language {
  name: string;
  level: string;
}

export interface Certification {
  name: string;
  issuer: string;
  date: string;
  url?: string;
}

export interface Project {
  name: string;
  description: string;
  url?: string;
  start_date?: string;
  end_date?: string;
}

export interface Reference {
  name: string;
  position: string;
  company: string;
  contact: string;
}

// Extended profile interfaces
export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postalCode?: string;
  country: string;
}

export interface Interest {
  type: 'professional' | 'personal';
  description: string;
}

export interface Award {
  title: string;
  date: string;
  issuer: string;
  description?: string;
}

export interface Presentation {
  title: string;
  date: string;
  venue: string;
  description?: string;
}

export interface SkillCategory {
  name: string;
  skills: string[];
}

export interface CandidateProfile {
  name: string;
  email: string;
  phone?: string;
  summary?: string;
  location?: string;
  linkedin?: string;
  website?: string;
  photo?: string;  // Base64 encoded image data
  skills: string[];
  experience: Experience[];
  education: Education[];
  languages?: Language[];
  certifications?: Certification[];
  projects?: Project[];
  references?: Reference[];
  // Extended fields
  job_title?: string;
  address?: Address;
  interests?: Interest[];
  awards?: Award[];
  presentations?: Presentation[];
  skill_categories?: SkillCategory[];
  creativity_levels?: {
    personal_info: number;
    summary: number;
    experience: number;
    education: number;
    skills: number;
    projects: number;
    awards: number;
    presentations: number;
    interests: number;
  };
}

export interface ProfileGenerationPrompt {
  prompt: string;
}

export async function getProfile() {
  try {
    return await fetchApi('/profile');
  } catch (error) {
    console.error('Error fetching profile:', error);
    return null;
  }
}

export async function saveProfile(profile: CandidateProfile) {
  try {
    console.log("Saving profile:", profile.name);
    
    // Sanitize the data before sending to API
    const sanitizedProfile = { ...profile };
    
    // Ensure creativity_levels is properly formatted
    if (sanitizedProfile.creativity_levels) {
      console.log("Creativity levels before sanitizing:", sanitizedProfile.creativity_levels);
      
      try {
        // Make sure the structure is an object with number values
        const cleanLevels: Record<string, number> = {};
        for (const [key, value] of Object.entries(sanitizedProfile.creativity_levels)) {
          // Convert any string values to numbers
          if (value === null || value === undefined) {
            // Use default value for missing fields
            cleanLevels[key] = 5; // Default creativity level
          } else if (typeof value === 'string') {
            const parsed = parseInt(value, 10);
            if (isNaN(parsed)) {
              console.warn(`Invalid creativity level for ${key}: ${value}, using default value`);
              cleanLevels[key] = 5;
            } else {
              cleanLevels[key] = parsed;
            }
          } else if (typeof value === 'number') {
            cleanLevels[key] = value;
          } else {
            console.warn(`Unexpected creativity level type for ${key}: ${typeof value}, using default value`);
            cleanLevels[key] = 5;
          }
        }
        
        // Ensure all required creativity fields exist
        const requiredFields = [
          'personal_info', 'summary', 'experience', 'education',
          'skills', 'projects', 'awards', 'presentations', 'interests'
        ];
        
        requiredFields.forEach(field => {
          if (!(field in cleanLevels)) {
            console.warn(`Missing creativity level for ${field}, adding default value`);
            cleanLevels[field] = 5;
          }
        });
        
        sanitizedProfile.creativity_levels = cleanLevels as any;
      } catch (error) {
        console.error("Error sanitizing creativity levels:", error);
        // Set default creativity levels if processing fails
        sanitizedProfile.creativity_levels = {
          personal_info: 5,
          summary: 5,
          experience: 5,
          education: 5,
          skills: 5,
          projects: 5,
          awards: 5,
          presentations: 5,
          interests: 5
        };
      }
      
      console.log("Sanitized creativity levels:", sanitizedProfile.creativity_levels);
    } else {
      // Provide default creativity levels if missing
      console.warn("Creativity levels missing, adding default values");
      sanitizedProfile.creativity_levels = {
        personal_info: 5,
        summary: 5,
        experience: 5,
        education: 5,
        skills: 5,
        projects: 5,
        awards: 5,
        presentations: 5,
        interests: 5
      };
    }
    
    // Ensure proper formatting for arrays
    ['skills', 'experience', 'education', 'languages', 'certifications', 
     'projects', 'references', 'interests', 'awards', 'presentations', 
     'skill_categories'].forEach(field => {
      if (sanitizedProfile[field as keyof CandidateProfile] === undefined || sanitizedProfile[field as keyof CandidateProfile] === null) {
        // If field is undefined or null, set it to an empty array for schema validation
        console.log(`Setting empty array for missing field: ${field}`);
        (sanitizedProfile as any)[field] = [];
      } else if (!Array.isArray(sanitizedProfile[field as keyof CandidateProfile])) {
        // If field is not an array, convert it to an array if possible
        console.warn(`Field ${field} is not an array, converting to array`);
        const value = (sanitizedProfile as any)[field];
        if (typeof value === 'string') {
          // Try to convert comma-separated string to array
          (sanitizedProfile as any)[field] = value.split(',').map(item => item.trim()).filter(item => item);
        } else {
          // If conversion is not possible, set to empty array
          (sanitizedProfile as any)[field] = [];
        }
      }
    });
    
    // Ensure address object is properly formatted if present
    if (sanitizedProfile.address) {
      try {
        const requiredAddressFields = ['line1', 'city', 'country'];
        requiredAddressFields.forEach(field => {
          if (!sanitizedProfile.address || sanitizedProfile.address[field as keyof typeof sanitizedProfile.address] === undefined) {
            if (!sanitizedProfile.address) sanitizedProfile.address = {} as any;
            console.warn(`Missing required address field: ${field}, setting to empty string`);
            (sanitizedProfile.address as any)[field] = '';
          }
        });
      } catch (error) {
        console.error("Error sanitizing address:", error);
        sanitizedProfile.address = {
          line1: '',
          city: '',
          country: ''
        };
      }
    }
    
    // Log the full profile for debugging
    console.log("Sending profile to API:", JSON.stringify(sanitizedProfile).substring(0, 200) + "...");
    
    const result = await fetchApi('/profile', {
      method: 'POST',
      body: JSON.stringify(sanitizedProfile)
    });
    
    console.log("Profile saved successfully");
    return result;
  } catch (error) {
    console.error("Error saving profile:", error);
    
    // Provide more detailed error information
    if (error instanceof Error) {
      console.error("Error details:", error.message);
      console.error("Stack trace:", error.stack);
      
      // Check for specific error types
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        console.error("Network error detected - API server may be unavailable");
        throw new Error("Unable to connect to the server. Please check your internet connection and try again.");
      } else if (error.message.includes('timeout') || error.message.includes('abort')) {
        console.error("Request timeout detected");
        throw new Error("Request timed out. Please try again later.");
      } else if (error.message.includes('400')) {
        console.error("Bad request error - likely data validation issue");
        throw new Error("Invalid profile data. Please check your inputs and try again.");
      } else if (error.message.includes('500')) {
        console.error("Server error detected");
        throw new Error("Server error occurred. Please try again later.");
      }
    }
    
    throw error;
  }
}

export async function updateProfile(updates: Partial<CandidateProfile>) {
  try {
    console.log("Updating profile with partial data");
    
    // Sanitize the data before sending to API
    const sanitizedUpdates = { ...updates };
    
    // Ensure creativity_levels is properly formatted
    if (sanitizedUpdates.creativity_levels) {
      console.log("Creativity levels before sanitizing:", sanitizedUpdates.creativity_levels);
      
      try {
        // Make sure the structure is an object with number values
        const cleanLevels: Record<string, number> = {};
        for (const [key, value] of Object.entries(sanitizedUpdates.creativity_levels)) {
          // Convert any string values to numbers
          if (value === null || value === undefined) {
            // Use default value for missing fields
            cleanLevels[key] = 5; // Default creativity level
          } else if (typeof value === 'string') {
            const parsed = parseInt(value, 10);
            if (isNaN(parsed)) {
              console.warn(`Invalid creativity level for ${key}: ${value}, using default value`);
              cleanLevels[key] = 5;
            } else {
              cleanLevels[key] = parsed;
            }
          } else if (typeof value === 'number') {
            cleanLevels[key] = value;
          } else {
            console.warn(`Unexpected creativity level type for ${key}: ${typeof value}, using default value`);
            cleanLevels[key] = 5;
          }
        }
        
        sanitizedUpdates.creativity_levels = cleanLevels as any;
      } catch (error) {
        console.error("Error sanitizing creativity levels:", error);
        // Skip setting creativity levels if processing fails in update
        delete sanitizedUpdates.creativity_levels;
      }
      
      console.log("Sanitized creativity levels:", sanitizedUpdates.creativity_levels);
    }
    
    // Ensure array fields are properly formatted
    if (sanitizedUpdates) {
      // Check all array fields that might be in the update
      ['skills', 'experience', 'education', 'languages', 'certifications', 
       'projects', 'references', 'interests', 'awards', 'presentations', 
       'skill_categories'].forEach(field => {
        if (field in sanitizedUpdates) {
          const fieldValue = sanitizedUpdates[field as keyof typeof sanitizedUpdates];
          
          if (fieldValue === undefined || fieldValue === null) {
            // If field is explicitly set to undefined or null, set it to an empty array
            console.log(`Setting empty array for null/undefined field in update: ${field}`);
            (sanitizedUpdates as any)[field] = [];
          } else if (!Array.isArray(fieldValue)) {
            // If field is not an array, convert it to an array if possible
            console.warn(`Field ${field} in update is not an array, converting to array`);
            if (typeof fieldValue === 'string') {
              // Try to convert comma-separated string to array
              (sanitizedUpdates as any)[field] = fieldValue.split(',').map(item => item.trim()).filter(item => item);
            } else {
              // If conversion is not possible, set to empty array
              (sanitizedUpdates as any)[field] = [];
            }
          }
        }
      });
    }
    
    // Ensure address object is properly formatted if present in update
    if (sanitizedUpdates.address) {
      try {
        const requiredAddressFields = ['line1', 'city', 'country'];
        let hasIssues = false;
        
        requiredAddressFields.forEach(field => {
          if (!sanitizedUpdates.address || sanitizedUpdates.address[field as keyof typeof sanitizedUpdates.address] === undefined) {
            hasIssues = true;
          }
        });
        
        if (hasIssues) {
          console.warn("Address in update has missing required fields; getting full profile to merge properly");
          // Fetch current profile to properly merge address
          const currentProfile = await fetchApi('/profile');
          if (currentProfile && currentProfile.address) {
            sanitizedUpdates.address = {
              ...currentProfile.address,
              ...sanitizedUpdates.address
            };
            
            // Ensure required fields are present after merge
            requiredAddressFields.forEach(field => {
              if (!sanitizedUpdates.address || sanitizedUpdates.address[field as keyof typeof sanitizedUpdates.address] === undefined) {
                if (!sanitizedUpdates.address) sanitizedUpdates.address = {} as any;
                console.warn(`Missing required address field after merge: ${field}, setting to empty string`);
                (sanitizedUpdates.address as any)[field] = '';
              }
            });
          }
        }
      } catch (error) {
        console.error("Error sanitizing address in update:", error);
        // Don't modify address if an error occurs during update operation
      }
    }
    
    // Log the update data for debugging
    console.log("Sending profile updates to API:", JSON.stringify(sanitizedUpdates).substring(0, 200) + "...");
    
    const result = await fetchApi('/profile', {
      method: 'PUT',
      body: JSON.stringify(sanitizedUpdates)
    });
    
    console.log("Profile updated successfully");
    return result;
  } catch (error) {
    console.error("Error updating profile:", error);
    
    // Provide more detailed error information
    if (error instanceof Error) {
      console.error("Error details:", error.message);
      console.error("Stack trace:", error.stack);
      
      // Check for specific error types
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        console.error("Network error detected - API server may be unavailable");
        throw new Error("Unable to connect to the server. Please check your internet connection and try again.");
      } else if (error.message.includes('timeout') || error.message.includes('abort')) {
        console.error("Request timeout detected");
        throw new Error("Request timed out. Please try again later.");
      } else if (error.message.includes('400')) {
        console.error("Bad request error - likely data validation issue");
        throw new Error("Invalid profile data. Please check your inputs and try again.");
      } else if (error.message.includes('500')) {
        console.error("Server error detected");
        throw new Error("Server error occurred. Please try again later.");
      }
    }
    
    throw error;
  }
}

export async function importCVProfile(cvFile: File) {
  // Validate file before upload
  if (!cvFile) {
    throw new Error("No file provided for import");
  }
  
  // Check file size (max 10MB)
  const maxSizeInBytes = 10 * 1024 * 1024; // 10MB
  if (cvFile.size > maxSizeInBytes) {
    throw new Error(`File size exceeds the maximum allowed size (10MB). Your file is ${(cvFile.size / (1024 * 1024)).toFixed(2)}MB.`);
  }
  
  // Check file type
  const allowedTypes = [
    'application/pdf', 
    'text/plain',
    'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/rtf'
  ];
  
  const fileType = cvFile.type;
  if (!allowedTypes.includes(fileType) && !cvFile.name.endsWith('.pdf') && !cvFile.name.endsWith('.txt') && 
      !cvFile.name.endsWith('.doc') && !cvFile.name.endsWith('.docx') && !cvFile.name.endsWith('.rtf')) {
    throw new Error(`Invalid file type: ${fileType || 'unknown'}. Please upload a PDF, TXT, DOC, DOCX, or RTF file.`);
  }
  
  // Create a FormData instance
  const formData = new FormData();
  formData.append('cv_file', cvFile);
  
  console.log(`Importing CV from file: ${cvFile.name} (${(cvFile.size / 1024).toFixed(2)} KB, type: ${cvFile.type})`);
  
  try {
    // Set up request timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 60000); // 60 second timeout for CV import which might involve AI processing
    
    // Use fetch directly since we need to handle FormData
    const response = await fetch(`${API_BASE_URL}/profile/import-cv`, {
      method: 'POST',
      body: formData,
      // Let the browser set the content-type with boundary for multipart/form-data
      headers: {
        // Don't set Content-Type here, browser will set it with boundary parameter
        'Accept': 'application/json'
      },
      mode: 'cors',
      signal: controller.signal
    });
    
    // Clear timeout
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      // Try to get error details from the response
      try {
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Unknown error';
        
        console.error(`CV import API error (${response.status}):`, errorData);
        
        // Handle specific error cases with more user-friendly messages
        if (errorMessage.includes('PDF parsing failed') || errorMessage.includes('Text extraction failed')) {
          throw new Error(`The PDF could not be parsed. It may be scanned, protected, or in an unsupported format. Please try a different file.`);
        } else if (errorMessage.includes('Empty document')) {
          throw new Error(`The uploaded file appears to be empty. Please try a different file.`);
        } else if (errorMessage.includes('Invalid file format')) {
          throw new Error(`The file format is not supported. Please upload a PDF, TXT, DOC, DOCX, or RTF file.`);
        }
        
        throw new Error(`CV import failed: ${response.status} - ${errorMessage}`);
      } catch (jsonError) {
        // If we can't parse the JSON, just use the status
        if (response.status === 413) {
          throw new Error(`File is too large. Maximum file size is 10MB.`);
        } else if (response.status === 415) {
          throw new Error(`Unsupported file type. Please upload a PDF, TXT, DOC, DOCX, or RTF file.`);
        } else if (response.status === 400) {
          throw new Error(`Bad request. Please check the file format and try again.`);
        } else if (response.status === 500) {
          throw new Error(`Server error processing your file. Please try again later.`);
        } else {
          throw new Error(`CV import failed: ${response.status}`);
        }
      }
    }
    
    const result = await response.json();
    console.log("CV import successful, data extracted");
    return result;
  } catch (error) {
    // Handle request timeouts and network errors
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('CV import request timed out after 60 seconds');
      throw new Error('CV import timed out. The file may be too large or complex to process.');
    } else if (error instanceof Error && (error.message === 'Network Error' || error.message.includes('Failed to fetch'))) {
      console.error('Network error during CV import:', error);
      throw new Error('Network error during CV import. Please check your connection and try again.');
    }
    
    console.error('Error importing CV profile:', error);
    throw error;
  }
}

export async function uploadProfilePhoto(photoFile: File) {
  // Validate file before upload
  if (!photoFile) {
    throw new Error("No photo file provided for upload");
  }
  
  // Check file size (max 5MB)
  const maxSizeInBytes = 5 * 1024 * 1024; // 5MB
  if (photoFile.size > maxSizeInBytes) {
    throw new Error(`Photo file size exceeds the maximum allowed size (5MB). Your file is ${(photoFile.size / (1024 * 1024)).toFixed(2)}MB.`);
  }
  
  // Check file type
  const allowedTypes = [
    'image/jpeg', 
    'image/png',
    'image/gif', 
    'image/webp',
    'image/svg+xml'
  ];
  
  const fileType = photoFile.type;
  if (!allowedTypes.includes(fileType) && !photoFile.name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
    throw new Error(`Invalid image file type: ${fileType || 'unknown'}. Please upload a JPG, PNG, GIF, WEBP, or SVG file.`);
  }
  
  // Create a FormData instance
  const formData = new FormData();
  formData.append('photo_file', photoFile);
  
  console.log(`Uploading profile photo: ${photoFile.name} (${(photoFile.size / 1024).toFixed(2)} KB, type: ${photoFile.type})`);
  
  try {
    // Set up request timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 30000); // 30 second timeout for photo upload
    
    // Use fetch directly since we need to handle FormData
    const response = await fetch(`${API_BASE_URL}/profile/upload-photo`, {
      method: 'POST',
      body: formData,
      // Let the browser set the content-type with boundary for multipart/form-data
      headers: {
        // Don't set Content-Type here, browser will set it with boundary parameter
        'Accept': 'application/json'
      },
      mode: 'cors',
      signal: controller.signal
    });
    
    // Clear timeout
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      // Try to get error details from the response
      try {
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Unknown error';
        
        console.error(`Photo upload API error (${response.status}):`, errorData);
        
        // Handle specific error cases with more user-friendly messages
        if (errorMessage.includes('Invalid image')) {
          throw new Error(`The file is not a valid image. Please upload a different photo.`);
        } else if (errorMessage.includes('File too large')) {
          throw new Error(`The photo file is too large. Maximum size is 5MB.`);
        } else if (errorMessage.includes('Unsupported file type')) {
          throw new Error(`Unsupported image format. Please upload a JPG, PNG, GIF, WEBP, or SVG file.`);
        }
        
        throw new Error(`Photo upload failed: ${response.status} - ${errorMessage}`);
      } catch (jsonError) {
        // If we can't parse the JSON, just use the status
        if (response.status === 413) {
          throw new Error(`Photo file is too large. Maximum size is 5MB.`);
        } else if (response.status === 415) {
          throw new Error(`Unsupported image format. Please upload a JPG, PNG, GIF, WEBP, or SVG file.`);
        } else if (response.status === 400) {
          throw new Error(`Invalid photo file. Please try a different image.`);
        } else if (response.status === 500) {
          throw new Error(`Server error processing your photo. Please try again later.`);
        } else {
          throw new Error(`Photo upload failed: ${response.status}`);
        }
      }
    }
    
    const result = await response.json();
    console.log("Photo upload successful");
    return result;
  } catch (error) {
    // Handle request timeouts and network errors
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('Photo upload request timed out after 30 seconds');
      throw new Error('Photo upload timed out. The file may be too large or your connection is slow.');
    } else if (error instanceof Error && (error.message === 'Network Error' || error.message.includes('Failed to fetch'))) {
      console.error('Network error during photo upload:', error);
      throw new Error('Network error during photo upload. Please check your connection and try again.');
    }
    
    console.error('Error uploading profile photo:', error);
    throw error;
  }
}

export async function generateProfileFromPrompt(data: ProfileGenerationPrompt) {
  try {
    // Validate input
    if (!data.prompt || !data.prompt.trim()) {
      throw new Error('Empty prompt. Please provide a description of the profile you want to generate.');
    }
    
    // Trim the prompt and ensure it's not too long
    const sanitizedData = {
      prompt: data.prompt.trim().substring(0, 5000) // Limit to 5000 chars
    };
    
    console.log(`Generating profile from prompt (${sanitizedData.prompt.length} chars)`);
    
    // Make the API call with a longer timeout since this involves AI generation
    const response = await fetchApi('/profile/generate-from-prompt', {
      method: 'POST',
      body: JSON.stringify(sanitizedData)
    });
    
    // Validate response data
    if (!response || !response.name || !response.email) {
      console.warn('Generated profile missing required fields:', response);
      throw new Error('The generated profile is incomplete. Please try a more detailed prompt.');
    }
    
    // Format arrays to ensure they're always arrays
    ['skills', 'experience', 'education', 'languages', 'certifications', 
     'projects', 'references', 'interests', 'awards', 'presentations', 
     'skill_categories'].forEach(field => {
      if (response[field] === undefined || response[field] === null) {
        // If field is undefined or null, set it to an empty array
        response[field] = [];
      } else if (!Array.isArray(response[field])) {
        // If field is not an array, convert it to an array if possible
        console.warn(`Field ${field} in generated profile is not an array, converting to array`);
        const value = response[field];
        if (typeof value === 'string') {
          // Try to convert comma-separated string to array
          response[field] = value.split(',').map((item: string) => item.trim()).filter((item: string) => item);
        } else {
          // If conversion is not possible, set to empty array
          response[field] = [];
        }
      }
    });
    
    console.log('Profile generated successfully from prompt');
    return response;
  } catch (error) {
    console.error('Error generating profile from prompt:', error);
    
    // Provide more specific error messages based on error type
    if (error instanceof Error) {
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        throw new Error('Unable to connect to the AI service. Please check your connection and try again.');
      } else if (error.message.includes('timeout') || error.message.includes('abort')) {
        throw new Error('Profile generation timed out. The AI service may be busy. Please try again later.');
      } else if (error.message.includes('500')) {
        throw new Error('The AI service encountered an error. Please try a different prompt or try again later.');
      } else if (error.message.includes('429')) {
        throw new Error('Too many requests to the AI service. Please wait a moment and try again.');
      }
    }
    
    throw error;
  }
}