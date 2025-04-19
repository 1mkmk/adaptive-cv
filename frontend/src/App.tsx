import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router';
import Home from './pages/Home';
import Profile from './pages/Profile';
import Templates from './pages/Templates';
import Jobs from './pages/Jobs';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app-container">
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/jobs" element={<Jobs />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;