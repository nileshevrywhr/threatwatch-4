import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import { supabase } from '../lib/supabaseClient';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check active sessions and sets the user
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    }).catch((error) => {
      console.error("Error getting session:", error);
      setSession(null);
      setUser(null);
      setLoading(false);
    });

    // Listen for changes on auth state (logged in, signed out, etc.)
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      try {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
      } catch (error) {
        console.error("Error in auth state change:", error);
        setLoading(false);
      }
    });

    return () => {
      if (data && data.subscription) {
        data.subscription.unsubscribe();
      }
    };
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
  }, []);

  // Performance Optimization: Memoize the context value to prevent unnecessary re-renders
  // in consuming components when AuthProvider's parent re-renders but auth state hasn't changed.
  const value = useMemo(() => ({
    session,
    user,
    signOut,
    loading
  }), [session, user, signOut, loading]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
