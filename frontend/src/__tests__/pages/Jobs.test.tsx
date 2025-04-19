import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Jobs from '@/pages/Jobs';
import { fetchApi } from '@/services/api';
import { generateCV, generatePdfCV, displayPdf } from '@/services/cvService';

// Mock window.open
window.open = jest.fn();

// Mock the react-router hooks
jest.mock('react-router', () => ({
  useNavigate: () => jest.fn(),
}));

// Mock the API services
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000',
  DIRECT_API_URL: 'http://localhost:8000',
  fetchApi: jest.fn(),
}));

jest.mock('@/services/cvService', () => ({
  generateCV: jest.fn(),
  generatePdfCV: jest.fn(),
  displayPdf: jest.fn(),
  downloadCV: jest.fn(),
  openCVInBrowser: jest.fn(),
  getDownloadCvUrl: jest.fn(() => 'http://localhost:8000/generate/download/1'),
  getPreviewCvUrl: jest.fn(() => 'http://localhost:8000/generate/preview/1'),
}));

// Mock Navbar
jest.mock('@/components/ui/Navbar', () => {
  return function MockNavbar() {
    return <div data-testid="navbar">Mock Navbar</div>;
  };
});

describe('Jobs Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock fetchApi to return an empty array for jobs
    (fetchApi as jest.Mock).mockResolvedValue([]);
  });
  
  it('renders the Jobs page with empty state', async () => {
    render(<Jobs />);
    
    // Check that the navbar and main title are displayed
    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByText('Job Applications')).toBeInTheDocument();
    
    // Check that empty state message is displayed
    await waitFor(() => {
      expect(screen.getByText('No job applications yet. Add your first job above.')).toBeInTheDocument();
    });
  });
  
  it('renders jobs when they are returned from the API', async () => {
    const mockJobs = [
      {
        id: '1',
        title: 'Frontend Developer',
        company: 'Tech Co',
        location: 'Remote',
        description: 'Frontend development with React',
        created_at: '2023-01-01',
      },
      {
        id: '2',
        title: 'Backend Developer',
        company: 'Enterprise Inc',
        location: 'New York',
        description: 'Backend development with FastAPI',
        created_at: '2023-01-02',
      }
    ];
    
    (fetchApi as jest.Mock).mockResolvedValue(mockJobs);
    
    render(<Jobs />);
    
    // Check that job titles are displayed
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
      expect(screen.getByText('Backend Developer')).toBeInTheDocument();
    });
  });
  
  it('allows adding a job from URL', async () => {
    (fetchApi as jest.Mock)
      .mockResolvedValueOnce([]) // Initial jobs fetch
      .mockResolvedValueOnce({ id: '3', title: 'New Job' }) // Job creation response
      .mockResolvedValueOnce([{ id: '3', title: 'New Job' }]); // Updated jobs fetch
    
    render(<Jobs />);
    
    // Switch to URL import tab if needed
    const urlTab = screen.getByText('Import from URL');
    fireEvent.click(urlTab);
    
    // Fill in the job URL
    const urlInput = screen.getByLabelText('Job Posting URL');
    fireEvent.change(urlInput, { target: { value: 'https://example.com/job' } });
    
    // Submit the form
    const importButton = screen.getByText('Import Job');
    fireEvent.click(importButton);
    
    // Verify the job was added
    await waitFor(() => {
      expect(fetchApi).toHaveBeenCalledWith(expect.stringContaining('/jobs/create'), expect.any(Object));
    });
  });
  
  it('generates a CV when requested', async () => {
    const mockJobs = [
      {
        id: '1',
        title: 'Frontend Developer',
        company: 'Tech Co',
        location: 'Remote',
        description: 'Frontend development with React',
        created_at: '2023-01-01',
      }
    ];
    
    (fetchApi as jest.Mock).mockResolvedValue(mockJobs);
    (generateCV as jest.Mock).mockResolvedValue({
      result: '# Test CV\n\nThis is a test CV',
      format: 'markdown'
    });
    
    render(<Jobs />);
    
    // Wait for jobs to load
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    });
    
    // Click on the job to select it
    fireEvent.click(screen.getByText('Frontend Developer'));
    
    // Click the Generate CV button
    const generateButton = screen.getAllByText('Generate CV')[0];
    fireEvent.click(generateButton);
    
    // Check that generateCV was called with the right parameters
    await waitFor(() => {
      expect(generateCV).toHaveBeenCalledWith({
        prompt: 'Frontend development with React',
        job_id: 1,
        format: 'markdown'
      });
    });
  });
  
  it('handles PDF generation', async () => {
    const mockJobs = [
      {
        id: '1',
        title: 'Frontend Developer',
        company: 'Tech Co',
        location: 'Remote',
        description: 'Frontend development with React',
        created_at: '2023-01-01',
        cv: '# Test CV',
        cv_format: 'markdown'
      }
    ];
    
    (fetchApi as jest.Mock).mockResolvedValue(mockJobs);
    (generatePdfCV as jest.Mock).mockResolvedValue({
      result: 'base64encodedpdf',
      format: 'pdf'
    });
    
    render(<Jobs />);
    
    // Wait for jobs to load
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    });
    
    // Click on the job to select it
    fireEvent.click(screen.getByText('Frontend Developer'));
    
    // Check that the job is selected and CV is displayed
    await waitFor(() => {
      expect(screen.getByText('CV for Frontend Developer')).toBeInTheDocument();
    });
    
    // Generate PDF
    const generatePdfButton = screen.getByText('Generate PDF');
    fireEvent.click(generatePdfButton);
    
    // Check that generatePdfCV was called with the right parameters
    await waitFor(() => {
      expect(generatePdfCV).toHaveBeenCalledWith(1);
    });
  });

  it('handles PDF generation timeout with fallback', async () => {
    const mockJobs = [
      {
        id: '1',
        title: 'Frontend Developer',
        company: 'Tech Co',
        location: 'Remote',
        description: 'Frontend development with React',
        created_at: '2023-01-01',
        cv: '# Test CV',
        cv_format: 'markdown'
      }
    ];
    
    (fetchApi as jest.Mock).mockResolvedValue(mockJobs);
    // Simulate a timeout by returning null
    (generatePdfCV as jest.Mock).mockResolvedValue(null);
    
    render(<Jobs />);
    
    // Wait for jobs to load
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    });
    
    // Click on the job to select it
    fireEvent.click(screen.getByText('Frontend Developer'));
    
    // Generate PDF
    const generatePdfButton = screen.getByText('Generate PDF');
    fireEvent.click(generatePdfButton);
    
    // Check that an error message is displayed and direct download button is shown
    await waitFor(() => {
      expect(screen.getByText('PDF generation via API timed out. Click the "Download PDF" button below to get your PDF directly.')).toBeInTheDocument();
      expect(screen.getByText('Download PDF Directly')).toBeInTheDocument();
    });
    
    // Test direct download functionality
    const downloadButton = screen.getByText('Download PDF Directly');
    fireEvent.click(downloadButton);
    
    expect(window.open).toHaveBeenCalledWith('http://localhost:8000/generate/download/1', '_blank');
  });
  
  it('displays PDF after successful generation', async () => {
    const mockJobs = [
      {
        id: '1',
        title: 'Frontend Developer',
        company: 'Tech Co',
        location: 'Remote',
        description: 'Frontend development with React',
        created_at: '2023-01-01',
        cv: '# Test CV',
        cv_format: 'markdown'
      }
    ];
    
    (fetchApi as jest.Mock).mockResolvedValue(mockJobs);
    (generatePdfCV as jest.Mock).mockResolvedValue({
      result: 'base64encodedpdf',
      format: 'pdf'
    });
    
    render(<Jobs />);
    
    // Wait for jobs to load and select the job
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Frontend Developer'));
    
    // Generate the PDF
    const generatePdfButton = screen.getByText('Generate PDF');
    fireEvent.click(generatePdfButton);
    
    // After generation, check that the View/Download PDF button is available
    await waitFor(() => {
      expect(screen.getByText('View/Download PDF')).toBeInTheDocument();
    });
    
    // Click the Open PDF button
    const openPdfButton = screen.getByText('Open PDF');
    fireEvent.click(openPdfButton);
    
    // Check that displayPdf was called with the base64 data
    expect(displayPdf).toHaveBeenCalledWith('base64encodedpdf', 'Frontend_Developer_CV.pdf');
  });
  
  it('handles export to text format', async () => {
    // Mock functions needed for text export
    const mockCreateObjectURL = jest.fn(() => 'blob:url');
    URL.createObjectURL = mockCreateObjectURL;
    URL.revokeObjectURL = jest.fn();
    
    // Mock creating an <a> element
    const originalCreateElement = document.createElement;
    const mockClick = jest.fn();
    document.createElement = jest.fn().mockImplementation((tag) => {
      const element = originalCreateElement.call(document, tag);
      if (tag === 'a') {
        element.click = mockClick;
      }
      return element;
    }) as any;
    
    const mockJobs = [
      {
        id: '1',
        title: 'Frontend Developer',
        company: 'Tech Co',
        location: 'Remote',
        description: 'Frontend development with React',
        created_at: '2023-01-01',
        cv: '# Generated CV content',
        cv_format: 'markdown'
      }
    ];
    
    (fetchApi as jest.Mock).mockResolvedValue(mockJobs);
    
    render(<Jobs />);
    
    // Select the job
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Frontend Developer'));
    
    // Export as text
    const exportButton = screen.getByText('Export as Text');
    fireEvent.click(exportButton);
    
    // Verify export logic
    expect(mockCreateObjectURL).toHaveBeenCalled();
    expect(mockClick).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalled();
    
    // Restore original functions
    document.createElement = originalCreateElement;
  });
});