import React from 'react';
import Header from '../components/layout/header';
import Footer from '../components/layout/footer';
import CvForm from '../components/cv/cv-form';

const Index: React.FC = () => {
  return (
    <div>
      <Header />
      <main>
        <h1>Welcome to the CV Creator</h1>
        <CvForm />
      </main>
      <Footer />
    </div>
  );
};

export default Index;