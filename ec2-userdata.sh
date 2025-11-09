#!/bin/bash
# EC2 User Data Script - Runs on instance startup
# Installs Docker, Redis, and deploys the FastAPI app

set -e

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
yum install -y git

# Create app directory
mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

# Clone repository (replace with your actual repo)
git clone https://github.com/guru-dev-labs/personal-zerodha-v1-backend.git .
git checkout feature/database-setup

# Create .env file with production settings
cat > .env << EOF
# Environment Configuration
ENVIRONMENT=production
APP_HOST=api.rupiya.life
APP_PORT=443

# Redis Configuration (local Redis on EC2)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Zerodha Configuration
KITE_API_KEY=88mnhtfg26ldg5cd
KITE_API_SECRET=x0q0jr6kprcxmbukd8imx5jocn3igori

# Supabase Configuration
SUPABASE_URL=https://emjshqjjxstzhsipzefi.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtanNocWpqeHN0emhzaXB6ZWZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1MDU5NzksImV4cCI6MjA3ODA4MTk3OX0.mELcn7hcy5tGByG_VQzS5faxEorL4ZzEVNzU_3LP2PQ

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
EOF

# Install Redis
yum install -y redis
systemctl start redis
systemctl enable redis

# Build and run the application
docker build -t zerodha-app .
docker run -d \
  --name zerodha-app \
  -p 80:8000 \
  --restart unless-stopped \
  --env-file .env \
  zerodha-app

# Install nginx for SSL termination (optional)
yum install -y nginx
systemctl start nginx
systemctl enable nginx

# Create nginx config for the app
cat > /etc/nginx/conf.d/zerodha.conf << EOF
server {
    listen 80;
    server_name api.rupiya.life;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Restart nginx
systemctl restart nginx

echo "✅ AWS deployment complete!"
echo "App running at: http://localhost:8000"
echo "Nginx proxy at: http://rupiya.life (after DNS update)"