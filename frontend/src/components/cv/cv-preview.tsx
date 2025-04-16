import React from 'react';

const CvPreview: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="cv-preview">
      <h1>{data.name}</h1>
      <p>{data.email}</p>
      <p>{data.phone}</p>
      <h2>Education</h2>
      {data.education.map((edu: any, index: number) => (
        <div key={index}>
          <h3>{edu.degree}</h3>
          <p>{edu.institution}</p>
          <p>{edu.year}</p>
        </div>
      ))}
      <h2>Experience</h2>
      {data.experience.map((exp: any, index: number) => (
        <div key={index}>
          <h3>{exp.jobTitle}</h3>
          <p>{exp.company}</p>
          <p>{exp.years}</p>
        </div>
      ))}
    </div>
  );
};

export default CvPreview;