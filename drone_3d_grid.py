# drone_3d_grid_redesign.py

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLabel, QMenu, QSlider, QPushButton, QCheckBox, 
    QStackedWidget, QFrame, QButtonGroup, QToolButton, QSpacerItem,
    QSizePolicy, QGroupBox, QGridLayout, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QCursor, QFont, QIcon, QPalette, QColor, QPainter, QBrush, QPen
import pyqtgraph.opengl as gl
import pyqtgraph as pg

# Configuration
NUM_DRONES = 12
COLORS = {
    'background': '#2b2b2b',
    'surface': '#3c3c3c',
    'primary': '#0d7377',
    'secondary': '#14a085',
    'accent': '#f39c12',
    'text': '#ffffff',
    'text_secondary': '#b0b0b0',
    'border': '#4a4a4a',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c'
}

class ModernButton(QPushButton):
    def __init__(self, text="", icon_text="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_text = icon_text
        self.setMinimumHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                color: {COLORS['text']};
                font-weight: 500;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['secondary']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_secondary']};
            }}
        """)

class ModernSlider(QSlider):
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 6px;
                background: {COLORS['surface']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                border: 1px solid {COLORS['secondary']};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['secondary']};
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['primary']};
                border-radius: 3px;
            }}
        """)

class ModernSwitch(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text']};
                font-weight: 500;
                spacing: 12px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 50px;
                height: 24px;
                border-radius: 12px;
                background-color: {COLORS['border']};
                border: 2px solid {COLORS['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['secondary']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['primary']};
            }}
        """)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get indicator rect
        indicator_rect = self.style().subElementRect(
            self.style().SubElement.SE_CheckBoxIndicator, 
            self.style().optionForButton(self), 
            self
        )
        
        # Draw the sliding circle
        circle_size = 18
        margin = 3
        
        if self.isChecked():
            # Right position for 3D
            circle_x = indicator_rect.x() + indicator_rect.width() - circle_size - margin
            circle_color = QColor(255, 255, 255)
        else:
            # Left position for 2D
            circle_x = indicator_rect.x() + margin
            circle_color = QColor(200, 200, 200)
        
        circle_y = indicator_rect.y() + margin
        
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawEllipse(circle_x, circle_y, circle_size, circle_size)
        
        # Draw mode text on the switch
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        if self.isChecked():
            # Show "3D" on left side
            text_rect = QRect(indicator_rect.x() + 5, indicator_rect.y(), 20, indicator_rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "3D")
        else:
            # Show "2D" on right side
            text_rect = QRect(indicator_rect.x() + indicator_rect.width() - 25, indicator_rect.y(), 20, indicator_rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "2D")

class CollapsibleSection(QWidget):
    def __init__(self, title="", collapsed=False, parent=None):
        super().__init__(parent)
        self.is_expanded = not collapsed
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self.header = ModernButton(title)
        self.header.clicked.connect(self.toggle_section)
        self._update_header_style()
        self.main_layout.addWidget(self.header)
        
        # Content frame
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-top: none;
                border-radius: 0 0 6px 6px;
            }}
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.addWidget(self.content_frame)
        
        # Animation
        self.animation = QPropertyAnimation(self.content_frame, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set initial state
        if collapsed:
            self.content_frame.setMaximumHeight(0)
            self.content_frame.setVisible(False)
    
    def _update_header_style(self):
        arrow = "▼" if self.is_expanded else "▶"
        self.header.setText(f"{arrow} {self.header.text().replace('▼ ', '').replace('▶ ', '')}")
    
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
    
    def toggle_section(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def collapse(self):
        self.is_expanded = False
        self._update_header_style()
        
        # Get current height before starting animation
        current_height = self.content_frame.height()
        
        self.animation.setStartValue(current_height)
        self.animation.setEndValue(0)
        self.animation.finished.connect(lambda: self.content_frame.setVisible(False))
        self.animation.start()
    
    def expand(self):
        self.is_expanded = True
        self._update_header_style()
        
        # Make visible and get the natural height
        self.content_frame.setVisible(True)
        self.content_frame.setMaximumHeight(16777215)
        natural_height = self.content_frame.sizeHint().height()
        
        self.animation.setStartValue(0)
        self.animation.setEndValue(natural_height)
        self.animation.finished.disconnect()  # Remove previous connections
        self.animation.start()

class DroneListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                color: {COLORS['text']};
                selection-background-color: {COLORS['primary']};
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['border']};
            }}
        """)

class StatusIndicator(QWidget):
    def __init__(self, text="", status="inactive", parent=None):
        super().__init__(parent)
        self.text = text
        self.status = status
        self.setFixedSize(120, 24)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Status colors
        status_colors = {
            'active': COLORS['success'],
            'warning': COLORS['warning'],
            'error': COLORS['danger'],
            'inactive': COLORS['border']
        }
        
        # Draw indicator circle
        painter.setBrush(QBrush(QColor(status_colors[self.status])))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 6, 12, 12)
        
        # Draw text
        painter.setPen(QColor(COLORS['text']))
        painter.drawText(20, 16, self.text)

class ZoomableGLViewWidget(gl.GLViewWidget):
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.zoom_factor = 1.2
        self.min_distance = 5
        self.max_distance = 100
        self.hovered_drone_id = None
        self.spheres = []  # Will be populated by parent
        
        # Modern styling
        self.setStyleSheet(f"""
            QOpenGLWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['background']};
            }}
        """)
        
        # Enable mouse tracking for hover detection
        self.setMouseTracking(True)
        
    def set_spheres(self, spheres):
        """Set reference to sphere objects for picking"""
        self.spheres = spheres
        
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover detection"""
        if self.parent_widget and self.spheres:
            # Get mouse position in widget coordinates
            mouse_pos = event.pos()
            
            # Find the closest sphere to mouse cursor
            closest_drone_id = self._pick_drone_at_position(mouse_pos)
            
            # Update hover state
            if closest_drone_id != self.hovered_drone_id:
                # Remove hover from previous drone
                if self.hovered_drone_id is not None:
                    self.spheres[self.hovered_drone_id].set_hover_state(False)
                
                # Add hover to new drone
                self.hovered_drone_id = closest_drone_id
                if self.hovered_drone_id is not None:
                    self.spheres[self.hovered_drone_id].set_hover_state(True)
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks for selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.hovered_drone_id is not None and self.parent_widget:
                # Confirm selection of hovered drone
                self.parent_widget._on_drone_clicked(self.hovered_drone_id)
                return
        
        super().mousePressEvent(event)
    
    def _pick_drone_at_position(self, mouse_pos):
        """Ray casting picking for accurate drone selection"""
        if not self.spheres:
            return None
            
        # Get viewport dimensions
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return None
        
        # Convert mouse position to normalized device coordinates (-1 to 1)
        x_ndc = (2.0 * mouse_pos.x()) / w - 1.0
        y_ndc = 1.0 - (2.0 * mouse_pos.y()) / h  # Flip Y axis
        
        # Get camera parameters
        try:
            center = np.array(self.opts['center'])
            distance = self.opts['distance']
            elevation = np.radians(self.opts['elevation'])
            azimuth = np.radians(self.opts['azimuth'])
            fov = np.radians(self.opts.get('fov', 60))
            
            # Calculate camera position
            cam_x = center[0] + distance * np.cos(elevation) * np.sin(azimuth)
            cam_y = center[1] + distance * np.cos(elevation) * np.cos(azimuth)
            cam_z = center[2] + distance * np.sin(elevation)
            cam_pos = np.array([cam_x, cam_y, cam_z])
            
            # Calculate view direction (from camera to center)
            view_dir = center - cam_pos
            view_dir = view_dir / np.linalg.norm(view_dir)
            
            # Calculate right and up vectors
            world_up = np.array([0, 0, 1])
            right = np.cross(view_dir, world_up)
            right = right / np.linalg.norm(right)
            up = np.cross(right, view_dir)
            up = up / np.linalg.norm(up)
            
            # Calculate the ray direction
            aspect_ratio = w / h
            tan_half_fov = np.tan(fov / 2.0)
            
            # Ray direction in world space
            ray_dir = view_dir + (x_ndc * tan_half_fov * aspect_ratio * right) + (y_ndc * tan_half_fov * up)
            ray_dir = ray_dir / np.linalg.norm(ray_dir)
            
            # Find closest sphere using ray-sphere intersection
            closest_drone_id = None
            min_distance = float('inf')
            sphere_radius = 0.3  # Sphere radius
            
            for i, sphere in enumerate(self.spheres):
                # Get sphere world position
                transform = sphere.transform()
                sphere_center = transform.map(np.array([0, 0, 0]))
                
                # Ray-sphere intersection
                oc = cam_pos - sphere_center
                a = np.dot(ray_dir, ray_dir)
                b = 2.0 * np.dot(oc, ray_dir)
                c = np.dot(oc, oc) - sphere_radius * sphere_radius
                
                discriminant = b * b - 4 * a * c
                
                if discriminant >= 0:
                    # Intersection found, calculate distance
                    t1 = (-b - np.sqrt(discriminant)) / (2.0 * a)
                    t2 = (-b + np.sqrt(discriminant)) / (2.0 * a)
                    
                    # Use the closest positive intersection
                    t = t1 if t1 > 0 else t2
                    if t > 0 and t < min_distance:
                        min_distance = t
                        closest_drone_id = i
            
            return closest_drone_id
            
        except Exception as e:
            # Fallback to simpler method if ray casting fails
            return self._pick_drone_simple_fallback(mouse_pos)
    
    def _pick_drone_simple_fallback(self, mouse_pos):
        """Fallback picking method using screen distance"""
        if not self.spheres:
            return None
            
        closest_drone_id = None
        min_screen_distance = float('inf')
        pickup_threshold = 80  # Increased threshold for easier picking
        
        # Get viewport center
        center_x, center_y = self.width() / 2, self.height() / 2
        
        try:
            for i, sphere in enumerate(self.spheres):
                # Get sphere position relative to view center
                transform = sphere.transform()
                sphere_pos = transform.map(np.array([0, 0, 0]))
                
                # Simple projection: map 3D distance to screen distance
                # This is very approximate but more reliable
                view_center = np.array(self.opts['center'])
                distance_from_center = np.linalg.norm(sphere_pos - view_center)
                
                # Calculate approximate screen position
                # This is a heuristic based on the sphere's offset from view center
                offset = sphere_pos - view_center
                scale_factor = 50 / max(self.opts['distance'], 1)  # Adjust scale based on zoom
                
                screen_x = center_x + offset[0] * scale_factor
                screen_y = center_y - offset[1] * scale_factor  # Flip Y
                
                # Calculate distance to mouse
                dx = screen_x - mouse_pos.x()
                dy = screen_y - mouse_pos.y()
                screen_distance = np.sqrt(dx*dx + dy*dy)
                
                if screen_distance < pickup_threshold and screen_distance < min_screen_distance:
                    min_screen_distance = screen_distance
                    closest_drone_id = i
                    
        except Exception:
            pass
        
        return closest_drone_id
    
    def leaveEvent(self, event):
        """Clear hover when mouse leaves the widget"""
        if self.hovered_drone_id is not None and self.spheres:
            self.spheres[self.hovered_drone_id].set_hover_state(False)
            self.hovered_drone_id = None
        super().leaveEvent(event)
        
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()
    
    def zoom_in(self):
        current_distance = self.opts['distance']
        new_distance = max(self.min_distance, current_distance / self.zoom_factor)
        self.opts['distance'] = new_distance
        self.update()
        if self.parent_widget:
            self.parent_widget._sync_zoom_slider(new_distance)
            self.parent_widget._update_zoom_info()
    
    def zoom_out(self):
        current_distance = self.opts['distance']
        new_distance = min(self.max_distance, current_distance * self.zoom_factor)
        self.opts['distance'] = new_distance
        self.update()
        if self.parent_widget:
            self.parent_widget._sync_zoom_slider(new_distance)
            self.parent_widget._update_zoom_info()
    
    def reset_zoom(self):
        self.opts['distance'] = 20
        self.update()
        if self.parent_widget:
            self.parent_widget._sync_zoom_slider(20)
            self.parent_widget._update_zoom_info()

class ClickableMeshItem(gl.GLMeshItem):
    def __init__(self, drone_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drone_id = drone_id
        self.parent_widget = None
        self.is_hovered = False
        self.is_selected = False
        self.default_color = (0.2, 0.6, 0.9, 0.8)
        self.hover_color = (0.9, 0.9, 0.4, 1.0)  # Yellow hover
        self.selected_color = (1.0, 0.8, 0.0, 1.0)  # Gold selected
        
    def set_hover_state(self, hovered):
        if self.is_hovered != hovered:
            self.is_hovered = hovered
            self._update_visual_state()
    
    def set_selected_state(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_visual_state()
    
    def _update_visual_state(self):
        if self.is_selected:
            self.setColor(self.selected_color)
        elif self.is_hovered:
            self.setColor(self.hover_color)
        else:
            self.setColor(self.default_color)
    
    def reset_to_default(self):
        self.is_hovered = False
        self.is_selected = False
        self.setColor(self.default_color)

class ClickableScatterItem(pg.ScatterPlotItem):
    def __init__(self, drone_id, parent_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drone_id = drone_id
        self.parent_widget = parent_widget
        
    def mouseClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_widget._on_drone_clicked(self.drone_id)
        super().mouseClickEvent(event)

class ModernDroneConsole(QWidget):
    drone_event_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }}
        """)
        
        self.is_3d_mode = True
        self.selected_drones = set()
        
        self._define_sphere_positions()
        self._define_circle_positions()
        self._setup_ui()
        self._create_drones()
        self._setup_initial_state()

    def _setup_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Left side - Viewport
        viewport_frame = QFrame()
        viewport_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        viewport_layout = QVBoxLayout(viewport_frame)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        
        # Viewport header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        self.title_label = QLabel("Drone Formation")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['text']};
            }}
        """)
        
        self.mode_toggle = ModernSwitch("View Mode")
        self.mode_toggle.setChecked(True)
        self.mode_toggle.stateChanged.connect(self._toggle_mode)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.mode_toggle)
        
        viewport_layout.addLayout(header_layout)
        
        # Views stack
        self.view_stack = QStackedWidget()
        
        # 3D View
        self.view_3d = ZoomableGLViewWidget(parent_widget=self)
        self.view_3d.opts['distance'] = 20
        grid = gl.GLGridItem()
        grid.scale(1, 1, 1)
        axes = gl.GLAxisItem()
        axes.setSize(x=5, y=5, z=5)
        self.view_3d.addItem(grid)
        self.view_3d.addItem(axes)
        
        # 2D View
        self.view_2d = pg.PlotWidget()
        self.view_2d.setAspectLocked(True)
        self.view_2d.setLabel('left', 'Y', color='white')
        self.view_2d.setLabel('bottom', 'X', color='white')
        self.view_2d.showGrid(x=True, y=True, alpha=0.3)
        self.view_2d.setXRange(-6, 6)
        self.view_2d.setYRange(-6, 6)
        self.view_2d.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border: none;
            }}
        """)
        
        self.view_stack.addWidget(self.view_3d)
        self.view_stack.addWidget(self.view_2d)
        viewport_layout.addWidget(self.view_stack)
        
        main_layout.addWidget(viewport_frame, 3)
        
        # Right side - Control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, 1)

    def _create_control_panel(self):
        panel = QFrame()
        panel.setMaximumWidth(320)
        panel.setMinimumWidth(280)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Status section
        status_section = self._create_status_section()
        layout.addWidget(status_section)
        
        # Formation controls
        formation_section = self._create_formation_section()
        layout.addWidget(formation_section)
        
        # Selection controls
        selection_section = self._create_selection_section()
        layout.addWidget(selection_section)
        
        # Action buttons
        action_section = self._create_action_section()
        layout.addWidget(action_section)
        
        layout.addStretch()
        
        return panel

    def _create_status_section(self):
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel("Status")
        title.setStyleSheet(f"font-weight: 600; color: {COLORS['text']}; font-size: 14px;")
        layout.addWidget(title)
        
        self.selection_status = StatusIndicator("No selection", "inactive")
        self.zoom_status = StatusIndicator("Distance: 20.0", "active")
        
        layout.addWidget(self.selection_status)
        layout.addWidget(self.zoom_status)
        
        return section


    def _create_formation_section(self):
        section = CollapsibleSection("Settings", collapsed=True)
        
        # Zoom control (placed first for better UX)
        self.zoom_slider, self.zoom_label = self._create_zoom_slider()
        section.add_widget(self._create_slider_widget("Zoom", self.zoom_slider, self.zoom_label))
        
        # Spread control
        self.r_slider, self.r_label = self._create_slider("Spread", 0, 50, 20)
        section.add_widget(self._create_slider_widget("Spread", self.r_slider, self.r_label))
        
        # Offset controls
        self.xoff_slider, self.xoff_label = self._create_slider("X Offset", -50, 50, 0)
        self.yoff_slider, self.yoff_label = self._create_slider("Y Offset", -50, 50, 0)
        self.z_slider, self.z_label = self._create_slider("Z Offset", -50, 50, 0)
        
        section.add_widget(self._create_slider_widget("X Offset", self.xoff_slider, self.xoff_label))
        section.add_widget(self._create_slider_widget("Y Offset", self.yoff_slider, self.yoff_label))
        
        # Store reference to Z offset widget for show/hide
        self.z_offset_widget = self._create_slider_widget("Z Offset", self.z_slider, self.z_label)
        section.add_widget(self.z_offset_widget)
        
        return section

    def _create_selection_section(self):
        section = CollapsibleSection("Drone Selection", collapsed=True)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        self.select_all_btn = ModernButton("All")
        self.clear_btn = ModernButton("Clear")
        self.select_all_btn.clicked.connect(self._select_all)
        self.clear_btn.clicked.connect(self._clear_selection)
        actions_layout.addWidget(self.select_all_btn)
        actions_layout.addWidget(self.clear_btn)
        section.add_widget(self._create_widget_from_layout(actions_layout))
        
        # Drone list
        self.drone_list = DroneListWidget()
        self.drone_list.setMaximumHeight(120)
        self.drone_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for i in range(NUM_DRONES):
            item = QListWidgetItem(f"Drone {i:02d}")
            self.drone_list.addItem(item)
        self.drone_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        section.add_widget(self.drone_list)
        
        return section

    def _create_action_section(self):
        section = QFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Event assignment
        self.assign_event_btn = ModernButton("Assign Event")
        self.assign_event_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 12px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_secondary']};
            }}
        """)
        self.assign_event_btn.clicked.connect(self._show_event_menu_for_selected)
        self.assign_event_btn.setEnabled(False)
        layout.addWidget(self.assign_event_btn)
        
        # Reset button
        self.reset_btn = ModernButton("Reset Formation")
        self.reset_btn.clicked.connect(self.reset_drones)
        layout.addWidget(self.reset_btn)
        
        return section

    def _create_slider(self, text, mn, mx, val):
        slider = ModernSlider()
        slider.setRange(mn, mx)
        slider.setValue(val)
        slider.valueChanged.connect(self.update_positions)
        
        label = QLabel(f"{val/10:.1f}")
        label.setMinimumWidth(40)
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        return slider, label
    
    def _create_zoom_slider(self):
        slider = ModernSlider()
        slider.setRange(5, 100)  # Distance range from 5 to 100
        slider.setValue(20)  # Default distance
        slider.valueChanged.connect(self._on_zoom_slider_changed)
        
        label = QLabel("20.0")
        label.setMinimumWidth(40)
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        return slider, label
    
    def _on_zoom_slider_changed(self, value):
        """Handle zoom slider changes"""
        if self.is_3d_mode:
            self.view_3d.opts['distance'] = value
            self.view_3d.update()
        else:
            # For 2D, adjust the view range
            range_size = value / 2.0
            self.view_2d.setXRange(-range_size, range_size)
            self.view_2d.setYRange(-range_size, range_size)
        
        self.zoom_label.setText(f"{value:.1f}")
        self._update_zoom_info()

    def _create_slider_widget(self, text, slider, label):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        text_label = QLabel(text)
        text_label.setMinimumWidth(60)
        layout.addWidget(text_label)
        layout.addWidget(slider)
        layout.addWidget(label)
        
        return widget

    def _create_widget_from_layout(self, layout):
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def _create_drones(self):
        # Create 3D spheres
        md = gl.MeshData.sphere(rows=10, cols=20, radius=0.3)
        self.spheres_3d = []
        
        for i in range(NUM_DRONES):
            sph = ClickableMeshItem(
                drone_id=i,
                meshdata=md,
                smooth=True,
                shader='shaded',
                color=(0.2, 0.6, 0.9, 0.8)
            )
            sph.parent_widget = self
            self.view_3d.addItem(sph)
            self.spheres_3d.append(sph)

        # Set spheres reference in the 3D view for picking
        self.view_3d.set_spheres(self.spheres_3d)

        # Create 2D circles
        self.circles_2d = []
        for i in range(NUM_DRONES):
            scatter = ClickableScatterItem(
                drone_id=i,
                parent_widget=self,
                x=[0], y=[0],
                size=25,
                brush=pg.mkBrush(51, 153, 230, 200),
                pen=pg.mkPen('white', width=2),
                symbol='o'
            )
            self.view_2d.addItem(scatter)
            self.circles_2d.append(scatter)

        self._position_2d_circles_initially()

    def _setup_initial_state(self):
        self._update_ui_for_mode()
        self.update_positions()
        self._update_selection_info()
        self._update_zoom_info()

    def _define_sphere_positions(self):
        if NUM_DRONES == 12:
            phi = (1 + np.sqrt(5)) / 2
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
        angles = np.linspace(0, 2*np.pi, NUM_DRONES, endpoint=False)
        self.circle_positions = []
        for angle in angles:
            x = np.cos(angle)
            y = np.sin(angle)
            self.circle_positions.append((x, y))

    def _position_2d_circles_initially(self):
        r_spread = 2.0
        for i, (base_x, base_y) in enumerate(self.circle_positions):
            if i < len(self.circles_2d):
                x = base_x * r_spread
                y = base_y * r_spread
                self.circles_2d[i].setData(x=[x], y=[y])

    def _toggle_mode(self, checked):
        self.is_3d_mode = checked
        self._update_ui_for_mode()
        self.update_positions()
        self._update_visual_selection()
        
        # Sync zoom slider with current view
        if self.is_3d_mode:
            distance = self.view_3d.opts['distance']
            self._sync_zoom_slider(distance)
        else:
            # Set a default range for 2D and sync slider
            current_range = 10  # Default 2D range
            self._sync_zoom_slider(current_range)
            self._on_zoom_slider_changed(current_range)
        
        self._update_zoom_info()

    def _update_ui_for_mode(self):
        if self.is_3d_mode:
            self.view_stack.setCurrentWidget(self.view_3d)
            self.z_slider.setVisible(True)
            self.z_label.setVisible(True)
        else:
            self.view_stack.setCurrentWidget(self.view_2d)
            self.z_slider.setVisible(False)
            self.z_label.setVisible(False)

    def _on_drone_clicked(self, drone_id):
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.selected_drones.add(drone_id)
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            self.selected_drones.discard(drone_id)
        else:
            if drone_id in self.selected_drones:
                self.selected_drones.remove(drone_id)
            else:
                self.selected_drones.add(drone_id)
        
        self._update_visual_selection()
        self._update_list_selection()
        self._update_selection_info()

    def _update_visual_selection(self):
        # Update 3D spheres using new state management
        for i, sphere in enumerate(self.spheres_3d):
            sphere.set_selected_state(i in self.selected_drones)
        
        # Update 2D circles
        for i, scatter in enumerate(self.circles_2d):
            if i in self.selected_drones:
                scatter.setBrush(pg.mkBrush(255, 204, 0, 200))  # Gold
                scatter.setPen(pg.mkPen('orange', width=3))
                scatter.setSize(30)
            else:
                scatter.setBrush(pg.mkBrush(51, 153, 230, 200))  # Blue
                scatter.setPen(pg.mkPen('white', width=2))
                scatter.setSize(25)

    def _update_list_selection(self):
        self.drone_list.blockSignals(True)
        self.drone_list.clearSelection()
        
        for i in range(self.drone_list.count()):
            item = self.drone_list.item(i)
            if i in self.selected_drones:
                item.setSelected(True)
        
        self.drone_list.blockSignals(False)

    def _on_list_selection_changed(self):
        selected_items = self.drone_list.selectedItems()
        new_selection = set()
        
        for item in selected_items:
            drone_id = int(item.text().split()[1])
            new_selection.add(drone_id)
        
        self.selected_drones = new_selection
        self._update_visual_selection()
        self._update_selection_info()

    def _update_selection_info(self):
        count = len(self.selected_drones)
        if count == 0:
            self.selection_status.text = "No selection"
            self.selection_status.status = "inactive"
            self.assign_event_btn.setEnabled(False)
        elif count == 1:
            drone_id = list(self.selected_drones)[0]
            self.selection_status.text = f"Drone {drone_id:02d}"
            self.selection_status.status = "active"
            self.assign_event_btn.setEnabled(True)
        else:
            self.selection_status.text = f"{count} drones"
            self.selection_status.status = "active"
            self.assign_event_btn.setEnabled(True)
        
        self.selection_status.update()

    def _sync_zoom_slider(self, distance):
        """Synchronize zoom slider with current distance"""
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(distance))
        self.zoom_label.setText(f"{distance:.1f}")
        self.zoom_slider.blockSignals(False)

    def _update_zoom_info(self):
        if self.is_3d_mode:
            distance = self.view_3d.opts['distance']
            self.zoom_status.text = f"Distance: {distance:.1f}"
        else:
            view_range = self.view_2d.getViewBox().viewRange()
            x_range = view_range[0][1] - view_range[0][0]
            self.zoom_status.text = f"Range: {x_range:.1f}"
        
        self.zoom_status.update()

    def _clear_selection(self):
        self.selected_drones.clear()
        self._update_visual_selection()
        self._update_list_selection()
        self._update_selection_info()

    def _select_all(self):
        self.selected_drones = set(range(NUM_DRONES))
        self._update_visual_selection()
        self._update_list_selection()
        self._update_selection_info()

    def _show_event_menu_for_selected(self):
        if not self.selected_drones:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                color: {COLORS['text']};
            }}
            QMenu::item {{
                padding: 8px 16px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        events = [
            ("🔥 Crash", "Crash"),
            ("⚠️ Isolation", "Isolation"),
            ("🎯 Target", "Target"),
            ("⚙️ Custom", "Custom")
        ]
        
        for icon_text, event_name in events:
            action = menu.addAction(f"{icon_text} ({len(self.selected_drones)} drones)")
            action.triggered.connect(lambda _, e=event_name: self._assign_event_to_selected(e))
        
        menu.exec(QCursor.pos())

    def _assign_event_to_selected(self, event_name: str):
        color_map_3d = {
            "Crash": (0.9, 0.2, 0.2, 1.0),      # Red
            "Isolation": (1.0, 0.6, 0.0, 1.0),  # Orange
            "Target": (0.2, 0.8, 0.2, 1.0),     # Green
            "Custom": (0.6, 0.4, 0.8, 1.0),     # Purple
        }
        
        color_map_2d = {
            "Crash": (230, 51, 51, 200),
            "Isolation": (255, 153, 0, 200),
            "Target": (51, 204, 51, 200),
            "Custom": (153, 102, 204, 200),
        }
        
        for drone_id in self.selected_drones:
            if drone_id < len(self.spheres_3d):
                # Update sphere event color and override selection color
                color_3d = color_map_3d.get(event_name, (0.2, 0.6, 0.9, 0.8))
                sphere = self.spheres_3d[drone_id]
                sphere.default_color = color_3d
                sphere.selected_color = color_3d  # Keep event color when selected
                sphere.setColor(color_3d)
            
            if drone_id < len(self.circles_2d):
                color_2d = color_map_2d.get(event_name, (51, 153, 230, 200))
                self.circles_2d[drone_id].setBrush(pg.mkBrush(*color_2d))
            
            self.drone_event_selected.emit(drone_id, event_name)

    def update_positions(self):
        r_spread = self.r_slider.value() / 10.0
        xoff = self.xoff_slider.value() / 10.0
        yoff = self.yoff_slider.value() / 10.0
        zoff = self.z_slider.value() / 10.0 if self.is_3d_mode else 0.0

        # Update labels
        self.r_label.setText(f"{r_spread:.1f}")
        self.xoff_label.setText(f"{xoff:.1f}")
        self.yoff_label.setText(f"{yoff:.1f}")
        if self.is_3d_mode:
            self.z_label.setText(f"{zoff:.1f}")

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
        # Reset sliders
        self.r_slider.setValue(20)
        self.xoff_slider.setValue(0)
        self.yoff_slider.setValue(0)
        self.z_slider.setValue(0)
        self.zoom_slider.setValue(20)  # Reset zoom
        
        # Reset view zoom
        if self.is_3d_mode:
            self.view_3d.opts['distance'] = 20
            self.view_3d.update()
        else:
            self.view_2d.setXRange(-6, 6)
            self.view_2d.setYRange(-6, 6)
        
        # Clear selections
        self._clear_selection()
        
        # Reset colors using new state management
        for sphere in self.spheres_3d:
            sphere.reset_to_default()
        
        for scatter in self.circles_2d:
            scatter.setBrush(pg.mkBrush(51, 153, 230, 200))
            scatter.setPen(pg.mkPen('white', width=2))
            scatter.setSize(25)
        
        self.update_positions()
        self._update_zoom_info()

class ModernDroneWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Formation Console")
        self.setMinimumSize(1000, 700)
        
        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
            }}
        """)
        
        self.console = ModernDroneConsole(self)
        self.setCentralWidget(self.console)
        
        # Expose the drone_event_selected signal for compatibility
        self.drone_event_selected = self.console.drone_event_selected

# Alias for backward compatibility with existing code
Drone3DWindow = ModernDroneWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Apply dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = ModernDroneWindow()
    window.show()
    
    sys.exit(app.exec())