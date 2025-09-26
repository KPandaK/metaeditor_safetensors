import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ExpandableSection {
    id: generalSection
    title: "General"
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.margins: 10
    expanded: true

    // Expose properties at the top level for easier access
    property alias titleText: titleField.text
    property alias modelType: typeComboBox.currentText
    property alias description: descriptionArea.text
    property alias tags: tagsField.text
    property bool fieldsEnabled: true

    // Signals for data changes
    signal titleUpdated(string text)
    signal modelTypeUpdated(string type)
    signal descriptionUpdated(string text)
    signal tagsUpdated(string text)

    // Functions to update from external data
    function setTitle(newTitle) {
        if (titleField.text !== newTitle) {
            titleField.text = newTitle;
        }
    }

    function setModelType(newType) {
        let idx = typeComboBox.model.indexOf(newType);
        if (idx >= 0 && typeComboBox.currentIndex !== idx) {
            typeComboBox.currentIndex = idx;
        }
    }

    function setDescription(newDescription) {
        if (descriptionArea.text !== newDescription) {
            descriptionArea.text = newDescription;
        }
    }

    function setTags(newTags) {
        if (tagsField.text !== newTags) {
            tagsField.text = newTags;
        }
    }

    ColumnLayout {
        id: content
        spacing: 10

        // Title and Type row
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            // Title
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5

                Label {
                    text: "Title:"
                }

                TextField {
                    id: titleField
                    Layout.fillWidth: true
                    placeholderText: "Name of the model."
                    enabled: generalSection.fieldsEnabled
                    onTextEdited: generalSection.titleUpdated(text)
                }
            }

            // Type
            ColumnLayout {
                spacing: 5

                Label {
                    text: "Model Type:"
                }

                ComboBox {
                    id: typeComboBox
                    Layout.fillWidth: true
                    model: ["Unknown", "Checkpoint", "LoRA", "TextualInversion", "VAE", "ControlNet"]
                    enabled: generalSection.fieldsEnabled
                    onEditTextChanged: generalSection.modelTypeUpdated(currentText)
                }
            }
        }

        // Description
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 5

            Label {
                text: "Description:"
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 200

                TextArea {
                    id: descriptionArea
                    placeholderText: "Describe the model's purpose, training data, and capabilities."
                    wrapMode: TextArea.Wrap
                    enabled: generalSection.fieldsEnabled
                    onTextEdited: generalSection.descriptionUpdated(text)
                }
            }
        }

        // Tags
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 5

            Label {
                text: "Tags:"
            }

            TextField {
                id: tagsField
                Layout.fillWidth: true
                placeholderText: "comma, separated, tags"
                enabled: generalSection.fieldsEnabled
                onTextEdited: generalSection.tagsUpdated(text)
            }
        }
    }
}
