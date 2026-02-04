"""
Configuration Manager for Bitcoin Trading System
Handles configuration validation, dynamic updates, and backup/restore
"""
import os
import json
import shutil
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .encryption import EncryptionService

logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationRule:
    """Configuration validation rule"""
    field_name: str
    validator: Callable[[Any], bool]
    error_message: str
    required: bool = True


@dataclass
class ConfigBackup:
    """Configuration backup information"""
    backup_id: str
    timestamp: datetime
    description: str
    file_path: str
    config_hash: str


class ConfigManager:
    """
    Manages system configuration including:
    - Configuration parameter validation
    - Dynamic configuration updates
    - Configuration backup and restore
    """
    
    def __init__(self, config_dir: str = "config", 
                 backup_dir: str = "config_backups",
                 encryption_service: Optional[EncryptionService] = None):
        """
        Initialize Configuration Manager
        
        Args:
            config_dir: Directory for configuration files
            backup_dir: Directory for configuration backups
            encryption_service: Optional encryption service for sensitive configs
        """
        self.config_dir = Path(config_dir)
        self.backup_dir = Path(backup_dir)
        self.encryption_service = encryption_service or EncryptionService()
        
        # Create directories if they don't exist
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Current configuration
        self.current_config: Dict[str, Any] = {}
        self.config_validators: Dict[str, List[ConfigValidationRule]] = {}
        self.config_change_callbacks: List[Callable[[str, Any, Any], None]] = []
        
        # Configuration metadata
        self.config_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Setup default validation rules
        self._setup_default_validators()
        
        # Load current configuration
        self._load_configuration()
    
    def register_validator(self, section: str, rule: ConfigValidationRule) -> None:
        """
        Register a validation rule for a configuration section
        
        Args:
            section: Configuration section name
            rule: Validation rule to register
        """
        if section not in self.config_validators:
            self.config_validators[section] = []
        
        self.config_validators[section].append(rule)
        logger.debug(f"Registered validator for {section}.{rule.field_name}")
    
    def register_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        Register a callback to be called when configuration changes
        
        Args:
            callback: Function to call with (key, old_value, new_value)
        """
        self.config_change_callbacks.append(callback)
    
    def validate_configuration(self, config: Dict[str, Any], 
                             section: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate configuration against registered rules
        
        Args:
            config: Configuration to validate
            section: Optional specific section to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        sections_to_validate = [section] if section else self.config_validators.keys()
        
        for section_name in sections_to_validate:
            if section_name not in self.config_validators:
                continue
            
            section_config = config.get(section_name, {})
            
            for rule in self.config_validators[section_name]:
                field_value = section_config.get(rule.field_name)
                
                # Check required fields
                if rule.required and field_value is None:
                    errors.append(f"{section_name}.{rule.field_name}: Field is required")
                    continue
                
                # Skip validation if field is not present and not required
                if field_value is None:
                    continue
                
                # Run validator
                try:
                    if not rule.validator(field_value):
                        errors.append(f"{section_name}.{rule.field_name}: {rule.error_message}")
                except Exception as e:
                    errors.append(f"{section_name}.{rule.field_name}: Validation error - {e}")
        
        return len(errors) == 0, errors
    
    def update_configuration(self, updates: Dict[str, Any], 
                           validate: bool = True, 
                           create_backup: bool = True) -> bool:
        """
        Update configuration with new values
        
        Args:
            updates: Dictionary of configuration updates
            validate: Whether to validate before applying
            create_backup: Whether to create backup before updating
            
        Returns:
            True if update was successful
        """
        try:
            # Create backup if requested
            if create_backup:
                backup_id = self.create_backup(f"Auto backup before update - {datetime.now()}")
                logger.info(f"Created backup {backup_id} before configuration update")
            
            # Merge updates with current config
            new_config = self._deep_merge(self.current_config.copy(), updates)
            
            # Validate if requested
            if validate:
                is_valid, errors = self.validate_configuration(new_config)
                if not is_valid:
                    logger.error(f"Configuration validation failed: {errors}")
                    return False
            
            # Track changes for callbacks
            changes = self._detect_changes(self.current_config, new_config)
            
            # Apply updates
            old_config = self.current_config.copy()
            self.current_config = new_config
            
            # Save to file
            self._save_configuration()
            
            # Call change callbacks
            for key, (old_value, new_value) in changes.items():
                for callback in self.config_change_callbacks:
                    try:
                        callback(key, old_value, new_value)
                    except Exception as e:
                        logger.error(f"Configuration change callback failed: {e}")
            
            logger.info(f"Configuration updated successfully. Changes: {list(changes.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_configuration(self, section: Optional[str] = None, 
                         decrypt_sensitive: bool = False) -> Dict[str, Any]:
        """
        Get current configuration
        
        Args:
            section: Optional specific section to return
            decrypt_sensitive: Whether to decrypt sensitive values
            
        Returns:
            Configuration dictionary
        """
        config = self.current_config.copy()
        
        if decrypt_sensitive:
            config = self._decrypt_sensitive_values(config)
        
        if section:
            return config.get(section, {})
        
        return config
    
    def create_backup(self, description: str = "") -> str:
        """
        Create a backup of current configuration
        
        Args:
            description: Optional description for the backup
            
        Returns:
            Backup ID
        """
        try:
            timestamp = datetime.now()
            backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup file
            backup_file = self.backup_dir / f"{backup_id}.json"
            
            backup_data = {
                "backup_id": backup_id,
                "timestamp": timestamp.isoformat(),
                "description": description,
                "configuration": self.current_config,
                "metadata": self.config_metadata
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Calculate config hash for integrity
            config_hash = self._calculate_config_hash(self.current_config)
            
            # Store backup metadata
            backup = ConfigBackup(
                backup_id=backup_id,
                timestamp=timestamp,
                description=description,
                file_path=str(backup_file),
                config_hash=config_hash
            )
            
            logger.info(f"Created configuration backup: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create configuration backup: {e}")
            raise
    
    def restore_backup(self, backup_id: str, validate: bool = True) -> bool:
        """
        Restore configuration from backup
        
        Args:
            backup_id: ID of backup to restore
            validate: Whether to validate restored configuration
            
        Returns:
            True if restore was successful
        """
        try:
            backup_file = self.backup_dir / f"{backup_id}.json"
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_id}")
                return False
            
            # Load backup data
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            restored_config = backup_data["configuration"]
            
            # Validate if requested
            if validate:
                is_valid, errors = self.validate_configuration(restored_config)
                if not is_valid:
                    logger.error(f"Restored configuration validation failed: {errors}")
                    return False
            
            # Create backup of current config before restoring
            current_backup_id = self.create_backup(f"Before restore of {backup_id}")
            
            # Apply restored configuration
            old_config = self.current_config.copy()
            self.current_config = restored_config
            self.config_metadata = backup_data.get("metadata", {})
            
            # Save restored configuration
            self._save_configuration()
            
            # Detect and notify changes
            changes = self._detect_changes(old_config, restored_config)
            for key, (old_value, new_value) in changes.items():
                for callback in self.config_change_callbacks:
                    try:
                        callback(key, old_value, new_value)
                    except Exception as e:
                        logger.error(f"Configuration change callback failed: {e}")
            
            logger.info(f"Configuration restored from backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore configuration from backup {backup_id}: {e}")
            return False
    
    def list_backups(self) -> List[ConfigBackup]:
        """
        List available configuration backups
        
        Returns:
            List of backup information
        """
        backups = []
        
        try:
            for backup_file in self.backup_dir.glob("backup_*.json"):
                try:
                    with open(backup_file, 'r') as f:
                        backup_data = json.load(f)
                    
                    backup = ConfigBackup(
                        backup_id=backup_data["backup_id"],
                        timestamp=datetime.fromisoformat(backup_data["timestamp"]),
                        description=backup_data.get("description", ""),
                        file_path=str(backup_file),
                        config_hash=self._calculate_config_hash(backup_data["configuration"])
                    )
                    backups.append(backup)
                    
                except Exception as e:
                    logger.warning(f"Failed to read backup file {backup_file}: {e}")
            
            # Sort by timestamp, newest first
            backups.sort(key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a configuration backup
        
        Args:
            backup_id: ID of backup to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            backup_file = self.backup_dir / f"{backup_id}.json"
            
            if backup_file.exists():
                backup_file.unlink()
                logger.info(f"Deleted backup: {backup_id}")
                return True
            else:
                logger.warning(f"Backup file not found: {backup_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def _setup_default_validators(self) -> None:
        """Setup default validation rules for common configuration sections"""
        
        # Database validation rules
        db_rules = [
            ConfigValidationRule("postgres_host", lambda x: isinstance(x, str) and len(x) > 0, "Must be non-empty string"),
            ConfigValidationRule("postgres_port", lambda x: isinstance(x, int) and 1 <= x <= 65535, "Must be valid port number"),
            ConfigValidationRule("postgres_db", lambda x: isinstance(x, str) and len(x) > 0, "Must be non-empty string"),
            ConfigValidationRule("influxdb_url", lambda x: isinstance(x, str) and x.startswith(('http://', 'https://')), "Must be valid URL"),
        ]
        
        for rule in db_rules:
            self.register_validator("database", rule)
        
        # API validation rules
        api_rules = [
            ConfigValidationRule("ai_temperature", lambda x: isinstance(x, (int, float)) and 0 <= x <= 2, "Must be between 0 and 2"),
            ConfigValidationRule("ai_max_tokens", lambda x: isinstance(x, int) and x > 0, "Must be positive integer"),
            ConfigValidationRule("binance_testnet", lambda x: isinstance(x, bool), "Must be boolean"),
        ]
        
        for rule in api_rules:
            self.register_validator("api", rule)
        
        # Trading validation rules
        trading_rules = [
            ConfigValidationRule("max_position_size", lambda x: isinstance(x, (int, float)) and 0 < x <= 1, "Must be between 0 and 1"),
            ConfigValidationRule("max_daily_loss", lambda x: isinstance(x, (int, float)) and 0 < x <= 1, "Must be between 0 and 1"),
            ConfigValidationRule("min_confidence_threshold", lambda x: isinstance(x, (int, float)) and 0 <= x <= 1, "Must be between 0 and 1"),
        ]
        
        for rule in trading_rules:
            self.register_validator("trading", rule)
    
    def _load_configuration(self) -> None:
        """Load configuration from file"""
        config_file = self.config_dir / "config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.current_config = json.load(f)
                logger.info("Configuration loaded from file")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                self.current_config = {}
        else:
            logger.info("No existing configuration file found, starting with empty config")
            self.current_config = {}
    
    def _save_configuration(self) -> None:
        """Save configuration to file"""
        config_file = self.config_dir / "config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.current_config, f, indent=2, default=str)
            logger.debug("Configuration saved to file")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _detect_changes(self, old_config: Dict[str, Any], 
                       new_config: Dict[str, Any], 
                       prefix: str = "") -> Dict[str, Tuple[Any, Any]]:
        """Detect changes between two configuration dictionaries"""
        changes = {}
        
        # Check for changes and additions
        for key, new_value in new_config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            old_value = old_config.get(key)
            
            if isinstance(new_value, dict) and isinstance(old_value, dict):
                # Recursively check nested dictionaries
                nested_changes = self._detect_changes(old_value, new_value, full_key)
                changes.update(nested_changes)
            elif old_value != new_value:
                changes[full_key] = (old_value, new_value)
        
        # Check for deletions
        for key, old_value in old_config.items():
            if key not in new_config:
                full_key = f"{prefix}.{key}" if prefix else key
                changes[full_key] = (old_value, None)
        
        return changes
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """Calculate hash of configuration for integrity checking"""
        import hashlib
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def _decrypt_sensitive_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive configuration values"""
        # This would identify and decrypt sensitive fields
        # For now, we'll just return the config as-is
        return config