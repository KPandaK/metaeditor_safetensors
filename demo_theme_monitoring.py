#!/usr/bin/env python3
"""
Demo script to test darkdetect system theme monitoring functionality.

This script demonstrates the new system theme monitoring capabilities:
1. Starts with auto theme
2. Shows current theme detection
3. Demonstrates system theme change handling

Note: This is for demonstration purposes. In the real application,
the monitoring happens automatically when the user selects "auto" theme.
"""

import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from metaeditor_safetensors.services.theme_service import ThemeService, SystemTheme


def demo_theme_monitoring():
    """Demonstrate theme monitoring capabilities."""
    app = QApplication(sys.argv)
    
    # Create theme service
    theme_service = ThemeService(app)
    
    print("=== Theme Monitoring Demo ===")
    print(f"Available themes: {list(theme_service._available_themes.keys())}")
    
    # Show current system theme
    system_theme = theme_service._detect_system_theme()
    print(f"Current system theme: {system_theme.value}")
    
    # Connect to signals to show when they're emitted
    def on_theme_changed(theme_id):
        current_theme = theme_service.get_current_theme()
        theme_name = current_theme.name if current_theme else "Unknown"
        print(f"✓ Theme changed signal: {theme_id} -> {theme_name}")
    
    def on_system_theme_changed(theme_name):
        print(f"✓ System theme changed signal: {theme_name}")
    
    theme_service.theme_changed.connect(on_theme_changed)
    theme_service.system_theme_changed.connect(on_system_theme_changed)
    
    # Apply different themes to show monitoring behavior
    print(f"\n1. Applying 'dark' theme...")
    theme_service.apply_theme("dark")
    print(f"   Monitoring active: {theme_service.is_monitoring_system_theme()}")
    print(f"   Current preference: {theme_service.get_current_theme_preference()}")
    
    print(f"\n2. Applying 'auto' theme...")
    theme_service.apply_theme("auto")
    print(f"   Monitoring active: {theme_service.is_monitoring_system_theme()}")
    print(f"   Current preference: {theme_service.get_current_theme_preference()}")
    
    # Give thread time to start
    app.processEvents()
    time.sleep(0.1)
    print(f"   Monitoring active (after delay): {theme_service.is_monitoring_system_theme()}")
    
    # Simulate system theme change
    print(f"\n3. Simulating system theme change...")
    print("   (In real usage, this would happen automatically when OS theme changes)")
    
    # Simulate the callback that darkdetect would call
    print("   Simulating system theme change from Dark to Light...")
    theme_service._on_system_theme_changed("Light")
    
    print("   Simulating system theme change from Light to Dark...")
    theme_service._on_system_theme_changed("Dark")
    
    print(f"\n4. Switching back to specific theme...")
    theme_service.apply_theme("light")
    print(f"   Monitoring active: {theme_service.is_monitoring_system_theme()}")
    print(f"   Current preference: {theme_service.get_current_theme_preference()}")
    
    # Simulate system theme change when not using auto - should be ignored
    print(f"\n5. System theme change when not using auto (should be ignored)...")
    theme_service._on_system_theme_changed("Dark")
    print("   (No theme change should occur)")
    
    # Cleanup
    print(f"\n6. Cleanup...")
    theme_service.cleanup()
    print(f"   Monitoring active after cleanup: {theme_service.is_monitoring_system_theme()}")
    
    print(f"\n=== Demo Complete ===")
    print("Key features demonstrated:")
    print("• System theme monitoring starts/stops with auto theme")
    print("• Automatic theme switching when system theme changes (auto mode only)")
    print("• Thread-safe signal emission")
    print("• Proper cleanup of monitoring resources")
    
    # Note: We don't run app.exec() because this is just a demo
    # In real usage, the theme service would be part of the running application


if __name__ == "__main__":
    demo_theme_monitoring()