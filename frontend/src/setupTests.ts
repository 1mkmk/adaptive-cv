import '@testing-library/jest-dom';
import 'whatwg-fetch';

// Mock import.meta.env for Vite environment variables
window.VITE_API_URL = 'http://localhost:8000';

// Create a mock for import.meta.env
global.import = { 
  meta: { 
    env: { 
      VITE_API_URL: 'http://localhost:8000' 
    } 
  } 
} as any;

// Mock FormData
if (typeof window.FormData === 'undefined') {
  class MockFormData {
    private data: Map<string, any> = new Map();
    
    append(key: string, value: any) {
      this.data.set(key, value);
    }
    
    get(key: string) {
      return this.data.get(key);
    }
    
    forEach(callback: (value: any, key: string) => void) {
      this.data.forEach((value, key) => callback(value, key));
    }
  }
  
  global.FormData = MockFormData as any;
}