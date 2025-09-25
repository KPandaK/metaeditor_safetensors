import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: creditsTab
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0
        
        // Logo section
        Item {
            Layout.preferredWidth: 250
            Layout.preferredHeight: 250
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            
            Image {
                id: logoImage
                anchors.centerIn: parent
                width: 250
                height: 250
                source: "qrc:/assets/logo.svg"
                fillMode: Image.PreserveAspectFit
            }
        }
        
        // Content section
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignTop
            spacing: 12
            
            // Title
            Label {
                text: "Credits"
                font.pointSize: 16
                font.bold: true
                Layout.fillWidth: true
            }
            
            // Credits content
            Label {
                text: 'Original Safetensors Icon by <a href="https://github.com/SHADOW-LIGHTS">SHADOW-LIGHTS</a>'
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                textFormat: Text.RichText
                
                onLinkActivated: function(link) {
                    console.log("Opening credits link:", link)
                    Qt.openUrlExternally(link)
                }
                
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton
                    cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
                }
            }
            
            Item { Layout.fillHeight: true }
        }
    }
    
    Component.onCompleted: {
        console.log("Credits tab loaded")
    }
}