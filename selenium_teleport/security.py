"""
Selenium Teleport - Security Module

Provides encryption, validation, and sanitization for secure state management.

Features:
    - State file encryption using Fernet (symmetric)
    - Token expiration validation
    - Domain validation (prevent cross-domain injection)
    - Input sanitization (prevent path traversal, SSRF)
"""

import base64
import hashlib
import ipaddress
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .config import get_config
from .exceptions import (
    DomainMismatchError,
    EncryptionError,
    PathTraversalError,
    SSRFError,
    ValidationError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Encryption Functions
# =============================================================================


def _get_fernet():
    """Lazy import of cryptography to make it optional."""
    try:
        from cryptography.fernet import Fernet, InvalidToken

        return Fernet, InvalidToken
    except ImportError:
        raise EncryptionError(
            "cryptography package not installed. Install with: pip install selenium-teleport[security]"
        )


def generate_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded encryption key string

    Example:
        >>> key = generate_key()
        >>> print(key)  # Save this securely!
        'abc123...'
    """
    Fernet, _ = _get_fernet()
    return Fernet.generate_key().decode("utf-8")


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
    """
    Derive a Fernet key from a password using PBKDF2.

    Args:
        password: User-provided password
        salt: Optional salt bytes (generated if not provided)

    Returns:
        Tuple of (key_string, salt_bytes)
    """
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        raise EncryptionError(
            "cryptography package not installed. Install with: pip install selenium-teleport[security]"
        )

    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode("utf-8"), salt


def encrypt_state(state: Dict[str, Any], key: Optional[str] = None) -> bytes:
    """
    Encrypt state dictionary using Fernet symmetric encryption.

    Args:
        state: State dictionary to encrypt
        key: Fernet key string (uses config if not provided)

    Returns:
        Encrypted bytes

    Raises:
        EncryptionError: If encryption fails or key is missing
    """
    Fernet, _ = _get_fernet()

    if key is None:
        config = get_config()
        key = config.encryption_key

    if not key:
        raise EncryptionError(
            "No encryption key provided. Set TELEPORT_ENCRYPTION_KEY or pass key parameter."
        )

    try:
        f = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
        json_bytes = json.dumps(state, ensure_ascii=False).encode("utf-8")
        return f.encrypt(json_bytes)
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}")


def decrypt_state(encrypted_data: bytes, key: Optional[str] = None) -> Dict[str, Any]:
    """
    Decrypt state data using Fernet symmetric encryption.

    Args:
        encrypted_data: Encrypted bytes
        key: Fernet key string (uses config if not provided)

    Returns:
        Decrypted state dictionary

    Raises:
        EncryptionError: If decryption fails or key is wrong
    """
    Fernet, InvalidToken = _get_fernet()

    if key is None:
        config = get_config()
        key = config.encryption_key

    if not key:
        raise EncryptionError(
            "No encryption key provided. Set TELEPORT_ENCRYPTION_KEY or pass key parameter."
        )

    try:
        f = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
        decrypted = f.decrypt(encrypted_data)
        return json.loads(decrypted.decode("utf-8"))
    except InvalidToken:
        raise EncryptionError("Decryption failed: Invalid key or corrupted data")
    except Exception as e:
        raise EncryptionError(f"Decryption failed: {e}")


def is_encrypted(data: bytes) -> bool:
    """
    Check if data appears to be Fernet-encrypted.

    Fernet tokens start with 'gAAAAA' when base64 encoded.
    """
    return data.startswith(b"gAAAAA")


# =============================================================================
# Token Expiration Validation
# =============================================================================


def validate_token_expiry(state: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that cookies in state haven't expired.

    Args:
        state: State dictionary containing cookies

    Returns:
        Tuple of (all_valid, list of expired cookie names)
    """
    cookies = state.get("cookies", [])
    current_time = time.time()
    expired = []

    for cookie in cookies:
        expiry = cookie.get("expiry")
        if expiry is not None:
            try:
                if float(expiry) < current_time:
                    expired.append(cookie.get("name", "unknown"))
            except (ValueError, TypeError):
                pass  # Skip invalid expiry values

    return len(expired) == 0, expired


def remove_expired_cookies(cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove expired cookies from a list.

    Args:
        cookies: List of cookie dictionaries

    Returns:
        List with expired cookies removed
    """
    current_time = time.time()
    valid_cookies = []

    for cookie in cookies:
        expiry = cookie.get("expiry")
        if expiry is None:
            # Session cookie, no expiry
            valid_cookies.append(cookie)
        else:
            try:
                if float(expiry) >= current_time:
                    valid_cookies.append(cookie)
                else:
                    logger.debug(f"Removing expired cookie: {cookie.get('name')}")
            except (ValueError, TypeError):
                valid_cookies.append(cookie)  # Keep if expiry is invalid

    removed_count = len(cookies) - len(valid_cookies)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} expired cookies")

    return valid_cookies


# =============================================================================
# Domain Validation
# =============================================================================


def extract_root_domain(url: str) -> str:
    """
    Extract the root domain from a URL.

    Examples:
        "https://mail.google.com/inbox" -> "google.com"
        "https://example.com:8080/path" -> "example.com"
    """
    parsed = urlparse(url)
    hostname = parsed.netloc.split(":")[0]  # Remove port

    # Handle IP addresses
    try:
        ipaddress.ip_address(hostname)
        return hostname
    except ValueError:
        pass

    # Extract root domain (last two parts for most TLDs)
    parts = hostname.split(".")
    if len(parts) >= 2:
        # Handle common two-part TLDs like .co.uk, .com.au
        if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "gov", "edu"):
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return hostname


def validate_domain_match(state_domain: str, target_url: str, strict: bool = False) -> bool:
    """
    Validate that the state domain matches the target URL domain.

    Args:
        state_domain: Domain from saved state (e.g., "https://example.com")
        target_url: Target URL to validate against
        strict: If True, require exact domain match; if False, allow subdomains

    Returns:
        True if domains match, False otherwise

    Raises:
        DomainMismatchError: If validation fails and config requires it
    """
    state_root = extract_root_domain(state_domain)
    target_root = extract_root_domain(target_url)

    if strict:
        parsed_state = urlparse(state_domain)
        parsed_target = urlparse(target_url)
        state_host = parsed_state.netloc.split(":")[0]
        target_host = parsed_target.netloc.split(":")[0]
        return state_host == target_host

    return state_root == target_root


def check_domain_allowed(url: str) -> bool:
    """
    Check if a domain is in the allowed list (enterprise feature).

    Returns True if:
        - No allowed_domains configured (allow all)
        - Domain is in allowed_domains list
    """
    config = get_config()

    if not config.allowed_domains:
        return True  # No whitelist = allow all

    root_domain = extract_root_domain(url)
    return root_domain in config.allowed_domains


def check_domain_blocked(url: str) -> bool:
    """
    Check if a domain is in the blocked list.

    Returns True if domain is blocked.
    """
    config = get_config()

    if not config.blocked_domains:
        return False  # No blocklist

    root_domain = extract_root_domain(url)
    return root_domain in config.blocked_domains


# =============================================================================
# Input Sanitization
# =============================================================================

# Patterns that indicate path traversal attempts
PATH_TRAVERSAL_PATTERNS = [
    r"\.\.",  # Parent directory
    r"\.\.[\\/]",  # Parent with separator
    r"[\\/]\.\.",  # Separator then parent
    r"^~",  # Home directory expansion
    r"%2e%2e",  # URL-encoded ..
    r"%252e%252e",  # Double URL-encoded ..
]

# Private IP ranges for SSRF prevention
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]


def sanitize_file_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    Sanitize a file path to prevent path traversal attacks.

    Args:
        path: File path to sanitize
        base_dir: Optional base directory to restrict paths to

    Returns:
        Sanitized absolute path

    Raises:
        PathTraversalError: If path traversal is detected
    """
    # Check for traversal patterns before normalization
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            raise PathTraversalError(path)

    # Normalize the path
    normalized = os.path.normpath(path)
    absolute = os.path.abspath(normalized)

    # If base_dir specified, ensure path is within it
    if base_dir:
        base_absolute = os.path.abspath(base_dir)
        if not absolute.startswith(base_absolute):
            raise PathTraversalError(path)

    # Double-check for traversal after normalization
    if ".." in absolute:
        raise PathTraversalError(path)

    return absolute


def validate_url(url: str, allow_private: bool = False) -> Tuple[bool, str]:
    """
    Validate a URL for security issues (SSRF prevention).

    Args:
        url: URL to validate
        allow_private: If True, allow private/internal IP addresses

    Returns:
        Tuple of (is_valid, error_message or "ok")

    Raises:
        SSRFError: If URL is potentially malicious
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise SSRFError(url, "Invalid URL format")

    # Require http or https scheme
    if parsed.scheme not in ("http", "https"):
        raise SSRFError(url, f"Invalid scheme: {parsed.scheme}")

    # Require a host
    if not parsed.netloc:
        raise SSRFError(url, "No host specified")

    hostname = parsed.netloc.split(":")[0]

    # Block common internal hostnames (nosec: this is intentional for SSRF prevention)
    internal_hostnames = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]  # nosec B104
    if hostname.lower() in internal_hostnames and not allow_private:
        raise SSRFError(url, "Internal hostname not allowed")

    # Check for private IP addresses
    if not allow_private:
        try:
            ip = ipaddress.ip_address(hostname)
            for network in PRIVATE_IP_RANGES:
                if ip in network:
                    raise SSRFError(url, f"Private IP address not allowed: {ip}")
        except ValueError:
            pass  # Not an IP address, hostname is fine

    return True, "ok"


def sanitize_cookie_value(value: str) -> str:
    """
    Sanitize a cookie value to prevent injection attacks.

    Removes or escapes potentially dangerous characters.
    """
    # Remove null bytes and control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", value)
    return sanitized


# =============================================================================
# Utility Functions
# =============================================================================


def hash_state_for_audit(state: Dict[str, Any]) -> str:
    """
    Create a SHA-256 hash of state for audit logging.

    This allows tracking state without storing sensitive data.
    """
    serialized = json.dumps(state, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()[:16]


def anonymize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove potentially sensitive data from state for analytics/logging.

    Returns a copy with:
        - Cookie values replaced with "[REDACTED]"
        - localStorage/sessionStorage values replaced
        - Metadata preserved
    """
    anonymized = {
        "metadata": state.get("metadata", {}),
        "cookies": [],
        "localStorage": {},
        "sessionStorage": {},
    }

    # Anonymize cookies
    for cookie in state.get("cookies", []):
        anonymized["cookies"].append(
            {
                "name": cookie.get("name"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path"),
                "value": "[REDACTED]",
                "expiry": cookie.get("expiry"),
            }
        )

    # Anonymize storage
    for key in state.get("localStorage", {}):
        anonymized["localStorage"][key] = "[REDACTED]"

    for key in state.get("sessionStorage", {}):
        anonymized["sessionStorage"][key] = "[REDACTED]"

    return anonymized
