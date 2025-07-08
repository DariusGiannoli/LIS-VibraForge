'''
This file contains the utility functions and constants used in the main application.
'''

from PyQt6.QtGui import *
import random
import platform

TIME_STAMP = 44100

OS_DEPENDENT_VALUE = 3 if platform.system() == "Darwin" else 2 

# Define the ACTUATOR_CONFIG dictionary
ACTUATOR_CONFIG = {
    "LRA": {
        "text_vertical_offset": -0.5,
        "text_horizontal_offset": 0.5,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    },
    "VCA": {
        "text_vertical_offset": -1,
        "text_horizontal_offset": 0.25,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    },
    "M  ": {
        "text_vertical_offset": -0.8,
        "text_horizontal_offset": 0.25,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    }
}

# Predefined color list for actuators (20 colors)
COLOR_LIST = [
    QColor(158, 175, 163),  # Dark Sea Green
    QColor(194, 166, 159),  # Pale Taupe
    QColor(194, 178, 128),  # Khaki
    QColor(145, 141, 18),  # Khaki
    QColor(150, 143, 132),  # Dark Gray
    QColor(175, 167, 191),  # Thistle
    QColor(144, 175, 197),  # Cadet Blue
    QColor(151, 102, 102),  
    QColor(227, 140, 122),
    QColor(103, 98, 172),
    QColor(33, 104, 80),
    QColor(183, 87, 116),
    QColor(119, 80, 29),
    QColor(172, 94, 169),
    QColor(81, 146, 58),
    QColor(21, 45, 138),
    QColor(206, 21, 39),
    QColor(199, 90, 18),
    QColor(100, 199, 187),
    QColor(209, 139, 0),
]

# Function to generate a contrasting color
def generate_contrasting_color(existing_colors):
    while True:
        new_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        contrast = all(abs(new_color.red() - color.red()) + abs(new_color.green() - color.green()) + abs(new_color.blue() - color.blue()) > 200 for color in existing_colors)
        if contrast:
            return new_color
        
def to_subscript(text):
    subscript_map = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')
    return text.translate(subscript_map)