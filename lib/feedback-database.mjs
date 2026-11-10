export function getFeedbackDatabaseConfig(env = process.env) {
  const supabaseUrl = env.SUPABASE_URL?.replace(/\/+$/, '');
  const apiKey = env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !apiKey) {
    return null;
  }

  const headers = {
    'Content-Type': 'application/json',
    apikey: apiKey
  };

  if (!apiKey.startsWith('sb_secret_')) {
    headers.Authorization = `Bearer ${apiKey}`;
  }

  return { supabaseUrl, headers };
}
