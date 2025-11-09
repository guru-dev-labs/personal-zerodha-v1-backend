#!/bin/bash
# AWS EC2 Deployment Script for Mumbai Region
# Run this on your local machine after setting up AWS CLI

set -e

# Configuration
REGION="ap-south-1"
INSTANCE_TYPE="t3.micro"
AMI_ID="ami-0f5ee92e2d63afc18"  # Amazon Linux 2 in Mumbai
KEY_NAME="zerodha-trading-key"
SECURITY_GROUP_NAME="zerodha-sg"
INSTANCE_NAME="zerodha-backend"

echo "🚀 Deploying to AWS Mumbai Region..."

# Create security group
echo "Creating security group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for Zerodha trading app" \
    --region $REGION \
    --output text \
    --query 'GroupId')

# Add inbound rules
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $REGION

echo "Security group created: $SG_ID"

# Launch EC2 instance
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $REGION \
    --user-data file://ec2-userdata.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --output text \
    --query 'Instances[0].InstanceId')

echo "Instance launched: $INSTANCE_ID"

# Wait for instance to be running
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --output text \
    --query 'Reservations[0].Instances[0].PublicIpAddress')

echo "✅ Deployment complete!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "Next steps:"
echo "1. Update your domain DNS to point to: $PUBLIC_IP"
echo "2. SSH into instance: ssh -i your-key.pem ec2-user@$PUBLIC_IP"
echo "3. Check logs: sudo docker logs zerodha-app"