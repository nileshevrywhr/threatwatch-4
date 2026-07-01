import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import { supabase } from '../lib/supabaseClient';
import { getSubscription, extractTier } from '../lib/billing';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subscriptionPlan, setSubscriptionPlan] = useState(null);

  const fetchSubscription = useCallback(async (currentSession) => {
    const activeUser = currentSession?.user;
    if (!activeUser) return;

    try {
      console.log("AuthProvider: Fetching subscription for", activeUser.email);
      const data = await getSubscription();
      console.log("AuthProvider: Subscription API response:", data);

      const tier = extractTier(data);
      console.log("AuthProvider: Setting subscriptionPlan state to:", tier);
      setSubscriptionPlan(tier);
    } catch (error) {
      console.error("AuthProvider: Error fetching subscription:", error);
      const metadataTier = extractTier(activeUser?.user_metadata?.subscription_tier);
      console.log("AuthProvider: Fallback to metadata tier:", metadataTier);
      setSubscriptionPlan(metadataTier);
    }
  }, []);

  // Update subscriptionPlan when session changes
  useEffect(() => {
    if (session) {
      fetchSubscription(session);
    } else {
      setSubscriptionPlan(null);
    }
  }, [session, fetchSubscription]);

  useEffect(() => {
    // Initial session check
    supabase.auth.getSession().then(({ data: { session: initialSession } }) => {
      console.log("AuthProvider: Initial session check:", initialSession?.user?.email);
      setSession(initialSession);
      setUser(initialSession?.user ?? null);
      setLoading(false);
    }).catch((error) => {
      console.error("AuthProvider: Error getting session:", error);
      setSession(null);
      setUser(null);
      setLoading(false);
    });

    // Auth state changes
    const { data } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      console.log("AuthProvider: Auth state changed:", _event, currentSession?.user?.email);
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      setLoading(false);
    });

    return () => {
      if (data && data.subscription) {
        data.subscription.unsubscribe();
      }
    };
  }, []);

  const signOut = useCallback(async () => {
    console.log("AuthProvider: Signing out");
    await supabase.auth.signOut();
  }, []);

  const value = useMemo(() => ({
    session,
    user,
    signOut,
    loading,
    subscriptionPlan,
    refreshSubscription: () => fetchSubscription(session)
  }), [session, user, signOut, loading, subscriptionPlan, fetchSubscription]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
