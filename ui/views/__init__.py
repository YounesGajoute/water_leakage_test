"""
Views module for UI components
"""

from .main_view import MainView
from .reference_view import ReferenceView
from .settings_view import SettingsView
from .calibration_view import CalibrationView

__all__ = [
    'MainView',
    'ReferenceView', 
    'SettingsView',
    'CalibrationView'
]