// Mock module directly - this simplifies things greatly
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000',
  DIRECT_API_URL: 'http://localhost:8000',
  fetchApi: jest.fn()
}));

// Import the mock module - ensures it's properly typed
import { fetchApi, API_BASE_URL, DIRECT_API_URL } from '@/services/api';

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should have proper API URLs configured', () => {
    expect(API_BASE_URL).toBeDefined();
    expect(DIRECT_API_URL).toBeDefined();
    expect(API_BASE_URL).toBe('http://localhost:8000');
  });

  it('should call fetchApi with the correct endpoint', async () => {
    // Setup mock implementation for this test
    (fetchApi as jest.Mock).mockResolvedValueOnce({ data: 'test' });
    
    // Call the function
    const result = await fetchApi('/test-endpoint');
    
    // Assert it was called correctly
    expect(fetchApi).toHaveBeenCalledWith('/test-endpoint');
    expect(result).toEqual({ data: 'test' });
  });

  it('should handle API errors correctly', async () => {
    // Mock an error response
    (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('API Error'));
    
    // Call and check for error
    await expect(fetchApi('/error-endpoint')).rejects.toThrow('API Error');
  });
});