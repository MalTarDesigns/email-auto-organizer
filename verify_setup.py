#!/usr/bin/env python3
"""
Verification script to check Phase 1 setup completion
"""
import os
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists


def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists"""
    exists = Path(dirpath).is_dir()
    status = "✓" if exists else "✗"
    print(f"{status} {dirpath}/")
    return exists


def main():
    print("Phase 1 Setup Verification")
    print("=" * 60)

    all_checks = []

    print("\n📁 Directory Structure:")
    directories = [
        "backend/app/api",
        "backend/app/core",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/workers",
        "backend/alembic/versions",
        "backend/tests",
        "frontend/app",
        "frontend/components",
        "frontend/lib",
        "frontend/types",
        "frontend/public"
    ]

    for directory in directories:
        all_checks.append(check_directory_exists(directory))

    print("\n📄 Backend Configuration Files:")
    backend_files = [
        "backend/app/core/config.py",
        "backend/app/core/database.py",
        "backend/app/core/redis_client.py",
        "backend/app/main.py",
        "backend/app/workers/celery_app.py",
        "backend/app/workers/tasks.py",
        "backend/requirements.txt",
        "backend/Dockerfile",
        "backend/alembic.ini",
        "backend/alembic/env.py",
        "backend/alembic/script.py.mako",
        "backend/alembic/versions/001_initial_schema.py",
        "backend/schema.sql"
    ]

    for file in backend_files:
        all_checks.append(check_file_exists(file))

    print("\n📄 Frontend Configuration Files:")
    frontend_files = [
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/next.config.js",
        "frontend/tailwind.config.ts",
        "frontend/postcss.config.js",
        "frontend/.eslintrc.json",
        "frontend/app/layout.tsx",
        "frontend/app/page.tsx",
        "frontend/app/globals.css",
        "frontend/Dockerfile"
    ]

    for file in frontend_files:
        all_checks.append(check_file_exists(file))

    print("\n📄 Project Files:")
    project_files = [
        "docker-compose.yml",
        ".env.example",
        ".gitignore",
        "README.md"
    ]

    for file in project_files:
        all_checks.append(check_file_exists(file))

    print("\n" + "=" * 60)

    total = len(all_checks)
    passed = sum(all_checks)

    if passed == total:
        print(f"✅ All checks passed! ({passed}/{total})")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and fill in your credentials")
        print("2. Run: docker-compose up --build")
        print("3. Run migrations: docker-compose exec backend alembic upgrade head")
        return 0
    else:
        print(f"❌ Some checks failed ({passed}/{total})")
        return 1


if __name__ == "__main__":
    exit(main())
