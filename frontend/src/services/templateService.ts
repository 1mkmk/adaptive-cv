import { fetchApi } from './api';

export interface Template {
  id: string;
  name: string;
  preview?: string; // Base64 encoded image
}

export async function getTemplates(): Promise<Template[]> {
  try {
    const response = await fetchApi('/generate/templates');
    return response.templates || [];
  } catch (error) {
    console.error('Error fetching templates:', error);
    return [];
  }
}

export interface CVGenerationParams {
  templateId?: string;
  model?: string;
  customContext?: string;
}

export async function generatePdfCV(jobId: number, params?: CVGenerationParams) {
  let url = `/generate/pdf/${jobId}`;
  
  const queryParams = [];
  
  if (params?.templateId) {
    queryParams.push(`template_id=${params.templateId}`);
  }
  
  if (params?.model) {
    queryParams.push(`model=${params.model}`);
  }
  
  if (params?.customContext) {
    queryParams.push(`custom_context=${encodeURIComponent(params.customContext)}`);
  }
  
  if (queryParams.length > 0) {
    url += `?${queryParams.join('&')}`;
  }
  
  try {
    const response = await fetchApi(url);
    return response;
  } catch (error) {
    console.error(`Error generating PDF CV for job ${jobId}:`, error);
    throw error;
  }
}

export async function downloadCV(
  jobId: number, 
  templateId?: string, 
  model?: string, 
  customContext?: string
) {
  let url = `/generate/download/${jobId}`;
  
  // Track if we're using advanced parameters or not
  let usingAdvancedParams = false;
  const queryParams = [];
  
  // Only add template ID if it's explicitly provided and not empty
  if (templateId && templateId.trim() !== '') {
    queryParams.push(`template_id=${templateId}`);
    usingAdvancedParams = true;
  }
  
  // Only add model if it's explicitly provided and not empty
  if (model && model.trim() !== '') {
    queryParams.push(`model=${model}`);
    usingAdvancedParams = true;
  }
  
  // Only add custom context if it's explicitly provided and not empty
  if (customContext && customContext.trim() !== '') {
    queryParams.push(`custom_context=${encodeURIComponent(customContext.trim())}`);
    usingAdvancedParams = true;
  }
  
  // Log whether we're using cached or generating new PDF
  console.log(usingAdvancedParams 
    ? "Generating new CV with custom parameters" 
    : "Using cached CV from server (if available)");
  
  if (queryParams.length > 0) {
    url += `?${queryParams.join('&')}`;
  }
  
  // For downloads, we need to handle this differently - generate a download link
  const downloadUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`;
  
  // Open in a new tab to trigger download
  window.open(downloadUrl, '_blank');
}

/**
 * Downloads the LaTeX source file for a CV
 */
export async function downloadLatexSource(
  jobId: number,
  templateId?: string
) {
  let url = `/generate/download/latex/${jobId}`;
  
  if (templateId && templateId.trim() !== '') {
    url += `?template_id=${templateId}`;
  }
  
  console.log("Downloading LaTeX source file");
  
  // Generate the download URL
  const downloadUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`;
  
  // Open in a new tab to trigger download
  window.open(downloadUrl, '_blank');
}

/**
 * Opens the LaTeX source in an online editor
 */
export async function editLatexOnline(
  jobId: number,
  templateId?: string,
  jobTitle?: string,
  companyName?: string
) {
  try {
    // First, get the LaTeX source
    let url = `/generate/download/latex/${jobId}`;
    
    if (templateId && templateId.trim() !== '') {
      url += `?template_id=${templateId}`;
    }
    
    console.log("Fetching LaTeX source for online editing");
    
    // Fetch the LaTeX content directly
    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch LaTeX source: ${response.status}`);
    }
    
    const latexContent = await response.text();
    
    // Generate a filename for the document
    const filename = jobTitle && companyName 
      ? `CV_${jobTitle.replace(/\s+/g, '_')}_${companyName.replace(/\s+/g, '_')}.tex`
      : `CV_${jobId}.tex`;
    
    // Open in Overleaf (which accepts LaTeX content via URL parameters)
    // Note: We need to encode the content for URL transmission
    const overleafUrl = `https://www.overleaf.com/docs?snip_uri=${encodeURIComponent(filename)}&snip_name=${encodeURIComponent(filename)}`;
    
    // Open Overleaf in a new tab
    const newTab = window.open(overleafUrl, '_blank');
    
    // If we can't open a new tab, inform the user
    if (!newTab) {
      alert('Please allow popups to open the LaTeX editor.');
    } else {
      // This is a workaround since we can't directly control the content via URL parameters
      // We'll need to ask the user to paste the content
      
      // Copy LaTeX to clipboard
      await navigator.clipboard.writeText(latexContent);
      
      // Alert the user with instructions
      alert('LaTeX source has been copied to your clipboard. Please paste it into the Overleaf editor that just opened.');
    }
    
    return true;
  } catch (error) {
    console.error('Error opening LaTeX in online editor:', error);
    alert('There was an error preparing the LaTeX source for editing. Please try downloading it instead.');
    return false;
  }
}

/**
 * Returns a list of recommended online LaTeX editors
 */
export function getLatexEditorOptions() {
  return [
    {
      id: 'overleaf',
      name: 'Overleaf',
      url: 'https://www.overleaf.com',
      description: 'Popular online LaTeX editor with real-time collaboration'
    },
    {
      id: 'verbosus',
      name: 'Verbosus',
      url: 'https://www.verbosus.com',
      description: 'Simple browser-based LaTeX editor'
    },
    {
      id: 'tex-studio',
      name: 'TeXstudio',
      url: 'https://www.texstudio.org',
      description: 'Desktop LaTeX editor (requires installation)'
    },
    {
      id: 'texmaker',
      name: 'Texmaker',
      url: 'https://www.xm1math.net/texmaker/',
      description: 'Cross-platform LaTeX editor (requires installation)'
    }
  ];
}