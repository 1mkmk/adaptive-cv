import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router';
import Header from './components/layout/header';
import Footer from './components/layout/footer';
import Sidebar from './components/layout/sidebar';
import Index from './pages/index';
import Editor from './pages/editor';
import Templates from './pages/templates';
import Preview from './pages/preview';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <Sidebar />
        <main>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/editor" element={<Editor />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/preview" element={<Preview />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App;