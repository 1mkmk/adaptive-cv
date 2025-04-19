import { getJobs, getJob, createJob, deleteJob } from '@/services/jobService';
import type { Job, JobCreateParams } from '@/services/jobService';

// Mock the fetchApi function
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000',
  DIRECT_API_URL: 'http://localhost:8000',
  fetchApi: jest.fn(),
}));

import { fetchApi } from '@/services/api';

describe('Job Service', () => {
  const mockJobs: Job[] = [
    {
      id: 1,
      title: 'Frontend Developer',
      company: 'Tech Company',
      location: 'Remote',
      description: 'Frontend development position',
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 2,
      title: 'Backend Developer',
      company: 'Another Company',
      location: 'New York',
      description: 'Backend development position',
      created_at: '2025-01-02T00:00:00Z',
    },
  ];

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('getJobs', () => {
    it('should call fetchApi with the correct endpoint', async () => {
      (fetchApi as jest.Mock).mockResolvedValueOnce(mockJobs);

      const result = await getJobs();

      expect(fetchApi).toHaveBeenCalledWith('/jobs');
      expect(result).toEqual(mockJobs);
    });

    it('should return an empty array when fetchApi fails', async () => {
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await getJobs();

      expect(fetchApi).toHaveBeenCalledWith('/jobs');
      expect(result).toEqual([]);
    });
  });

  describe('getJob', () => {
    it('should call fetchApi with the correct endpoint', async () => {
      (fetchApi as jest.Mock).mockResolvedValueOnce(mockJobs[0]);

      const result = await getJob(1);

      expect(fetchApi).toHaveBeenCalledWith('/jobs/1');
      expect(result).toEqual(mockJobs[0]);
    });

    it('should return null when fetchApi fails', async () => {
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await getJob(1);

      expect(fetchApi).toHaveBeenCalledWith('/jobs/1');
      expect(result).toBeNull();
    });
  });

  describe('createJob', () => {
    it('should call fetchApi with the correct endpoint and FormData', async () => {
      const mockJobData: JobCreateParams = {
        title: 'Software Engineer',
        company: 'New Company',
        location: 'Berlin',
        description: 'Exciting role',
        requirements: 'JavaScript, React',
      };

      (fetchApi as jest.Mock).mockImplementationOnce((url, options) => {
        // Verify FormData was created properly
        expect(url).toBe('/jobs/create');
        expect(options.method).toBe('POST');
        expect(options.body instanceof FormData).toBe(true);
        
        // Return the mock job with ID
        return Promise.resolve({ ...mockJobData, id: 3, created_at: '2025-01-03T00:00:00Z' });
      });

      const result = await createJob(mockJobData);

      expect(fetchApi).toHaveBeenCalled();
      expect(result).toEqual({
        ...mockJobData,
        id: 3,
        created_at: '2025-01-03T00:00:00Z',
      });
    });

    it('should return null when fetchApi fails', async () => {
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await createJob({
        title: 'Software Engineer',
        company: 'New Company',
        location: 'Berlin',
        description: 'Exciting role',
      });

      expect(fetchApi).toHaveBeenCalled();
      expect(result).toBeNull();
    });
  });

  describe('deleteJob', () => {
    it('should call fetchApi with the correct endpoint and method', async () => {
      (fetchApi as jest.Mock).mockResolvedValueOnce({ detail: 'Job deleted successfully' });

      const result = await deleteJob(1);

      expect(fetchApi).toHaveBeenCalledWith('/jobs/1', {
        method: 'DELETE',
      });
      expect(result).toBe(true);
    });

    it('should return false when fetchApi fails', async () => {
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await deleteJob(1);

      expect(fetchApi).toHaveBeenCalledWith('/jobs/1', {
        method: 'DELETE',
      });
      expect(result).toBe(false);
    });
  });
});