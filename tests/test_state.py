"""
Tests for state management module.
"""

import json
import os
import pytest


class TestSaveState:
    """Tests for save_state function."""
    
    def test_save_state_creates_file(self, mock_driver, temp_dir):
        """Test that save_state creates a state file."""
        from selenium_teleport.state import save_state
        
        file_path = os.path.join(temp_dir, "test_state.json")
        state = save_state(mock_driver, file_path)
        
        assert os.path.exists(file_path)
        assert "cookies" in state
        assert "localStorage" in state
        assert "sessionStorage" in state
        assert "metadata" in state
    
    def test_save_state_metadata(self, mock_driver, temp_dir):
        """Test that metadata is correctly populated."""
        from selenium_teleport.state import save_state
        
        file_path = os.path.join(temp_dir, "test_state.json")
        state = save_state(mock_driver, file_path)
        
        assert "saved_at" in state["metadata"]
        assert "source_url" in state["metadata"]
        assert "source_domain" in state["metadata"]
        assert state["metadata"]["version"] == "2.1"
    
    def test_save_state_encrypted(self, mock_driver, temp_dir, encryption_key):
        """Test saving encrypted state."""
        from selenium_teleport.state import save_state
        from selenium_teleport.security import is_encrypted
        
        file_path = os.path.join(temp_dir, "test_state.enc")
        save_state(mock_driver, file_path, encrypt=True, encryption_key=encryption_key)
        
        with open(file_path, "rb") as f:
            content = f.read()
        
        assert is_encrypted(content)


class TestLoadState:
    """Tests for load_state function."""
    
    def test_load_state_basic(self, mock_driver, state_file, sample_state):
        """Test basic state loading."""
        from selenium_teleport.state import load_state
        
        loaded = load_state(
            mock_driver,
            state_file,
            "https://example.com/dashboard",
            validate_domain=False,
        )
        
        assert loaded["metadata"]["source_url"] == sample_state["metadata"]["source_url"]
    
    def test_load_state_navigates(self, mock_driver, state_file):
        """Test that load_state navigates to destination."""
        from selenium_teleport.state import load_state
        
        load_state(
            mock_driver,
            state_file,
            "https://example.com/dashboard",
            validate_domain=False,
        )
        
        # Should navigate to base domain then destination
        assert mock_driver.get.call_count >= 2
    
    def test_load_state_file_not_found(self, mock_driver, temp_dir):
        """Test error when state file doesn't exist."""
        from selenium_teleport.state import load_state
        from selenium_teleport.exceptions import StateFileNotFoundError
        
        with pytest.raises(StateFileNotFoundError):
            load_state(
                mock_driver,
                os.path.join(temp_dir, "nonexistent.json"),
                "https://example.com",
            )
    
    def test_load_state_domain_mismatch(self, mock_driver, state_file):
        """Test domain validation failure."""
        from selenium_teleport.state import load_state
        from selenium_teleport.exceptions import DomainMismatchError
        
        with pytest.raises(DomainMismatchError):
            load_state(
                mock_driver,
                state_file,
                "https://evil.com/steal",
                validate_domain=True,
            )


class TestStateInfo:
    """Tests for get_state_info function."""
    
    def test_get_state_info(self, state_file, sample_state):
        """Test getting state file info."""
        from selenium_teleport.state import get_state_info
        
        info = get_state_info(state_file)
        
        assert info["encrypted"] is False
        assert info["cookie_count"] == len(sample_state["cookies"])
        assert info["source_domain"] == sample_state["metadata"]["source_domain"]


class TestDeleteState:
    """Tests for delete_state function."""
    
    def test_delete_state(self, temp_dir, sample_state):
        """Test secure state deletion."""
        from selenium_teleport.state import delete_state
        
        file_path = os.path.join(temp_dir, "to_delete.json")
        with open(file_path, "w") as f:
            json.dump(sample_state, f)
        
        assert os.path.exists(file_path)
        
        delete_state(file_path, secure=True)
        
        assert not os.path.exists(file_path)
    
    def test_delete_nonexistent_no_error(self, temp_dir):
        """Test that deleting nonexistent file doesn't raise error."""
        from selenium_teleport.state import delete_state
        
        file_path = os.path.join(temp_dir, "nonexistent.json")
        delete_state(file_path)  # Should not raise
