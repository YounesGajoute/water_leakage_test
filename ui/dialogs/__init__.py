"""
Dialogs module for modal dialog components
"""

from .reference_dialog import ReferenceDialog
from .login_dialog import LoginInterface
from .password_change_dialog import PasswordChangeDialog, show_password_change_dialog

__all__ = [
    'ReferenceDialog',
    'LoginInterface',
    'PasswordChangeDialog',
    'show_password_change_dialog'
]