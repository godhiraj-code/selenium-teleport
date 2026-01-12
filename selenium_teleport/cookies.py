"""
Selenium Teleport - Cookie Utilities

Functions for cookie handling, sanitization, and manipulation.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def sanitize_cookie(cookie: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a cookie for injection, handling edge cases.
    
    - Converts float 'expiry' to int (Selenium requirement)
    - Handles problematic 'sameSite' attribute
    - Removes None values that cause issues
    
    Args:
        cookie: Raw cookie dictionary
        
    Returns:
        Sanitized cookie dictionary safe for driver.add_cookie()
    """
    sanitized = cookie.copy()
    
    # Handle expiry - must be an integer
    if "expiry" in sanitized:
        try:
            sanitized["expiry"] = int(sanitized["expiry"])
        except (ValueError, TypeError):
            del sanitized["expiry"]
    
    # Handle sameSite attribute
    if "sameSite" in sanitized:
        same_site = sanitized["sameSite"]
        if same_site not in ("Strict", "Lax", "None"):
            if isinstance(same_site, str):
                same_site_lower = same_site.lower()
                if same_site_lower == "strict":
                    sanitized["sameSite"] = "Strict"
                elif same_site_lower == "lax":
                    sanitized["sameSite"] = "Lax"
                elif same_site_lower == "none":
                    sanitized["sameSite"] = "None"
                else:
                    del sanitized["sameSite"]
            else:
                del sanitized["sameSite"]
    
    # Clean None values that cause issues
    if sanitized.get("httpOnly") is None:
        sanitized.pop("httpOnly", None)
    if sanitized.get("secure") is None:
        sanitized.pop("secure", None)
    
    return sanitized


def inject_cookies(driver, cookies: List[Dict[str, Any]]) -> int:
    """
    Inject a list of cookies into the browser.
    
    Args:
        driver: Selenium WebDriver instance
        cookies: List of cookie dictionaries
        
    Returns:
        Number of successfully injected cookies
    """
    success_count = 0
    
    for cookie in cookies:
        try:
            sanitized = sanitize_cookie(cookie)
            driver.add_cookie(sanitized)
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to add cookie '{cookie.get('name', 'unknown')}': {e}")
    
    logger.debug(f"Injected {success_count}/{len(cookies)} cookies")
    return success_count


def extract_cookies(driver) -> List[Dict[str, Any]]:
    """
    Extract all cookies from the browser.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of cookie dictionaries
    """
    try:
        return driver.get_cookies()
    except Exception as e:
        logger.warning(f"Failed to extract cookies: {e}")
        return []


def filter_cookies_by_domain(cookies: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    """
    Filter cookies to only those matching a domain.
    
    Args:
        cookies: List of cookie dictionaries
        domain: Domain to filter by (e.g., "example.com")
        
    Returns:
        Filtered list of cookies
    """
    filtered = []
    domain_lower = domain.lower()
    
    for cookie in cookies:
        cookie_domain = cookie.get("domain", "").lower()
        # Match exact domain or subdomain
        if cookie_domain == domain_lower or cookie_domain.endswith(f".{domain_lower}"):
            filtered.append(cookie)
    
    return filtered


def get_auth_cookies(cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter cookies to only those likely to be authentication cookies.
    
    Looks for common auth cookie naming patterns.
    
    Args:
        cookies: List of cookie dictionaries
        
    Returns:
        Filtered list of likely auth cookies
    """
    auth_patterns = [
        "session", "auth", "token", "jwt", "sid", "ssid",
        "login", "user", "credential", "access", "refresh",
    ]
    
    auth_cookies = []
    for cookie in cookies:
        name = cookie.get("name", "").lower()
        if any(pattern in name for pattern in auth_patterns):
            auth_cookies.append(cookie)
    
    return auth_cookies
