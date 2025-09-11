"""
CSS Class Service
================

Simple CSS-like class system for Qt widgets using the 'class' property,
compatible with qt-material's approach but adapted for our theme system.

Usage:
    from metaeditor_safetensors.services.css_service import set_css_class, add_css_class

    # Set a CSS class
    set_css_class(button, "secondary")

    # Add multiple classes
    add_css_class(button, "large")

Supported in QSS:
    QPushButton[class="secondary"] { background: transparent; }
    QPushButton[class~="large"] { min-height: 40px; }  /* Contains class */
"""

from typing import Set

from PySide6.QtWidgets import QWidget


def set_css_class(widget: QWidget, class_name: str) -> None:
    """Set a CSS class on a widget."""
    widget.setProperty("class", class_name)


def has_css_class(widget: QWidget, class_name: str) -> bool:
    """Check if a widget has a specific CSS class."""
    return widget.property("class") == class_name


def refresh_style_recursive(widget: QWidget) -> None:
    """Recursively refresh the style of a widget and its children."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    for child in widget.findChildren(QWidget):
        refresh_style_recursive(child)