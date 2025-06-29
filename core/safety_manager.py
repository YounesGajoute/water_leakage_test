"""
Enhanced Safety Manager - Comprehensive safety system management
"""
import time
import threading
import json
from datetime import datetime
from typing import Tuple, Callable, Optional, Dict, List, Any
from enum import Enum


class SafetyLevel(Enum):
    """Safety alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SafetyCondition(Enum):
    """Safety condition types"""
    DOOR_CLOSED = "door_closed"
    EMERGENCY_BUTTON = "emergency_button"
    TANK_LEVEL = "tank_level"
    LIMIT_SWITCHES = "limit_switches"
    PRESSURE_LIMITS = "pressure_limits"
    TEMPERATURE_LIMITS = "temperature_limits"
    COMMUNICATION = "communication"


class SafetyManager:
    def __init__(self, hardware_manager, emergency_callback: Optional[Callable] = None,
                 alert_callback: Optional[Callable] = None):
        """
        Initialize enhanced safety manager
        
        Args:
            hardware_manager: Hardware interface
            emergency_callback: Function to call on emergency
            alert_callback: Function to call for safety alerts
        """
        self.hardware = hardware_manager
        self.emergency_callback = emergency_callback
        self.alert_callback = alert_callback
        
        # Safety state
        self.emergency_active = False
        self.monitoring_active = False
        self.monitoring_thread = None
        self.safety_lock = threading.RLock()
        
        # Safety conditions registry
        self.safety_conditions = {
            SafetyCondition.DOOR_CLOSED: {
                'check': self._check_door_closed,
                'critical': True,
                'enabled': True,
                'last_check': 0,
                'failure_count': 0
            },
            SafetyCondition.EMERGENCY_BUTTON: {
                'check': self._check_emergency_button,
                'critical': True,
                'enabled': True,
                'last_check': 0,
                'failure_count': 0
            },
            SafetyCondition.TANK_LEVEL: {
                'check': self._check_tank_level,
                'critical': False,
                'enabled': True,
                'last_check': 0,
                'failure_count': 0
            },
            SafetyCondition.LIMIT_SWITCHES: {
                'check': self._check_limit_switches,
                'critical': True,
                'enabled': True,
                'last_check': 0,
                'failure_count': 0
            },
            SafetyCondition.PRESSURE_LIMITS: {
                'check': self._check_pressure_limits,
                'critical': False,
                'enabled': True,
                'last_check': 0,
                'failure_count': 0
            }
        }
        
        # Safety thresholds and limits
        self.safety_limits = {
            'max_pressure': 5.0,  # bar
            'min_pressure': -0.5,  # bar (vacuum)
            'max_temperature': 80.0,  # °C
            'max_failure_count': 3,
            'emergency_reset_delay': 5.0,  # seconds
            'monitoring_interval': 0.1  # seconds
        }
        
        # Safety log
        self.safety_log = []
        self.alert_history = []
        
        # Performance monitoring
        self.check_stats = {
            'total_checks': 0,
            'failed_checks': 0,
            'emergency_triggers': 0,
            'monitoring_start_time': time.time(),
            'last_check_time': 0,
            'average_check_time': 0,
            'monitoring_uptime': time.time() - self.check_stats.get('monitoring_start_time', time.time()),
            'conditions_enabled': sum(1 for config in self.safety_conditions.values() if config['enabled']),
            'critical_conditions': sum(1 for config in self.safety_conditions.values() if config['critical'] and config['enabled'])
        }
        
        # Start monitoring automatically
        self.start_monitoring()
    
    def check_safety_conditions(self, critical_only: bool = False) -> Tuple[bool, str]:
        """
        Check all safety conditions
        
        Args:
            critical_only: If True, only check critical conditions
            
        Returns:
            Tuple[bool, str]: (safe, message)
        """
        try:
            with self.safety_lock:
                start_time = time.time()
                self.check_stats['total_checks'] += 1
                
                failed_conditions = []
                critical_failures = []
                
                # Check each enabled safety condition
                for condition, config in self.safety_conditions.items():
                    if not config['enabled']:
                        continue
                    
                    if critical_only and not config['critical']:
                        continue
                    
                    try:
                        is_safe, message = config['check']()
                        config['last_check'] = time.time()
                        
                        if not is_safe:
                            failed_conditions.append(f"{condition.value}: {message}")
                            config['failure_count'] += 1
                            
                            if config['critical']:
                                critical_failures.append(condition.value)
                            
                            # Log safety failure
                            self._log_safety_event(
                                SafetyLevel.CRITICAL if config['critical'] else SafetyLevel.WARNING,
                                f"Safety check failed: {condition.value}",
                                {'condition': condition.value, 'message': message}
                            )
                        else:
                            # Reset failure count on success
                            config['failure_count'] = 0
                    
                    except Exception as e:
                        error_msg = f"Error checking {condition.value}: {str(e)}"
                        failed_conditions.append(error_msg)
                        config['failure_count'] += 1
                        
                        self._log_safety_event(
                            SafetyLevel.CRITICAL,
                            f"Safety check error: {condition.value}",
                            {'condition': condition.value, 'error': str(e)}
                        )
                
                # Update statistics
                check_time = time.time() - start_time
                self.check_stats['last_check_time'] = check_time
                self.check_stats['average_check_time'] = (
                    (self.check_stats['average_check_time'] * (self.check_stats['total_checks'] - 1) + check_time) /
                    self.check_stats['total_checks']
                )
                
                # Determine overall safety status
                if critical_failures:
                    self.check_stats['failed_checks'] += 1
                    return False, f"Critical safety failures: {', '.join(critical_failures)}"
                elif failed_conditions and not critical_only:
                    return False, f"Safety warnings: {', '.join(failed_conditions)}"
                else:
                    return True, "All safety checks passed"
                
        except Exception as e:
            self._log_safety_event(
                SafetyLevel.EMERGENCY,
                "Safety system error",
                {'error': str(e)}
            )
            return False, f"Safety system error: {str(e)}"
    
    def _check_door_closed(self) -> Tuple[bool, str]:
        """Check if door is properly closed"""
        try:
            if hasattr(self.hardware, 'input_lines') and 'door_close' in self.hardware.input_lines:
                door_state = self.hardware.input_lines["door_close"].get_value()
                if not door_state:
                    return False, "Door must be closed before operation"
                return True, "Door properly closed"
            else:
                # Mock hardware fallback
                return True, "Door check bypassed (mock mode)"
        except Exception as e:
            return False, f"Door sensor error: {str(e)}"
    
    def _check_emergency_button(self) -> Tuple[bool, str]:
        """Check emergency button state"""
        try:
            if hasattr(self.hardware, 'input_lines') and 'emergency_btn' in self.hardware.input_lines:
                # Emergency button is typically inverted (active low)
                emergency_state = self.hardware.input_lines["emergency_btn"].get_value()
                if emergency_state:  # Button pressed
                    return False, "Emergency button is activated"
                return True, "Emergency button normal"
            else:
                # Mock hardware fallback
                return True, "Emergency button check bypassed (mock mode)"
        except Exception as e:
            return False, f"Emergency button error: {str(e)}"
    
    def _check_tank_level(self) -> Tuple[bool, str]:
        """Check tank minimum level"""
        try:
            if hasattr(self.hardware, 'input_lines') and 'tank_min' in self.hardware.input_lines:
                tank_level = self.hardware.input_lines["tank_min"].get_value()
                if not tank_level:
                    return False, "Tank level too low"
                return True, "Tank level adequate"
            else:
                # Mock hardware fallback
                return True, "Tank level check bypassed (mock mode)"
        except Exception as e:
            return False, f"Tank level sensor error: {str(e)}"
    
    def _check_limit_switches(self) -> Tuple[bool, str]:
        """Check actuator limit switches"""
        try:
            if hasattr(self.hardware, 'input_lines'):
                if 'actuator_min' in self.hardware.input_lines and 'actuator_max' in self.hardware.input_lines:
                    min_limit = self.hardware.input_lines["actuator_min"].get_value()
                    max_limit = self.hardware.input_lines["actuator_max"].get_value()
                    
                    # Both limits active would be an error
                    if min_limit and max_limit:
                        return False, "Both limit switches active - sensor error"
                    
                    return True, "Limit switches normal"
                else:
                    return True, "Limit switches not available"
            else:
                # Mock hardware fallback
                return True, "Limit switch check bypassed (mock mode)"
        except Exception as e:
            return False, f"Limit switch error: {str(e)}"
    
    def _check_pressure_limits(self) -> Tuple[bool, str]:
        """Check pressure within safe limits"""
        try:
            if hasattr(self.hardware, 'read_pressure'):
                pressure = self.hardware.read_pressure()
                if pressure is not None:
                    if pressure > self.safety_limits['max_pressure']:
                        return False, f"Pressure too high: {pressure:.2f} bar"
                    if pressure < self.safety_limits['min_pressure']:
                        return False, f"Pressure too low: {pressure:.2f} bar"
                    return True, f"Pressure normal: {pressure:.2f} bar"
                else:
                    return False, "Cannot read pressure"
            else:
                # Mock hardware fallback
                return True, "Pressure check bypassed (mock mode)"
        except Exception as e:
            return False, f"Pressure sensor error: {str(e)}"
    
    def start_monitoring(self):
        """Start continuous safety monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_safety,
            daemon=True,
            name="SafetyMonitor"
        )
        self.monitoring_thread.start()
        
        self._log_safety_event(
            SafetyLevel.INFO,
            "Safety monitoring started",
            {'monitoring_interval': self.safety_limits['monitoring_interval']}
        )
    
    def stop_monitoring(self):
        """Stop safety monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        
        self._log_safety_event(SafetyLevel.INFO, "Safety monitoring stopped")
    
    def _monitor_safety(self):
        """Continuous safety monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform quick safety check (critical conditions only)
                is_safe, message = self.check_safety_conditions(critical_only=True)
                
                if not is_safe and not self.emergency_active:
                    # Check if this is a new emergency or continuation
                    self.trigger_emergency(message)
                
                # Check for emergency button specifically (high priority)
                try:
                    if hasattr(self.hardware, 'input_lines') and 'emergency_btn' in self.hardware.input_lines:
                        emergency_state = self.hardware.input_lines["emergency_btn"].get_value()
                        if emergency_state and not self.emergency_active:
                            self.trigger_emergency("Emergency button pressed")
                except:
                    pass  # Ignore errors in emergency button check during monitoring
                
                time.sleep(self.safety_limits['monitoring_interval'])
                
            except Exception as e:
                self._log_safety_event(
                    SafetyLevel.CRITICAL,
                    "Error in safety monitoring",
                    {'error': str(e)}
                )
                time.sleep(1)  # Slower retry on error
    
    def trigger_emergency(self, reason: str = "Unknown"):
        """Trigger emergency stop"""
        with self.safety_lock:
            if self.emergency_active:
                return  # Already in emergency state
            
            self.emergency_active = True
            self.check_stats['emergency_triggers'] += 1
            timestamp = datetime.now().isoformat()
            
            # Log emergency event
            self._log_safety_event(
                SafetyLevel.EMERGENCY,
                f"EMERGENCY TRIGGERED: {reason}",
                {
                    'reason': reason,
                    'timestamp': timestamp,
                    'system_state': self._get_system_state()
                }
            )
            
            # Call emergency callback
            if self.emergency_callback:
                try:
                    self.emergency_callback(reason)
                except Exception as e:
                    self._log_safety_event(
                        SafetyLevel.CRITICAL,
                        "Error in emergency callback",
                        {'error': str(e)}
                    )
            
            # Send alert
            self._send_alert(SafetyLevel.EMERGENCY, f"Emergency stop: {reason}")
    
    def reset_emergency(self) -> bool:
        """Reset emergency state after conditions are cleared"""
        try:
            with self.safety_lock:
                # Check if emergency conditions are cleared
                is_safe, message = self.check_safety_conditions(critical_only=True)
                if not is_safe:
                    self._log_safety_event(
                        SafetyLevel.WARNING,
                        f"Cannot reset emergency - conditions not met: {message}"
                    )
                    return False
                
                # Wait for reset delay
                time.sleep(self.safety_limits['emergency_reset_delay'])
                
                # Check again after delay
                is_safe, message = self.check_safety_conditions(critical_only=True)
                if not is_safe:
                    self._log_safety_event(
                        SafetyLevel.WARNING,
                        f"Emergency reset failed - conditions changed: {message}"
                    )
                    return False
                
                self.emergency_active = False
                self._log_safety_event(SafetyLevel.INFO, "Emergency state reset")
                self._send_alert(SafetyLevel.INFO, "Emergency state cleared")
                return True
                
        except Exception as e:
            self._log_safety_event(
                SafetyLevel.CRITICAL,
                "Error resetting emergency",
                {'error': str(e)}
            )
            return False
    
    def _get_system_state(self) -> Dict:
        """Get current system state for logging"""
        try:
            state: Dict[str, Any] = {'timestamp': time.time()}
            
            # Get input states
            if hasattr(self.hardware, 'input_lines'):
                state['inputs'] = {}
                for pin_name, line in self.hardware.input_lines.items():
                    try:
                        state['inputs'][pin_name] = line.get_value()
                    except:
                        state['inputs'][pin_name] = "ERROR"
            
            # Get pressure reading
            if hasattr(self.hardware, 'read_pressure'):
                try:
                    pressure = self.hardware.read_pressure()
                    state['pressure'] = pressure if pressure is not None else "ERROR"
                except:
                    state['pressure'] = "ERROR"
            
            # Get safety condition states
            state['safety_conditions'] = {}
            for condition, config in self.safety_conditions.items():
                state['safety_conditions'][condition.value] = {
                    'enabled': config['enabled'],
                    'critical': config['critical'],
                    'failure_count': config['failure_count'],
                    'last_check': config['last_check']
                }
            
            return state
            
        except Exception as e:
            return {"error": f"Could not read system state: {str(e)}"}
    
    def _log_safety_event(self, level: SafetyLevel, message: str, data: Optional[Dict] = None):
        """Log a safety event with timestamp"""
        try:
            event = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'level': level.value,
                'message': message,
                'data': data or {}
            }
            
            self.safety_log.append(event)
            
            # Keep log size manageable
            if len(self.safety_log) > 1000:
                self.safety_log = self.safety_log[-500:]  # Keep last 500 events
            
            # Print for debugging
            print(f"[SAFETY {level.value.upper()}] {message}")
            
        except Exception as e:
            print(f"Error logging safety event: {e}")
    
    def _send_alert(self, level: SafetyLevel, message: str):
        """Send safety alert via callback"""
        try:
            alert = {
                'timestamp': time.time(),
                'level': level.value,
                'message': message
            }
            
            self.alert_history.append(alert)
            
            # Keep alert history manageable
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-50:]
            
            if self.alert_callback:
                self.alert_callback(level, message)
                
        except Exception as e:
            print(f"Error sending alert: {e}")
    
    def is_safe_to_operate(self) -> bool:
        """Quick safety check for operation"""
        if self.emergency_active:
            return False
        
        # Check only critical conditions quickly
        is_safe, _ = self.check_safety_conditions(critical_only=True)
        return is_safe
    
    def get_safety_status(self) -> Dict:
        """Get comprehensive safety status"""
        return {
            'emergency_active': self.emergency_active,
            'monitoring_active': self.monitoring_active,
            'is_safe_to_operate': self.is_safe_to_operate(),
            'condition_states': {
                condition.value: {
                    'enabled': config['enabled'],
                    'critical': config['critical'],
                    'failure_count': config['failure_count'],
                    'last_check': config['last_check']
                }
                for condition, config in self.safety_conditions.items()
            },
            'statistics': self.check_stats.copy(),
            'recent_alerts': self.alert_history[-10:],  # Last 10 alerts
            'system_state': self._get_system_state()
        }
    
    def enable_condition(self, condition: SafetyCondition, enabled: bool = True):
        """Enable or disable a safety condition"""
        if condition in self.safety_conditions:
            self.safety_conditions[condition]['enabled'] = enabled
            self._log_safety_event(
                SafetyLevel.INFO,
                f"Safety condition {'enabled' if enabled else 'disabled'}: {condition.value}"
            )
    
    def set_safety_limit(self, limit_name: str, value: float):
        """Set a safety limit value"""
        if limit_name in self.safety_limits:
            old_value = self.safety_limits[limit_name]
            self.safety_limits[limit_name] = value
            self._log_safety_event(
                SafetyLevel.INFO,
                f"Safety limit updated: {limit_name}",
                {'old_value': old_value, 'new_value': value}
            )
    
    def export_safety_log(self, filepath: str) -> bool:
        """Export safety log to file"""
        try:
            export_data = {
                'safety_log': self.safety_log,
                'alert_history': self.alert_history,
                'safety_status': self.get_safety_status(),
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=4)
            
            return True
            
        except Exception as e:
            self._log_safety_event(
                SafetyLevel.CRITICAL,
                "Error exporting safety log",
                {'error': str(e)}
            )
            return False
    
    def clear_safety_log(self):
        """Clear safety log (keep recent entries)"""
        self.safety_log = self.safety_log[-50:]  # Keep last 50 entries
        self.alert_history = self.alert_history[-20:]  # Keep last 20 alerts
        self._log_safety_event(SafetyLevel.INFO, "Safety log cleared")
    
    def get_statistics(self) -> Dict:
        """Get safety system statistics"""
        return {
            'total_checks': self.check_stats['total_checks'],
            'failed_checks': self.check_stats['failed_checks'],
            'success_rate': (
                (self.check_stats['total_checks'] - self.check_stats['failed_checks']) / 
                self.check_stats['total_checks'] * 100
            ) if self.check_stats['total_checks'] > 0 else 0,
            'emergency_triggers': self.check_stats['emergency_triggers'],
            'average_check_time': self.check_stats['average_check_time'],
            'monitoring_uptime': self.check_stats['monitoring_uptime'],
            'conditions_enabled': self.check_stats['conditions_enabled'],
            'critical_conditions': self.check_stats['critical_conditions']
        }