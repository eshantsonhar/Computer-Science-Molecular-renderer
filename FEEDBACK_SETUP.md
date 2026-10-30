# Feedback System Setup Instructions

The feedback system now uses a centralized database (Supabase) instead of localStorage, so feedback from any device will be visible in the admin panel.

## Setup Steps:

### 1. Create a Supabase Project (Free)

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up for a free account
3. Click "New Project"
4. Choose a name (e.g., "atomview-feedback")
5. Set a database password (save this!)
6. Choose a region closest to you
7. Wait for the project to be created (1-2 minutes)

### 2. Create the Feedback Table

1. In your Supabase project dashboard, go to "Table Editor"
2. Click "Create a new table"
3. Name the table: `feedback`
4. Add columns:
   - `id` (default, auto-increment)
   - `feedback` (type: text)
   - `created_at` (default, timestamp)
5. Click "Save"

### 3. Get Your Supabase Credentials

1. In Supabase dashboard, go to "Settings" → "API Keys"
2. Copy these values:
   - **Project URL** (this is your SUPABASE_URL)
   - **Secret key** (click reveal button, starts with `sb_secret_...`) - this is your SUPABASE_SECRET_KEY
   - ⚠️ Use the **secret key**, NOT the publishable key!

### 4. Configure Vercel Environment Variables

1. Go to your Vercel project dashboard
2. Go to "Settings" → "Environment Variables"
3. Add the following variables:

   **Name:** `SUPABASE_URL`
   **Value:** (paste your Supabase Project URL from step 3)
   **Environments:** Production, Preview, Development

   **Name:** `SUPABASE_SECRET_KEY`
   **Value:** (paste your secret key from step 3, starts with `sb_secret_...`)
   **Environments:** Production, Preview, Development

4. Click "Save"
5. Redeploy your project (Vercel will auto-deploy or you can trigger it manually)

### 5. Test the System

1. Visit your deployed site
2. Go to the Feedback page
3. Submit some feedback
4. Visit the admin page at: `your-domain.com/pages/admin_feedback.html`
5. Enter password: `orsonkrennic2cracked`
6. You should see the feedback you just submitted
7. Try from a different device/browser - it should all appear in the same list!

## Troubleshooting

- If feedback submission fails: Check that environment variables are set correctly in Vercel
- If admin page shows error: Verify the `feedback` table exists in Supabase
- Make sure you're using the `service_role` key, not the `anon` key

## Security Notes

- The admin page is not linked from anywhere on the main site (must access via direct URL)
- Password protection is on the client side (for this simple implementation)
- For production, consider adding Row Level Security (RLS) in Supabase for additional security
