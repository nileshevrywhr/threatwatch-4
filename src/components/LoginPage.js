import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthModal from './AuthModal';
import { useAuth } from './AuthProvider';
import { Loader2 } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && user) {
      navigate('/feed');
    }
  }, [user, loading, navigate]);

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

  // If we are not loading and have no user, show the login modal
  // Note: If user exists, we return null to avoid flash while the useEffect redirects
  if (user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center p-4">
      <AuthModal
        isOpen={true}
        onClose={() => navigate('/')}
        onAuthSuccess={() => navigate('/feed')}
      />
    </div>
  );
};

export default LoginPage;
