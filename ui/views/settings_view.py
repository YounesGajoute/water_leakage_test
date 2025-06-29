# ui/views/enhanced_settings_view.py
"""
Enhanced Settings View with Input State Monitoring and Password Management
Supports M100 Motor Controller integration and live GPIO monitoring
No messageboxes - uses status updates and print statements only
"""

import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import threading
import time
import hashlib
from typing import Dict, Any, Optional
from ui.components.numeric_keypad import get_numeric_input


class EnhancedSettingsView:
    def __init__(self, parent, app_controller, colors):
        self.parent = parent
        self.app_controller = app_controller
        self.colors = colors
        
        # Settings variables
        self.m100_enabled_var = tk.BooleanVar()
        self.auto_frequency_var = tk.BooleanVar()
        self.port_var = tk.StringVar()
        self.baudrate_var = tk.StringVar()
        self.slave_address_var = tk.StringVar()
        self.default_frequency_var = tk.StringVar()
        
        # Password variables
        self.current_password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        
        # Connection test results
        self.connection_status = tk.StringVar(value="Not tested")
        
        # Input monitoring
        self.input_state_labels = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        self.stop_monitoring = False
        
        # Password status
        self.password_status_label = None
        
        # Status label for general feedback
        self.general_status_label = None
        
        # Create settings view frame
        self.settings_frame = None

    def show(self):
        """Display the enhanced settings view with a vertical scrollbar"""
        # Create a canvas and a vertical scrollbar
        canvas = tk.Canvas(self.parent, bg=self.colors.get('white', '#FFFFFF'), highlightthickness=0)
        v_scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Create settings frame inside the canvas
        self.settings_frame = tk.Frame(canvas, bg=self.colors.get('white', '#FFFFFF'))
        self.settings_frame_id = canvas.create_window((0, 0), window=self.settings_frame, anchor="nw")

        # Configure scrolling
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.settings_frame.bind("<Configure>", on_frame_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Resize the canvas window when the canvas size changes
        def on_canvas_configure(event):
            canvas.itemconfig(self.settings_frame_id, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Initialize default settings in database if needed
        self.initialize_default_settings()
        
        # Create header
        self.create_header()
        
        # Create status section
        self.create_status_section()
        
        # Load current settings from database
        self.load_current_settings()
        
        # Create settings sections
        self.create_motor_control_section()
        self.create_m100_settings()
        self.create_test_sequence_settings()
        self.create_password_management_section()
        self.create_input_monitoring()
        
        # Create control buttons
        self.create_control_buttons()

    def create_header(self):
        """Create the header section"""
        header_frame = tk.Frame(self.settings_frame, bg=self.colors.get('white', '#FFFFFF'))
        header_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = tk.Label(
            header_frame, 
            text="System Settings & Configuration", 
            font=('Arial', 18, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3')
        )
        title_label.pack(side='left')
        
        # Add connection status indicator
        status_frame = tk.Frame(header_frame, bg=self.colors.get('white', '#FFFFFF'))
        status_frame.pack(side='right', padx=20)
        
        tk.Label(
            status_frame,
            text="M100 Status:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222')
        ).pack(side='left')
        
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.connection_status,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        )
        self.status_label.pack(side='left', padx=(5, 0))

    def create_status_section(self):
        """Create status section for general feedback"""
        status_frame = tk.Frame(self.settings_frame, bg=self.colors.get('white', '#FFFFFF'))
        status_frame.pack(fill='x', padx=20, pady=5)
        
        self.general_status_label = tk.Label(
            status_frame,
            text="Ready",
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        )
        self.general_status_label.pack(side='left')

    def create_motor_control_section(self):
        """(No-op) Motor control settings are handled in other sections."""
        pass

    def create_m100_settings(self):
        """Create M100 motor controller settings section"""
        m100_frame = tk.LabelFrame(
            self.settings_frame, 
            text="M100 Motor Controller Settings", 
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=10,
            pady=10
        )
        m100_frame.pack(fill='x', padx=20, pady=10)
        
        # Enable M100 control
        enable_frame = tk.Frame(m100_frame, bg=self.colors.get('white', '#FFFFFF'))
        enable_frame.pack(fill='x', pady=5)
        
        enable_check = tk.Checkbutton(
            enable_frame,
            text="Enable M100 Motor Controller (RS-485)",
            variable=self.m100_enabled_var,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            command=self.on_m100_enable_change
        )
        enable_check.pack(side='left')
        
        # Communication settings container
        self.comm_container = tk.Frame(m100_frame, bg=self.colors.get('white', '#FFFFFF'))
        self.comm_container.pack(fill='x', pady=10)
        
        # Serial port selection
        port_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        port_frame.pack(fill='x', pady=5)
        
        tk.Label(
            port_frame,
            text="Serial Port:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        port_combo = ttk.Combobox(
            port_frame,
            textvariable=self.port_var,
            values=self.get_available_ports(),
            width=15
        )
        port_combo.pack(side='left', padx=10)
        
        refresh_button = tk.Button(
            port_frame,
            text="Refresh Now",
            command=self.refresh_ports,
            font=('Arial', 10),
            bg=self.colors.get('secondary', self.colors.get('primary', '#00B2E3')),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=10
        )
        refresh_button.pack(side='left', padx=5)
        
        # Baud rate
        baud_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        baud_frame.pack(fill='x', pady=5)
        
        tk.Label(
            baud_frame,
            text="Baud Rate:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        baud_combo = ttk.Combobox(
            baud_frame,
            textvariable=self.baudrate_var,
            values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
            state="readonly",
            width=10
        )
        baud_combo.pack(side='left', padx=10)
        
        # Slave address
        slave_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        slave_frame.pack(fill='x', pady=5)
        
        tk.Label(
            slave_frame,
            text="Slave Address:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        slave_entry = tk.Entry(slave_frame, textvariable=self.slave_address_var, width=10)
        slave_entry.pack(side='left', padx=10)
        
        # Keypad button for slave address
        slave_keypad_btn = tk.Button(
            slave_frame,
            text="⌨",
            command=lambda: self.open_keypad_for_entry(self.slave_address_var, "Slave Address", 1, 247, 0),
            font=('Arial', 10, 'bold'),
            bg=self.colors.get('secondary', self.colors.get('primary', '#00B2E3')),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            width=3
        )
        slave_keypad_btn.pack(side='left', padx=5)
        
        tk.Label(
            slave_frame,
            text="(1-247)",
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        ).pack(side='left', padx=5)
        
        # Default frequency
        freq_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        freq_frame.pack(fill='x', pady=5)
        
        tk.Label(
            freq_frame,
            text="Default Frequency (Hz):",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        freq_entry = tk.Entry(freq_frame, textvariable=self.default_frequency_var, width=10)
        freq_entry.pack(side='left', padx=10)
        
        # Keypad button for frequency
        freq_keypad_btn = tk.Button(
            freq_frame,
            text="⌨",
            command=lambda: self.open_keypad_for_entry(self.default_frequency_var, "Default Frequency (Hz)", 0.5, 60.0, 1),
            font=('Arial', 10, 'bold'),
            bg=self.colors.get('secondary', self.colors.get('primary', '#00B2E3')),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            width=3
        )
        freq_keypad_btn.pack(side='left', padx=5)
        
        tk.Label(
            freq_frame,
            text="(0.5-60.0)",
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        ).pack(side='left', padx=5)
        
        # Connection test
        test_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        test_frame.pack(fill='x', pady=10)
        
        test_button = tk.Button(
            test_frame,
            text="Test Connection",
            command=self.test_m100_connection,
            font=('Arial', 10),
            bg=self.colors.get('primary', '#00B2E3'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=15
        )
        test_button.pack(side='left')
        
        # Initially disable comm settings if M100 not enabled
        self.update_m100_settings_state()

    def create_test_sequence_settings(self):
        """Create adaptive test sequence settings"""
        sequence_frame = tk.LabelFrame(
            self.settings_frame,
            text="Test Sequence Configuration",
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=10,
            pady=10
        )
        sequence_frame.pack(fill='x', padx=20, pady=10)
        
        # Auto frequency control
        auto_freq_frame = tk.Frame(sequence_frame, bg=self.colors.get('white', '#FFFFFF'))
        auto_freq_frame.pack(fill='x', pady=5)
        
        auto_freq_check = tk.Checkbutton(
            auto_freq_frame,
            text="Enable Automatic Frequency Setting",
            variable=self.auto_frequency_var,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3')
        )
        auto_freq_check.pack(side='left')
        
        # Explanation
        explanation_frame = tk.Frame(sequence_frame, bg=self.colors.get('white', '#FFFFFF'))
        explanation_frame.pack(fill='x', pady=10)
        
        explanation_text = (
            "Test Sequence Modes:\n\n"
            "• With Automatic Frequency: Safety → Home → Position → Set Frequency → Start Motor → Monitor → Complete → Home\n"
            "• Without Automatic Frequency: Safety → Home → Position → Start Motor → Monitor → Complete → Home\n\n"
            "When automatic frequency is enabled, motor frequency will be set from reference parameters before starting."
        )
        
        explanation_label = tk.Label(
            explanation_frame,
            text=explanation_text,
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            justify='left',
            wraplength=800
        )
        explanation_label.pack(side='left')

    def create_password_management_section(self):
        """Create password management section"""
        password_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Password Management", 
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=10,
            pady=10
        )
        password_frame.pack(fill='x', padx=20, pady=10)
        
        # Current password
        current_frame = tk.Frame(password_frame, bg=self.colors.get('white', '#FFFFFF'))
        current_frame.pack(fill='x', pady=5)
        
        tk.Label(
            current_frame,
            text="Current Password:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        current_entry = tk.Entry(current_frame, textvariable=self.current_password_var, show="*", width=20)
        current_entry.pack(side='left', padx=10)
        current_entry.focus_set()  # Set focus for accessibility
        
        # New password
        new_frame = tk.Frame(password_frame, bg=self.colors.get('white', '#FFFFFF'))
        new_frame.pack(fill='x', pady=5)
        
        tk.Label(
            new_frame,
            text="New Password:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        new_entry = tk.Entry(new_frame, textvariable=self.new_password_var, show="*", width=20)
        new_entry.pack(side='left', padx=10)
        
        # Confirm password
        confirm_frame = tk.Frame(password_frame, bg=self.colors.get('white', '#FFFFFF'))
        confirm_frame.pack(fill='x', pady=5)
        
        tk.Label(
            confirm_frame,
            text="Confirm Password:",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        confirm_entry = tk.Entry(confirm_frame, textvariable=self.confirm_password_var, show="*", width=20)
        confirm_entry.pack(side='left', padx=10)
        
        # Change password button
        change_frame = tk.Frame(password_frame, bg=self.colors.get('white', '#FFFFFF'))
        change_frame.pack(fill='x', pady=10)
        
        change_button = tk.Button(
            change_frame,
            text="Change Password",
            command=self.change_password,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('primary', '#00B2E3'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=20,
            pady=5
        )
        change_button.pack(side='left')
        
        # Password status
        if not self.password_status_label:
            self.password_status_label = tk.Label(
                change_frame,
                text="No Changes",
                font=('Arial', 10),
                bg=self.colors.get('white', '#FFFFFF'),
                fg=self.colors.get('text_secondary', '#888888')
            )
        self.password_status_label.pack(side='left', padx=20)
        # Add tooltip or help text if needed
        # (Optional: Add tooltips using a tooltip library if desired)

    def create_input_monitoring(self):
        """Create input state monitoring section (without Input Pin column)"""
        input_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Input State Monitoring", 
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=10,
            pady=10
        )
        input_frame.pack(fill='x', padx=20, pady=10)
        
        # Create grid for input pins
        input_grid = tk.Frame(input_frame, bg=self.colors.get('white', '#FFFFFF'))
        input_grid.pack(fill='x', pady=10)
        
        # Header row (no Input Pin column)
        header_frame = tk.Frame(input_grid, bg=self.colors.get('white', '#FFFFFF'))
        header_frame.pack(fill='x', pady=5)
        
        tk.Label(
            header_frame,
            text="Description",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            width=20,
            anchor='w'
        ).pack(side='left', padx=10)
        
        tk.Label(
            header_frame,
            text="Status",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            width=10,
            anchor='w'
        ).pack(side='left', padx=10)
        
        tk.Label(
            header_frame,
            text="Value",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            width=8,
            anchor='w'
        ).pack(side='left', padx=10)
        
        # Create input pin rows (without Input Pin cell)
        input_pins = ["emergency_btn", "door_close", "tank_min", "start_button", 
                     "actuator_min", "actuator_max"]
        
        for pin_name in input_pins:
            self.create_input_row(input_grid, pin_name)

    def create_input_row(self, parent, pin_name):
        """Create a row for a single input pin (without Input Pin cell)"""
        row_frame = tk.Frame(parent, bg=self.colors.get('white', '#FFFFFF'))
        row_frame.pack(fill='x', pady=2)
        
        # Get pin info
        pin_info = self.get_pin_info(pin_name)
        
        # Remove Pin name cell
        # tk.Label(
        #     row_frame,
        #     text=f"GPIO{pin_info['pin']}",
        #     font=('Arial', 11),
        #     bg=self.colors['white'],
        #     fg=self.colors['text_primary'],
        #     width=15,
        #     anchor='w'
        # ).pack(side='left')
        
        # Description
        tk.Label(
            row_frame,
            text=pin_info['description'],
            font=('Arial', 11),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            width=20,
            anchor='w'
        ).pack(side='left', padx=10)
        
        # Status indicator
        status_var = tk.StringVar(value="Unknown")
        self.input_state_labels[pin_name] = status_var
        
        status_label = tk.Label(
            row_frame,
            textvariable=status_var,
            font=('Arial', 11, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            width=10,
            anchor='w'
        )
        status_label.pack(side='left', padx=10)
        
        # Value indicator
        value_var = tk.StringVar(value="-")
        self.input_state_labels[f"{pin_name}_value"] = value_var
        
        value_label = tk.Label(
            row_frame,
            textvariable=value_var,
            font=('Arial', 11, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            width=8,
            anchor='w'
        )
        value_label.pack(side='left', padx=10)

    def get_pin_info(self, pin_name):
        """Get pin information from hardware manager"""
        if hasattr(self.app_controller, 'hardware_manager') and self.app_controller.hardware_manager:
            return self.app_controller.hardware_manager.gpio_pins.get(pin_name, {
                'pin': 'N/A',
                'description': 'Unknown',
                'inverted': False
            })
        else:
            # Fallback pin info
            fallback_pins = {
                "emergency_btn": {"pin": 17, "description": "Emergency Button", "inverted": True},
                "door_close": {"pin": 4, "description": "Door Closure Switch", "inverted": False},
                "tank_min": {"pin": 23, "description": "Tank Min Level", "inverted": False},
                "start_button": {"pin": 6, "description": "Start Button", "inverted": False},
                "actuator_min": {"pin": 27, "description": "Actuator Min", "inverted": False},
                "actuator_max": {"pin": 22, "description": "Actuator Max", "inverted": False}
            }
            return fallback_pins.get(pin_name, {"pin": "N/A", "description": "Unknown", "inverted": False})

    def cleanup(self):
        """Cleanup resources when view is destroyed"""
        print("Settings view cleanup completed")

    def initialize_default_settings(self):
        """Initialize default settings in settings.json if they don't exist"""
        try:
            # Password hash
            if not self.app_controller.settings.get("password_hash"):
                default_hash = hashlib.sha256('Admin123'.encode()).hexdigest()
                self.app_controller.settings["password_hash"] = default_hash
                print("Default password hash initialized in settings.json")
            # M100 config
            if not self.app_controller.settings.get("m100"):
                self.app_controller.settings["m100"] = {
                    'enabled': False,
                    'auto_frequency': False,
                    'port': '/dev/ttyUSB0',
                    'baudrate': 9600,
                    'slave_address': 1,
                    'default_frequency': 25.0
                }
                print("Default M100 config initialized in settings.json")
            # UI config
            if not self.app_controller.settings.get("ui"):
                self.app_controller.settings["ui"] = {
                    'theme': 'default',
                    'fullscreen': True,
                    'auto_save': True
                }
                print("Default UI config initialized in settings.json")
            # Motor config
            if not self.app_controller.settings.get("motor"):
                self.app_controller.settings["motor"] = {
                    'default_speed': 25,
                    'home_timeout': 120,
                    'move_timeout': 60
                }
                print("Default motor config initialized in settings.json")
            self.app_controller.save_settings()
        except Exception as e:
            print(f"Error initializing default settings: {e}")
            self.update_general_status(f"Failed to initialize defaults: {e}", 'error')

    def reset_to_defaults(self):
        """Reset all settings to defaults in settings.json"""
        self.update_general_status("Resetting all settings to defaults...", 'info')
        try:
            self.app_controller.settings["password_hash"] = hashlib.sha256('Admin123'.encode()).hexdigest()
            self.app_controller.settings["m100"] = {
                'enabled': False,
                'auto_frequency': False,
                'port': '/dev/ttyUSB0',
                'baudrate': 9600,
                'slave_address': 1,
                'default_frequency': 25.0
            }
            self.app_controller.settings["ui"] = {
                'theme': 'default',
                'fullscreen': True,
                'auto_save': True
            }
            self.app_controller.settings["motor"] = {
                'default_speed': 25,
                'home_timeout': 120,
                'move_timeout': 60
            }
            self.app_controller.save_settings()
            # Update UI variables
            self.m100_enabled_var.set(False)
            self.auto_frequency_var.set(False)
            self.port_var.set('/dev/ttyUSB0')
            self.baudrate_var.set('9600')
            self.slave_address_var.set('1')
            self.default_frequency_var.set('25.0')
            self.clear_password_fields()
            self.update_m100_settings_state()
            self.connection_status.set("Not tested")
            self.status_label.configure(fg=self.colors.get('text_secondary', '#888888'))
            self.update_general_status("All settings have been reset to defaults", 'success')
            print("All settings have been reset to defaults in settings.json")
        except Exception as e:
            self.update_general_status(f"Failed to reset settings: {str(e)}", 'error')
            print(f"Failed to reset settings: {str(e)}")

    def load_current_settings(self):
        """Load current settings from settings.json"""
        try:
            # Load M100 settings from settings.json
            m100_config = self.app_controller.settings.get("m100", {})
            self.m100_enabled_var.set(m100_config.get('enabled', False))
            self.auto_frequency_var.set(m100_config.get('auto_frequency', False))
            self.port_var.set(m100_config.get('port', '/dev/ttyUSB0'))
            self.baudrate_var.set(str(m100_config.get('baudrate', 9600)))
            self.slave_address_var.set(str(m100_config.get('slave_address', 1)))
            self.default_frequency_var.set(str(m100_config.get('default_frequency', 25.0)))
        except Exception as e:
            print(f"Error loading settings from settings.json: {e}")
            self.update_general_status(f"Failed to load settings: {e}", 'error')

    def get_available_ports(self):
        """Get list of available serial ports"""
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [port.device for port in ports]
            if not port_list:
                port_list = ['/dev/ttyUSB0', '/dev/ttyUSB1', 'COM1', 'COM2']
            return port_list
        except Exception:
            return ['/dev/ttyUSB0', '/dev/ttyUSB1', 'COM1', 'COM2']

    def refresh_ports(self):
        """Refresh the list of available ports"""
        try:
            # Find the port combobox and update its values
            for widget in self.comm_container.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Combobox) and child.cget('textvariable') == str(self.port_var):
                        child['values'] = self.get_available_ports()
                        break
            print("Port list refreshed")
        except Exception as e:
            print(f"Error refreshing ports: {e}")

    def on_m100_enable_change(self):
        """Handle M100 enable/disable change"""
        self.update_m100_settings_state()

    def update_m100_settings_state(self):
        """Update M100 settings widgets state based on enable checkbox"""
        state = 'normal' if self.m100_enabled_var.get() else 'disabled'
        
        # Update all widgets in comm_container
        for widget in self.comm_container.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, (tk.Entry, ttk.Combobox, tk.Button)):
                    try:
                        child.configure(state=state)
                    except:
                        pass

    def test_m100_connection(self):
        """Test M100 connection with current settings"""
        try:
            if not self.m100_enabled_var.get():
                print("M100 Disabled")
                return
            
            # Validate settings
            if not self.validate_m100_settings():
                return
            
            self.connection_status.set("Testing...")
            self.status_label.configure(fg=self.colors.get('warning', '#f59e0b'))
            if self.settings_frame is not None:
                self.settings_frame.update()
            
            # Import and test M100 controller
            from hardware.m100_controller import M100Controller, M100Config  # type: ignore
            
            config = M100Config(
                port=self.port_var.get(),
                baudrate=int(self.baudrate_var.get()),
                slave_address=int(self.slave_address_var.get())
            )
            
            controller = M100Controller(config)
            
            if controller.connect():
                # Test basic communication
                status = controller.read_status()
                if status:
                    self.connection_status.set("Connected")
                    self.status_label.configure(fg=self.colors.get('success', '#10b981'))
                    print(f"M100 controller connected successfully!\n\nPort: {config.port}\nBaud Rate: {config.baudrate}\nStatus: {status}")
                else:
                    self.connection_status.set("Communication Error")
                    self.status_label.configure(fg=self.colors.get('error', '#ef4444'))
                    print("Connected but cannot read status")
                
                controller.disconnect()
            else:
                self.connection_status.set("Connection Failed")
                self.status_label.configure(fg=self.colors.get('error', '#ef4444'))
                print("Cannot connect to M100 controller")
                
        except Exception as e:
            self.connection_status.set("Error")
            self.status_label.configure(fg=self.colors.get('error', '#ef4444'))
            print(f"Connection test failed:\n{str(e)}")

    def test_m100_sequence(self):
        """Test complete M100 sequence"""
        try:
            if not self.m100_enabled_var.get():
                print("M100 Disabled")
                return
            
            if not self.validate_m100_settings():
                return
            
            # Run test sequence in a separate thread
            test_thread = threading.Thread(target=self._run_m100_test_sequence, daemon=True)
            test_thread.start()
            
        except Exception as e:
            print(f"Failed to start test sequence:\n{str(e)}")

    def _run_m100_test_sequence(self):
        """Run M100 test sequence in background thread"""
        try:
            from hardware.m100_controller import M100Controller, M100Config  # type: ignore
            import time
            
            config = M100Config(
                port=self.port_var.get(),
                baudrate=int(self.baudrate_var.get()),
                slave_address=int(self.slave_address_var.get())
            )
            
            controller = M100Controller(config)
            
            # Update status in main thread
            if self.settings_frame is not None:
                self.settings_frame.after(0, lambda: self.connection_status.set("Testing sequence..."))
            
            if not controller.connect():
                raise Exception("Failed to connect to M100")
            
            # Test frequency setting if enabled
            if self.auto_frequency_var.get():
                frequency = float(self.default_frequency_var.get())
                if not controller.set_frequency(frequency):
                    raise Exception("Failed to set frequency")
                time.sleep(1)
            
            # Start motor
            if not controller.start_motor_relay(self.app_controller.hardware_manager):
                raise Exception("Failed to start motor (relay)")
            
            # Run for 10 seconds
            for i in range(10):
                time.sleep(1)
                status = controller.read_status()
                if not status or not status['running']:
                    raise Exception("Motor stopped unexpectedly")
            
            # Stop motor
            if not controller.stop_motor_relay(self.app_controller.hardware_manager):
                raise Exception("Failed to stop motor (relay)")
            
            controller.disconnect()
            
            # Success
            if self.settings_frame is not None:
                self.settings_frame.after(0, lambda: self.connection_status.set("Test Passed"))
                self.settings_frame.after(0, lambda: self.status_label.configure(fg=self.colors.get('success', '#10b981')))
                print("M100 sequence test completed successfully!")
            
        except Exception as e:
            if self.settings_frame is not None:
                self.settings_frame.after(0, lambda: self.connection_status.set("Test Failed"))
                self.settings_frame.after(0, lambda: self.status_label.configure(fg=self.colors.get('error', '#ef4444')))
                print(f"M100 sequence test failed:\n{str(e)}")

    def validate_m100_settings(self):
        """Validate M100 settings"""
        try:
            # Validate slave address
            slave_addr = int(self.slave_address_var.get())
            if not (1 <= slave_addr <= 247):
                print("Slave address must be between 1 and 247")
                return False
            
            # Validate frequency
            frequency = float(self.default_frequency_var.get())
            if not (0.5 <= frequency <= 60.0):
                print("Frequency must be between 0.5 and 60.0 Hz")
                return False
            
            # Validate port
            port = self.port_var.get().strip()
            if not port:
                print("Serial port cannot be empty")
                return False
            
            return True
            
        except ValueError:
            print("Invalid numeric values in M100 settings")
            return False

    def change_password(self):
        """Change system password using settings.json"""
        try:
            current = self.current_password_var.get()
            new_pwd = self.new_password_var.get()
            confirm = self.confirm_password_var.get()
            # Validate current password
            if not current:
                self.update_password_status("Current password required", 'error')
                self.update_general_status("Please enter your current password", 'error')
                print("Please enter your current password")
                return
            stored_hash = self.app_controller.settings.get("password_hash", "")
            current_hash = hashlib.sha256(current.encode()).hexdigest()
            if current_hash != stored_hash:
                self.update_password_status("Authentication failed", 'error')
                self.update_general_status("Current password is incorrect", 'error')
                print("Current password is incorrect")
                return
            # Validate new password
            if not new_pwd:
                self.update_password_status("New password required", 'error')
                self.update_general_status("Please enter a new password", 'error')
                print("Please enter a new password")
                return
            if len(new_pwd) < 6:
                self.update_password_status("Password too short", 'error')
                self.update_general_status("Password must be at least 6 characters long", 'error')
                print("Password must be at least 6 characters long")
                return
            if not any(c.isalpha() for c in new_pwd) or not any(c.isdigit() for c in new_pwd):
                self.update_password_status("Invalid password format", 'error')
                self.update_general_status("Password must contain both letters and numbers", 'error')
                print("Password must contain both letters and numbers")
                return
            if new_pwd != confirm:
                self.update_password_status("Passwords do not match", 'error')
                self.update_general_status("New password and confirmation do not match", 'error')
                print("New password and confirmation do not match")
                return
            if new_pwd == current:
                self.update_password_status("Password unchanged", 'warning')
                self.update_general_status("New password must be different from current password", 'warning')
                print("New password must be different from current password")
                return
            # Update password in settings.json
            self.update_password_status("Changing password...", 'warning')
            new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
            self.app_controller.settings["password_hash"] = new_hash
            self.app_controller.save_settings()
            self.clear_password_fields()
            self.update_password_status("Password changed successfully", 'success')
            self.update_general_status("Password changed successfully!", 'success')
            print("Password changed successfully!")
            if self.settings_frame is not None:
                self.settings_frame.after(5000, lambda: self.update_password_status("No Changes", 'inactive'))
        except Exception as e:
            self.update_password_status("Error occurred", 'error')
            self.update_general_status(f"Password change failed: {str(e)}", 'error')
            print(f"Password change failed: {str(e)}")

    def update_general_status(self, message, status):
        """Update general status message"""
        if self.general_status_label:
            self.general_status_label.config(text=message)
            self.general_status_label.configure(fg=self.colors.get(status, 'black'))

    def update_password_status(self, message, status):
        """Update password status message"""
        if self.password_status_label:
            self.password_status_label.config(text=message)
            self.password_status_label.configure(fg=self.colors.get(status, 'black'))

    def clear_password_fields(self):
        """Clear password fields"""
        self.current_password_var.set('')
        self.new_password_var.set('')
        self.confirm_password_var.set('')

    def create_control_buttons(self):
        """Create control buttons"""
        button_frame = tk.Frame(self.settings_frame, bg=self.colors.get('white', '#FFFFFF'))
        button_frame.pack(fill='x', padx=20, pady=20)

        # Save button
        save_button = tk.Button(
            button_frame,
            text="Save All Settings",
            command=self.save_all_settings,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('success', '#10b981'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=20,
            pady=10
        )
        save_button.pack(side='left', padx=10)
        save_button.focus_set()  # Set initial focus for accessibility

        test_sequence_button = tk.Button(
            button_frame,
            text="Test M100 Sequence",
            command=self.test_m100_sequence,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('warning', '#f59e0b'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=20,
            pady=10
        )
        test_sequence_button.pack(side='left', padx=10)

        # Use secondary color if available, else fallback to primary
        reset_color = self.colors.get('secondary', self.colors.get('primary', '#00B2E3'))
        reset_button = tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('error', '#ef4444'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=20,
            pady=10
        )
        reset_button.pack(side='right', padx=10)

    def save_all_settings(self):
        """Save all settings to settings.json"""
        try:
            self.app_controller.settings["m100"] = {
                'enabled': self.m100_enabled_var.get(),
                'auto_frequency': self.auto_frequency_var.get(),
                'port': self.port_var.get(),
                'baudrate': int(self.baudrate_var.get()),
                'slave_address': int(self.slave_address_var.get()),
                'default_frequency': float(self.default_frequency_var.get())
            }
            # Add other settings as needed
            self.app_controller.save_settings()
            self.update_general_status("All settings saved successfully!", 'success')
            print("All settings saved successfully to settings.json")
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.update_general_status(f"Failed to save settings: {e}", 'error')

    def open_keypad_for_entry(self, var, title, min_value, max_value, decimal_places):
        """Open the numeric keypad for input"""
        try:
            # Get current value as initial value
            current_value = float(var.get()) if var.get() else 0.0
            
            # Open numeric keypad dialog
            result = get_numeric_input(
                parent=self.parent,
                colors=self.colors,
                title=title,
                initial_value=current_value,
                min_value=min_value,
                max_value=max_value,
                decimal_places=decimal_places
            )
            
            # Update the variable if a value was entered
            if result is not None:
                var.set(str(result))
                print(f"{title} updated to: {result}")
            else:
                print(f"{title} input cancelled")
                
        except Exception as e:
            print(f"Error opening keypad for {title}: {e}")
            self.update_general_status(f"Keypad error: {e}", 'error')

# Create alias for backward compatibility
SettingsView = EnhancedSettingsView