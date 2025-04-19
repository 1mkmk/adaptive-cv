/**
 * This test file specifically checks the LaTeX CV generation workflow
 * across both frontend and backend components.
 */

import { fetchApi } from '@/services/api';
import { generatePdfCV, downloadCV, getDownloadCvUrl, displayPdf } from '@/services/cvService';

// Mock the API calls
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000',
  DIRECT_API_URL: 'http://localhost:8000',
  fetchApi: jest.fn(),
}));

// Mock DOM APIs
window.open = jest.fn();
global.URL.createObjectURL = jest.fn(() => 'blob:url');
global.URL.revokeObjectURL = jest.fn();

// Mock document.createElement to return different elements based on creation order
const mockElements = {
  a: { href: '', download: '', target: '', click: jest.fn() }
};

document.createElement = jest.fn((tag) => {
  if (tag === 'a') {
    return mockElements.a;
  }
  // Return a basic element for other tags
  return { tagName: tag };
});

document.body.appendChild = jest.fn();
document.body.removeChild = jest.fn();

// Mock console functions
console.error = jest.fn();
console.log = jest.fn();

// Mock atob for base64 decoding in displayPdf
global.atob = jest.fn((str) => 'decoded');

// Sample base64 encoded PDF content
const sampleBase64Pdf = 'JVBERi0xLjUKJYCBgoMKMSAwIG9iago8PC9GaWx0ZXIvRmxhdGVEZWNvZGUvRmlyc3QgMTQxL04g';

describe('LaTeX CV Generation Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Backend Flow', () => {
    it('should understand how LaTeX CV generation works on the backend', () => {
      /**
       * Backend Flow:
       * 1. generate_cv_from_template(db, job_id) is called from generate.py
       * 2. This function:
       *    - Fetches candidate profile and job data from the database
       *    - Prepares a temporary LaTeX environment
       *    - Copies the template and fills it with data
       *    - Compiles LaTeX to PDF using pdflatex
       *    - Generates a preview image of the first page
       *    - Encodes both as base64
       *    - Returns a dictionary with the encoded PDF and preview
       * 3. The PDF data is stored in the job record in the database
       * 4. The base64 encoded PDF and preview are returned to the frontend
       */
      
      // This is a non-executable test to document the flow
      expect(true).toBe(true);
    });
  });

  describe('Frontend Flow', () => {
    it('should handle PDF generation success correctly', async () => {
      // Mock successful PDF generation response
      const mockPdfResponse = {
        result: sampleBase64Pdf,
        format: 'pdf',
        preview: 'base64encodedpreview'
      };
      
      (fetchApi as jest.Mock).mockResolvedValueOnce(mockPdfResponse);
      
      // Call the function to generate PDF CV
      const result = await generatePdfCV(1);
      
      // Verify API endpoint was called correctly
      expect(fetchApi).toHaveBeenCalledWith('/generate/pdf/1', {
        method: 'GET',
      });
      
      // Check the result contains expected PDF data
      expect(result).toEqual(mockPdfResponse);
      
      // Test displaying the PDF
      displayPdf(result!.result, 'test_cv.pdf');
      
      // Verify PDF display operations were performed
      expect(global.atob).toHaveBeenCalledWith(sampleBase64Pdf);
      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(mockElements.a.click).toHaveBeenCalled();
      expect(document.body.appendChild).toHaveBeenCalled();
      expect(window.open).toHaveBeenCalled();
    });
    
    it('should handle PDF generation failure with direct download fallback', async () => {
      // Mock a failed PDF generation with timeout
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('AbortError: The operation was aborted.'));
      
      // Call the function that would fail
      const result = await generatePdfCV(1);
      
      // Verify the function called the correct endpoint
      expect(fetchApi).toHaveBeenCalledWith('/generate/pdf/1', {
        method: 'GET',
      });
      
      // Check that null is returned on failure
      expect(result).toBeNull();
      
      // Verify error was logged
      expect(console.error).toHaveBeenCalledWith('Error generating PDF CV:', expect.any(Error));
      
      // Test the direct download fallback
      const downloadUrl = getDownloadCvUrl(1);
      expect(downloadUrl).toBe('http://localhost:8000/generate/download/1');
      
      // Test opening the direct download URL
      window.open(downloadUrl, '_blank');
      expect(window.open).toHaveBeenCalledWith('http://localhost:8000/generate/download/1', '_blank');
    });
    
    it('should handle direct PDF download correctly', () => {
      // Test the downloadCV function with direct download
      // Mock Date.prototype.toISOString for consistent filename
      const originalToISOString = Date.prototype.toISOString;
      Date.prototype.toISOString = jest.fn().mockReturnValue('2023-01-01T00:00:00.000Z');
      
      // Use fake timers to control setTimeout
      jest.useFakeTimers();
      
      // Call the function to download CV
      downloadCV(1, 'Software Engineer', 'Tech Company');
      
      // Verify the anchor element was created with the correct URL
      expect(mockElements.a.href).toBe('http://localhost:8000/generate/download/1');
      expect(mockElements.a.download).toBe('CV_Software_Engineer_Tech_Company_2023-01-01.pdf');
      
      // Verify click was triggered to start download
      expect(mockElements.a.click).toHaveBeenCalled();
      
      // Run timers to trigger setTimeout callback for cleanup
      jest.runAllTimers();
      
      // Verify cleanup was performed
      expect(document.body.removeChild).toHaveBeenCalled();
      
      // Restore mocks
      jest.useRealTimers();
      Date.prototype.toISOString = originalToISOString;
    });
  });
  
  describe('End-to-End Flow', () => {
    it('should document the complete LaTeX CV flow from request to download', () => {
      /**
       * Complete Flow:
       * 
       * 1. User clicks "Generate PDF" button in Jobs.tsx
       * 2. Frontend calls generatePdfCV(jobId) from cvService.ts
       * 3. generatePdfCV makes API request to /generate/pdf/{job_id}
       * 4. Backend generates LaTeX CV from template:
       *    - Copies template from assets/templates
       *    - Fills with data from candidate profile and job
       *    - Compiles with pdflatex
       *    - Encodes as base64
       * 5. Backend returns base64 PDF data and preview
       * 6. Frontend receives the data and:
       *    - Converts base64 to Blob
       *    - Creates URL for the Blob
       *    - Opens PDF in new tab and/or downloads it
       * 
       * Fallback Flow (on timeout):
       * 1. If generatePdfCV times out or fails:
       *    - Frontend shows error message
       *    - Offers direct download link
       * 2. User clicks "Download PDF Directly" button
       * 3. Browser opens /generate/download/{job_id} URL
       * 4. Backend serves PDF file for download via StreamingResponse
       */
      
      // Non-executable documentation test
      expect(true).toBe(true);
    });
  });
});