"""
Selenium Teleport - Context Managers

Provides context managers for automatic state management.
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from .exceptions import SecurityError
from .security import sanitize_file_path
from .state import load_state, save_state

logger = logging.getLogger(__name__)


class Teleport:
    """
    Context manager for automatic state saving on successful exit.

    This context manager will automatically save the browser state when
    the context exits without an exception (i.e., when the test passes).

    For best results, use with a driver created via create_driver().

    Example:
        >>> from selenium_teleport import create_driver, Teleport
        >>>
        >>> driver = create_driver(profile_path="my_profile")
        >>> with Teleport(driver, "session_state.json") as teleport:
        ...     if teleport.has_state():
        ...         teleport.load("https://news.ycombinator.com")
        ...     else:
        ...         driver.get("https://news.ycombinator.com/login")
        ...         # ... manual login ...
        ...
        ...     # Do your testing
        ... # State is automatically saved on successful exit
        >>> driver.quit()
    """

    def __init__(
        self,
        driver,
        file_path: str,
        auto_save: bool = True,
        encrypt: bool = False,
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize the Teleport context manager.

        Args:
            driver: Selenium WebDriver instance (use create_driver() for best results)
            file_path: Path for saving/loading state
            auto_save: If True, automatically save state on successful exit
            encrypt: If True, encrypt saved state files
            encryption_key: Optional encryption key
        """
        self.driver = driver
        self.file_path = sanitize_file_path(file_path)
        self.auto_save = auto_save
        self.encrypt = encrypt
        self.encryption_key = encryption_key
        self._state: Optional[Dict[str, Any]] = None

    def __enter__(self) -> "Teleport":
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager. Saves state if no exception occurred."""
        if exc_type is None and self.auto_save:
            try:
                save_state(
                    self.driver,
                    self.file_path,
                    encrypt=self.encrypt,
                    encryption_key=self.encryption_key,
                )
                logger.info("Auto-saved state on successful exit")
            except Exception as e:
                logger.error(f"Failed to auto-save state: {e}")

    def has_state(self) -> bool:
        """Check if a state file exists."""
        return os.path.exists(self.file_path)

    def load(
        self,
        destination_url: str,
        validate_expiry: bool = True,
        validate_domain: bool = True,
    ) -> Dict[str, Any]:
        """
        Load state and teleport to the destination URL.

        Args:
            destination_url: URL to navigate to after loading state
            validate_expiry: If True, validate token expiry
            validate_domain: If True, validate domain match

        Returns:
            Loaded state dictionary
        """
        self._state = load_state(
            self.driver,
            self.file_path,
            destination_url,
            validate_expiry=validate_expiry,
            validate_domain=validate_domain,
            encryption_key=self.encryption_key,
        )
        return self._state

    def save(self) -> Dict[str, Any]:
        """Manually save the current state."""
        self._state = save_state(
            self.driver,
            self.file_path,
            encrypt=self.encrypt,
            encryption_key=self.encryption_key,
        )
        return self._state

    @property
    def state(self) -> Optional[Dict[str, Any]]:
        """Get the current state (if loaded or saved)."""
        return self._state


@contextmanager
def teleport_session(
    driver,
    file_path: str,
    destination_url: Optional[str] = None,
    encrypt: bool = False,
    encryption_key: Optional[str] = None,
):
    """
    Functional context manager alternative to the Teleport class.

    If a state file exists and destination_url is provided, the state
    will be loaded automatically on entry. State is saved on successful exit.

    Args:
        driver: Selenium WebDriver instance
        file_path: Path for state file
        destination_url: Optional URL to teleport to if state exists
        encrypt: If True, encrypt saved state
        encryption_key: Optional encryption key

    Yields:
        Loaded state dictionary (empty if no existing state)

    Example:
        >>> from selenium_teleport import create_driver, teleport_session
        >>>
        >>> driver = create_driver()
        >>> with teleport_session(driver, "state.json", "https://example.com/dashboard") as state:
        ...     if not state:
        ...         driver.get("https://example.com/login")
        ...         # ... login process ...
        ... # State auto-saved on exit
    """
    file_path = sanitize_file_path(file_path)
    state = {}

    if destination_url and os.path.exists(file_path):
        try:
            state = load_state(
                driver,
                file_path,
                destination_url,
                encryption_key=encryption_key,
            )
            logger.info("Loaded existing state")
        except SecurityError:
            raise
        except Exception as e:
            logger.warning(f"Failed to load state, starting fresh: {e}")

    try:
        yield state
        save_state(
            driver,
            file_path,
            encrypt=encrypt,
            encryption_key=encryption_key,
        )
        logger.info("Saved state on successful exit")
    except Exception:
        raise
