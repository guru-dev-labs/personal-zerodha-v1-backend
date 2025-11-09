# 🚀 AWS Mumbai Deployment Guide

## Overview
Deploy your Zerodha trading backend to AWS Mumbai region for Indian data residency compliance.

## 🏗️ Architecture
- **Region**: Mumbai (ap-south-1)
- **EC2 Instance**: t3.micro (free tier eligible)
- **Redis**: Local Redis on EC2
- **Frontend**: Vercel (global CDN)

## 📋 Prerequisites

1. **AWS Account** with Mumbai region access
2. **AWS CLI** installed and configured
3. **EC2 Key Pair** created in Mumbai region
4. **Domain**: rupiya.life configured

## 🚀 Quick Deployment (Automated)

### Step 1: Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key, Secret Key, and set region to ap-south-1
```

### Step 2: Make Scripts Executable
```bash
chmod +x deploy-aws.sh ec2-userdata.sh
```

### Step 3: Deploy
```bash
./deploy-aws.sh
```

### Step 4: Get Your Instance IP
The script will output your instance's public IP address.

## 🔧 Manual Deployment

### Step 1: Launch EC2 Instance
1. Go to AWS Console → EC2 → Launch Instance
2. **AMI**: Amazon Linux 2 (HVM)
3. **Instance Type**: t3.micro
4. **Region**: Asia Pacific (Mumbai)
5. **Security Group**: Allow SSH (22), HTTP (80), HTTPS (443)
6. **Key Pair**: Create/select your key pair
7. **User Data**: Copy contents of `ec2-userdata.sh`

### Step 2: Configure Domain
Update your DNS to point `rupiya.life` to the EC2 public IP.

## 📊 Cost Estimate (Mumbai Region)

| Service | Cost/Month | Free Tier |
|---------|------------|-----------|
| EC2 t3.micro | ₹400 | 750 hours |
| EBS Storage | ₹50 | 30GB free |
| Data Transfer | ₹100 | 15GB free |
| **Total** | **₹550** | **~3 months free** |

## 🔒 Security Features

- ✅ **Indian Data Center** (Mumbai)
- ✅ **Security Groups** configured
- ✅ **Auto-scaling ready**
- ✅ **SSL ready** (add certificate later)

## 📈 Monitoring

```bash
# SSH into your instance
ssh -i your-key.pem ec2-user@YOUR_PUBLIC_IP

# Check app status
sudo docker ps
sudo docker logs zerodha-app

# Check Redis
redis-cli ping
```

## 🔄 Updates

```bash
# SSH into instance
cd /home/ec2-user/app

# Pull latest changes
git pull origin feature/database-setup

# Rebuild and restart
sudo docker build -t zerodha-app .
sudo docker stop zerodha-app
sudo docker run -d --name zerodha-app -p 80:8000 --restart unless-stopped --env-file .env zerodha-app
```

## 🌐 Frontend Deployment

Keep your Vite frontend on Vercel:
1. Deploy to Vercel as usual
2. Point `rupiya.life` to Vercel
3. Update API calls to use the EC2 instance IP or domain

## 🆘 Troubleshooting

### App Not Starting
```bash
# Check logs
sudo docker logs zerodha-app

# Check if Redis is running
sudo systemctl status redis

# Check environment variables
cat /home/ec2-user/app/.env
```

### Connection Issues
- Verify security groups allow ports 80/443
- Check if instance is running in Mumbai region
- Verify domain DNS propagation

## 📞 Support

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Free Tier Limits**: https://aws.amazon.com/free/
- **Mumbai Region**: ap-south-1

---

**🎉 Your trading app will be live at `https://rupiya.life` with Indian data residency!**