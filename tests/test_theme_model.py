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

    def test_infer_category_light_themes(self):
        """Test that _infer_category correctly identifies light themes."""
        light_ids = ["light_theme", "bright_ui", "white_background", "LIGHT-MODE"]
        for theme_id in light_ids:
            with self.subTest(theme_id=theme_id):
                category = Theme._infer_category(theme_id)
                self.assertEqual(category, "light", f"Theme ID '{theme_id}' should be categorized as light")

    def test_infer_category_dark_themes(self):
        """Test that _infer_category correctly identifies dark themes."""
        dark_ids = ["dark_theme", "night_mode", "black_ui", "DARK-THEME"]
        for theme_id in dark_ids:
            with self.subTest(theme_id=theme_id):
                category = Theme._infer_category(theme_id)
                self.assertEqual(category, "dark", f"Theme ID '{theme_id}' should be categorized as dark")

    def test_infer_category_defaults_to_dark(self):
        """Test that _infer_category defaults to dark for ambiguous names."""
        ambiguous_ids = ["my_theme", "custom", "beautiful", "theme123", ""]
        for theme_id in ambiguous_ids:
            with self.subTest(theme_id=theme_id):
                category = Theme._infer_category(theme_id)
                self.assertEqual(category, "dark", f"Theme ID '{theme_id}' should default to dark")

    def test_theme_str_and_repr(self):
        """Test Theme string representations."""
        theme = Theme("test_id", "Test Theme", "dark", description="A test theme")
        
        # Test __str__
        str_repr = str(theme)
        self.assertEqual(str_repr, "Test Theme (test_id)")
        
        # Test __repr__
        repr_str = repr(theme)
        self.assertEqual(repr_str, "Theme('test_id', 'Test Theme', 'dark')")

    def test_theme_initialization_with_all_parameters(self):
        """Test Theme initialization with all parameters."""
        theme_dir = self.temp_dir / "full_theme"
        theme_dir.mkdir()
        
        settings = {"color": "blue", "font_size": 12}
        qss_order = ["main.qss", "widgets.qss"]
        
        theme = Theme(
            theme_id="full_theme",
            name="Full Theme",
            category="light",
            theme_directory=theme_dir,
            description="A complete theme",
            version="2.0.0",
            qss_order=qss_order,
            settings=settings
        )
        
        self.assertEqual(theme.theme_id, "full_theme")
        self.assertEqual(theme.name, "Full Theme")
        self.assertEqual(theme.category, "light")
        self.assertEqual(theme.theme_directory, theme_dir)
        self.assertEqual(theme.description, "A complete theme")
        self.assertEqual(theme.version, "2.0.0")
        self.assertEqual(theme.qss_order, qss_order)
        self.assertEqual(theme.settings, settings)

    def test_theme_initialization_with_defaults(self):
        """Test Theme initialization with minimal parameters and defaults."""
        theme = Theme("minimal", "Minimal Theme", "dark")
        
        self.assertEqual(theme.theme_id, "minimal")
        self.assertEqual(theme.name, "Minimal Theme")
        self.assertEqual(theme.category, "dark")
        self.assertIsNone(theme.theme_directory)
        self.assertEqual(theme.description, "Theme: Minimal Theme")  # Default description
        self.assertEqual(theme.version, "1.0.0")  # Default version
        self.assertEqual(theme.qss_order, [])  # Default empty list
        self.assertEqual(theme.settings, {})  # Default empty dict

    def test_get_qss_with_missing_files(self):
        """Test QSS loading when some files in qss_order don't exist."""
        theme_dir = self.temp_dir / "missing_files_theme"
        theme_dir.mkdir()
        
        # Create YAML with files that don't exist
        yaml_content = """
name: "Missing Files Theme"
qss_order:
  - "existing.qss"
  - "missing.qss"
  - "another_existing.qss"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")
        
        # Create only some of the QSS files
        (theme_dir / "existing.qss").write_text("/* Existing file */", encoding="utf-8")
        (theme_dir / "another_existing.qss").write_text("/* Another existing file */", encoding="utf-8")
        # missing.qss intentionally not created
        
        theme = Theme.from_directory(theme_dir)
        qss_content = theme.get_qss()
        
        # Should contain content from existing files but not fail
        self.assertIn("/* From: existing.qss */", qss_content)
        self.assertIn("/* Existing file */", qss_content)
        self.assertIn("/* From: another_existing.qss */", qss_content)
        self.assertIn("/* Another existing file */", qss_content)
        
        # Should not contain content from missing file
        self.assertNotIn("missing.qss", qss_content)

    def test_get_qss_with_empty_files(self):
        """Test QSS loading with empty files."""
        theme_dir = self.temp_dir / "empty_files_theme"
        theme_dir.mkdir()
        
        yaml_content = """
name: "Empty Files Theme"
qss_order:
  - "empty.qss"
  - "whitespace.qss"
  - "content.qss"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")
        
        # Create files with different emptiness patterns
        (theme_dir / "empty.qss").write_text("", encoding="utf-8")
        (theme_dir / "whitespace.qss").write_text("   \n\t  \n", encoding="utf-8")
        (theme_dir / "content.qss").write_text("/* Has content */", encoding="utf-8")
        
        theme = Theme.from_directory(theme_dir)
        qss_content = theme.get_qss()
        
        # Only files with actual content should be included
        self.assertNotIn("/* From: empty.qss */", qss_content)
        self.assertNotIn("/* From: whitespace.qss */", qss_content)
        self.assertIn("/* From: content.qss */", qss_content)
        self.assertIn("/* Has content */", qss_content)

    def test_get_qss_read_error_handling(self):
        """Test QSS loading when file read fails."""
        theme_dir = self.temp_dir / "read_error_theme"
        theme_dir.mkdir()
        
        yaml_content = """
name: "Read Error Theme"
qss_order:
  - "good.qss"
  - "problematic.qss"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")
        
        # Create a good file
        (theme_dir / "good.qss").write_text("/* Good file */", encoding="utf-8")
        
        # Create a file with restricted permissions (if on Unix-like system)
        problematic_file = theme_dir / "problematic.qss"
        problematic_file.write_text("/* Problematic file */", encoding="utf-8")
        
        theme = Theme.from_directory(theme_dir)
        
        # Patch open to simulate read error for problematic file
        import unittest.mock
        original_open = open
        
        def mock_open(*args, **kwargs):
            if "problematic.qss" in str(args[0]):
                raise IOError("Simulated read error")
            return original_open(*args, **kwargs)
        
        with unittest.mock.patch("builtins.open", side_effect=mock_open):
            qss_content = theme.get_qss()
        
        # Should contain good file content but skip problematic file
        self.assertIn("/* From: good.qss */", qss_content)
        self.assertIn("/* Good file */", qss_content)
        self.assertNotIn("problematic.qss", qss_content)

    def test_load_theme_config_io_error(self):
        """Test _load_theme_config error handling for IO errors."""
        theme_dir = self.temp_dir / "io_error_theme"
        theme_dir.mkdir()
        
        # Create a YAML file
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("name: Test", encoding="utf-8")
        
        # Patch open to simulate IO error
        import unittest.mock
        
        with unittest.mock.patch("builtins.open", side_effect=IOError("Simulated IO error")):
            with self.assertRaises(ValueError) as context:
                Theme._load_theme_config(yaml_file)
            
            self.assertIn("Error reading theme config", str(context.exception))
            self.assertIn("Simulated IO error", str(context.exception))

    def test_load_theme_config_non_dict_yaml(self):
        """Test _load_theme_config handling of non-dictionary YAML content."""
        theme_dir = self.temp_dir / "non_dict_theme"
        theme_dir.mkdir()
        
        # Create YAML file with non-dictionary content
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("- item1\n- item2\n", encoding="utf-8")  # YAML list instead of dict
        
        config = Theme._load_theme_config(yaml_file)
        self.assertEqual(config, {})  # Should return empty dict for non-dict YAML

    def test_theme_directory_with_no_qss_files(self):
        """Test theme directory that has YAML but no QSS files."""
        theme_dir = self.temp_dir / "no_qss_theme"
        theme_dir.mkdir()
        
        # Create YAML config
        yaml_content = """
name: "No QSS Theme"
description: "Theme with no QSS files"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")
        
        theme = Theme.from_directory(theme_dir)
        
        self.assertEqual(theme.name, "No QSS Theme")
        self.assertEqual(theme.description, "Theme with no QSS files")
        self.assertEqual(theme.qss_order, [])  # No QSS files found
        self.assertEqual(theme.get_qss(), "")  # Empty QSS content
        self.assertEqual(theme.get_qss_file_paths(), [])  # No file paths

    def test_theme_cache_clearing(self):
        """Test that cache clearing works correctly."""
        theme_dir = self.temp_dir / "cache_theme"
        theme_dir.mkdir()
        
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("name: Cache Theme", encoding="utf-8")
        
        qss_file = theme_dir / "style.qss"
        qss_file.write_text("/* Original content */", encoding="utf-8")
        
        theme = Theme.from_directory(theme_dir)
        
        # Load QSS content (creates cache)
        original_content = theme.get_qss()
        self.assertIn("/* Original content */", original_content)
        
        # Verify cache is being used by checking internal state
        self.assertIsNotNone(theme._qss_cache)
        
        # Clear cache
        theme.clear_cache()
        self.assertIsNone(theme._qss_cache)
        
        # Modify the file (simulating external change)
        qss_file.write_text("/* Modified content */", encoding="utf-8")
        
        # Get QSS content again (should re-read from file)
        new_content = theme.get_qss()
        self.assertIn("/* Modified content */", new_content)


if __name__ == "__main__":
    unittest.main()
