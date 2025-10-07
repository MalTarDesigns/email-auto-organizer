"""
Test script for Phase 2 implementation

This script helps verify that all Phase 2 components are working correctly.
Run this after setting up the environment and starting all services.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, engine
from app.models import User, Email, EmailClassification
from app.core.config import settings
from sqlalchemy import inspect


def test_database_connection():
    """Test database connection and tables"""
    print("🔍 Testing database connection...")

    try:
        db = SessionLocal()

        # Test connection
        db.execute("SELECT 1")
        print("✅ Database connection successful")

        # Check if tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        required_tables = ['users', 'emails', 'email_classifications']
        for table in required_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing - run migrations!")
                return False

        db.close()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def test_models():
    """Test SQLAlchemy models"""
    print("\n🔍 Testing SQLAlchemy models...")

    try:
        # Test User model
        user_attrs = ['id', 'email', 'google_id', 'access_token', 'refresh_token']
        for attr in user_attrs:
            if hasattr(User, attr):
                print(f"✅ User.{attr} exists")
            else:
                print(f"❌ User.{attr} missing")

        # Test Email model
        email_attrs = ['id', 'user_id', 'message_id', 'subject', 'body_text']
        for attr in email_attrs:
            if hasattr(Email, attr):
                print(f"✅ Email.{attr} exists")
            else:
                print(f"❌ Email.{attr} missing")

        # Test EmailClassification model
        classification_attrs = ['id', 'email_id', 'category', 'priority']
        for attr in classification_attrs:
            if hasattr(EmailClassification, attr):
                print(f"✅ EmailClassification.{attr} exists")
            else:
                print(f"❌ EmailClassification.{attr} missing")

        return True

    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        return False


def test_config():
    """Test configuration settings"""
    print("\n🔍 Testing configuration...")

    required_settings = [
        'DATABASE_URL',
        'REDIS_URL',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'GOOGLE_REDIRECT_URI',
        'SECRET_KEY'
    ]

    all_present = True
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if value and value != "":
            print(f"✅ {setting} is set")
        else:
            print(f"❌ {setting} is missing or empty")
            all_present = False

    return all_present


def test_imports():
    """Test if all components can be imported"""
    print("\n🔍 Testing imports...")

    try:
        # Test API imports
        from app.api.v1.auth import router as auth_router
        print("✅ Auth router imported successfully")

        # Test service imports
        from app.services.email_service import EmailService
        print("✅ EmailService imported successfully")

        # Test worker imports
        from app.workers.email_processor import process_email
        from app.workers.sync_worker import fetch_new_emails
        print("✅ Worker tasks imported successfully")

        # Test celery app
        from app.celery_app import celery_app
        print("✅ Celery app imported successfully")

        # Test schemas
        from app.schemas import User, Email, AuthResponse
        print("✅ Schemas imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False


def test_celery_connection():
    """Test Celery/Redis connection"""
    print("\n🔍 Testing Celery/Redis connection...")

    try:
        from app.celery_app import celery_app

        # Ping Redis
        result = celery_app.control.inspect().ping()
        if result:
            print(f"✅ Celery workers active: {list(result.keys())}")
            return True
        else:
            print("⚠️  No Celery workers found - make sure worker is running")
            return False

    except Exception as e:
        print(f"❌ Celery connection failed: {str(e)}")
        print("   Make sure Redis is running and Celery worker is started")
        return False


def test_api_endpoints():
    """Test if API endpoints are accessible"""
    print("\n🔍 Testing API endpoints...")

    try:
        import httpx

        base_url = "http://localhost:8000"

        # Test health endpoint
        response = httpx.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False

        # Test OAuth login endpoint
        response = httpx.get(f"{base_url}/api/v1/auth/google/login")
        if response.status_code == 200:
            data = response.json()
            if 'authorization_url' in data and 'state' in data:
                print("✅ OAuth login endpoint working")
                print(f"   Authorization URL: {data['authorization_url'][:60]}...")
            else:
                print("❌ OAuth response missing required fields")
                return False
        else:
            print(f"❌ OAuth endpoint failed: {response.status_code}")
            return False

        return True

    except httpx.ConnectError:
        print("❌ Cannot connect to API - make sure FastAPI server is running")
        return False
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 2 Implementation Test Suite")
    print("=" * 60)

    results = {
        "Configuration": test_config(),
        "Imports": test_imports(),
        "Database Connection": test_database_connection(),
        "Models": test_models(),
        "Celery/Redis": test_celery_connection(),
        "API Endpoints": test_api_endpoints(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("🎉 All tests passed! Phase 2 is ready to use.")
        print("\n📝 Next steps:")
        print("1. Visit http://localhost:8000/api/v1/auth/google/login")
        print("2. Complete OAuth flow to authenticate")
        print("3. Wait for automatic email sync (every 5 minutes)")
        print("4. Or manually trigger: fetch_new_emails.delay(user_id)")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Common fixes:")
        print("1. Make sure .env file is configured")
        print("2. Run database migrations: alembic upgrade head")
        print("3. Start FastAPI: uvicorn app.main:app --reload")
        print("4. Start Redis: redis-server")
        print("5. Start Celery worker: celery -A app.celery_app worker --loglevel=info")
        print("6. Start Celery beat: celery -A app.celery_app beat --loglevel=info")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
