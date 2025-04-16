import React, { createContext, useContext, useState, ReactNode } from 'react';

interface CVData {
  personalInfo: {
    name: string;
    email: string;
    phone: string;
  };
  education: Array<{
    degree: string;
    institution: string;
    year: string;
  }>;
  experience: Array<{
    jobTitle: string;
    company: string;
    duration: string;
  }>;
}

interface CVContextType {
  cvData: CVData;
  setCvData: React.Dispatch<React.SetStateAction<CVData>>;
}

const CVContext = createContext<CVContextType | undefined>(undefined);

export const CVProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [cvData, setCvData] = useState<CVData>({
    personalInfo: { name: '', email: '', phone: '' },
    education: [],
    experience: [],
  });

  return (
    <CVContext.Provider value={{ cvData, setCvData }}>
      {children}
    </CVContext.Provider>
  );
};

export const useCVContext = () => {
  const context = useContext(CVContext);
  if (!context) {
    throw new Error('useCVContext must be used within a CVProvider');
  }
  return context;
};