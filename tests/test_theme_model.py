"""
Unit tests for Theme Model
==========================

Tests for theme directory loading, YAML configuration parsing,
and QSS file handling in the Theme model.
"""

import logging
import tempfile
from pathlib import Path

import pytest

from metaeditor_safetensors.models.theme import Theme


@pytest.fixture
def temp_dir():
    """Set up a temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Clean up temporary directory
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress debug/info logging during tests for cleaner output."""
    logging.getLogger().setLevel(logging.ERROR)


class TestThemeModel:
    """Test cases for Theme model functionality."""

    def test_valid_theme_directory_with_yaml(self, temp_dir):
        """Test loading a theme from a valid directory with YAML config."""
        # Create a valid theme directory
        theme_dir = temp_dir / "valid_theme"
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
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        # Create some QSS files
        (theme_dir / "main.qss").write_text("/* Main styles */", encoding="utf-8")
        (theme_dir / "widgets.qss").write_text("/* Widget styles */", encoding="utf-8")

        # Load theme and validate
        theme = Theme.from_directory(theme_dir)

        assert theme.config.theme_id == "test_theme"
        assert theme.config.name == "Test Theme"
        assert theme.config.description == "A test theme for validation"
        assert theme.config.category == "dark"
        assert theme.config.version == "1.0.0"
        assert theme.qss_order == ["main.qss", "widgets.qss"]
        assert theme.directory == theme_dir

    def test_theme_directory_without_yaml_fails(self, temp_dir):
        """Test that a directory without YAML file raises ValueError."""
        # Create a directory without YAML file
        theme_dir = temp_dir / "no_yaml_theme"
        theme_dir.mkdir()

        # Create some QSS files but no YAML
        (theme_dir / "main.qss").write_text("/* Main styles */", encoding="utf-8")

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            Theme.from_directory(theme_dir)

        assert "No YAML file found" in str(exc_info.value)

    def test_theme_directory_with_invalid_yaml_fails(self, temp_dir):
        """Test that a directory with invalid YAML raises ValueError."""
        # Create a theme directory
        theme_dir = temp_dir / "invalid_yaml_theme"
        theme_dir.mkdir()

        # Create an invalid YAML file
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("invalid: yaml: content: [unclosed", encoding="utf-8")

        # Should raise ValueError when YAML parsing fails
        with pytest.raises(ValueError) as exc_info:
            Theme.from_directory(theme_dir)

        assert "Error reading theme config" in str(exc_info.value)

    def test_theme_directory_with_empty_yaml_fails(self, temp_dir):
        """Test that empty YAML file fails due to missing required fields."""
        # Create a theme directory
        theme_dir = temp_dir / "empty_yaml_theme"
        theme_dir.mkdir()

        # Create an empty YAML file
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("", encoding="utf-8")

        # Create a QSS file
        (theme_dir / "style.qss").write_text("/* Some styles */", encoding="utf-8")

        # Should raise ValueError due to missing required fields
        with pytest.raises(ValueError) as exc_info:
            Theme.from_directory(theme_dir)

        assert "Error reading theme config" in str(exc_info.value)

    def test_theme_directory_with_minimal_yaml(self, temp_dir):
        """Test loading theme with minimal YAML configuration."""
        # Create a theme directory
        theme_dir = temp_dir / "minimal_theme"
        theme_dir.mkdir()

        # Create minimal YAML config with required theme_id
        yaml_content = """
theme_id: "minimal_theme"
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
        assert theme.config.theme_id == "minimal_theme"
        assert theme.config.name == "Minimal Theme"
        assert theme.config.category == "light"  # Default value
        assert theme.config.version == "1.0.0"
        # QSS files should be auto-discovered alphabetically
        assert theme.qss_order == ["advanced.qss", "base.qss"]

    def test_theme_qss_order_with_extra_files(self, temp_dir):
        """Test that extra QSS files not in qss_order are appended."""
        # Create a theme directory
        theme_dir = temp_dir / "ordered_theme"
        theme_dir.mkdir()

        # Create YAML with partial qss_order
        yaml_content = """
theme_id: "ordered_theme"
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
        assert theme.qss_order == expected_order

    def test_get_qss_file_paths(self, temp_dir):
        """Test getting QSS file paths for file watching."""
        # Create a theme directory
        theme_dir = temp_dir / "paths_theme"
        theme_dir.mkdir()

        # Create YAML config
        yaml_content = """
theme_id: "paths_theme"
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
        assert paths == expected_paths

    def test_qss_content_loading_and_caching(self, temp_dir):
        """Test QSS content loading and caching behavior."""
        # Create a theme directory
        theme_dir = temp_dir / "qss_test_theme"
        theme_dir.mkdir()

        # Create YAML config
        yaml_content = """
theme_id: "qss_test_theme"
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
        assert "/* From: first.qss */" in qss_content
        assert "/* First file content */" in qss_content
        assert "/* From: second.qss */" in qss_content
        assert "/* Second file content */" in qss_content

        # Get QSS content again (should use cache)
        qss_content_cached = theme.get_qss()
        assert qss_content == qss_content_cached

        # Clear cache and get content again
        theme.clear_cache()
        qss_content_after_clear = theme.get_qss()
        assert qss_content == qss_content_after_clear

    def test_theme_without_directory_returns_empty_qss(self, temp_dir):
        """Test that theme with empty directory returns empty QSS."""
        from metaeditor_safetensors.models.theme import ThemeConfig

        # Create an empty directory for testing
        empty_dir = temp_dir / "empty_theme"
        empty_dir.mkdir()

        config = ThemeConfig(theme_id="test", name="Test Theme")
        theme = Theme(config=config, directory=empty_dir, qss_order=[])
        assert theme.get_qss() == ""
        assert theme.get_qss_file_paths() == []

    def test_theme_initialization_with_all_parameters(self, temp_dir):
        """Test Theme initialization with all parameters via config."""
        from metaeditor_safetensors.models.theme import ThemeConfig, ThemeType

        theme_dir = temp_dir / "full_theme"
        theme_dir.mkdir()

        config = ThemeConfig(
            theme_id="full_theme",
            name="Full Theme",
            category=ThemeType.LIGHT,
            description="A complete theme",
            version="2.0.0",
            qss_order=["main.qss", "widgets.qss"],
        )

        theme = Theme(
            config=config, directory=theme_dir, qss_order=["main.qss", "widgets.qss"]
        )

        assert theme.config.theme_id == "full_theme"
        assert theme.config.name == "Full Theme"
        assert theme.config.category == ThemeType.LIGHT
        assert theme.directory == theme_dir
        assert theme.config.description == "A complete theme"
        assert theme.config.version == "2.0.0"
        assert theme.qss_order == ["main.qss", "widgets.qss"]

    def test_theme_initialization_with_defaults(self, temp_dir):
        """Test Theme initialization with minimal parameters and defaults."""
        from metaeditor_safetensors.models.theme import ThemeConfig, ThemeType

        # Create a directory for the theme
        theme_dir = temp_dir / "minimal_theme"
        theme_dir.mkdir()

        config = ThemeConfig(theme_id="minimal", name="Minimal Theme")
        theme = Theme(config=config, directory=theme_dir, qss_order=[])

        assert theme.config.theme_id == "minimal"
        assert theme.config.name == "Minimal Theme"
        assert theme.config.category == ThemeType.LIGHT  # Default category
        assert theme.directory == theme_dir
        assert theme.config.description is None  # Default description
        assert theme.config.version == "1.0.0"  # Default version
        assert theme.qss_order == []  # Empty qss_order

    def test_get_qss_with_missing_files(self, temp_dir):
        """Test QSS loading when some files in qss_order don't exist."""
        theme_dir = temp_dir / "missing_files_theme"
        theme_dir.mkdir()

        # Create YAML with files that don't exist
        yaml_content = """
theme_id: "missing_files_theme"
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
        (theme_dir / "another_existing.qss").write_text(
            "/* Another existing file */", encoding="utf-8"
        )
        # missing.qss intentionally not created

        theme = Theme.from_directory(theme_dir)
        qss_content = theme.get_qss()

        # Should contain content from existing files but not fail
        assert "/* From: existing.qss */" in qss_content
        assert "/* Existing file */" in qss_content
        assert "/* From: another_existing.qss */" in qss_content
        assert "/* Another existing file */" in qss_content

        # Should not contain content from missing file
        assert "missing.qss" not in qss_content

    def test_get_qss_with_empty_files(self, temp_dir):
        """Test QSS loading with empty files."""
        theme_dir = temp_dir / "empty_files_theme"
        theme_dir.mkdir()

        yaml_content = """
theme_id: "empty_files_theme"
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
        assert "/* From: empty.qss */" not in qss_content
        assert "/* From: whitespace.qss */" not in qss_content
        assert "/* From: content.qss */" in qss_content
        assert "/* Has content */" in qss_content

    def test_get_qss_read_error_handling(self, temp_dir, mocker):
        """Test QSS loading when file read fails."""
        theme_dir = temp_dir / "read_error_theme"
        theme_dir.mkdir()

        yaml_content = """
theme_id: "read_error_theme"
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
        original_open = open

        def mock_open(*args, **kwargs):
            if "problematic.qss" in str(args[0]):
                raise IOError("Simulated read error")
            return original_open(*args, **kwargs)

        mocker.patch("builtins.open", side_effect=mock_open)
        qss_content = theme.get_qss()

        # Should contain good file content but skip problematic file
        assert "/* From: good.qss */" in qss_content
        assert "/* Good file */" in qss_content
        assert "problematic.qss" not in qss_content

    def test_load_theme_config_io_error(self, temp_dir, mocker):
        """Test _load_theme_config error handling for IO errors."""
        theme_dir = temp_dir / "io_error_theme"
        theme_dir.mkdir()

        # Create a YAML file
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text("name: Test", encoding="utf-8")

        # Patch open to simulate IO error
        mocker.patch("builtins.open", side_effect=IOError("Simulated IO error"))

        with pytest.raises(ValueError) as exc_info:
            Theme._load_theme_config(yaml_file)

        assert "Error reading theme config" in str(exc_info.value)
        assert "Simulated IO error" in str(exc_info.value)

    def test_load_theme_config_non_dict_yaml(self, temp_dir):
        """Test _load_theme_config handling of non-dictionary YAML content."""
        theme_dir = temp_dir / "non_dict_theme"
        theme_dir.mkdir()

        # Create YAML file with non-dictionary content
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(
            "- item1\n- item2\n", encoding="utf-8"
        )  # YAML list instead of dict

        # Should raise ValueError due to Pydantic validation failure
        with pytest.raises(ValueError) as exc_info:
            Theme._load_theme_config(yaml_file)

        assert "Error reading theme config" in str(exc_info.value)

    def test_theme_directory_with_no_qss_files(self, temp_dir):
        """Test theme directory that has YAML but no QSS files."""
        theme_dir = temp_dir / "no_qss_theme"
        theme_dir.mkdir()

        # Create YAML config
        yaml_content = """
theme_id: "no_qss_theme"
name: "No QSS Theme"
description: "Theme with no QSS files"
"""
        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(yaml_content.strip(), encoding="utf-8")

        theme = Theme.from_directory(theme_dir)

        assert theme.config.name == "No QSS Theme"
        assert theme.config.description == "Theme with no QSS files"
        assert theme.qss_order == []  # No QSS files found
        assert theme.get_qss() == ""  # Empty QSS content
        assert theme.get_qss_file_paths() == []  # No file paths

    def test_theme_cache_clearing(self, temp_dir):
        """Test that cache clearing works correctly."""
        theme_dir = temp_dir / "cache_theme"
        theme_dir.mkdir()

        yaml_file = theme_dir / "theme.yaml"
        yaml_file.write_text(
            """
theme_id: "cache_theme"
name: "Cache Theme"
""",
            encoding="utf-8",
        )

        qss_file = theme_dir / "style.qss"
        qss_file.write_text("/* Original content */", encoding="utf-8")

        theme = Theme.from_directory(theme_dir)

        # Load QSS content (creates cache)
        original_content = theme.get_qss()
        assert "/* Original content */" in original_content

        # Verify cache is being used by checking internal state
        assert theme._qss_cache is not None

        # Clear cache
        theme.clear_cache()
        assert theme._qss_cache is None

        # Modify the file (simulating external change)
        qss_file.write_text("/* Modified content */", encoding="utf-8")

        # Get QSS content again (should re-read from file)
        new_content = theme.get_qss()
        assert "/* Modified content */" in new_content
