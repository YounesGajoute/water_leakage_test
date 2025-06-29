"""
Enhanced Test Controller - Comprehensive test sequence management with automatic frequency setting
"""
import time
import threading
import json
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from enum import Enum


class TestState(Enum):
    """Test state enumeration with automatic frequency setting support"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    HOMING = "homing"
    MOVING_TO_POSITION = "moving_to_position"
    SETTING_FREQUENCY = "setting_frequency"  # NEW: Automatic frequency setting phase
    STARTING_MOTOR = "starting_motor"
    TESTING = "testing"
    STOPPING = "stopping"
    RETURNING_HOME = "returning_home"
    COMPLETED = "completed"
    ERROR = "error"
    EMERGENCY_STOPPED = "emergency_stopped"


class TestController:
    def __init__(self, hardware_manager, motor_controller, safety_manager, 
                 app_controller=None,  # NEW: Added app_controller for settings access
                 status_callback: Optional[Callable] = None,
                 data_callback: Optional[Callable] = None):
        """
        Initialize enhanced test controller with automatic frequency support
        
        Args:
            hardware_manager: Hardware interface
            motor_controller: Motor control interface
            safety_manager: Safety system interface
            app_controller: Main application controller for settings access
            status_callback: Function to call for status updates
            data_callback: Function to call for data updates
        """
        self.hardware = hardware_manager
        self.motor = motor_controller
        self.safety = safety_manager
        self.app_controller = app_controller  # NEW: Store app controller reference
        self.status_callback = status_callback
        self.data_callback = data_callback
        
        # Test state management
        self.test_state = TestState.IDLE
        self.test_thread = None
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        
        # Test parameters
        self.test_parameters = {}
        self.test_start_time = None
        self.test_duration = 0.0
        self.target_duration = 0.0
        
        # NEW: Frequency control parameters
        self.calculated_frequency = None
        self.frequency_set_successfully = False
        
        # Data collection
        self.pressure_data = []
        self.test_log = []
        self.current_pressure = 0.0
        self.max_pressure_reached = 0.0
        self.min_pressure_reached = float('inf')
        
        # Test results
        self.test_results = {}
        self.test_id = None
        
        # Configuration
        self.data_collection_interval = 0.1  # 10Hz
        self.status_update_interval = 0.5    # 2Hz
        
    @property
    def is_testing(self) -> bool:
        """Check if test is currently running"""
        return self.test_state not in [TestState.IDLE, TestState.COMPLETED, 
                                     TestState.ERROR, TestState.EMERGENCY_STOPPED]
    
    @property
    def can_start_test(self) -> bool:
        """Check if test can be started"""
        return self.test_state == TestState.IDLE

    # NEW: Automatic frequency setting methods
    def is_automatic_frequency_enabled(self) -> bool:
        """Check if automatic frequency control is enabled in settings"""
        try:
            if not self.app_controller or not hasattr(self.app_controller, 'settings'):
                return False
            
            m100_settings = self.app_controller.settings.get('m100', {})
            return m100_settings.get('auto_frequency', False)
        except Exception as e:
            print(f"Error checking automatic frequency setting: {e}")
            return False

    def calculate_frequency_from_calibration(self, pressure: float) -> float:
        """
        Calculate frequency from pressure using calibration mapping with linear interpolation
        
        Args:
            pressure: Target pressure in bar
            
        Returns:
            float: Calculated frequency in Hz (clamped to 20.0-50.0 Hz range)
        """
        try:
            if not self.app_controller or not hasattr(self.app_controller, 'settings'):
                return 25.0  # Default fallback
            
            # Get calibration mapping from settings
            hardware_config = self.app_controller.settings.get('hardware_config', {})
            mapping_config = hardware_config.get('frequency_mapping', {})
            mapping_points = mapping_config.get('mapping_points', [])
            
            if not mapping_points:
                # Default mapping if none exists
                mapping_points = [
                    {'pressure': 1.0, 'frequency': 25.0},
                    {'pressure': 1.5, 'frequency': 30.0},
                    {'pressure': 2.0, 'frequency': 35.0},
                    {'pressure': 2.5, 'frequency': 40.0},
                    {'pressure': 3.0, 'frequency': 45.0},
                    {'pressure': 3.5, 'frequency': 47.0},
                    {'pressure': 4.0, 'frequency': 49.0},
                    {'pressure': 4.5, 'frequency': 50.0}
                ]
            
            # Sort mapping points by pressure
            sorted_points = sorted(mapping_points, key=lambda x: x['pressure'])
            
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
            
        except Exception as e:
            print(f"Error calculating frequency from calibration: {e}")
            return 25.0  # Default fallback

    def set_m100_frequency(self, frequency: float) -> bool:
        """
        Set M100 device frequency via hardware manager
        
        Args:
            frequency: Target frequency in Hz
            
        Returns:
            bool: True if frequency was set successfully
        """
        try:
            # Check if M100 is enabled
            if not self.app_controller:
                return False
                
            m100_settings = self.app_controller.settings.get('m100', {})
            if not m100_settings.get('enabled', False):
                self._log_event(f"M100 not enabled, cannot set frequency to {frequency} Hz")
                return False
            
            # Validate frequency range
            if not (20.0 <= frequency <= 50.0):
                self._log_event(f"Invalid frequency {frequency} Hz - must be between 20.0 and 50.0 Hz", level="error")
                return False
            
            # Set frequency via hardware manager
            if hasattr(self.hardware, 'set_m100_frequency'):
                success = self.hardware.set_m100_frequency(frequency)
                if success:
                    self._log_event(f"M100 frequency set to {frequency:.1f} Hz successfully")
                    return True
                else:
                    self._log_event(f"Failed to set M100 frequency to {frequency:.1f} Hz", level="error")
                    return False
            else:
                self._log_event("Hardware manager does not support M100 frequency setting", level="warning")
                return False
                
        except Exception as e:
            self._log_event(f"Error setting M100 frequency: {str(e)}", level="error")
            return False

    def start_test(self, reference_data: Dict[str, Any]) -> bool:
        """
        Start the test sequence with automatic frequency support
        
        Args:
            reference_data: Test parameters from reference
            
        Returns:
            bool: True if test started successfully
        """
        try:
            # Validate preconditions
            if not self.can_start_test:
                self._update_status(f"Cannot start test - current state: {self.test_state.value}", "error")
                return False
            
            # Validate reference data
            if not self._validate_reference_data(reference_data):
                self._update_status("Invalid reference data", "error")
                return False
            
            # Check safety conditions
            safety_ok, safety_msg = self.safety.check_safety_conditions()
            if not safety_ok:
                self._update_status(f"Safety check failed: {safety_msg}", "error")
                return False
            
            # Initialize test
            self._initialize_test(reference_data)
            
            # Start test sequence
            self.stop_event.clear()
            self.test_thread = threading.Thread(
                target=self._run_test_sequence,
                daemon=True,
                name="TestSequence"
            )
            self.test_thread.start()
            
            # Start monitoring
            self.monitoring_thread = threading.Thread(
                target=self._monitor_test_progress,
                daemon=True,
                name="TestMonitoring"
            )
            self.monitoring_thread.start()
            
            self._update_status("Test started", "success")
            return True
            
        except Exception as e:
            self._handle_test_error(f"Failed to start test: {str(e)}")
            return False
    
    def stop_test(self, reason: str = "User requested") -> bool:
        """
        Stop the current test
        
        Args:
            reason: Reason for stopping the test
            
        Returns:
            bool: True if test stopped successfully
        """
        try:
            if not self.is_testing:
                self._update_status("No test in progress", "warning")
                return False
            
            # Signal stop
            self.stop_event.set()
            self._log_event(f"Test stop requested: {reason}")
            
            # Change state to stopping
            self._change_state(TestState.STOPPING)
            self._update_status(f"Stopping test: {reason}", "warning")
            
            # Stop hardware safely
            self._stop_hardware_safely()
            
            # Wait for threads to finish
            if self.test_thread and self.test_thread.is_alive():
                self.test_thread.join(timeout=5.0)
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2.0)
            
            # Finalize test results
            self._finalize_test_results(status="STOPPED", reason=reason)
            
            # Return to home position
            self._return_to_home_safe()
            
            self._change_state(TestState.IDLE)
            self._update_status("Test stopped successfully", "info")
            return True
            
        except Exception as e:
            self._handle_test_error(f"Error stopping test: {str(e)}")
            return False

    def pause_test(self) -> bool:
        """Pause the current test"""
        try:
            # Stop motor operation temporarily
            self.hardware.output_lines['relay_control_h300'].set_value(0)
            self._log_event("Test paused")
            self._update_status("Test paused", "warning")
            return True
            
        except Exception as e:
            print(f"Error pausing test: {e}")
            return False
    
    def resume_test(self) -> bool:
        """Resume a paused test"""
        try:
            # Resume motor operation
            self.hardware.output_lines['relay_control_h300'].set_value(1)
            self._log_event("Test resumed")
            self._update_status("Test resumed", "info")
            return True
            
        except Exception as e:
            print(f"Error resuming test: {e}")
            return False
    
    def _initialize_test(self, reference_data: Dict[str, Any]):
        """Initialize test parameters and data structures"""
        self.test_id = f"test_{int(time.time())}"
        self.test_parameters = {
            'reference_id': reference_data.get('name', 'Unknown'),
            'position': reference_data['parameters']['position'],
            'target_pressure': reference_data['parameters']['target_pressure'],
            'inspection_time': reference_data['parameters']['inspection_time']
        }
        
        self.target_duration = self.test_parameters['inspection_time'] * 60  # Convert to seconds
        self.test_start_time = time.time()
        
        # NEW: Reset frequency control parameters
        self.calculated_frequency = None
        self.frequency_set_successfully = False
        
        # Reset data collections
        self.pressure_data = []
        self.test_log = []
        self.current_pressure = 0.0
        self.max_pressure_reached = 0.0
        self.min_pressure_reached = float('inf')
        
        self._log_event("Test initialized", self.test_parameters)
        self._change_state(TestState.INITIALIZING)

    def _run_test_sequence(self):
        """
        UPDATED: Main test sequence execution with automatic frequency setting support
        """
        try:
            # Phase 1: Move to home position
            if self.stop_event.is_set():
                return
            
            self._change_state(TestState.HOMING)
            self._update_status("Moving to home position...", "info")
            
            if not self._check_home_position():
                if not self.motor.move_to_home():
                    raise RuntimeError("Failed to reach home position")
            
            self._log_event("Home position reached")
            time.sleep(0.5)
            
            # Phase 2: Move to target position
            if self.stop_event.is_set():
                return
            
            self._change_state(TestState.MOVING_TO_POSITION)
            target_position = self.test_parameters['position']
            self._update_status(f"Moving to test position: {target_position} mm", "info")
            
            if not self.motor.move_to_position(target_position):
                raise RuntimeError(f"Failed to reach target position: {target_position} mm")
            
            self._log_event(f"Target position reached: {target_position} mm")
            time.sleep(0.5)
            
            # Phase 3: NEW - Automatic Frequency Setting (if enabled)
            if self.stop_event.is_set():
                return
            
            if self.is_automatic_frequency_enabled():
                self._change_state(TestState.SETTING_FREQUENCY)
                self._update_status("Setting automatic frequency based on pressure...", "info")
                
                # Calculate frequency from target pressure
                target_pressure = self.test_parameters['target_pressure']
                self.calculated_frequency = self.calculate_frequency_from_calibration(target_pressure)
                
                self._log_event(f"Calculated frequency for {target_pressure} bar: {self.calculated_frequency:.1f} Hz")
                self._update_status(f"Setting frequency to {self.calculated_frequency:.1f} Hz for {target_pressure} bar", "info")
                
                # Set the frequency on M100 device
                self.frequency_set_successfully = self.set_m100_frequency(self.calculated_frequency)
                
                if not self.frequency_set_successfully:
                    self._log_event("Failed to set automatic frequency, continuing with manual settings", level="warning")
                    self._update_status("Frequency setting failed, using manual settings", "warning")
                else:
                    self._log_event(f"Automatic frequency set successfully: {self.calculated_frequency:.1f} Hz")
                    self._update_status(f"Frequency set to {self.calculated_frequency:.1f} Hz", "success")
                
                time.sleep(1.0)  # Allow time for frequency setting to stabilize
            else:
                self._log_event("Automatic frequency disabled, using manual frequency settings")
            
            # Phase 4: Start motor/pump system
            if self.stop_event.is_set():
                return
            
            self._change_state(TestState.STARTING_MOTOR)
            
            if self.is_automatic_frequency_enabled() and self.frequency_set_successfully:
                self._update_status(f"Starting motor with automatic frequency: {self.calculated_frequency:.1f} Hz", "info")
            else:
                self._update_status("Starting motor with manual frequency settings", "info")
            
            # Start the motor/pump
            if not self._start_motor():
                raise RuntimeError("Failed to start motor")
            
            self._log_event("Motor started successfully")
            time.sleep(1.0)
            
            # Phase 5: Testing phase
            if self.stop_event.is_set():
                return
            
            self._change_state(TestState.TESTING)
            self._update_status(f"Testing in progress... Duration: {self.test_parameters['inspection_time']} min", "info")
            
            # Run the main testing loop
            self._run_testing_loop()
            
            # Phase 6: Stop motor and complete test
            if not self.stop_event.is_set():
                self._change_state(TestState.STOPPING)
                self._update_status("Test completed, stopping motor...", "info")
                self._stop_motor()
                
                # Phase 7: Return to home position
                self._change_state(TestState.RETURNING_HOME)
                self._update_status("Returning to home position...", "info")
                self._return_to_home()
                
                # Phase 8: Complete test
                self._change_state(TestState.COMPLETED)
                self._finalize_test_results(status="COMPLETED")
                self._update_status("Test completed successfully", "success")
            
        except Exception as e:
            self._handle_test_error(f"Test sequence error: {str(e)}")
        finally:
            # Ensure safe shutdown
            self._ensure_safe_shutdown()
    
    def _run_testing_loop(self):
        """Run the main testing loop with data collection"""
        try:
            test_start = time.time()
            
            while not self.stop_event.is_set():
                current_time = time.time()
                elapsed = current_time - test_start
                
                # Check if test duration reached
                if elapsed >= self.target_duration:
                    self._log_event(f"Test duration reached: {elapsed:.1f}s / {self.target_duration:.1f}s")
                    break
                
                # Read current pressure
                self.current_pressure = self.hardware.read_pressure()
                if self.current_pressure is not None:
                    # Update min/max tracking
                    self.max_pressure_reached = max(self.max_pressure_reached, self.current_pressure)
                    if self.min_pressure_reached == float('inf'):
                        self.min_pressure_reached = self.current_pressure
                    else:
                        self.min_pressure_reached = min(self.min_pressure_reached, self.current_pressure)
                    
                    # Store data point
                    self.pressure_data.append({
                        'timestamp': current_time,
                        'pressure': self.current_pressure,
                        'elapsed': elapsed
                    })
                    
                    # Call data callback
                    if self.data_callback:
                        self.data_callback(self.current_pressure, elapsed)
                
                # Sleep for data collection interval
                time.sleep(self.data_collection_interval)
                
        except Exception as e:
            self._log_event(f"Error in testing loop: {str(e)}", level="error")
            raise

    def _monitor_test_progress(self):
        """Monitor test progress and update status"""
        try:
            while not self.stop_event.is_set() and self.is_testing:
                if self.test_start_time:
                    elapsed = time.time() - self.test_start_time
                    remaining = max(0, self.target_duration - elapsed)
                    
                    progress = min(100, (elapsed / self.target_duration) * 100)
                    
                    status_msg = f"Testing... {progress:.1f}% complete ({remaining:.0f}s remaining)"
                    
                    if self.is_automatic_frequency_enabled() and self.calculated_frequency:
                        status_msg += f" | Freq: {self.calculated_frequency:.1f}Hz"
                    
                    self._update_status(status_msg, "info")
                
                time.sleep(self.status_update_interval)
                
        except Exception as e:
            print(f"Error in test monitoring: {e}")

    def _validate_reference_data(self, reference_data: Dict[str, Any]) -> bool:
        """Validate reference data parameters"""
        try:
            params = reference_data.get('parameters', {})
            
            # Check required parameters
            required_params = ['position', 'target_pressure', 'inspection_time']
            for param in required_params:
                if param not in params:
                    print(f"Missing required parameter: {param}")
                    return False
            
            # Validate parameter ranges
            position = params['position']
            if not (65 <= position <= 200):
                print(f"Position {position} mm out of range (65-200 mm)")
                return False
            
            pressure = params['target_pressure']
            if not (0 <= pressure <= 4.5):
                print(f"Pressure {pressure} bar out of range (0-4.5 bar)")
                return False
            
            time_minutes = params['inspection_time']
            if not (0 <= time_minutes <= 120):
                print(f"Time {time_minutes} min out of range (0-120 min)")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating reference data: {e}")
            return False

    def _check_home_position(self) -> bool:
        """Check if system is at home position"""
        try:
            if hasattr(self.motor, 'is_at_home'):
                return self.motor.is_at_home()
            return False
        except Exception as e:
            print(f"Error checking home position: {e}")
            return False

    def _start_motor(self) -> bool:
        """Start the motor/pump system"""
        try:
            # Start motor via relay control
            if 'relay_control_h300' in self.hardware.output_lines:
                self.hardware.output_lines['relay_control_h300'].set_value(1)
                return True
            return False
        except Exception as e:
            print(f"Error starting motor: {e}")
            return False

    def _stop_motor(self):
        """Stop the motor/pump system"""
        try:
            if 'relay_control_h300' in self.hardware.output_lines:
                self.hardware.output_lines['relay_control_h300'].set_value(0)
        except Exception as e:
            print(f"Error stopping motor: {e}")

    def _return_to_home(self):
        """Return system to home position"""
        try:
            self.motor.move_to_home()
        except Exception as e:
            print(f"Error returning to home: {e}")

    def _return_to_home_safe(self):
        """Safely return to home position"""
        try:
            self._stop_motor()
            time.sleep(1.0)
            self._return_to_home()
        except Exception as e:
            print(f"Error in safe return to home: {e}")

    def _stop_hardware_safely(self):
        """Stop all hardware safely"""
        try:
            self._stop_motor()
            # Add any other hardware safety stops here
        except Exception as e:
            print(f"Error stopping hardware safely: {e}")

    def _ensure_safe_shutdown(self):
        """Ensure all systems are safely shut down"""
        try:
            self._stop_hardware_safely()
            self._return_to_home_safe()
            if self.test_state not in [TestState.COMPLETED, TestState.ERROR]:
                self._change_state(TestState.IDLE)
        except Exception as e:
            print(f"Error in safe shutdown: {e}")

    def _finalize_test_results(self, status: str, reason: str = ""):
        """Finalize and save test results"""
        try:
            end_time = time.time()
            actual_duration = end_time - self.test_start_time if self.test_start_time else 0
            
            self.test_results = {
                'test_id': self.test_id,
                'status': status,
                'reason': reason,
                'parameters': self.test_parameters.copy(),
                'results': {
                    'start_time': self.test_start_time,
                    'end_time': end_time,
                    'actual_duration': actual_duration,
                    'target_duration': self.target_duration,
                    'max_pressure': self.max_pressure_reached,
                    'min_pressure': self.min_pressure_reached,
                    'final_pressure': self.current_pressure,
                    'data_points': len(self.pressure_data)
                },
                'frequency_control': {  # NEW: Frequency control information
                    'automatic_enabled': self.is_automatic_frequency_enabled(),
                    'calculated_frequency': self.calculated_frequency,
                    'frequency_set_successfully': self.frequency_set_successfully
                },
                'pressure_data': self.pressure_data,
                'test_log': self.test_log
            }
            
            # Save results to file
            self._save_test_results()
            
        except Exception as e:
            print(f"Error finalizing test results: {e}")

    def _save_test_results(self):
        """Save test results to file"""
        try:
            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"Test results saved to: {filename}")
        except Exception as e:
            print(f"Error saving test results: {e}")

    def _change_state(self, new_state: TestState):
        """Change test state and log the change"""
        old_state = self.test_state
        self.test_state = new_state
        self._log_event(f"State changed: {old_state.value} → {new_state.value}")

    def _log_event(self, message: str, data: Any = None, level: str = "info"):
        """Log an event with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'data': data
        }
        self.test_log.append(log_entry)
        print(f"[{timestamp}] [{level.upper()}] {message}")

    def _update_status(self, message: str, level: str = "info"):
        """Update status via callback"""
        if self.status_callback:
            self.status_callback(message, level)
        else:
            print(f"Status: {message}")

    def _handle_test_error(self, error_message: str):
        """Handle test errors safely"""
        try:
            self._log_event(error_message, level="error")
            self._change_state(TestState.ERROR)
            self._update_status(f"Test error: {error_message}", "error")
            self._ensure_safe_shutdown()
        except Exception as e:
            print(f"Error in error handler: {e}")

    # Public methods for getting test information
    def get_test_status(self) -> Dict[str, Any]:
        """Get current test status information"""
        return {
            'state': self.test_state.value,
            'is_testing': self.is_testing,
            'test_id': self.test_id,
            'parameters': self.test_parameters,
            'current_pressure': self.current_pressure,
            'elapsed_time': time.time() - self.test_start_time if self.test_start_time else 0,
            'target_duration': self.target_duration,
            'automatic_frequency_enabled': self.is_automatic_frequency_enabled(),
            'calculated_frequency': self.calculated_frequency,
            'frequency_set_successfully': self.frequency_set_successfully
        }

    def get_test_results(self) -> Dict[str, Any]:
        """Get final test results"""
        return self.test_results.copy() if self.test_results else {}

    def get_pressure_data(self) -> List[Dict[str, Any]]:
        """Get collected pressure data"""
        return self.pressure_data.copy()