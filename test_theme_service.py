#!/usr/bin/env python3
"""
Test script for the ThemeService functionality.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from metaeditor_safetensors.services.config_service import ConfigService
from metaeditor_safetensors.services.theme_service import ThemeService, ThemeCategory

def test_theme_service():
    """Test theme service functionality."""
    print("=== Theme Service Test ===\n")
    
    # Create a minimal QApplication for testing
    app = QApplication(sys.argv)
    
    # Create services
    config_service = ConfigService()
    theme_service = ThemeService(app, config_service)
    
    # Test 1: Get theme info
    print("1. Theme Information:")
    theme_info = theme_service.get_theme_info()
    print(f"   Available themes: {theme_info['available_themes']}")
    print(f"   System theme: {theme_info['system_theme']}")
    print(f"   User preference: {theme_info['user_preference']}")
    print(f"   Categories: {theme_info['categories']}")
    print()
    
    # Test 2: List themes by category
    print("2. Themes by Category:")
    for category in theme_service.get_theme_categories():
        themes = theme_service.get_themes_by_category(category)
        print(f"   {category.value}: {len(themes)} themes")
        if themes:
            for theme in themes[:3]:  # Show first 3
                print(f"     - {theme.display_name}")
            if len(themes) > 3:
                print(f"     ... and {len(themes) - 3} more")
    print()
    
    # Test 3: Apply auto theme
    print("3. Applying auto theme:")
    success = theme_service.apply_theme('auto')
    print(f"   Success: {success}")
    current = theme_service.get_current_theme()
    if current:
        print(f"   Applied: {current.display_name} ({current.filename})")
    print()
    
    # Test 4: Apply specific themes
    print("4. Testing specific themes:")
    test_themes = ['dark_teal.xml', 'light_blue.xml']
    for theme_file in test_themes:
        print(f"   Applying {theme_file}:")
        success = theme_service.apply_theme(theme_file, save_preference=False)
        print(f"     Success: {success}")
        if success:
            current = theme_service.get_current_theme()
            print(f"     Applied: {current.display_name}")
    print()
    
    # Test 5: User preference handling
    print("5. User Preference Test:")
    print(f"   Current preference: {config_service.get_theme_preference()}")
    theme_service.apply_user_preference()
    current = theme_service.get_current_theme()
    if current:
        print(f"   Applied from preference: {current.display_name}")
    print()
    
    print("=== Test Complete ===")
    
    # Don't start the event loop for this test
    return 0

if __name__ == "__main__":
    sys.exit(test_theme_service())
