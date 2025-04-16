import React from 'react';
import CvForm from '../components/cv/cv-form';
import CvPreview from '../components/cv/cv-preview';

const Editor: React.FC = () => {
  return (
    <div className="editor-container">
      <h1>Edit Your CV</h1>
      <CvForm />
      <CvPreview />
    </div>
  );
};

export default Editor;