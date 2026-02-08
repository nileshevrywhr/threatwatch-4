import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase configuration. Please set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY environment variables.'
  );
}

export const AUTH_REDIRECT_BASE = process.env.REACT_APP_AUTH_REDIRECT_BASE || process.env.NEXT_PUBLIC_AUTH_REDIRECT_BASE || "https://threatwatch-4.vercel.app";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
