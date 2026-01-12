"""
Selenium Teleport - Custom Exceptions

Hierarchical exception classes for better error handling and user feedback.
"""

from typing import Any, Dict, Optional


class TeleportError(Exception):
    """Base exception for all Teleport errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SecurityError(TeleportError):
    """Raised for security violations."""

    pass


class StateError(TeleportError):
    """Raised for state file issues."""

    pass


class DriverError(TeleportError):
    """Raised for driver creation issues."""

    pass


class ValidationError(TeleportError):
    """Raised for validation failures."""

    pass


class EncryptionError(SecurityError):
    """Raised for encryption/decryption failures."""

    pass


class DomainMismatchError(SecurityError):
    """Raised when state domain doesn't match target domain."""

    def __init__(self, state_domain: str, target_domain: str):
        message = (
            f"Domain mismatch: state from '{state_domain}' cannot be loaded to '{target_domain}'"
        )
        super().__init__(message, {"state_domain": state_domain, "target_domain": target_domain})
        self.state_domain = state_domain
        self.target_domain = target_domain


class PathTraversalError(SecurityError):
    """Raised when path traversal attack is detected."""

    def __init__(self, path: str):
        message = f"Path traversal detected in: '{path}'"
        super().__init__(message, {"path": path})
        self.path = path


class SSRFError(SecurityError):
    """Raised when SSRF attack is detected (private IP, local URL)."""

    def __init__(self, url: str, reason: str):
        message = f"SSRF prevention: {reason} - '{url}'"
        super().__init__(message, {"url": url, "reason": reason})
        self.url = url
        self.reason = reason


class ExpiredSessionError(StateError):
    """Raised when all session tokens are expired."""

    def __init__(self, expired_count: int, total_count: int):
        message = f"All {expired_count}/{total_count} cookies have expired"
        super().__init__(message, {"expired_count": expired_count, "total_count": total_count})
        self.expired_count = expired_count
        self.total_count = total_count


class StateFileNotFoundError(StateError):
    """Raised when state file doesn't exist."""

    def __init__(self, file_path: str):
        message = f"State file not found: '{file_path}'"
        super().__init__(message, {"file_path": file_path})
        self.file_path = file_path


class InvalidStateError(StateError):
    """Raised when state file has invalid format."""

    def __init__(self, file_path: str, reason: str):
        message = f"Invalid state file '{file_path}': {reason}"
        super().__init__(message, {"file_path": file_path, "reason": reason})
        self.file_path = file_path
        self.reason = reason


class DriverNotFoundError(DriverError):
    """Raised when required driver package is not installed."""

    def __init__(self, driver_type: str, install_command: str):
        message = f"{driver_type} not installed. Install with: {install_command}"
        super().__init__(message, {"driver_type": driver_type, "install_command": install_command})
        self.driver_type = driver_type
        self.install_command = install_command
