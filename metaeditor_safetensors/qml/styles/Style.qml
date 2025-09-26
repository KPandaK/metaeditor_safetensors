import QtQuick

/*
Base Style Definitions
======================

Contains all raw design tokens (colors, fonts, spacing, effects) that
themes can compose into semantic meanings.

Based on the existing dark theme color palette.
*/

QtObject {
    // Color Palette
    property color background: "#1e1e1e"
    property color sidebar: "#252526"
    property color borders: "#454545"
    property color textPrimary: "#cccccc"
    property color textSecondary: "#999999"
    property color accent: "#007acc"
    property color white: "#ffffff"
    property color black: "#000000"
    property color transparentOverlay: "rgba(255, 255, 255, 0.02)"

    // Typography
    property string fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"
    property int fontSizeSmall: 12
    property int fontSizeMedium: 14
    property int fontSizeLarge: 16
    property int fontWeightNormal: 400
    property int fontWeightBold: 600

    // Spacing
    property int spacingTiny: 4
    property int spacingSmall: 8
    property int spacingMedium: 16
    property int spacingLarge: 24
    property int spacingXLarge: 32

    // Border Radius
    property int borderRadiusSmall: 3
    property int borderRadiusMedium: 6
    property int borderRadiusLarge: 8

    // Shadows
    property int shadowBlur: 8
    property color shadowColor: "rgba(0, 0, 0, 0.3)"

    // Animation
    property int animationDurationFast: 150
    property int animationDurationNormal: 300
    property int animationDurationSlow: 500
}
