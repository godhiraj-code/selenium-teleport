"""
Selenium Teleport
=================

Save and restore browser state (Cookies, LocalStorage, SessionStorage) to
skip login screens and setup flows in Selenium automation scripts.

Features:
    - Persistent Chrome profile for maximum compatibility
    - Anti-detection measures built-in
    - Save complete browser state to a JSON file (with optional encryption)
    - Restore state and "teleport" to any authenticated page
    - Context manager for automatic state management
    - StealthBot-compatible functions for sb-stealth-wrapper
    - Security features: encryption, domain validation, path sanitization

Quick Start:
    >>> from selenium_teleport import create_driver, Teleport
    >>>
    >>> driver = create_driver(profile_path="my_profile")
    >>>
    >>> with Teleport(driver, "session.json") as t:
    ...     if t.has_state():
    ...         t.load("https://example.com/dashboard")
    ...     else:
    ...         driver.get("https://example.com/login")
    >>>
    >>> driver.quit()

With Encryption:
    >>> # Set TELEPORT_ENCRYPTION_KEY environment variable
    >>> with Teleport(driver, "session.enc", encrypt=True) as t:
    ...     # State is automatically encrypted/decrypted
    ...     pass
"""

__version__ = "2.1.0"
__author__ = "Dhiraj Das"
__license__ = "MIT"

# Configuration
from .config import (
    TeleportConfig,
    get_config,
    set_config,
)

# Context managers
from .context import (
    Teleport,
    teleport_session,
)

# Core driver creation
from .drivers import create_driver

# Exceptions
from .exceptions import (
    DomainMismatchError,
    DriverError,
    DriverNotFoundError,
    EncryptionError,
    ExpiredSessionError,
    InvalidStateError,
    PathTraversalError,
    SecurityError,
    SSRFError,
    StateError,
    StateFileNotFoundError,
    TeleportError,
    ValidationError,
)

# Security utilities
from .security import (
    decrypt_state,
    encrypt_state,
    generate_key,
    remove_expired_cookies,
    validate_domain_match,
)

# State management (main API)
from .state import (
    delete_state,
    get_state_info,
    load_state,
    save_state,
)

# StealthBot-compatible functions
from .stealth import (
    load_state_stealth,
    save_state_stealth,
)

__all__ = [
    # Version
    "__version__",
    # Driver
    "create_driver",
    # State management
    "save_state",
    "load_state",
    "delete_state",
    "get_state_info",
    # Stealth
    "save_state_stealth",
    "load_state_stealth",
    # Context managers
    "Teleport",
    "teleport_session",
    # Configuration
    "TeleportConfig",
    "get_config",
    "set_config",
    # Security
    "generate_key",
    "encrypt_state",
    "decrypt_state",
    "validate_domain_match",
    "remove_expired_cookies",
    # Exceptions
    "TeleportError",
    "SecurityError",
    "StateError",
    "DriverError",
    "ValidationError",
    "EncryptionError",
    "DomainMismatchError",
    "PathTraversalError",
    "SSRFError",
    "ExpiredSessionError",
    "StateFileNotFoundError",
    "InvalidStateError",
    "DriverNotFoundError",
]
