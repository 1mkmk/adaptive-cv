import React, { createContext, useState, useEffect, useContext } from 'react';
import { fetchApi, API_BASE_URL } from '../services/api';

interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  locale: string;
  is_guest: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  login: () => {},
  logout: () => {}
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchUser = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const userData = await fetchApi('/auth/me');
      setUser(userData);
    } catch (err) {
      console.error('Error fetching user:', err);
      setUser(null);
      setError('Failed to load user. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchUser();
  }, []);
  
  const login = () => {
    // Redirect to Google login
    window.location.href = `${API_BASE_URL}/auth/google/authorize`;
  };
  
  const logout = async () => {
    try {
      await fetchApi('/auth/logout');
      setUser(null);
      // Redirect to home page after logout
      window.location.href = '/';
    } catch (err) {
      console.error('Error logging out:', err);
      setError('Failed to log out. Please try again.');
    }
  };
  
  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};