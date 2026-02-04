"""
Command-line interface for security and configuration management
"""
import click
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from .integration import secure_config_service


@click.group()
def security_cli():
    """Security and Configuration Management CLI"""
    pass


@security_cli.group()
def config():
    """Configuration management commands"""
    pass


@security_cli.group()
def security():
    """Security management commands"""
    pass


@config.command()
@click.option('--section', help='Configuration section to display')
@click.option('--decrypt', is_flag=True, help='Decrypt sensitive values')
def show(section, decrypt):
    """Show current configuration"""
    try:
        config_data = secure_config_service.config_manager.get_configuration(
            section=section, 
            decrypt_sensitive=decrypt
        )
        click.echo(json.dumps(config_data, indent=2, default=str))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@config.command()
@click.option('--file', '-f', required=True, help='JSON file with configuration updates')
@click.option('--no-validate', is_flag=True, help='Skip validation')
@click.option('--no-backup', is_flag=True, help='Skip creating backup')
def update(file, no_validate, no_backup):
    """Update configuration from JSON file"""
    try:
        with open(file, 'r') as f:
            updates = json.load(f)
        
        success = secure_config_service.config_manager.update_configuration(
            updates, 
            validate=not no_validate, 
            create_backup=not no_backup
        )
        
        if success:
            click.echo("Configuration updated successfully")
        else:
            click.echo("Configuration update failed", err=True)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@config.command()
@click.option('--description', '-d', help='Backup description')
def backup(description):
    """Create configuration backup"""
    try:
        backup_id = secure_config_service.create_configuration_backup(description or "")
        click.echo(f"Backup created: {backup_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@config.command()
def list_backups():
    """List available configuration backups"""
    try:
        backups = secure_config_service.config_manager.list_backups()
        
        if not backups:
            click.echo("No backups found")
            return
        
        click.echo("Available backups:")
        click.echo("-" * 80)
        for backup in backups:
            click.echo(f"ID: {backup.backup_id}")
            click.echo(f"Date: {backup.timestamp}")
            click.echo(f"Description: {backup.description}")
            click.echo(f"Hash: {backup.config_hash[:16]}...")
            click.echo("-" * 80)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@config.command()
@click.argument('backup_id')
@click.option('--no-validate', is_flag=True, help='Skip validation')
def restore(backup_id, no_validate):
    """Restore configuration from backup"""
    try:
        success = secure_config_service.config_manager.restore_backup(
            backup_id, 
            validate=not no_validate
        )
        
        if success:
            click.echo(f"Configuration restored from backup: {backup_id}")
        else:
            click.echo("Configuration restore failed", err=True)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@security.command()
def status():
    """Show security status"""
    try:
        status = secure_config_service.get_security_status()
        
        click.echo("Security Status:")
        click.echo("-" * 40)
        click.echo(f"System Status: {status['system_status']}")
        click.echo(f"Blocked IPs: {status['blocked_ips']}")
        click.echo(f"Recent Alerts: {status['recent_alerts']}")
        click.echo(f"Critical Alerts: {status['critical_alerts']}")
        
        click.echo("\nAccess Statistics:")
        click.echo("-" * 40)
        stats = status['access_statistics']
        click.echo(f"Total Attempts: {stats['total_attempts']}")
        click.echo(f"Success Rate: {stats['success_rate']:.2%}")
        click.echo(f"Unique IPs: {stats['unique_ips']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@security.command()
@click.option('--severity', help='Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)')
@click.option('--hours', default=24, help='Hours to look back')
def alerts(severity, hours):
    """Show security alerts"""
    try:
        since = datetime.now() - timedelta(hours=hours) if hours else None
        alerts = secure_config_service.security_manager.get_security_alerts(
            severity=severity, 
            since=since
        )
        
        if not alerts:
            click.echo("No alerts found")
            return
        
        click.echo(f"Security Alerts (last {hours} hours):")
        click.echo("-" * 60)
        
        for alert in alerts:
            click.echo(f"[{alert.severity}] {alert.alert_type}")
            click.echo(f"Time: {alert.timestamp}")
            click.echo(f"Message: {alert.message}")
            if alert.details:
                click.echo(f"Details: {json.dumps(alert.details, indent=2)}")
            click.echo("-" * 60)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@security.command()
@click.argument('key_name')
@click.argument('api_key')
def store_key(key_name, api_key):
    """Store an API key securely"""
    try:
        success = secure_config_service.store_secure_api_key(key_name, api_key)
        
        if success:
            click.echo(f"API key '{key_name}' stored securely")
        else:
            click.echo("Failed to store API key", err=True)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@security.command()
@click.argument('key_name')
def get_key(key_name):
    """Retrieve a stored API key"""
    try:
        api_key = secure_config_service.get_secure_api_key(key_name)
        
        if api_key:
            # Only show first and last few characters for security
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            click.echo(f"API key '{key_name}': {masked_key}")
        else:
            click.echo(f"API key '{key_name}' not found")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == '__main__':
    security_cli()