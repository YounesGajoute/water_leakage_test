"""
Enhanced Test Controller - Comprehensive test sequence management
"""
import time
import threading
import json
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from enum import Enum


class TestState(Enum):
    """Test state enumeration"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    HOMING = "homing"
    MOVING_TO_POSITION = "moving_to_position"
    STARTING_MOTOR = "starting_motor"
    TESTING = "testing"
    STOPPING = "stopping"
    RETURNING_HOME = "returning_home"
    COMPLETED = "completed"
    ERROR = "error"
    EMERGENCY_STOPPED = "emergency_stopped"


class TestController:
    def __init__(self, hardware_manager, motor_controller, safety_manager, 
                 status_callback: Optional[Callable] = None,
                 data_callback: Optional[Callable] = None):
        """
        Initialize enhanced test controller
        
        Args:
            hardware_manager: Hardware interface
            motor_controller: Motor control interface
            safety_manager: Safety system interface
            status_callback: Function to call for status updates
            data_callback: Function to call for data updates
        """
        self.hardware = hardware_manager
        self.motor = motor_controller
        self.safety = safety_manager
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
    
    def start_test(self, reference_data: Dict[str, Any]) -> bool:
        """
        Start the test sequence
        
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
                return True
            
            self._log_event("Test stop requested", {"reason": reason})
            self._change_state(TestState.STOPPING)
            
            # Signal stop to all threads
            self.stop_event.set()
            
            # Stop hardware immediately
            self._emergency_stop_hardware()
            
            # Wait for threads to finish
            if self.test_thread and self.test_thread.is_alive():
                self.test_thread.join(timeout=5)
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2)
            
            # Return to home position
            self._update_status("Returning to home position...", "info")
            if self.motor.move_to_home():
                self._update_status("Test stopped - System ready", "success")
            else:
                self._update_status("Test stopped - Home position failed", "warning")
            
            # Save test results
            self._finalize_test(completed=False, reason=reason)
            
            return True
            
        except Exception as e:
            self._handle_test_error(f"Error stopping test: {str(e)}")
            return False
    
    def emergency_stop(self, reason: str = "Emergency stop activated"):
        """Handle emergency stop situation"""
        try:
            self._log_event("Emergency stop", {"reason": reason})
            self._change_state(TestState.EMERGENCY_STOPPED)
            
            # Signal stop to all threads
            self.stop_event.set()
            
            # Immediate hardware stop
            self._emergency_stop_hardware()
            
            self._update_status(f"EMERGENCY STOP: {reason}", "error")
            
            # Save emergency stop event
            self._finalize_test(completed=False, reason=f"Emergency: {reason}")
            
        except Exception as e:
            print(f"Error in emergency stop: {e}")
    
    def pause_test(self) -> bool:
        """Pause the current test (if supported)"""
        try:
            if self.test_state != TestState.TESTING:
                return False
            
            # For this implementation, pause means stopping motor but staying in position
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
        
        # Reset data collections
        self.pressure_data = []
        self.test_log = []
        self.current_pressure = 0.0
        self.max_pressure_reached = 0.0
        self.min_pressure_reached = float('inf')
        
        self._log_event("Test initialized", self.test_parameters)
        self._change_state(TestState.INITIALIZING)
    
    def _run_test_sequence(self):
        """Main test sequence execution"""
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
            self._update_status(f"Moving to position {target_position}mm...", "info")
            
            if not self.motor.move_to_position(target_position, self._check_stop_condition):
                raise RuntimeError("Failed to reach target position")
            
            self._log_event("Target position reached", {"position": target_position})
            time.sleep(0.5)
            
            # Phase 3: Start motor/pump
            if self.stop_event.is_set():
                return
            
            self._change_state(TestState.STARTING_MOTOR)
            self._update_status("Starting motor...", "info")
            
            self.hardware.output_lines['relay_control_h300'].set_value(1)
            self._log_event("Motor started")
            time.sleep(1.0)  # Allow motor to start
            
            # Phase 4: Begin test monitoring
            if self.stop_event.is_set():
                return
            
            self._change_state(TestState.TESTING)
            self._update_status("Test in progress...", "info")
            self._run_test_monitoring()
            
            # Phase 5: Complete test
            if not self.stop_event.is_set():
                self._complete_test_sequence()
            
        except Exception as e:
            self._handle_test_error(str(e))
    
    def _run_test_monitoring(self):
        """Run the main test monitoring loop"""
        test_start = time.time()
        
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - test_start
                
                # Check if test duration reached
                if elapsed >= self.target_duration:
                    self._log_event("Test duration completed")
                    break
                
                # Check emergency conditions
                if self._check_emergency_conditions():
                    break
                
                # Small sleep to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in test monitoring: {e}")
                break
    
    def _monitor_test_progress(self):
        """Monitor test progress and collect data"""
        while not self.stop_event.is_set() and self.is_testing:
            try:
                # Collect pressure data
                pressure = self.hardware.read_pressure()
                if pressure is not None:
                    self.current_pressure = pressure
                    self.max_pressure_reached = max(self.max_pressure_reached, pressure)
                    if pressure < self.min_pressure_reached:
                        self.min_pressure_reached = pressure
                    
                    # Store data point
                    if self.test_start_time is not None:
                        timestamp = time.time() - self.test_start_time
                        self.pressure_data.append({
                            'timestamp': timestamp,
                            'pressure': pressure
                        })
                
                # Calculate test progress
                if self.test_start_time:
                    elapsed = time.time() - self.test_start_time
                    self.test_duration = elapsed / 60  # Convert to minutes
                
                # Update UI via callback
                if self.data_callback:
                    self.data_callback({
                        'pressure': self.current_pressure,
                        'duration': self.test_duration,
                        'target_duration': self.target_duration / 60,
                        'state': self.test_state.value
                    })
                
                time.sleep(self.data_collection_interval)
                
            except Exception as e:
                print(f"Error in progress monitoring: {e}")
                time.sleep(1)
    
    def _complete_test_sequence(self):
        """Complete the test successfully"""
        try:
            # Stop motor
            self.hardware.output_lines['relay_control_h300'].set_value(0)
            self._log_event("Motor stopped")
            time.sleep(0.5)
            
            # Return to home
            self._change_state(TestState.RETURNING_HOME)
            self._update_status("Returning to home position...", "info")
            
            if self.motor.move_to_home():
                self._update_status("Test completed successfully", "success")
                self._log_event("Returned to home position")
            else:
                self._update_status("Test completed - Home position failed", "warning")
                self._log_event("Failed to return to home position")
            
            # Finalize test
            self._finalize_test(completed=True, reason="Normal completion")
            
        except Exception as e:
            self._handle_test_error(f"Error completing test: {str(e)}")
    
    def _finalize_test(self, completed: bool, reason: str):
        """Finalize test and save results"""
        try:
            end_time = time.time()
            
            # Calculate statistics
            pressure_stats = self._calculate_pressure_statistics()
            
            # Create test results
            self.test_results = {
                'test_id': self.test_id,
                'timestamp': datetime.now().isoformat(),
                'completed': completed,
                'reason': reason,
                'duration_seconds': end_time - self.test_start_time if self.test_start_time else 0,
                'duration_minutes': self.test_duration,
                'parameters': self.test_parameters.copy(),
                'pressure_stats': pressure_stats,
                'data_points': len(self.pressure_data),
                'test_log': self.test_log.copy()
            }
            
            # Save results
            self._save_test_results()
            
            # Update state
            self._change_state(TestState.COMPLETED if completed else TestState.ERROR)
            
            self._log_event("Test finalized", {
                'completed': completed,
                'reason': reason,
                'duration': self.test_duration
            })
            
        except Exception as e:
            print(f"Error finalizing test: {e}")
    
    def _calculate_pressure_statistics(self) -> Dict[str, float]:
        """Calculate pressure statistics"""
        try:
            if not self.pressure_data:
                return {}
            
            pressures = [dp['pressure'] for dp in self.pressure_data]
            
            return {
                'min_pressure': min(pressures),
                'max_pressure': max(pressures),
                'avg_pressure': sum(pressures) / len(pressures),
                'final_pressure': pressures[-1] if pressures else 0,
                'pressure_range': max(pressures) - min(pressures),
                'data_points': len(pressures)
            }
            
        except Exception as e:
            print(f"Error calculating pressure statistics: {e}")
            return {}
    
    def _save_test_results(self):
        """Save test results to file"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}_{self.test_id}.json"
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=4)
            
            print(f"Test results saved: {filename}")
            
        except Exception as e:
            print(f"Error saving test results: {e}")
    
    def _emergency_stop_hardware(self):
        """Immediately stop all hardware"""
        try:
            # Stop motor/pump
            if hasattr(self.hardware, 'output_lines'):
                self.hardware.output_lines['relay_control_h300'].set_value(0)
                # Disable stepper motor
                self.hardware.output_lines['stepper_enable'].set_value(1)
                # Set all other outputs to safe state
                for name, line in self.hardware.output_lines.items():
                    if name not in ['stepper_enable']:
                        line.set_value(0)
            
        except Exception as e:
            print(f"Error in emergency hardware stop: {e}")
    
    def _check_stop_condition(self) -> bool:
        """Check if test should be stopped"""
        return self.stop_event.is_set() or self._check_emergency_conditions()
    
    def _check_emergency_conditions(self) -> bool:
        """Check for emergency conditions"""
        try:
            # Check emergency button
            if hasattr(self.hardware, 'input_lines'):
                if self.hardware.input_lines['emergency_btn'].get_value():
                    self.emergency_stop("Emergency button pressed")
                    return True
            
            # Check safety manager
            if self.safety.emergency_active:
                return True
            
        except Exception as e:
            print(f"Error checking emergency conditions: {e}")
        
        return False
    
    def _check_home_position(self) -> bool:
        """Check if actuator is at home position"""
        try:
            if hasattr(self.hardware, 'input_lines'):
                return self.hardware.input_lines['actuator_min'].get_value()
        except:
            pass
        return False
    
    def _validate_reference_data(self, reference_data: Dict) -> bool:
        """Validate reference data structure"""
        try:
            if not isinstance(reference_data, dict):
                return False
            
            params = reference_data.get('parameters', {})
            if not isinstance(params, dict):
                return False
            
            required_keys = ['position', 'target_pressure', 'inspection_time']
            
            for key in required_keys:
                if key not in params:
                    return False
                value = params[key]
                if not isinstance(value, (int, float)) or value <= 0:
                    return False
            
            # Validate ranges
            if not (65 < params['position'] <= 200):
                return False
            if not (0 < params['target_pressure'] <= 4.5):
                return False
            if not (0 < params['inspection_time'] <= 120):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating reference data: {e}")
            return False
    
    def _change_state(self, new_state: TestState):
        """Change test state and log the change"""
        old_state = self.test_state
        self.test_state = new_state
        self._log_event("State change", {
            'from': old_state.value,
            'to': new_state.value
        })
    
    def _log_event(self, event: str, data: Optional[Dict] = None):
        """Log an event with timestamp"""
        try:
            log_entry = {
                'timestamp': time.time(),
                'event': event,
                'test_time': time.time() - self.test_start_time if self.test_start_time else 0,
                'data': data or {}
            }
            self.test_log.append(log_entry)
            
            # Print for debugging
            print(f"[TEST LOG] {event}: {data or ''}")
            
        except Exception as e:
            print(f"Error logging event: {e}")
    
    def _handle_test_error(self, error_message: str):
        """Handle test errors"""
        self._log_event("Test error", {'error': error_message})
        print(f"Test error: {error_message}")
        
        # Stop hardware safely
        self._emergency_stop_hardware()
        
        # Update status
        self._update_status(f"Test failed: {error_message}", "error")
        
        # Save error results
        self._finalize_test(completed=False, reason=f"Error: {error_message}")
        
        # Signal stop
        self.stop_event.set()
    
    def _update_status(self, message: str, level: str = "info"):
        """Update status via callback"""
        if self.status_callback:
            try:
                self.status_callback(message, level)
            except Exception as e:
                print(f"Error in status callback: {e}")
        
        print(f"[{level.upper()}] {message}")
    
    def get_test_status(self) -> Dict[str, Any]:
        """Get comprehensive test status"""
        return {
            'test_id': self.test_id,
            'state': self.test_state.value,
            'is_testing': self.is_testing,
            'can_start': self.can_start_test,
            'current_pressure': self.current_pressure,
            'test_duration': self.test_duration,
            'target_duration': self.target_duration / 60 if self.target_duration else 0,
            'parameters': self.test_parameters.copy(),
            'pressure_stats': {
                'current': self.current_pressure,
                'max': self.max_pressure_reached,
                'min': self.min_pressure_reached if self.min_pressure_reached != float('inf') else 0
            },
            'data_points_collected': len(self.pressure_data),
            'test_log_entries': len(self.test_log)
        }
    
    def get_pressure_data(self) -> List[Dict]:
        """Get collected pressure data"""
        return self.pressure_data.copy()
    
    def get_test_log(self) -> List[Dict]:
        """Get test event log"""
        return self.test_log.copy()
    
    def get_test_results(self) -> Dict[str, Any]:
        """Get final test results"""
        return self.test_results.copy()
    
    def export_test_data(self, filepath: str) -> bool:
        """Export test data to file"""
        try:
            export_data = {
                'test_results': self.test_results,
                'pressure_data': self.pressure_data,
                'test_log': self.test_log,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=4)
            
            print(f"Test data exported to: {filepath}")
            return True
            
        except Exception as e:
            print(f"Error exporting test data: {e}")
            return False
    
    def reset_controller(self):
        """Reset controller to initial state"""
        try:
            # Stop any running test
            if self.is_testing:
                self.stop_test("Controller reset")
            
            # Wait for threads to finish
            if self.test_thread and self.test_thread.is_alive():
                self.test_thread.join(timeout=5)
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2)
            
            # Reset state
            self.test_state = TestState.IDLE
            self.stop_event.clear()
            
            # Clear data
            self.test_parameters = {}
            self.pressure_data = []
            self.test_log = []
            self.test_results = {}
            self.test_id = None
            self.test_start_time = None
            self.test_duration = 0.0
            self.current_pressure = 0.0
            self.max_pressure_reached = 0.0
            self.min_pressure_reached = float('inf')
            
            print("Test controller reset")
            return True
            
        except Exception as e:
            print(f"Error resetting controller: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get test statistics"""
        try:
            if not self.test_start_time:
                return {}
            
            elapsed = time.time() - self.test_start_time
            progress = min(100, (elapsed / self.target_duration * 100)) if self.target_duration > 0 else 0
            
            return {
                'elapsed_time': elapsed,
                'progress_percent': progress,
                'pressure_readings': len(self.pressure_data),
                'average_pressure': sum(dp['pressure'] for dp in self.pressure_data) / len(self.pressure_data) if self.pressure_data else 0,
                'data_collection_rate': len(self.pressure_data) / elapsed if elapsed > 0 else 0,
                'estimated_completion': self.test_start_time + self.target_duration if self.target_duration > 0 else None
            }
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return {}
    
    def set_data_collection_interval(self, interval: float):
        """Set data collection interval"""
        if 0.01 <= interval <= 10.0:  # Between 10ms and 10s
            self.data_collection_interval = interval
            return True
        return False
    
    def set_status_update_interval(self, interval: float):
        """Set status update interval"""
        if 0.1 <= interval <= 60.0:  # Between 100ms and 60s
            self.status_update_interval = interval
            return True
        return False