import QtQuick
import "../styles"

/*
Dark Theme
==========

Semantic color and style mappings for dark mode using base Style definitions.
Maps raw style values to semantic meanings for UI components.
*/

QtObject {
    property Style style: Style {}

    // Semantic Background Colors
    property color primaryBackground: style.background
    property color secondaryBackground: style.sidebar
    property color surfaceBackground: style.transparentOverlay

    // Semantic Text Colors
    property color primaryText: style.textPrimary
    property color secondaryText: style.textSecondary
    property color accentText: style.accent

    // Semantic Border Colors
    property color primaryBorder: style.borders
    property color focusBorder: style.accent

    // Interactive Colors
    property color buttonBackground: style.accent
    property color buttonText: style.white
    property color buttonHover: "#1a86d1"
    property color buttonPressed: "#005a9e"

    // Status Colors
    property color success: "#28a745"
    property color warning: "#ffc107"
    property color error: "#dc3545"
    property color info: style.accent

    // Typography Mappings
    property string fontFamily: style.fontFamily
    property int headingSize: style.fontSizeLarge
    property int bodySize: style.fontSizeMedium
    property int captionSize: style.fontSizeSmall

    // Spacing Mappings
    property int paddingSmall: style.spacingTiny
    property int paddingMedium: style.spacingSmall
    property int paddingLarge: style.spacingMedium
    property int marginSmall: style.spacingSmall
    property int marginMedium: style.spacingMedium
    property int marginLarge: style.spacingLarge

    // Border Radius Mappings
    property int containerRadius: style.borderRadiusSmall
    property int buttonRadius: style.borderRadiusSmall
    property int cardRadius: style.borderRadiusMedium

    // Animation Mappings
    property int hoverTransition: style.animationDurationFast
    property int contentTransition: style.animationDurationNormal
}