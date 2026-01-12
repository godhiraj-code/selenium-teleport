"""
Selenium Teleport - Driver Creation Module

Functions for creating WebDriver instances with anti-detection measures.
"""

import logging
import os
from typing import Any, Optional

from .config import get_config
from .exceptions import DriverNotFoundError

logger = logging.getLogger(__name__)


def create_driver(
    profile_path: Optional[str] = None,
    headless: bool = False,
    browser: str = "chrome",
    use_undetected: bool = True,
    use_stealth_wrapper: bool = False,
    success_criteria: Optional[str] = None,
    proxy: Optional[str] = None,
) -> Any:
    """
    Create a WebDriver with persistent profile and anti-detection measures.

    By default, uses undetected-chromedriver for anti-detection.

    For sites with bot detection (Cloudflare, etc.), use use_stealth_wrapper=True
    which uses sb-stealth-wrapper for maximum stealth.

    Args:
        profile_path: Path to store browser profile. If None, creates a 'selenium_profile'
                     folder in the current directory. Use a consistent path to maintain
                     sessions across runs.
        headless: If True, run browser in headless mode. Note: some sites detect headless.
        browser: Browser to use - 'chrome' or 'edge'. Default is 'chrome'.
        use_undetected: If True (default), use undetected-chromedriver to bypass bot detection.
                       Set to False to use regular Selenium (for sites that don't need it).
        use_stealth_wrapper: If True, use sb-stealth-wrapper for maximum anti-detection.
                            Best for sites with strong bot detection (Cloudflare, etc.).
                            Returns a StealthBot instance instead of a WebDriver.
        success_criteria: (Stealth mode only) Text that confirms the page is fully loaded
                         and challenges are passed. E.g., "Dashboard", "Welcome".
        proxy: (Stealth mode only) Proxy in format user:pass@host:port.

    Returns:
        Configured WebDriver instance (or StealthBot if use_stealth_wrapper=True)

    Example:
        >>> from selenium_teleport import create_driver, Teleport
        >>>
        >>> # Standard approach with undetected-chromedriver
        >>> driver = create_driver(profile_path="my_profile")
        >>> driver.get("https://example.com")
        >>> driver.quit()
        >>>
        >>> # For sites with bot detection (Cloudflare, etc.)
        >>> with create_driver(use_stealth_wrapper=True, success_criteria="Welcome") as bot:
        ...     bot.safe_get("https://example.com")
    """
    # If stealth wrapper is requested, use sb-stealth-wrapper
    if use_stealth_wrapper:
        return _create_stealth_wrapper_driver(
            profile_path,
            headless,
            success_criteria=success_criteria,
            proxy=proxy,
        )

    # Set default profile path from config
    if profile_path is None:
        config = get_config()
        profile_path = os.path.join(os.getcwd(), config.default_profile_path)

    # Convert to absolute path
    profile_path = os.path.abspath(profile_path)

    logger.info(f"Using browser profile at: {profile_path}")

    if browser.lower() == "chrome":
        if use_undetected:
            return _create_undetected_chrome_driver(profile_path, headless)
        else:
            return _create_chrome_driver(profile_path, headless)
    elif browser.lower() == "edge":
        return _create_edge_driver(profile_path, headless)
    else:
        raise ValueError(f"Unsupported browser: {browser}. Use 'chrome' or 'edge'.")


def _create_stealth_wrapper_driver(
    profile_path: Optional[str],
    headless: bool,
    success_criteria: Optional[str] = None,
    proxy: Optional[str] = None,
) -> Any:
    """
    Create a StealthBot driver using sb-stealth-wrapper for maximum anti-detection.

    This is the best option for sites with strong bot detection (Cloudflare, DataDome, etc.).
    Returns a StealthBot context manager that can be used directly.

    Note: StealthBot uses SeleniumBase internally. To save/restore cookies:
        - Use bot.sb.save_cookies(name="session_name") to save
        - Use bot.sb.load_cookies(name="session_name") to restore
        - Cookies are saved to saved_cookies/<name>.txt
        - Use bot.sb.get_cookies() to inspect current cookies

    Args:
        profile_path: Optional path for browser profile (not used by StealthBot)
        headless: If True, run in headless mode (not recommended for stealth)
        success_criteria: Optional text that confirms page is fully loaded/unlocked
        proxy: Optional proxy in format user:pass@host:port

    Example:
        >>> from selenium_teleport import create_driver
        >>> import os
        >>>
        >>> with create_driver(use_stealth_wrapper=True) as bot:
        ...     bot.safe_get("https://news.ycombinator.com")
        ...
        ...     # Restore cookies if they exist
        ...     if os.path.exists("saved_cookies/hn_session.txt"):
        ...         bot.sb.load_cookies(name="hn_session")
        ...         bot.sb.refresh()
        ...
        ...     # ... do your work ...
        ...
        ...     # Save cookies for next time
        ...     bot.sb.save_cookies(name="hn_session")
    """
    try:
        from sb_stealth_wrapper import StealthBot
    except ImportError:
        logger.warning(
            "sb-stealth-wrapper not installed. Install with: pip install sb-stealth-wrapper"
        )
        logger.warning("Falling back to undetected-chromedriver.")
        if profile_path is None:
            config = get_config()
            profile_path = os.path.join(os.getcwd(), config.default_profile_path)
        return _create_undetected_chrome_driver(os.path.abspath(profile_path), headless)

    logger.info("Using StealthBot for maximum anti-detection")
    logger.info("To save/restore cookies, use bot.sb.save_cookies() and bot.sb.load_cookies()")

    # Create StealthBot with v0.4.0+ API
    # success_criteria: text that confirms challenges are passed
    bot = StealthBot(
        headless=headless,
        success_criteria=success_criteria,
        proxy=proxy,
        screenshot_path="debug_screenshots",
    )

    return bot


def _create_undetected_chrome_driver(profile_path: str, headless: bool) -> Any:
    """Create an undetected Chrome driver that bypasses bot detection."""
    try:
        import undetected_chromedriver as uc
    except ImportError:
        raise DriverNotFoundError("undetected-chromedriver", "pip install undetected-chromedriver")

    options = uc.ChromeOptions()

    # Persistent profile
    options.add_argument(f"--user-data-dir={profile_path}")

    # Performance
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    # undetected-chromedriver handles anti-detection automatically
    driver = uc.Chrome(options=options, use_subprocess=True)

    return driver


def _create_chrome_driver(profile_path: str, headless: bool) -> Any:
    """Create a Chrome driver with anti-detection measures."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()

    # Persistent profile - THIS IS THE KEY for universal compatibility
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")

    # Anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Performance and stability
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions-except=")
    options.add_argument("--disable-infobars")

    # Window settings
    options.add_argument("--start-maximized")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    # Remove webdriver property to avoid detection
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Hide automation indicators
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Spoof chrome object
            window.chrome = {
                runtime: {}
            };
        """
        },
    )

    return driver


def _create_edge_driver(profile_path: str, headless: bool) -> Any:
    """Create an Edge driver with anti-detection measures."""
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options

    options = Options()

    # Persistent profile
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")

    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Performance
    options.add_argument("--no-first-run")
    options.add_argument("--start-maximized")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Edge(options=options)

    return driver
