# drone_3d_grid.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QListWidget, QVBoxLayout, QLabel, QMenu,
    QSlider, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import pyqtgraph.opengl as gl

class Drone3DGrid(QWidget):
    # emits (drone_id: int, event_name: str)
    drone_event_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 3D View
        self.view = gl.GLViewWidget()
        self.view.opts['distance'] = 20
        grid = gl.GLGridItem(); grid.scale(1,1,1)
        axes = gl.GLAxisItem(); axes.setSize(x=5, y=5, z=5)
        self.view.addItem(grid); self.view.addItem(axes)

        # Create 16 spheres
        md = gl.MeshData.sphere(rows=10, cols=20, radius=0.3)
        self.spheres = []
        for _ in range(16):
            sph = gl.GLMeshItem(
                meshdata=md, smooth=True, shader='shaded',
                color=(0.4, 0.6, 0.9, 1)
            )
            self.view.addItem(sph)
            self.spheres.append(sph)

        splitter.addWidget(self.view)

        # Control panel
        ctrl = QWidget()
        ctrl_l = QVBoxLayout(ctrl)
        ctrl_l.setSpacing(10)

        # Drone list
        ctrl_l.addWidget(QLabel("Select Drone:"))
        self.drone_list = QListWidget()
        for i in range(16):
            self.drone_list.addItem(f"Drone {i}")
        self.drone_list.itemClicked.connect(self._on_drone_selected)
        ctrl_l.addWidget(self.drone_list)

        # helper to create sliders
        def make_slider(text, mn, mx, val, color):
            lbl = QLabel(f"{text}: {val}")
            lbl.setStyleSheet(f"color: {color};")
            sld = QSlider(Qt.Orientation.Horizontal)
            sld.setRange(mn, mx)
            sld.setValue(val)
            sld.valueChanged.connect(self.update_positions)
            ctrl_l.addWidget(lbl)
            ctrl_l.addWidget(sld)
            return sld, lbl

        self.x_slider,    self.x_label   = make_slider("X spread",  1, 50, 10, "red")
        self.y_slider,    self.y_label   = make_slider("Y spread",  1, 50, 10, "green")
        self.xoff_slider, self.xoff_label= make_slider("X offset", -50,50,  0, "red")
        self.z_slider,    self.z_label   = make_slider("Z offset", -50,50,  0, "blue")
        self.yoff_slider, self.yoff_label= make_slider("Y offset", -50,50,  0, "green")

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_drones)
        ctrl_l.addWidget(reset_btn)

        splitter.addWidget(ctrl)

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.update_positions()

    def showEvent(self, event):
        """Override showEvent to ensure drones are properly positioned when window is shown."""
        super().showEvent(event)
        # Forcer la mise à jour des positions quand la fenêtre est affichée
        self.update_positions()

    def _on_drone_selected(self, item):
        drone_id = int(item.text().split()[1])
        self._show_event_menu(drone_id)

    def _show_event_menu(self, drone_id: int):
        menu = QMenu(self)
        for evt in ("Crash", "Isolation", "Custom…"):
            action = menu.addAction(evt)
            action.triggered.connect(lambda _, e=evt: self._emit_event(drone_id, e))
        menu.exec(QCursor.pos())

    def _emit_event(self, drone_id: int, event_name: str):
        # map events to RGBA colors
        color_map = {
            "Crash":     (1.0, 0.0, 0.0, 1.0),  # red
            "Isolation": (1.0, 1.0, 0.0, 1.0),  # yellow
            "Custom…":   (0.5, 0.5, 0.5, 1.0),  # gray
        }
        c = color_map.get(event_name, (0.4, 0.6, 0.9, 1.0))
        # color the chosen sphere
        if drone_id < len(self.spheres) and self.spheres[drone_id] is not None:
            self.spheres[drone_id].setColor(c)
        # emit and print
        print(f"[Event] Drone {drone_id} → {event_name}")
        self.drone_event_selected.emit(drone_id, event_name)

    def update_positions(self):
        xs    = self.x_slider.value()    / 10.0
        ys    = self.y_slider.value()    / 10.0
        xoff  = self.xoff_slider.value() / 10.0
        zoff  = self.z_slider.value()    / 10.0
        yoff  = self.yoff_slider.value() / 10.0

        self.x_label.setText(f"X spread: {xs:.1f}")
        self.y_label.setText(f"Y spread: {ys:.1f}")
        self.xoff_label.setText(f"X offset: {xoff:.1f}")
        self.z_label.setText(f"Z offset: {zoff:.1f}")
        self.yoff_label.setText(f"Y offset: {yoff:.1f}")

        idx = 0
        for row in range(4):
            for col in range(4):
                x = (col - 1.5) * xs + xoff
                y = (1.5 - row) * ys + yoff
                z = zoff
                
                # S'assurer que la sphère existe avant de la déplacer
                if idx < len(self.spheres) and self.spheres[idx] is not None:
                    sph = self.spheres[idx]
                    sph.resetTransform()
                    sph.translate(x, y, z)
                    # S'assurer que la sphère est visible
                    sph.setVisible(True)
                idx += 1

    def reset_drones(self):
        """Reset all drones to origin positions and default color."""
        # reset sliders to defaults
        self.x_slider.setValue(10)
        self.y_slider.setValue(10)
        self.xoff_slider.setValue(0)
        self.z_slider.setValue(0)
        self.yoff_slider.setValue(0)
        # clear list selection
        self.drone_list.clearSelection()
        # reset colors and ensure visibility
        default_color = (0.4, 0.6, 0.9, 1.0)
        for sph in self.spheres:
            if sph is not None:
                sph.setColor(default_color)
                sph.setVisible(True)
        # reposition
        self.update_positions()
        print("[Reset] All drones reset to origin and default color")

class Drone3DWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Drone Grid")
        self.setCentralWidget(Drone3DGrid(self))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Drone3DWindow()
    w.resize(1000, 600)
    w.show()
    sys.exit(app.exec())