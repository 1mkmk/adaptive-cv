import { useState } from 'react';

interface CvData {
  personalInfo: {
    name: string;
    email: string;
    phone: string;
  };
  education: Array<{
    institution: string;
    degree: string;
    year: string;
  }>;
  experience: Array<{
    company: string;
    position: string;
    duration: string;
  }>;
}

const useCvData = () => {
  const [cvData, setCvData] = useState<CvData>({
    personalInfo: {
      name: '',
      email: '',
      phone: '',
    },
    education: [],
    experience: [],
  });

  const updatePersonalInfo = (info: Partial<CvData['personalInfo']>) => {
    setCvData((prevData) => ({
      ...prevData,
      personalInfo: {
        ...prevData.personalInfo,
        ...info,
      },
    }));
  };

  const addEducation = (education: CvData['education'][0]) => {
    setCvData((prevData) => ({
      ...prevData,
      education: [...prevData.education, education],
    }));
  };

  const addExperience = (experience: CvData['experience'][0]) => {
    setCvData((prevData) => ({
      ...prevData,
      experience: [...prevData.experience, experience],
    }));
  };

  return {
    cvData,
    updatePersonalInfo,
    addEducation,
    addExperience,
  };
};

export default useCvData;