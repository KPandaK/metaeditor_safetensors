import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: aboutDialog
    
    title: "About"
    width: 690
    height: 425
    minimumWidth: 690
    minimumHeight: 425
    maximumWidth: 690
    maximumHeight: 425
    
    visible: true
    modality: Qt.ApplicationModal
    flags: Qt.Dialog
    
    // Main content layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 0
        
        // Tab content area
        StackLayout {
            id: stackLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex
            
            // About tab content
            AboutTab {
                id: aboutTab
            }
            
            // Credits tab content  
            CreditsTab {
                id: creditsTab
            }
            
            // License tab content
            LicenseTab {
                id: licenseTab
            }
        }
        
        // Tab bar at bottom
        TabBar {
            id: tabBar
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            
            TabButton {
                text: "About"
            }
            
            TabButton {
                text: "Credits"
            }
            
            TabButton {
                text: "License"
            }
        }
    }
}