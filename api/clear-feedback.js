// Vercel serverless function for clearing all feedback (admin)
export default async function handler(req, res) {
  // Only allow DELETE requests
  if (req.method !== 'DELETE') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Environment variables (set in Vercel dashboard)
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !supabaseKey) {
      return res.status(500).json({ error: 'Database configuration missing' });
    }

    // Delete all feedback from Supabase
    const response = await fetch(`${supabaseUrl}/rest/v1/feedback`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Prefer': 'return=minimal'
      }
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Failed to clear feedback' });
    }

    return res.status(200).json({ success: true, message: 'All feedback cleared successfully' });
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
