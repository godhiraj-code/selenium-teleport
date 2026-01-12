"""
Selenium Teleport - Utility Functions

URL helpers and general utilities used across the library.
"""

from urllib.parse import urlparse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def extract_base_domain(url: str) -> str:
    """
    Extract the base domain from a URL.
    
    Example: 
        "https://example.com/checkout/v2" -> "https://example.com"
        "https://mail.google.com:8080/inbox" -> "https://mail.google.com:8080"
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent comparison.
    
    - Removes trailing slashes
    - Lowercases the scheme and host
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    
    normalized = f"{scheme}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


def get_domain_from_url(url: str) -> str:
    """
    Get just the domain/host from a URL.
    
    Example:
        "https://example.com:8080/path" -> "example.com"
    """
    parsed = urlparse(url)
    return parsed.netloc.split(":")[0]


def is_same_origin(url1: str, url2: str) -> bool:
    """
    Check if two URLs have the same origin (scheme + host + port).
    """
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)
    
    return (
        parsed1.scheme == parsed2.scheme
        and parsed1.netloc == parsed2.netloc
    )


def ensure_scheme(url: str, default_scheme: str = "https") -> str:
    """
    Ensure a URL has a scheme, adding default if missing.
    """
    if not url.startswith(("http://", "https://")):
        return f"{default_scheme}://{url}"
    return url
