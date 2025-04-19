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

// Direct URL to backend if proxy doesn't work
export const DIRECT_API_URL = 'http://localhost:8000';

// Helper function for API calls
export async function fetchApi(endpoint: string, options = {}) {
  // Check if this is a PDF generation request (which might take longer)
  const isPdfRequest = endpoint.includes('/generate/pdf/');
  
  // Determine timeout based on request type
  const timeoutDuration = isPdfRequest ? 60000 : 60000; // 60 seconds for all requests - plenty of time to avoid timeouts
  
  // Najpierw spróbuj użyć proxy URL
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log(`Fetching from: ${url}${isPdfRequest ? ' (PDF request with extended timeout)' : ''}`);
  
  const fetchOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(options as any).headers,
    },
    mode: 'cors' as RequestMode,
  };
  
  try {
    console.log(`Setting timeout to ${timeoutDuration}ms for request to ${url}`);
    
    // Dodaj timeout, aby nie czekać w nieskończoność
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log(`Request to ${url} timed out after ${timeoutDuration}ms`);
      controller.abort();
    }, timeoutDuration); 
    
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal
    });
    
    // Wyczyść timeout
    clearTimeout(timeoutId);
    console.log(`Request to ${url} succeeded, cleared timeout`);
    
    if (!response.ok) {
      console.error(`API call failed: ${response.status}`, response);
      throw new Error(`API call failed: ${response.status}`);
    }
    
    return response.json();
  } catch (error: any) {
    console.error(`Error fetching ${url}:`, error);
    
    // Jeśli to timeout lub CORS, spróbuj bezpośrednio
    if (error.name === 'AbortError' || error.message.includes('CORS') || error.message.includes('timeout') || error.message.includes('NetworkError')) {
      console.log(`Retrying with direct API connection to ${DIRECT_API_URL}${endpoint}`);
      
      try {
        // For direct connection on timeout, also use extended timeout for PDF requests
        const directController = new AbortController();
        console.log(`Setting direct timeout to ${timeoutDuration}ms for request to ${DIRECT_API_URL}${endpoint}`);
        
        const directTimeoutId = setTimeout(() => {
          console.log(`Direct request to ${DIRECT_API_URL}${endpoint} timed out after ${timeoutDuration}ms`);
          directController.abort();
        }, timeoutDuration);
        
        const directResponse = await fetch(`${DIRECT_API_URL}${endpoint}`, {
          ...fetchOptions,
          signal: directController.signal
        });
        
        // Clear timeout
        clearTimeout(directTimeoutId);
        console.log(`Direct request to ${DIRECT_API_URL}${endpoint} succeeded, cleared timeout`);
        
        if (!directResponse.ok) {
          console.error(`Direct API call failed: ${directResponse.status}`, directResponse);
          throw new Error(`Direct API call failed: ${directResponse.status}`);
        }
        
        return directResponse.json();
      } catch (directError) {
        console.error(`Error in direct API call to ${DIRECT_API_URL}${endpoint}:`, directError);
        throw directError;
      }
    }
    
    throw error;
  }
}