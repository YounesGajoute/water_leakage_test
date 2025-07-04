import serial
import time
import threading
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass


class ModbusFunctionCodes(Enum):
    """Modbus RTU function codes"""
    READ_COILS = 0x01
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10


class M100Status(Enum):
    """M100 motor status states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAULT = "fault"
    UNKNOWN = "unknown"


@dataclass
class M100Config:
    """M100 configuration parameters"""
    port: str = '/dev/ttyUSB0'
    baudrate: int = 9600
    slave_address: int = 0x01
    timeout: float = 1.0
    max_retries: int = 3
    frame_delay: float = 0.01
    response_timeout: float = 0.5


class ModbusException(Exception):
    """Custom exception for Modbus communication errors"""
    ERROR_CODES = {
        0x01: "Illegal Function",
        0x02: "Illegal Data Address", 
        0x03: "Illegal Data Value",
        0x04: "Slave Device Failure",
        0x05: "Acknowledge",
        0x06: "Slave Device Busy",
        0x08: "Memory Parity Error",
        0x0A: "Gateway Path Unavailable",
        0x0B: "Gateway Target Device Failed to Respond"
    }

    def __init__(self, error_code: int):
        self.error_code = error_code
        message = self.ERROR_CODES.get(error_code, f"Unknown Error (0x{error_code:02X})")
        super().__init__(f"Modbus Error 0x{error_code:02X}: {message}")


class M100Controller:
    """
    Enhanced M100 Motor Controller with robust RS-485 communication
    Integrates with Air Leakage Test Application control logic
    """
    
    # Control bit addresses
    CONTROL_BITS = {
        'OPERATION': 0x0048,
        'FORWARD': 0x0049,
        'REVERSE': 0x004A,
        'STOP': 0x004B,
        'FWD_REV_SWITCH': 0x004C,
        'JOG': 0x004D,
        'JOG_FORWARD': 0x004E,
        'JOG_REVERSE': 0x004F
    }
    
    # Status bit addresses
    STATUS_BITS = {
        'OPERATION': 0x0000,
        'JOG': 0x0001,
        'DIRECTION': 0x0002,
        'RUNNING': 0x0003,
        'JOGGING': 0x0004,
        'ROT_DIR': 0x0005,
        'BRAKING': 0x0006,
        'FREQ_TRACK': 0x0007
    }
    
    # Register addresses
    REGISTERS = {
        'FREQUENCY': 0x0201,
        'F002_PARAM': 0x0002,
        'OUTPUT_VOLTAGE': 0x0100,
        'OUTPUT_CURRENT': 0x0101,
        'MOTOR_SPEED': 0x0102
    }

    def __init__(self, config: Optional[M100Config] = None):
        """Initialize M100 controller with enhanced configuration"""
        self.config = config or M100Config()
        self.serial_connection = None
        self.communication_lock = threading.RLock()
        self.last_command_time = 0
        self.connection_established = False
        self.current_status = M100Status.UNKNOWN
        self.error_count = 0
        self.max_error_count = 10
        
        # Communication statistics
        self.stats = {
            'commands_sent': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'timeouts': 0,
            'retries': 0
        }
        
        print(f"Initializing M100 Controller on {self.config.port}")

    def connect(self) -> bool:
        """Establish RS-485 connection with enhanced error handling"""
        try:
            with self.communication_lock:
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                
                self.serial_connection = serial.Serial(
                    port=self.config.port,
                    baudrate=self.config.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.config.timeout,
                    write_timeout=self.config.timeout
                )
                
                # Calculate optimal frame delay based on baud rate
                self.frame_delay = max(0.01, (10.0 / self.config.baudrate) * 3.5)
                
                # Verify communication
                if self._verify_communication():
                    self.connection_established = True
                    print("M100 Controller connected successfully")
                    return True
                else:
                    print("M100 Controller connection verification failed")
                    return False
                    
        except serial.SerialException as e:
            print(f"Serial connection failed: {e}")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Safely disconnect from M100"""
        try:
            with self.communication_lock:
                if self.serial_connection and self.serial_connection.is_open:
                    # Emergency stop before disconnecting
                    self._emergency_stop_immediate()
                    self.serial_connection.close()
                    print("M100 Controller disconnected")
                self.connection_established = False
        except Exception as e:
            print(f"Error during disconnect: {e}")

    def _calculate_crc(self, message: bytes) -> Tuple[int, int]:
        """Calculate CRC16 for Modbus RTU"""
        crc = 0xFFFF
        polynomial = 0xA001
        
        for byte in message:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ polynomial
                else:
                    crc >>= 1
        
        return crc & 0xFF, (crc >> 8) & 0xFF

    def _send_command(self, command: bytes, expected_length: Optional[int] = None) -> Optional[bytes]:
        """Send Modbus command with robust error handling and retry logic"""
        if not self.connection_established:
            raise ConnectionError("M100 Controller not connected")
        
        with self.communication_lock:
            for attempt in range(self.config.max_retries):
                try:
                    # Ensure proper timing between commands
                    current_time = time.time()
                    elapsed = current_time - self.last_command_time
                    if elapsed < self.frame_delay:
                        time.sleep(self.frame_delay - elapsed)
                    
                    # Clear buffers
                    assert self.serial_connection is not None
                    self.serial_connection.reset_input_buffer()
                    self.serial_connection.reset_output_buffer()
                    
                    # Send command
                    crc_low, crc_high = self._calculate_crc(command)
                    full_command = command + bytes([crc_low, crc_high])
                    
                    self.serial_connection.write(full_command)
                    self.serial_connection.flush()
                    self.last_command_time = time.time()
                    self.stats['commands_sent'] += 1
                    
                    # Wait for response
                    response = self._read_response(expected_length)
                    
                    if response:
                        self._verify_response(response, command[1])
                        self.stats['successful_responses'] += 1
                        self.error_count = 0  # Reset error count on success
                        return response
                    
                except ModbusException as e:
                    print(f"Modbus error on attempt {attempt + 1}: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                except Exception as e:
                    print(f"Communication error on attempt {attempt + 1}: {e}")
                    if attempt == self.config.max_retries - 1:
                        self.error_count += 1
                        if self.error_count >= self.max_error_count:
                            self.connection_established = False
                            raise ConnectionError("Too many communication errors")
                        raise
                
                self.stats['retries'] += 1
                time.sleep(0.1 * (attempt + 1))  # Progressive delay
            
            self.stats['failed_responses'] += 1
            return None

    def _read_response(self, expected_length: Optional[int] = None) -> Optional[bytes]:
        """Read response with timeout handling"""
        response = bytearray()
        start_time = time.time()
        
        while time.time() - start_time < self.config.response_timeout:
            assert self.serial_connection is not None
            if self.serial_connection.in_waiting:
                response.extend(self.serial_connection.read(self.serial_connection.in_waiting))
                
                # Check if we have minimum response or expected length
                if expected_length is not None and len(response) >= expected_length:
                    break
                elif len(response) >= 5:  # Minimum Modbus response
                    break
            
            time.sleep(0.001)  # Small delay to prevent CPU spinning
        
        if not response:
            self.stats['timeouts'] += 1
            raise TimeoutError("No response received")
        
        return bytes(response)

    def _verify_response(self, response: bytes, expected_function: int):
        """Verify response integrity and handle errors"""
        if len(response) < 4:
            raise ValueError("Response too short")
        
        if response[0] != self.config.slave_address:
            raise ValueError(f"Invalid slave address: {response[0]}")
        
        if response[1] == expected_function + 0x80:  # Error response
            if len(response) >= 3:
                raise ModbusException(response[2])
            raise ValueError("Invalid error response")
        
        if response[1] != expected_function:
            raise ValueError(f"Unexpected function code: {response[1]}")

    def _verify_communication(self) -> bool:
        """Verify communication by reading status"""
        try:
            status = self.read_status()
            return status is not None
        except Exception:
            return False

    def write_control_bit(self, bit_name: str, value: bool) -> bool:
        """Write control bit with validation"""
        if bit_name not in self.CONTROL_BITS:
            raise ValueError(f"Unknown control bit: {bit_name}")
        
        address = self.CONTROL_BITS[bit_name]
        command = bytes([
            self.config.slave_address,
            ModbusFunctionCodes.WRITE_SINGLE_COIL.value,
            (address >> 8) & 0xFF,
            address & 0xFF,
            0xFF if value else 0x00,
            0x00
        ])
        
        try:
            response = self._send_command(command, 8)
            return response is not None
        except Exception as e:
            print(f"Failed to write control bit {bit_name}: {e}")
            return False

    def read_status(self) -> Optional[Dict[str, bool]]:
        """Read motor status with comprehensive error handling"""
        command = bytes([
            self.config.slave_address,
            ModbusFunctionCodes.READ_COILS.value,
            0x00, 0x00,  # Start address
            0x00, 0x08   # Read 8 bits
        ])
        
        try:
            response = self._send_command(command)
            if response and len(response) >= 4:
                status_byte = response[3]
                status = {
                    'operation': bool(status_byte & 0x01),
                    'jog': bool(status_byte & 0x02),
                    'direction': bool(status_byte & 0x04),
                    'running': bool(status_byte & 0x08),
                    'jogging': bool(status_byte & 0x10),
                    'rotation_dir': bool(status_byte & 0x20),
                    'braking': bool(status_byte & 0x40),
                    'freq_tracking': bool(status_byte & 0x80)
                }
                
                # Update internal status
                if status['running']:
                    self.current_status = M100Status.RUNNING
                elif status['operation']:
                    self.current_status = M100Status.STARTING
                else:
                    self.current_status = M100Status.STOPPED
                
                return status
        except Exception as e:
            print(f"Failed to read status: {e}")
            self.current_status = M100Status.UNKNOWN
        
        return None

    def set_frequency(self, frequency_hz: float) -> bool:
        """Set motor frequency with validation and verification"""
        if not (0.5 <= frequency_hz <= 60.0):
            raise ValueError("Frequency must be between 0.5 and 60.0 Hz")
        
        # Convert to register value (0.1 Hz units)
        freq_value = int(frequency_hz * 10)
        
        command = bytes([
            self.config.slave_address,
            ModbusFunctionCodes.WRITE_SINGLE_REGISTER.value,
            (self.REGISTERS['FREQUENCY'] >> 8) & 0xFF,
            self.REGISTERS['FREQUENCY'] & 0xFF,
            (freq_value >> 8) & 0xFF,
            freq_value & 0xFF
        ])
        
        try:
            response = self._send_command(command, 8)
            if response:
                # Verify frequency was set correctly
                time.sleep(0.1)
                actual_freq = self.read_frequency()
                if actual_freq and abs(actual_freq - frequency_hz) <= 0.5:
                    print(f"Frequency set successfully: {frequency_hz} Hz")
                    return True
                else:
                    print(f"Frequency verification failed. Set: {frequency_hz}, Read: {actual_freq}")
                    
            return False
        except Exception as e:
            print(f"Failed to set frequency: {e}")
            return False

    def read_frequency(self) -> Optional[float]:
        """Read current motor frequency"""
        command = bytes([
            self.config.slave_address,
            ModbusFunctionCodes.READ_HOLDING_REGISTERS.value,
            (self.REGISTERS['FREQUENCY'] >> 8) & 0xFF,
            self.REGISTERS['FREQUENCY'] & 0xFF,
            0x00, 0x01  # Read 1 register
        ])
        
        try:
            response = self._send_command(command)
            if response and len(response) >= 7:
                freq_value = (response[3] << 8) | response[4]
                return freq_value / 10.0  # Convert from 0.1 Hz units
        except Exception as e:
            print(f"Failed to read frequency: {e}")
        
        return None

    def start_motor_relay(self, hardware_manager) -> bool:
        """Start motor via relay control (GPIO pin 24) - NOT Modbus"""
        try:
            if not hardware_manager or not hasattr(hardware_manager, 'output_lines'):
                print("Hardware manager not available for relay control")
                return False
            
            # Start motor via relay control
            hardware_manager.output_lines['relay_control_h300'].set_value(1)
            print("Motor started via relay control (GPIO pin 24)")
            
            # Wait a moment and verify via Modbus status
            time.sleep(2.0)
            status = self.read_status()
            if status and status['running']:
                print("Motor start verified via Modbus status")
                return True
            else:
                print("Warning: Motor start not confirmed via Modbus status")
                return True  # Still return True as relay was activated
                
        except Exception as e:
            print(f"Failed to start motor via relay: {e}")
            return False

    def stop_motor_relay(self, hardware_manager) -> bool:
        """Stop motor via relay control (GPIO pin 24) - NOT Modbus"""
        try:
            if not hardware_manager or not hasattr(hardware_manager, 'output_lines'):
                print("Hardware manager not available for relay control")
                return False
            
            # Stop motor via relay control
            hardware_manager.output_lines['relay_control_h300'].set_value(0)
            print("Motor stopped via relay control (GPIO pin 24)")
            
            # Wait a moment and verify via Modbus status
            time.sleep(2.0)
            status = self.read_status()
            if status and not status['running']:
                print("Motor stop verified via Modbus status")
                return True
            else:
                print("Warning: Motor stop not confirmed via Modbus status")
                return True  # Still return True as relay was deactivated
                
        except Exception as e:
            print(f"Failed to stop motor via relay: {e}")
            return False

    def _emergency_stop_relay(self, hardware_manager):
        """Immediate emergency stop via relay - NOT Modbus"""
        try:
            if hardware_manager and hasattr(hardware_manager, 'output_lines'):
                hardware_manager.output_lines['relay_control_h300'].set_value(0)
                print("Emergency stop executed via relay control")
        except:
            pass  # Silent failure acceptable for emergency stop

    def _emergency_stop_immediate(self):
        """Immediate emergency stop via Modbus"""
        try:
            if self.connection_established:
                self.write_control_bit('STOP', True)
                print("Emergency stop executed via Modbus")
        except:
            pass  # Silent failure acceptable for emergency stop

    def get_motor_data(self) -> Dict[str, Any]:
        """Get comprehensive motor data (Modbus monitoring only)"""
        data = {
            'status': self.current_status.value,
            'frequency': self.read_frequency(),
            'connected': self.connection_established,
            'error_count': self.error_count,
            'control_method': 'relay_gpio_pin_24'  # Indicate relay control
        }
        
        status = self.read_status()
        if status:
            data.update(status)
        
        return data

    def get_communication_stats(self) -> Dict[str, float]:
        """Get communication statistics (allow floats)"""
        total_commands = self.stats['commands_sent']
        if total_commands > 0:
            success_rate = (self.stats['successful_responses'] / total_commands) * 100
        else:
            success_rate = 0.0
        
        return {
            **self.stats,
            'success_rate_percent': round(success_rate, 2),
            'error_count': float(self.error_count),
            'max_errors': float(self.max_error_count)
        }


# Enhanced integration with existing test controller
class EnhancedTestController:
    """
    Enhanced Test Controller with M100 integration
    M100 provides frequency control via Modbus, start/stop via GPIO relay
    """
    
    def __init__(self, hardware_manager, motor_controller, safety_manager, 
                 m100_controller: M100Controller, status_callback=None):
        # Store original test controller functionality
        from core.test_controller import TestController
        self.base_controller = TestController(
            hardware_manager, motor_controller, safety_manager, status_callback
        )
        
        self.hardware_manager = hardware_manager  # Store for relay control
        self.m100_controller = m100_controller
        self.settings = {}
        
    def load_settings(self, settings: Dict[str, Any]):
        """Load test settings including M100 configuration"""
        self.settings = settings
        
        # Configure M100 if settings available
        m100_config = settings.get('m100_config', {})
        if m100_config.get('enabled', False):
            config = M100Config(
                port=m100_config.get('port', '/dev/ttyUSB0'),
                baudrate=m100_config.get('baudrate', 9600),
                slave_address=m100_config.get('slave_address', 1)
            )
            self.m100_controller.config = config

    def start_test(self, reference_data: Dict[str, Any]) -> bool:
        """Enhanced test start with adaptive sequence"""
        try:
            # Get configuration
            auto_frequency = self.settings.get('m100_config', {}).get('auto_frequency', False)
            target_frequency = reference_data.get('parameters', {}).get('motor_frequency', 25.0)
            
            print(f"Starting test with adaptive sequence (auto_frequency: {auto_frequency})")
            
            # Phase 1: Safety validation
            if not self._validate_safety():
                return False
            
            # Phase 2: Home positioning
            if not self._move_to_home():
                return False
            
            # Phase 3: Target positioning
            target_position = reference_data['parameters']['position']
            if not self._move_to_position(target_position):
                return False
            
            # Phase 4: Motor control (adaptive based on configuration)
            if auto_frequency:
                # Set frequency via Modbus before starting motor
                if not self._set_motor_frequency_modbus(target_frequency):
                    return False
                
                # Start motor via relay control
                if not self._start_motor_relay():
                    return False
            else:
                # Start motor via relay control without frequency setting
                if not self._start_motor_relay():
                    return False
            
            # Phase 5: Start base test monitoring
            if not self.base_controller.start_test(reference_data):
                return False
            
            print("Enhanced test sequence started successfully")
            return True
            
        except Exception as e:
            print(f"Failed to start enhanced test: {e}")
            self._emergency_cleanup()
            return False

    def _validate_safety(self) -> bool:
        """Comprehensive safety validation"""
        # Use existing safety manager
        safety_ok, safety_msg = self.base_controller.safety.check_safety_conditions()
        if not safety_ok:
            print(f"Safety validation failed: {safety_msg}")
            return False
        
        # Additional M100 safety checks
        if self.settings.get('m100_config', {}).get('enabled', False):
            if not self.m100_controller.connection_established:
                if not self.m100_controller.connect():
                    print("M100 Modbus connection failed")
                    return False
            
            # Ensure motor is stopped via relay
            if not self._stop_motor_relay():
                print("Failed to ensure motor is stopped via relay")
                return False
        
        print("Safety validation passed")
        return True

    def _move_to_home(self) -> bool:
        """Move actuator to home position"""
        print("Moving to home position...")
        return self.base_controller.motor.move_to_home()

    def _move_to_position(self, position: float) -> bool:
        """Move actuator to target position"""
        print(f"Moving to position {position}mm...")
        return self.base_controller.motor.move_to_position(
            position, 
            self.base_controller._check_stop_condition
        )

    def _set_motor_frequency_modbus(self, frequency: float) -> bool:
        """Set M100 motor frequency via Modbus if enabled"""
        if not self.settings.get('m100_config', {}).get('enabled', False):
            print("M100 not enabled, skipping frequency setting")
            return True
        
        print(f"Setting motor frequency to {frequency} Hz via Modbus...")
        return self.m100_controller.set_frequency(frequency)

    def _start_motor_relay(self) -> bool:
        """Start motor via relay control (GPIO pin 24)"""
        m100_enabled = self.settings.get('m100_config', {}).get('enabled', False)
        
        if m100_enabled:
            print("Starting M100 motor via relay control (GPIO pin 24)...")
            return self.m100_controller.start_motor_relay(self.hardware_manager)
        else:
            print("Starting relay-controlled motor via GPIO...")
            return self.base_controller.motor.start_motor()

    def _stop_motor_relay(self) -> bool:
        """Stop motor via relay control (GPIO pin 24)"""
        m100_enabled = self.settings.get('m100_config', {}).get('enabled', False)
        
        if m100_enabled:
            print("Stopping M100 motor via relay control (GPIO pin 24)...")
            return self.m100_controller.stop_motor_relay(self.hardware_manager)
        else:
            print("Stopping relay-controlled motor via GPIO...")
            return self.base_controller.motor.stop_motor()

    def stop_test(self, reason: str = "User requested") -> bool:
        """Enhanced test stop with relay control"""
        try:
            # Stop motor via relay control
            if self.settings.get('m100_config', {}).get('enabled', False):
                self.m100_controller.stop_motor_relay(self.hardware_manager)
            
            # Use base controller stop functionality
            return self.base_controller.stop_test(reason)
            
        except Exception as e:
            print(f"Error during enhanced test stop: {e}")
            self._emergency_cleanup()
            return False

    def _emergency_cleanup(self):
        """Emergency cleanup procedure with relay control"""
        try:
            # Stop motor via relay immediately
            if self.hardware_manager and hasattr(self.hardware_manager, 'output_lines'):
                self.hardware_manager.output_lines['relay_control_h300'].set_value(0)
                print("Emergency stop via relay control executed")
            
            # Additional M100 emergency stop via relay
            if self.m100_controller:
                self.m100_controller._emergency_stop_relay(self.hardware_manager)
            
            # Use base controller emergency stop
            self.base_controller.emergency_stop("Enhanced controller emergency")
            
        except Exception as e:
            print(f"Error during emergency cleanup: {e}")

    def get_test_status(self) -> Dict[str, Any]:
        """Get enhanced test status including M100 data"""
        base_status = self.base_controller.get_test_status()
        
        if self.settings.get('m100_config', {}).get('enabled', False):
            m100_data = self.m100_controller.get_motor_data()
            base_status['m100_status'] = m100_data
            base_status['m100_stats'] = self.m100_controller.get_communication_stats()
            base_status['motor_control_method'] = 'relay_gpio_pin_24'
        
        return base_status


# Settings integration
def update_settings_with_m100(settings_manager):
    """Update settings manager with M100 configuration"""
    m100_defaults = {
        'm100_config': {
            'enabled': False,
            'auto_frequency': False,
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
            'slave_address': 1,
            'default_frequency': 25.0,
            'frequency_range': {'min': 0.5, 'max': 60.0}
        }
    }
    
    # Merge with existing settings
    current_settings = settings_manager.settings
    for key, value in m100_defaults.items():
        if key not in current_settings:
            current_settings[key] = value
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if sub_key not in current_settings[key]:
                    current_settings[key][sub_key] = sub_value
    
    settings_manager.save_settings()
    print("Settings updated with M100 configuration")


# Explicitly export the main classes
__all__ = ['M100Controller', 'M100Config', 'M100Status', 'ModbusException']


if __name__ == "__main__":
    # Test M100 controller functionality
    config = M100Config(port='/dev/ttyUSB0', baudrate=9600)
    controller = M100Controller(config)
    
    try:
        if controller.connect():
            print("Testing M100 communication...")
            
            # Test status reading
            status = controller.read_status()
            print(f"Motor status: {status}")
            
            # Test frequency setting
            if controller.set_frequency(25.0):
                print("Frequency set successfully")
            
            # Print statistics
            stats = controller.get_communication_stats()
            print(f"Communication stats: {stats}")
            
    finally:
        controller.disconnect()
