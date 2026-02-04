"""
Test script for security and configuration management
"""
import os
import tempfile
import shutil
from datetime import datetime

from security.encryption import EncryptionService
from security.security_manager import SecurityManager
from security.config_manager import ConfigManager
from security.integration import SecureConfigurationService


def test_encryption_service():
    """Test encryption service functionality"""
    print("Testing Encryption Service...")
    
    encryption = EncryptionService()
    
    # Test string encryption
    test_data = "sk-test-api-key-12345"
    encrypted = encryption.encrypt(test_data)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == test_data, "String encryption/decryption failed"
    print("✓ String encryption/decryption works")
    
    # Test dictionary encryption
    test_dict = {"api_key": "secret", "config": {"value": 123}}
    encrypted_dict = encryption.encrypt_dict(test_dict)
    decrypted_dict = encryption.decrypt_dict(encrypted_dict)
    
    assert decrypted_dict == test_dict, "Dictionary encryption/decryption failed"
    print("✓ Dictionary encryption/decryption works")
    
    # Test password hashing
    password = "test_password"
    hashed, salt = encryption.hash_password(password)
    is_valid = encryption.verify_password(password, hashed, salt)
    
    assert is_valid, "Password hashing/verification failed"
    print("✓ Password hashing/verification works")


def test_security_manager():
    """Test security manager functionality"""
    print("\nTesting Security Manager...")
    
    security = SecurityManager()
    
    # Test API key encryption
    api_key = "sk-test-key-12345"
    encrypted_key = security.encrypt_api_key(api_key, "test_key")
    decrypted_key = security.decrypt_api_key(encrypted_key, "test_key")
    
    assert decrypted_key == api_key, "API key encryption failed"
    print("✓ API key encryption/decryption works")
    
    # Test access permission (should allow normal access)
    ip = "192.168.1.100"
    user_agent = "Mozilla/5.0 (compatible; test)"
    endpoint = "/api/trading"
    
    access_granted = security.verify_access_permission(ip, user_agent, endpoint)
    assert access_granted, "Normal access should be granted"
    print("✓ Access permission verification works")
    
    # Test suspicious activity detection
    suspicious_agent = "hacker-bot/1.0"
    suspicious_access = security.verify_access_permission(ip, suspicious_agent, endpoint)
    assert not suspicious_access, "Suspicious access should be blocked"
    print("✓ Suspicious activity detection works")


def test_config_manager():
    """Test configuration manager functionality"""
    print("\nTesting Configuration Manager...")
    
    # Use temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = os.path.join(temp_dir, "config")
        backup_dir = os.path.join(temp_dir, "backups")
        
        config_manager = ConfigManager(config_dir, backup_dir)
        
        # Test configuration update
        test_config = {
            "database": {
                "postgres_host": "localhost",
                "postgres_port": 5432,
                "postgres_db": "test_db",
                "influxdb_url": "http://localhost:8086"
            },
            "trading": {
                "max_position_size": 0.1,
                "max_daily_loss": 0.05,
                "min_confidence_threshold": 0.7
            },
            "api": {
                "ai_temperature": 0.3,
                "ai_max_tokens": 1000,
                "binance_testnet": True
            }
        }
        
        success = config_manager.update_configuration(test_config)
        assert success, "Configuration update failed"
        print("✓ Configuration update works")
        
        # Test configuration retrieval
        retrieved_config = config_manager.get_configuration("trading")
        assert retrieved_config == test_config["trading"], "Configuration retrieval failed"
        print("✓ Configuration retrieval works")
        
        # Test backup creation
        backup_id = config_manager.create_backup("Test backup")
        assert backup_id is not None, "Backup creation failed"
        print("✓ Configuration backup works")
        
        # Test backup listing
        backups = config_manager.list_backups()
        assert len(backups) > 0, "Backup listing failed"
        print("✓ Backup listing works")
        
        # Test configuration validation
        invalid_config = {
            "trading": {
                "max_position_size": 2.0  # Invalid: should be <= 1.0
            }
        }
        
        is_valid, errors = config_manager.validate_configuration(invalid_config)
        assert not is_valid, "Invalid configuration should fail validation"
        assert len(errors) > 0, "Validation should return errors"
        print("✓ Configuration validation works")


def test_integration_service():
    """Test the integrated security configuration service"""
    print("\nTesting Integration Service...")
    
    # Create a new service instance for testing
    service = SecureConfigurationService()
    
    # Test secure API key storage
    test_key = "sk-test-integration-key"
    success = service.store_secure_api_key("test_integration_key", test_key)
    assert success, "Secure API key storage failed"
    print("✓ Secure API key storage works")
    
    # Test secure API key retrieval
    retrieved_key = service.get_secure_api_key("test_integration_key")
    assert retrieved_key == test_key, "Secure API key retrieval failed"
    print("✓ Secure API key retrieval works")
    
    # Test access validation
    access_granted = service.validate_request_access(
        "192.168.1.100", 
        "Mozilla/5.0 (compatible; test)", 
        "/api/portfolio"
    )
    assert access_granted, "Normal request should be granted access"
    print("✓ Request access validation works")
    
    # Test security status
    status = service.get_security_status()
    assert "system_status" in status, "Security status should include system status"
    assert "access_statistics" in status, "Security status should include access statistics"
    print("✓ Security status reporting works")


def main():
    """Run all tests"""
    print("Running Security and Configuration Management Tests")
    print("=" * 60)
    
    try:
        test_encryption_service()
        test_security_manager()
        test_config_manager()
        test_integration_service()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Security and Configuration Management is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()