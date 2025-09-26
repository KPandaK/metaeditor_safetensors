import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MetaEditor.Controls 1.0
import "../components"

ExpandableSection {
    id: sourceSection
    title: "Source"
    Layout.fillWidth: true
    expanded: true

    property alias author: authorField.text
    property alias mergedFrom: mergedFromField.text
    property alias dateControl: dateTimeEdit
    property bool fieldsEnabled: true

    readonly property string dateIsoString: dateTimeEdit.isoDateTime

    signal authorUpdated(string text)
    signal dateUpdated(string isoDateTime)
    signal mergedFromUpdated(string text)

    property bool _suppressDateSignal: false

    function setAuthor(newAuthor) {
        const value = newAuthor ? newAuthor : "";
        if (authorField.text !== value) {
            authorField.text = value;
        }
    }

    function setDate(isoString) {
        if (!isoString) {
            return;
        }
        _suppressDateSignal = true;
        dateTimeEdit.isoDateTime = isoString;
        Qt.callLater(function () {
            _suppressDateSignal = false;
        });
    }

    function setMergedFrom(value) {
        const textValue = value ? value : "";
        if (mergedFromField.text !== textValue) {
            mergedFromField.text = textValue;
        }
    }

    ColumnLayout {
        id: content
        spacing: 12
        Layout.fillWidth: true

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Label {
                    text: "Author:"
                }

                TextField {
                    id: authorField
                    Layout.fillWidth: true
                    placeholderText: "Author name or organization."
                    enabled: sourceSection.fieldsEnabled
                    onTextEdited: sourceSection.authorUpdated(text)
                }
            }

            ColumnLayout {
                spacing: 4

                Label {
                    text: "Date:"
                }

                QDateTimeEditBridge {
                    id: dateTimeEdit
                    Layout.preferredWidth: 180
                    displayFormat: "MM/dd/yyyy h:mm AP"
                    calendarPopup: true
                    enabled: sourceSection.fieldsEnabled
                    onEditingFinished: sourceSection.dateUpdated(isoDateTime)
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4

            Label {
                text: "Merged From:"
            }

            TextField {
                id: mergedFromField
                Layout.fillWidth: true
                placeholderText: "Source models, if merged from other models."
                enabled: sourceSection.fieldsEnabled
                onTextEdited: sourceSection.mergedFromUpdated(text)
            }
        }
    }

    Connections {
        target: dateTimeEdit
        function onIsoDateTimeChanged(value) {
            if (!sourceSection._suppressDateSignal) {
                sourceSection.dateUpdated(value);
            }
        }
    }
}
