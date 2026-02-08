import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { Loader2 } from 'lucide-react';

const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Supabase automatically handles the auth token from the URL hash/query
        // Calling getSession() ensures we wait for the session to be established
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error) throw error;

        if (session) {
          // Success! Redirect to feed
          navigate('/feed', { replace: true });
        } else {
          // No session found, might be an invalid or expired link
          throw new Error('No active session found.');
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        const errorMessage = error.message || 'Authentication failed';
        navigate(`/login?error=${encodeURIComponent(errorMessage)}`, { replace: true });
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center" role="status" aria-label="Verifying authentication">
      <Loader2 className="h-10 w-10 animate-spin text-cyan-500" />
      <p className="mt-4 text-slate-400 animate-pulse font-medium">Verifying authentication...</p>
    </div>
  );
};

export default AuthCallback;
