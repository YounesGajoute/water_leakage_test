# -*- coding: utf-8 -*-
"""
Complete Settings Configuration Manager
Includes frequency mapping, M100 settings, and all required configurations
"""

import json
import os
import threading
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor


class SettingsManager:
    """Async settings manager with complete default configuration"""
    
    # Complete DEFAULT_SETTINGS with all required configurations
    DEFAULT_SETTINGS = {
        # UI Enhancements
        'ui_enhancements': {
            'enable_global_escape': True,
            'enable_function_keys': True,
            'hotkeys': {
                'emergency_stop': 'Ctrl+E',
                'quick_exit': 'Ctrl+Q',
                'quick_start': 'Ctrl+S',
                'quick_reference': 'Ctrl+R'
            }
        },
        
        # UI Settings
        'ui': {
            'theme': 'default',
            'fullscreen': True,
            'auto_save': True,
            'colors': {
                'primary': '#00B2E3',
                'background': '#f8fafc',
                'white': '#ffffff',
                'text_primary': '#222222',
                'text_secondary': '#64748b',
                'error': '#ef4444',
                'border': '#e2e8f0',
                'status_bg': '#e0f2f7',
                'button_hover': '#0891b2',
                'success': '#10b981',
                'warning': '#f59e0b'
            },
            'fonts': {
                'default': ['Arial', 12],
                'header': ['Arial', 18, 'bold'],
                'button': ['Arial', 12, 'bold'],
                'gauge': ['Arial', 18, 'bold'],
                'small': ['Arial', 10]
            }
        },
        
        # Validation Ranges
        'validation_ranges': {
            'position': {'min': 65, 'max': 200, 'unit': 'mm'},
            'pressure': {'min': 0, 'max': 4.5, 'unit': 'bar'},
            'time': {'min': 0, 'max': 120, 'unit': 'min'}
        },
        
        # M100 Motor Controller Settings
        'm100': {
            'enabled': False,
            'auto_frequency': False,  # Enable/disable automatic frequency control
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
            'slave_address': 1,
            'default_frequency': 25.0
        },
        
        # Motor Control Settings
        'motor': {
            'default_speed': 25,
            'home_timeout': 120,
            'move_timeout': 60
        },
        
        # Hardware Configuration with Frequency Mapping
        'hardware_config': {
            'adc_config': {
                'voltage_offset': -0.579,
                'voltage_multiplier': 1.286
            },
            # GPIO Pin Configuration
            'gpio_pins': {
                'emergency_stop': 23,
                'door_sensor': 25,
                'actuator_min': 27,
                'actuator_max': 22,
                'stepper_pulse': 16,
                'stepper_dir': 21,
                'relay_control_h300': 24,
                'stepper_enable': 20
            },
            # Motor Configuration
            'motor_config': {
                'steps_per_rev': 200,
                'max_speed': 1000,
                'acceleration': 500,
                'min_pulse_width': 0.001
            },
            # Frequency Mapping for Automatic Frequency Control
            'frequency_mapping': {
                'mapping_points': [
                    {'pressure': 1.0, 'frequency': 25.0},
                    {'pressure': 1.5, 'frequency': 30.0},
                    {'pressure': 2.0, 'frequency': 35.0},
                    {'pressure': 2.5, 'frequency': 40.0},
                    {'pressure': 3.0, 'frequency': 45.0},
                    {'pressure': 3.5, 'frequency': 47.0},
                    {'pressure': 4.0, 'frequency': 49.0},
                    {'pressure': 4.5, 'frequency': 50.0}
                ],
                'timestamp': '2024-01-01T00:00:00.000000'
            }
        },
        
        # Safety Settings
        'safety': {
            'pressure_limits': {
                'max_pressure': 5.0,  # bar
                'min_pressure': -0.5,  # bar
                'emergency_threshold': 4.8  # bar
            },
            'timeout_settings': {
                'emergency_timeout': 5.0,  # seconds
                'safety_check_interval': 0.1,  # seconds
                'watchdog_timeout': 10.0  # seconds
            }
        },
        
        # Password Security
        'password_hash': None,  # Will be set during initialization
        
        # Reference Management
        'references': {},
        'last_reference': None,
        
        # Logging Configuration
        'logging': {
            'level': 'INFO',
            'max_file_size': 10485760,  # 10MB
            'backup_count': 5,
            'log_to_console': True,
            'log_to_file': True
        },
        
        # Data Management
        'data': {
            'auto_export': True,
            'export_format': 'json',
            'backup_interval': 3600,  # seconds
            'max_data_points': 10000
        }
    }
    
    def __init__(self, settings_file: str = 'settings.json'):
        """Initialize settings manager with complete configuration"""
        self.settings_file = settings_file
        self.settings = {}
        self._settings_lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="SettingsIO")
        self._pending_operations = {}
        self._operation_counter = 0
        
        # Load settings synchronously on init (only once)
        self._load_settings_sync()
        
        # Ensure all required configurations exist
        self._ensure_complete_configuration()
    
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

    def _ensure_complete_configuration(self):
        """Ensure all required configurations exist"""
        try:
            # Ensure password hash is set
            if not self.settings.get('password_hash'):
                self.settings['password_hash'] = hashlib.sha256('Admin123'.encode()).hexdigest()
            
            # Ensure frequency mapping exists with current timestamp
            if 'hardware_config' not in self.settings:
                self.settings['hardware_config'] = self.DEFAULT_SETTINGS['hardware_config'].copy()
            
            if 'frequency_mapping' not in self.settings['hardware_config']:
                self.settings['hardware_config']['frequency_mapping'] = {
                    'mapping_points': [
                        {'pressure': 1.0, 'frequency': 25.0},
                        {'pressure': 1.5, 'frequency': 30.0},
                        {'pressure': 2.0, 'frequency': 35.0},
                        {'pressure': 2.5, 'frequency': 40.0},
                        {'pressure': 3.0, 'frequency': 45.0},
                        {'pressure': 3.5, 'frequency': 47.0},
                        {'pressure': 4.0, 'frequency': 49.0},
                        {'pressure': 4.5, 'frequency': 50.0}
                    ],
                    'timestamp': datetime.now().isoformat()
                }
                print("Default frequency mapping added to settings")
            
            # Ensure M100 settings exist
            if 'm100' not in self.settings:
                self.settings['m100'] = self.DEFAULT_SETTINGS['m100'].copy()
                print("Default M100 settings added")
            
            # Ensure all M100 required keys exist
            m100_defaults = self.DEFAULT_SETTINGS['m100']
            for key, default_value in m100_defaults.items():
                if key not in self.settings['m100']:
                    self.settings['m100'][key] = default_value
                    print(f"Added missing M100 setting: {key} = {default_value}")
            
            # Ensure motor settings exist
            if 'motor' not in self.settings:
                self.settings['motor'] = self.DEFAULT_SETTINGS['motor'].copy()
                print("Default motor settings added")
            
            # Save if any updates were made
            self.save_settings()
            
        except Exception as e:
            print(f"Error ensuring complete configuration: {e}")

    def _merge_settings(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded settings with defaults"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_settings(default[key], value)
            else:
                default[key] = value
        return default

    def save_settings_async(self, callback: Optional[callable] = None) -> str:
        """Save settings asynchronously and return operation ID"""
        operation_id = f"save_{self._operation_counter}"
        self._operation_counter += 1
        
        def save_task():
            try:
                result = self._save_settings_sync()
                if callback:
                    callback(result, operation_id)
                return result
            except Exception as e:
                print(f"Async save error: {e}")
                if callback:
                    callback(False, operation_id)
                return False
            finally:
                # Clean up completed operation
                self._pending_operations.pop(operation_id, None)
        
        future = self._executor.submit(save_task)
        self._pending_operations[operation_id] = future
        return operation_id

    def save_settings(self) -> bool:
        """Save settings synchronously"""
        return self._save_settings_sync()

    def _save_settings_sync(self) -> bool:
        """Internal synchronous save method"""
        try:
            # Create backup
            self._create_backup()
            
            # Write settings
            with self._settings_lock:
                settings_copy = self.settings.copy()
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_copy, f, indent=2, default=str)
            
            print(f"Settings saved successfully to {self.settings_file}")
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def _create_backup(self):
        """Create backup of current settings file"""
        try:
            if os.path.exists(self.settings_file):
                backup_name = f"{self.settings_file}.backup_{int(datetime.now().timestamp())}"
                import shutil
                shutil.copy2(self.settings_file, backup_name)
                
                # Keep only last 5 backups
                self._cleanup_old_backups()
                
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")

    def _cleanup_old_backups(self):
        """Keep only the last 5 backup files"""
        try:
            backup_files = [f for f in os.listdir('.') if f.startswith(f"{self.settings_file}.backup_")]
            backup_files.sort(reverse=True)
            
            # Remove old backups (keep only 5)
            for old_backup in backup_files[5:]:
                try:
                    os.remove(old_backup)
                except Exception as e:
                    print(f"Could not remove old backup {old_backup}: {e}")
                    
        except Exception as e:
            print(f"Error cleaning up backups: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value with thread safety"""
        with self._settings_lock:
            keys = key.split('.')
            value = self.settings
            
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                return default

    def set(self, key: str, value: Any) -> bool:
        """Set setting value with thread safety"""
        try:
            with self._settings_lock:
                keys = key.split('.')
                target = self.settings
                
                # Navigate to parent
                for k in keys[:-1]:
                    if k not in target:
                        target[k] = {}
                    target = target[k]
                
                # Set final value
                target[keys[-1]] = value
                return True
                
        except Exception as e:
            print(f"Error setting {key}: {e}")
            return False

    def get_references(self) -> Dict[str, Any]:
        """Get all references"""
        with self._settings_lock:
            return self.settings.get('references', {}).copy()

    def add_reference(self, ref_id: str, ref_data: Dict[str, Any]) -> bool:
        """Add new reference"""
        try:
            with self._settings_lock:
                if 'references' not in self.settings:
                    self.settings['references'] = {}
                
                self.settings['references'][ref_id] = {
                    **ref_data,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            
            # Save immediately for references
            return self.save_settings()
            
        except Exception as e:
            print(f"Error adding reference {ref_id}: {e}")
            return False

    def update_reference(self, ref_id: str, ref_data: Dict[str, Any]) -> bool:
        """Update existing reference"""
        try:
            with self._settings_lock:
                if 'references' not in self.settings:
                    self.settings['references'] = {}
                
                if ref_id in self.settings['references']:
                    # Preserve created_at, update updated_at
                    existing = self.settings['references'][ref_id]
                    self.settings['references'][ref_id] = {
                        **ref_data,
                        'created_at': existing.get('created_at', datetime.now().isoformat()),
                        'updated_at': datetime.now().isoformat()
                    }
                else:
                    # New reference
                    self.settings['references'][ref_id] = {
                        **ref_data,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
            
            return self.save_settings()
            
        except Exception as e:
            print(f"Error updating reference {ref_id}: {e}")
            return False

    def delete_reference(self, ref_id: str) -> bool:
        """Delete reference"""
        try:
            with self._settings_lock:
                if 'references' in self.settings and ref_id in self.settings['references']:
                    del self.settings['references'][ref_id]
                    
                    # Clear last_reference if it was deleted
                    if self.settings.get('last_reference') == ref_id:
                        self.settings['last_reference'] = None
                    
                    return self.save_settings()
            
            return False
            
        except Exception as e:
            print(f"Error deleting reference {ref_id}: {e}")
            return False

    def get_current_reference(self) -> Optional[str]:
        """Get current reference ID"""
        with self._settings_lock:
            return self.settings.get('last_reference')

    def set_current_reference(self, ref_id: Optional[str]) -> bool:
        """Set current reference ID"""
        try:
            with self._settings_lock:
                if ref_id is None or ref_id in self.settings.get('references', {}):
                    self.settings['last_reference'] = ref_id
                    return self.save_settings()
            
            return False
            
        except Exception as e:
            print(f"Error setting current reference: {e}")
            return False

    def get_frequency_mapping(self) -> Dict[str, Any]:
        """Get frequency mapping configuration"""
        with self._settings_lock:
            return self.settings.get('hardware_config', {}).get('frequency_mapping', {
                'mapping_points': [
                    {'pressure': 1.0, 'frequency': 25.0},
                    {'pressure': 1.5, 'frequency': 30.0},
                    {'pressure': 2.0, 'frequency': 35.0},
                    {'pressure': 2.5, 'frequency': 40.0},
                    {'pressure': 3.0, 'frequency': 45.0},
                    {'pressure': 3.5, 'frequency': 47.0},
                    {'pressure': 4.0, 'frequency': 49.0},
                    {'pressure': 4.5, 'frequency': 50.0}
                ],
                'timestamp': datetime.now().isoformat()
            })

    def update_frequency_mapping(self, mapping_points: list) -> bool:
        """Update frequency mapping points"""
        try:
            with self._settings_lock:
                if 'hardware_config' not in self.settings:
                    self.settings['hardware_config'] = {}
                
                self.settings['hardware_config']['frequency_mapping'] = {
                    'mapping_points': mapping_points,
                    'timestamp': datetime.now().isoformat()
                }
            
            return self.save_settings()
            
        except Exception as e:
            print(f"Error updating frequency mapping: {e}")
            return False

    def is_auto_frequency_enabled(self) -> bool:
        """Check if automatic frequency control is enabled"""
        with self._settings_lock:
            return self.settings.get('m100', {}).get('auto_frequency', False)

    def get_m100_settings(self) -> Dict[str, Any]:
        """Get M100 motor controller settings"""
        with self._settings_lock:
            return self.settings.get('m100', self.DEFAULT_SETTINGS['m100']).copy()

    def wait_for_pending_operations(self, timeout: float = 5.0) -> bool:
        """Wait for all pending operations to complete"""
        try:
            for operation_id, future in list(self._pending_operations.items()):
                try:
                    future.result(timeout=timeout)
                except Exception as e:
                    print(f"Operation {operation_id} failed: {e}")
            
            return len(self._pending_operations) == 0
            
        except Exception as e:
            print(f"Error waiting for operations: {e}")
            return False

    def shutdown(self):
        """Shutdown settings manager"""
        try:
            # Wait for pending operations
            self.wait_for_pending_operations()
            
            # Shutdown executor
            self._executor.shutdown(wait=True)
            print("Settings manager shutdown complete")
            
        except Exception as e:
            print(f"Error during shutdown: {e}")

    def validate_settings(self) -> bool:
        """Validate current settings structure"""
        try:
            required_sections = ['ui', 'm100', 'motor', 'hardware_config', 'validation_ranges']
            
            for section in required_sections:
                if section not in self.settings:
                    print(f"Missing required section: {section}")
                    return False
            
            # Validate frequency mapping
            freq_mapping = self.settings.get('hardware_config', {}).get('frequency_mapping', {})
            if not freq_mapping.get('mapping_points'):
                print("Missing frequency mapping points")
                return False
            
            # Validate M100 settings
            m100_settings = self.settings.get('m100', {})
            required_m100_keys = ['enabled', 'auto_frequency', 'port', 'baudrate', 'slave_address', 'default_frequency']
            for key in required_m100_keys:
                if key not in m100_settings:
                    print(f"Missing M100 setting: {key}")
                    return False
            
            print("Settings validation passed")
            return True
            
        except Exception as e:
            print(f"Settings validation error: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        try:
            with self._settings_lock:
                # Keep references but reset everything else
                existing_refs = self.settings.get('references', {})
                last_ref = self.settings.get('last_reference')
                
                self.settings = self.DEFAULT_SETTINGS.copy()
                
                # Restore references
                self.settings['references'] = existing_refs
                self.settings['last_reference'] = last_ref
                
                # Set password hash
                self.settings['password_hash'] = hashlib.sha256('Admin123'.encode()).hexdigest()
                
                # Update timestamp for frequency mapping
                if 'hardware_config' in self.settings and 'frequency_mapping' in self.settings['hardware_config']:
                    self.settings['hardware_config']['frequency_mapping']['timestamp'] = datetime.now().isoformat()
            
            result = self.save_settings()
            if result:
                print("Settings reset to defaults successfully")
            return result
            
        except Exception as e:
            print(f"Error resetting settings to defaults: {e}")
            return False


# Convenience functions for backward compatibility
def load_settings(settings_file: str = 'settings.json') -> SettingsManager:
    """Load settings and return manager instance"""
    return SettingsManager(settings_file)

def get_default_settings() -> Dict[str, Any]:
    """Get copy of default settings"""
    return SettingsManager.DEFAULT_SETTINGS.copy()

def ensure_frequency_mapping_exists(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure frequency mapping exists in settings dictionary"""
    if "hardware_config" not in settings:
        settings["hardware_config"] = {}
    
    if "frequency_mapping" not in settings["hardware_config"]:
        settings["hardware_config"]["frequency_mapping"] = {
            "mapping_points": [
                {"pressure": 1.0, "frequency": 25.0},
                {"pressure": 1.5, "frequency": 30.0},
                {"pressure": 2.0, "frequency": 35.0},
                {"pressure": 2.5, "frequency": 40.0},
                {"pressure": 3.0, "frequency": 45.0},
                {"pressure": 3.5, "frequency": 47.0},
                {"pressure": 4.0, "frequency": 49.0},
                {"pressure": 4.5, "frequency": 50.0}
            ],
            "timestamp": datetime.now().isoformat()
        }
        print("Default frequency mapping added to settings")
    
    return settings


if __name__ == "__main__":
    # Test the settings manager
    print("Testing Settings Manager...")
    
    # Create settings manager
    settings_mgr = SettingsManager("test_settings.json")
    
    # Validate settings
    if settings_mgr.validate_settings():
        print("✅ Settings validation passed")
    else:
        print("❌ Settings validation failed")
    
    # Test frequency mapping
    freq_mapping = settings_mgr.get_frequency_mapping()
    print(f"📊 Frequency mapping points: {len(freq_mapping.get('mapping_points', []))}")
    
    # Test M100 settings
    m100_settings = settings_mgr.get_m100_settings()
    print(f"🔧 M100 auto frequency enabled: {m100_settings.get('auto_frequency', False)}")
    
    # Cleanup
    settings_mgr.shutdown()
    print("🏁 Settings manager test complete") 