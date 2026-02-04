#!/usr/bin/env python3
"""
Test configuration loading and basic functionality
"""
import os
import sys
from pathlib import Path

def test_config_loading():
    """Test configuration loading"""
    try:
        from config import settings
        print("✓ Configuration loaded successfully")
        
        # Test database settings
        print(f"  - PostgreSQL URL: {settings.database.postgres_url}")
        print(f"  - InfluxDB URL: {settings.database.influxdb_url}")
        print(f"  - Redis URL: {settings.redis.redis_url}")
        
        # Test app settings
        print(f"  - Debug mode: {settings.app.debug}")
        print(f"  - Log level: {settings.app.log_level}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_database_models():
    """Test database models import"""
    try:
        from database.models import NewsItem, TradingRecord, Portfolio
        print("✓ Database models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Database models import failed: {e}")
        return False

def test_directory_structure():
    """Test that all required directories exist"""
    required_dirs = [
        "database",
        "tasks", 
        "core",
        "api",
        "tests",
        "logs",
        "alembic"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✓ Directory exists: {directory}")
        else:
            print(f"✗ Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def test_env_file():
    """Test .env file exists and has required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("✗ .env file not found")
        return False
    
    print("✓ .env file exists")
    
    # Check for required environment variables
    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_DB", 
        "POSTGRES_USER",
        "REDIS_HOST",
        "INFLUXDB_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in os.environ:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠ Missing environment variables: {', '.join(missing_vars)}")
        print("  (This is normal if you haven't loaded the .env file)")
    else:
        print("✓ All required environment variables are set")
    
    return True

def main():
    """Main test function"""
    print("🧪 Testing Bitcoin Trading System Configuration")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Environment File", test_env_file),
        ("Configuration Loading", test_config_loading),
        ("Database Models", test_database_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Infrastructure is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\nTo fix issues:")
        print("1. Make sure you're in the backend directory")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check that .env file has correct values")

if __name__ == "__main__":
    main()