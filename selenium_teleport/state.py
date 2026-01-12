"""
Selenium Teleport - State Management Module

Core functions for saving and loading browser state with security features.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import get_config
from .cookies import extract_cookies, inject_cookies
from .exceptions import (
    DomainMismatchError,
    ExpiredSessionError,
    InvalidStateError,
    StateFileNotFoundError,
)
from .security import (
    decrypt_state,
    encrypt_state,
    is_encrypted,
    remove_expired_cookies,
    sanitize_file_path,
    validate_domain_match,
    validate_url,
)
from .storage import (
    get_indexeddb_info,
    get_local_storage,
    get_session_storage,
    set_local_storage,
    set_session_storage,
)
from .utils import extract_base_domain

logger = logging.getLogger(__name__)


# Current state file version
STATE_VERSION = "2.1"


def save_state(
    driver,
    file_path: str,
    encrypt: bool = False,
    encryption_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract and save browser state (Cookies, LocalStorage, SessionStorage) to a JSON file.

    For best results, use with a driver created via create_driver() which uses
    a persistent Chrome profile for maximum compatibility.

    Args:
        driver: Selenium WebDriver instance
        file_path: Path where the state JSON file will be saved
        encrypt: If True, encrypt the state file
        encryption_key: Optional encryption key (uses env var if not provided)

    Returns:
        Dictionary containing the saved state

    Example:
        >>> from selenium_teleport import create_driver, save_state
        >>>
        >>> driver = create_driver()
        >>> driver.get("https://example.com")
        >>> # ... login process ...
        >>> save_state(driver, "session_state.json")
        >>>
        >>> # With encryption
        >>> save_state(driver, "session_state.enc", encrypt=True)
    """
    # Sanitize file path
    file_path = sanitize_file_path(file_path)

    logger.info(f"Saving browser state to {file_path}")

    current_url = driver.current_url

    # Extract all storage types
    cookies = extract_cookies(driver)
    local_storage = get_local_storage(driver)
    session_storage = get_session_storage(driver)
    indexeddb_info = get_indexeddb_info(driver)

    logger.debug(
        f"Extracted {len(cookies)} cookies, "
        f"{len(local_storage)} localStorage items, "
        f"{len(session_storage)} sessionStorage items"
    )

    state = {
        "metadata": {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "source_url": current_url,
            "source_domain": extract_base_domain(current_url),
            "version": STATE_VERSION,
            "encrypted": encrypt,
        },
        "cookies": cookies,
        "localStorage": local_storage,
        "sessionStorage": session_storage,
        "indexedDB": indexeddb_info,
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

    if encrypt:
        encrypted_data = encrypt_state(state, encryption_key)
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
        logger.info(f"Encrypted state saved to {file_path}")
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        logger.info(f"State saved successfully to {file_path}")

    return state


def load_state(
    driver,
    file_path: str,
    destination_url: str,
    validate_expiry: bool = True,
    validate_domain: bool = True,
    remove_expired: bool = True,
    encryption_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load browser state from a JSON file and teleport to the destination URL.

    This function handles the Same-Origin Policy by:
    1. Navigating to the base domain first
    2. Injecting cookies and storage
    3. Navigating to the final destination

    For best results, use with a driver created via create_driver() which uses
    a persistent Chrome profile for maximum compatibility.

    Args:
        driver: Selenium WebDriver instance
        file_path: Path to the state JSON file
        destination_url: The URL to navigate to after restoring state
        validate_expiry: If True, check for expired cookies (default True)
        validate_domain: If True, verify domain match (default True)
        remove_expired: If True, remove expired cookies before injection (default True)
        encryption_key: Optional encryption key for encrypted files

    Returns:
        Dictionary containing the loaded state

    Raises:
        StateFileNotFoundError: If state file doesn't exist
        DomainMismatchError: If domain validation fails
        ExpiredSessionError: If all cookies are expired

    Example:
        >>> from selenium_teleport import create_driver, load_state
        >>>
        >>> driver = create_driver()
        >>> load_state(driver, "session_state.json", "https://example.com/dashboard")
    """
    # Sanitize and validate inputs
    file_path = sanitize_file_path(file_path)
    validate_url(destination_url)

    if not os.path.exists(file_path):
        raise StateFileNotFoundError(file_path)

    logger.info(f"Loading browser state from {file_path}")

    # Load and potentially decrypt state
    with open(file_path, "rb") as f:
        content = f.read()

    if is_encrypted(content):
        state = decrypt_state(content, encryption_key)
        logger.debug("Decrypted state file")
    else:
        try:
            state = json.loads(content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise InvalidStateError(file_path, str(e))

    # Validate state structure
    if "cookies" not in state:
        raise InvalidStateError(file_path, "Missing 'cookies' key")

    # Get config for validation settings
    config = get_config()
    validate_domain = validate_domain and config.validate_domain
    validate_expiry = validate_expiry and config.validate_expiry

    # Domain validation
    if validate_domain:
        source_domain = state.get("metadata", {}).get("source_domain", "")
        if source_domain and not validate_domain_match(source_domain, destination_url):
            raise DomainMismatchError(source_domain, destination_url)

    cookies = state.get("cookies", [])
    local_storage = state.get("localStorage", {})
    session_storage = state.get("sessionStorage", {})

    # Handle expired cookies
    if validate_expiry or remove_expired:
        original_count = len(cookies)
        cookies = remove_expired_cookies(cookies)
        if len(cookies) == 0 and original_count > 0:
            raise ExpiredSessionError(original_count, original_count)

    # Navigate to base domain first (Same-Origin Policy)
    base_domain = extract_base_domain(destination_url)
    logger.info(f"Navigating to base domain: {base_domain}")
    driver.get(base_domain)

    # Inject cookies
    inject_cookies(driver, cookies)

    # Inject storage
    set_local_storage(driver, local_storage)
    set_session_storage(driver, session_storage)

    # Teleport to final destination
    logger.info(f"Teleporting to: {destination_url}")
    driver.get(destination_url)

    logger.info("State loaded and teleport complete!")

    return state


def delete_state(file_path: str, secure: bool = True) -> None:
    """
    Delete a state file securely (GDPR compliance).

    Args:
        file_path: Path to the state file to delete
        secure: If True, overwrite file before deletion
    """
    file_path = sanitize_file_path(file_path)

    if not os.path.exists(file_path):
        return

    if secure:
        # Overwrite with random data before deletion
        file_size = os.path.getsize(file_path)
        with open(file_path, "wb") as f:
            f.write(os.urandom(file_size))

    os.remove(file_path)
    logger.info(f"Securely deleted state file: {file_path}")


def get_state_info(file_path: str, encryption_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get metadata about a state file without loading full state.

    Args:
        file_path: Path to the state file
        encryption_key: Optional encryption key

    Returns:
        Dictionary with state metadata
    """
    file_path = sanitize_file_path(file_path)

    if not os.path.exists(file_path):
        raise StateFileNotFoundError(file_path)

    with open(file_path, "rb") as f:
        content = f.read()

    is_enc = is_encrypted(content)

    if is_enc:
        if encryption_key:
            state = decrypt_state(content, encryption_key)
        else:
            return {
                "encrypted": True,
                "file_size": len(content),
                "requires_key": True,
            }
    else:
        state = json.loads(content.decode("utf-8"))

    metadata = state.get("metadata", {})

    return {
        "encrypted": is_enc,
        "file_size": len(content),
        "version": metadata.get("version", "unknown"),
        "saved_at": metadata.get("saved_at"),
        "source_domain": metadata.get("source_domain"),
        "cookie_count": len(state.get("cookies", [])),
        "localStorage_count": len(state.get("localStorage", {})),
        "sessionStorage_count": len(state.get("sessionStorage", {})),
    }
