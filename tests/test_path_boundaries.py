import os

import pytest

from selenium_teleport.exceptions import PathTraversalError
from selenium_teleport.security import sanitize_file_path


def test_base_directory_rejects_sibling_with_shared_prefix(tmp_path):
    base = tmp_path / "sessions"
    outside = tmp_path / "sessions-other" / "token.json"
    with pytest.raises(PathTraversalError):
        sanitize_file_path(str(outside), str(base))
    inside = base / "token.json"
    assert sanitize_file_path(str(inside), str(base)) == os.path.realpath(inside)


def test_base_directory_rejects_symlink_escape(tmp_path):
    base = tmp_path / "sessions"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (base / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlink creation is unavailable")
    with pytest.raises(PathTraversalError):
        sanitize_file_path(str(base / "linked" / "token.json"), str(base))
