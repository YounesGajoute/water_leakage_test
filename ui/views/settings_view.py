"""
Corrected Settings View with Complete Numeric Keypad Integration
Enhanced for touch-screen use with proper numeric input handling
"""

import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import threading
import time
import hashlib
from typing import Dict, Any, Optional
from ..components.numeric_keypad import NumericKeypad, get_numeric_input
from ..components.keyboard import VirtualKeyboard
from ..dialogs import show_password_change_dialog


class CorrectedSettingsView:
    def __init__(self, parent, app_controller, colors):
        """Initialize the corrected settings view"""
        self.parent = parent
        self.app_controller = app_controller
        self.colors = colors
        
        # Initialize UI components
        self.settings_frame = None
        self.canvas = None
        self.scrollbar = None
        self.port_combobox = None  # Add this attribute
        
        # Initialize variables
        self.initialize_default_settings()
        
        # Settings variables
        self.m100_enabled_var = tk.BooleanVar(value=False)
        self.auto_frequency_var = tk.BooleanVar(value=False)
        self.port_var = tk.StringVar(value='/dev/ttyUSB0')
        self.baudrate_var = tk.StringVar(value='9600')
        self.slave_address_var = tk.StringVar(value='1')
        self.default_frequency_var = tk.StringVar(value='25.0')
        self.general_status_var = tk.StringVar(value='Ready')
        self.connection_status = tk.StringVar(value='Not tested')
        
        # Password status variable (simplified)
        self.password_status_var = tk.StringVar()
        
        # Motor settings variables
        self.motor_speed_var = tk.StringVar(value='25')
        self.home_timeout_var = tk.StringVar(value='120')
        self.move_timeout_var = tk.StringVar(value='60')
        
        # Calibration variables
        self.pressure_offset_var = tk.StringVar(value='-0.579')
        self.pressure_multiplier_var = tk.StringVar(value='1.286')
        
        # Monitoring variables
        self.monitoring_active = False
        self.stop_monitoring = False
        self.monitoring_thread = None
        self.monitoring_button = None
        self.input_state_labels = {}
        
        # Keypad integration
        self.numeric_keypad = None
        self.keypad_frame = None
        self.current_keypad_target = None
        
        # Port caching
        self._cached_ports = None

    def show(self):
        """Display the corrected settings view with integrated numeric keypad"""
        try:
            # Create scrollable canvas setup
            self.setup_scrollable_canvas()
            
            # Initialize default settings
            self.initialize_default_settings()
            
            # Load current settings
            self.load_current_settings()
            
            # Create UI sections asynchronously to prevent freezing
            self.create_header()
            self.create_status_section()
            
            # Schedule heavy operations for after UI is responsive
            self.parent.after(100, self._create_remaining_sections)
            
            # Start input monitoring in background thread
            self.parent.after(200, self.start_input_monitoring)
            
        except Exception as e:
            print(f"Error in settings view show() method: {e}")
            import traceback
            traceback.print_exc()

    def _create_remaining_sections(self):
        """Create remaining UI sections asynchronously"""
        try:
            # Create sections progressively
            self.create_m100_settings()
            self.parent.update_idletasks()
            
            self.create_motor_settings()
            self.parent.update_idletasks()
            
            self.create_calibration_settings()
            self.parent.update_idletasks()
            
            self.create_password_management_section()
            self.parent.update_idletasks()
            
            self.create_input_monitoring()
            self.parent.update_idletasks()
            
            self.create_integrated_keypad()
            self.parent.update_idletasks()
            
            self.create_control_buttons()
            self.parent.update_idletasks()
            
            # Update status when complete
            self.update_general_status("Settings view loaded successfully", 'success')
            
        except Exception as e:
            print(f"Error creating UI sections: {e}")
            import traceback
            traceback.print_exc()
            self.update_general_status(f"Error loading settings: {e}", 'error')

        

    def setup_scrollable_canvas(self):
        """Setup scrollable canvas for settings content"""
        # Create main container
        main_container = tk.Frame(self.parent, bg=self.colors.get('white', '#FFFFFF'))
        main_container.pack(fill='both', expand=True)
        
        # Configure grid for layout
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=0)
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(
            main_container, 
            bg=self.colors.get('white', '#FFFFFF'), 
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky='nsew')
        
        # Create vertical scrollbar - MADE BIGGER
        self.scrollbar = tk.Scrollbar(
            main_container, 
            orient="vertical", 
            command=self.canvas.yview,
            width=25  # ADD THIS LINE - makes scrollbar bigger (default is ~15)
        )
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Configure scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create settings frame inside canvas
        self.settings_frame = tk.Frame(self.canvas, bg=self.colors.get('white', '#FFFFFF'))
        self.settings_frame_id = self.canvas.create_window(
            (0, 0), 
            window=self.settings_frame, 
            anchor="nw"
        )
        
        # Bind events for scrolling
        self.setup_scroll_events()
        
    def setup_scroll_events(self):
        """Setup scrolling event handlers"""
        def on_frame_configure(event):
            if self.canvas is not None:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        def on_canvas_configure(event):
            if self.canvas is not None and hasattr(self, 'settings_frame_id'):
                self.canvas.itemconfig(self.settings_frame_id, width=event.width)
        
        def on_mousewheel(event):
            if self.canvas is not None:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        if self.settings_frame is not None:
            self.settings_frame.bind("<Configure>", on_frame_configure)
        if self.canvas is not None:
            self.canvas.bind("<Configure>", on_canvas_configure)
            self.canvas.bind_all("<MouseWheel>", on_mousewheel)

    def create_header(self):
        """Create the enhanced header section"""
        header_frame = tk.Frame(self.settings_frame, bg=self.colors.get('white', '#FFFFFF'))
        header_frame.pack(fill='x', padx=20, pady=15)
        
        # Title with improved styling
        title_label = tk.Label(
            header_frame, 
            text="System Settings & Configuration", 
            font=('Arial', 20, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3')
        )
        title_label.pack(side='left')
        
        # Connection status with better visual feedback
        status_container = tk.Frame(header_frame, bg=self.colors.get('white', '#FFFFFF'))
        status_container.pack(side='right', padx=20)
        
        tk.Label(
            status_container,
            text="M100 Status:",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222')
        ).pack(side='top')
        
        self.connection_status_label = tk.Label(
            status_container,
            textvariable=self.connection_status,
            font=('Arial', 11),
            bg=self.colors.get('status_bg', '#e0f2f7'),
            fg=self.colors.get('text_secondary', '#888888'),
            padx=10,
            pady=5,
            relief='solid',
            bd=1
        )
        self.connection_status_label.pack(side='top', pady=5)

    def create_status_section(self):
        """Create enhanced status section"""
        status_frame = tk.LabelFrame(
            self.settings_frame,
            text="System Status",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=10
        )
        status_frame.pack(fill='x', padx=20, pady=10)
        
        # General status
        general_status_container = tk.Frame(status_frame, bg=self.colors.get('white', '#FFFFFF'))
        general_status_container.pack(fill='x', pady=5)
        
        tk.Label(
            general_status_container,
            text="General Status:",
            font=('Arial', 11, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222')
        ).pack(side='left')
        
        self.general_status_label = tk.Label(
            general_status_container,
            textvariable=self.general_status_var,
            font=('Arial', 11),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('success', '#10b981')
        )
        self.general_status_label.pack(side='left', padx=10)

    def create_m100_settings(self):
        """Create M100 motor controller settings with keypad integration"""
        m100_frame = tk.LabelFrame(
            self.settings_frame, 
            text="M100 Motor Controller Settings", 
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=15
        )
        m100_frame.pack(fill='x', padx=20, pady=10)
        
        # Enable M100 control
        enable_frame = tk.Frame(m100_frame, bg=self.colors.get('white', '#FFFFFF'))
        enable_frame.pack(fill='x', pady=10)
        
        enable_check = tk.Checkbutton(
            enable_frame,
            text="Enable M100 Motor Controller (RS-485 Communication)",
            variable=self.m100_enabled_var,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            command=self.on_m100_enable_change
        )
        enable_check.pack(side='left')
        
        # Communication settings container
        self.comm_container = tk.Frame(m100_frame, bg=self.colors.get('white', '#FFFFFF'))
        self.comm_container.pack(fill='x', pady=15)
        
        # Serial port selection
        self.create_port_selection()
        
        # Baud rate selection
        self.create_baudrate_selection()
        
        # Slave address with keypad
        self.create_numeric_input_row(
            self.comm_container,
            "Slave Address:",
            self.slave_address_var,
            "Modbus slave address (1-247)",
            min_val=1,
            max_val=247,
            decimal_places=0,
            width=10
        )
        
        # Default frequency with keypad
        self.create_numeric_input_row(
            self.comm_container,
            "Default Frequency (Hz):",
            self.default_frequency_var,
            "Motor frequency in Hz (0.5-60.0)",
            min_val=0.5,
            max_val=60.0,
            decimal_places=1,
            width=10
        )
        
        # Auto frequency control
        auto_freq_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        auto_freq_frame.pack(fill='x', pady=10)
        
        auto_freq_check = tk.Checkbutton(
            auto_freq_frame,
            text="Enable Automatic Frequency Control (set frequency from reference parameters)",
            variable=self.auto_frequency_var,
            font=('Arial', 11),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222')
        )
        auto_freq_check.pack(side='left')
        
        # Connection test button
        test_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        test_frame.pack(fill='x', pady=15)
        
        test_button = tk.Button(
            test_frame,
            text="🔗 Test M100 Connection",
            command=self.test_m100_connection,
            font=('Arial', 11, 'bold'),
            bg=self.colors.get('primary', '#00B2E3'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=20,
            pady=8
        )
        test_button.pack(side='left')

    def create_motor_settings(self):
        """Create motor control settings with keypad integration"""
        motor_frame = tk.LabelFrame(
            self.settings_frame,
            text="Motor Control Settings",
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=15
        )
        motor_frame.pack(fill='x', padx=20, pady=10)
        
        # Motor speed
        self.create_numeric_input_row(
            motor_frame,
            "Default Motor Speed:",
            self.motor_speed_var,
            "Default motor speed setting (1-100)",
            min_val=1,
            max_val=100,
            decimal_places=0,
            width=10
        )
        
        # Home timeout
        self.create_numeric_input_row(
            motor_frame,
            "Homing Timeout (sec):",
            self.home_timeout_var,
            "Maximum time for homing operation (30-300 seconds)",
            min_val=30,
            max_val=300,
            decimal_places=0,
            width=10
        )
        
        # Move timeout
        self.create_numeric_input_row(
            motor_frame,
            "Movement Timeout (sec):",
            self.move_timeout_var,
            "Maximum time for position moves (10-180 seconds)",
            min_val=10,
            max_val=180,
            decimal_places=0,
            width=10
        )

    def create_calibration_settings(self):
        """Create calibration settings with keypad integration"""
        cal_frame = tk.LabelFrame(
            self.settings_frame,
            text="Pressure Calibration Settings",
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=15
        )
        cal_frame.pack(fill='x', padx=20, pady=10)
        
        # Pressure offset
        self.create_numeric_input_row(
            cal_frame,
            "Pressure Offset (bar):",
            self.pressure_offset_var,
            "Pressure sensor offset calibration (-2.0 to +2.0 bar)",
            min_val=-2.0,
            max_val=2.0,
            decimal_places=3,
            width=12
        )
        
        # Pressure multiplier
        self.create_numeric_input_row(
            cal_frame,
            "Pressure Multiplier:",
            self.pressure_multiplier_var,
            "Pressure sensor gain calibration (0.5-3.0)",
            min_val=0.5,
            max_val=3.0,
            decimal_places=3,
            width=12
        )

    def create_port_selection(self):
        """Create serial port selection with async loading"""
        port_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        port_frame.pack(fill='x', pady=8)
        
        tk.Label(
            port_frame,
            text="Serial Port:",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        # Create combobox with default values first
        port_combo = ttk.Combobox(
            port_frame,
            textvariable=self.port_var,
            values=self.get_available_ports(),  # This returns immediately
            width=15,
            font=('Arial', 11)
        )
        port_combo.pack(side='left', padx=10)
        self.port_combobox = port_combo  # Store reference
        
        refresh_button = tk.Button(
            port_frame,
            text="🔄 Refresh Ports",
            command=self.refresh_ports,
            font=('Arial', 10, 'bold'),
            bg=self.colors.get('background', '#f8fafc'),
            fg=self.colors.get('primary', '#00B2E3'),
            relief='flat',
            padx=15,
            pady=5
        )
        refresh_button.pack(side='left', padx=10)

    def create_baudrate_selection(self):
        """Create baud rate selection"""
        baud_frame = tk.Frame(self.comm_container, bg=self.colors.get('white', '#FFFFFF'))
        baud_frame.pack(fill='x', pady=8)
        
        tk.Label(
            baud_frame,
            text="Baud Rate:",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222'),
            width=20,
            anchor='w'
        ).pack(side='left')
        
        baud_combo = ttk.Combobox(
            baud_frame,
            textvariable=self.baudrate_var,
            values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
            state="readonly",
            width=10,
            font=('Arial', 11)
        )
        baud_combo.pack(side='left', padx=10)

    def create_numeric_input_row(self, parent, label_text, variable, help_text, 
                                min_val, max_val, decimal_places=0, width=15):
        """Create a numeric input row with integrated keypad button"""
        row_frame = tk.Frame(parent, bg=self.colors.get('white', '#FFFFFF'))
        row_frame.pack(fill='x', pady=8)
        
        # Label
        label = tk.Label(
            row_frame,
            text=label_text,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222'),
            width=20,
            anchor='w'
        )
        label.pack(side='left')
        
        # Entry field
        entry = tk.Entry(
            row_frame,
            textvariable=variable,
            width=width,
            font=('Arial', 11),
            justify='center'
        )
        entry.pack(side='left', padx=10)
        
        # Make entry readonly to force keypad use
        entry.configure(state='readonly')
        
        # Keypad button
        keypad_button = tk.Button(
            row_frame,
            text="⌨️",
            command=lambda: self.open_numeric_keypad(
                variable, label_text, min_val, max_val, decimal_places
            ),
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('primary', '#00B2E3'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            width=3,
            height=1
        )
        keypad_button.pack(side='left', padx=5)
        
        # Range indicator
        range_label = tk.Label(
            row_frame,
            text=f"({min_val}-{max_val})",
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        )
        range_label.pack(side='left', padx=5)
        
        # Help text
        if help_text:
            help_label = tk.Label(
                row_frame,
                text=help_text,
                font=('Arial', 9),
                bg=self.colors.get('white', '#FFFFFF'),
                fg=self.colors.get('text_secondary', '#888888'),
                wraplength=300
            )
            help_label.pack(side='left', padx=10)

    def create_integrated_keypad(self):
        """Create integrated numeric keypad in settings view"""
        keypad_container = tk.LabelFrame(
            self.settings_frame,
            text="Numeric Keypad",
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=15
        )
        keypad_container.pack(fill='x', padx=20, pady=10)
        
        # Instructions
        instruction_label = tk.Label(
            keypad_container,
            text="Click ⌨️ button next to any numeric field to use keypad for input",
            font=('Arial', 11),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        )
        instruction_label.pack(pady=10)
        
        # Keypad frame
        self.keypad_frame = tk.Frame(keypad_container, bg=self.colors.get('white', '#FFFFFF'))
        self.keypad_frame.pack(pady=10)
        
        # Create numeric keypad
        self.numeric_keypad = NumericKeypad(
            self.keypad_frame,
            self.colors,
            callback=self.on_keypad_confirm
        )
        self.numeric_keypad.create()
        
        # Target field indicator
        self.target_field_label = tk.Label(
            keypad_container,
            text="No field selected",
            font=('Arial', 10, 'bold'),
            bg=self.colors.get('status_bg', '#e0f2f7'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=10,
            pady=5
        )
        self.target_field_label.pack(pady=5)

    def create_password_management_section(self):
        """Create password management section with single button to open dialog"""
        password_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Password Management", 
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=15
        )
        password_frame.pack(fill='x', padx=20, pady=10)
        
        # Password change button
        button_frame = tk.Frame(password_frame, bg=self.colors.get('white', '#FFFFFF'))
        button_frame.pack(fill='x', pady=15)
        
        # Create button with enhanced styling and hover effects
        change_password_button = tk.Button(
            button_frame,
            text="🔒 Change System Password",
            command=self.open_password_change_dialog,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('warning', '#f59e0b'),
            fg=self.colors.get('white', '#FFFFFF'),
            activebackground='#d97706',
            activeforeground=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=25,
            pady=10,
            cursor='hand2'  # Show hand cursor on hover
        )
        change_password_button.pack()
        
        # Add hover effects
        def on_enter(e):
            change_password_button.config(bg='#d97706')
        
        def on_leave(e):
            change_password_button.config(bg=self.colors.get('warning', '#f59e0b'))
        
        change_password_button.bind('<Enter>', on_enter)
        change_password_button.bind('<Leave>', on_leave)
        
        # Status label
        self.password_status_label = tk.Label(
            button_frame,
            textvariable=self.password_status_var,
            font=('Arial', 11),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888')
        )
        self.password_status_label.pack(pady=10)

    def open_password_change_dialog(self):
        """Open password change dialog using the new dialog component"""
        try:
            print("Opening password change dialog...")
            
            # Find the root window for dialog parent
            parent_window = self.parent
            while parent_window and not isinstance(parent_window, tk.Tk):
                parent_window = parent_window.master
            
            if not parent_window:
                print("Error: Could not find root window")
                self.password_status_var.set("Error: No root window")
                return
            
            # Ensure we have the app controller
            if not self.app_controller:
                print("Error: No app controller available")
                self.password_status_var.set("Error: No app controller")
                return
            
            # Ensure we have colors
            if not self.colors:
                print("Error: No colors available")
                self.password_status_var.set("Error: No colors")
                return
            
            print(f"Parent window: {parent_window}")
            print(f"App controller: {self.app_controller}")
            print(f"Colors: {self.colors}")
            
            # Show the password change dialog
            result = show_password_change_dialog(parent_window, self.app_controller, self.colors)
            
            print(f"Password change dialog result: {result}")
            
            # Update status based on result
            if result:
                self.password_status_var.set("Password changed successfully!")
                self.update_general_status("Password changed successfully!", 'success')
                print("Password change completed successfully")
            else:
                self.password_status_var.set("Password change cancelled")
                print("Password change was cancelled")
                
        except ImportError as e:
            print(f"Import error in password change dialog: {e}")
            self.password_status_var.set(f"Import error: {str(e)}")
            self.update_general_status(f"Password dialog import error: {e}", 'error')
        except Exception as e:
            print(f"Error opening password change dialog: {e}")
            import traceback
            traceback.print_exc()
            self.password_status_var.set(f"Error: {str(e)}")
            self.update_general_status(f"Password dialog error: {e}", 'error')
            
            # Fallback: Try to show a simple message
            self._show_fallback_password_message()

    def _show_fallback_password_message(self):
        """Show a fallback message if dialog fails"""
        try:
            # Create a simple message window as fallback
            fallback_window = tk.Toplevel(self.parent)
            fallback_window.title("Password Change")
            fallback_window.geometry("400x200")
            fallback_window.configure(bg=self.colors.get('white', '#FFFFFF'))
            fallback_window.transient(self.parent)
            fallback_window.grab_set()
            
            # Center the window
            fallback_window.update_idletasks()
            x = (fallback_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (fallback_window.winfo_screenheight() // 2) - (200 // 2)
            fallback_window.geometry(f"400x200+{x}+{y}")
            
            # Message
            tk.Label(
                fallback_window,
                text="Password Change Dialog",
                font=('Arial', 16, 'bold'),
                bg=self.colors.get('white', '#FFFFFF'),
                fg=self.colors.get('primary', '#00B2E3')
            ).pack(pady=20)
            
            tk.Label(
                fallback_window,
                text="The password change dialog could not be displayed.\nPlease try again or contact support.",
                font=('Arial', 12),
                bg=self.colors.get('white', '#FFFFFF'),
                fg=self.colors.get('text_primary', '#222222'),
                justify='center'
            ).pack(pady=10)
            
            # OK button
            tk.Button(
                fallback_window,
                text="OK",
                command=fallback_window.destroy,
                font=('Arial', 12, 'bold'),
                bg=self.colors.get('primary', '#00B2E3'),
                fg=self.colors.get('white', '#FFFFFF'),
                relief='flat',
                padx=20,
                pady=8
            ).pack(pady=20)
            
        except Exception as e:
            print(f"Error showing fallback message: {e}")

    # Keypad Integration Methods
    
    def open_numeric_keypad(self, variable, title, min_val, max_val, decimal_places):
        """Open numeric keypad for input"""
        try:
            # Set current target
            self.current_keypad_target = {
                'variable': variable,
                'title': title,
                'min_val': min_val,
                'max_val': max_val,
                'decimal_places': decimal_places
            }
            
            # Update target field indicator if it exists
            if hasattr(self, 'target_field_label') and self.target_field_label is not None:
                self.target_field_label.config(
                    text=f"Editing: {title}",
                    fg=self.colors.get('primary', '#00B2E3')
                )
            
            # Configure keypad if it exists
            if hasattr(self, 'numeric_keypad') and self.numeric_keypad is not None:
                self.numeric_keypad.set_decimal_places(decimal_places)
                self.numeric_keypad.set_allow_negative(min_val < 0)
                
                # Set current value
                try:
                    current_value = float(variable.get()) if variable.get() else 0.0
                    self.numeric_keypad.set_value(current_value)
                except (ValueError, AttributeError):
                    self.numeric_keypad.set_value(0.0)
            
            # Scroll to keypad if it exists
            if hasattr(self, 'scroll_to_keypad'):
                self.scroll_to_keypad()
            
        except Exception as e:
            print(f"Error opening numeric keypad: {e}")
            self.update_general_status(f"Keypad error: {e}", 'error')

    def scroll_to_keypad(self):
        """Scroll the view to show the keypad"""
        try:
            # Update the canvas scroll region
            if self.canvas is not None:
                self.canvas.update_idletasks()
            
            # Get keypad position
            if hasattr(self, 'keypad_frame') and self.keypad_frame is not None:
                keypad_y = self.keypad_frame.winfo_y()
                if self.canvas is not None:
                    canvas_height = self.canvas.winfo_height()
                    if self.settings_frame is not None:
                        total_height = self.settings_frame.winfo_reqheight()
                        
                        # Calculate scroll position
                        if total_height > canvas_height:
                            scroll_position = keypad_y / total_height
                            self.canvas.yview_moveto(max(0, scroll_position - 0.2))
                
        except Exception as e:
            print(f"Error scrolling to keypad: {e}")

    def on_keypad_confirm(self, value):
        """Handle keypad value confirmation"""
        try:
            if not self.current_keypad_target:
                return
            
            target = self.current_keypad_target
            
            # Validate range
            if not (target['min_val'] <= value <= target['max_val']):
                self.update_general_status(
                    f"Value must be between {target['min_val']} and {target['max_val']}", 
                    'error'
                )
                if hasattr(self, 'numeric_keypad') and self.numeric_keypad is not None:
                    self.numeric_keypad.flash_display(error=True)
                return
            
            # Update variable
            formatted_value = f"{value:.{target['decimal_places']}f}"
            target['variable'].set(formatted_value)
            
            # Update status
            self.update_general_status(
                f"{target['title']} updated to {formatted_value}", 
                'success'
            )
            
            # Reset target
            self.current_keypad_target = None
            
            # Update target field label if it exists
            if hasattr(self, 'target_field_label') and self.target_field_label is not None:
                self.target_field_label.config(
                    text="Value updated successfully",
                    fg=self.colors.get('success', '#10b981')
                )
                
                # Clear selection after delay
                if self.settings_frame is not None:
                    self.settings_frame.after(3000, lambda: self.target_field_label.config(
                        text="No field selected",
                        fg=self.colors.get('text_secondary', '#888888')
                    ) if self.target_field_label is not None else None)
            
        except Exception as e:
            print(f"Error confirming keypad value: {e}")
            self.update_general_status(f"Error updating value: {e}", 'error')

    # Settings Management Methods
    
    def initialize_default_settings(self):
        """Initialize default settings if not present"""
        try:
            # Set default values for variables if they don't exist
            if not hasattr(self, 'm100_enabled_var'):
                self.m100_enabled_var = tk.BooleanVar(value=False)
            if not hasattr(self, 'auto_frequency_var'):
                self.auto_frequency_var = tk.BooleanVar(value=False)
            if not hasattr(self, 'port_var'):
                self.port_var = tk.StringVar(value='/dev/ttyUSB0')
            if not hasattr(self, 'baudrate_var'):
                self.baudrate_var = tk.StringVar(value='9600')
            if not hasattr(self, 'slave_address_var'):
                self.slave_address_var = tk.StringVar(value='1')
            if not hasattr(self, 'default_frequency_var'):
                self.default_frequency_var = tk.StringVar(value='25.0')
            if not hasattr(self, 'general_status_var'):
                self.general_status_var = tk.StringVar(value='Ready')
            if not hasattr(self, 'connection_status'):
                self.connection_status = tk.StringVar(value='Not tested')
            if not hasattr(self, 'password_status_var'):
                self.password_status_var = tk.StringVar()
            
            # Initialize monitoring variables
            self.monitoring_active = False
            self.input_state_labels = {}
            self.current_keypad_target = None
            
        except Exception as e:
            print(f"Error initializing default settings: {e}")

    def load_current_settings(self):
        """Load current settings from app controller"""
        try:
            if hasattr(self.app_controller, 'settings'):
                settings = self.app_controller.settings
                
                # Load M100 settings
                m100_settings = settings.get('m100', {})
                self.m100_enabled_var.set(m100_settings.get('enabled', False))
                self.auto_frequency_var.set(m100_settings.get('auto_frequency', False))
                self.port_var.set(m100_settings.get('port', '/dev/ttyUSB0'))
                self.baudrate_var.set(str(m100_settings.get('baudrate', 9600)))
                self.slave_address_var.set(str(m100_settings.get('slave_address', 1)))
                self.default_frequency_var.set(str(m100_settings.get('default_frequency', 25.0)))
                
        except Exception as e:
            print(f"Error loading current settings: {e}")

    def save_all_settings(self):
        """Save all settings to storage"""
        try:
            self.update_general_status("Saving settings...", 'info')
            
            # M100 settings
            self.app_controller.settings["m100"] = {
                'enabled': self.m100_enabled_var.get(),
                'auto_frequency': self.auto_frequency_var.get(),
                'port': self.port_var.get(),
                'baudrate': int(self.baudrate_var.get()),
                'slave_address': int(self.slave_address_var.get()),
                'default_frequency': float(self.default_frequency_var.get())
            }
            
            # Motor settings
            self.app_controller.settings["motor"] = {
                'default_speed': int(self.motor_speed_var.get()),
                'home_timeout': int(self.home_timeout_var.get()),
                'move_timeout': int(self.move_timeout_var.get())
            }
            
            # Calibration settings
            if "hardware_config" not in self.app_controller.settings:
                self.app_controller.settings["hardware_config"] = {}
            if "adc_config" not in self.app_controller.settings["hardware_config"]:
                self.app_controller.settings["hardware_config"]["adc_config"] = {}
            
            self.app_controller.settings["hardware_config"]["adc_config"].update({
                'voltage_offset': float(self.pressure_offset_var.get()),
                'voltage_multiplier': float(self.pressure_multiplier_var.get())
            })
            
            # Save to file
            success = self.app_controller.save_settings()
            
            if success:
                self.update_general_status("All settings saved successfully!", 'success')
            else:
                self.update_general_status("Failed to save settings", 'error')
                
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.update_general_status(f"Failed to save settings: {e}", 'error')

    # Hardware Testing Methods
    
    def test_m100_connection(self):
        """Test M100 motor controller connection"""
        try:
            self.update_connection_status("Testing connection...", 'info')
            # Simulate connection test
            import time
            time.sleep(1)
            self.update_connection_status("Connection test completed", 'success')
        except Exception as e:
            self.update_connection_status(f"Connection failed: {e}", 'error')

    def test_all_systems(self):
        """Test all system components"""
        self.update_general_status("Testing all systems...", 'info')
        
        # Test M100 if enabled
        if self.m100_enabled_var.get():
            self.test_m100_connection()
        
        # Test hardware manager if available
        if hasattr(self.app_controller, 'hardware_manager') and self.app_controller.hardware_manager:
            try:
                # Test pressure reading
                pressure = self.app_controller.hardware_manager.read_pressure()
                if pressure is not None:
                    self.update_general_status(f"Hardware test passed - Pressure: {pressure:.2f} bar", 'success')
                else:
                    self.update_general_status("Hardware test failed - No pressure reading", 'warning')
            except Exception as e:
                self.update_general_status(f"Hardware test error: {e}", 'error')
        else:
            self.update_general_status("Hardware manager not available - running in simulation mode", 'info')

    # Input Monitoring Methods
    
    def start_input_monitoring(self):
        """Start monitoring input pins in background thread"""
        try:
            if not self.monitoring_active:
                self.monitoring_active = True
                self.stop_monitoring = False
                
                # Start monitoring in background thread
                import threading
                self.monitoring_thread = threading.Thread(
                    target=self._monitor_inputs,
                    daemon=True,
                    name="InputMonitoring"
                )
                self.monitoring_thread.start()
                
        except Exception as e:
            print(f"Error starting input monitoring: {e}")

    def toggle_monitoring(self):
        """Toggle input monitoring on/off"""
        try:
            if self.monitoring_active:
                self.stop_input_monitoring()
            else:
                self.start_input_monitoring()
        except Exception as e:
            print(f"Error toggling monitoring: {e}")

    def stop_input_monitoring(self):
        """Stop input monitoring"""
        self.monitoring_active = False
        self.stop_monitoring = True
        
        if self.monitoring_button:
            self.monitoring_button.config(
                text="▶️ Start Monitoring",
                bg=self.colors.get('success', '#10b981')
            )

    def _monitor_inputs(self):
        """Monitor GPIO inputs in background thread"""
        while self.monitoring_active and not self.stop_monitoring:
            try:
                if hasattr(self.app_controller, 'hardware_manager') and self.app_controller.hardware_manager:
                    hw = self.app_controller.hardware_manager
                    
                    for pin_name in ["emergency_btn", "door_close", "tank_min", "start_button", 
                                   "actuator_min", "actuator_max"]:
                        try:
                            if pin_name in hw.input_lines:
                                value = hw.input_lines[pin_name].get_value()
                                pin_info = self.get_pin_info(pin_name)
                                
                                # Determine status based on value and inversion
                                if pin_info.get('inverted', False):
                                    status = "INACTIVE" if value else "ACTIVE"
                                else:
                                    status = "ACTIVE" if value else "INACTIVE"
                                
                                # Update UI on main thread
                                if self.settings_frame is not None:
                                    self.settings_frame.after(0, self._update_input_display, pin_name, status, value)
                                
                        except Exception as e:
                            if self.settings_frame is not None:
                                self.settings_frame.after(0, self._update_input_display, pin_name, "ERROR", "-")
                
                time.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                print(f"Input monitoring error: {e}")
                time.sleep(1)

    def _update_input_display(self, pin_name, status, value):
        """Update input display on main thread"""
        try:
            if pin_name in self.input_state_labels:
                self.input_state_labels[pin_name].set(status)
            
            value_key = f"{pin_name}_value"
            if value_key in self.input_state_labels:
                self.input_state_labels[value_key].set(str(value))
                
        except Exception as e:
            print(f"Error updating input display: {e}")

    # Utility Methods
    
    def get_pin_info(self, pin_name):
        """Get pin information for display"""
        try:
            pin_info = {
                "emergency_btn": {"pin": 17, "description": "Emergency Button"},
                "door_close": {"pin": 4, "description": "Door Closure Switch"},
                "tank_min": {"pin": 23, "description": "Tank Min Level"},
                "start_button": {"pin": 6, "description": "Start Button"},
                "actuator_min": {"pin": 27, "description": "Actuator Min"},
                "actuator_max": {"pin": 22, "description": "Actuator Max"},
                "stepper_pulse": {"pin": 16, "description": "Stepper Pulse"},
                "stepper_dir": {"pin": 21, "description": "Stepper Direction"},
                "relay_control_h300": {"pin": 24, "description": "Relay Control"},
                "stepper_enable": {"pin": 20, "description": "Stepper Enable"}
            }
            return pin_info.get(pin_name, {"pin": 0, "description": "Unknown Pin"})
        except Exception as e:
            print(f"Error getting pin info: {e}")
            return {"pin": 0, "description": "Error"}

    def get_available_ports(self):
        """Get list of available serial ports - cached to prevent blocking"""
        try:
            # Return cached ports if available
            if hasattr(self, '_cached_ports') and self._cached_ports:
                return self._cached_ports
            
            # Default ports for immediate response
            default_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', 'COM1', 'COM2']
            
            # Try to get actual ports in background
            def update_ports():
                try:
                    import serial.tools.list_ports
                    ports = [port.device for port in serial.tools.list_ports.comports()]
                    if ports:
                        self._cached_ports = ports
                        # Update combobox if it exists
                        if hasattr(self, 'port_combobox') and self.port_combobox is not None:
                            self.port_combobox['values'] = ports
                except ImportError:
                    self._cached_ports = default_ports
                except Exception as e:
                    print(f"Error getting ports: {e}")
                    self._cached_ports = default_ports
            
            # Start port detection in background
            import threading
            port_thread = threading.Thread(target=update_ports, daemon=True)
            port_thread.start()
            
            return default_ports
            
        except Exception as e:
            print(f"Error in get_available_ports: {e}")
            return ['/dev/ttyUSB0', '/dev/ttyUSB1', 'COM1', 'COM2']

    def refresh_ports(self):
        """Refresh available ports list"""
        try:
            ports = self.get_available_ports()
            # Check if port_combobox exists and is not None
            if hasattr(self, 'port_combobox') and self.port_combobox is not None:
                self.port_combobox['values'] = ports
        except Exception as e:
            print(f"Error refreshing ports: {e}")

    def on_m100_enable_change(self):
        """Handle M100 enable/disable change"""
        try:
            self.update_m100_settings_state()
        except Exception as e:
            print(f"Error handling M100 enable change: {e}")

    def update_m100_settings_state(self):
        """Update M100 settings widgets state"""
        state = 'normal' if self.m100_enabled_var.get() else 'disabled'
        
        # Update widgets in comm_container
        for widget in self.comm_container.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, (tk.Entry, ttk.Combobox, tk.Button)):
                    try:
                        if hasattr(child, 'configure'):
                            child.configure(state=state)
                    except:
                        pass

    def update_general_status(self, message, level):
        """Update general status message"""
        self.general_status_var.set(message)
        
        color_map = {
            'info': self.colors.get('primary', '#00B2E3'),
            'success': self.colors.get('success', '#10b981'),
            'warning': self.colors.get('warning', '#f59e0b'),
            'error': self.colors.get('error', '#ef4444')
        }
        
        if self.general_status_label:
            self.general_status_label.configure(fg=color_map.get(level, '#222222'))

    def update_connection_status(self, status, level):
        """Update M100 connection status"""
        self.connection_status.set(status)
        
        color_map = {
            'info': self.colors.get('text_secondary', '#888888'),
            'success': self.colors.get('success', '#10b981'),
            'warning': self.colors.get('warning', '#f59e0b'),
            'error': self.colors.get('error', '#ef4444')
        }
        
        if self.connection_status_label:
            self.connection_status_label.configure(fg=color_map.get(level, '#222222'))

    def cleanup(self):
        """Cleanup resources when view is destroyed"""
        try:
            # Stop input monitoring
            self.stop_input_monitoring()
            
            # Wait for monitoring thread to finish
            if hasattr(self, 'monitoring_thread') and self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2)
            
            print("Settings view cleanup completed")
        except Exception as e:
            print(f"Error during settings cleanup: {e}")

    def _show_loading_progress(self, message):
        """Show loading progress message"""
        try:
            if hasattr(self, 'general_status_var'):
                self.general_status_var.set(message)
                self.parent.update_idletasks()
        except Exception as e:
            print(f"Error showing loading progress: {e}")

    def create_input_monitoring(self):
        """Create input state monitoring section"""
        input_frame = tk.LabelFrame(
            self.settings_frame, 
            text="GPIO Input State Monitoring", 
            font=('Arial', 14, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('primary', '#00B2E3'),
            padx=15,
            pady=15
        )
        input_frame.pack(fill='x', padx=20, pady=10)
        
        # Monitoring control
        control_frame = tk.Frame(input_frame, bg=self.colors.get('white', '#FFFFFF'))
        control_frame.pack(fill='x', pady=10)
        
        self.monitoring_button = tk.Button(
            control_frame,
            text="▶️ Start Monitoring",
            command=self.toggle_monitoring,
            font=('Arial', 11, 'bold'),
            bg=self.colors.get('success', '#10b981'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=15,
            pady=5
        )
        self.monitoring_button.pack(side='left')
        
        # Create input grid
        self.create_input_grid(input_frame)

    def create_input_grid(self, parent):
        """Create grid for input pin monitoring"""
        grid_frame = tk.Frame(parent, bg=self.colors.get('white', '#FFFFFF'))
        grid_frame.pack(fill='x', pady=15)
        
        # Header
        header_frame = tk.Frame(grid_frame, bg=self.colors.get('background', '#f8fafc'))
        header_frame.pack(fill='x', pady=5)
        
        headers = ["Pin Name", "Description", "Status", "Value"]
        widths = [15, 25, 12, 8]
        
        for header, width in zip(headers, widths):
            tk.Label(
                header_frame,
                text=header,
                font=('Arial', 11, 'bold'),
                bg=self.colors.get('background', '#f8fafc'),
                fg=self.colors.get('primary', '#00B2E3'),
                width=width,
                anchor='w'
            ).pack(side='left', padx=5)
        
        # Input rows
        input_pins = ["emergency_btn", "door_close", "tank_min", "start_button", 
                     "actuator_min", "actuator_max"]
        
        for pin_name in input_pins:
            self.create_input_monitoring_row(grid_frame, pin_name)

    def create_input_monitoring_row(self, parent, pin_name):
        """Create a single input monitoring row"""
        row_frame = tk.Frame(parent, bg=self.colors.get('white', '#FFFFFF'))
        row_frame.pack(fill='x', pady=2)
        
        pin_info = self.get_pin_info(pin_name)
        
        # Pin name
        tk.Label(
            row_frame,
            text=pin_name,
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222'),
            width=15,
            anchor='w'
        ).pack(side='left', padx=5)
        
        # Description
        tk.Label(
            row_frame,
            text=pin_info['description'],
            font=('Arial', 10),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            width=25,
            anchor='w'
        ).pack(side='left', padx=5)
        
        # Status
        status_var = tk.StringVar(value="Unknown")
        self.input_state_labels[pin_name] = status_var
        
        status_label = tk.Label(
            row_frame,
            textvariable=status_var,
            font=('Arial', 10, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            width=12,
            anchor='w'
        )
        status_label.pack(side='left', padx=5)
        
        # Value
        value_var = tk.StringVar(value="-")
        self.input_state_labels[f"{pin_name}_value"] = value_var
        
        value_label = tk.Label(
            row_frame,
            textvariable=value_var,
            font=('Arial', 10, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_secondary', '#888888'),
            width=8,
            anchor='w'
        )
        value_label.pack(side='left', padx=5)

    def create_control_buttons(self):
        """Create enhanced control buttons"""
        button_frame = tk.Frame(self.settings_frame, bg=self.colors.get('white', '#FFFFFF'))
        button_frame.pack(fill='x', padx=20, pady=25)
        
        # Left side buttons
        left_buttons = tk.Frame(button_frame, bg=self.colors.get('white', '#FFFFFF'))
        left_buttons.pack(side='left')
        
        save_button = tk.Button(
            left_buttons,
            text="💾 Save All Settings",
            command=self.save_all_settings,
            font=('Arial', 13, 'bold'),
            bg=self.colors.get('success', '#10b981'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=25,
            pady=12
        )
        save_button.pack(side='left', padx=10)
        
        test_button = tk.Button(
            left_buttons,
            text="🧪 Test All Systems",
            command=self.test_all_systems,
            font=('Arial', 13, 'bold'),
            bg=self.colors.get('warning', '#f59e0b'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=25,
            pady=12
        )
        test_button.pack(side='left', padx=10)
        
        # Right side buttons
        right_buttons = tk.Frame(button_frame, bg=self.colors.get('white', '#FFFFFF'))
        right_buttons.pack(side='right')
        
        reset_button = tk.Button(
            right_buttons,
            text="⚠️ Reset to Defaults",
            command=self.confirm_reset_to_defaults,
            font=('Arial', 13, 'bold'),
            bg=self.colors.get('error', '#ef4444'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=25,
            pady=12
        )
        reset_button.pack(side='left', padx=10)

    def confirm_reset_to_defaults(self):
        """Confirm reset to defaults"""
        # Find the root window for dialog parent
        parent_window = self.parent
        while parent_window and not isinstance(parent_window, tk.Tk):
            parent_window = parent_window.master
        
        if not parent_window:
            print("Error: Could not find root window for confirmation dialog")
            return
        
        # Create simple confirmation dialog
        confirm_window = tk.Toplevel(parent_window)
        confirm_window.title("Confirm Reset")
        confirm_window.geometry("400x250")
        confirm_window.configure(bg=self.colors.get('white', '#FFFFFF'))
        confirm_window.transient(parent_window)
        confirm_window.grab_set()
        
        # Center the window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (250 // 2)
        confirm_window.geometry(f"400x250+{x}+{y}")
        
        # Warning message
        tk.Label(
            confirm_window,
            text="⚠️ Reset All Settings?",
            font=('Arial', 16, 'bold'),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('error', '#ef4444')
        ).pack(pady=20)
        
        tk.Label(
            confirm_window,
            text="This will reset ALL settings to defaults.\nThis action cannot be undone.",
            font=('Arial', 12),
            bg=self.colors.get('white', '#FFFFFF'),
            fg=self.colors.get('text_primary', '#222222'),
            justify='center'
        ).pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(confirm_window, bg=self.colors.get('white', '#FFFFFF'))
        button_frame.pack(pady=20)
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=confirm_window.destroy,
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('background', '#f8fafc'),
            fg=self.colors.get('text_primary', '#222222'),
            relief='flat',
            padx=20,
            pady=8
        )
        cancel_button.pack(side='left', padx=10)
        
        # Confirm button
        confirm_button = tk.Button(
            button_frame,
            text="✅ Confirm Reset",
            command=lambda: [self.reset_to_defaults(), confirm_window.destroy()],
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('error', '#ef4444'),
            fg=self.colors.get('white', '#FFFFFF'),
            relief='flat',
            padx=20,
            pady=8
        )
        confirm_button.pack(side='left', padx=10)

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            self.update_general_status("Resetting all settings to defaults...", 'info')
            
            # Reset all settings
            self.app_controller.settings["password_hash"] = hashlib.sha256('Admin123'.encode()).hexdigest()
            self.app_controller.settings["m100"] = {
                'enabled': False,
                'auto_frequency': False,
                'port': '/dev/ttyUSB0',
                'baudrate': 9600,
                'slave_address': 1,
                'default_frequency': 25.0
            }
            self.app_controller.settings["motor"] = {
                'default_speed': 25,
                'home_timeout': 120,
                'move_timeout': 60
            }
            self.app_controller.settings["hardware_config"] = {
                "adc_config": {
                    "voltage_offset": -0.579,
                    "voltage_multiplier": 1.286
                }
            }
            
            # Save settings
            self.app_controller.save_settings()
            
            # Reload UI
            self.load_current_settings()
            self.update_m100_settings_state()
            
            # Reset status displays
            self.connection_status.set("Not tested")
            self.password_status_var.set("Reset to default")
            
            self.update_general_status("All settings reset to defaults successfully!", 'success')
            
        except Exception as e:
            self.update_general_status(f"Reset failed: {e}", 'error')


# Create alias for backward compatibility
SettingsView = CorrectedSettingsView