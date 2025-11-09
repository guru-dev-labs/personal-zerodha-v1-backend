#!/usr/bin/env python3
"""
Configuration Demo Script

This script demonstrates how the environment-based configuration works
for different deployment environments.
"""

import os
from app.config import Settings

def demo_environment_config():
    """Demonstrate different environment configurations"""

    print("🚀 Personal Zerodha Backend - Environment Configuration Demo")
    print("=" * 60)

    # Development Environment
    print("\n🏠 DEVELOPMENT ENVIRONMENT:")
    print("-" * 30)

    dev_settings = Settings(
        ENVIRONMENT="development",
        APP_HOST="127.0.0.1",
        APP_PORT=8000,
        KITE_API_KEY="dev_key",
        KITE_API_SECRET="dev_secret",
        SUPABASE_URL="https://dev.supabase.co",
        SUPABASE_KEY="dev_key"
    )

    print(f"Environment: {dev_settings.ENVIRONMENT}")
    print(f"Base URL: {dev_settings.base_url}")
    print(f"Redirect URL: {dev_settings.get_redirect_url()}")
    print(f"Redis URL: {dev_settings.REDIS_URL}")
    print(f"Is Development: {dev_settings.is_development}")
    print(f"Is Production: {dev_settings.is_production}")

    # Staging Environment
    print("\n🧪 STAGING ENVIRONMENT:")
    print("-" * 30)

    staging_settings = Settings(
        ENVIRONMENT="staging",
        APP_HOST="staging-api.yourapp.com",
        APP_PORT=80,
        KITE_API_KEY="staging_key",
        KITE_API_SECRET="staging_secret",
        SUPABASE_URL="https://staging.supabase.co",
        SUPABASE_KEY="staging_key"
    )

    print(f"Environment: {staging_settings.ENVIRONMENT}")
    print(f"Base URL: {staging_settings.base_url}")
    print(f"Redirect URL: {staging_settings.get_redirect_url()}")
    print(f"Redis URL: {staging_settings.REDIS_URL}")
    print(f"Is Development: {staging_settings.is_development}")
    print(f"Is Production: {staging_settings.is_production}")

    # Production Environment
    print("\n🏭 PRODUCTION ENVIRONMENT:")
    print("-" * 30)

    prod_settings = Settings(
        ENVIRONMENT="production",
        APP_HOST="api.yourapp.com",  # Use your actual production domain
        APP_PORT=443,
        KITE_API_KEY="prod_key",
        KITE_API_SECRET="prod_secret",
        SUPABASE_URL="https://prod.supabase.co",
        SUPABASE_KEY="prod_key",
        REDIS_HOST="redis.production.host",
        REDIS_PASSWORD="secure_password"
    )

    print(f"Environment: {prod_settings.ENVIRONMENT}")
    print(f"Base URL: {prod_settings.base_url}")
    print(f"Redirect URL: {prod_settings.get_redirect_url()}")
    print(f"Redis URL: {prod_settings.REDIS_URL}")
    print(f"Is Development: {prod_settings.is_development}")
    print(f"Is Production: {prod_settings.is_production}")

    # Custom Redis URL Example
    print("\n🔧 CUSTOM REDIS URL EXAMPLE:")
    print("-" * 30)

    custom_settings = Settings(
        ENVIRONMENT="production",
        APP_HOST="yourapp.com",
        APP_PORT=443,
        KITE_API_KEY="prod_key",
        KITE_API_SECRET="prod_secret",
        SUPABASE_URL="https://prod.supabase.co",
        SUPABASE_KEY="prod_key",
        REDIS_URL="redis://user:pass@redis-cluster.amazonaws.com:6379/0"
    )

    print(f"Environment: {custom_settings.ENVIRONMENT}")
    print(f"Redis URL: {custom_settings.REDIS_URL} (custom)")

    print("\n✅ Configuration is now environment-aware!")
    print("No more hardcoded localhost addresses!")

if __name__ == "__main__":
    demo_environment_config()