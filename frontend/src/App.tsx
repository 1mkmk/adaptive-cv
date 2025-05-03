import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router';
import Navbar from './components/ui/Navbar';
import Profile from './pages/Profile';
import Templates from './pages/templates';
import Jobs from './pages/Jobs';
import Account from './pages/Account';
import Login from './pages/auth/Login';
import { useAuth } from './context/AuthContext';
import { useTranslation } from 'react-i18next';
import SubscriptionManager from './components/subscription/SubscriptionManager';

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
  const { isAuthenticated } = useAuth();
  const { t } = useTranslation();
  
  return (
    <div className="min-h-screen bg-slate-50">
      <SubscriptionManager>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route 
            path="/" 
            element={
              isAuthenticated ? 
                <Navigate to="/profile" replace /> : 
                <Navigate to="/login" replace />
            } 
          />
          
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
          
          {/* Account settings path */}
          <Route 
            path="/account-settings" 
            element={
              <ProtectedRoute>
                <Navbar />
                <main className="container mx-auto px-4 py-8">
                  <Account />
                </main>
              </ProtectedRoute>
            } 
          />
          
          {/* Catch all for 404 */}
          <Route path="*" element={<Navigate to={isAuthenticated ? "/jobs" : "/login"} replace />} />
        </Routes>
      </SubscriptionManager>
    </div>
  );
};

export default App;