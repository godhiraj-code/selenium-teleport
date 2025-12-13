"""
Selenium Teleport - Core Implementation

Save and restore browser state (Cookies, LocalStorage, SessionStorage)
to skip login screens and setup flows.

Note: Session persistence varies by site. Some sites use complex authentication
that may not persist with cookies alone.
"""

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# =============================================================================
# Driver Creation with Anti-Detection
# =============================================================================

def create_driver(
    profile_path: Optional[str] = None,
    headless: bool = False,
    browser: str = "chrome",
    use_undetected: bool = True,
    use_stealth_wrapper: bool = False,
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
        >>> with create_driver(use_stealth_wrapper=True) as bot:
        ...     bot.safe_get("https://example.com")
    """
    # If stealth wrapper is requested, use sb-stealth-wrapper
    if use_stealth_wrapper:
        return _create_stealth_wrapper_driver(profile_path, headless)
    
    # Set default profile path
    if profile_path is None:
        profile_path = os.path.join(os.getcwd(), "selenium_profile")
    
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


def _create_stealth_wrapper_driver(profile_path: Optional[str], headless: bool) -> Any:
    """
    Create a StealthBot driver using sb-stealth-wrapper for maximum anti-detection.
    
    This is the best option for sites with strong bot detection (Cloudflare, DataDome, etc.).
    Returns a StealthBot context manager that can be used directly.
    
    Note: StealthBot uses SeleniumBase internally. To save/restore cookies:
        - Use bot.sb.save_cookies(name="session_name") to save
        - Use bot.sb.load_cookies(name="session_name") to restore
        - Cookies are saved to saved_cookies/<name>.txt
        - Use bot.sb.get_cookies() to inspect current cookies
    
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
        logger.warning("sb-stealth-wrapper not installed. Install with: pip install sb-stealth-wrapper")
        logger.warning("Falling back to undetected-chromedriver.")
        if profile_path is None:
            profile_path = os.path.join(os.getcwd(), "selenium_profile")
        return _create_undetected_chrome_driver(os.path.abspath(profile_path), headless)
    
    logger.info("Using StealthBot for maximum anti-detection")
    logger.info("To save/restore cookies, use bot.sb.save_cookies() and bot.sb.load_cookies()")
    
    # Create StealthBot - it handles all the anti-detection internally
    # Note: StealthBot uses xvfb on Linux, handles challenges, etc.
    bot = StealthBot(headless=headless)
    
    return bot


def _create_undetected_chrome_driver(profile_path: str, headless: bool) -> Any:
    """Create an undetected Chrome driver that bypasses bot detection."""
    try:
        import undetected_chromedriver as uc
    except ImportError:
        logger.warning("undetected-chromedriver not installed. Install with: pip install undetected-chromedriver")
        logger.warning("Falling back to regular Chrome driver.")
        return _create_chrome_driver(profile_path, headless)
    
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
    from selenium.webdriver.chrome.service import Service
    
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
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
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
    })
    
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


# =============================================================================
# URL Helpers
# =============================================================================

def _extract_base_domain(url: str) -> str:
    """
    Extract the base domain from a URL.
    
    Example: "https://example.com/checkout/v2" -> "https://example.com"
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


# =============================================================================
# Storage Extraction and Injection
# =============================================================================

def _get_storage(driver, storage_type: str) -> Dict[str, Any]:
    """Extract localStorage or sessionStorage from the browser."""
    try:
        script = f"""
            var storage = window.{storage_type};
            var data = {{}};
            for (var i = 0; i < storage.length; i++) {{
                var key = storage.key(i);
                data[key] = storage.getItem(key);
            }}
            return data;
        """
        return driver.execute_script(script) or {}
    except Exception as e:
        logger.warning(f"Failed to extract {storage_type}: {e}")
        return {}


def _set_storage(driver, storage_type: str, data: Dict[str, Any]) -> None:
    """Inject data into localStorage or sessionStorage."""
    if not data:
        return
    
    try:
        for key, value in data.items():
            escaped_value = json.dumps(value)
            script = f"window.{storage_type}.setItem({json.dumps(key)}, {escaped_value});"
            driver.execute_script(script)
    except Exception as e:
        logger.warning(f"Failed to inject {storage_type}: {e}")


def _get_indexeddb(driver) -> Dict[str, Any]:
    """
    Extract IndexedDB data from the browser.
    
    This captures additional auth tokens used by modern web apps like Google.
    Note: This is a best-effort extraction - some complex data may not serialize.
    """
    try:
        script = """
            return new Promise((resolve) => {
                const dbData = {};
                
                if (!window.indexedDB) {
                    resolve(dbData);
                    return;
                }
                
                // Get list of databases
                if (indexedDB.databases) {
                    indexedDB.databases().then(databases => {
                        if (databases.length === 0) {
                            resolve(dbData);
                            return;
                        }
                        
                        let completed = 0;
                        databases.forEach(dbInfo => {
                            const dbName = dbInfo.name;
                            const request = indexedDB.open(dbName);
                            
                            request.onerror = () => {
                                completed++;
                                if (completed === databases.length) resolve(dbData);
                            };
                            
                            request.onsuccess = (event) => {
                                const db = event.target.result;
                                dbData[dbName] = {
                                    version: db.version,
                                    stores: Array.from(db.objectStoreNames)
                                };
                                db.close();
                                completed++;
                                if (completed === databases.length) resolve(dbData);
                            };
                        });
                    }).catch(() => resolve(dbData));
                } else {
                    resolve(dbData);
                }
            });
        """
        result = driver.execute_script(script)
        return result if result else {}
    except Exception as e:
        logger.debug(f"IndexedDB extraction not available: {e}")
        return {}


def _sanitize_cookie(cookie: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a cookie for injection, handling edge cases.
    
    - Converts float 'expiry' to int (Selenium requirement)
    - Handles problematic 'sameSite' attribute
    """
    sanitized = cookie.copy()
    
    # Handle expiry - must be an integer
    if 'expiry' in sanitized:
        try:
            sanitized['expiry'] = int(sanitized['expiry'])
        except (ValueError, TypeError):
            del sanitized['expiry']
    
    # Handle sameSite attribute
    if 'sameSite' in sanitized:
        same_site = sanitized['sameSite']
        if same_site not in ('Strict', 'Lax', 'None'):
            if isinstance(same_site, str):
                same_site_lower = same_site.lower()
                if same_site_lower == 'strict':
                    sanitized['sameSite'] = 'Strict'
                elif same_site_lower == 'lax':
                    sanitized['sameSite'] = 'Lax'
                elif same_site_lower == 'none':
                    sanitized['sameSite'] = 'None'
                else:
                    del sanitized['sameSite']
            else:
                del sanitized['sameSite']
    
    # Clean None values
    if sanitized.get('httpOnly') is None:
        sanitized.pop('httpOnly', None)
    if sanitized.get('secure') is None:
        sanitized.pop('secure', None)
    
    return sanitized


# =============================================================================
# Main API Functions
# =============================================================================

def save_state(driver, file_path: str) -> Dict[str, Any]:
    """
    Extract and save browser state (Cookies, LocalStorage, SessionStorage) to a JSON file.
    
    For best results, use with a driver created via create_driver() which uses
    a persistent Chrome profile for maximum compatibility.
    
    Args:
        driver: Selenium WebDriver instance
        file_path: Path where the state JSON file will be saved
        
    Returns:
        Dictionary containing the saved state
        
    Example:
        >>> from selenium_teleport import create_driver, save_state
        >>> 
        >>> driver = create_driver()
        >>> driver.get("https://example.com")
        >>> # ... login process ...
        >>> save_state(driver, "session_state.json")
    """
    logger.info(f"Saving browser state to {file_path}")
    
    current_url = driver.current_url
    
    # Extract all storage types
    cookies = driver.get_cookies()
    local_storage = _get_storage(driver, 'localStorage')
    session_storage = _get_storage(driver, 'sessionStorage')
    indexeddb_info = _get_indexeddb(driver)
    
    logger.debug(f"Extracted {len(cookies)} cookies, "
                 f"{len(local_storage)} localStorage items, "
                 f"{len(session_storage)} sessionStorage items")
    
    state = {
        'metadata': {
            'saved_at': datetime.utcnow().isoformat(),
            'source_url': current_url,
            'source_domain': _extract_base_domain(current_url),
            'version': '2.0',
        },
        'cookies': cookies,
        'localStorage': local_storage,
        'sessionStorage': session_storage,
        'indexedDB': indexeddb_info,
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    logger.info(f"State saved successfully to {file_path}")
    
    return state


def load_state(driver, file_path: str, destination_url: str) -> Dict[str, Any]:
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
        
    Returns:
        Dictionary containing the loaded state
        
    Example:
        >>> from selenium_teleport import create_driver, load_state
        >>> 
        >>> driver = create_driver()
        >>> load_state(driver, "session_state.json", "https://example.com/dashboard")
    """
    logger.info(f"Loading browser state from {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    cookies = state.get('cookies', [])
    local_storage = state.get('localStorage', {})
    session_storage = state.get('sessionStorage', {})
    
    # Navigate to base domain first (Same-Origin Policy)
    base_domain = _extract_base_domain(destination_url)
    logger.info(f"Navigating to base domain: {base_domain}")
    driver.get(base_domain)
    
    # Inject cookies
    logger.debug(f"Injecting {len(cookies)} cookies")
    for cookie in cookies:
        try:
            sanitized = _sanitize_cookie(cookie)
            driver.add_cookie(sanitized)
        except Exception as e:
            logger.warning(f"Failed to add cookie '{cookie.get('name', 'unknown')}': {e}")
    
    # Inject storage
    _set_storage(driver, 'localStorage', local_storage)
    _set_storage(driver, 'sessionStorage', session_storage)
    
    # Teleport to final destination
    logger.info(f"Teleporting to: {destination_url}")
    driver.get(destination_url)
    
    logger.info("State loaded and teleport complete!")
    
    return state


# =============================================================================
# StealthBot-Compatible State Functions
# =============================================================================

def save_state_stealth(bot, file_path: str) -> Dict[str, Any]:
    """
    Save browser state using StealthBot's bot.sb methods.
    
    This function works around an issue where bot.sb.driver becomes stale
    after navigation with challenge handling. It uses bot.sb methods which
    maintain a stable connection.
    
    Args:
        bot: StealthBot instance (use within 'with StealthBot() as bot:' context)
        file_path: Path where the state JSON file will be saved
        
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
        local_storage = sb.execute_script("""
            var data = {};
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                data[key] = localStorage.getItem(key);
            }
            return data;
        """) or {}
    except Exception as e:
        logger.warning(f"Failed to get localStorage: {e}")
        local_storage = {}
    
    # Extract sessionStorage via bot.sb.execute_script()
    try:
        session_storage = sb.execute_script("""
            var data = {};
            for (var i = 0; i < sessionStorage.length; i++) {
                var key = sessionStorage.key(i);
                data[key] = sessionStorage.getItem(key);
            }
            return data;
        """) or {}
    except Exception as e:
        logger.warning(f"Failed to get sessionStorage: {e}")
        session_storage = {}
    
    logger.debug(f"Extracted {len(cookies)} cookies, "
                 f"{len(local_storage)} localStorage items, "
                 f"{len(session_storage)} sessionStorage items")
    
    state = {
        'metadata': {
            'saved_at': datetime.utcnow().isoformat(),
            'source_url': current_url,
            'source_domain': _extract_base_domain(current_url) if current_url != "unknown" else "unknown",
            'version': '2.0',
            'mode': 'stealth',
        },
        'cookies': cookies,
        'localStorage': local_storage,
        'sessionStorage': session_storage,
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    logger.info(f"State saved successfully to {file_path}")
    
    return state


def load_state_stealth(bot, file_path: str, destination_url: str) -> Dict[str, Any]:
    """
    Load browser state using StealthBot's bot.sb methods.
    
    This function works around an issue where bot.sb.driver becomes stale
    after navigation with challenge handling. It uses bot.sb methods which
    maintain a stable connection.
    
    Args:
        bot: StealthBot instance (use within 'with StealthBot() as bot:' context)
        file_path: Path to the state JSON file
        destination_url: The URL to navigate to after restoring state
        
    Returns:
        Dictionary containing the loaded state
        
    Example:
        >>> from sb_stealth_wrapper import StealthBot
        >>> from selenium_teleport import load_state_stealth
        >>> 
        >>> with StealthBot() as bot:
        ...     load_state_stealth(bot, "state.json", "https://example.com/dashboard")
    """
    logger.info(f"Loading browser state (stealth mode) from {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    sb = bot.sb
    
    cookies = state.get('cookies', [])
    local_storage = state.get('localStorage', {})
    session_storage = state.get('sessionStorage', {})
    
    # Navigate to base domain first (Same-Origin Policy)
    base_domain = _extract_base_domain(destination_url)
    logger.info(f"Navigating to base domain: {base_domain}")
    bot.safe_get(base_domain)
    
    # Inject cookies via bot.sb.add_cookie()
    logger.debug(f"Injecting {len(cookies)} cookies")
    for cookie in cookies:
        try:
            sanitized = _sanitize_cookie(cookie)
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


# =============================================================================
# Context Managers
# =============================================================================

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
    
    def __init__(self, driver, file_path: str, auto_save: bool = True):
        """
        Initialize the Teleport context manager.
        
        Args:
            driver: Selenium WebDriver instance (use create_driver() for best results)
            file_path: Path for saving/loading state
            auto_save: If True, automatically save state on successful exit
        """
        self.driver = driver
        self.file_path = file_path
        self.auto_save = auto_save
        self._state: Optional[Dict[str, Any]] = None
    
    def __enter__(self) -> 'Teleport':
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the context manager. Saves state if no exception occurred."""
        if exc_type is None and self.auto_save:
            try:
                save_state(self.driver, self.file_path)
                logger.info("Auto-saved state on successful exit")
            except Exception as e:
                logger.error(f"Failed to auto-save state: {e}")
        return False
    
    def has_state(self) -> bool:
        """Check if a state file exists."""
        return os.path.exists(self.file_path)
    
    def load(self, destination_url: str) -> Dict[str, Any]:
        """Load state and teleport to the destination URL."""
        self._state = load_state(self.driver, self.file_path, destination_url)
        return self._state
    
    def save(self) -> Dict[str, Any]:
        """Manually save the current state."""
        self._state = save_state(self.driver, self.file_path)
        return self._state
    
    @property
    def state(self) -> Optional[Dict[str, Any]]:
        """Get the current state (if loaded or saved)."""
        return self._state


@contextmanager
def teleport_session(driver, file_path: str, destination_url: Optional[str] = None):
    """
    Functional context manager alternative to the Teleport class.
    
    If a state file exists and destination_url is provided, the state
    will be loaded automatically on entry. State is saved on successful exit.
    
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
    state = {}
    
    if destination_url and os.path.exists(file_path):
        try:
            state = load_state(driver, file_path, destination_url)
            logger.info("Loaded existing state")
        except Exception as e:
            logger.warning(f"Failed to load state, starting fresh: {e}")
    
    try:
        yield state
        save_state(driver, file_path)
        logger.info("Saved state on successful exit")
    except Exception:
        raise
