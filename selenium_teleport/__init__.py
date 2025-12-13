"""
Selenium Teleport
=================

Save and restore browser state (Cookies, LocalStorage, SessionStorage) to
skip login screens and setup flows in Selenium automation scripts.

Features:
    - Persistent Chrome profile for maximum compatibility
    - Anti-detection measures built-in
    - Save complete browser state to a JSON file
    - Restore state and "teleport" to any authenticated page
    - Context manager for automatic state management
    - StealthBot-compatible functions for sb-stealth-wrapper

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
"""

__version__ = "2.0.0"
__author__ = "Selenium Teleport Contributors"
__license__ = "MIT"

from .core import (
    # Main driver creation
    create_driver,
    # Core functions
    save_state,
    load_state,
    # StealthBot-compatible functions
    save_state_stealth,
    load_state_stealth,
    # Context managers
    Teleport,
    teleport_session,
)

__all__ = [
    "create_driver",
    "save_state",
    "load_state",
    "save_state_stealth",
    "load_state_stealth",
    "Teleport",
    "teleport_session",
    "__version__",
]

