import { getProfile, saveProfile, updateProfile } from '@/services/profileService';
import { CandidateProfile } from '@/services/profileService';

// Mock the fetchApi function
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000',
  DIRECT_API_URL: 'http://localhost:8000',
  fetchApi: jest.fn(),
}));

import { fetchApi } from '@/services/api';

describe('Profile Service', () => {
  const mockProfile: CandidateProfile = {
    name: 'Test User',
    email: 'test@example.com',
    phone: '123-456-7890',
    summary: 'Test summary',
    location: 'Test City',
    linkedin: 'https://linkedin.com/in/testuser',
    website: 'https://testuser.com',
    skills: ['JavaScript', 'React', 'Node.js'],
    experience: [
      {
        company: 'Test Company',
        position: 'Developer',
        start_date: '2020-01',
        end_date: '2023-01',
        current: false,
        description: 'Test description',
      },
    ],
    education: [
      {
        institution: 'Test University',
        degree: 'Bachelor',
        field: 'Computer Science',
        start_date: '2016-09',
        end_date: '2020-05',
        current: false,
      },
    ],
    languages: [],
    certifications: [],
    projects: [],
    references: [],
  };

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('getProfile', () => {
    it('should call fetchApi with the correct endpoint', async () => {
      (fetchApi as jest.Mock).mockResolvedValueOnce(mockProfile);

      const result = await getProfile();

      expect(fetchApi).toHaveBeenCalledWith('/profile');
      expect(result).toEqual(mockProfile);
    });

    it('should return null when fetchApi fails', async () => {
      (fetchApi as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await getProfile();

      expect(fetchApi).toHaveBeenCalledWith('/profile');
      expect(result).toBeNull();
    });
  });

  describe('saveProfile', () => {
    it('should call fetchApi with the correct endpoint and parameters', async () => {
      (fetchApi as jest.Mock).mockResolvedValueOnce({ success: true });

      await saveProfile(mockProfile);

      expect(fetchApi).toHaveBeenCalledWith('/profile', {
        method: 'POST',
        body: JSON.stringify(mockProfile),
      });
    });
  });

  describe('updateProfile', () => {
    it('should call fetchApi with the correct endpoint and parameters for partial updates', async () => {
      const partialUpdate = {
        name: 'Updated Name',
        email: 'updated@example.com',
      };

      (fetchApi as jest.Mock).mockResolvedValueOnce({ success: true });

      await updateProfile(partialUpdate);

      expect(fetchApi).toHaveBeenCalledWith('/profile', {
        method: 'PUT',
        body: JSON.stringify(partialUpdate),
      });
    });
  });
});