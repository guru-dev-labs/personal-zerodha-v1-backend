# 🔐 Security Checklist

## Pre-Commit Checks

- [ ] No `.env` files committed
- [ ] No `*.pem`, `*.key`, `*.p12` files committed
- [ ] No AWS credentials in code
- [ ] No API keys hardcoded
- [ ] No database passwords in code

## Environment Setup

- [ ] `.env` file created from `.env.example`
- [ ] All required environment variables set
- [ ] Virtual environment activated
- [ ] Dependencies installed with `pip install -r requirements.txt`

## API Keys & Secrets

- [ ] Zerodha API key and secret obtained
- [ ] Supabase URL and key configured
- [ ] Redis password set (if required)
- [ ] JWT secret key generated (for future auth)

## AWS Security (for deployment)

- [ ] IAM user created with minimal permissions
- [ ] Access keys generated and stored securely
- [ ] EC2 key pair created and downloaded
- [ ] Security groups configured properly
- [ ] SSL certificate obtained (for HTTPS)

## Git Security

- [ ] Sensitive files added to `.gitignore`
- [ ] Git history cleaned of sensitive data
- [ ] Repository set to private
- [ ] Branch protection enabled

## Application Security

- [ ] CORS configured properly
- [ ] Rate limiting implemented
- [ ] Input validation in place
- [ ] Error messages don't leak sensitive info
- [ ] Logging doesn't expose secrets

## Database Security

- [ ] Supabase RLS (Row Level Security) enabled
- [ ] Database credentials not in code
- [ ] Redis protected with password
- [ ] Backup strategy in place

## Monitoring & Alerts

- [ ] Error logging configured
- [ ] Health check endpoints working
- [ ] Monitoring dashboard set up
- [ ] Alert system for failures

## Regular Maintenance

- [ ] Rotate API keys quarterly
- [ ] Update dependencies regularly
- [ ] Review access logs monthly
- [ ] Security audit biannually
