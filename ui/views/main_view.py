"""
Main Test View - Primary interface for conducting air leakage tests
"""

import tkinter as tk
from ..components.gauges import PressureGauge, DurationGauge


class MainView:
    def __init__(self, parent, app_controller, colors):
        self.parent = parent
        self.app_controller = app_controller
        self.colors = colors
        
        # Test parameters storage
        self.test_parameters = []
        
        # Create main view frame
        self.main_frame = None

    def show(self):
        """Display the main test view"""
        # Create main frame
        self.main_frame = tk.Frame(self.parent, bg=self.colors['background'])
        self.main_frame.pack(fill='both', expand=True)
        
        # Create parameters card
        self.create_parameters_section()
        
        # Create test gauges section
        self.create_test_section()
        
        # Create status and control section
        self.create_controls_section()
        
        # Update parameters from app controller
        self.update_test_parameters()

    def create_parameters_section(self):
        """Create the test parameters display section"""
        self.params_frame = tk.Frame(self.main_frame, 
                                     bg=self.colors['white'],
                                     highlightbackground=self.colors['border'],
                                     highlightthickness=1)
        self.params_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Parameters will be updated by update_test_parameters method
        self.create_parameters_card()

    def create_parameters_card(self):
        """Create a horizontal parameters display card"""
        # Clear previous parameter content
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        # Main container with border
        main_container = tk.Frame(
            self.params_frame,
            bg=self.colors['white'],
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        main_container.pack(fill='x', padx=20, pady=10)
        
        # Content container for parameters
        content_container = tk.Frame(main_container, bg=self.colors['white'])
        content_container.pack(fill='x', padx=20, pady=10)
        
        # Get parameters from app controller or use defaults
        params = self.get_current_parameters()
        
        for param, value in params:
            param_frame = tk.Frame(content_container, bg=self.colors['white'])
            param_frame.pack(side='left', padx=20)
            
            # Parameter label
            tk.Label(
                param_frame,
                text=param,
                font=('Arial', 12),
                bg=self.colors['white'],
                fg=self.colors['text_secondary']
            ).pack(side='left', padx=(0, 5))
            
            # Value label
            tk.Label(
                param_frame,
                text=value,
                font=('Arial', 12, 'bold'),
                bg=self.colors['white'],
                fg=self.colors['text_primary']
            ).pack(side='left')

    def get_current_parameters(self):
        """Get current test parameters from app controller"""
        try:
            if hasattr(self.app_controller, 'current_reference') and self.app_controller.current_reference:
                ref_data = self.app_controller.settings['references'][self.app_controller.current_reference]
                params = ref_data.get('parameters', {})
                
                return [
                    ("Reference ID", self.app_controller.current_reference),
                    ("Target Pressure", f"{params.get('target_pressure', 0):.1f} bar"),
                    ("Position", f"{params.get('position', 0):.1f} mm"),
                    ("Inspection Time", f"{params.get('inspection_time', 0):.1f} min")
                ]
            else:
                return [
                    ("Reference ID", "None"),
                    ("Target Pressure", "0.0 bar"),
                    ("Position", "0.0 mm"),
                    ("Inspection Time", "0.0 min")
                ]
        except Exception as e:
            print(f"Error getting parameters: {e}")
            return [
                ("Reference ID", "Error"),
                ("Target Pressure", "0.0 bar"),
                ("Position", "0.0 mm"),
                ("Inspection Time", "0.0 min")
            ]

    def create_test_section(self):
        """Create the test gauges section"""
        self.test_frame = tk.Frame(self.main_frame, 
                                   bg=self.colors['white'],
                                   highlightbackground=self.colors['border'],
                                   highlightthickness=1)
        self.test_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left Gauge - Pressure (max 4.5 bar)
        pressure_container = tk.Frame(self.test_frame, bg=self.colors['white'])
        pressure_container.pack(side='left', expand=True, padx=20)
        
        self.pressure_gauge = PressureGauge(pressure_container, self.colors, max_value=4.5)
        self.pressure_canvas = self.pressure_gauge.create()
        
        # Get initial inspection time for duration gauge
        initial_duration = self.get_inspection_time()
        
        # Right Gauge - Duration (countdown)
        duration_container = tk.Frame(self.test_frame, bg=self.colors['white'])
        duration_container.pack(side='right', expand=True, padx=20)
        
        self.duration_gauge = DurationGauge(duration_container, self.colors, max_value=initial_duration)
        self.duration_canvas = self.duration_gauge.create()

    def get_inspection_time(self):
        """Get inspection time from current reference"""
        try:
            if hasattr(self.app_controller, 'current_reference') and self.app_controller.current_reference:
                ref_data = self.app_controller.settings['references'][self.app_controller.current_reference]
                return ref_data['parameters'].get('inspection_time', 120.0)
            return 120.0
        except:
            return 120.0

    def create_controls_section(self):
        """Create status and control buttons section"""
        self.controls_frame = tk.Frame(self.main_frame, 
                                       bg=self.colors['white'],
                                       highlightbackground=self.colors['border'],
                                       highlightthickness=1)
        self.controls_frame.pack(fill='x', padx=20, pady=(10, 0))
        
        # Status message
        self.status_label = tk.Label(self.controls_frame, 
                                    text="System Ready - Press Start to begin test",
                                    bg=self.colors['status_bg'],
                                    fg=self.colors['primary'],
                                    width=60, height=3)
        self.status_label.pack(side='left', padx=(30, 30))
        
        # Control buttons
        btn_frame = tk.Frame(self.controls_frame, bg=self.colors['background'])
        btn_frame.pack(side='right', padx=20)
        
        # Start button
        self.start_btn = tk.Button(btn_frame, 
                                  text="Start Test",
                                  bg=self.colors['primary'],
                                  fg=self.colors['white'],
                                  activebackground=self.colors['primary'],
                                  activeforeground=self.colors['white'],
                                  width=12, height=2,
                                  relief='flat',
                                  command=self.start_test)
        self.start_btn.pack(side='left', padx=5)
        
        # Stop button
        self.stop_btn = tk.Button(btn_frame, 
                                 text="Stop Test",
                                 bg=self.colors['error'],
                                 fg=self.colors['white'],
                                 activebackground=self.colors['error'],
                                 activeforeground=self.colors['white'],
                                 width=12, height=2,
                                 relief='flat',
                                 command=self.stop_test,
                                 state='disabled')
        self.stop_btn.pack(side='left', padx=5)

    def start_test(self):
        """Start the test sequence"""
        try:
            # Check if a reference is selected
            if not self.app_controller.current_reference:
                self.update_status("Please select a reference before starting the test", is_error=True)
                return
            
            # Delegate to app controller
            success = self.app_controller.start_test()
            
            if success:
                # Update UI state
                self.start_btn.configure(state='disabled')
                self.stop_btn.configure(state='normal')
                self.update_status("Test starting...")
            else:
                self.update_status("Failed to start test", is_error=True)
                
        except Exception as e:
            print(f"Error starting test: {e}")
            self.update_status(f"Error: {str(e)}", is_error=True)

    def stop_test(self):
        """Stop the test sequence"""
        try:
            # Delegate to app controller
            success = self.app_controller.stop_test()
            
            if success:
                # Update UI state
                self.start_btn.configure(state='normal')
                self.stop_btn.configure(state='disabled')
                self.update_status("Test stopped")
            else:
                self.update_status("Failed to stop test", is_error=True)
                
        except Exception as e:
            print(f"Error stopping test: {e}")
            self.update_status(f"Error: {str(e)}", is_error=True)

    def update_status(self, message, is_error=False):
        """Update status message"""
        if hasattr(self, 'status_label'):
            color = self.colors['error'] if is_error else self.colors['primary']
            self.status_label.configure(text=message, fg=color)

    def update_pressure_display(self, pressure):
        """Update pressure gauge with new value"""
        try:
            if hasattr(self, 'pressure_gauge'):
                formatted_pressure = min(float(f"{pressure:.2f}"), 4.5)
                self.pressure_gauge.update_value(formatted_pressure)
        except Exception as e:
            print(f"Error updating pressure display: {e}")

    def update_duration_display(self, duration, max_val=None):
        """Update duration gauge with countdown"""
        try:
            if hasattr(self, 'duration_gauge'):
                # Format duration to 1 decimal place
                formatted_duration = float(f"{duration:.1f}")
                
                # Update gauge with optional max value
                if max_val:
                    self.duration_gauge.max_value = max_val
                self.duration_gauge.update_value(formatted_duration)
        except Exception as e:
            print(f"Error updating duration display: {e}")

    def update_test_parameters(self):
        """Update test parameters display"""
        if hasattr(self, 'params_frame'):
            self.create_parameters_card()

    def reset_ui_state(self):
        """Reset UI to initial state"""
        if hasattr(self, 'start_btn'):
            self.start_btn.configure(state='normal')
        if hasattr(self, 'stop_btn'):
            self.stop_btn.configure(state='disabled')
        self.update_status("System Ready - Press Start to begin test")

    def set_test_running_state(self, is_running):
        """Set UI state based on test running status"""
        if hasattr(self, 'start_btn') and hasattr(self, 'stop_btn'):
            if is_running:
                self.start_btn.configure(state='disabled')
                self.stop_btn.configure(state='normal')
            else:
                self.start_btn.configure(state='normal')
                self.stop_btn.configure(state='disabled')