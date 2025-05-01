import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router';
import Navbar from './components/ui/Navbar';
import Home from './pages/Home';
import Profile from './pages/Profile';
import Templates from './pages/templates';
import Jobs from './pages/Jobs';
import Login from './pages/auth/Login';
import { useAuth } from './context/AuthContext';
import { useTranslation } from 'react-i18next';

// Protected route component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  
  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }
  
  if (!isAuthenticated) {
    // Redirect to login page but save the current location they tried to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return <>{children}</>;
};

const App: React.FC = () => {
  const { i18n } = useTranslation();
  
  return (
    <div className="app-container" dir={i18n.dir()}>
      <Routes>
        <Route 
          path="/login" 
          element={<Login />} 
        />
        
        <Route 
          path="/" 
          element={
            <>
              <Navbar />
              <main className="container mx-auto px-4 py-8">
                <Home />
              </main>
            </>
          } 
        />
        
        {/* Protected routes */}
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Navbar />
              <main className="container mx-auto px-4 py-8">
                <Profile />
              </main>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/templates" 
          element={
            <ProtectedRoute>
              <Navbar />
              <main className="container mx-auto px-4 py-8">
                <Templates />
              </main>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/jobs" 
          element={
            <ProtectedRoute>
              <Navbar />
              <main className="container mx-auto px-4 py-8">
                <Jobs />
              </main>
            </ProtectedRoute>
          } 
        />
        
        {/* New route: Redirect to business-card landing page */}
        <Route 
          path="/landing/*" 
          element={<Navigate to={window.location.origin + "/landing"} replace />} 
        />
        
        {/* Catch all for 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
};

export default App;