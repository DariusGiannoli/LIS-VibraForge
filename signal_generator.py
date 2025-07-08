from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class OscillatorDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()

        self.resize(300, 100)


        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0, 400)  # Adjust range as needed
        self.frequency_input.setValue(5)  # Default value
        form_layout.addRow("Frequency (0-400Hz):", self.frequency_input)
        
        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(0, 1)  # Adjust range as needed
        self.amplitude_input.setValue(1)  # Default value
        form_layout.addRow("Amplitude (0-1):", self.amplitude_input)

        # Configure the duration input
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 60)  # Set a reasonable upper limit for duration
        self.duration_input.setValue(1)  # Default value
        self.duration_input.setSingleStep(1)  # Increment in 1s steps
        form_layout.addRow("Duration (s):", self.duration_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        return {
            "duration": self.duration_input.value(),
            "frequency": self.frequency_input.value(),
            "amplitude": self.amplitude_input.value()
        }

class ChirpDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()

        # Signal Type (Radio Buttons with Circular Layout)
        signal_layout = QHBoxLayout()

        # Create the radio buttons
        self.sine_radio = QRadioButton("Sine")
        self.square_radio = QRadioButton("Square")
        self.saw_radio = QRadioButton("Saw")
        self.triangle_radio = QRadioButton("Triangle")

        # Button group to manage radio buttons (ensures mutual exclusivity)
        self.signal_group = QButtonGroup(self)
        self.signal_group.addButton(self.sine_radio)
        self.signal_group.addButton(self.square_radio)
        self.signal_group.addButton(self.saw_radio)
        self.signal_group.addButton(self.triangle_radio)

        self.sine_radio.setChecked(True)

        # Set the default checked radio button based on signal_type
        if signal_type == "Sine":
            self.sine_radio.setChecked(True)
        elif signal_type == "Square":
            self.square_radio.setChecked(True)
        elif signal_type == "Saw":
            self.saw_radio.setChecked(True)
        elif signal_type == "Triangle":
            self.triangle_radio.setChecked(True)

        # Add radio buttons to the layout
        signal_layout.addWidget(self.sine_radio)
        signal_layout.addWidget(self.square_radio)
        signal_layout.addWidget(self.saw_radio)
        signal_layout.addWidget(self.triangle_radio)

        # Add the signal layout to the form layout
        form_layout.addRow("Signal Type:", signal_layout)

        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0, 400)  # Adjust range as needed
        self.frequency_input.setValue(10)  # Default value
        form_layout.addRow("Frequency (0-400Hz):", self.frequency_input)

        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(0, 1)  # Adjust range as needed
        self.amplitude_input.setValue(1)  # Default value
        form_layout.addRow("Amplitude (0-1):", self.amplitude_input)
        
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 400)  # Adjust range as needed
        self.rate_input.setValue(10)  # Default value
        form_layout.addRow("Rate (Hz/s):", self.rate_input)

        # Configure the duration input
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 60)  # Set a reasonable upper limit for duration
        self.duration_input.setValue(1)  # Default value
        self.duration_input.setSingleStep(1)  # Increment in 1s steps
        form_layout.addRow("Duration (s):", self.duration_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        if self.sine_radio.isChecked():
            selected_signal = "Sine"
        elif self.square_radio.isChecked():
            selected_signal = "Square"
        elif self.saw_radio.isChecked():
            selected_signal = "Saw"
        elif self.triangle_radio.isChecked():
            selected_signal = "Triangle"
        return {
            "duration": self.duration_input.value(),
            "chirp_type": selected_signal,
            "frequency": self.frequency_input.value(),
            "amplitude": self.amplitude_input.value(),
            "rate": self.rate_input.value()
        }

class NoiseDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()

        self.resize(300, 100)

        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(0, 1)  # Adjust range as needed
        self.amplitude_input.setDecimals(1)  # Allow up to two decimal places
        self.amplitude_input.setSingleStep(0.1)  # Increment in 0.1s steps
        self.amplitude_input.setValue(1)  # Default value
        form_layout.addRow("Amplitude (0-1):", self.amplitude_input)

        # Configure the duration input
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 60)  # Set a reasonable upper limit for duration
        self.duration_input.setValue(1)  # Default value
        self.duration_input.setSingleStep(1)  # Increment in 1s steps
        form_layout.addRow("Duration (s):", self.duration_input)
        
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        return {
            "duration": self.duration_input.value(),
            "amplitude": self.amplitude_input.value(),
        }

class FMDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()

        # Signal Type (Radio Buttons with Circular Layout)
        signal_layout = QHBoxLayout()

        # Create the radio buttons
        self.sine_radio = QRadioButton("Sine")
        self.square_radio = QRadioButton("Square")
        self.saw_radio = QRadioButton("Saw")
        self.triangle_radio = QRadioButton("Triangle")

        # Button group to manage radio buttons (ensures mutual exclusivity)
        self.signal_group = QButtonGroup(self)
        self.signal_group.addButton(self.sine_radio)
        self.signal_group.addButton(self.square_radio)
        self.signal_group.addButton(self.saw_radio)
        self.signal_group.addButton(self.triangle_radio)

        self.sine_radio.setChecked(True)

        # Set the default checked radio button based on signal_type
        if signal_type == "Sine":
            self.sine_radio.setChecked(True)
        elif signal_type == "Square":
            self.square_radio.setChecked(True)
        elif signal_type == "Saw":
            self.saw_radio.setChecked(True)
        elif signal_type == "Triangle":
            self.triangle_radio.setChecked(True)

        # Add radio buttons to the layout
        signal_layout.addWidget(self.sine_radio)
        signal_layout.addWidget(self.square_radio)
        signal_layout.addWidget(self.saw_radio)
        signal_layout.addWidget(self.triangle_radio)

        # Add the signal layout to the form layout
        form_layout.addRow("Signal Type:", signal_layout)

        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0, 400)  # Adjust range as needed
        self.frequency_input.setValue(10)  # Default value
        form_layout.addRow("Frequency (0-400Hz):", self.frequency_input)

        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(0, 1)  # Adjust range as needed
        self.amplitude_input.setDecimals(1)  # Allow up to two decimal places
        self.amplitude_input.setSingleStep(0.1)  # Increment in 0.1s steps
        self.amplitude_input.setValue(1)  # Default value
        form_layout.addRow("Amplitude (0-1):", self.amplitude_input)
        
        self.modulation_input = QDoubleSpinBox()
        self.modulation_input.setRange(0, 400)  # Adjust range as needed
        self.modulation_input.setValue(10)  # Default value
        form_layout.addRow("Modulation Frequency (0-400Hz):", self.modulation_input)

        self.index_input = QDoubleSpinBox()
        self.index_input.setRange(0, 10)  # Adjust range as needed
        self.index_input.setValue(2)  # Default value
        form_layout.addRow("Index (0-10):", self.index_input)

        # Configure the duration input
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 60)  # Set a reasonable upper limit for duration
        self.duration_input.setValue(1)  # Default value
        self.duration_input.setSingleStep(1)  # Increment in 1s steps
        form_layout.addRow("Duration (s):", self.duration_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        if self.sine_radio.isChecked():
            selected_signal = "Sine"
        elif self.square_radio.isChecked():
            selected_signal = "Square"
        elif self.saw_radio.isChecked():
            selected_signal = "Saw"
        elif self.triangle_radio.isChecked():
            selected_signal = "Triangle"
        return {
            "duration": self.duration_input.value(),
            "FM_type": selected_signal,
            "frequency": self.frequency_input.value(),
            "amplitude": self.amplitude_input.value(),
            "modulation": self.modulation_input.value(),
            "index": self.index_input.value()
        }

class PWMDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()

        self.resize(300, 100)

        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0, 400)  # Adjust range as needed
        self.frequency_input.setValue(10)  # Default value
        form_layout.addRow("Frequency (0-400Hz):", self.frequency_input)

        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(0, 1)  # Adjust range as needed
        self.amplitude_input.setDecimals(1)  # Allow up to two decimal places
        self.amplitude_input.setSingleStep(0.1)  # Increment in 0.1s steps
        self.amplitude_input.setValue(1)  # Default value
        form_layout.addRow("Amplitude (0-1):", self.amplitude_input)

        self.duty_cycle_input = QDoubleSpinBox()
        self.duty_cycle_input.setRange(0, 100)  # Adjust range as needed
        self.duty_cycle_input.setValue(50)  # Default value
        form_layout.addRow("Duty Cycle (%):", self.duty_cycle_input)

        # Configure the duration input
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 60)  # Set a reasonable upper limit for duration
        self.duration_input.setValue(1)  # Default value

        self.duration_input.setSingleStep(1)  # Increment in 1s steps
        form_layout.addRow("Duration (s):", self.duration_input)
        
        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        return {
            "duration": self.duration_input.value(),
            "frequency": self.frequency_input.value(),
            "amplitude": self.amplitude_input.value(),
            "duty_cycle": self.duty_cycle_input.value()
        }
