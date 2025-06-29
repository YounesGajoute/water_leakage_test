# hardware/hardware_manager.py
import threading
import time
from queue import Queue
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any

# Import M100 controller with proper type handling
M100Controller: Optional[Any] = None
M100Config: Optional[Any] = None
M100_AVAILABLE = False

try:
    # Import using the explicit __all__ export
    from hardware.m100_controller import M100Controller, M100Config
    M100_AVAILABLE = True
except (ImportError, AttributeError):
    # If import fails, keep the None values
    M100_AVAILABLE = False
    print("M100 controller not available - serial communication disabled")


class MotorState:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._frequency = 0
        
    @property
    def is_running(self):
        with self._lock:
            return self._running
            
    def set_running(self, state):
        with self._lock:
            self._running = state
            
    @property
    def current_frequency(self):
        with self._lock:
            return self._frequency
            
    def set_frequency(self, freq):
        with self._lock:
            self._frequency = freq


class HardwareManager:
    def __init__(self):
        # GPIO configuration with properties - initialize this first
        self.gpio_pins = {
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
        }

        # Initialize storage for hardware components
        self.chip = None
        self.input_lines = {}
        self.output_lines = {}
        self.adc = None
        
        # M100 controller integration
        self.m100_controller = None
        self.m100_enabled = False
        
        # Initialize state variables
        self.emergency_stop = False
        self.is_running = False
        self.pressure_queue = Queue()

    def init_gpio(self):
        """Initialize GPIO with testing"""
        try:
            import gpiod  # type: ignore
            self.chip = gpiod.Chip('gpiochip0')
            print("\nInitializing GPIO...")

            # Initialize inputs
            input_pins = ["emergency_btn", "door_close", "tank_min", "start_button", 
                          "actuator_min", "actuator_max"]

            for pin_name in input_pins:
                pin_info = self.gpio_pins[pin_name]
                line = self.chip.get_line(pin_info["pin"])
                line.request(
                    consumer=f"monitor_{pin_name}",
                    type=gpiod.LINE_REQ_DIR_IN,
                    flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN
                )
                self.input_lines[pin_name] = line

                # Test read from input
                value = line.get_value()
                print(f"Testing input {pin_name}: {value}")

            # Initialize outputs
            output_pins = ["stepper_pulse", "stepper_dir", "relay_control_h300", "stepper_enable"]

            for pin_name in output_pins:
                pin_info = self.gpio_pins[pin_name]
                line = self.chip.get_line(pin_info["pin"])
                line.request(
                    consumer=f"control_{pin_name}",
                    type=gpiod.LINE_REQ_DIR_OUT
                )
                self.output_lines[pin_name] = line

                # Initialize output to low state
                line.set_value(0)

            print("GPIO initialization completed successfully")
            return True

        except Exception as e:
            print(f"Error during GPIO initialization: {e}")
            return False

    def init_adc(self):
        """Initialize ADC with testing"""
        try:
            import Adafruit_ADS1x15  # type: ignore
            self.adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)

            # ADC configuration
            self.adc_channel = 0
            self.adc_gain = 1
            self.voltage_multiplier = 1.286
            self.voltage_offset = -0.579

            # Test ADC by taking a reading
            test_reading = self.read_pressure()
            if test_reading is None:
                raise RuntimeError("Failed to get initial ADC reading")

            print(f"ADC initialized successfully. Test reading: {test_reading:.2f} bar")
            return True

        except Exception as e:
            print(f"ADC initialization failed: {e}")
            return False

    def init_m100_controller(self, m100_config=None):
        """Initialize M100 motor controller"""
        if not M100_AVAILABLE or M100Config is None or M100Controller is None:
            print("M100 controller not available - skipping initialization")
            return False
        
        try:
            # Use provided config or default
            if m100_config is None:
                m100_config = M100Config()
            
            self.m100_controller = M100Controller(m100_config)
            
            # Attempt to connect
            if self.m100_controller.connect():
                self.m100_enabled = True
                print("M100 controller initialized and connected successfully")
                return True
            else:
                print("M100 controller initialization failed - will use relay control only")
                self.m100_enabled = False
                return False
                
        except Exception as e:
            print(f"Error initializing M100 controller: {e}")
            self.m100_enabled = False
            return False

    def get_m100_status(self):
        """Get M100 controller status"""
        if not self.m100_enabled or not self.m100_controller:
            return {
                'enabled': False,
                'connected': False,
                'status': 'not_available'
            }
        
        try:
            motor_data = self.m100_controller.get_motor_data()
            stats = self.m100_controller.get_communication_stats()
            return {
                'enabled': True,
                'connected': self.m100_controller.connection_established,
                'status': motor_data.get('status', 'unknown'),
                'frequency': motor_data.get('frequency'),
                'error_count': motor_data.get('error_count', 0),
                'communication_stats': stats
            }
        except Exception as e:
            print(f"Error getting M100 status: {e}")
            return {
                'enabled': True,
                'connected': False,
                'status': 'error',
                'error': str(e)
            }

    def set_motor_frequency(self, frequency_hz):
        """Set motor frequency via M100 if available"""
        if not self.m100_enabled or not self.m100_controller:
            print("M100 controller not available for frequency control")
            return False
        
        try:
            return self.m100_controller.set_frequency(frequency_hz)
        except Exception as e:
            print(f"Error setting motor frequency: {e}")
            return False

    def read_pressure(self):
        """Read and validate pressure value"""
        try:
            if self.adc is None:
                print("ADC not initialized.")
                return None
            raw = self.adc.read_adc(self.adc_channel, gain=self.adc_gain)
            voltage = (raw / 32767.0) * 4.096
            if not 0 <= voltage <= 4.096:
                print(f"Invalid voltage reading: {voltage}V")
                return None
            pressure = max(0, (voltage * self.voltage_multiplier) + self.voltage_offset-0.2)
            return pressure
        except Exception as e:
            print(f"Error reading pressure: {e}")
            return None

    def cleanup(self):
        """Clean up hardware resources"""
        try:
            # Disable all outputs
            for line in self.output_lines.values():
                line.set_value(0)
            
            # Disconnect M100 controller
            if self.m100_controller:
                self.m100_controller.disconnect()
                print("M100 controller disconnected")
            
            # Release all lines
            for line in self.input_lines.values():
                line.release()
            for line in self.output_lines.values():
                line.release()
                
            print("Hardware cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def check_safety_conditions(self):
        """Check all safety conditions"""
        try:
            # Check door closure
            if not self.input_lines["door_close"].get_value():
                return False, "Door must be closed"
            
            # Check emergency stop
            if self.input_lines["emergency_btn"].get_value():
                return False, "Emergency stop activated"
            
            return True, "All safety conditions met"
            
        except Exception as e:
            return False, f"Safety check error: {e}"