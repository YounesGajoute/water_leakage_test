# Contributing to Air Leakage Test Application

Thank you for your interest in contributing to the Air Leakage Test Application! This document provides guidelines for contributing to this industrial automation project.

## 🏭 Project Overview

This is an industrial-grade application for automated air leakage testing. As such, we maintain high standards for code quality, safety, and reliability. All contributions must follow industrial software development best practices.

## 🚀 Getting Started

### Prerequisites

- Python 3.7+ (3.8+ recommended)
- Git
- Raspberry Pi (for hardware testing)
- Basic understanding of industrial automation concepts

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/air-leakage-test.git
   cd air-leakage-test
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Hardware Simulation Mode**
   ```bash
   # For development without hardware
   python main.py --simulation-mode
   ```

## 📋 Code Style and Standards

### Python Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with the following modifications:

- **Line Length**: 88 characters (Black default)
- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: Google-style docstrings for all public functions
- **Imports**: Organized with `isort`

### Code Formatting

We use automated tools to maintain code quality:

```bash
# Format code
black .
isort .

# Check code quality
flake8 .
mypy .

# Run tests
pytest
```

### Type Hints

All functions must include type hints:

```python
from typing import Optional, List, Dict, Any
import numpy as np

def read_pressure_sensor(sensor_id: str, timeout: float = 1.0) -> Optional[float]:
    """
    Read pressure from specified sensor.
    
    Args:
        sensor_id: Unique identifier for the sensor
        timeout: Maximum time to wait for reading in seconds
        
    Returns:
        Pressure reading in PSI, or None if reading failed
    """
    # Implementation here
    pass
```

### Documentation Standards

- **Module Docstrings**: Required for all modules
- **Function Docstrings**: Google-style for all public functions
- **Inline Comments**: For complex logic
- **README Updates**: When adding new features

## 🧪 Testing Requirements

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for module interactions
├── hardware/       # Hardware-specific tests
├── simulation/     # Hardware simulation tests
└── safety/         # Safety system tests
```

### Writing Tests

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test module interactions
3. **Hardware Tests**: Test with actual hardware (when available)
4. **Simulation Tests**: Test with mock hardware

### Test Examples

```python
import pytest
from unittest.mock import Mock, patch
from core.pressure_sensor import PressureSensor

class TestPressureSensor:
    """Test cases for PressureSensor class."""
    
    def test_sensor_initialization(self):
        """Test sensor initialization with valid parameters."""
        sensor = PressureSensor(sensor_id="test_sensor", adc_channel=0)
        assert sensor.sensor_id == "test_sensor"
        assert sensor.adc_channel == 0
        
    @patch('hardware.adc.ADS1115')
    def test_pressure_reading_simulation(self, mock_adc):
        """Test pressure reading in simulation mode."""
        mock_adc.return_value.read_adc.return_value = 2048
        sensor = PressureSensor(sensor_id="test", simulation_mode=True)
        reading = sensor.read_pressure()
        assert reading is not None
        assert 0 <= reading <= 100  # Expected range in PSI
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=hardware --cov=ui

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/hardware/ -m "hardware"
pytest tests/simulation/ -m "simulation"

# Run tests in parallel
pytest -n auto
```

## 🔧 Hardware Simulation

### Simulation Mode

For contributors without access to hardware, we provide comprehensive simulation:

```python
# Enable simulation mode
python main.py --simulation-mode

# Or in code
from core.config import Config
config = Config()
config.simulation_mode = True
```

### Mock Hardware Components

```python
from hardware.mock_components import MockStepperMotor, MockPressureSensor

# Use mock components in tests
motor = MockStepperMotor()
sensor = MockPressureSensor()
```

### Hardware Testing Guidelines

If you have access to hardware:

1. **Safety First**: Always follow safety procedures
2. **Calibration**: Calibrate sensors before testing
3. **Documentation**: Document hardware configuration
4. **Validation**: Validate against known good measurements

## 🔒 Safety Considerations

### Safety-Critical Code

- **Input Validation**: Validate all user inputs and sensor readings
- **Error Handling**: Implement comprehensive error handling
- **Safety Limits**: Always check safety limits before operations
- **Emergency Procedures**: Test emergency shutdown procedures

### Safety Testing

```python
def test_emergency_stop_functionality():
    """Test emergency stop functionality."""
    safety_system = SafetySystem()
    
    # Simulate emergency condition
    safety_system.trigger_emergency_stop()
    
    # Verify all systems are stopped
    assert safety_system.is_emergency_active()
    assert not safety_system.is_motor_running()
    assert safety_system.get_pressure() < safety_system.safety_limit
```

## 📝 Pull Request Process

### Before Submitting

1. **Code Quality**: Ensure all tests pass
2. **Documentation**: Update relevant documentation
3. **Type Checking**: Run mypy and fix type issues
4. **Security**: Run security scans (bandit, safety)

### PR Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass (unit, integration, simulation)
- [ ] Type hints are complete and correct
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Hardware simulation works (if applicable)
- [ ] Safety systems are tested

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Hardware simulation works
- [ ] Safety systems tested

## Hardware Testing
- [ ] Tested on actual hardware (if applicable)
- [ ] Hardware simulation mode works
- [ ] No hardware-specific issues

## Safety Impact
- [ ] No impact on safety systems
- [ ] Safety systems enhanced
- [ ] Safety systems modified (requires review)
```

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, include:

- **Hardware Configuration**: Raspberry Pi model, connected hardware
- **Software Version**: Python version, application version
- **Error Messages**: Complete error traceback
- **Steps to Reproduce**: Detailed reproduction steps
- **Expected vs Actual**: Expected vs actual behavior
- **Logs**: Relevant log files

### Feature Requests

For feature requests:

- **Use Case**: Describe the use case
- **Requirements**: Specific requirements
- **Impact**: Impact on existing functionality
- **Safety Considerations**: Any safety implications

## 🔍 Code Review Process

### Review Criteria

1. **Code Quality**: Readability, maintainability
2. **Safety**: Safety implications and testing
3. **Performance**: Impact on system performance
4. **Compatibility**: Hardware compatibility
5. **Documentation**: Code and user documentation

### Review Process

1. **Automated Checks**: CI/CD pipeline validation
2. **Peer Review**: At least one reviewer approval
3. **Safety Review**: Safety-critical changes require additional review
4. **Hardware Testing**: Hardware changes require hardware testing

## 📚 Documentation

### Documentation Standards

- **User Documentation**: Clear, step-by-step instructions
- **API Documentation**: Complete API reference
- **Hardware Documentation**: Wiring diagrams, setup instructions
- **Safety Documentation**: Safety procedures and warnings

### Documentation Updates

When updating documentation:

1. **User Impact**: Consider user impact of changes
2. **Screenshots**: Update screenshots for UI changes
3. **Examples**: Provide working examples
4. **Troubleshooting**: Update troubleshooting guides

## 🏢 Industrial Standards

### Compliance

- **Safety Standards**: Follow relevant safety standards
- **Quality Standards**: Maintain high quality standards
- **Documentation**: Comprehensive documentation
- **Testing**: Thorough testing procedures

### Best Practices

- **Defensive Programming**: Assume hardware can fail
- **Error Recovery**: Implement error recovery mechanisms
- **Logging**: Comprehensive logging for debugging
- **Monitoring**: Real-time system monitoring

## 🤝 Community Guidelines

### Communication

- **Respectful**: Be respectful to all contributors
- **Constructive**: Provide constructive feedback
- **Professional**: Maintain professional communication
- **Helpful**: Help other contributors

### Support

- **Questions**: Ask questions in discussions
- **Help**: Offer help to other contributors
- **Mentoring**: Mentor new contributors
- **Documentation**: Improve documentation

## 📞 Contact

For questions about contributing:

- **GitHub Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Email**: development@techmac.com for private matters

## 🙏 Acknowledgments

Thank you for contributing to industrial automation and helping make this application safer and more reliable for industrial use!

---

**⚠️ Safety Notice**: Remember that this is industrial software. Always prioritize safety in your contributions and thoroughly test any changes that affect safety-critical systems. 