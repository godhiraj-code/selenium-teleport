"""
Selenium Teleport - Configuration Management

Centralized configuration for enterprise deployments.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TeleportConfig:
    """
    Configuration settings for Selenium Teleport.
    
    Can be loaded from environment variables, config file, or set programmatically.
    
    Example:
        >>> config = TeleportConfig.from_env()
        >>> config.encryption_enabled
        True
    """

    # Security settings
    encryption_key: Optional[str] = None
    encryption_enabled: bool = False
    validate_expiry: bool = True
    validate_domain: bool = True
    
    # Path settings
    default_profile_path: str = "selenium_profile"
    state_file_extension: str = ".json"
    
    # Logging
    log_level: str = "INFO"
    audit_logging: bool = False
    
    # Enterprise features
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    multi_tenant_mode: bool = False
    tenant_id: Optional[str] = None
    
    # Performance
    async_enabled: bool = False
    
    @classmethod
    def from_env(cls) -> "TeleportConfig":
        """
        Load configuration from environment variables.
        
        Environment variables:
            TELEPORT_ENCRYPTION_KEY: Encryption key (enables encryption if set)
            TELEPORT_VALIDATE_EXPIRY: "true" or "false"
            TELEPORT_VALIDATE_DOMAIN: "true" or "false"
            TELEPORT_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR
            TELEPORT_ALLOWED_DOMAINS: Comma-separated list
            TELEPORT_TENANT_ID: Tenant ID for multi-tenant mode
        """
        encryption_key = os.environ.get("TELEPORT_ENCRYPTION_KEY")
        
        def parse_bool(key: str, default: bool = True) -> bool:
            value = os.environ.get(key, "").lower()
            if value in ("true", "1", "yes"):
                return True
            if value in ("false", "0", "no"):
                return False
            return default
        
        def parse_list(key: str) -> List[str]:
            value = os.environ.get(key, "")
            if not value:
                return []
            return [d.strip() for d in value.split(",") if d.strip()]
        
        return cls(
            encryption_key=encryption_key,
            encryption_enabled=encryption_key is not None,
            validate_expiry=parse_bool("TELEPORT_VALIDATE_EXPIRY", True),
            validate_domain=parse_bool("TELEPORT_VALIDATE_DOMAIN", True),
            default_profile_path=os.environ.get("TELEPORT_PROFILE_PATH", "selenium_profile"),
            log_level=os.environ.get("TELEPORT_LOG_LEVEL", "INFO"),
            audit_logging=parse_bool("TELEPORT_AUDIT_LOGGING", False),
            allowed_domains=parse_list("TELEPORT_ALLOWED_DOMAINS"),
            blocked_domains=parse_list("TELEPORT_BLOCKED_DOMAINS"),
            multi_tenant_mode=parse_bool("TELEPORT_MULTI_TENANT", False),
            tenant_id=os.environ.get("TELEPORT_TENANT_ID"),
        )
    
    @classmethod
    def from_file(cls, path: str) -> "TeleportConfig":
        """
        Load configuration from a JSON file.
        
        Args:
            path: Path to the JSON configuration file
            
        Returns:
            TeleportConfig instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(
            encryption_key=data.get("encryption_key"),
            encryption_enabled=data.get("encryption_enabled", False),
            validate_expiry=data.get("validate_expiry", True),
            validate_domain=data.get("validate_domain", True),
            default_profile_path=data.get("default_profile_path", "selenium_profile"),
            state_file_extension=data.get("state_file_extension", ".json"),
            log_level=data.get("log_level", "INFO"),
            audit_logging=data.get("audit_logging", False),
            allowed_domains=data.get("allowed_domains", []),
            blocked_domains=data.get("blocked_domains", []),
            multi_tenant_mode=data.get("multi_tenant_mode", False),
            tenant_id=data.get("tenant_id"),
        )
    
    def to_dict(self) -> dict:
        """Convert config to dictionary (excludes sensitive data)."""
        return {
            "encryption_enabled": self.encryption_enabled,
            "validate_expiry": self.validate_expiry,
            "validate_domain": self.validate_domain,
            "default_profile_path": self.default_profile_path,
            "log_level": self.log_level,
            "audit_logging": self.audit_logging,
            "allowed_domains": self.allowed_domains,
            "multi_tenant_mode": self.multi_tenant_mode,
        }
    
    def get_encryption_key_bytes(self) -> Optional[bytes]:
        """Get encryption key as bytes, or None if not set."""
        if not self.encryption_key:
            return None
        return self.encryption_key.encode("utf-8")


# Global config instance (can be overridden)
_global_config: Optional[TeleportConfig] = None


def get_config() -> TeleportConfig:
    """Get the global configuration, loading from env if not set."""
    global _global_config
    if _global_config is None:
        _global_config = TeleportConfig.from_env()
    return _global_config


def set_config(config: TeleportConfig) -> None:
    """Set the global configuration."""
    global _global_config
    _global_config = config
    logger.debug(f"Configuration updated: {config.to_dict()}")
