pragma Singleton
import QtQuick

/*
QML Theme Manager
=================

Central theme management singleton that:
1. Reads current theme from Python QmlThemeService
2. Provides the active theme object to all QML components
3. Automatically switches themes when system theme changes

Usage in components:
    Rectangle {
        color: ThemeManager.activeTheme.primaryBackground
    }
*/

QtObject {
    id: themeManager

    // Current theme name from Python service
    property string currentTheme: themeService ? themeService.currentTheme : "dark"

    // Theme instances
    property DarkTheme darkTheme: DarkTheme {}
    // Light theme placeholder for future implementation
    // property LightTheme lightTheme: LightTheme {}

    // Active theme object - components use this
    property var activeTheme: darkTheme  // For now, always dark

    // Future: This will switch based on currentTheme
    // property var activeTheme: currentTheme === "dark" ? darkTheme : lightTheme

    Component.onCompleted: {
        console.log("ThemeManager initialized with theme:", currentTheme);
    }

    onCurrentThemeChanged: {
        console.log("Theme changed to:", currentTheme);
        // Future: Update activeTheme based on currentTheme
    }
}
