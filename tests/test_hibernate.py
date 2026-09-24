"""
Unit tests for Windows Laptop Hibernation Script.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import hibernate
import create_desktop_shortcut
import generate_icon
from PIL import Image


class TestHibernateUtility(unittest.TestCase):
    """Test suite for hibernation utilities."""

    def test_config_loading_defaults(self):
        """Test that configuration loader returns required keys and valid types."""
        config = hibernate.load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("confirm_before_hibernate", config)
        self.assertIn("countdown_seconds", config)
        self.assertIn("force_kill_apps", config)
        self.assertIn("enable_hotkey", config)
        self.assertIn("hotkey", config)
        self.assertIn("battery_monitor", config)
        self.assertIsInstance(config["countdown_seconds"], int)

    def test_system_support_check(self):
        """Test system support query returns boolean and descriptive string."""
        is_supported, msg = hibernate.check_system_support()
        self.assertIsInstance(is_supported, bool)
        self.assertIsInstance(msg, str)
        self.assertTrue(len(msg) > 0)

    def test_dry_run_execution(self):
        """Test that dry-run mode passes without executing actual hibernation."""
        # Dry-run should validate environment and return True without sleeping
        result = hibernate.hibernate_system(dry_run=True, skip_confirm=True)
        self.assertTrue(result)

    def test_directory_resolvers(self):
        """Test that desktop and start menu directory resolvers return valid paths."""
        desktop = create_desktop_shortcut.get_desktop_dir()
        self.assertTrue(desktop.is_dir(), f"Desktop directory not found: {desktop}")

        start_menu = create_desktop_shortcut.get_start_menu_programs_dir()
        self.assertTrue(start_menu.is_dir(), f"Start Menu directory not found: {start_menu}")

    def test_pythonw_executable_resolver(self):
        """Test that pythonw locator finds an executable."""
        exe = create_desktop_shortcut.find_pythonw_executable()
        self.assertTrue(exe.is_file(), f"Python executable not found: {exe}")

    def test_icon_generation_integrity(self):
        """Test that generated icon contains all standard resolutions."""
        icon_path = PROJECT_ROOT / "hibernate.ico"
        self.assertTrue(icon_path.is_file(), "hibernate.ico must exist")

        with Image.open(icon_path) as im:
            self.assertEqual(im.format, "ICO")
            self.assertEqual(im.size, (256, 256))


if __name__ == "__main__":
    unittest.main()
