"""Tests for driver selection defaults."""

import inspect

from selenium_teleport.drivers import create_driver


def test_regular_selenium_is_the_dependency_safe_default():
    """The base install must not default to an optional driver package."""
    signature = inspect.signature(create_driver)

    assert signature.parameters["use_undetected"].default is False
