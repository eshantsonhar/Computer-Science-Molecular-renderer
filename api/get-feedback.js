// Vercel serverless function for retrieving feedback (admin)
import { getFeedbackDatabaseConfig } from '../lib/feedback-database.mjs';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const database = getFeedbackDatabaseConfig();
    if (!database) {
      return res.status(500).json({ error: 'Database configuration missing' });
    }

    const response = await fetch(
      `${database.supabaseUrl}/rest/v1/feedback?order=created_at.desc`,
      { method: 'GET', headers: database.headers }
    );

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
