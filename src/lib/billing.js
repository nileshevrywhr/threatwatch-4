import { supabase } from './supabaseClient';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const apiClient = async (endpoint, options = {}) => {
  const { data: { session } } = await supabase.auth.getSession();

  const headers = {
    'Content-Type': 'application/json',
    ...(session?.access_token ? { 'Authorization': `Bearer ${session.access_token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || 'API request failed');
    error.status = response.status;
    throw error;
  }

  return response.json();
};

export const getSubscription = () => {
  return apiClient('/api/billing/subscription');
};

export const cancelSubscription = () => {
  return apiClient('/api/billing/cancel', {
    method: 'POST'
  });
};
