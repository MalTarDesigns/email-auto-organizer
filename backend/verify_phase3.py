"""
Phase 3 Verification Script

This script verifies that all Phase 3 AI Triage Engine components
are properly installed and configured.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))


def verify_imports():
    """Verify all service imports"""
    print("\n1. Verifying Service Imports...")

    try:
        from app.services import (
            TriageService,
            PriorityEngine,
            EmbeddingService,
            ConfidenceService,
            CompleteTriageService
        )
        print("   ✓ All services imported successfully")
        return True
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False


def verify_models():
    """Verify model structure"""
    print("\n2. Verifying Model Structure...")

    try:
        from app.models.email import Email
        from app.models.user import User
        from app.models.email_classification import EmailClassification

        # Check Email model
        assert hasattr(Email, 'embedding'), "Email missing embedding field"
        assert hasattr(Email, 'subject'), "Email missing subject field"
        assert hasattr(Email, 'body_text'), "Email missing body_text field"
        assert hasattr(Email, 'sender_email'), "Email missing sender_email field"

        # Check User model
        assert hasattr(User, 'preferences'), "User missing preferences field"
        assert hasattr(User, 'email'), "User missing email field"

        # Check EmailClassification model
        assert hasattr(EmailClassification, 'category'), "EmailClassification missing category"
        assert hasattr(EmailClassification, 'confidence_score'), "EmailClassification missing confidence_score"

        print("   ✓ Models have all required fields")
        return True
    except AssertionError as e:
        print(f"   ✗ Model verification error: {e}")
        return False
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False


def verify_openai():
    """Verify OpenAI configuration"""
    print("\n3. Verifying OpenAI Configuration...")

    try:
        from app.core.config import settings
        from openai import OpenAI

        # Check if API key is set
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            print("   ✗ OPENAI_API_KEY not set in environment")
            return False

        # Try to initialize client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        print("   ✓ OpenAI client initialized")
        print(f"   ✓ Using model: {settings.OPENAI_MODEL}")
        return True
    except Exception as e:
        print(f"   ✗ OpenAI verification error: {e}")
        return False


def verify_database_config():
    """Verify database configuration"""
    print("\n4. Verifying Database Configuration...")

    try:
        from app.core.config import settings
        from app.core.database import engine, SessionLocal

        # Check if DATABASE_URL is set
        if not settings.DATABASE_URL:
            print("   ✗ DATABASE_URL not set in environment")
            return False

        print("   ✓ Database URL configured")

        # Try to create session
        db = SessionLocal()
        db.close()

        print("   ✓ Database session created successfully")
        return True
    except Exception as e:
        print(f"   ✗ Database configuration error: {e}")
        return False


def verify_service_functionality():
    """Test basic service functionality"""
    print("\n5. Testing Service Functionality...")

    try:
        from app.services import PriorityEngine, ConfidenceService

        # Test PriorityEngine
        preferences = {
            'whitelist_senders': ['test@example.com'],
            'blacklist_senders': [],
            'priority_rules': []
        }

        engine = PriorityEngine(preferences)
        email = {
            'subject': 'Test',
            'sender_email': 'test@example.com',
            'body': 'Test email'
        }

        classification = {
            'category': 'other',
            'priority': 'medium',
            'urgency_score': 0.5,
            'sentiment': 'neutral',
            'requires_action': False,
            'reasoning': 'Test'
        }

        result = engine.apply_custom_rules(email, classification)
        assert result['priority'] == 'high', "Whitelist rule not applied"

        print("   ✓ PriorityEngine working correctly")

        # Test ConfidenceService
        confidence_service = ConfidenceService()
        confidence = confidence_service.calculate_confidence(
            ai_classification={'category': 'work'},
            user_rules_applied=True,
            similar_emails=[]
        )

        assert 0.0 <= confidence <= 1.0, "Invalid confidence score"
        print("   ✓ ConfidenceService working correctly")

        return True
    except Exception as e:
        print(f"   ✗ Service functionality test error: {e}")
        return False


def verify_dependencies():
    """Verify required dependencies"""
    print("\n6. Verifying Dependencies...")

    dependencies = [
        ('openai', '1.10.0'),
        ('pgvector', '0.2.4'),
        ('sqlalchemy', '2.0.25'),
        ('pydantic', '2.5.3'),
    ]

    all_ok = True
    for package, min_version in dependencies:
        try:
            import importlib.metadata
            version = importlib.metadata.version(package)
            print(f"   ✓ {package} {version} installed")
        except Exception as e:
            print(f"   ✗ {package} not found or error: {e}")
            all_ok = False

    return all_ok


def print_summary(results):
    """Print verification summary"""
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    tests = [
        "Service Imports",
        "Model Structure",
        "OpenAI Configuration",
        "Database Configuration",
        "Service Functionality",
        "Dependencies"
    ]

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i}. {test}: {status}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All verifications passed! Phase 3 is ready to use.")
        print("\nNext steps:")
        print("1. Apply database migration: alembic upgrade head")
        print("2. Run example: python examples/triage_usage_example.py")
        print("3. Run tests: pytest tests/services/ -v")
    else:
        print("\n✗ Some verifications failed. Please review errors above.")
        print("\nTroubleshooting:")
        print("- Ensure virtual environment is activated")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Set OPENAI_API_KEY in .env file")
        print("- Configure DATABASE_URL in .env file")

    print("=" * 60)


def main():
    """Run all verifications"""
    print("=" * 60)
    print("PHASE 3 AI TRIAGE ENGINE VERIFICATION")
    print("=" * 60)

    results = [
        verify_imports(),
        verify_models(),
        verify_openai(),
        verify_database_config(),
        verify_service_functionality(),
        verify_dependencies()
    ]

    print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
