# drone_grid_window.py

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
    QMenu, QSlider, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
from drone_widget import DroneCircle

class DroneGridWindow(QDialog):
    drone_event_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Drone Event Console")

        # ─── Main horizontal layout ───────────────────────────────────────────
        self.main_layout = QHBoxLayout(self)

        # ─── Left side: grid + width slider ─────────────────────────────────
        left_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        left_layout.addLayout(self.grid_layout)
        self.drone_widgets = {}
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)


        # populate 4×4 grid of circles
        for row in range(4):
            for col in range(4):
                drone_id = row * 4 + col
                w = DroneCircle(drone_id, diameter=60)
                w.clicked.connect(lambda d=drone_id: self._show_event_menu(d))
                self.grid_layout.addWidget(w, row, col)
                self.drone_widgets[drone_id] = w

        # width slider + label
        self.width_label = QLabel("Width spacing: 50 px", self)
        self.width_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.width_slider.setRange(0, 100)
        self.width_slider.setValue(50)
        self.width_slider.valueChanged.connect(self.on_width_changed)

        width_layout = QHBoxLayout()
        width_layout.addWidget(self.width_label)
        width_layout.addWidget(self.width_slider)
        left_layout.addLayout(width_layout)

        self.main_layout.addLayout(left_layout)

        # ─── Right side: height slider ───────────────────────────────────────
        right_layout = QVBoxLayout()
        self.height_label = QLabel("Height spacing: 50 px", self)
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.height_label)

        self.height_slider = QSlider(Qt.Orientation.Vertical, self)
        self.height_slider.setRange(0, 100)
        self.height_slider.setValue(50)
        self.height_slider.valueChanged.connect(self.on_height_changed)
        right_layout.addWidget(self.height_slider)

        self.main_layout.addLayout(right_layout)

        # initialize spacing
        self.on_width_changed(50)
        self.on_height_changed(50)

    def _show_event_menu(self, drone_id: int):
        menu = QMenu(self)
        for evt in ("Crash", "Isolation", "Selection", "Other"):
            action = menu.addAction(evt)
            action.triggered.connect(lambda checked=False, e=evt: self._emit_event(drone_id, e))
        menu.exec(QCursor.pos())

    def _emit_event(self, drone_id: int, event_name: str):
        self.drone_widgets[drone_id].update_color_for_event(event_name)
        self.drone_event_selected.emit(drone_id, event_name)

    def on_width_changed(self, value: int):
        """Adjust horizontal spacing and update label."""
        self.grid_layout.setHorizontalSpacing(value)
        self.width_label.setText(f"Width spacing: {value} px")

    def on_height_changed(self, value: int):
        """Adjust vertical spacing and update label."""
        self.grid_layout.setVerticalSpacing(value)
        self.height_label.setText(f"Height spacing: {value} px")
