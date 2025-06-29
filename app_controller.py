"""
Complete Fixed App Controller - Resolves all PyRight errors
Integrates operations to prevent UI freezing
"""

import threading
import time
from typing import Optional, Callable, Dict, Any
from config.settings import SettingsManager


class AppController:
    """App controller with operations to prevent UI freezing"""
    
    def __init__(self, settings_file='settings.json'):
        # Initialize settings manager
        self.settings_manager = SettingsManager(settings_file)
        self.settings = self.settings_manager.settings
        
        # Reference management
        self.current_reference = self.settings_manager.get_current_reference()
        
        # UI reference
        self.main_window = None
        
        # Hardware components (initialize as None for simulation mode)
        self.hardware_manager = None
        self.motor_controller = None
        self.sensor_manager = None
        self.safety_manager = None
        self.test_controller = None
        self.data_manager = None
        
        # Application state
        self.is_testing = False
        self.system_ready = False
        
        # Status callback for UI updates
        self.status_callback: Optional[Callable[[str, str], None]] = None
        
        print("Application controller initialized")

    def initialize_hardware(self) -> bool:
        """Initialize hardware components (only on actual hardware)"""
        try:
            # Try to import hardware modules
            try:
                from hardware.hardware_manager import HardwareManager
                from hardware.motor_controller import MotorController
                from hardware.sensor_manager import SensorManager
                from core.safety_manager import SafetyManager
                from core.test_controller import TestController
                from core.data_manager import DataManager
                
                # Initialize hardware manager
                self.hardware_manager = HardwareManager()
                
                if self.hardware_manager.init_gpio() and self.hardware_manager.init_adc():
                    self.motor_controller = MotorController(self.hardware_manager)
                    self.sensor_manager = SensorManager(self.hardware_manager)
                    self.safety_manager = SafetyManager(self.hardware_manager, self.handle_emergency)
                    self.test_controller = TestController(
                        self.hardware_manager,
                        self.motor_controller,
                        self.safety_manager,
                        self.update_status
                    )
                    
                    # Start sensor monitoring
                    self.sensor_manager.start_monitoring()
                    
                    self.system_ready = True
                    print("Hardware initialized successfully")
                    return True
                else:
                    print("Hardware initialization failed")
                    return False
                    
            except ImportError as ie:
                print(f"Hardware modules not available: {ie}")
                print("Running in simulation mode")
                return False
                
        except Exception as e:
            print(f"Hardware initialization error: {e}")
            print("Running in simulation mode")
            return False

    def set_status_callback(self, callback: Callable[[str, str], None]):
        """Set callback for status updates"""
        self.status_callback = callback

    def update_status(self, message: str, level: str = "info"):
        """Update status via callback"""
        if self.status_callback:
            try:
                is_error = level in ["error", "warning"]
                self.status_callback(message, level)
            except Exception as e:
                print(f"Error in status callback: {e}")
        print(f"[{level.upper()}] {message}")

    def handle_emergency(self, reason: str):
        """Handle emergency situations"""
        print(f"EMERGENCY: {reason}")
        if self.is_testing:
            self.stop_test()
        self.update_status(f"EMERGENCY: {reason}", "error")

    def start_test(self) -> bool:
        """Start a test sequence"""
        try:
            if not self.current_reference:
                self.update_status("No reference selected", "error")
                return False
            
            if self.is_testing:
                self.update_status("Test already in progress", "warning")
                return False
            
            # Get reference data
            ref_data = self.settings['references'].get(self.current_reference)
            if not ref_data:
                self.update_status("Invalid reference data", "error")
                return False
            
            # Start test
            if self.system_ready and self.test_controller:
                success = self.test_controller.start_test(ref_data)
                if success:
                    self.is_testing = True
                    self.update_status("Test started", "info")
                    return True
                else:
                    self.update_status("Failed to start test", "error")
                    return False
            else:
                # Simulation mode
                self.is_testing = True
                self.update_status("Test started (simulation mode)", "info")
                self._simulate_test(ref_data)
                return True
                
        except Exception as e:
            self.update_status(f"Error starting test: {e}", "error")
            return False

    def stop_test(self) -> bool:
        """Stop current test"""
        try:
            if not self.is_testing:
                self.update_status("No test in progress", "warning")
                return False
            
            if self.system_ready and self.test_controller:
                success = self.test_controller.stop_test()
                if success:
                    self.is_testing = False
                    self.update_status("Test stopped", "info")
                    return True
                else:
                    self.update_status("Error stopping test", "error")
                    return False
            else:
                # Simulation mode
                self.is_testing = False
                self.update_status("Test stopped (simulation mode)", "info")
                return True
                
        except Exception as e:
            self.update_status(f"Error stopping test: {e}", "error")
            return False

    def _simulate_test(self, ref_data: Dict[str, Any]):
        """Simulate test for development/testing"""
        def simulate():
            try:
                inspection_time = ref_data['parameters']['inspection_time'] * 60  # Convert to seconds
                start_time = time.time()
                
                while self.is_testing and (time.time() - start_time) < inspection_time:
                    elapsed = time.time() - start_time
                    # Simulate pressure and duration updates here if needed
                    time.sleep(1)
                
                if self.is_testing:
                    self.is_testing = False
                    self.update_status("Test completed (simulation)", "success")
                    
            except Exception as e:
                print(f"Simulation error: {e}")
                self.is_testing = False

        sim_thread = threading.Thread(target=simulate, daemon=True)
        sim_thread.start()

    def save_settings(self) -> bool:
        """Save settings synchronously"""
        return self.settings_manager.save_settings()

    def add_reference(self, ref_id: str, ref_data: Dict[str, Any]) -> bool:
        """Add reference synchronously"""
        return self.settings_manager.add_reference(ref_id, ref_data)

    def delete_reference(self, ref_id: str) -> bool:
        """Delete reference synchronously"""
        return self.settings_manager.delete_reference(ref_id)

    def set_current_reference(self, ref_id: str) -> bool:
        """Set current reference"""
        if ref_id in self.settings.get('references', {}):
            self.current_reference = ref_id
            self.settings['last_reference'] = ref_id
            
            # Save settings
            self.save_settings()
            return True
        return False

    def get_references(self) -> Dict[str, Any]:
        """Get all references"""
        return self.settings_manager.get_references()

    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update application settings"""
        try:
            for key, value in new_settings.items():
                self.settings_manager.set(key, value)
            
            # Save settings
            self.save_settings()
            return True
            
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False

    def on_closing(self):
        """Clean up when application is closing"""
        try:
            print("Cleaning up application...")
            
            # Stop any running test
            if self.is_testing:
                self.stop_test()
            
            # Stop sensor monitoring
            if self.sensor_manager:
                self.sensor_manager.stop_monitoring()
            
            # Stop safety monitoring
            if self.safety_manager:
                self.safety_manager.stop_monitoring()
            
            # Cleanup hardware
            if self.hardware_manager:
                self.hardware_manager.cleanup()
            
            print("Application cleanup completed")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'system_ready': self.system_ready,
            'is_testing': self.is_testing,
            'current_reference': self.current_reference,
            'hardware_available': self.hardware_manager is not None
        }

    def force_cursor_visible(self):
        """Force cursor to be visible"""
        try:
            if self.main_window and hasattr(self.main_window, 'force_cursor_visible'):
                self.main_window.force_cursor_visible()
            elif self.main_window and hasattr(self.main_window, 'show_cursor'):
                self.main_window.show_cursor()
        except Exception as e:
            print(f"Error forcing cursor visibility: {e}")

    def hide_cursor(self):
        """Hide cursor"""
        try:
            if self.main_window and hasattr(self.main_window, 'hide_cursor'):
                self.main_window.hide_cursor()
        except Exception as e:
            print(f"Error hiding cursor: {e}")

    def toggle_cursor_visibility(self):
        """Toggle cursor visibility"""
        try:
            if self.main_window and hasattr(self.main_window, 'toggle_cursor_visibility'):
                self.main_window.toggle_cursor_visibility()
        except Exception as e:
            print(f"Error toggling cursor visibility: {e}")