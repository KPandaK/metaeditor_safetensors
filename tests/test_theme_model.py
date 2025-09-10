"""
Unit tests for Theme Model
==========================

Tests for theme directory loading, YAML configuration parsing,
and QSS file handling in the Theme model.
"""

import logging
import tempfile
import unittest
from pathlib import Path

from metaeditor_safetensors.models.theme import Theme


class TestThemeModel(unittest.TestCase):
    """Test cases for Theme model functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Suppress debug/info logging during tests for cleaner output
        logging.getLogger().setLevel(logging.ERROR)

        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up after each test."""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_theme_directory_with_yaml(self):
        """Test loading a theme from a valid directory with YAML config."""
        # Create a valid theme directory
        theme_dir = self.temp_dir / "valid_theme"
        theme_dir.mkdir()

        # Create a valid YAML config
        yaml_content = """
theme_id: "test_theme"
name: "Test Theme"
description: "A test theme for validation"
category: "dark"
version: "1.0.0"
qss_order:
  - "main.qss"
  - "widgets.qss"
settings:
  some_setting: "value"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        # Create some QSS files
        (theme_dir / "main.qss").write_text("/* Main styles */", encoding="utf-8")
        (theme_dir / "widgets.qss").write_text("/* Widget styles */", encoding="utf-8")

        # Load theme and validate
        theme = Theme.from_directory(theme_dir)

        self.assertEqual(theme.theme_id, "test_theme")
        self.assertEqual(theme.name, "Test Theme")
        self.assertEqual(theme.description, "A test theme for validation")
        self.assertEqual(theme.category, "dark")
        self.assertEqual(theme.version, "1.0.0")
        self.assertEqual(theme.qss_order, ["main.qss", "widgets.qss"])
        self.assertEqual(theme.settings, {"some_setting": "value"})
        self.assertEqual(theme.theme_directory, theme_dir)

    def test_theme_directory_without_yaml_fails(self):
        """Test that a directory without YAML file raises ValueError."""
        # Create a directory without YAML file
        theme_dir = self.temp_dir / "no_yaml_theme"
        theme_dir.mkdir()

        # Create some QSS files but no YAML
        (theme_dir / "main.qss").write_text("/* Main styles */", encoding="utf-8")

        # Should raise ValueError
        with self.assertRaises(ValueError) as cm:
            Theme.from_directory(theme_dir)

        self.assertIn("No YAML file found", str(cm.exception))

    def test_theme_directory_with_invalid_yaml_fails(self):
        """Test that a directory with invalid YAML raises ValueError."""
        # Create a theme directory
        theme_dir = self.temp_dir / "invalid_yaml_theme"
        theme_dir.mkdir()

        # Create an invalid YAML file
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("invalid: yaml: content: [unclosed", encoding="utf-8")

        # Should raise ValueError when YAML parsing fails
        with self.assertRaises(ValueError) as cm:
            Theme.from_directory(theme_dir)

        self.assertIn("Invalid YAML syntax", str(cm.exception))

    def test_theme_directory_with_empty_yaml_uses_defaults(self):
        """Test that empty YAML file uses reasonable defaults."""
        # Create a theme directory
        theme_dir = self.temp_dir / "empty_yaml_theme"
        theme_dir.mkdir()

        # Create an empty YAML file
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("", encoding="utf-8")

        # Create a QSS file
        (theme_dir / "style.qss").write_text("/* Some styles */", encoding="utf-8")

        # Load theme and check defaults
        theme = Theme.from_directory(theme_dir)

        self.assertEqual(theme.theme_id, "empty_yaml_theme")  # Uses directory name
        self.assertEqual(theme.name, "Unknown Theme")
        self.assertEqual(theme.category, "empty_yaml_theme")  # Uses theme_id as default
        self.assertEqual(theme.version, "1.0.0")
        self.assertEqual(theme.qss_order, ["style.qss"])  # Auto-discovered
        self.assertEqual(theme.settings, {})

    def test_theme_directory_with_minimal_yaml(self):
        """Test loading theme with minimal YAML configuration."""
        # Create a theme directory
        theme_dir = self.temp_dir / "minimal_theme"
        theme_dir.mkdir()

        # Create minimal YAML config
        yaml_content = """
name: "Minimal Theme"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        # Create QSS files
        (theme_dir / "base.qss").write_text("/* Base styles */", encoding="utf-8")
        (theme_dir / "advanced.qss").write_text(
            "/* Advanced styles */", encoding="utf-8"
        )

        # Load theme
        theme = Theme.from_directory(theme_dir)

        # Check that defaults are applied
        self.assertEqual(theme.theme_id, "minimal_theme")
        self.assertEqual(theme.name, "Minimal Theme")
        self.assertEqual(theme.category, "minimal_theme")
        self.assertEqual(theme.version, "1.0.0")
        # QSS files should be auto-discovered alphabetically
        self.assertEqual(theme.qss_order, ["advanced.qss", "base.qss"])

    def test_theme_qss_order_with_extra_files(self):
        """Test that extra QSS files not in qss_order are appended."""
        # Create a theme directory
        theme_dir = self.temp_dir / "ordered_theme"
        theme_dir.mkdir()

        # Create YAML with partial qss_order
        yaml_content = """
name: "Ordered Theme"
qss_order:
  - "main.qss"
  - "buttons.qss"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        # Create QSS files (including extras not in order)
        (theme_dir / "main.qss").write_text("/* Main */", encoding="utf-8")
        (theme_dir / "buttons.qss").write_text("/* Buttons */", encoding="utf-8")
        (theme_dir / "extra1.qss").write_text("/* Extra 1 */", encoding="utf-8")
        (theme_dir / "extra2.qss").write_text("/* Extra 2 */", encoding="utf-8")

        # Load theme
        theme = Theme.from_directory(theme_dir)

        # Check that specified order is maintained and extras are appended
        expected_order = ["main.qss", "buttons.qss", "extra1.qss", "extra2.qss"]
        self.assertEqual(theme.qss_order, expected_order)

    def test_get_qss_file_paths(self):
        """Test getting QSS file paths for file watching."""
        # Create a theme directory
        theme_dir = self.temp_dir / "paths_theme"
        theme_dir.mkdir()

        # Create YAML config
        yaml_content = """
name: "Paths Theme"
qss_order:
  - "first.qss"
  - "second.qss"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        # Create QSS files
        (theme_dir / "first.qss").write_text("/* First */", encoding="utf-8")
        (theme_dir / "second.qss").write_text("/* Second */", encoding="utf-8")

        # Load theme and get paths
        theme = Theme.from_directory(theme_dir)
        paths = theme.get_qss_file_paths()

        expected_paths = [theme_dir / "first.qss", theme_dir / "second.qss"]
        self.assertEqual(paths, expected_paths)

    def test_qss_content_loading_and_caching(self):
        """Test QSS content loading and caching behavior."""
        # Create a theme directory
        theme_dir = self.temp_dir / "qss_test_theme"
        theme_dir.mkdir()

        # Create YAML config
        yaml_content = """
name: "QSS Test Theme"
qss_order:
  - "first.qss"
  - "second.qss"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        # Create QSS files with specific content
        (theme_dir / "first.qss").write_text(
            "/* First file content */", encoding="utf-8"
        )
        (theme_dir / "second.qss").write_text(
            "/* Second file content */", encoding="utf-8"
        )

        # Load theme
        theme = Theme.from_directory(theme_dir)

        # Get QSS content (should load and cache)
        qss_content = theme.get_qss()

        # Verify content includes both files
        self.assertIn("/* From: first.qss */", qss_content)
        self.assertIn("/* First file content */", qss_content)
        self.assertIn("/* From: second.qss */", qss_content)
        self.assertIn("/* Second file content */", qss_content)

        # Get QSS content again (should use cache)
        qss_content_cached = theme.get_qss()
        self.assertEqual(qss_content, qss_content_cached)

        # Clear cache and get content again
        theme.clear_cache()
        qss_content_after_clear = theme.get_qss()
        self.assertEqual(qss_content, qss_content_after_clear)

    def test_theme_without_directory_returns_empty_qss(self):
        """Test that theme without directory returns empty QSS."""
        theme = Theme("test", "Test Theme", "test", None)
        self.assertEqual(theme.get_qss(), "")
        self.assertEqual(theme.get_qss_file_paths(), [])


if __name__ == "__main__":
    unittest.main()
