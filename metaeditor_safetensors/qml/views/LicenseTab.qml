import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: licenseTab
    
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
                text: "The MIT License (MIT)"
                font.pointSize: 16
                font.bold: true
                Layout.fillWidth: true
            }
            
            // Scrollable license text
            ScrollView {
                id: licenseScrollView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                
                TextArea {
                    id: licenseTextArea
                    anchors.fill: parent
                    wrapMode: TextArea.Wrap
                    padding: 12
                    readOnly: true
                    background: null
                    
                    text: `Copyright © 2025 KPandaK

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.`
                }
            }
        }
    }
    
    Component.onCompleted: {
        console.log("License tab loaded")
    }
}