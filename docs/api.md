# API Documentation

## Core Modules

### Hardware Interface

#### StepperMotor
```python
class StepperMotor:
    def __init__(self, pins: List[int], steps_per_rev: int = 200)
    def move(self, steps: int, speed: int) -> bool
    def stop(self) -> None
    def set_position(self, position: int) -> None
    def get_position(self) -> int
```

#### PressureSensor
```python
class PressureSensor:
    def __init__(self, adc_channel: int, calibration_factor: float = 1.0)
    def read_pressure(self) -> Optional[float]
    def calibrate(self, known_pressure: float) -> bool
    def get_calibration_data(self) -> Dict[str, float]
```

#### SafetySystem
```python
class SafetySystem:
    def __init__(self, emergency_stop_pin: int)
    def trigger_emergency_stop(self) -> None
    def is_emergency_active(self) -> bool
    def reset_emergency_stop(self) -> bool
    def monitor_pressure(self, pressure: float) -> bool
```

### Test Management

#### TestController
```python
class TestController:
    def __init__(self, config: Dict[str, Any])
    def start_test(self, test_type: str) -> bool
    def stop_test(self) -> None
    def pause_test(self) -> None
    def get_test_status(self) -> Dict[str, Any]
    def get_test_results(self) -> Dict[str, Any]
```

#### DataLogger
```python
class DataLogger:
    def __init__(self, log_file: str)
    def log_data(self, data: Dict[str, Any]) -> None
    def export_data(self, format: str) -> str
    def get_test_history(self) -> List[Dict[str, Any]]
```

## Configuration

### Settings Structure
```json
{
  "hardware": {
    "stepper_motors": {},
    "pressure_sensors": {},
    "safety_systems": {}
  },
  "test": {
    "parameters": {},
    "sequences": {}
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log"
  }
}
```

## Error Handling

### Custom Exceptions
```python
class HardwareError(Exception): pass
class SafetyError(Exception): pass
class TestError(Exception): pass
class ConfigurationError(Exception): pass
```

## Usage Examples

### Basic Test
```python
from core.test_controller import TestController
from core.config import Config

config = Config()
controller = TestController(config)

# Start a manual test
success = controller.start_test("manual")
if success:
    results = controller.get_test_results()
    print(f"Test completed: {results['status']}")
```

### Hardware Control
```python
from hardware.stepper_motor import StepperMotor
from hardware.pressure_sensor import PressureSensor

# Control stepper motor
motor = StepperMotor([17, 18, 27, 22])
motor.move(100, 1000)  # 100 steps at 1000 steps/sec

# Read pressure
sensor = PressureSensor(0)
pressure = sensor.read_pressure()
print(f"Pressure: {pressure} PSI")
```

---

**📚 Full Documentation**: See [User Manual](user-manual.md) and [Hardware Setup Guide](hardware-setup.md) for complete details. 