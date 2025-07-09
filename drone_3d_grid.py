# drone_3d_grid.py

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QListWidget, QVBoxLayout, QLabel, QMenu,
    QSlider, QHBoxLayout, QPushButton, QCheckBox, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import pyqtgraph.opengl as gl
import pyqtgraph as pg

# Configuration: Change this value to modify the number of drones
NUM_DRONES = 12

class Drone3DGrid(QWidget):
    # emits (drone_id: int, event_name: str)
    drone_event_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize mode (True = 3D, False = 2D)
        self.is_3d_mode = True
        
        # Initialize positions first
        self._define_sphere_positions()
        self._define_circle_positions()
        
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Create stacked widget to hold both 3D and 2D views
        self.view_stack = QStackedWidget()
        
        # 3D View setup
        self.view_3d = gl.GLViewWidget()
        self.view_3d.opts['distance'] = 20
        grid = gl.GLGridItem(); grid.scale(1,1,1)
        axes = gl.GLAxisItem(); axes.setSize(x=5, y=5, z=5)
        self.view_3d.addItem(grid); self.view_3d.addItem(axes)
        
        # 2D View setup
        self.view_2d = pg.PlotWidget()
        self.view_2d.setAspectLocked(True)
        self.view_2d.setLabel('left', 'Y')
        self.view_2d.setLabel('bottom', 'X')
        self.view_2d.setTitle('2D Drone Formation (Top View)')
        self.view_2d.showGrid(x=True, y=True)
        # Set reasonable axis ranges to see the radial effect
        self.view_2d.setXRange(-6, 6)
        self.view_2d.setYRange(-6, 6)
        
        # Add both views to stack
        self.view_stack.addWidget(self.view_3d)
        self.view_stack.addWidget(self.view_2d)
        self.view_stack.setCurrentWidget(self.view_3d)

        # Create spheres for 3D view
        md = gl.MeshData.sphere(rows=10, cols=20, radius=0.3)
        self.spheres_3d = []
        self.selected_drones = set()  # Track selected drones
        
        for _ in range(NUM_DRONES):
            sph = gl.GLMeshItem(
                meshdata=md, smooth=True, shader='shaded',
                color=(0.4, 0.6, 0.9, 1)
            )
            self.view_3d.addItem(sph)
            self.spheres_3d.append(sph)

        # Create circles for 2D view using ScatterPlotItem
        self.circles_2d = []
        for i in range(NUM_DRONES):
            # Create individual scatter points for each drone
            scatter = pg.ScatterPlotItem(
                x=[0], y=[0], 
                size=30,  # Increased size for better visibility
                brush=pg.mkBrush(100, 150, 200, 150),
                pen=pg.mkPen('blue', width=2),
                symbol='o'
            )
            scatter.sigClicked.connect(lambda obj, points, drone_id=i: self._on_2d_drone_click(drone_id))
            self.view_2d.addItem(scatter)
            self.circles_2d.append(scatter)

        # Position 2D circles initially
        self._position_2d_circles_initially()

        # Add click detection to the 3D view
        self.view_3d.mousePressEvent = self._on_3d_click

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

        # Drone list
        ctrl_l.addWidget(QLabel("Select Drone(s):"))
        self.drone_list = QListWidget()
        self.drone_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for i in range(NUM_DRONES):
            self.drone_list.addItem(f"Drone {i}")
        self.drone_list.itemClicked.connect(self._on_list_item_clicked)
        self.drone_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        ctrl_l.addWidget(self.drone_list)

        # Create sliders - R spread starts at 20 for better initial visibility
        self.r_slider, self.r_label = self._make_slider("R spread", 0, 50, 20, "purple", ctrl_l)
        self.xoff_slider, self.xoff_label = self._make_slider("X offset", -50, 50, 0, "red", ctrl_l)
        self.yoff_slider, self.yoff_label = self._make_slider("Y offset", -50, 50, 0, "green", ctrl_l)
        self.z_slider, self.z_label = self._make_slider("Z offset", -50, 50, 0, "blue", ctrl_l)

        # Event assignment button
        self.assign_event_btn = QPushButton("Assign Event to Selected")
        self.assign_event_btn.clicked.connect(self._show_event_menu_for_selected)
        ctrl_l.addWidget(self.assign_event_btn)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_drones)
        ctrl_l.addWidget(reset_btn)

        splitter.addWidget(ctrl)

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Initial positioning
        self._update_ui_for_mode()
        self.update_positions()

    def _make_slider(self, text, mn, mx, val, color, parent_layout):
        """Helper method to create sliders"""
        lbl = QLabel(f"{text}: {val}")
        lbl.setStyleSheet(f"color: {color};")
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
        
        mode_text = "3D Sphere" if self.is_3d_mode else "2D Disc"
        print(f"[Mode] Switched to {mode_text} mode")

    def _update_ui_for_mode(self):
        """Update UI elements based on current mode"""
        if self.is_3d_mode:
            # 3D mode: show 3D view and Z offset slider
            self.view_stack.setCurrentWidget(self.view_3d)
            self.z_slider.setVisible(True)
            self.z_label.setVisible(True)
            self.z_label.setText("Z offset (3D)")
        else:
            # 2D mode: show 2D view and hide Z offset slider
            self.view_stack.setCurrentWidget(self.view_2d)
            self.z_slider.setVisible(False)
            self.z_label.setVisible(False)

    def _position_2d_circles_initially(self):
        """Position 2D circles with initial spread"""
        r_spread = 2.0  # Default spread value (slider initial value 20 / 10)
        positions = self.circle_positions
        print(f"[2D Init] Positioning {len(positions)} circles with r_spread={r_spread}")
        
        for i, (base_x, base_y) in enumerate(positions):
            if i < len(self.circles_2d) and self.circles_2d[i] is not None:
                # Radial positioning: multiply by radius
                x = base_x * r_spread
                y = base_y * r_spread
                
                # Debug first few positions
                if i < 3:
                    print(f"[2D Init] Drone {i}: base=({base_x:.2f}, {base_y:.2f}) -> final=({x:.2f}, {y:.2f})")
                
                # Update scatter position
                scatter = self.circles_2d[i]
                scatter.setData(x=[x], y=[y])

    def _define_sphere_positions(self):
        """Define positions for drones arranged in a symmetric sphere"""
        if NUM_DRONES == 12:
            # Icosahedron vertices - most symmetric for 12 points
            phi = (1 + np.sqrt(5)) / 2  # Golden ratio
            
            # Icosahedron vertices in cartesian coordinates (normalized)
            vertices = [
                (0, 1, phi), (0, -1, phi), (0, 1, -phi), (0, -1, -phi),
                (1, phi, 0), (-1, phi, 0), (1, -phi, 0), (-1, -phi, 0),
                (phi, 0, 1), (phi, 0, -1), (-phi, 0, 1), (-phi, 0, -1)
            ]
            
            # Normalize vertices to unit sphere
            self.sphere_positions = []
            for x, y, z in vertices:
                norm = np.sqrt(x*x + y*y + z*z)
                self.sphere_positions.append((x/norm, y/norm, z/norm))
                
        elif NUM_DRONES == 8:
            # Cube vertices
            self.sphere_positions = [
                (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
                (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)
            ]
            # Normalize to unit sphere
            self.sphere_positions = [(x/np.sqrt(3), y/np.sqrt(3), z/np.sqrt(3)) 
                                   for x, y, z in self.sphere_positions]
                                       
        elif NUM_DRONES == 6:
            # Octahedron vertices
            self.sphere_positions = [
                (1, 0, 0), (-1, 0, 0), (0, 1, 0), 
                (0, -1, 0), (0, 0, 1), (0, 0, -1)
            ]
            
        else:
            # Fallback: distribute points on sphere using Fibonacci spiral
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
        # Distribute drones evenly around a circle with radius = 1
        angles = np.linspace(0, 2*np.pi, NUM_DRONES, endpoint=False)
        
        self.circle_positions = []
        for angle in angles:
            x = np.cos(angle)
            y = np.sin(angle)
            self.circle_positions.append((x, y))
        
        print(f"[2D] Circle positions defined for {NUM_DRONES} drones")
        print(f"[2D] Sample positions: {self.circle_positions[:3]}")  # Debug: show first 3 positions

    def _on_3d_click(self, event):
        """Handle clicks on the 3D view to select drones"""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_event_menu_for_selected()

    def _on_2d_drone_click(self, drone_id):
        """Handle clicks on 2D drones"""
        # Toggle selection
        if drone_id in self.selected_drones:
            self.selected_drones.remove(drone_id)
        else:
            self.selected_drones.add(drone_id)
        
        self._update_visual_selection()
        
        # Update list selection to match
        for i in range(self.drone_list.count()):
            item = self.drone_list.item(i)
            if int(item.text().split()[1]) == drone_id:
                item.setSelected(drone_id in self.selected_drones)

    def _on_list_item_clicked(self, item):
        """Handle single click on list item"""
        drone_id = int(item.text().split()[1])
        
        # Toggle selection
        if drone_id in self.selected_drones:
            self.selected_drones.remove(drone_id)
        else:
            self.selected_drones.add(drone_id)
        
        self._update_visual_selection()

    def _on_list_selection_changed(self):
        """Handle list selection change"""
        self.selected_drones.clear()
        for item in self.drone_list.selectedItems():
            drone_id = int(item.text().split()[1])
            self.selected_drones.add(drone_id)
        
        self._update_visual_selection()

    def _update_visual_selection(self):
        """Update visual appearance of selected drones"""
        if self.is_3d_mode:
            # Update 3D spheres
            for i, sphere in enumerate(self.spheres_3d):
                if sphere is not None:
                    if i in self.selected_drones:
                        sphere.setColor((1.0, 1.0, 0.0, 1.0))  # Yellow for selection
                    else:
                        sphere.setColor((0.4, 0.6, 0.9, 1.0))  # Default blue
        else:
            # Update 2D circles
            for i, scatter in enumerate(self.circles_2d):
                if scatter is not None:
                    if i in self.selected_drones:
                        scatter.setBrush(pg.mkBrush(255, 255, 0, 150))  # Yellow for selection
                        scatter.setPen(pg.mkPen('yellow', width=3))
                    else:
                        scatter.setBrush(pg.mkBrush(100, 150, 200, 150))  # Default blue
                        scatter.setPen(pg.mkPen('blue', width=2))

    def _show_event_menu_for_selected(self):
        """Show event menu for all selected drones"""
        if not self.selected_drones:
            return
            
        menu = QMenu(self)
        for evt in ("Crash", "Isolation", "Custom…"):
            action = menu.addAction(evt)
            action.triggered.connect(lambda _, e=evt: self._assign_event_to_selected(e))
        menu.exec(QCursor.pos())

    def _assign_event_to_selected(self, event_name: str):
        """Assign event to all selected drones"""
        color_map_3d = {
            "Crash":     (1.0, 0.0, 0.0, 1.0),  # red
            "Isolation": (1.0, 1.0, 0.0, 1.0),  # yellow
            "Custom…":   (0.5, 0.5, 0.5, 1.0),  # gray
        }
        
        color_map_2d = {
            "Crash":     ('red', (255, 0, 0, 150)),
            "Isolation": ('yellow', (255, 255, 0, 150)),
            "Custom…":   ('gray', (128, 128, 128, 150)),
        }
        
        for drone_id in self.selected_drones:
            if self.is_3d_mode:
                if drone_id < len(self.spheres_3d) and self.spheres_3d[drone_id] is not None:
                    event_color = color_map_3d.get(event_name, (0.4, 0.6, 0.9, 1.0))
                    self.spheres_3d[drone_id].setColor(event_color)
            else:
                if drone_id < len(self.circles_2d) and self.circles_2d[drone_id] is not None:
                    pen_color, brush_color = color_map_2d.get(event_name, ('blue', (100, 150, 200, 150)))
                    self.circles_2d[drone_id].setPen(pg.mkPen(pen_color, width=3))
                    self.circles_2d[drone_id].setBrush(pg.mkBrush(*brush_color))
            
            print(f"[Event] Drone {drone_id} → {event_name}")
            self.drone_event_selected.emit(drone_id, event_name)

    def showEvent(self, event):
        """Override showEvent to ensure drones are properly positioned when window is shown."""
        super().showEvent(event)
        # Force position update when window is shown
        self.update_positions()

    def update_positions(self):
        """Update drone positions based on slider values and current mode"""
        r_spread = self.r_slider.value() / 10.0
        xoff = self.xoff_slider.value() / 10.0
        yoff = self.yoff_slider.value() / 10.0
        
        # Z offset only applies in 3D mode
        if self.is_3d_mode:
            zoff = self.z_slider.value() / 10.0
        else:
            zoff = 0.0

        # Update labels
        self.r_label.setText(f"R spread: {r_spread:.1f}")
        self.xoff_label.setText(f"X offset: {xoff:.1f}")
        self.yoff_label.setText(f"Y offset: {yoff:.1f}")
        if self.is_3d_mode:
            self.z_label.setText(f"Z offset: {zoff:.1f}")

        # Always update 3D spheres
        positions_3d = self.sphere_positions
        for i, (base_x, base_y, base_z) in enumerate(positions_3d):
            if i < len(self.spheres_3d) and self.spheres_3d[i] is not None:
                x = base_x * r_spread + xoff
                y = base_y * r_spread + yoff
                z = base_z * r_spread + zoff
                
                sph = self.spheres_3d[i]
                sph.resetTransform()
                sph.translate(x, y, z)
                sph.setVisible(True)

        # Always update 2D circles with RADIAL effect
        positions_2d = self.circle_positions
        for i, (base_x, base_y) in enumerate(positions_2d):
            if i < len(self.circles_2d) and self.circles_2d[i] is not None:
                # RADIAL positioning: base positions are on unit circle, scale by r_spread
                x = base_x * r_spread + xoff
                y = base_y * r_spread + yoff
                
                # Debug info for first drone when slider changes
                if i == 0:
                    print(f"[2D Update] r_spread={r_spread:.2f}, base=({base_x:.2f}, {base_y:.2f}) -> final=({x:.2f}, {y:.2f})")
                
                # Update scatter position
                scatter = self.circles_2d[i]
                scatter.setData(x=[x], y=[y])

    def reset_drones(self):
        """Reset all drones to origin positions and default color."""
        # reset sliders to defaults
        self.r_slider.setValue(20)  # Updated to match new default
        self.xoff_slider.setValue(0)
        self.yoff_slider.setValue(0)
        self.z_slider.setValue(0)
        
        # clear selections
        self.drone_list.clearSelection()
        self.selected_drones.clear()
        
        # reset colors and ensure visibility for both 3D and 2D views
        # Reset 3D spheres
        default_color_3d = (0.4, 0.6, 0.9, 1.0)
        for sph in self.spheres_3d:
            if sph is not None:
                sph.setColor(default_color_3d)
                sph.setVisible(True)
        
        # Reset 2D circles
        for scatter in self.circles_2d:
            if scatter is not None:
                scatter.setPen(pg.mkPen('blue', width=2))
                scatter.setBrush(pg.mkBrush(100, 150, 200, 150))
        
        # reposition
        self.update_positions()
        
        mode_text = "3D Sphere" if self.is_3d_mode else "2D Disc"
        print(f"[Reset] All {NUM_DRONES} drones reset to {mode_text} formation and default color")

class Drone3DWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D/2D Drone Grid")
        self.setCentralWidget(Drone3DGrid(self))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Drone3DWindow()
    w.resize(1000, 600)
    w.show()
    sys.exit(app.exec())