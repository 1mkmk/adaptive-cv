import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select } from '../ui/select';
import { EducationSection } from './education-section';
import { ExperienceSection } from './experience-section';
import { PersonalInfoSection } from './personal-info-section';

const CvForm: React.FC = () => {
  const [personalInfo, setPersonalInfo] = useState({ name: '', email: '', phone: '' });
  const [education, setEducation] = useState([{ degree: '', institution: '', year: '' }]);
  const [experience, setExperience] = useState([{ jobTitle: '', company: '', duration: '' }]);

  const handlePersonalInfoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPersonalInfo({ ...personalInfo, [name]: value });
  };

  const handleEducationChange = (index: number, field: string, value: string) => {
    const updatedEducation = [...education];
    updatedEducation[index][field] = value;
    setEducation(updatedEducation);
  };

  const handleExperienceChange = (index: number, field: string, value: string) => {
    const updatedExperience = [...experience];
    updatedExperience[index][field] = value;
    setExperience(updatedExperience);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission logic
  };

  return (
    <form onSubmit={handleSubmit}>
      <PersonalInfoSection personalInfo={personalInfo} onChange={handlePersonalInfoChange} />
      {education.map((edu, index) => (
        <EducationSection
          key={index}
          education={edu}
          onChange={(field, value) => handleEducationChange(index, field, value)}
        />
      ))}
      {experience.map((exp, index) => (
        <ExperienceSection
          key={index}
          experience={exp}
          onChange={(field, value) => handleExperienceChange(index, field, value)}
        />
      ))}
      <Button type="submit">Generate CV</Button>
    </form>
  );
};

export default CvForm;