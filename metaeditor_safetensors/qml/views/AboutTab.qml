import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: aboutTab
    
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
                text: "Safetensors Metadata Editor"
                font.pointSize: 16
                font.bold: true
                Layout.fillWidth: true
            }
            
            // Version row with copy button
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                
                Label {
                    id: versionLabel
                    text: appVersion
                    font.pointSize: 10
                }
                
                Button {
                    icon.name: "edit-copy"
                    implicitWidth: 20
                    implicitHeight: 20
                    
                    ToolTip.text: "Copy version to clipboard"
                    ToolTip.visible: hovered
                    
                    onClicked: {
                        if (clipboardHelper) {
                            clipboardHelper.copyToClipboard(versionLabel.text)
                        }
                    }
                }
                
                Item { Layout.fillWidth: true }
            }
            
            // Author
            Label {
                text: "Created by: KPandaK"
                font.pointSize: 9
                Layout.fillWidth: true
            }
            
            Item { Layout.preferredHeight: 8 }
            
            // Description
            Label {
                text: 'This is a free and open source app for viewing and editing metadata in safetensors model files.\n\nIt implements v1.01 of Stability.AI\'s model metadata standard specification.\n\nIf you enjoy this app, feel free to tip me for a coffee!'
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            
            Item { Layout.fillHeight: true }
            
            // Links section
            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignCenter
                spacing: 30
                
                // Ko-fi link
                Image {
                    id: kofiImage
                    Layout.preferredWidth: 134
                    Layout.preferredHeight: 71
                    Layout.alignment: Qt.AlignVCenter
                    source: "qrc:/assets/support_me.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    antialiasing: true
                    mipmap: true
                    
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally("https://ko-fi.com/kpandak")
                        
                        onPressed: kofiImage.scale = 0.95
                        onReleased: kofiImage.scale = 1.0
                        
                        Behavior on scale {
                            NumberAnimation { duration: 100 }
                        }
                    }
                }
                
                // GitHub link
                Image {
                    id: githubImage
                    Layout.preferredWidth: 191
                    Layout.preferredHeight: 47
                    Layout.alignment: Qt.AlignVCenter
                    source: "qrc:/assets/GitHub_Lockup_Dark.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    antialiasing: true
                    mipmap: true               
                    
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally("https://github.com/KPandaK/metaeditor_safetensors")
                        
                        onPressed: githubImage.scale = 0.95
                        onReleased: githubImage.scale = 1.0
                        
                        Behavior on scale {
                            NumberAnimation { duration: 100 }
                        }
                    }
                }
            }            

            Item { Layout.preferredHeight: 16 }
        }
    }
}