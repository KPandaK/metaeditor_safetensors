import QtQuick
import Qt5Compat.GraphicalEffects

Item {
    id: section

    // Public properties
    property string title: "Section"
    property bool expanded: true

    // Animation constants
    readonly property int animationDuration: 300
    readonly property int headerHeight: 32
    readonly property int contentMargin: 12
    readonly property int headerMargin: 4
    readonly property int arrowSize: 24

    default property alias content: contentArea.data

    signal toggled(bool expanded)

    // Private properties
    property int contentHeight: 0
    property bool animationsEnabled: false

    height: headerHeight + contentHeight

    // Animation behavior for height changes
    Behavior on height {
        enabled: section.animationsEnabled
        NumberAnimation {
            duration: section.animationDuration
            easing.type: Easing.InOutCubic
        }
    }

    // Header
    Item {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: section.headerHeight

        Row {
            id: headerContent
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: section.headerMargin
            anchors.rightMargin: section.headerMargin
            spacing: 4

            // Arrow icon
            Item {
                width: section.arrowSize
                height: section.arrowSize
                anchors.verticalCenter: parent.verticalCenter

                Image {
                    id: arrowImage
                    anchors.centerIn: parent
                    source: "qrc:/assets/arrow-right.svg"
                    sourceSize.width: section.arrowSize
                    sourceSize.height: section.arrowSize
                    rotation: section.expanded ? 90 : 0
                    visible: false

                    Behavior on rotation {
                        enabled: section.animationsEnabled
                        RotationAnimation {
                            duration: section.animationDuration
                            easing.type: Easing.InOutCubic
                        }
                    }
                }

                ColorOverlay {
                    anchors.fill: arrowImage
                    source: arrowImage
                    color: "black"
                    rotation: arrowImage.rotation
                }
            }

            Text {
                text: section.title
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                section.expanded = !section.expanded;
                section.toggled(section.expanded);
            }
        }
    }

    // Content area - clean without borders
    Item {
        id: contentContainer
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        clip: true

        Item {
            id: contentArea
            anchors.fill: parent
            anchors.margins: section.contentMargin
        }
    }

    // Content height calculation
    function updateContentHeight() {
        if (expanded) {
            contentHeight = contentArea.childrenRect.height + (section.contentMargin * 2);
        } else {
            contentHeight = 0;
        }
    }

    // Initialize after component is ready
    Component.onCompleted: {
        Qt.callLater(function () {
            section.updateContentHeight();
            animationsEnabled = true;
        });
    }

    // Update height when content changes
    Connections {
        target: contentArea
        function onChildrenRectChanged() {
            section.updateContentHeight();
        }
    }

    // Update height when expanded state changes
    onExpandedChanged: section.updateContentHeight()

    // Public methods
    function toggle() {
        expanded = !expanded;
        toggled(expanded);
    }

    function setExpanded(exp) {
        if (expanded !== exp) {
            expanded = exp;
            toggled(expanded);
        }
    }
}
