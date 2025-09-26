import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components"

ApplicationWindow {
    id: mainWindow
    title: "MetaEditor SafeTensors"
    width: 1100
    height: 900
    visible: true

    // Main content area
    Rectangle {
        anchors.fill: parent
        anchors.margins: 15
        color: "transparent"

        RowLayout {
            id: mainLayout
            anchors.fill: parent
            spacing: 10

            // Left column - metadata sections
            ColumnLayout {
                id: leftColumn
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.6
                spacing: 10

                // General Section
                CollapsibleGroupBox {
                    id: generalSection
                    title: "General"
                    Layout.fillWidth: true
                    expanded: true

                    contentItem: GeneralSection {
                        id: generalSectionContent
                        fieldsEnabled: mainViewHelper.getFieldsEnabled()

                        // Connect to helper methods
                        onTitleChanged: mainViewHelper.setTitle(text)
                        onModelTypeChanged: mainViewHelper.setModelType(type)
                        onDescriptionChanged: mainViewHelper.setDescription(text)
                        onTagsChanged: mainViewHelper.setTags(text)

                        Component.onCompleted: {
                            updateTitle(mainViewHelper.getTitle());
                            updateModelType(mainViewHelper.getModelType());
                            updateDescription(mainViewHelper.getDescription());
                            updateTags(mainViewHelper.getTags());
                        }
                    }
                }

                // Source Section
                GroupBox {
                    id: sourceSection
                    title: "Source"
                    Layout.fillWidth: true

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        // Author and Date row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            // Author
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5

                                Label {
                                    text: "Author:"
                                }

                                TextField {
                                    id: authorField
                                    Layout.fillWidth: true
                                    placeholderText: "Author name or organization."
                                }
                            }

                            // Date
                            ColumnLayout {
                                Layout.preferredWidth: 200
                                spacing: 5

                                Label {
                                    text: "Date:"
                                }

                                TextField {
                                    id: dateField
                                    Layout.fillWidth: true
                                    placeholderText: "MM/dd/yyyy h:mm AP"
                                    // TODO: Replace with proper date/time picker
                                }
                            }
                        }

                        // Merged From
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Label {
                                text: "Merged From:"
                            }

                            TextField {
                                id: mergedFromField
                                Layout.fillWidth: true
                                placeholderText: "Source models, if merged from other models."
                            }
                        }
                    }
                }

                // Usage Section
                GroupBox {
                    id: usageSection
                    title: "Usage"
                    Layout.fillWidth: true

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        // Usage Hint
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Label {
                                text: "Usage Hint:"
                            }

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 80

                                TextArea {
                                    id: usageHintArea
                                    placeholderText: "Usage instructions or tips for using the model."
                                    wrapMode: TextArea.Wrap
                                }
                            }
                        }

                        // License
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Label {
                                text: "License:"
                            }

                            TextField {
                                id: licenseField
                                Layout.fillWidth: true
                                placeholderText: "License type (e.g., MIT, Apache-2.0, CC-BY-4.0)."
                            }
                        }
                    }
                }

                // Spacer to push everything up
                Item {
                    Layout.fillHeight: true
                }
            }

            // Right column - thumbnail area
            ColumnLayout {
                id: rightColumn
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.4
                spacing: 10

                // Thumbnail Group
                GroupBox {
                    id: thumbnailGroup
                    title: "Thumbnail"
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        // Thumbnail display area
                        Rectangle {
                            id: thumbnailDisplay
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumHeight: 200
                            color: "#f0f0f0"
                            border.color: "#ccc"
                            border.width: 1

                            Image {
                                id: thumbnailImage
                                anchors.fill: parent
                                anchors.margins: 5
                                fillMode: Image.PreserveAspectFit
                                source: mainViewHelper.getThumbnailSource()
                                visible: source !== ""

                                // Placeholder when no image
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 100
                                    height: 60
                                    color: "transparent"
                                    visible: !thumbnailImage.visible

                                    Text {
                                        anchors.centerIn: parent
                                        text: "No thumbnail"
                                        color: "#666"
                                        font.pixelSize: 14
                                    }
                                }
                            }
                        }

                        // Thumbnail buttons
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Button {
                                id: setThumbnailBtn
                                text: "Set"
                                Layout.fillWidth: true
                                enabled: mainViewHelper.getFieldsEnabled()
                                onClicked: mainViewHelper.onSetThumbnailClicked()
                            }

                            Button {
                                id: viewThumbnailBtn
                                text: "View"
                                Layout.fillWidth: true
                                enabled: mainViewHelper.getFieldsEnabled()
                                onClicked: mainViewHelper.onViewThumbnailClicked()
                            }

                            Button {
                                id: clearThumbnailBtn
                                text: "Clear"
                                Layout.fillWidth: true
                                enabled: mainViewHelper.getFieldsEnabled()
                                onClicked: mainViewHelper.onClearThumbnailClicked()
                            }
                        }
                    }
                }

                // Spacer
                Item {
                    Layout.fillHeight: true
                    Layout.minimumHeight: 10
                }
            }
        }
    }

    // Progress bar at bottom
    Rectangle {
        id: progressBarContainer
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 6
        color: "transparent"
        visible: false

        ProgressBar {
            id: progressBar
            anchors.fill: parent
            value: 0
            visible: parent.visible
        }
    }
}
