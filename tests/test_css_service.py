"""
Unit tests for CSS Service
===========================

Tests for CSS class management functionality for Qt widgets.
"""

import pytest

# Import the functions we're testing
from metaeditor_safetensors.services.css_service import (
    has_css_class,
    refresh_style_recursive,
    set_css_class,
)


@pytest.fixture
def mock_widget(mocker):
    """Create a mock widget for testing."""
    widget = mocker.MagicMock()
    widget.setProperty = mocker.MagicMock()
    widget.property = mocker.MagicMock()
    return widget


class TestCSSService:
    """Test cases for CSS service functionality."""

    def test_set_css_class(self, mock_widget):
        """Test setting CSS class on a widget."""
        class_name = "test-class"

        # Call the function
        set_css_class(mock_widget, class_name)

        # Verify setProperty was called with correct arguments
        mock_widget.setProperty.assert_called_once_with("class", class_name)

    def test_has_css_class_returns_true_when_class_matches(self, mock_widget):
        """Test has_css_class returns True when widget has the specified class."""
        class_name = "test-class"

        # Mock the widget to return the class name
        mock_widget.property.return_value = class_name

        # Call the function
        result = has_css_class(mock_widget, class_name)

        # Verify the result
        assert result is True
        mock_widget.property.assert_called_once_with("class")

    def test_has_css_class_returns_false_when_class_doesnt_match(self, mock_widget):
        """Test has_css_class returns False when widget doesn't have the specified class."""
        class_name = "test-class"
        different_class = "different-class"

        # Mock the widget to return a different class name
        mock_widget.property.return_value = different_class

        # Call the function
        result = has_css_class(mock_widget, class_name)

        # Verify the result
        assert result is False
        mock_widget.property.assert_called_once_with("class")

    def test_has_css_class_returns_false_when_no_class_set(self, mock_widget):
        """Test has_css_class returns False when widget has no class property."""
        class_name = "test-class"

        # Mock the widget to return None (no class set)
        mock_widget.property.return_value = None

        # Call the function
        result = has_css_class(mock_widget, class_name)

        # Verify the result
        assert result is False
        mock_widget.property.assert_called_once_with("class")

    def test_has_css_class_returns_false_when_empty_string(self, mock_widget):
        """Test has_css_class returns False when widget has empty string class."""
        class_name = "test-class"

        # Mock the widget to return empty string
        mock_widget.property.return_value = ""

        # Call the function
        result = has_css_class(mock_widget, class_name)

        # Verify the result
        assert result is False
        mock_widget.property.assert_called_once_with("class")

    def test_refresh_style_recursive_single_widget(self, mock_widget, mocker):
        """Test refresh_style_recursive on a widget with no children."""
        # Mock the style methods
        mock_style = mocker.MagicMock()
        mock_widget.style.return_value = mock_style
        mock_widget.findChildren.return_value = []  # No children

        # Call the function
        refresh_style_recursive(mock_widget)

        # Verify style refresh was called
        mock_style.unpolish.assert_called_once_with(mock_widget)
        mock_style.polish.assert_called_once_with(mock_widget)
        mock_widget.findChildren.assert_called_once()

    def test_refresh_style_recursive_with_children(self, mock_widget, mocker):
        """Test refresh_style_recursive on a widget with children."""
        # Create mock child widgets
        mock_child1 = mocker.MagicMock()
        mock_child1_style = mocker.MagicMock()
        mock_child1.style.return_value = mock_child1_style
        mock_child1.findChildren.return_value = []  # No grandchildren

        mock_child2 = mocker.MagicMock()
        mock_child2_style = mocker.MagicMock()
        mock_child2.style.return_value = mock_child2_style
        mock_child2.findChildren.return_value = []  # No grandchildren

        # Mock the parent widget
        mock_style = mocker.MagicMock()
        mock_widget.style.return_value = mock_style
        mock_widget.findChildren.return_value = [mock_child1, mock_child2]

        # Call the function
        refresh_style_recursive(mock_widget)

        # Verify style refresh was called on parent
        mock_style.unpolish.assert_called_once_with(mock_widget)
        mock_style.polish.assert_called_once_with(mock_widget)

        # Verify style refresh was called on children
        mock_child1_style.unpolish.assert_called_once_with(mock_child1)
        mock_child1_style.polish.assert_called_once_with(mock_child1)
        mock_child2_style.unpolish.assert_called_once_with(mock_child2)
        mock_child2_style.polish.assert_called_once_with(mock_child2)

    def test_refresh_style_recursive_nested_children(self, mock_widget, mocker):
        """Test refresh_style_recursive on a widget with nested children."""
        # Create mock grandchild
        mock_grandchild = mocker.MagicMock()
        mock_grandchild_style = mocker.MagicMock()
        mock_grandchild.style.return_value = mock_grandchild_style
        mock_grandchild.findChildren.return_value = []  # No great-grandchildren

        # Create mock child with a grandchild
        mock_child = mocker.MagicMock()
        mock_child_style = mocker.MagicMock()
        mock_child.style.return_value = mock_child_style
        mock_child.findChildren.return_value = [mock_grandchild]

        # Mock the parent widget
        mock_style = mocker.MagicMock()
        mock_widget.style.return_value = mock_style
        mock_widget.findChildren.return_value = [mock_child]

        # Call the function
        refresh_style_recursive(mock_widget)

        # Verify style refresh was called on all levels
        mock_style.unpolish.assert_called_once_with(mock_widget)
        mock_style.polish.assert_called_once_with(mock_widget)
        mock_child_style.unpolish.assert_called_once_with(mock_child)
        mock_child_style.polish.assert_called_once_with(mock_child)
        mock_grandchild_style.unpolish.assert_called_once_with(mock_grandchild)
        mock_grandchild_style.polish.assert_called_once_with(mock_grandchild)
