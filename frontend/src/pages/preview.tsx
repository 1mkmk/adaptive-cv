import React from 'react';
import CvPreview from '../components/cv/cv-preview';
import useCvData from '../hooks/use-cv-data';

const Preview: React.FC = () => {
  const { cvData } = useCvData();

  return (
    <div className="preview-container">
      <h1 className="text-2xl font-bold">CV Preview</h1>
      <CvPreview data={cvData} />
    </div>
  );
};

export default Preview;