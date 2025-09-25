import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: thumbnailDialog
    
    title: "Thumbnail Preview"
    
    visible: true
    modality: Qt.ApplicationModal
    flags: Qt.Dialog
    
    width: 400
    height: 300
    minimumWidth: 200
    minimumHeight: 150
    
    // Properties for margins
    property int dialogMargin: 20
    
    // Function to center dialog over parent (or screen if no parent) with bounds checking
    function centerOnScreen() {
        var padding = 20
        
        var centerX, centerY
        
        if (thumbnailHelper.parentWidth() > 0 && thumbnailHelper.parentHeight() > 0) {
            centerX = thumbnailHelper.parentX() + (thumbnailHelper.parentWidth() - width) / 2
            centerY = thumbnailHelper.parentY() + (thumbnailHelper.parentHeight() - height) / 2
        } else {
            // No parent, center on screen
            centerX = (Screen.width - width) / 2
            centerY = (Screen.height - height) / 2
        }
        
        // Ensure dialog stays on screen with padding
        var finalX = Math.max(padding, Math.min(centerX, Screen.width - width - padding))
        var finalY = Math.max(padding, Math.min(centerY, Screen.height - height - padding))
        
        x = finalX
        y = finalY
    }
    
    // Main content
    Rectangle {
        anchors.fill: parent
        color: palette.window
        
        // Placeholder text while loading
        Label {
            id: placeholderText
            anchors.centerIn: parent
            text: "Loading image..."
            visible: !thumbnailImage.visible
            color: palette.windowText
        }
        
        // Main image display
        Image {
            id: thumbnailImage
            objectName: "thumbnailImage"
            anchors.fill: parent
            anchors.margins: thumbnailDialog.dialogMargin
            source: thumbnailHelper.image_uri()
            
            fillMode: Image.PreserveAspectFit
            smooth: true
            antialiasing: true
            mipmap: true
            
            visible: status === Image.Ready
            
            onStatusChanged: {
                if (status === Image.Ready) {
                    // Resize dialog to fit image (with reasonable constraints)
                    var maxWidth = Screen.width * 0.9
                    var maxHeight = Screen.height * 0.9
                    
                    var idealWidth = Math.min(sourceSize.width + (thumbnailDialog.dialogMargin * 2), maxWidth)
                    var idealHeight = Math.min(sourceSize.height + (thumbnailDialog.dialogMargin * 2), maxHeight)
                    
                    thumbnailDialog.width = Math.max(idealWidth, minimumWidth)
                    thumbnailDialog.height = Math.max(idealHeight, minimumHeight)
                    
                    // Center dialog on screen after resizing
                    centerOnScreen()
                } else if (status === Image.Error) {
                    placeholderText.text = "Failed to load image"
                    placeholderText.visible = true
                }
            }
        }
    }
}