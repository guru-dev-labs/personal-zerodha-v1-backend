# 🚀 AWS Deployment Guide (Mumbai Region)

## Prerequisites (on your other laptop):
1. Install AWS CLI: `pip install awscli`
2. Configure AWS: `aws configure` (use Mumbai region: ap-south-1)
3. Install Git
4. Create EC2 key pair in AWS Console

## Step 1: Clone Repository
```bash
git clone https://github.com/guru-dev-labs/personal-zerodha-v1-backend.git
cd personal-zerodha-v1-backend
```

## Step 2: AWS Deployment
```bash
# Make scripts executable
chmod +x deploy-aws.sh ec2-userdata.sh

# Run deployment (creates EC2 instance in Mumbai)
./deploy-aws.sh
```

## Step 3: Configure Domain
1. Get the public IP from deployment output
2. Update DNS: Point `api.rupiya.life` to the EC2 public IP
3. Wait for DNS propagation (~5-10 minutes)

## Step 4: Verify Deployment
```bash
# Test the API
curl https://api.rupiya.life/

# Check API documentation
open https://api.rupiya.life/docs
```

## Step 5: Deploy Frontend (Vercel)
```bash
# On your other laptop or any machine
git clone [your-frontend-repo]
cd [frontend-directory]

# Deploy to Vercel
npm install -g vercel
vercel --prod

# Set custom domain: rupiya.life
```

## Step 6: Update Frontend API Calls
In your frontend code, change API base URL to:
```javascript
const API_BASE = 'https://api.rupiya.life';
```

## Environment Variables (Auto-configured)
The deployment script automatically sets up:
- ENVIRONMENT=production
- APP_HOST=api.rupiya.life
- APP_PORT=443
- Redis (local on EC2)
- Zerodha API credentials
- Supabase configuration

## Monitoring & Maintenance
```bash
# SSH into your instance
ssh -i zerodha-key.pem ec2-user@api.rupiya.life

# Check app status
sudo docker ps
sudo docker logs zerodha-app

# Check Redis
redis-cli ping

# Restart services
sudo systemctl restart docker
```

## Cost Estimate (Mumbai Region)
- EC2 t3.micro: ₹400/month
- EBS Storage: ₹50/month
- Data Transfer: ₹100/month
- **Total: ₹550/month** (first 3 months free with AWS credits)

## Troubleshooting
- **Can't access API?** Check security groups allow ports 80/443
- **App not starting?** Check Docker logs: `sudo docker logs zerodha-app`
- **DNS not working?** Wait 10-15 minutes for propagation

---
**Deploy from your other laptop (not behind firewall) for best results!**