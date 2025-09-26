import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    minimumWidth: 520
    minimumHeight: 360
    width: 580
    height: 420
    title: "Source Section Preview"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Item {
            id: sectionContainer
            Layout.fillWidth: true
            Layout.fillHeight: true

            implicitHeight: sectionLoader.item ? sectionLoader.item.height : 0

            Loader {
                id: sectionLoader
                anchors.fill: parent
                source: "../../metaeditor_safetensors/qml/views/SourceSection.qml"
                onLoaded: {
                    if (!item) {
                        return;
                    }
                    item.width = sectionContainer.width;
                    if (item.setAuthor) {
                        item.setAuthor("Jane Doe");
                    }
                    if (item.setDate) {
                        item.setDate("2024-09-25T08:30:00.000");
                    }
                    if (item.setMergedFrom) {
                        item.setMergedFrom("model_a.safetensors, model_b.safetensors");
                    }
                }
            }

            onWidthChanged: {
                if (sectionLoader.item) {
                    sectionLoader.item.width = width;
                }
            }
        }

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Interact with the fields above to verify bindings. Updates are logged to the console."
        }

        Button {
            text: "Toggle Enabled"
            onClicked: {
                if (sectionLoader.item) {
                    sectionLoader.item.fieldsEnabled = !sectionLoader.item.fieldsEnabled;
                }
            }
        }
    }

    Connections {
        target: sectionLoader.item
        function onAuthorUpdated(text) {
            console.log("authorUpdated:", text);
        }
        function onDateUpdated(isoDate) {
            console.log("dateUpdated:", isoDate);
        }
        function onMergedFromUpdated(text) {
            console.log("mergedFromUpdated:", text);
        }
    }
}
