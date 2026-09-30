import { supabase } from './supabase';
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function api(path, options = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  const headers = new Headers(options.headers || {});
  if (session?.access_token) headers.set('Authorization', `Bearer ${session.access_token}`);
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const res = await fetch(`${API}${path}`, { ...options, headers });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || 'Request failed');
  return body;
}
