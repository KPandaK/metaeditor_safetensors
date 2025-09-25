from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class CollapsibleSection(QFrame):
    def __init__(self, parent=None, title="Section", expanded=True):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self._expanded = expanded
        self._animation_duration = 400
        self._animation_callback = None
        self._desired_height = 0

        # Set size policy to allow height changes
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Create UI components
        self._create_header(title)
        self._create_content_area()

        # Setup smooth expand/collapse animation
        self.animation = QPropertyAnimation(self, b"contentHeight")
        self.animation.setDuration(self._animation_duration)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Set initial state
        self._set_initial_state(expanded)

    def _create_header(self, title):
        self.header_widget = QWidget(self)
        self.header_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.toggle_button.setIconSize(QSize(10, 10))
        self.toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.toggle_button.clicked.connect(self.toggle)

        header_layout.addWidget(self.toggle_button)

        # Position header at top using calculated margins
        left, top, right, bottom = self._get_margins()
        header_width = max(200, self.width() - left - right)
        self.header_widget.setGeometry(
            left, top, header_width, self.header_widget.sizeHint().height()
        )

    def _get_margins(self):
        margins = self.contentsMargins()
        return margins.left(), margins.top(), margins.right(), margins.bottom()

    def _get_header_height(self):
        if hasattr(self, "header_widget"):
            return self.header_widget.sizeHint().height()
        return 32  # Fallback default

    def _create_content_area(self):
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("CollapsibleContent")
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 5, 5)
        self.content_layout.setSpacing(5)

        # Position content below header using calculated values
        left, top, right, bottom = self._get_margins()
        header_height = self._get_header_height()
        content_top = top + header_height
        content_width = max(200, self.width() - left - right)
        self.content_widget.setGeometry(left, content_top, content_width, 0)

    def _set_initial_state(self, expanded):
        self._expanded = expanded
        self.toggle_button.setChecked(expanded)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )

        if expanded:
            self.content_widget.show()
            # Start with minimal height - will be updated when content is added
            self.set_content_height(10)
        else:
            self.set_content_height(0)
            self.content_widget.hide()

    # Content height property for animation
    def get_content_height(self):
        return self.content_widget.height() if hasattr(self, "content_widget") else 0

    def set_content_height(self, height):
        if hasattr(self, "content_widget"):
            height = int(height)
            left, top, right, bottom = self._get_margins()
            header_height = self._get_header_height()
            content_top = top + header_height
            content_width = max(200, self.width() - left - right)

            self.content_widget.setGeometry(left, content_top, content_width, height)
            # Store the desired height for size hint calculations
            self._desired_height = top + header_height + height + bottom
            # Allow the layout to adjust our size naturally
            self.updateGeometry()

    contentHeight = Property(int, get_content_height, set_content_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "header_widget"):
            left, top, right, bottom = self._get_margins()
            header_width = self.width() - left - right
            header_height = self.header_widget.sizeHint().height()
            self.header_widget.setGeometry(left, top, header_width, header_height)

        if hasattr(self, "content_widget"):
            left, top, right, bottom = self._get_margins()
            header_height = self._get_header_height()
            content_top = top + header_height
            content_width = self.width() - left - right
            current_height = self.content_widget.height()
            self.content_widget.setGeometry(
                left, content_top, content_width, current_height
            )

    def sizeHint(self):
        if hasattr(self, "_desired_height") and self._desired_height > 0:
            return QSize(200, self._desired_height)
        else:
            # Fallback for initial sizing - provide minimum size
            left, top, right, bottom = self._get_margins()
            header_height = self._get_header_height()
            content_height = self.get_content_height() if self._expanded else 0
            total_height = top + header_height + content_height + bottom
            return QSize(200, max(total_height, header_height + top + bottom))

    def minimumSizeHint(self):
        left, top, right, bottom = self._get_margins()
        header_height = self._get_header_height()
        return QSize(200, top + header_height + bottom)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def _update_content_size(self):
        if self._expanded and hasattr(self, "content_widget"):
            # Get the natural size hint from the content
            natural_height = self.content_widget.sizeHint().height()
            if natural_height > 0:
                self.set_content_height(natural_height)

    def setExpanded(self, expanded):
        if self._expanded == expanded:
            return

        self._expanded = expanded
        self.toggle_button.setChecked(expanded)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )

        # Cleanup previous animation
        if self._animation_callback:
            try:
                self.animation.finished.disconnect(self._animation_callback)
            except (TypeError, RuntimeError):
                pass

        # Calculate animation range
        start_height = self.get_content_height()
        target_height = (
            max(100, self.content_widget.sizeHint().height()) if expanded else 0
        )

        # Setup animation
        self.animation.setStartValue(start_height)
        self.animation.setEndValue(target_height)

        # Animation completion callback
        def on_finished():
            if expanded:
                self.content_widget.show()
            else:
                self.content_widget.hide()
            self._animation_callback = None

        self._animation_callback = on_finished
        self.animation.finished.connect(self._animation_callback)

        # Ensure content is visible during animation
        if expanded:
            self.content_widget.show()

        self.animation.start()

    def toggle(self):
        self.setExpanded(self.toggle_button.isChecked())

    def isExpanded(self):
        return self._expanded

    def setTitle(self, title):
        self.toggle_button.setText(title)

    def showEvent(self, event):
        super().showEvent(event)
        if self._expanded:
            self._update_content_size()
