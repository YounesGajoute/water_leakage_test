# Air Leakage Test Application (TechMac)

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Raspberry Pi](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)
[![Hardware: Industrial](https://img.shields.io/badge/hardware-Industrial-orange.svg)](https://github.com/your-org/air-leakage-test)

> **Professional Industrial Air Leakage Testing System**
> 
> A comprehensive, safety-critical industrial application for automated air leakage testing with full hardware control, real-time monitoring, and comprehensive data logging capabilities.

## 🏭 Project Overview

The Air Leakage Test Application (TechMac) is a professional-grade industrial automation system designed for automated air leakage testing in manufacturing environments. Built specifically for Raspberry Pi with GPIO control, this application provides precise control over stepper motors, pressure sensors, and safety systems while maintaining comprehensive data logging and export capabilities.

### 🎯 Key Features

- **🔧 Hardware Control**: Direct GPIO control for stepper motors, pressure sensors, and safety systems
- **🛡️ Safety Systems**: Comprehensive safety monitoring with emergency shutdown capabilities
- **🤖 Test Automation**: Fully automated test sequences with configurable parameters
- **📊 Data Management**: Real-time data logging with export to multiple formats (CSV, JSON, Excel)
- **🖥️ Touchscreen UI**: Fullscreen Tkinter interface optimized for industrial touchscreens
- **🔍 Hardware Simulation**: Complete hardware simulation mode for development and testing
- **📈 Real-time Monitoring**: Live pressure graphs, test status, and system health monitoring
- **⚙️ Modular Architecture**: Extensible design for custom hardware integration
- **🔒 Industrial Security**: Built-in security features for industrial control systems

## 🖥️ System Requirements

### Hardware Requirements
- **Raspberry Pi 4** (4GB RAM recommended) or **Raspberry Pi 3B+**
- **Touchscreen Display** (7" or larger recommended)
- **Stepper Motors** with appropriate drivers
- **Pressure Sensors** (ADC-compatible)
- **GPIO Expansion Board** (optional, for additional I/O)
- **Power Supply** (5V/3A minimum for Pi + peripherals)

### Software Requirements
- **Python 3.7+** (3.8+ recommended)
- **Raspberry Pi OS** (Bullseye or newer)
- **GPIO Libraries**: `gpiod`, `RPi.GPIO`
- **Display**: X11 or Wayland support

### Optional Hardware
- **ADC Module** (ADS1115/ADS1015 for high-precision pressure reading)
- **Real-time Clock** (RTC) module for timestamp accuracy
- **Network Connectivity** for remote monitoring
- **UPS** for power backup

## 🚀 Installation

### Production Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/air-leakage-test.git
   cd air-leakage-test
   ```

2. **Install System Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv python3-tk
   sudo apt install libgpiod-dev libgpiod2
   ```

3. **Setup Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Hardware**
   ```bash
   # Enable I2C and SPI interfaces
   sudo raspi-config
   # Navigate to Interface Options > I2C > Enable
   # Navigate to Interface Options > SPI > Enable
   ```

5. **Setup Permissions**
   ```bash
   # Add user to gpio group
   sudo usermod -a -G gpio $USER
   # Grant access to I2C devices
   sudo chmod 666 /dev/i2c-1
   ```

6. **Configure Application**
   ```bash
   cp config/settings.example.json config/settings.json
   # Edit settings.json with your hardware configuration
   ```

7. **Run the Application**
   ```bash
   python main.py
   ```

### Development Installation

1. **Clone with Development Tools**
   ```bash
   git clone https://github.com/your-org/air-leakage-test.git
   cd air-leakage-test
   ```

2. **Install Development Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Run Tests**
   ```bash
   pytest tests/
   ```

## 📖 Usage Guide

### Quick Start

1. **Power On**: Connect all hardware components and power on the Raspberry Pi
2. **Launch Application**: Run `python main.py` or use the desktop shortcut
3. **Calibrate Sensors**: Navigate to Settings > Calibration to calibrate pressure sensors
4. **Configure Test Parameters**: Set test pressure, duration, and tolerance in Test Configuration
5. **Run Test**: Select test mode and press "Start Test"
6. **Monitor Results**: View real-time pressure graphs and test status
7. **Export Data**: Save test results to CSV, JSON, or Excel format

### Test Modes

- **Manual Test**: Single test with user-defined parameters
- **Batch Test**: Multiple tests with automated sequencing
- **Continuous Test**: Ongoing monitoring with configurable intervals
- **Calibration Test**: Sensor calibration and validation

### Safety Features

- **Emergency Stop**: Hardware and software emergency stop buttons
- **Pressure Monitoring**: Real-time pressure monitoring with safety limits
- **System Health**: Continuous monitoring of hardware status
- **Fault Detection**: Automatic detection and reporting of hardware faults

## 🔧 Configuration

### Hardware Configuration

Edit `config/settings.json` to configure your hardware setup:

```json
{
  "hardware": {
    "stepper_motors": {
      "motor1": {
        "pins": [17, 18, 27, 22],
        "steps_per_rev": 200,
        "max_speed": 1000
      }
    },
    "pressure_sensors": {
      "sensor1": {
        "adc_channel": 0,
        "calibration_factor": 1.0,
        "offset": 0.0
      }
    },
    "safety_systems": {
      "emergency_stop_pin": 23,
      "pressure_limit": 100.0
    }
  }
}
```

### Test Parameters

Configure test parameters in the UI or settings file:

- **Test Pressure**: Target pressure for leakage testing
- **Test Duration**: Duration of each test cycle
- **Tolerance**: Acceptable pressure drop percentage
- **Sample Rate**: Data sampling frequency
- **Safety Limits**: Maximum pressure and time limits

## 🛠️ Hardware Setup

### Wiring Diagram

```
Raspberry Pi 4
├── GPIO 17-22 → Stepper Motor Driver
├── I2C SDA/SCL → ADC Module (ADS1115)
├── GPIO 23 → Emergency Stop Button
├── 5V/3.3V → Power Distribution
└── GND → Common Ground
```

### Component Connections

1. **Stepper Motors**
   - Connect motor drivers to GPIO pins 17, 18, 27, 22
   - Ensure proper power supply (12V recommended)
   - Add flyback diodes for protection

2. **Pressure Sensors**
   - Connect to ADC module via I2C
   - Use appropriate voltage dividers if needed
   - Calibrate sensors before use

3. **Safety Systems**
   - Emergency stop button to GPIO 23
   - Pressure relief valves for overpressure protection
   - Status LEDs for system indication

## 🔍 Troubleshooting

### Common Issues

**GPIO Access Denied**
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Reboot or log out/in
```

**I2C Device Not Found**
```bash
# Check I2C bus
i2cdetect -y 1
# Enable I2C in raspi-config
sudo raspi-config
```

**Pressure Sensor Reading Errors**
- Check wiring connections
- Verify ADC address (default: 0x48)
- Calibrate sensor offset and gain

**Stepper Motor Issues**
- Verify motor driver connections
- Check power supply voltage
- Test individual motor phases

### Debug Mode

Enable debug logging in `config/settings.json`:

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/debug.log"
  }
}
```

### Hardware Simulation

For development without hardware:

```bash
python main.py --simulation-mode
```

## 🤝 Contributing

We welcome contributions from the industrial automation community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code style and standards
- Development setup
- Testing requirements
- Pull request process
- Hardware simulation for contributors

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛡️ Security

For security concerns, please see our [Security Policy](SECURITY.md) or contact us directly.

## 📞 Support

### Documentation
- [User Manual](docs/user-manual.md)
- [Hardware Setup Guide](docs/hardware-setup.md)
- [API Documentation](docs/api.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

### Community
- [GitHub Issues](https://github.com/your-org/air-leakage-test/issues)
- [Discussions](https://github.com/your-org/air-leakage-test/discussions)
- [Wiki](https://github.com/your-org/air-leakage-test/wiki)

### Contact
- **Email**: support@techmac.com
- **Technical Support**: tech-support@techmac.com
- **Sales**: sales@techmac.com

## 🏢 About TechMac

TechMac is a leading provider of industrial automation solutions, specializing in precision testing and measurement systems. Our Air Leakage Test Application represents years of experience in industrial automation and quality control systems.

---

**⚠️ Safety Notice**: This is industrial control software. Always follow proper safety procedures and ensure all hardware is properly installed and tested before operation. Never operate without proper training and safety equipment.

**🔧 Industrial Use**: This application is designed for industrial environments. Ensure compliance with local safety regulations and industry standards. 