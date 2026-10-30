// Vercel serverless function for retrieving feedback (admin)
export default async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Environment variables (set in Vercel dashboard)
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !supabaseKey) {
      return res.status(500).json({ error: 'Database configuration missing' });
    }

    // Fetch all feedback from Supabase, ordered by created_at descending
    const response = await fetch(`${supabaseUrl}/rest/v1/feedback?order=created_at.desc`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      }
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Failed to retrieve feedback' });
    }

    const data = await response.json();

    return res.status(200).json({ success: true, feedback: data });
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
