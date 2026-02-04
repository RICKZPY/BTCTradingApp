# Security and Configuration Management

This module provides comprehensive security and configuration management for the Bitcoin Trading System.

## Features

### Security Manager
- **API Key Encryption**: Secure storage and retrieval of sensitive API keys
- **Access Control**: IP-based access validation and rate limiting
- **Anomaly Detection**: Detection of suspicious access patterns
- **Security Alerts**: Real-time security event monitoring and alerting
- **IP Blocking**: Automatic blocking of suspicious IP addresses

### Configuration Manager
- **Configuration Validation**: Validate configuration parameters against rules
- **Dynamic Updates**: Update configuration at runtime with validation
- **Backup & Restore**: Create and restore configuration backups
- **Change Tracking**: Track configuration changes and notify callbacks

### Encryption Service
- **Data Encryption**: Encrypt/decrypt sensitive strings and dictionaries
- **Password Hashing**: Secure password hashing with PBKDF2
- **Key Derivation**: Derive encryption keys from master passwords

## Quick Start

### Basic Usage

```python
from security.integration import get_secure_config_service

# Get the service instance
service = get_secure_config_service()

# Store an API key securely
service.store_secure_api_key("binance_api_key", "your-secret-key")

# Retrieve the API key
api_key = service.get_secure_api_key("binance_api_key")

# Validate request access
is_allowed = service.validate_request_access(
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    endpoint="/api/trading"
)

# Update configuration
config_updates = {
    "trading": {
        "max_position_size": 0.15,
        "min_confidence_threshold": 0.8
    }
}
service.update_trading_configuration(config_updates)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from security.example_integration import setup_security_for_app, create_secure_api_routes

app = FastAPI()

# Setup security middleware
setup_security_for_app(app)

# Add security API routes
create_secure_api_routes(app)
```

### CLI Usage

```bash
# Show current configuration
python -m security.cli config show

# Create a backup
python -m security.cli config backup -d "Before production deployment"

# Show security status
python -m security.cli security status

# View security alerts
python -m security.cli security alerts --severity HIGH --hours 24

# Store an API key
python -m security.cli security store-key binance_api_key "your-key-here"
```

## Configuration

### Environment Variables

```bash
# Encryption master key (REQUIRED in production)
ENCRYPTION_MASTER_KEY=your-secure-master-key

# Security settings
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### Configuration Validation Rules

The system includes built-in validation rules for:

- **Database Settings**: Host, port, database name validation
- **API Settings**: Temperature ranges, token limits, boolean flags
- **Trading Settings**: Position sizes, loss limits, confidence thresholds

Custom validation rules can be added:

```python
from security.config_manager import ConfigValidationRule

rule = ConfigValidationRule(
    field_name="custom_field",
    validator=lambda x: isinstance(x, int) and x > 0,
    error_message="Must be positive integer",
    required=True
)

config_manager.register_validator("custom_section", rule)
```

## Security Features

### Access Control

- **IP-based filtering**: Block suspicious IP addresses
- **Rate limiting**: Prevent abuse with configurable rate limits
- **User agent analysis**: Detect and block suspicious user agents
- **Endpoint protection**: Monitor access to sensitive endpoints

### Anomaly Detection

- **Rapid requests**: Detect unusually high request rates
- **Failed authentication**: Monitor failed login attempts
- **Suspicious patterns**: Identify potential attack patterns
- **Geographic anomalies**: Detect access from unusual locations (future feature)

### Security Alerts

Alert types include:
- `RATE_LIMIT_EXCEEDED`: Too many requests from single IP
- `MULTIPLE_FAILED_AUTH`: Multiple authentication failures
- `SUSPICIOUS_USER_AGENT`: Suspicious user agent detected
- `SUSPICIOUS_ENDPOINT`: Access to sensitive endpoints
- `IP_BLOCKED`: IP address blocked for suspicious activity

## Configuration Management

### Backup System

- **Automatic backups**: Created before configuration updates
- **Manual backups**: Create backups with custom descriptions
- **Integrity checking**: SHA256 hashes for backup verification
- **Easy restoration**: Restore from any backup with validation

### Dynamic Updates

- **Runtime updates**: Change configuration without restart
- **Validation**: Ensure updates meet validation rules
- **Rollback**: Automatic backup before changes
- **Notifications**: Callbacks for configuration changes

## Testing

Run the test suite:

```bash
cd backend
python test_security_config.py
```

The test suite covers:
- Encryption/decryption functionality
- Security manager access control
- Configuration validation and updates
- Backup and restore operations
- Integration service functionality

## Production Deployment

### Security Checklist

1. **Set encryption master key**: `ENCRYPTION_MASTER_KEY` environment variable
2. **Configure rate limits**: Adjust based on expected traffic
3. **Setup monitoring**: Monitor security alerts and access patterns
4. **Regular backups**: Schedule automatic configuration backups
5. **Key rotation**: Regularly rotate API keys and encryption keys
6. **Access logs**: Enable detailed access logging
7. **Network security**: Use HTTPS and proper firewall rules

### Monitoring

Monitor these metrics:
- Security alert frequency and severity
- Access success/failure rates
- Blocked IP addresses
- Configuration change frequency
- Backup creation and restoration events

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ FastAPI         │    │ Security        │    │ Configuration   │
│ Middleware      │───▶│ Manager         │───▶│ Manager         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │ Encryption      │    │ Backup          │
         │              │ Service         │    │ System          │
         │              └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Access Control  │
│ & Monitoring    │
└─────────────────┘
```

## Contributing

When adding new security features:

1. Add appropriate validation rules
2. Include comprehensive tests
3. Update documentation
4. Consider security implications
5. Test with various attack scenarios

## License

This module is part of the Bitcoin Trading System and follows the same license terms.