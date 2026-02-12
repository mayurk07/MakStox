# UDTS Stock Analyzer - Deployment Guide

This guide will help you deploy the UDTS Stock Analyzer application to production using:
- **Backend**: Render.com (Free tier - 750 hours/month)
- **Database**: Supabase PostgreSQL (Already configured)
- **Frontend**: Vercel (Unlimited free for personal projects)

---

## Prerequisites

Before you begin, make sure you have:
1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Supabase project (already set up in this Bolt session)
4. Supabase Service Role Key (we'll get this in Step 1)

---

## Step 1: Get Your Supabase Service Role Key

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Click on **Settings** (gear icon) in the left sidebar
4. Click on **API** in the settings menu
5. Under **Project API keys**, find the **service_role** key
6. Click the **Copy** button next to it
7. **IMPORTANT**: Keep this key secure - it has full admin access to your database!

---

## Step 2: Deploy Backend to Render.com

### 2.1 Create Render Account
1. Go to https://render.com
2. Click **Sign Up** and create an account (you can sign up with GitHub)
3. Verify your email address

### 2.2 Connect GitHub Repository
1. In Render Dashboard, click **New +** button
2. Select **Blueprint**
3. Click **Connect GitHub** and authorize Render to access your repositories
4. Select your repository from the list

### 2.3 Configure Environment Variables
Render will automatically detect the `render.yaml` file. You need to add these environment variables:

1. After connecting your repo, Render will show a configuration screen
2. Add these environment variables:

   ```
   VITE_SUPABASE_URL=https://lqodntgumcjwbdwvsprm.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=<paste-your-service-role-key-here>
   CORS_ORIGINS=*
   ```

3. Replace `<paste-your-service-role-key-here>` with the service role key you copied in Step 1

### 2.4 Deploy
1. Click **Apply** to create the service
2. Render will automatically:
   - Install Python dependencies
   - Start your FastAPI backend
   - Assign a free URL like: `https://udts-stock-analyzer-backend.onrender.com`
3. Wait 5-10 minutes for the first deployment to complete
4. Once deployed, click on the service URL to verify it's working (you should see a health check response)

### 2.5 Get Your Backend URL
1. In your Render service dashboard, you'll see your service URL
2. Copy this URL - you'll need it for the frontend deployment
3. Example: `https://udts-stock-analyzer-backend.onrender.com`

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account
1. Go to https://vercel.com
2. Click **Sign Up** and create an account (sign up with GitHub is recommended)
3. Authorize Vercel to access your repositories

### 3.2 Import Project
1. In Vercel Dashboard, click **Add New...** → **Project**
2. Select **Import Git Repository**
3. Find and select your repository
4. Click **Import**

### 3.3 Configure Build Settings
1. Vercel will auto-detect it's a React app
2. Update these settings:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### 3.4 Add Environment Variables
1. In the configuration screen, add these environment variables:

   ```
   REACT_APP_API_URL=https://your-render-backend-url.onrender.com
   VITE_SUPABASE_URL=https://lqodntgumcjwbdwvsprm.supabase.co
   VITE_SUPABASE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxxb2RudGd1bWNqd2Jkd3ZzcHJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA5MDQ1NzcsImV4cCI6MjA4NjQ4MDU3N30.S3UPt92c2nDVT4TwTVIhzzr8rU4Kj3T5TyNzPsne954
   ```

2. **IMPORTANT**: Replace `https://your-render-backend-url.onrender.com` with the actual Render URL from Step 2.5

### 3.5 Deploy
1. Click **Deploy**
2. Vercel will automatically:
   - Install npm dependencies
   - Build your React app
   - Deploy to a global CDN
   - Assign a free URL like: `https://your-app.vercel.app`
3. Wait 2-3 minutes for deployment to complete
4. Once deployed, click **Visit** to see your live application!

---

## Step 4: Update CORS Settings (Important!)

After deploying both frontend and backend:

1. Go back to your Render.com dashboard
2. Select your backend service
3. Go to **Environment** section
4. Update the `CORS_ORIGINS` variable:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app
   ```
5. Replace `your-app` with your actual Vercel domain
6. Click **Save Changes**
7. Render will automatically redeploy with the new CORS settings

---

## Step 5: Verify Deployment

Test your deployed application:

1. **Backend Health Check**:
   - Visit: `https://your-backend.onrender.com/health`
   - You should see: `{"status": "healthy", "database": "supabase", "db_status": "connected"}`

2. **Frontend**:
   - Visit your Vercel URL
   - The app should load and display the stock screener
   - Try clicking the **Refresh Stock List** button to verify it's connected to the backend

3. **Database Connection**:
   - In the app, the stock data should load (may take 8-12 minutes for first load)
   - Check your Supabase dashboard → Table Editor → you should see data in the cache tables after the first load

---

## Step 6: Set Up Auto-Deployment (Optional but Recommended)

Both Render and Vercel support automatic deployments from GitHub:

1. **Render**: Already configured via `render.yaml` with `autoDeploy: true`
2. **Vercel**: Automatically enabled when you connect via GitHub

Now whenever you push code to your GitHub repository:
- Backend will automatically redeploy on Render
- Frontend will automatically redeploy on Vercel

---

## Important Notes

### Free Tier Limitations

**Render.com Free Tier**:
- 750 hours/month (enough for 24/7 uptime for one service)
- Services spin down after 15 minutes of inactivity
- First request after spin-down will take 30-60 seconds
- ⚠️ **IMPORTANT**: The heartbeat mechanism in the code will keep your service alive and prevent spin-downs

**Vercel Free Tier**:
- Unlimited deployments
- 100 GB bandwidth per month
- Global CDN included
- Custom domains supported

**Supabase Free Tier**:
- 500 MB database storage
- Unlimited API requests
- Auto-pauses after 7 days of inactivity (easily reactivated)

### Security Best Practices

1. **Never commit secrets to Git**:
   - The `.env` file is already in `.gitignore`
   - Always use environment variables on Render and Vercel

2. **Service Role Key**:
   - Only use it on the backend
   - Never expose it in frontend code or logs
   - Keep it in Render environment variables only

3. **CORS Settings**:
   - Update CORS_ORIGINS to only allow your Vercel domain
   - Don't use `*` in production for security

### Database Migration

The database schema is already created and configured in your Supabase project. The backend will automatically:
- Connect to Supabase on startup
- Store cached data in the 4 tables we created
- Handle cache invalidation and refresh

### Monitoring

1. **Render Logs**:
   - Go to your service dashboard
   - Click **Logs** tab to see real-time backend logs

2. **Vercel Analytics**:
   - Available in your project dashboard
   - Shows page views, performance metrics

3. **Supabase Logs**:
   - Go to your project → Logs
   - See all database queries and API calls

---

## Troubleshooting

### Backend not connecting to database

**Symptom**: Health check shows `"db_status": "unavailable"`

**Solution**:
1. Verify `SUPABASE_SERVICE_ROLE_KEY` is set correctly in Render
2. Check Render logs for connection errors
3. Verify the Supabase URL is correct

### Frontend can't reach backend

**Symptom**: Stock data not loading, network errors in browser console

**Solution**:
1. Verify `REACT_APP_API_URL` is set correctly in Vercel
2. Check that CORS is configured properly in Render
3. Verify backend is running (check Render dashboard)

### First Load Takes Too Long

**Symptom**: Initial stock data load takes more than 15 minutes

**Solution**:
- This is normal for the first load (500 stocks)
- After first load, data is cached in Supabase
- Subsequent loads will be instant (< 5 seconds)
- The app auto-refreshes every 15 minutes

### Backend Keeps Spinning Down

**Symptom**: Backend URL returns "Service Unavailable" intermittently

**Solution**:
- The built-in heartbeat should prevent this
- Verify the heartbeat thread is running (check Render logs)
- The code has a 3-minute ping to keep the service alive

---

## Cost Estimation

With the recommended free tiers:

| Service | Cost |
|---------|------|
| Render.com (Backend) | **$0/month** (750 free hours) |
| Vercel (Frontend) | **$0/month** (unlimited free) |
| Supabase (Database) | **$0/month** (free tier) |
| **Total** | **$0/month** |

To scale beyond free tiers:
- Render Starter: $7/month (no spin-down)
- Vercel Pro: $20/month (team features, more bandwidth)
- Supabase Pro: $25/month (8 GB storage, no pause)

---

## Next Steps

After successful deployment:

1. **Custom Domain** (Optional):
   - Vercel: Add your domain in project settings
   - Render: Available on paid plans

2. **Monitoring** (Recommended):
   - Set up Uptime monitoring (e.g., UptimeRobot, Pingdom)
   - Monitor Render logs for errors

3. **Backup** (Recommended):
   - Supabase has daily automatic backups
   - Consider setting up manual exports for critical data

---

## Support

If you encounter issues:

1. Check Render logs: https://dashboard.render.com
2. Check Vercel logs: https://vercel.com/dashboard
3. Check Supabase logs: https://supabase.com/dashboard
4. Review the README.md for application-specific details

---

## Summary Checklist

- [ ] Got Supabase Service Role Key
- [ ] Created Render account and connected GitHub
- [ ] Deployed backend to Render with correct environment variables
- [ ] Copied backend URL from Render
- [ ] Created Vercel account and connected GitHub
- [ ] Deployed frontend to Vercel with correct environment variables (including backend URL)
- [ ] Updated CORS settings in Render to include Vercel domain
- [ ] Verified backend health check works
- [ ] Verified frontend loads and connects to backend
- [ ] Tested stock data loading
- [ ] Set up auto-deployment (already configured)

**Congratulations! Your UDTS Stock Analyzer is now live!** 🎉
