# drone_3d_grid.py

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QListWidget, QVBoxLayout, QLabel, QMenu,
    QSlider, QHBoxLayout, QPushButton, QCheckBox, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QCursor, QWheelEvent
import pyqtgraph.opengl as gl
import pyqtgraph as pg

# Configuration: Change this value to modify the number of drones
NUM_DRONES = 12

class ClickableMeshItem(gl.GLMeshItem):
    """Custom GLMeshItem that can emit click signals"""
    def __init__(self, drone_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drone_id = drone_id
        self.parent_widget = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_widget:
            self.parent_widget._on_drone_clicked(self.drone_id)
        super().mousePressEvent(event)

class ClickableScatterItem(pg.ScatterPlotItem):
    """Custom ScatterPlotItem that handles clicks properly"""
    def __init__(self, drone_id, parent_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drone_id = drone_id
        self.parent_widget = parent_widget
        
    def mouseClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_widget._on_drone_clicked(self.drone_id)
        super().mouseClickEvent(event)

class ZoomableGLViewWidget(gl.GLViewWidget):
    """Custom GLViewWidget with zoom functionality"""
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.zoom_factor = 1.2  # Facteur de zoom
        self.min_distance = 5   # Distance minimale (zoom max)
        self.max_distance = 100 # Distance maximale (zoom min)
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if event.angleDelta().y() > 0:
            # Zoom avant (molette vers le haut)
            self.zoom_in()
        else:
            # Zoom arrière (molette vers le bas)
            self.zoom_out()
        event.accept()
    
    def zoom_in(self):
        """Zoom avant"""
        current_distance = self.opts['distance']
        new_distance = max(self.min_distance, current_distance / self.zoom_factor)
        self.opts['distance'] = new_distance
        self.update()
        if self.parent_widget:
            self.parent_widget._update_zoom_info()
    
    def zoom_out(self):
        """Zoom arrière"""
        current_distance = self.opts['distance']
        new_distance = min(self.max_distance, current_distance * self.zoom_factor)
        self.opts['distance'] = new_distance
        self.update()
        if self.parent_widget:
            self.parent_widget._update_zoom_info()
    
    def reset_zoom(self):
        """Reset le zoom à la valeur par défaut"""
        self.opts['distance'] = 20
        self.update()
        if self.parent_widget:
            self.parent_widget._update_zoom_info()

class Drone3DGrid(QWidget):
    # emits (drone_id: int, event_name: str)
    drone_event_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize mode (True = 3D, False = 2D)
        self.is_3d_mode = True
        
        # Selection state
        self.selected_drones = set()
        
        # Initialize positions first
        self._define_sphere_positions()
        self._define_circle_positions()
        
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Create stacked widget to hold both 3D and 2D views
        self.view_stack = QStackedWidget()
        
        # 3D View setup with zoom functionality
        self.view_3d = ZoomableGLViewWidget(parent_widget=self)
        self.view_3d.opts['distance'] = 20
        grid = gl.GLGridItem(); grid.scale(1,1,1)
        axes = gl.GLAxisItem(); axes.setSize(x=5, y=5, z=5)
        self.view_3d.addItem(grid); self.view_3d.addItem(axes)
        
        # 2D View setup with zoom functionality
        self.view_2d = pg.PlotWidget()
        self.view_2d.setAspectLocked(True)
        self.view_2d.setLabel('left', 'Y')
        self.view_2d.setLabel('bottom', 'X')
        self.view_2d.setTitle('2D Drone Formation (Top View)')
        self.view_2d.showGrid(x=True, y=True)
        self.view_2d.setXRange(-6, 6)
        self.view_2d.setYRange(-6, 6)
        
        # Add both views to stack
        self.view_stack.addWidget(self.view_3d)
        self.view_stack.addWidget(self.view_2d)
        self.view_stack.setCurrentWidget(self.view_3d)

        # Create 3D spheres with click detection
        md = gl.MeshData.sphere(rows=10, cols=20, radius=0.3)
        self.spheres_3d = []
        
        for i in range(NUM_DRONES):
            sph = ClickableMeshItem(
                drone_id=i,
                meshdata=md, 
                smooth=True, 
                shader='shaded',
                color=(0.4, 0.6, 0.9, 1)
            )
            sph.parent_widget = self
            self.view_3d.addItem(sph)
            self.spheres_3d.append(sph)

        # Create 2D circles with click detection
        self.circles_2d = []
        for i in range(NUM_DRONES):
            scatter = ClickableScatterItem(
                drone_id=i,
                parent_widget=self,
                x=[0], y=[0], 
                size=30,
                brush=pg.mkBrush(100, 150, 200, 200),
                pen=pg.mkPen('blue', width=2),
                symbol='o'
            )
            self.view_2d.addItem(scatter)
            self.circles_2d.append(scatter)

        # Position 2D circles initially
        self._position_2d_circles_initially()

        # Add right-click context menu to both views
        self.view_3d.mousePressEvent = self._on_view_click
        self.view_2d.mousePressEvent = self._on_view_click

        splitter.addWidget(self.view_stack)

        # Control panel
        ctrl = QWidget()
        ctrl_l = QVBoxLayout(ctrl)
        ctrl_l.setSpacing(10)

        # 3D/2D Mode toggle
        self.mode_checkbox = QCheckBox("3D Mode (uncheck for 2D disc)")
        self.mode_checkbox.setChecked(True)
        self.mode_checkbox.stateChanged.connect(self._toggle_mode)
        ctrl_l.addWidget(self.mode_checkbox)

        # Zoom controls section
        zoom_label = QLabel("Zoom Controls:")
        zoom_label.setStyleSheet("font-weight: bold; color: navy;")
        ctrl_l.addWidget(zoom_label)
        
        zoom_controls = QHBoxLayout()
        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_out_btn = QPushButton("Zoom -")
        self.zoom_reset_btn = QPushButton("Reset")
        
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        self.zoom_reset_btn.clicked.connect(self._reset_zoom)
        
        zoom_controls.addWidget(self.zoom_in_btn)
        zoom_controls.addWidget(self.zoom_out_btn)
        zoom_controls.addWidget(self.zoom_reset_btn)
        ctrl_l.addLayout(zoom_controls)
        
        # Zoom info label
        self.zoom_info_label = QLabel("Distance: 20.0")
        self.zoom_info_label.setStyleSheet("color: darkblue; font-size: 10px;")
        ctrl_l.addWidget(self.zoom_info_label)
        
        # Instructions
        zoom_help = QLabel("💡 Utilisez la molette de la souris pour zoomer")
        zoom_help.setStyleSheet("color: gray; font-size: 9px; font-style: italic;")
        zoom_help.setWordWrap(True)
        ctrl_l.addWidget(zoom_help)

        # Selection info
        self.selection_label = QLabel("No drones selected")
        self.selection_label.setStyleSheet("font-weight: bold; color: purple;")
        ctrl_l.addWidget(self.selection_label)

        # Drone list
        ctrl_l.addWidget(QLabel("Drone List:"))
        self.drone_list = QListWidget()
        self.drone_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for i in range(NUM_DRONES):
            self.drone_list.addItem(f"Drone {i}")
        self.drone_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        ctrl_l.addWidget(self.drone_list)

        # Clear selection button
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self._clear_selection)
        ctrl_l.addWidget(clear_btn)

        # Select all button
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        ctrl_l.addWidget(select_all_btn)

        # Create sliders
        self.r_slider, self.r_label = self._make_slider("R spread", 0, 50, 20, "purple", ctrl_l)
        self.xoff_slider, self.xoff_label = self._make_slider("X offset", -50, 50, 0, "red", ctrl_l)
        self.yoff_slider, self.yoff_label = self._make_slider("Y offset", -50, 50, 0, "green", ctrl_l)
        self.z_slider, self.z_label = self._make_slider("Z offset", -50, 50, 0, "blue", ctrl_l)

        # Event assignment button
        self.assign_event_btn = QPushButton("Assign Event to Selected")
        self.assign_event_btn.clicked.connect(self._show_event_menu_for_selected)
        self.assign_event_btn.setEnabled(False)
        ctrl_l.addWidget(self.assign_event_btn)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_drones)
        ctrl_l.addWidget(reset_btn)

        splitter.addWidget(ctrl)

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Initial setup
        self._update_ui_for_mode()
        self.update_positions()
        self._update_selection_info()
        self._update_zoom_info()

    def _zoom_in(self):
        """Zoom avant via bouton"""
        if self.is_3d_mode:
            self.view_3d.zoom_in()
        else:
            self.view_2d.getViewBox().scaleBy((0.8, 0.8))

    def _zoom_out(self):
        """Zoom arrière via bouton"""
        if self.is_3d_mode:
            self.view_3d.zoom_out()
        else:
            self.view_2d.getViewBox().scaleBy((1.25, 1.25))

    def _reset_zoom(self):
        """Reset du zoom via bouton"""
        if self.is_3d_mode:
            self.view_3d.reset_zoom()
        else:
            self.view_2d.setXRange(-6, 6)
            self.view_2d.setYRange(-6, 6)

    def _update_zoom_info(self):
        """Met à jour l'affichage des informations de zoom"""
        if self.is_3d_mode:
            distance = self.view_3d.opts['distance']
            self.zoom_info_label.setText(f"Distance: {distance:.1f}")
        else:
            view_range = self.view_2d.getViewBox().viewRange()
            x_range = view_range[0][1] - view_range[0][0]
            self.zoom_info_label.setText(f"View range: {x_range:.1f}")

    def _make_slider(self, text, mn, mx, val, color, parent_layout):
        """Helper method to create sliders"""
        lbl = QLabel(f"{text}: {val}")
        lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
        sld = QSlider(Qt.Orientation.Horizontal)
        sld.setRange(mn, mx)
        sld.setValue(val)
        sld.valueChanged.connect(self.update_positions)
        parent_layout.addWidget(lbl)
        parent_layout.addWidget(sld)
        return sld, lbl

    def _toggle_mode(self, checked):
        """Toggle between 3D and 2D mode"""
        self.is_3d_mode = checked
        self._update_ui_for_mode()
        self.update_positions()
        self._update_visual_selection()
        self._update_zoom_info()
        
        mode_text = "3D Sphere" if self.is_3d_mode else "2D Disc"
        print(f"[Mode] Switched to {mode_text} mode")

    def _update_ui_for_mode(self):
        """Update UI elements based on current mode"""
        if self.is_3d_mode:
            self.view_stack.setCurrentWidget(self.view_3d)
            self.z_slider.setVisible(True)
            self.z_label.setVisible(True)
        else:
            self.view_stack.setCurrentWidget(self.view_2d)
            self.z_slider.setVisible(False)
            self.z_label.setVisible(False)

    def _define_sphere_positions(self):
        """Define positions for drones arranged in a symmetric sphere"""
        if NUM_DRONES == 12:
            # Icosahedron vertices - most symmetric for 12 points
            phi = (1 + np.sqrt(5)) / 2  # Golden ratio
            vertices = [
                (0, 1, phi), (0, -1, phi), (0, 1, -phi), (0, -1, -phi),
                (1, phi, 0), (-1, phi, 0), (1, -phi, 0), (-1, -phi, 0),
                (phi, 0, 1), (phi, 0, -1), (-phi, 0, 1), (-phi, 0, -1)
            ]
            self.sphere_positions = []
            for x, y, z in vertices:
                norm = np.sqrt(x*x + y*y + z*z)
                self.sphere_positions.append((x/norm, y/norm, z/norm))
        else:
            # Fallback: Fibonacci spiral distribution
            indices = np.arange(0, NUM_DRONES, dtype=float) + 0.5
            theta = np.arccos(1 - 2*indices/NUM_DRONES)
            phi = np.pi * (1 + 5**0.5) * indices
            
            self.sphere_positions = []
            for t, p in zip(theta, phi):
                x = np.sin(t) * np.cos(p)
                y = np.sin(t) * np.sin(p)
                z = np.cos(t)
                self.sphere_positions.append((x, y, z))

    def _define_circle_positions(self):
        """Define positions for drones arranged in a 2D circle"""
        angles = np.linspace(0, 2*np.pi, NUM_DRONES, endpoint=False)
        self.circle_positions = []
        for angle in angles:
            x = np.cos(angle)
            y = np.sin(angle)
            self.circle_positions.append((x, y))

    def _position_2d_circles_initially(self):
        """Position 2D circles with initial spread"""
        r_spread = 2.0  # Default spread value
        for i, (base_x, base_y) in enumerate(self.circle_positions):
            if i < len(self.circles_2d):
                x = base_x * r_spread
                y = base_y * r_spread
                self.circles_2d[i].setData(x=[x], y=[y])

    def _on_drone_clicked(self, drone_id):
        """Handle drone click - toggle selection"""
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Click: Add to selection
            self.selected_drones.add(drone_id)
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            # Shift+Click: Remove from selection
            self.selected_drones.discard(drone_id)
        else:
            # Normal click: Toggle selection
            if drone_id in self.selected_drones:
                self.selected_drones.remove(drone_id)
            else:
                self.selected_drones.add(drone_id)
        
        print(f"[Click] Drone {drone_id} clicked. Selected: {sorted(list(self.selected_drones))}")
        self._update_visual_selection()
        self._update_list_selection()
        self._update_selection_info()

    def _on_view_click(self, event):
        """Handle clicks on empty areas and right-click context menu"""
        if event.button() == Qt.MouseButton.RightButton and self.selected_drones:
            self._show_event_menu_for_selected()

    def _on_list_selection_changed(self):
        """Handle list selection change"""
        selected_items = self.drone_list.selectedItems()
        new_selection = set()
        
        for item in selected_items:
            drone_id = int(item.text().split()[1])
            new_selection.add(drone_id)
        
        self.selected_drones = new_selection
        print(f"[List] Selection changed: {sorted(list(self.selected_drones))}")
        self._update_visual_selection()
        self._update_selection_info()

    def _update_visual_selection(self):
        """Update visual appearance of selected drones"""
        # Update 3D spheres
        for i, sphere in enumerate(self.spheres_3d):
            if i in self.selected_drones:
                sphere.setColor((1.0, 1.0, 0.0, 1.0))  # Yellow
            else:
                sphere.setColor((0.4, 0.6, 0.9, 1.0))  # Blue
        
        # Update 2D circles
        for i, scatter in enumerate(self.circles_2d):
            if i in self.selected_drones:
                scatter.setBrush(pg.mkBrush(255, 255, 0, 200))  # Yellow
                scatter.setPen(pg.mkPen('orange', width=3))
                scatter.setSize(35)  # Bigger when selected
            else:
                scatter.setBrush(pg.mkBrush(100, 150, 200, 200))  # Blue
                scatter.setPen(pg.mkPen('blue', width=2))
                scatter.setSize(30)  # Normal size

    def _update_list_selection(self):
        """Update list widget to match drone selection"""
        self.drone_list.blockSignals(True)
        self.drone_list.clearSelection()
        
        for i in range(self.drone_list.count()):
            item = self.drone_list.item(i)
            drone_id = int(item.text().split()[1])
            if drone_id in self.selected_drones:
                item.setSelected(True)
        
        self.drone_list.blockSignals(False)

    def _update_selection_info(self):
        """Update selection information label"""
        count = len(self.selected_drones)
        if count == 0:
            self.selection_label.setText("No drones selected")
            self.assign_event_btn.setEnabled(False)
        elif count == 1:
            drone_id = list(self.selected_drones)[0]
            self.selection_label.setText(f"Drone {drone_id} selected")
            self.assign_event_btn.setEnabled(True)
        else:
            self.selection_label.setText(f"{count} drones selected")
            self.assign_event_btn.setEnabled(True)

    def _clear_selection(self):
        """Clear all selections"""
        self.selected_drones.clear()
        print("[Clear] All selections cleared")
        self._update_visual_selection()
        self._update_list_selection()
        self._update_selection_info()

    def _select_all(self):
        """Select all drones"""
        self.selected_drones = set(range(NUM_DRONES))
        print("[Select All] All drones selected")
        self._update_visual_selection()
        self._update_list_selection()
        self._update_selection_info()

    def _show_event_menu_for_selected(self):
        """Show event menu for selected drones"""
        if not self.selected_drones:
            return
            
        menu = QMenu(self)
        for evt in ("Crash", "Isolation", "Custom…"):
            action = menu.addAction(f"{evt} ({len(self.selected_drones)} drones)")
            action.triggered.connect(lambda _, e=evt: self._assign_event_to_selected(e))
        menu.exec(QCursor.pos())

    def _assign_event_to_selected(self, event_name: str):
        """Assign event to selected drones"""
        color_map_3d = {
            "Crash": (1.0, 0.0, 0.0, 1.0),  # red
            "Isolation": (1.0, 0.5, 0.0, 1.0),  # orange
            "Custom…": (0.5, 0.5, 0.5, 1.0),  # gray
        }
        
        color_map_2d = {
            "Crash": (255, 0, 0, 200),
            "Isolation": (255, 128, 0, 200),
            "Custom…": (128, 128, 128, 200),
        }
        
        for drone_id in self.selected_drones:
            # Update 3D sphere
            if drone_id < len(self.spheres_3d):
                color_3d = color_map_3d.get(event_name, (0.4, 0.6, 0.9, 1.0))
                self.spheres_3d[drone_id].setColor(color_3d)
            
            # Update 2D circle
            if drone_id < len(self.circles_2d):
                color_2d = color_map_2d.get(event_name, (100, 150, 200, 200))
                self.circles_2d[drone_id].setBrush(pg.mkBrush(*color_2d))
            
            print(f"[Event] Drone {drone_id} → {event_name}")
            self.drone_event_selected.emit(drone_id, event_name)

    def update_positions(self):
        """Update drone positions based on slider values"""
        r_spread = self.r_slider.value() / 10.0
        xoff = self.xoff_slider.value() / 10.0
        yoff = self.yoff_slider.value() / 10.0
        zoff = self.z_slider.value() / 10.0 if self.is_3d_mode else 0.0

        # Update labels
        self.r_label.setText(f"R spread: {r_spread:.1f}")
        self.xoff_label.setText(f"X offset: {xoff:.1f}")
        self.yoff_label.setText(f"Y offset: {yoff:.1f}")
        if self.is_3d_mode:
            self.z_label.setText(f"Z offset: {zoff:.1f}")

        # Update 3D spheres
        for i, (base_x, base_y, base_z) in enumerate(self.sphere_positions):
            if i < len(self.spheres_3d):
                x = base_x * r_spread + xoff
                y = base_y * r_spread + yoff
                z = base_z * r_spread + zoff
                
                sphere = self.spheres_3d[i]
                sphere.resetTransform()
                sphere.translate(x, y, z)

        # Update 2D circles
        for i, (base_x, base_y) in enumerate(self.circle_positions):
            if i < len(self.circles_2d):
                x = base_x * r_spread + xoff
                y = base_y * r_spread + yoff
                self.circles_2d[i].setData(x=[x], y=[y])

    def reset_drones(self):
        """Reset all drones to default state"""
        # Reset sliders
        self.r_slider.setValue(20)
        self.xoff_slider.setValue(0)
        self.yoff_slider.setValue(0)
        self.z_slider.setValue(0)
        
        # Clear selections
        self._clear_selection()
        
        # Reset colors
        default_color_3d = (0.4, 0.6, 0.9, 1.0)
        for sphere in self.spheres_3d:
            sphere.setColor(default_color_3d)
        
        for scatter in self.circles_2d:
            scatter.setBrush(pg.mkBrush(100, 150, 200, 200))
            scatter.setPen(pg.mkPen('blue', width=2))
            scatter.setSize(30)
        
        # Reset zoom
        self._reset_zoom()
        
        # Reposition
        self.update_positions()
        
        print(f"[Reset] All {NUM_DRONES} drones reset")

    def showEvent(self, event):
        """Ensure proper positioning when window is shown"""
        super().showEvent(event)
        self.update_positions()

class Drone3DWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D/2D Drone Grid - Click to Select - Zoom avec molette")
        self.setCentralWidget(Drone3DGrid(self))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Drone3DWindow()
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec())