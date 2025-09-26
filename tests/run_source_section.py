import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType

from metaeditor_safetensors.qml.components.date_time_edit_bridge import (
    QDateTimeEditBridge,
)


def main() -> int:
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    qmlRegisterType(QDateTimeEditBridge, "MetaEditor.Controls", 1, 0, "QDateTimeEditBridge")

    qml_dir = Path(__file__).resolve().parent / "qml"
    qml_file = qml_dir / "SourceSectionTest.qml"

    if not qml_file.exists():
        print(f"Unable to locate QML harness: {qml_file}")
        return 1

    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
