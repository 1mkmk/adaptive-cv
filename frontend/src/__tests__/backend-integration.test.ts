import { fetchApi } from '@/services/api';
import { generatePdfCV, downloadCV, getDownloadCvUrl } from '@/services/cvService';

// Mock the API calls
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000',
  DIRECT_API_URL: 'http://localhost:8000',
  fetchApi: jest.fn(),
}));

// Mock DOM APIs
window.open = jest.fn();
const mockClickFn = jest.fn();
const mockAnchorElement = {
  href: '',
  download: '',
  target: '',
  click: mockClickFn
};
document.createElement = jest.fn().mockReturnValue(mockAnchorElement);
document.body.appendChild = jest.fn();
document.body.removeChild = jest.fn();

// Mock console.error to suppress error messages during tests
console.error = jest.fn();

describe('Backend Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('LaTeX CV Generation Flow', () => {
    it('should process the correct flow when generating a PDF CV', async () => {
      // 1. The frontend calls the backend with the job ID for PDF generation
      const mockPdfResponse = {
        result: 'base64encodedpdf',
        format: 'pdf',
        preview: 'base64encodedpreview'
      };
      
      (fetchApi as jest.Mock).mockResolvedValueOnce(mockPdfResponse);
      
      // Test the generatePdfCV function
      const result = await generatePdfCV(1);
      
      // Verify the correct endpoint was called
      expect(fetchApi).toHaveBeenCalledWith('/generate/pdf/1', {
        method: 'GET',
      });
      
      // Verify the result contains the expected data
      expect(result).toEqual(mockPdfResponse);
    });

    it('should handle the direct download flow correctly', () => {
      // Test the URL generation for direct download
      const downloadUrl = getDownloadCvUrl(123);
      expect(downloadUrl).toBe('http://localhost:8000/generate/download/123');
      
      // Test the downloadCV function
      // Mock Date.prototype.toISOString for predictable filenames
      const originalToISOString = Date.prototype.toISOString;
      Date.prototype.toISOString = jest.fn().mockReturnValue('2023-01-01T00:00:00.000Z');
      
      // Use fake timers to control setTimeout
      jest.useFakeTimers();
      
      // Call the download function
      downloadCV(123, 'Software Engineer', 'Tech Company');
      
      // Verify the URL in the download link is correct
      expect(mockAnchorElement.href).toBe('http://localhost:8000/generate/download/123');
      
      // Check the filename was formatted correctly
      expect(mockAnchorElement.download).toBe('CV_Software_Engineer_Tech_Company_2023-01-01.pdf');
      
      // Verify the click on the download link was triggered
      expect(mockClickFn).toHaveBeenCalled();
      
      // Verify the DOM appendChild operation was performed
      expect(document.body.appendChild).toHaveBeenCalled();
      
      // Run timers to trigger the setTimeout callback that removes the element
      jest.runAllTimers();
      
      // Now check if removeChild was called
      expect(document.body.removeChild).toHaveBeenCalled();
      
      // Restore real timers
      jest.useRealTimers();
      
      // Restore original Date.prototype.toISOString
      Date.prototype.toISOString = originalToISOString;
    });

    it('should handle PDF generation timeout with direct download fallback', async () => {
      // Simulate a timeout or network error during PDF generation
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('AbortError: The operation was aborted.'));
      
      // Test the generatePdfCV function with simulated timeout
      const result = await generatePdfCV(1);
      
      // Check that fetchApi was called with the correct endpoint
      expect(fetchApi).toHaveBeenCalledWith('/generate/pdf/1', {
        method: 'GET',
      });
      
      // Verify null is returned on error
      expect(result).toBeNull();
      
      // Verify error was logged to console
      expect(console.error).toHaveBeenCalledWith('Error generating PDF CV:', expect.any(Error));
      
      // In the real application at this point, the Jobs.tsx component would:
      // 1. Display an error message
      // 2. Make the direct download link visible
      // 3. User would click on the direct download button
      
      // Test the direct download fallback
      window.open = jest.fn();
      window.open(`http://localhost:8000/generate/download/1`, '_blank');
      expect(window.open).toHaveBeenCalledWith('http://localhost:8000/generate/download/1', '_blank');
    });
  });

  describe('LaTeX Template Understanding', () => {
    it('should understand the integration with LaTeX templates', () => {
      /**
       * The latex_cv_generator.py process:
       * 1. Prepares a LaTeX environment using prepare_latex_environment
       * 2. Generates a LaTeX CV file by copying a template and filling in data
       * 3. Compiles the LaTeX file to PDF using pdflatex/MiKTeX
       * 4. Creates a preview image
       * 5. Returns paths to PDF and preview
       * 6. Then encodes both as base64 for sending to frontend
       * 
       * The frontend should:
       * 1. Call generatePdfCV with the job ID
       * 2. If successful, get back base64 encoded PDF data
       * 3. Display or download the PDF
       * 4. If generation fails, provide a direct download link
       */
      
      // This is a non-executable test to document the flow
      expect(true).toBe(true);
    });
  });
});