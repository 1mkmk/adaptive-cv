// Mock for api.ts - use this in tests
export const API_BASE_URL = 'http://localhost:8000';
export const DIRECT_API_URL = 'http://localhost:8000';

export const fetchApi = jest.fn().mockImplementation(async (endpoint, options = {}) => {
  // Default implementation just returns a successful mock response
  return { success: true, data: { message: 'Mocked API response' } };
});