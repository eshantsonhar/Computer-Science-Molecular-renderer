// Vercel serverless function for submitting feedback
import { getFeedbackDatabaseConfig } from '../lib/feedback-database.cjs';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const feedback = req.body?.feedback;
    if (typeof feedback !== 'string' || feedback.trim().length === 0) {
      return res.status(400).json({ error: 'Feedback is required' });
    }

    const database = getFeedbackDatabaseConfig();
    if (!database) {
      return res.status(500).json({ error: 'Database configuration missing' });
    }

    const response = await fetch(`${database.supabaseUrl}/rest/v1/feedback`, {
      method: 'POST',
      headers: {
        ...database.headers,
        Prefer: 'return=minimal'
      },
      body: JSON.stringify({
        feedback: feedback.trim(),
        created_at: new Date().toISOString()
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Failed to save feedback' });
    }

    return res.status(200).json({ success: true, message: 'Feedback submitted successfully' });
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
