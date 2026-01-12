"""
Selenium Teleport - StealthBot Compatibility Module

Functions for saving and loading state using sb-stealth-wrapper's StealthBot.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import get_config
from .cookies import sanitize_cookie
from .exceptions import ExpiredSessionError, InvalidStateError, StateFileNotFoundError
from .security import (
    decrypt_state,
    encrypt_state,
    is_encrypted,
    remove_expired_cookies,
    sanitize_file_path,
    validate_domain_match,
)
from .utils import extract_base_domain

logger = logging.getLogger(__name__)


# Current state file version
STATE_VERSION = "2.1"


def save_state_stealth(
    bot,
    file_path: str,
    encrypt: bool = False,
    encryption_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save browser state using StealthBot's bot.sb methods.

    This function works around an issue where bot.sb.driver becomes stale
    after navigation with challenge handling. It uses bot.sb methods which
    maintain a stable connection.

    Args:
        bot: StealthBot instance (use within 'with StealthBot() as bot:' context)
        file_path: Path where the state JSON file will be saved
        encrypt: If True, encrypt the state file
        encryption_key: Optional encryption key

    Returns:
        Dictionary containing the saved state

    Example:
        >>> from sb_stealth_wrapper import StealthBot
        >>> from selenium_teleport import save_state_stealth
        >>>
        >>> with StealthBot() as bot:
        ...     bot.safe_get("https://example.com")
        ...     # ... login ...
        ...     save_state_stealth(bot, "state.json")
    """
    file_path = sanitize_file_path(file_path)

    logger.info(f"Saving browser state (stealth mode) to {file_path}")

    # Use bot.sb methods which stay connected
    sb = bot.sb

    # Get current URL
    try:
        current_url = sb.get_current_url()
    except Exception:
        current_url = "unknown"

    # Extract cookies via bot.sb.get_cookies()
    try:
        cookies = sb.get_cookies()
    except Exception as e:
        logger.warning(f"Failed to get cookies: {e}")
        cookies = []

    # Extract localStorage via bot.sb.execute_script()
    try:
        local_storage = (
            sb.execute_script(
                """
            var data = {};
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                data[key] = localStorage.getItem(key);
            }
            return data;
        """
            )
            or {}
        )
    except Exception as e:
        logger.warning(f"Failed to get localStorage: {e}")
        local_storage = {}

    # Extract sessionStorage via bot.sb.execute_script()
    try:
        session_storage = (
            sb.execute_script(
                """
            var data = {};
            for (var i = 0; i < sessionStorage.length; i++) {
                var key = sessionStorage.key(i);
                data[key] = sessionStorage.getItem(key);
            }
            return data;
        """
            )
            or {}
        )
    except Exception as e:
        logger.warning(f"Failed to get sessionStorage: {e}")
        session_storage = {}

    logger.debug(
        f"Extracted {len(cookies)} cookies, "
        f"{len(local_storage)} localStorage items, "
        f"{len(session_storage)} sessionStorage items"
    )

    state = {
        "metadata": {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "source_url": current_url,
            "source_domain": (
                extract_base_domain(current_url) if current_url != "unknown" else "unknown"
            ),
            "version": STATE_VERSION,
            "mode": "stealth",
            "encrypted": encrypt,
        },
        "cookies": cookies,
        "localStorage": local_storage,
        "sessionStorage": session_storage,
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


def load_state_stealth(
    bot,
    file_path: str,
    destination_url: str,
    validate_expiry: bool = True,
    validate_domain: bool = True,
    remove_expired: bool = True,
    encryption_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load browser state using StealthBot's bot.sb methods.

    This function works around an issue where bot.sb.driver becomes stale
    after navigation with challenge handling. It uses bot.sb methods which
    maintain a stable connection.

    Args:
        bot: StealthBot instance (use within 'with StealthBot() as bot:' context)
        file_path: Path to the state JSON file
        destination_url: The URL to navigate to after restoring state
        validate_expiry: If True, check for expired cookies
        validate_domain: If True, verify domain match
        remove_expired: If True, remove expired cookies
        encryption_key: Optional encryption key

    Returns:
        Dictionary containing the loaded state

    Example:
        >>> from sb_stealth_wrapper import StealthBot
        >>> from selenium_teleport import load_state_stealth
        >>>
        >>> with StealthBot() as bot:
        ...     load_state_stealth(bot, "state.json", "https://example.com/dashboard")
    """
    file_path = sanitize_file_path(file_path)

    if not os.path.exists(file_path):
        raise StateFileNotFoundError(file_path)

    logger.info(f"Loading browser state (stealth mode) from {file_path}")

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

    # Get config for validation settings
    config = get_config()
    validate_domain = validate_domain and config.validate_domain
    validate_expiry = validate_expiry and config.validate_expiry

    # Domain validation
    if validate_domain:
        source_domain = state.get("metadata", {}).get("source_domain", "")
        if source_domain and source_domain != "unknown":
            if not validate_domain_match(source_domain, destination_url):
                from .exceptions import DomainMismatchError

                raise DomainMismatchError(source_domain, destination_url)

    sb = bot.sb

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
    bot.safe_get(base_domain)

    # Inject cookies via bot.sb.add_cookie()
    logger.debug(f"Injecting {len(cookies)} cookies")
    for cookie in cookies:
        try:
            sanitized = sanitize_cookie(cookie)
            sb.add_cookie(sanitized)
        except Exception as e:
            logger.warning(f"Failed to add cookie '{cookie.get('name', 'unknown')}': {e}")

    # Inject localStorage via bot.sb.execute_script()
    if local_storage:
        try:
            for key, value in local_storage.items():
                escaped_value = json.dumps(value)
                sb.execute_script(f"localStorage.setItem({json.dumps(key)}, {escaped_value});")
        except Exception as e:
            logger.warning(f"Failed to inject localStorage: {e}")

    # Inject sessionStorage via bot.sb.execute_script()
    if session_storage:
        try:
            for key, value in session_storage.items():
                escaped_value = json.dumps(value)
                sb.execute_script(f"sessionStorage.setItem({json.dumps(key)}, {escaped_value});")
        except Exception as e:
            logger.warning(f"Failed to inject sessionStorage: {e}")

    # Teleport to final destination
    logger.info(f"Teleporting to: {destination_url}")
    bot.safe_get(destination_url)

    logger.info("State loaded and teleport complete!")

    return state
