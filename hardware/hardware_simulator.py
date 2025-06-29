"""
Hardware Simulator for Development and Testing

This module provides a simulation of the hardware components for development
and testing purposes when physical hardware is not available.
"""

import time
import threading
import random
import logging
from typing import Dict, Any
from queue import Queue


class MockGPIOLine:
    """Mock GPIO line for simulation"""
    
    def __init__(self, pin: int, direction: str = "input", initial_value: int = 0):
        self.pin = pin
        self.direction = direction
        self.value = initial_value
        self.inverted = False
        
    def get_value(self) -> int:
        """Get simulated GPIO value"""
        return self.value
        
    def set_value(self, value: int):
        """Set simulated GPIO value"""
        if self.direction == "output":
            self.value = value
            logging.debug(f"GPIO Pin {self.pin} set to {value}")
        else:
            logging.warning(f"Attempting to set input pin {self.pin}")
            
    def request(self, consumer: str, type: Any, flags: Any = None):
        """Mock GPIO request"""
        logging.debug(f"GPIO Pin {self.pin} requested by {consumer}")
        
    def release(self):
        """Mock GPIO release"""
        logging.debug(f"GPIO Pin {self.pin} released")


class MockChip:
    """Mock GPIO chip for simulation"""
    
    def __init__(self):
        self.lines = {}
        
    def get_line(self, pin: int) -> MockGPIOLine:
        """Get mock GPIO line"""
        if pin not in self.lines:
            self.lines[pin] = MockGPIOLine(pin)
        return self.lines[pin]


class MockADC:
    """Mock ADC for pressure simulation"""
    
    def __init__(self):
        self.base_pressure = 0.0
        self.noise_level = 0.05
        self.pressure_trend = 0.0
        self._test_running = False
        
    def read_adc(self, channel: int, gain: int = 1) -> int:
        """Simulate ADC reading with realistic pressure values"""
        # Simulate pressure changes during test
        if hasattr(self, '_test_running') and self._test_running:
            # Gradually increase pressure during test
            self.base_pressure = min(2.5, self.base_pressure + 0.02)
        else:
            # Ambient pressure when not testing
            self.base_pressure = max(0.0, self.base_pressure - 0.01)
            
        # Add some realistic noise
        noise = random.uniform(-self.noise_level, self.noise_level)
        pressure = max(0.0, self.base_pressure + noise)
        
        # Convert to ADC value (0-4.096V range, 16-bit)
        voltage = (pressure + 0.579) / 1.286  # Reverse calibration
        adc_value = int((voltage / 4.096) * 32767)
        
        return max(0, min(32767, adc_value))


class HardwareSimulator:
    """
    Hardware simulator that mimics the real HardwareManager interface
    """
    
    def __init__(self):
        """Initialize hardware simulator"""
        self.logger = logging.getLogger(__name__)
        
        # GPIO simulation
        self.chip = MockChip()
        self.input_lines = {}
        self.output_lines = {}
        
        # ADC simulation
        self.adc = MockADC()
        self.adc_channel = 0
        self.adc_gain = 1
        self.voltage_multiplier = 1.286
        self.voltage_offset = -0.579
        
        # State simulation
        self.emergency_stop = False
        self.is_running = False
        self.pressure_queue = Queue()
        
        # Simulation state
        self.actuator_position = 0  # 0 = home, 100 = max
        self.door_closed = True
        self.tank_level_ok = True
        self.motor_running = False
        
        # GPIO pin configuration (same as real hardware)
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
        
        self.logger.info("Hardware simulator initialized")

    def init_gpio(self) -> bool:
        """Initialize simulated GPIO"""
        try:
            self.logger.info("Initializing simulated GPIO...")
            
            # Initialize input pins
            input_pins = ["emergency_btn", "door_close", "tank_min", "start_button", 
                          "actuator_min", "actuator_max"]
                          
            for pin_name in input_pins:
                pin_info = self.gpio_pins[pin_name]
                line = self.chip.get_line(pin_info["pin"])
                line.direction = "input"
                
                # Set initial realistic values
                if pin_name == "door_close":
                    line.value = 1  # Door closed
                elif pin_name == "tank_min":
                    line.value = 1  # Tank OK
                elif pin_name == "actuator_min":
                    line.value = 1  # At home position
                elif pin_name == "actuator_max":
                    line.value = 0  # Not at max
                else:
                    line.value = 0
                    
                self.input_lines[pin_name] = line
                self.logger.debug(f"Simulated input {pin_name}: {line.value}")
            
            # Initialize output pins
            output_pins = ["stepper_pulse", "stepper_dir", "relay_control_h300", "stepper_enable"]
            
            for pin_name in output_pins:
                pin_info = self.gpio_pins[pin_name]
                line = self.chip.get_line(pin_info["pin"])
                line.direction = "output"
                line.value = 0
                self.output_lines[pin_name] = line
                
            self.logger.info("Simulated GPIO initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Simulated GPIO initialization failed: {e}")
            return False

    def init_adc(self) -> bool:
        """Initialize simulated ADC"""
        try:
            self.logger.info("Initializing simulated ADC...")
            
            # Test simulated ADC
            test_reading = self.read_pressure()
            if test_reading is None:
                raise RuntimeError("Simulated ADC test failed")
                
            self.logger.info(f"Simulated ADC initialized. Test reading: {test_reading:.2f} bar")
            return True
            
        except Exception as e:
            self.logger.error(f"Simulated ADC initialization failed: {e}")
            return False

    def read_pressure(self) -> float:
        """Simulate pressure reading"""
        try:
            raw = self.adc.read_adc(self.adc_channel, gain=self.adc_gain)
            voltage = (raw / 32767.0) * 4.096
            pressure = max(0, (voltage * self.voltage_multiplier) + self.voltage_offset - 0.2)
            
            # Add to queue for monitoring
            if not self.pressure_queue.full():
                self.pressure_queue.put(pressure)
                
            return pressure
            
        except Exception as e:
            self.logger.error(f"Error reading simulated pressure: {e}")
            return 0.0

    def simulate_motor_movement(self, target_position: int):
        """Simulate stepper motor movement"""
        def move():
            steps = abs(target_position - self.actuator_position)
            step_time = 0.002  # 2ms per step
            
            for i in range(steps):
                if target_position > self.actuator_position:
                    self.actuator_position += 1
                else:
                    self.actuator_position -= 1
                    
                # Update limit switches
                self.input_lines['actuator_min'].value = 1 if self.actuator_position <= 0 else 0
                self.input_lines['actuator_max'].value = 1 if self.actuator_position >= 100 else 0
                
                time.sleep(step_time)
                
        # Run movement simulation in background
        threading.Thread(target=move, daemon=True).start()

    def simulate_test_pressure_buildup(self):
        """Simulate pressure building up during test"""
        self.adc._test_running = True
        
        def pressure_buildup():
            while self.motor_running and self.adc._test_running:
                # Simulate pressure increase
                current_pressure = self.read_pressure()
                if current_pressure < 2.5:  # Target pressure
                    self.adc.base_pressure = min(2.5, self.adc.base_pressure + 0.05)
                time.sleep(0.5)
                
        threading.Thread(target=pressure_buildup, daemon=True).start()

    def cleanup(self):
        """Cleanup simulated hardware"""
        try:
            self.logger.info("Cleaning up simulated hardware...")
            
            # Stop any simulations
            self.adc._test_running = False
            self.motor_running = False
            
            # Reset outputs
            for line in self.output_lines.values():
                line.set_value(0)
                
            # Reset position
            self.actuator_position = 0
            self.input_lines['actuator_min'].value = 1
            self.input_lines['actuator_max'].value = 0
            
            self.logger.info("Simulated hardware cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during simulated cleanup: {e}")

    def check_safety_conditions(self) -> tuple:
        """Simulate safety condition checking"""
        try:
            # Check door
            if not self.input_lines["door_close"].get_value():
                return False, "Door must be closed"
                
            # Check emergency stop
            if self.input_lines["emergency_btn"].get_value():
                return False, "Emergency stop activated"
                
            # Check tank level
            if not self.input_lines["tank_min"].get_value():
                return False, "Tank level too low"
                
            return True, "All safety conditions met"
            
        except Exception as e:
            return False, f"Safety check error: {e}"

    def simulate_emergency_condition(self):
        """Simulate emergency condition for testing"""
        self.logger.warning("Simulating emergency condition")
        self.input_lines["emergency_btn"].value = 1
        self.emergency_stop = True

    def reset_emergency(self):
        """Reset emergency condition"""
        self.logger.info("Resetting emergency condition")
        self.input_lines["emergency_btn"].value = 0
        self.emergency_stop = False

    def simulate_door_open(self):
        """Simulate door opening"""
        self.logger.info("Simulating door open")
        self.input_lines["door_close"].value = 0
        self.door_closed = False

    def simulate_door_close(self):
        """Simulate door closing"""
        self.logger.info("Simulating door close")
        self.input_lines["door_close"].value = 1
        self.door_closed = True

    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        return {
            "actuator_position": self.actuator_position,
            "door_closed": self.door_closed,
            "tank_level_ok": self.tank_level_ok,
            "motor_running": self.motor_running,
            "emergency_stop": self.emergency_stop,
            "current_pressure": self.read_pressure(),
            "gpio_states": {
                name: line.get_value() 
                for name, line in {**self.input_lines, **self.output_lines}.items()
            }
        }

    def print_simulation_status(self):
        """Print current simulation status for debugging"""
        status = self.get_simulation_status()
        print("\n=== Hardware Simulation Status ===")
        print(f"Actuator Position: {status['actuator_position']}")
        print(f"Door Closed: {status['door_closed']}")
        print(f"Motor Running: {status['motor_running']}")
        print(f"Current Pressure: {status['current_pressure']:.2f} bar")
        print(f"Emergency Stop: {status['emergency_stop']}")
        print("\nGPIO States:")
        for name, value in status['gpio_states'].items():
            print(f"  {name}: {value}")
        print("=" * 35)


# Additional simulation utilities
class SimulationController:
    """Controller for managing hardware simulation scenarios"""
    
    def __init__(self, hardware_simulator: HardwareSimulator):
        self.hardware = hardware_simulator
        self.scenarios = {
            "normal_operation": self.scenario_normal_operation,
            "emergency_stop": self.scenario_emergency_stop,
            "door_open": self.scenario_door_open,
            "sensor_failure": self.scenario_sensor_failure,
            "successful_test": self.scenario_successful_test
        }
        
    def run_scenario(self, scenario_name: str):
        """Run a specific test scenario"""
        if scenario_name in self.scenarios:
            print(f"Running scenario: {scenario_name}")
            self.scenarios[scenario_name]()
        else:
            print(f"Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {list(self.scenarios.keys())}")
            
    def scenario_normal_operation(self):
        """Simulate normal operation conditions"""
        self.hardware.simulate_door_close()
        self.hardware.reset_emergency()
        
    def scenario_emergency_stop(self):
        """Simulate emergency stop condition"""
        self.hardware.simulate_emergency_condition()
        
    def scenario_door_open(self):
        """Simulate door open condition"""
        self.hardware.simulate_door_open()
        
    def scenario_sensor_failure(self):
        """Simulate sensor failure"""
        self.hardware.input_lines["tank_min"].value = 0
        
    def scenario_successful_test(self):
        """Simulate a complete successful test"""
        self.scenario_normal_operation()
        # Additional test simulation logic can be added here


if __name__ == "__main__":
    # Test the hardware simulator
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing Hardware Simulator...")
    
    # Create simulator
    sim = HardwareSimulator()
    
    # Initialize
    if sim.init_gpio() and sim.init_adc():
        print("Simulator initialized successfully")
        
        # Test pressure reading
        pressure = sim.read_pressure()
        print(f"Pressure reading: {pressure:.2f} bar")
        
        # Test GPIO output
        sim.output_lines['stepper_enable'].set_value(1)
        time.sleep(0.5)
        sim.output_lines['stepper_enable'].set_value(0)
        print("GPIO output test completed")
        
        # Test motor control
        sim.simulate_motor_movement(50)
        time.sleep(1)
        sim.simulate_motor_movement(0)
        
        print("All simulator tests completed")
        
    else:
        print("Simulator initialization failed")