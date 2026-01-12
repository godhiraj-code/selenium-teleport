"""
Tests for utility functions.
"""

import pytest


class TestUrlHelpers:
    """Tests for URL helper functions."""
    
    def test_extract_base_domain(self):
        """Test base domain extraction."""
        from selenium_teleport.utils import extract_base_domain
        
        assert extract_base_domain("https://example.com/path/to/page") == "https://example.com"
        assert extract_base_domain("http://localhost:8080/api") == "http://localhost:8080"
        assert extract_base_domain("https://sub.domain.com:443/") == "https://sub.domain.com:443"
    
    def test_normalize_url(self):
        """Test URL normalization."""
        from selenium_teleport.utils import normalize_url
        
        assert normalize_url("HTTPS://EXAMPLE.COM/path/") == "https://example.com/path"
        assert normalize_url("http://test.com") == "http://test.com/"
    
    def test_get_domain_from_url(self):
        """Test domain extraction without port."""
        from selenium_teleport.utils import get_domain_from_url
        
        assert get_domain_from_url("https://example.com:8080/path") == "example.com"
        assert get_domain_from_url("http://localhost/") == "localhost"
    
    def test_is_same_origin(self):
        """Test same origin checking."""
        from selenium_teleport.utils import is_same_origin
        
        assert is_same_origin(
            "https://example.com/path1",
            "https://example.com/path2"
        ) is True
        
        assert is_same_origin(
            "https://example.com",
            "http://example.com"  # Different scheme
        ) is False
        
        assert is_same_origin(
            "https://example.com",
            "https://other.com"
        ) is False
    
    def test_ensure_scheme(self):
        """Test scheme addition."""
        from selenium_teleport.utils import ensure_scheme
        
        assert ensure_scheme("example.com") == "https://example.com"
        assert ensure_scheme("http://example.com") == "http://example.com"
        assert ensure_scheme("example.com", "http") == "http://example.com"
