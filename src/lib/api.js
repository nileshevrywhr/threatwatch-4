import { supabase } from './supabaseClient';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

class UnauthorizedError extends Error {
  constructor(message) {
    super(message);
    this.name = 'UnauthorizedError';
    this.status = 401;
  }
}

const apiClient = async (endpoint, options = {}) => {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new UnauthorizedError('No active session');
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    throw new UnauthorizedError('Session expired or invalid');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || 'API request failed');
    error.status = response.status;
    error.response = { data: errorData, status: response.status };
    throw error;
  }

  return response.json();
};

export const getFeed = () => {
  return apiClient('/api/feed');
};

export const downloadReport = (reportId) => {
  // Redirect-based download as requested.
  // Note: This does not attach the Bearer token header, so the endpoint
  // must rely on cookies or be accessible without the header for this flow.
  const url = `${API_BASE_URL}/api/reports/${reportId}/download`;
  window.location.href = url;
};
