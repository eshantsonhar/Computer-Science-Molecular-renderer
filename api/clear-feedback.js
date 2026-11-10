// Vercel serverless function for clearing all feedback (admin)
import { getFeedbackDatabaseConfig } from '../lib/feedback-database.mjs';

export default async function handler(req, res) {
  if (req.method !== 'DELETE') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const database = getFeedbackDatabaseConfig();
    if (!database) {
      return res.status(500).json({ error: 'Database configuration missing' });
    }

    const response = await fetch(`${database.supabaseUrl}/rest/v1/feedback`, {
      method: 'DELETE',
      headers: {
        ...database.headers,
        Prefer: 'return=minimal'
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
