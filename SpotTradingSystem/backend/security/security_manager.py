"""
Security Manager for Bitcoin Trading System
Handles API key encryption, access control, and anomaly detection
"""
import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

from .encryption import EncryptionService

logger = logging.getLogger(__name__)


@dataclass
class AccessAttempt:
    """Record of an access attempt"""
    timestamp: datetime
    ip_address: str
    user_agent: str
    endpoint: str
    success: bool
    reason: Optional[str] = None


@dataclass
class SecurityAlert:
    """Security alert information"""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    timestamp: datetime
    details: Dict[str, Any]


class SecurityManager:
    """
    Manages security aspects of the trading system including:
    - API key encryption and storage
    - Access permission verification
    - Anomaly detection and blocking
    """
    
    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize Security Manager
        
        Args:
            encryption_service: Optional encryption service. Creates default if None.
        """
        self.encryption_service = encryption_service or EncryptionService()
        self.access_attempts: List[AccessAttempt] = []
        self.blocked_ips: Dict[str, datetime] = {}
        self.security_alerts: List[SecurityAlert] = []
        
        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.rate_limit_window = timedelta(minutes=1)
        self.max_requests_per_window = 60
        
        # Track request rates per IP
        self.request_counts: Dict[str, List[datetime]] = defaultdict(list)
        
        # Load existing security data
        self._load_security_data()
    
    def encrypt_api_key(self, api_key: str, key_name: str) -> str:
        """
        Encrypt and store an API key
        
        Args:
            api_key: The API key to encrypt
            key_name: Name/identifier for the key
            
        Returns:
            Encrypted key string
        """
        try:
            encrypted_key = self.encryption_service.encrypt(api_key)
            logger.info(f"API key '{key_name}' encrypted successfully")
            return encrypted_key
        except Exception as e:
            logger.error(f"Failed to encrypt API key '{key_name}': {e}")
            raise
    
    def decrypt_api_key(self, encrypted_key: str, key_name: str) -> str:
        """
        Decrypt an API key
        
        Args:
            encrypted_key: The encrypted key
            key_name: Name/identifier for the key
            
        Returns:
            Decrypted API key
        """
        try:
            decrypted_key = self.encryption_service.decrypt(encrypted_key)
            logger.debug(f"API key '{key_name}' decrypted successfully")
            return decrypted_key
        except Exception as e:
            logger.error(f"Failed to decrypt API key '{key_name}': {e}")
            raise
    
    def store_encrypted_config(self, config_data: Dict[str, Any], config_name: str) -> str:
        """
        Encrypt and store configuration data
        
        Args:
            config_data: Configuration dictionary to encrypt
            config_name: Name of the configuration
            
        Returns:
            Encrypted configuration string
        """
        try:
            encrypted_config = self.encryption_service.encrypt_dict(config_data)
            logger.info(f"Configuration '{config_name}' encrypted and stored")
            return encrypted_config
        except Exception as e:
            logger.error(f"Failed to encrypt configuration '{config_name}': {e}")
            raise
    
    def load_encrypted_config(self, encrypted_config: str, config_name: str) -> Dict[str, Any]:
        """
        Load and decrypt configuration data
        
        Args:
            encrypted_config: Encrypted configuration string
            config_name: Name of the configuration
            
        Returns:
            Decrypted configuration dictionary
        """
        try:
            config_data = self.encryption_service.decrypt_dict(encrypted_config)
            logger.debug(f"Configuration '{config_name}' loaded and decrypted")
            return config_data
        except Exception as e:
            logger.error(f"Failed to decrypt configuration '{config_name}': {e}")
            raise
    
    def verify_access_permission(self, ip_address: str, user_agent: str, endpoint: str) -> bool:
        """
        Verify if access should be granted based on security policies
        
        Args:
            ip_address: Client IP address
            user_agent: Client user agent
            endpoint: Requested endpoint
            
        Returns:
            True if access should be granted
        """
        # Check if IP is blocked
        if self._is_ip_blocked(ip_address):
            self._log_access_attempt(ip_address, user_agent, endpoint, False, "IP blocked")
            return False
        
        # Check rate limiting
        if self._is_rate_limited(ip_address):
            self._log_access_attempt(ip_address, user_agent, endpoint, False, "Rate limited")
            self._create_security_alert(
                "RATE_LIMIT_EXCEEDED",
                "MEDIUM",
                f"Rate limit exceeded for IP {ip_address}",
                {"ip_address": ip_address, "endpoint": endpoint}
            )
            return False
        
        # Check for suspicious patterns
        if self._detect_suspicious_activity(ip_address, user_agent, endpoint):
            self._log_access_attempt(ip_address, user_agent, endpoint, False, "Suspicious activity")
            return False
        
        # Log successful access
        self._log_access_attempt(ip_address, user_agent, endpoint, True)
        return True
    
    def detect_anomalous_access(self, ip_address: str, user_agent: str, endpoint: str) -> bool:
        """
        Detect anomalous access patterns
        
        Args:
            ip_address: Client IP address
            user_agent: Client user agent
            endpoint: Requested endpoint
            
        Returns:
            True if anomalous activity detected
        """
        # Check for rapid successive requests
        recent_attempts = [
            attempt for attempt in self.access_attempts
            if attempt.ip_address == ip_address and 
            attempt.timestamp > datetime.now() - timedelta(minutes=5)
        ]
        
        if len(recent_attempts) > 20:  # More than 20 requests in 5 minutes
            self._create_security_alert(
                "RAPID_REQUESTS",
                "HIGH",
                f"Rapid successive requests detected from {ip_address}",
                {"ip_address": ip_address, "request_count": len(recent_attempts)}
            )
            return True
        
        # Check for failed authentication attempts
        failed_attempts = [
            attempt for attempt in recent_attempts
            if not attempt.success and "auth" in attempt.endpoint.lower()
        ]
        
        if len(failed_attempts) >= self.max_failed_attempts:
            self._block_ip(ip_address)
            self._create_security_alert(
                "MULTIPLE_FAILED_AUTH",
                "CRITICAL",
                f"Multiple failed authentication attempts from {ip_address}",
                {"ip_address": ip_address, "failed_count": len(failed_attempts)}
            )
            return True
        
        return False
    
    def block_suspicious_ip(self, ip_address: str, reason: str) -> None:
        """
        Block an IP address for suspicious activity
        
        Args:
            ip_address: IP address to block
            reason: Reason for blocking
        """
        self._block_ip(ip_address)
        self._create_security_alert(
            "IP_BLOCKED",
            "HIGH",
            f"IP {ip_address} blocked: {reason}",
            {"ip_address": ip_address, "reason": reason}
        )
        logger.warning(f"Blocked IP {ip_address}: {reason}")
    
    def get_security_alerts(self, severity: Optional[str] = None, 
                          since: Optional[datetime] = None) -> List[SecurityAlert]:
        """
        Get security alerts with optional filtering
        
        Args:
            severity: Filter by severity level
            since: Filter alerts since this datetime
            
        Returns:
            List of security alerts
        """
        alerts = self.security_alerts
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        if since:
            alerts = [alert for alert in alerts if alert.timestamp >= since]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_access_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get access statistics for the specified time period
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with access statistics
        """
        since = datetime.now() - timedelta(hours=hours)
        recent_attempts = [
            attempt for attempt in self.access_attempts
            if attempt.timestamp >= since
        ]
        
        total_attempts = len(recent_attempts)
        successful_attempts = len([a for a in recent_attempts if a.success])
        failed_attempts = total_attempts - successful_attempts
        
        # Count unique IPs
        unique_ips = len(set(attempt.ip_address for attempt in recent_attempts))
        
        # Count attempts by endpoint
        endpoint_counts = defaultdict(int)
        for attempt in recent_attempts:
            endpoint_counts[attempt.endpoint] += 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "unique_ips": unique_ips,
            "blocked_ips": len(self.blocked_ips),
            "endpoint_counts": dict(endpoint_counts),
            "time_period_hours": hours
        }
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is currently blocked"""
        if ip_address not in self.blocked_ips:
            return False
        
        # Check if lockout period has expired
        blocked_time = self.blocked_ips[ip_address]
        if datetime.now() - blocked_time > self.lockout_duration:
            del self.blocked_ips[ip_address]
            logger.info(f"IP {ip_address} unblocked after lockout period")
            return False
        
        return True
    
    def _is_rate_limited(self, ip_address: str) -> bool:
        """Check if an IP address is rate limited"""
        now = datetime.now()
        
        # Clean old requests outside the window
        cutoff_time = now - self.rate_limit_window
        self.request_counts[ip_address] = [
            req_time for req_time in self.request_counts[ip_address]
            if req_time > cutoff_time
        ]
        
        # Add current request
        self.request_counts[ip_address].append(now)
        
        # Check if rate limit exceeded
        return len(self.request_counts[ip_address]) > self.max_requests_per_window
    
    def _detect_suspicious_activity(self, ip_address: str, user_agent: str, endpoint: str) -> bool:
        """Detect suspicious activity patterns"""
        # Check for suspicious user agents
        suspicious_agents = ['bot', 'crawler', 'scanner', 'hack', 'exploit']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            self._create_security_alert(
                "SUSPICIOUS_USER_AGENT",
                "MEDIUM",
                f"Suspicious user agent detected: {user_agent}",
                {"ip_address": ip_address, "user_agent": user_agent}
            )
            return True
        
        # Check for suspicious endpoints
        suspicious_endpoints = ['/admin', '/.env', '/config', '/backup', '/dump']
        if any(sus_endpoint in endpoint.lower() for sus_endpoint in suspicious_endpoints):
            self._create_security_alert(
                "SUSPICIOUS_ENDPOINT",
                "HIGH",
                f"Access to suspicious endpoint: {endpoint}",
                {"ip_address": ip_address, "endpoint": endpoint}
            )
            return True
        
        return False
    
    def _block_ip(self, ip_address: str) -> None:
        """Block an IP address"""
        self.blocked_ips[ip_address] = datetime.now()
        logger.warning(f"IP {ip_address} has been blocked")
    
    def _log_access_attempt(self, ip_address: str, user_agent: str, endpoint: str, 
                           success: bool, reason: Optional[str] = None) -> None:
        """Log an access attempt"""
        attempt = AccessAttempt(
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            success=success,
            reason=reason
        )
        self.access_attempts.append(attempt)
        
        # Keep only recent attempts to prevent memory issues
        cutoff_time = datetime.now() - timedelta(days=7)
        self.access_attempts = [
            attempt for attempt in self.access_attempts
            if attempt.timestamp > cutoff_time
        ]
    
    def _create_security_alert(self, alert_type: str, severity: str, 
                              message: str, details: Dict[str, Any]) -> None:
        """Create a security alert"""
        alert = SecurityAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            details=details
        )
        self.security_alerts.append(alert)
        
        # Keep only recent alerts
        cutoff_time = datetime.now() - timedelta(days=30)
        self.security_alerts = [
            alert for alert in self.security_alerts
            if alert.timestamp > cutoff_time
        ]
        
        logger.warning(f"Security alert [{severity}]: {message}")
    
    def _load_security_data(self) -> None:
        """Load existing security data from storage"""
        # In a real implementation, this would load from a database
        # For now, we'll start with empty data
        pass
    
    def _save_security_data(self) -> None:
        """Save security data to storage"""
        # In a real implementation, this would save to a database
        pass