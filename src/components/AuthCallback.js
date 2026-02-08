import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { Loader2 } from 'lucide-react';

const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Set a timeout as a fallback in case Supabase fails to establish a session
    const timeout = setTimeout(() => {
      console.error('Auth callback timeout: No session established within 10 seconds.');
      navigate('/login?error=Authentication%20timed%20out.%20Please%20try%20signing%20in%20again.', { replace: true });
    }, 10000);

    // Use onAuthStateChange to wait for the session to be established
    // This is more reliable than getSession() which might be called too early
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      // If we have a session, the auth process was successful
      if (session) {
        clearTimeout(timeout);
        navigate('/feed', { replace: true });
      }

      // We can also handle explicit sign out or failure events if needed,
      // but session presence is the ultimate indicator of success here.
    });

    return () => {
      clearTimeout(timeout);
      if (subscription) {
        subscription.unsubscribe();
      }
    };
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center" role="status" aria-label="Verifying authentication">
      <Loader2 className="h-10 w-10 animate-spin text-cyan-500" />
      <p className="mt-4 text-slate-400 animate-pulse font-medium">Verifying authentication...</p>
    </div>
  );
};

export default AuthCallback;
