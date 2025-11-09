# 🚀 Deployment Guide for Other Laptop

## Prerequisites (on your other laptop):
1. Install AWS CLI: `pip install awscli`
2. Configure AWS: `aws configure` (use Mumbai region: ap-south-1)
3. Install Git

## Step 1: Clone and Deploy Backend
```bash
# Clone the repository
git clone https://github.com/guru-dev-labs/personal-zerodha-v1-backend.git
cd personal-zerodha-v1-backend

# Deploy to Railway (recommended)
# Go to https://railway.app and deploy from GitHub
```

## Step 2: Railway Deployment
1. Connect GitHub repo
2. Add environment variables:
   - ENVIRONMENT=production
   - APP_HOST=api.rupiya.life
   - KITE_API_KEY=88mnhtfg26ldg5cd
   - KITE_API_SECRET=x0q0jr6kprcxmbukd8imx5jocn3igori
   - SUPABASE_URL=https://emjshqjjxstzhsipzefi.supabase.co
   - SUPABASE_KEY=[your-key]
   - DEBUG=False

3. Add Redis database in Railway
4. Set custom domain: api.rupiya.life

## Step 3: Deploy Frontend (Vite)
```bash
# On your other laptop
git clone [your-frontend-repo]
cd [frontend-directory]

# Deploy to Vercel
npm install -g vercel
vercel --prod

# Set custom domain: rupiya.life
```

## Step 4: Update Frontend API Calls
In your frontend code, change API base URL to:
```javascript
const API_BASE = 'https://api.rupiya.life';
```

## Testing
- Backend: https://api.rupiya.life/docs
- Frontend: https://rupiya.life