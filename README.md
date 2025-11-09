# Personal Zerodha Backend

A sophisticated algorithmic trading backend built with Python, FastAPI, and Zerodha Kite API. Features real-time market scanning, automated trading signals, and comprehensive risk management.

## 🚨 Security Notice

**This repository contains sensitive configuration. Never commit actual secrets to version control.**

### What Was Fixed

- ✅ Removed `.env` files containing API keys from Git history
- ✅ Removed private key files (`.pem`) from repository
- ✅ Updated `.gitignore` to prevent future exposure
- ✅ Added comprehensive `.env.example` template

### If You Cloned This Repo

If you cloned this repository and see sensitive files, **delete them immediately** and regenerate new credentials.

## 🛠️ Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/guru-dev-labs/personal-zerodha-v1-backend.git
cd personal-zerodha-v1-backend
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your actual values
nano .env
```

**Required Environment Variables:**

- `KITE_API_KEY` - From Zerodha Kite Connect
- `KITE_API_SECRET` - From Zerodha Kite Connect
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key

### 4. Set Up Zerodha API

1. Go to [Zerodha Kite Connect](https://kite.zerodha.com/connect/login)
2. Create a new app or use existing one
3. Copy API Key and Secret to `.env`
4. Set redirect URL to: `http://localhost:8000/auth/callback`

### 5. Run Application

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Authentication

- `GET /auth/login` - Get Zerodha login URL
- `GET /auth/callback` - Handle OAuth callback

### Trading Data

- `GET /profile` - User profile
- `GET /holdings` - Portfolio holdings

### Short Sell Scanner

- `GET /short-sell/alerts` - Active short sell opportunities
- `GET /short-sell/alerts/{instrument_token}` - Specific instrument alert
- `POST /short-sell/scan` - Manual scan trigger

## 🚀 Deployment

### AWS Deployment

```bash
# Configure AWS CLI
aws configure

# Make scripts executable
chmod +x deploy-aws.sh ec2-userdata.sh

# Deploy
./deploy-aws.sh
```

### Environment Setup for Production

```bash
# Update .env for production
ENVIRONMENT=production
APP_HOST=your-domain.com
APP_PORT=443
DEBUG=False
```

## 🔐 Security Best Practices

### Never Commit These Files:

- `.env` (use `.env.example` as template)
- `*.pem`, `*.key` (private keys)
- `*.p12`, `*.pfx` (certificates)
- AWS credentials files

### Environment Variables:

- Use strong, unique secrets
- Rotate API keys regularly
- Use different keys for dev/staging/prod

### AWS Security:

- Use IAM roles instead of access keys
- Enable MFA on AWS account
- Regularly rotate access keys

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Zerodha API   │
│   (React/Vue)   │◄──►│   Backend       │◄──►│   (Kite)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Supabase DB   │
                       └─────────────────┘
```

## 📊 Features

- ✅ **Real-time Market Scanning** - Nifty 500 stocks, custom conditions
- ✅ **Short Sell Alerts** - Automated opportunity detection
- ✅ **Risk Management** - Position sizing, stop losses
- ✅ **Portfolio Tracking** - Holdings, P&L, performance
- ✅ **Caching Layer** - Redis for fast data access
- ✅ **Background Tasks** - Continuous scanning during market hours

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📝 Development

### Code Structure

```
app/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── zerodha_client.py    # Zerodha API client
├── short_sell_scanner.py # Market scanner
├── database.py          # DB connections
└── config.py            # Settings
```

### Adding New Features

1. Create feature branch
2. Add tests
3. Update documentation
4. Create PR

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit PR

## 📄 License

Private - All rights reserved

## ⚠️ Disclaimer

This software is for educational purposes only. Trading involves risk. Past performance doesn't guarantee future results. Always do your own research and never risk more than you can afford to lose.
