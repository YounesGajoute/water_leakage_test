"""
Simplified Calibration View - Pressure offset and fixed frequency mapping with numeric keypad
"""

import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
from ..components.numeric_keypad import NumericKeypad, get_numeric_input


class CalibrationView:
    def __init__(self, parent, app_controller, colors):
        self.parent = parent
        self.app_controller = app_controller
        self.colors = colors
        
        # Calibration state
        self.calibration_frame = None
        
        # Calibration parameters
        self.pressure_offset = tk.DoubleVar()
        
        # Fixed pressure points with editable frequencies
        self.pressure_frequency_map = [
            {'pressure': 1.0, 'frequency': 25.0},
            {'pressure': 1.5, 'frequency': 30.0},
            {'pressure': 2.0, 'frequency': 35.0},
            {'pressure': 2.5, 'frequency': 40.0},
            {'pressure': 3.0, 'frequency': 45.0},
            {'pressure': 3.5, 'frequency': 47.0},
            {'pressure': 4.0, 'frequency': 49.0},
            {'pressure': 4.5, 'frequency': 50.0}
        ]
        
        # Frequency input variables
        self.frequency_vars = {}
        for point in self.pressure_frequency_map:
            pressure = point['pressure']
            self.frequency_vars[pressure] = tk.DoubleVar(value=point['frequency'])
        
        # Load current calibration settings
        self.load_calibration_settings()

    def show(self):
        """Display the calibration view"""
        # Create calibration frame
        self.calibration_frame = tk.Frame(self.parent, bg=self.colors['white'])
        self.calibration_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create main sections
        self.create_header()
        self.create_pressure_calibration_section()
        self.create_frequency_mapping_section()
        self.create_numeric_keypad_section()
        self.create_control_buttons()

    def create_header(self):
        """Create the header section"""
        header_frame = tk.Frame(self.calibration_frame, bg=self.colors['white'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="System Calibration - Pressure Offset & Frequency Mapping",
            font=('Arial', 18, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(side='left')

    def create_pressure_calibration_section(self):
        """Create pressure sensor calibration section"""
        pressure_frame = tk.LabelFrame(
            self.calibration_frame,
            text="Pressure Sensor Calibration",
            font=('Arial', 14, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary'],
            padx=20,
            pady=15
        )
        pressure_frame.pack(fill='x', pady=(0, 15))
        
        # Current pressure display
        current_frame = tk.Frame(pressure_frame, bg=self.colors['white'])
        current_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            current_frame,
            text="Current Pressure Reading:",
            font=('Arial', 12, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['text_primary']
        ).pack(side='left')
        
        self.current_pressure_label = tk.Label(
            current_frame,
            text="0.00 bar",
            font=('Arial', 12),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        self.current_pressure_label.pack(side='right')
        
        # Pressure offset parameter
        params_frame = tk.Frame(pressure_frame, bg=self.colors['white'])
        params_frame.pack(fill='x', pady=10)
        
        # Pressure offset
        tk.Label(
            params_frame,
            text="Pressure Offset (bar):",
            font=('Arial', 11),
            bg=self.colors['white'],
            fg=self.colors['text_primary'],
            width=20,
            anchor='e'
        ).grid(row=0, column=0, padx=10, pady=5, sticky='e')
        
        # Entry
        offset_entry = tk.Entry(
            params_frame,
            textvariable=self.pressure_offset,
            font=('Arial', 11),
            width=12,
            justify='center'
        )
        offset_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Add click binding for keypad input
        offset_entry.bind('<Button-1>', lambda e: self.set_keypad_target(offset_entry, "pressure_offset"))
        offset_entry.bind('<FocusIn>', lambda e: self.set_keypad_target(offset_entry, "pressure_offset"))
        
        # Bind change event
        self.pressure_offset.trace_add('write', lambda *args: self.update_pressure_reading())
        
        # Help text
        tk.Label(
            params_frame,
            text="Offset added to pressure reading",
            font=('Arial', 9),
            bg=self.colors['white'],
            fg=self.colors['text_secondary'],
            anchor='w'
        ).grid(row=0, column=2, padx=10, pady=5, sticky='w')

    def create_frequency_mapping_section(self):
        """Create pressure-to-frequency mapping section"""
        mapping_frame = tk.LabelFrame(
            self.calibration_frame,
            text="Pressure-to-Frequency Mapping",
            font=('Arial', 14, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary'],
            padx=20,
            pady=15
        )
        mapping_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Instructions
        instruction_label = tk.Label(
            mapping_frame,
            text="Set frequency values for each pressure point:",
            font=('Arial', 12, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['text_primary']
        )
        instruction_label.pack(pady=(0, 15))
        
        # Create grid for pressure-frequency pairs
        grid_frame = tk.Frame(mapping_frame, bg=self.colors['white'])
        grid_frame.pack(fill='both', expand=True, pady=10)
        
        # Configure grid weights for centering
        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)
        for i in range(3):
            grid_frame.rowconfigure(i, weight=1)
        
        # Create input pairs in a 4x2 grid
        self.frequency_entries = {}
        row = 0
        col = 0
        
        for point in self.pressure_frequency_map:
            pressure = point['pressure']
            
            # Create frame for this pressure-frequency pair
            pair_frame = tk.Frame(
                grid_frame, 
                bg=self.colors['background'],
                relief='raised',
                bd=1,
                padx=15,
                pady=10
            )
            pair_frame.grid(row=row, column=col, padx=10, pady=5, sticky='nsew')
            
            # Pressure label (fixed)
            pressure_label = tk.Label(
                pair_frame,
                text=f"{pressure:.1f} bar",
                font=('Arial', 12, 'bold'),
                bg=self.colors['background'],
                fg=self.colors['text_primary']
            )
            pressure_label.pack(pady=(0, 5))
            
            # Frequency input
            frequency_entry = tk.Entry(
                pair_frame,
                textvariable=self.frequency_vars[pressure],
                font=('Arial', 11),
                width=8,
                justify='center'
            )
            frequency_entry.pack(pady=(0, 3))
            self.frequency_entries[pressure] = frequency_entry
            
            # Add click binding for keypad input
            frequency_entry.bind('<Button-1>', 
                lambda e, p=pressure: self.set_keypad_target(self.frequency_entries[p], f"frequency_{p}"))
            frequency_entry.bind('<FocusIn>', 
                lambda e, p=pressure: self.set_keypad_target(self.frequency_entries[p], f"frequency_{p}"))
            
            # Hz label
            hz_label = tk.Label(
                pair_frame,
                text="Hz",
                font=('Arial', 10),
                bg=self.colors['background'],
                fg=self.colors['text_secondary']
            )
            hz_label.pack()
            
            # Bind change event
            self.frequency_vars[pressure].trace_add('write', 
                lambda *args, p=pressure: self.update_frequency_mapping(p))
            
            # Move to next position
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def create_numeric_keypad_section(self):
        """Create the numeric keypad section"""
        keypad_frame = tk.LabelFrame(
            self.calibration_frame,
            text="Numeric Keypad",
            font=('Arial', 14, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary'],
            padx=20,
            pady=15
        )
        keypad_frame.pack(side='right', fill='y', padx=(20, 0))
        
        # Create keypad
        self.keypad = NumericKeypad(
            keypad_frame,
            self.colors,
            callback=self.on_keypad_value_entered,
            allow_negative=True,
            decimal_places=3
        )
        self.keypad_widget = self.keypad.create()
        
        # Current target info
        self.target_info_label = tk.Label(
            keypad_frame,
            text="Click an input field to edit",
            font=('Arial', 10),
            bg=self.colors['white'],
            fg=self.colors['text_secondary'],
            wraplength=200
        )
        self.target_info_label.pack(pady=10)

    def set_keypad_target(self, entry_widget, field_type):
        """Set the keypad target and configure for field type"""
        # Set keypad target
        self.keypad.set_target_entry(entry_widget)
        
        # Configure keypad based on field type
        if field_type == "pressure_offset":
            self.keypad.set_allow_negative(True)
            self.keypad.set_decimal_places(3)
            self.target_info_label.config(
                text="Editing: Pressure Offset\nRange: -2.0 to +2.0 bar\nPress ENT to confirm"
            )
        elif field_type.startswith("frequency_"):
            pressure = field_type.split("_")[1]
            self.keypad.set_allow_negative(False)
            self.keypad.set_decimal_places(1)
            self.target_info_label.config(
                text=f"Editing: Frequency at {pressure} bar\nRange: 20.0 to 50.0 Hz\nPress ENT to confirm"
            )
        
        # Load current value into keypad
        try:
            current_value = entry_widget.get()
            if current_value:
                self.keypad.set_value(float(current_value))
        except (ValueError, AttributeError):
            pass
        
        # Highlight the target entry
        entry_widget.configure(bg=self.colors.get('status_bg', '#e0f2f7'))
        
        # Remove highlight from other entries after delay
        if self.calibration_frame is not None:
            self.calibration_frame.after(3000, lambda: self.clear_entry_highlights())

    def set_keypad_target_for_test_pressure(self, spinbox_widget):
        """Set keypad target for test pressure spinbox"""
        # Create a temporary entry-like interface for the spinbox
        class SpinboxAdapter:
            def __init__(self, spinbox, var):
                self.spinbox = spinbox
                self.var = var
            
            def get(self):
                return str(self.var.get())
            
            def delete(self, start, end):
                pass  # Not needed for spinbox
            
            def insert(self, pos, text):
                try:
                    value = float(text)
                    self.var.set(value)
                except ValueError:
                    pass
        
        adapter = SpinboxAdapter(spinbox_widget, self.test_pressure_var)
        
        # Configure keypad
        self.keypad.set_target_entry(adapter)
        self.keypad.set_allow_negative(False)
        self.keypad.set_decimal_places(1)
        self.target_info_label.config(
            text="Editing: Test Pressure\nRange: 1.0 to 4.5 bar\nPress ENT to confirm"
        )
        
        # Load current value
        try:
            current_value = self.test_pressure_var.get()
            self.keypad.set_value(current_value)
        except (ValueError, AttributeError):
            pass
        
        # Highlight the spinbox
        spinbox_widget.configure(bg=self.colors.get('status_bg', '#e0f2f7'))
        
        # Clear highlight after delay
        if self.calibration_frame is not None:
            self.calibration_frame.after(3000, lambda: spinbox_widget.configure(bg='white'))

    def clear_entry_highlights(self):
        """Clear highlights from all entry fields"""
        try:
            if self.calibration_frame is None:
                return
                
            # Clear pressure offset highlight
            for widget in self.calibration_frame.winfo_children():
                if isinstance(widget, tk.LabelFrame):
                    for child in widget.winfo_children():
                        self.clear_widget_highlights(child)
        except Exception as e:
            print(f"Error clearing highlights: {e}")

    def clear_widget_highlights(self, widget):
        """Recursively clear highlights from widgets"""
        if widget is None:
            return
            
        if isinstance(widget, tk.Entry):
            widget.configure(bg='white')
        
        # Check children
        try:
            for child in widget.winfo_children():
                self.clear_widget_highlights(child)
        except:
            pass

    def on_keypad_value_entered(self, value):
        """Handle value entered via keypad"""
        try:
            # Validate based on current target
            target_info = self.target_info_label.cget('text')
            
            if "Pressure Offset" in target_info:
                # Validate pressure offset range
                if not (-2.0 <= value <= 2.0):
                    print("Pressure offset must be between -2.0 and +2.0 bar")
                    self.keypad.flash_display(error=True)
                    return
                
                # Update pressure reading
                self.update_pressure_reading()
                
            elif "Frequency" in target_info:
                # Validate frequency range
                if not (20.0 <= value <= 50.0):
                    print("Frequency must be between 20.0 and 50.0 Hz")
                    self.keypad.flash_display(error=True)
                    return
                
                # Update test frequency
                self.update_test_frequency()
            
            # Clear highlights
            self.clear_entry_highlights()
            
            # Reset keypad target info
            self.target_info_label.config(text="Click an input field to edit")
            
        except Exception as e:
            print(f"Error handling keypad value: {e}")

    def create_control_buttons(self):
        """Create main control buttons"""
        control_frame = tk.Frame(self.calibration_frame, bg=self.colors['white'])
        control_frame.pack(fill='x', pady=20)
        
        # Save calibration
        save_btn = tk.Button(
            control_frame,
            text="Save Calibration",
            font=('Arial', 12, 'bold'),
            bg=self.colors.get('success', '#10b981'),
            fg=self.colors['white'],
            width=15,
            height=2,
            command=self.save_calibration
        )
        save_btn.pack(side='left', padx=10)
        
        # Reset to defaults
        reset_btn = tk.Button(
            control_frame,
            text="Reset to Default",
            font=('Arial', 12),
            bg=self.colors['background'],
            fg=self.colors['text_primary'],
            width=15,
            height=2,
            command=self.reset_to_defaults
        )
        reset_btn.pack(side='right', padx=10)
        
        # Test frequency calculator
        test_frame = tk.Frame(control_frame, bg=self.colors['white'])
        test_frame.pack(expand=True)
        
        tk.Label(
            test_frame,
            text="Test Pressure:",
            font=('Arial', 11),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        ).pack(side='left', padx=5)
        
        self.test_pressure_var = tk.DoubleVar(value=2.5)
        test_pressure_spinbox = tk.Spinbox(
            test_frame,
            from_=1.0,
            to=4.5,
            increment=0.1,
            textvariable=self.test_pressure_var,
            width=8,
            font=('Arial', 11),
            command=self.update_test_frequency
        )
        test_pressure_spinbox.pack(side='left', padx=5)
        
        # Add click binding for keypad input
        test_pressure_spinbox.bind('<Button-1>', 
            lambda e: self.set_keypad_target_for_test_pressure(test_pressure_spinbox))
        test_pressure_spinbox.bind('<FocusIn>', 
            lambda e: self.set_keypad_target_for_test_pressure(test_pressure_spinbox))
        
        tk.Label(
            test_frame,
            text="bar →",
            font=('Arial', 11),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        ).pack(side='left', padx=5)
        
        self.test_frequency_label = tk.Label(
            test_frame,
            text="40.0 Hz",
            font=('Arial', 11, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        self.test_frequency_label.pack(side='left', padx=5)

    def load_calibration_settings(self):
        """Load current calibration settings from app controller"""
        try:
            # Get hardware config from settings
            hardware_config = self.app_controller.settings.get('hardware_config', {})
            adc_config = hardware_config.get('adc_config', {})
            
            # Load pressure calibration
            self.pressure_offset.set(adc_config.get('voltage_offset', -0.579))
            
            # Load frequency mapping
            mapping_config = hardware_config.get('frequency_mapping', {})
            mapping_points = mapping_config.get('mapping_points')
            if mapping_points:
                # Update frequency variables with saved values
                for point in mapping_points:
                    pressure = point['pressure']
                    if pressure in self.frequency_vars:
                        self.frequency_vars[pressure].set(point['frequency'])
            
        except Exception as e:
            print(f"Error loading calibration settings: {e}")
            # Use defaults if loading fails
            self.pressure_offset.set(-0.579)

    def update_pressure_reading(self):
        """Update pressure reading with current calibration"""
        try:
            if hasattr(self.app_controller, 'hardware_manager'):
                # Read raw pressure
                raw_pressure = self.app_controller.hardware_manager.read_pressure()
                if raw_pressure is not None:
                    # Apply calibration
                    offset = self.pressure_offset.get()
                    calibrated_pressure = raw_pressure + offset
                    
                    # Update display
                    self.current_pressure_label.config(text=f"{calibrated_pressure:.2f} bar")
                    return calibrated_pressure
                else:
                    self.current_pressure_label.config(text="Sensor Error")
                    return 0.0
            else:
                # Simulation mode
                import random
                simulated_pressure = 2.5 + random.uniform(-0.2, 0.2)
                offset = self.pressure_offset.get()
                calibrated_pressure = simulated_pressure + offset
                
                self.current_pressure_label.config(text=f"{calibrated_pressure:.2f} bar")
                return calibrated_pressure
                
        except Exception as e:
            print(f"Error updating pressure reading: {e}")
            return 0.0

    def update_frequency_mapping(self, pressure):
        """Update frequency mapping when value changes"""
        try:
            frequency = self.frequency_vars[pressure].get()
            # Update the mapping list
            for point in self.pressure_frequency_map:
                if point['pressure'] == pressure:
                    point['frequency'] = frequency
                    break
            
            # Update test frequency if needed
            self.update_test_frequency()
            
        except Exception as e:
            print(f"Error updating frequency mapping: {e}")

    def calculate_frequency_from_pressure(self, pressure):
        """Calculate frequency from pressure using mapping points"""
        # Sort mapping points by pressure
        sorted_points = sorted(self.pressure_frequency_map, key=lambda x: x['pressure'])
        
        # Handle edge cases
        if pressure <= sorted_points[0]['pressure']:
            return sorted_points[0]['frequency']
        if pressure >= sorted_points[-1]['pressure']:
            return sorted_points[-1]['frequency']
        
        # Linear interpolation between points
        for i in range(len(sorted_points) - 1):
            p1 = sorted_points[i]
            p2 = sorted_points[i + 1]
            
            if p1['pressure'] <= pressure <= p2['pressure']:
                # Linear interpolation
                ratio = (pressure - p1['pressure']) / (p2['pressure'] - p1['pressure'])
                frequency = p1['frequency'] + ratio * (p2['frequency'] - p1['frequency'])
                return max(20.0, min(50.0, frequency))  # Clamp to safe range
        
        return 25.0  # Default fallback

    def update_test_frequency(self):
        """Update test frequency display"""
        test_pressure = self.test_pressure_var.get()
        test_frequency = self.calculate_frequency_from_pressure(test_pressure)
        self.test_frequency_label.config(text=f"{test_frequency:.1f} Hz")

    def save_calibration(self):
        """Save calibration settings to app controller"""
        try:
            # Update mapping points with current frequency values
            for point in self.pressure_frequency_map:
                pressure = point['pressure']
                if pressure in self.frequency_vars:
                    point['frequency'] = self.frequency_vars[pressure].get()
            
            # Update app controller settings
            if 'hardware_config' not in self.app_controller.settings:
                self.app_controller.settings['hardware_config'] = {}
            
            hardware_config = self.app_controller.settings['hardware_config']
            
            # Update ADC config
            if 'adc_config' not in hardware_config:
                hardware_config['adc_config'] = {}
            
            hardware_config['adc_config'].update({
                'voltage_offset': self.pressure_offset.get()
            })
            
            # Update frequency mapping
            hardware_config['frequency_mapping'] = {
                'mapping_points': self.pressure_frequency_map.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to file
            success = self.app_controller.save_settings()
            
            if success:
                print("Calibration settings saved successfully!")
            else:
                print("Failed to save calibration settings")
                
        except Exception as e:
            print(f"Error saving calibration: {str(e)}")

    def reset_to_defaults(self):
        """Reset calibration to default values"""
        # Remove messagebox confirmation - just reset directly
        print("Resetting calibration to default values")
        
        # Reset pressure offset
        self.pressure_offset.set(-0.579)
        
        # Reset frequency mapping to defaults
        default_frequencies = [25.0, 30.0, 35.0, 40.0, 45.0, 47.0, 49.0, 50.0]
        
        for i, point in enumerate(self.pressure_frequency_map):
            point['frequency'] = default_frequencies[i]
            pressure = point['pressure']
            if pressure in self.frequency_vars:
                self.frequency_vars[pressure].set(default_frequencies[i])
        
        self.update_pressure_reading()
        self.update_test_frequency()

    def get_current_frequency_for_pressure(self, pressure):
        """Public method to get frequency for given pressure"""
        return self.calculate_frequency_from_pressure(pressure)

    def get_calibrated_pressure(self):
        """Public method to get current calibrated pressure"""
        return self.update_pressure_reading()