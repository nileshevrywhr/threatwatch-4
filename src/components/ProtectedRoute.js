import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthProvider';
import { Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div
        className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4"
        role="status"
        aria-label="Verifying authentication"
      >
        <Loader2 className="h-10 w-10 animate-spin text-cyan-500" aria-hidden="true" />
        <p className="text-slate-400 animate-pulse font-medium">Verifying authentication...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
