"""
Integration module for security and configuration management
Integrates with the existing trading system configuration
"""
import os
from typing import Dict, Any, Optional
import logging

from .security_manager import SecurityManager
from .config_manager import ConfigManager
from .encryption import EncryptionService
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import settings

logger = logging.getLogger(__name__)


class SecureConfigurationService:
    """
    Service that integrates security and configuration management
    with the existing trading system
    """
    
    def __init__(self):
        """Initialize the secure configuration service"""
        self.encryption_service = EncryptionService()
        self.security_manager = SecurityManager(self.encryption_service)
        
        # Use relative paths from current working directory
        config_dir = "config"
        backup_dir = "config_backups"
        
        self.config_manager = ConfigManager(
            config_dir=config_dir,
            backup_dir=backup_dir,
            encryption_service=self.encryption_service
        )
        
        # Register configuration change callbacks
        self.config_manager.register_change_callback(self._on_config_change)
        
        # Setup secure storage for sensitive API keys
        self._setup_secure_api_keys()
    
    def get_secure_api_key(self, key_name: str) -> Optional[str]:
        """
        Get a securely stored API key
        
        Args:
            key_name: Name of the API key (e.g., 'binance_api_key', 'openai_api_key')
            
        Returns:
            Decrypted API key or None if not found
        """
        try:
            # First check if we have an encrypted version stored
            encrypted_key = self._get_encrypted_key_from_storage(key_name)
            if encrypted_key:
                return self.security_manager.decrypt_api_key(encrypted_key, key_name)
            
            # Fallback to environment variable or settings
            return self._get_key_from_settings(key_name)
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key '{key_name}': {e}")
            return None
    
    def store_secure_api_key(self, key_name: str, api_key: str) -> bool:
        """
        Store an API key securely
        
        Args:
            key_name: Name of the API key
            api_key: The API key to store
            
        Returns:
            True if storage was successful
        """
        try:
            encrypted_key = self.security_manager.encrypt_api_key(api_key, key_name)
            return self._store_encrypted_key(key_name, encrypted_key)
        except Exception as e:
            logger.error(f"Failed to store API key '{key_name}': {e}")
            return False
    
    def validate_request_access(self, ip_address: str, user_agent: str, endpoint: str) -> bool:
        """
        Validate if a request should be allowed access
        
        Args:
            ip_address: Client IP address
            user_agent: Client user agent
            endpoint: Requested endpoint
            
        Returns:
            True if access should be granted
        """
        # Check basic access permissions
        if not self.security_manager.verify_access_permission(ip_address, user_agent, endpoint):
            return False
        
        # Check for anomalous activity
        if self.security_manager.detect_anomalous_access(ip_address, user_agent, endpoint):
            return False
        
        return True
    
    def update_trading_configuration(self, updates: Dict[str, Any]) -> bool:
        """
        Update trading configuration with validation
        
        Args:
            updates: Configuration updates
            
        Returns:
            True if update was successful
        """
        return self.config_manager.update_configuration(updates, validate=True, create_backup=True)
    
    def get_trading_configuration(self) -> Dict[str, Any]:
        """
        Get current trading configuration
        
        Returns:
            Trading configuration dictionary
        """
        return self.config_manager.get_configuration("trading")
    
    def create_configuration_backup(self, description: str = "") -> str:
        """
        Create a backup of current configuration
        
        Args:
            description: Optional description for the backup
            
        Returns:
            Backup ID
        """
        return self.config_manager.create_backup(description)
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get current security status and statistics
        
        Returns:
            Security status information
        """
        access_stats = self.security_manager.get_access_statistics()
        recent_alerts = self.security_manager.get_security_alerts(since=None)
        
        return {
            "access_statistics": access_stats,
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len([a for a in recent_alerts if a.severity == "CRITICAL"]),
            "blocked_ips": len(self.security_manager.blocked_ips),
            "system_status": "SECURE" if access_stats["success_rate"] > 0.95 else "WARNING"
        }
    
    def _setup_secure_api_keys(self) -> None:
        """Setup secure storage for existing API keys"""
        # List of sensitive API keys that should be encrypted
        sensitive_keys = [
            'binance_api_key',
            'binance_secret_key',
            'openai_api_key',
            'anthropic_api_key',
            'google_api_key',
            'deepseek_api_key',
            'doubao_api_key',
            'twitter_bearer_token',
            'newsapi_key'
        ]
        
        for key_name in sensitive_keys:
            # Check if we already have this key stored securely
            if not self._has_encrypted_key(key_name):
                # Try to get from current settings and store securely
                key_value = self._get_key_from_settings(key_name)
                if key_value and key_value not in ['', 'your-api-key', 'NA']:
                    self.store_secure_api_key(key_name, key_value)
                    logger.info(f"Migrated API key '{key_name}' to secure storage")
    
    def _get_key_from_settings(self, key_name: str) -> Optional[str]:
        """Get API key from current settings"""
        key_mapping = {
            'binance_api_key': settings.api.binance_api_key,
            'binance_secret_key': settings.api.binance_secret_key,
            'openai_api_key': settings.api.openai_api_key,
            'anthropic_api_key': settings.api.anthropic_api_key,
            'google_api_key': settings.api.google_api_key,
            'deepseek_api_key': settings.api.deepseek_api_key,
            'doubao_api_key': settings.api.doubao_api_key,
            'twitter_bearer_token': settings.api.twitter_bearer_token,
            'newsapi_key': settings.api.newsapi_key,
        }
        
        return key_mapping.get(key_name)
    
    def _get_encrypted_key_from_storage(self, key_name: str) -> Optional[str]:
        """Get encrypted key from secure storage"""
        # In a real implementation, this would query a database
        # For now, we'll use the configuration manager
        secure_config = self.config_manager.get_configuration("secure_keys")
        return secure_config.get(key_name)
    
    def _store_encrypted_key(self, key_name: str, encrypted_key: str) -> bool:
        """Store encrypted key in secure storage"""
        try:
            # Store in configuration manager under secure_keys section
            updates = {
                "secure_keys": {
                    key_name: encrypted_key
                }
            }
            return self.config_manager.update_configuration(updates, validate=False)
        except Exception as e:
            logger.error(f"Failed to store encrypted key '{key_name}': {e}")
            return False
    
    def _has_encrypted_key(self, key_name: str) -> bool:
        """Check if we have an encrypted version of the key"""
        secure_config = self.config_manager.get_configuration("secure_keys")
        return key_name in secure_config
    
    def _on_config_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes"""
        logger.info(f"Configuration changed: {key}")
        
        # If trading configuration changed, validate it affects trading parameters
        if key.startswith("trading."):
            logger.info(f"Trading configuration updated: {key} = {new_value}")
            
            # Here you could trigger notifications to trading components
            # about configuration changes


# Global instance - initialized on first use
_secure_config_service = None

def get_secure_config_service():
    """Get the global secure configuration service instance"""
    global _secure_config_service
    if _secure_config_service is None:
        _secure_config_service = SecureConfigurationService()
    return _secure_config_service