import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let mounted = true;

    const handleAuth = async () => {
      try {
        // 1. Check for errors in URL (Query or Hash)
        const queryParams = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(window.location.hash.substring(1));

        const error = queryParams.get('error_description') ||
                      queryParams.get('error') ||
                      hashParams.get('error_description') ||
                      hashParams.get('error');

        if (error) {
          throw new Error(error);
        }

        // 2. Handle PKCE code exchange
        const code = queryParams.get('code');
        if (code) {
          console.log('Exchanging code for session...');
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) throw exchangeError;
        }

        // 3. Final session check
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        if (sessionError) throw sessionError;

        if (session) {
          if (mounted) {
            setStatus('success');
            // Wait a moment to show success state for better UX
            setTimeout(() => {
              if (mounted) navigate('/feed', { replace: true });
            }, 1500);
          }
        } else {
          // If no session immediately, wait for onAuthStateChange as a fallback
          const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            if (session && mounted) {
              subscription.unsubscribe();
              setStatus('success');
              setTimeout(() => {
                if (mounted) navigate('/feed', { replace: true });
              }, 1500);
            }
          });

          // Timeout after 5 seconds if still nothing
          setTimeout(() => {
            if (mounted && status === 'verifying') {
               setStatus('error');
               setErrorMessage('No active session found. Please try logging in again.');
               setTimeout(() => {
                 if (mounted) navigate('/login', { replace: true });
               }, 3000);
            }
          }, 5000);

          return () => subscription.unsubscribe();
        }
      } catch (err) {
        console.error('Auth callback error:', err);
        if (mounted) {
          setStatus('error');
          setErrorMessage(err.message || 'Authentication failed');
          // Auto redirect to login after 3 seconds on error
          setTimeout(() => {
            if (mounted) navigate(`/login?error=${encodeURIComponent(err.message || 'Authentication failed')}`, { replace: true });
          }, 3000);
        }
      }
    };

    handleAuth();
    return () => { mounted = false; };
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4" role="status" aria-label="Authentication Callback">
      <div className="max-w-md w-full text-center space-y-6">
        {status === 'verifying' && (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-cyan-500 mx-auto" />
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-white">Verifying your account</h2>
              <p className="text-slate-400">Please wait while we complete the authentication process...</p>
            </div>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="h-12 w-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-white">Account Verified!</h2>
              <p className="text-slate-400">Redirecting you to your intelligence feed...</p>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="h-12 w-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto">
              <AlertCircle className="h-8 w-8 text-red-500" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-white">Verification Failed</h2>
              <p className="text-red-400">{errorMessage}</p>
              <p className="text-slate-500 text-sm mt-4">Redirecting to login page...</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;
