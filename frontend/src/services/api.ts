// Function to get API URL that works in both Vite and Jest environments
function getApiUrl() {
  try {
    // For Vite environment
    if (typeof import.meta !== 'undefined' && import.meta.env) {
      return import.meta.env.VITE_API_URL || 'http://localhost:8000';
    }
  } catch (e) {
    // For Jest environment or if import.meta is not available
    return 'http://localhost:8000';
  }
  
  // Fallback
  return 'http://localhost:8000';
}

// Base API URL from environment variables with fallback
export const API_BASE_URL = getApiUrl();

// Direct URL to backend
export const DIRECT_API_URL = 'http://localhost:8000';

// Helper function for API calls
export async function fetchApi(endpoint: string, options = {}) {
  // Check if this is a PDF generation request (which might take longer)
  const isPdfRequest = endpoint.includes('/generate/pdf/');
  
  // Determine timeout based on request type
  const timeoutDuration = isPdfRequest ? 60000 : 60000; // 60 seconds for all requests - plenty of time to avoid timeouts
  
  // Use direct endpoint (without /api prefix)
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log(`Fetching from: ${url}${isPdfRequest ? ' (PDF request with extended timeout)' : ''}`);
  
  // Determine if we're dealing with FormData
  const isFormData = (options as any).body instanceof FormData;
  
  const fetchOptions = {
    ...options,
    headers: {
      // Don't set Content-Type for FormData as the browser will set it with boundary
      ...(!isFormData && { 'Content-Type': 'application/json' }),
      'Accept': 'application/json',
      ...(options as any).headers,
    },
    mode: 'cors' as RequestMode,
    credentials: 'include', // Include cookies
  };
  
  try {
    console.log(`Setting timeout to ${timeoutDuration}ms for request to ${url}`);
    
    // Add timeout to avoid waiting indefinitely
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log(`Request to ${url} timed out after ${timeoutDuration}ms`);
      controller.abort();
    }, timeoutDuration); 
    
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      credentials: fetchOptions.credentials as RequestCredentials
    });
    
    // Clear timeout
    clearTimeout(timeoutId);
    console.log(`Request to ${url} succeeded, cleared timeout`);
    
    if (!response.ok) {
      console.error(`API call failed: ${response.status}`, response);
      throw new Error(`API call failed: ${response.status}`);
    }
    
    return response.json();
  } catch (error: any) {
    console.error(`Error fetching ${url}:`, error);
    throw error;
  }
}