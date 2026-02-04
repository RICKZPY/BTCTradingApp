"""
Encryption service for secure storage of sensitive data
"""
import os
import base64
import hashlib
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data like API keys"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            master_key: Master key for encryption. If None, will use environment variable
        """
        self._master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        if not self._master_key:
            # Generate a default key for development (should be set in production)
            self._master_key = "default-development-key-change-in-production"
            logger.warning("Using default encryption key. Set ENCRYPTION_MASTER_KEY in production!")
        
        self._fernet = self._create_fernet_key()
    
    def _create_fernet_key(self) -> Fernet:
        """Create Fernet encryption key from master key"""
        # Use PBKDF2 to derive a key from the master key
        from cryptography.hazmat.backends import default_backend
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'bitcoin_trading_salt',  # In production, use random salt per key
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode()))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string
        
        Args:
            data: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary by converting to JSON first
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted JSON string
        """
        json_data = json.dumps(data, sort_keys=True)
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt a dictionary from encrypted JSON
        
        Args:
            encrypted_data: Encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password with salt
        
        Args:
            password: Password to hash
            salt: Optional salt. If None, generates random salt
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = base64.urlsafe_b64encode(os.urandom(32)).decode()
        
        # Use PBKDF2 for password hashing
        from cryptography.hazmat.backends import default_backend
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        hashed = base64.urlsafe_b64encode(kdf.derive(password.encode())).decode()
        return hashed, salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Password to verify
            hashed_password: Stored hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches
        """
        try:
            new_hash, _ = self.hash_password(password, salt)
            return new_hash == hashed_password
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False