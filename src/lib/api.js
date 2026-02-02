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

export const getMonitors = () => {
  return apiClient('/api/monitors');
};

export const getReportsForMonitor = (monitorId) => {
  return apiClient(`/api/monitors/${monitorId}/reports`);
};

export const downloadReport = async (reportId) => {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error('No active session');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/reports/${reportId}/download`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
      redirect: 'follow', // Follow the redirect to the PDF URL
    });

    if (response.status === 401) {
      throw new Error('Session expired or invalid');
    }

    if (!response.ok) {
      throw new Error('Failed to download report');
    }

    // Get the blob from the response (will be the PDF after redirect)
    const blob = await response.blob();

    // Create a download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `threat-report-${reportId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
};
