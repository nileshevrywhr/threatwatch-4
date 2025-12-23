import React from 'react';
import { useNavigate } from 'react-router-dom';
import AuthModal from './AuthModal';
import { useAuth } from './AuthProvider';

const LoginPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) {
      navigate('/feed');
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center p-4">
      {/* Background elements to match LandingPage vibe if desired, or keep simple */}
      <AuthModal
        isOpen={true}
        onClose={() => navigate('/')}
        onAuthSuccess={() => navigate('/feed')}
      />
    </div>
  );
};

export default LoginPage;
