# -*- coding: utf-8 -*-
"""
Fixed Settings Manager - Non-blocking I/O operations
Solves UI freezing during settings save/load operations
"""

import os
import json
import shutil
import hashlib
import threading
import queue
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import time


class AsyncSettingsManager:
    """Settings manager with async I/O to prevent UI freezing"""
    
    DEFAULT_SETTINGS = {
        'references': {},
        'last_reference': None,
        'password_hash': hashlib.sha256('Admin123'.encode()).hexdigest(),
        'hardware_config': {
            'gpio_pins': {
                "emergency_btn": {"pin": 17, "inverted": True, "description": "Emergency Button"},
                "door_close": {"pin": 4, "inverted": False, "description": "Door Closure Switch"},
                "tank_min": {"pin": 23, "inverted": False, "description": "Tank Min Level"},
                "start_button": {"pin": 6, "inverted": False, "description": "Start Button"},
                "actuator_min": {"pin": 27, "inverted": False, "description": "Actuator Min"},
                "actuator_max": {"pin": 22, "inverted": False, "description": "Actuator Max"},
                "stepper_pulse": {"pin": 16, "inverted": False, "description": "Stepper Pulse"},
                "stepper_dir": {"pin": 21, "inverted": False, "description": "Stepper Direction"},
                "relay_control_h300": {"pin": 24, "inverted": False, "description": "Relay Control"},
                "stepper_enable": {"pin": 20, "inverted": False, "description": "Stepper Enable"}
            },
            'adc_config': {
                'address': 0x48,
                'busnum': 1,
                'channel': 0,
                'gain': 1,
                'voltage_multiplier': 1.286,
                'voltage_offset': -0.579
            },
            'motor_config': {
                'steps_per_mm': 380.95,
                'max_frequency': 50.0,
                'default_frequency': 25.0,
                'home_timeout': 120,
                'move_timeout': 60
            }
        },
        'ui_config': {
            'colors': {
                'primary': '#00B2E3',
                'background': '#f8fafc',
                'white': '#ffffff',
                'text_primary': '#1e293b',
                'text_secondary': '#64748b',
                'error': '#ef4444',
                'border': '#e2e8f0',
                'status_bg': '#e0f2f7',
                'button_hover': '#0891b2',
                'success': '#10b981',
                'warning': '#f59e0b'
            },
            'fonts': {
                'default': ('Arial', 12),
                'header': ('Arial', 18, 'bold'),
                'button': ('Arial', 12, 'bold'),
                'gauge': ('Arial', 18, 'bold'),
                'small': ('Arial', 10)
            }
        },
        'validation_ranges': {
            'position': {'min': 65, 'max': 200, 'unit': 'mm'},
            'pressure': {'min': 0, 'max': 4.5, 'unit': 'bar'},
            'time': {'min': 0, 'max': 120, 'unit': 'min'}
        }
    }
    
    def __init__(self, settings_file: str = 'settings.json'):
        """Initialize async settings manager"""
        self.settings_file = settings_file
        self.settings = {}
        self._settings_lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="SettingsIO")
        self._pending_operations = {}
        self._operation_counter = 0
        
        # Load settings synchronously on init (only once)
        self._load_settings_sync()
    
    def _load_settings_sync(self) -> bool:
        """Load settings synchronously (only called on initialization)"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    
                # Merge with defaults to ensure all required keys exist
                with self._settings_lock:
                    self.settings = self._merge_settings(self.DEFAULT_SETTINGS.copy(), loaded_settings)
                print(f"Settings loaded successfully from {self.settings_file}")
                return True
            else:
                # Create default settings
                with self._settings_lock:
                    self.settings = self.DEFAULT_SETTINGS.copy()
                # Save asynchronously
                self.save_settings_async()
                print(f"Created new settings file at {self.settings_file}")
                return True
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            with self._settings_lock:
                self.settings = self.DEFAULT_SETTINGS.copy()
            return False
    
    def save_settings_async(self, callback: Optional[Callable[[bool, str], None]] = None) -> str:
        """
        Save settings asynchronously to prevent UI freezing
        
        Args:
            callback: Optional callback function (success: bool, message: str) -> None
            
        Returns:
            operation_id: String identifier for tracking this operation
        """
        operation_id = f"save_{self._operation_counter}"
        self._operation_counter += 1
        
        # Create a snapshot of current settings
        with self._settings_lock:
            settings_snapshot = json.loads(json.dumps(self.settings))  # Deep copy
        
        def _save_worker():
            """Worker function for async save operation"""
            try:
                # Create backup if file exists (non-blocking for UI)
                if os.path.exists(self.settings_file):
                    backup_file = f"{self.settings_file}.backup_{int(time.time())}"
                    shutil.copy2(self.settings_file, backup_file)
                    
                    # Cleanup old backups
                    self._cleanup_old_backups()
                
                # Write settings to temporary file first
                temp_file = f"{self.settings_file}.tmp"
                with open(temp_file, 'w') as f:
                    json.dump(settings_snapshot, f, indent=4)
                
                # Atomic rename (fast operation)
                if os.path.exists(temp_file):
                    if os.path.exists(self.settings_file):
                        os.remove(self.settings_file)
                    os.rename(temp_file, self.settings_file)
                
                # Set permissions
                os.chmod(self.settings_file, 0o666)
                
                success_msg = f"Settings saved successfully to {self.settings_file}"
                print(success_msg)
                
                if callback:
                    callback(True, success_msg)
                
                return True, success_msg
                
            except Exception as e:
                error_msg = f"Error saving settings: {e}"
                print(error_msg)
                
                # Cleanup temp file if it exists
                temp_file = f"{self.settings_file}.tmp"
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                if callback:
                    callback(False, error_msg)
                
                return False, error_msg
        
        # Submit to thread pool
        future = self._executor.submit(_save_worker)
        self._pending_operations[operation_id] = future
        
        return operation_id
    
    def _cleanup_old_backups(self):
        """Clean up old backup files (keep only 5 most recent)"""
        try:
            import glob
            backup_pattern = f"{self.settings_file}.backup_*"
            backup_files = glob.glob(backup_pattern)
            
            if len(backup_files) > 5:
                # Sort by modification time
                backup_files.sort(key=os.path.getmtime)
                # Remove oldest files
                for old_backup in backup_files[:-5]:
                    try:
                        os.remove(old_backup)
                    except:
                        pass  # Ignore errors during cleanup
                        
        except Exception as e:
            print(f"Error during backup cleanup: {e}")
    
    def add_reference_async(self, ref_id: str, ref_data: Dict[str, Any], 
                           callback: Optional[Callable[[bool, str], None]] = None) -> str:
        """
        Add reference asynchronously
        
        Args:
            ref_id: Reference identifier
            ref_data: Reference data
            callback: Optional callback function
            
        Returns:
            operation_id: String identifier for tracking this operation
        """
        def _add_worker():
            try:
                with self._settings_lock:
                    if 'references' not in self.settings:
                        self.settings['references'] = {}
                    
                    self.settings['references'][ref_id] = ref_data
                    self.settings['last_reference'] = ref_id
                
                # Save settings asynchronously
                save_op_id = self.save_settings_async()
                
                # Wait for save to complete (with timeout)
                save_future = self._pending_operations.get(save_op_id)
                if save_future:
                    try:
                        success, msg = save_future.result(timeout=10)  # 10 second timeout
                        if callback:
                            callback(success, f"Reference '{ref_id}' {'added' if success else 'failed'}: {msg}")
                        return success, msg
                    except Exception as e:
                        error_msg = f"Save timeout or error: {e}"
                        if callback:
                            callback(False, error_msg)
                        return False, error_msg
                else:
                    success_msg = f"Reference '{ref_id}' added successfully"
                    if callback:
                        callback(True, success_msg)
                    return True, success_msg
                    
            except Exception as e:
                error_msg = f"Error adding reference: {e}"
                print(error_msg)
                if callback:
                    callback(False, error_msg)
                return False, error_msg
        
        operation_id = f"add_ref_{self._operation_counter}"
        self._operation_counter += 1
        
        future = self._executor.submit(_add_worker)
        self._pending_operations[operation_id] = future
        
        return operation_id
    
    def delete_reference_async(self, ref_id: str, 
                              callback: Optional[Callable[[bool, str], None]] = None) -> str:
        """Delete reference asynchronously"""
        def _delete_worker():
            try:
                with self._settings_lock:
                    if ref_id in self.settings.get('references', {}):
                        del self.settings['references'][ref_id]
                        
                        # Reset last reference if it was deleted
                        if self.settings.get('last_reference') == ref_id:
                            remaining_refs = list(self.settings['references'].keys())
                            self.settings['last_reference'] = remaining_refs[0] if remaining_refs else None
                        
                        # Save settings asynchronously
                        save_op_id = self.save_settings_async()
                        
                        success_msg = f"Reference '{ref_id}' deleted successfully"
                        if callback:
                            callback(True, success_msg)
                        return True, success_msg
                    else:
                        error_msg = f"Reference '{ref_id}' not found"
                        if callback:
                            callback(False, error_msg)
                        return False, error_msg
                        
            except Exception as e:
                error_msg = f"Error deleting reference: {e}"
                print(error_msg)
                if callback:
                    callback(False, error_msg)
                return False, error_msg
        
        operation_id = f"del_ref_{self._operation_counter}"
        self._operation_counter += 1
        
        future = self._executor.submit(_delete_worker)
        self._pending_operations[operation_id] = future
        
        return operation_id
    
    def get_operation_status(self, operation_id: str) -> Optional[str]:
        """
        Get status of an async operation
        
        Returns:
            'pending', 'completed', 'failed', or None if operation not found
        """
        if operation_id not in self._pending_operations:
            return None
        
        future = self._pending_operations[operation_id]
        
        if future.done():
            try:
                future.result()  # This will raise exception if failed
                return 'completed'
            except:
                return 'failed'
        else:
            return 'pending'
    
    def wait_for_operation(self, operation_id: str, timeout: float = 5.0) -> tuple[bool, str]:
        """
        Wait for an async operation to complete
        
        Args:
            operation_id: Operation identifier
            timeout: Timeout in seconds
            
        Returns:
            (success, message)
        """
        if operation_id not in self._pending_operations:
            return False, "Operation not found"
        
        future = self._pending_operations[operation_id]
        
        try:
            success, message = future.result(timeout=timeout)
            # Clean up completed operation
            del self._pending_operations[operation_id]
            return success, message
        except Exception as e:
            return False, f"Operation failed or timed out: {e}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value (thread-safe)"""
        keys = key.split('.')
        
        with self._settings_lock:
            value = self.settings
            
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                return default
    
    def set(self, key: str, value: Any) -> None:
        """Set setting value (thread-safe)"""
        keys = key.split('.')
        
        with self._settings_lock:
            setting = self.settings
            
            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k not in setting:
                    setting[k] = {}
                setting = setting[k]
            
            # Set the value
            setting[keys[-1]] = value
    
    def get_references(self) -> Dict[str, Any]:
        """Get all references (thread-safe)"""
        with self._settings_lock:
            return self.settings.get('references', {}).copy()
    
    def get_current_reference(self) -> Optional[str]:
        """Get current reference ID (thread-safe)"""
        with self._settings_lock:
            return self.settings.get('last_reference')
    
    def _merge_settings(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded settings with defaults"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_settings(default[key], value)
            else:
                default[key] = value
        return default
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Wait for pending operations to complete
            for operation_id, future in self._pending_operations.items():
                try:
                    future.result(timeout=2)  # Short timeout
                except:
                    future.cancel()  # Cancel if not completed
            
            self._pending_operations.clear()
            self._executor.shutdown(wait=False)
            print("Settings manager cleanup completed")
            
        except Exception as e:
            print(f"Error during settings manager cleanup: {e}")


# Compatibility wrapper for existing code
class SettingsManager(AsyncSettingsManager):
    """Backward compatible settings manager"""
    
    def save_settings(self) -> bool:
        """Synchronous save method for backward compatibility"""
        operation_id = self.save_settings_async()
        success, _ = self.wait_for_operation(operation_id, timeout=10)
        return success
    
    def add_reference(self, ref_id: str, ref_data: Dict[str, Any]) -> bool:
        """Synchronous add reference for backward compatibility"""
        operation_id = self.add_reference_async(ref_id, ref_data)
        success, _ = self.wait_for_operation(operation_id, timeout=10)
        return success
    
    def delete_reference(self, ref_id: str) -> bool:
        """Synchronous delete reference for backward compatibility"""
        operation_id = self.delete_reference_async(ref_id)
        success, _ = self.wait_for_operation(operation_id, timeout=10)
        return success