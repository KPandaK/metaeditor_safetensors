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


def add_css_class(widget: QWidget, class_name: str) -> None:
    """Add a CSS class to a widget, preserving existing classes."""
    current_classes = get_css_classes(widget)
    current_classes.add(class_name)

    class_string = " ".join(sorted(current_classes))
    widget.setProperty("class", class_string)


def remove_css_class(widget: QWidget, class_name: str) -> None:
    """Remove a CSS class from a widget."""
    current_classes = get_css_classes(widget)
    current_classes.discard(class_name)

    if current_classes:
        class_string = " ".join(sorted(current_classes))
        widget.setProperty("class", class_string)
    else:
        widget.setProperty("class", None)


def has_css_class(widget: QWidget, class_name: str) -> bool:
    """Check if a widget has a specific CSS class."""
    current_classes = get_css_classes(widget)
    return class_name in current_classes


def get_css_classes(widget: QWidget) -> Set[str]:
    """Get all CSS classes currently applied to a widget."""
    class_property = widget.property("class")
    if not class_property:
        return set()

    if isinstance(class_property, str):
        return set(class_property.split())

    return set()
