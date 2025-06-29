# Hardware Setup Guide

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Component Selection](#component-selection)
3. [Wiring Diagrams](#wiring-diagrams)
4. [Installation Steps](#installation-steps)
5. [Testing and Calibration](#testing-and-calibration)
6. [Safety Considerations](#safety-considerations)
7. [Troubleshooting](#troubleshooting)

## Hardware Requirements

### Essential Components

#### Raspberry Pi
- **Model**: Raspberry Pi 4 (4GB RAM recommended) or Raspberry Pi 3B+
- **Power Supply**: 5V/3A minimum (5V/4A recommended)
- **Storage**: 32GB+ microSD card (Class 10 or better)
- **Cooling**: Heat sink and fan for continuous operation

#### Stepper Motors
- **Type**: NEMA 17 or NEMA 23
- **Torque**: 40 oz-in minimum (higher for larger systems)
- **Steps per Revolution**: 200 (standard)
- **Current**: 1.5A per phase (check motor specifications)
- **Driver**: A4988, DRV8825, or TMC2208

#### Pressure Sensors
- **Type**: MPX5050DP, MPX5700, or similar
- **Range**: 0-50 PSI or 0-100 PSI (depending on application)
- **Output**: Analog voltage (0-5V or 0-3.3V)
- **Accuracy**: ±2.5% or better
- **ADC**: ADS1115 or ADS1015 for high precision

#### Emergency Stop System
- **Button**: Industrial emergency stop button (NO/NC)
- **Relay**: Solid-state relay for power control
- **Indicator**: LED status indicators
- **Wiring**: Properly rated cables and connectors

### Optional Components

#### Additional Hardware
- **Real-time Clock**: DS3231 or similar for accurate timestamps
- **Display**: 7" or larger touchscreen display
- **UPS**: Uninterruptible power supply for critical systems
- **Network**: Ethernet or WiFi for remote monitoring
- **Storage**: External USB drive for data backup

#### Safety Equipment
- **Pressure Relief Valves**: Automatic pressure release
- **Flow Control Valves**: Manual or automated flow control
- **Pressure Gauges**: Visual pressure indicators
- **Temperature Sensors**: System temperature monitoring

## Component Selection

### Stepper Motor Selection

#### NEMA 17 Motors
**Advantages**:
- Compact size
- Lower power consumption
- Good for small to medium systems
- Wide availability

**Specifications**:
- Frame size: 42mm x 42mm
- Shaft diameter: 5mm
- Typical torque: 40-60 oz-in
- Current: 1.5-2A per phase

**Recommended Models**:
- 17HS4401 (40 oz-in, 1.5A)
- 17HS4023 (23 oz-in, 1.7A)
- 17HS8401 (84 oz-in, 2A)

#### NEMA 23 Motors
**Advantages**:
- Higher torque
- Better for heavy loads
- More robust construction
- Industrial applications

**Specifications**:
- Frame size: 57mm x 57mm
- Shaft diameter: 6.35mm
- Typical torque: 100-200 oz-in
- Current: 2-3A per phase

**Recommended Models**:
- 23HS22-2804S (100 oz-in, 2A)
- 23HS30-2804S (150 oz-in, 2.5A)
- 23HS45-2804S (200 oz-in, 3A)

### Motor Driver Selection

#### A4988 Driver
**Features**:
- 16 microstep modes
- Current limiting
- Thermal shutdown
- Simple configuration

**Specifications**:
- Voltage: 8-35V
- Current: 2A per phase
- Microstepping: 1/16
- Price: Low

#### DRV8825 Driver
**Features**:
- 32 microstep modes
- Advanced current control
- Better thermal management
- Higher current capacity

**Specifications**:
- Voltage: 8.2-45V
- Current: 2.5A per phase
- Microstepping: 1/32
- Price: Medium

#### TMC2208 Driver
**Features**:
- Silent operation
- Advanced current control
- Stall detection
- High efficiency

**Specifications**:
- Voltage: 4.75-36V
- Current: 1.4A RMS
- Microstepping: 1/256
- Price: High

### Pressure Sensor Selection

#### MPX5050DP
**Features**:
- 0-50 PSI range
- Temperature compensated
- Calibrated output
- Good accuracy

**Specifications**:
- Pressure range: 0-50 PSI
- Output: 0.5-4.5V
- Accuracy: ±2.5%
- Response time: 1ms

#### MPX5700
**Features**:
- 0-100 PSI range
- Higher pressure capability
- Industrial grade
- Temperature compensation

**Specifications**:
- Pressure range: 0-100 PSI
- Output: 0.5-4.5V
- Accuracy: ±2.5%
- Response time: 1ms

### ADC Module Selection

#### ADS1115
**Features**:
- 16-bit resolution
- 4 single-ended channels
- I2C interface
- Programmable gain

**Specifications**:
- Resolution: 16-bit
- Channels: 4 single-ended
- Interface: I2C
- Sample rate: 8-860 SPS
- Price: Medium

#### ADS1015
**Features**:
- 12-bit resolution
- 4 single-ended channels
- I2C interface
- Lower cost

**Specifications**:
- Resolution: 12-bit
- Channels: 4 single-ended
- Interface: I2C
- Sample rate: 128-3300 SPS
- Price: Low

## Wiring Diagrams

### Basic System Wiring

```
Raspberry Pi 4
├── GPIO 17 → Stepper Driver A4988 (STEP)
├── GPIO 18 → Stepper Driver A4988 (DIR)
├── GPIO 27 → Stepper Driver A4988 (ENABLE)
├── GPIO 22 → Stepper Driver A4988 (MS1)
├── GPIO 23 → Emergency Stop Button (NO)
├── GPIO 24 → Status LED
├── I2C SDA → ADS1115 (SDA)
├── I2C SCL → ADS1115 (SCL)
├── 5V → Power Distribution
├── 3.3V → ADS1115 (VDD)
└── GND → Common Ground
```

### Stepper Motor Wiring

```
Stepper Motor (NEMA 17)
├── Coil A+ → A4988 Driver (A+)
├── Coil A- → A4988 Driver (A-)
├── Coil B+ → A4988 Driver (B+)
└── Coil B- → A4988 Driver (B-)

A4988 Driver
├── STEP → GPIO 17
├── DIR → GPIO 18
├── ENABLE → GPIO 27
├── MS1 → GPIO 22
├── MS2 → GND (1/16 microstepping)
├── MS3 → GND
├── RESET → SLEEP (connected together)
├── SLEEP → GPIO 27
├── VDD → 5V (logic power)
├── VMOT → 12V (motor power)
└── GND → Common Ground
```

### Pressure Sensor Wiring

```
Pressure Sensor (MPX5050DP)
├── VCC → 5V
├── GND → GND
└── VOUT → ADS1115 (A0)

ADS1115
├── VDD → 3.3V
├── GND → GND
├── SDA → I2C SDA
├── SCL → I2C SCL
├── A0 → Pressure Sensor VOUT
├── A1 → (unused)
├── A2 → (unused)
└── A3 → (unused)
```

### Emergency Stop Wiring

```
Emergency Stop Button
├── NO Contact → GPIO 23
├── NC Contact → (unused)
├── Common → 3.3V
└── LED → GPIO 24 (via current limiting resistor)
```

## Installation Steps

### Step 1: Prepare Raspberry Pi

1. **Install Operating System**
   ```bash
   # Download Raspberry Pi OS
   # Flash to microSD card
   # Enable SSH and configure network
   ```

2. **Enable Required Interfaces**
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   # Interface Options → SPI → Enable
   # Interface Options → Serial → Disable
   ```

3. **Install System Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv python3-tk
   sudo apt install libgpiod-dev libgpiod2
   sudo apt install i2c-tools
   ```

### Step 2: Install Hardware Components

1. **Mount Raspberry Pi**
   - Use proper mounting bracket
   - Ensure adequate ventilation
   - Secure all connections

2. **Connect Power Supply**
   - Use 5V/3A minimum power supply
   - Connect to power distribution board
   - Verify stable voltage

3. **Install Stepper Motors**
   - Mount motors securely
   - Connect to drivers
   - Test basic movement

4. **Install Pressure Sensors**
   - Mount sensors in appropriate location
   - Connect to ADC module
   - Verify connections

5. **Install Emergency Stop**
   - Mount in easily accessible location
   - Connect to GPIO
   - Test functionality

### Step 3: Configure GPIO

1. **Set GPIO Permissions**
   ```bash
   sudo usermod -a -G gpio $USER
   sudo chmod 666 /dev/i2c-1
   ```

2. **Test I2C Communication**
   ```bash
   i2cdetect -y 1
   # Should show ADS1115 at address 0x48
   ```

3. **Test GPIO Access**
   ```bash
   python3 -c "
   import RPi.GPIO as GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
   print('GPIO access successful')
   "
   ```

### Step 4: Install Application

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/air-leakage-test.git
   cd air-leakage-test
   ```

2. **Setup Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure Application**
   ```bash
   cp config/settings.example.json config/settings.json
   # Edit settings.json with your hardware configuration
   ```

## Testing and Calibration

### Hardware Testing

#### Stepper Motor Test
```python
from hardware.stepper_motor import StepperMotor

# Test motor movement
motor = StepperMotor()
motor.move(100, 1000)  # 100 steps at 1000 steps/sec
motor.stop()
print("Motor test completed")
```

#### Pressure Sensor Test
```python
from hardware.pressure_sensor import PressureSensor

# Test pressure reading
sensor = PressureSensor()
reading = sensor.read_pressure()
print(f"Pressure: {reading} PSI")
```

#### Emergency Stop Test
```python
from core.safety_system import SafetySystem

# Test emergency stop
safety = SafetySystem()
safety.trigger_emergency_stop()
assert safety.is_emergency_active()
print("Emergency stop test passed")
```

### Calibration Procedures

#### Pressure Sensor Calibration

1. **Zero Point Calibration**
   ```python
   # Connect sensor to known 0 PSI source
   sensor.calibrate_zero()
   ```

2. **Span Calibration**
   ```python
   # Connect sensor to known pressure (e.g., 50 PSI)
   sensor.calibrate_span(50.0)
   ```

3. **Linearity Check**
   ```python
   # Test multiple pressure points
   pressures = [0, 10, 20, 30, 40, 50]
   for p in pressures:
       reading = sensor.read_pressure()
       print(f"Expected: {p} PSI, Actual: {reading} PSI")
   ```

#### Motor Calibration

1. **Step Accuracy**
   ```python
   # Test step accuracy
   motor.move(200, 1000)  # One full revolution
   # Verify motor returned to starting position
   ```

2. **Speed Calibration**
   ```python
   # Test different speeds
   speeds = [500, 1000, 1500, 2000]
   for speed in speeds:
       motor.move(100, speed)
       # Measure actual time taken
   ```

### System Integration Test

1. **Full System Test**
   ```python
   # Test complete system
   from main import main
   
   # Run in test mode
   main(test_mode=True)
   ```

2. **Performance Test**
   ```python
   # Test system performance
   import time
   
   start_time = time.time()
   # Run test sequence
   end_time = time.time()
   
   print(f"Test completed in {end_time - start_time:.2f} seconds")
   ```

## Safety Considerations

### Electrical Safety

#### Power Supply Safety
- Use properly rated power supplies
- Ensure adequate current capacity
- Install fuses and circuit breakers
- Use proper grounding

#### Wiring Safety
- Use appropriate wire gauge
- Secure all connections
- Protect against short circuits
- Use strain relief on connections

#### Component Safety
- Operate within component specifications
- Monitor component temperatures
- Install thermal protection
- Use proper heat sinks

### Mechanical Safety

#### Motor Safety
- Secure motor mounting
- Protect against moving parts
- Install emergency stops
- Use proper guards

#### Pressure Safety
- Install pressure relief valves
- Use pressure-rated components
- Monitor pressure limits
- Install safety interlocks

#### System Safety
- Emergency stop functionality
- Fail-safe operation
- Safety monitoring
- Alarm systems

### Environmental Safety

#### Temperature
- Monitor system temperature
- Ensure adequate ventilation
- Install temperature sensors
- Thermal protection

#### Humidity
- Protect against moisture
- Use appropriate enclosures
- Monitor humidity levels
- Corrosion protection

#### Dust and Debris
- Use appropriate enclosures
- Regular cleaning
- Air filtration
- Component protection

## Troubleshooting

### Common Hardware Issues

#### Stepper Motor Problems

**Problem**: Motor not moving
- **Check**: Power supply voltage
- **Verify**: Driver connections
- **Test**: Individual motor phases
- **Solution**: Check wiring or replace driver

**Problem**: Motor skipping steps
- **Check**: Current setting
- **Verify**: Load on motor
- **Test**: Reduce speed
- **Solution**: Increase current or reduce load

**Problem**: Motor overheating
- **Check**: Current setting
- **Verify**: Heat sink installation
- **Test**: Reduce duty cycle
- **Solution**: Reduce current or improve cooling

#### Pressure Sensor Problems

**Problem**: No pressure reading
- **Check**: Power supply
- **Verify**: Wiring connections
- **Test**: ADC communication
- **Solution**: Check connections or replace sensor

**Problem**: Incorrect readings
- **Check**: Sensor calibration
- **Verify**: Reference pressure
- **Test**: Known pressure source
- **Solution**: Recalibrate sensor

**Problem**: Unstable readings
- **Check**: Power supply stability
- **Verify**: Wiring quality
- **Test**: Filtering
- **Solution**: Improve power supply or add filtering

#### ADC Problems

**Problem**: No I2C communication
- **Check**: I2C bus
- **Verify**: Address configuration
- **Test**: i2cdetect command
- **Solution**: Check wiring or address

**Problem**: Incorrect readings
- **Check**: Reference voltage
- **Verify**: Gain setting
- **Test**: Known voltage source
- **Solution**: Check configuration or replace ADC

### Diagnostic Commands

#### I2C Diagnostics
```bash
# Check I2C bus
i2cdetect -y 1

# Check specific device
i2cget -y 1 0x48 0x00
```

#### GPIO Diagnostics
```bash
# Check GPIO status
gpio readall

# Test specific pin
gpio -g mode 23 in
gpio -g read 23
```

#### System Diagnostics
```bash
# Check system temperature
vcgencmd measure_temp

# Check CPU usage
top

# Check memory usage
free -h
```

### Performance Optimization

#### Hardware Optimization
- Use appropriate wire gauge
- Minimize wire length
- Use proper connectors
- Ensure good grounding

#### Software Optimization
- Optimize sampling rate
- Use efficient algorithms
- Minimize I/O operations
- Use appropriate data structures

#### System Optimization
- Monitor system resources
- Optimize power consumption
- Improve thermal management
- Regular maintenance

---

## Appendices

### A. Component Specifications

#### Stepper Motor Specifications
| Model | Torque | Current | Voltage | Steps/Rev |
|-------|--------|---------|---------|-----------|
| 17HS4401 | 40 oz-in | 1.5A | 12V | 200 |
| 17HS4023 | 23 oz-in | 1.7A | 12V | 200 |
| 17HS8401 | 84 oz-in | 2A | 12V | 200 |

#### Pressure Sensor Specifications
| Model | Range | Output | Accuracy | Response |
|-------|-------|--------|----------|----------|
| MPX5050DP | 0-50 PSI | 0.5-4.5V | ±2.5% | 1ms |
| MPX5700 | 0-100 PSI | 0.5-4.5V | ±2.5% | 1ms |

#### ADC Specifications
| Model | Resolution | Channels | Interface | Sample Rate |
|-------|------------|----------|-----------|-------------|
| ADS1115 | 16-bit | 4 | I2C | 8-860 SPS |
| ADS1015 | 12-bit | 4 | I2C | 128-3300 SPS |

### B. Wiring Reference

#### GPIO Pin Assignments
| Function | GPIO | BCM | Physical |
|----------|------|-----|----------|
| Stepper STEP | 17 | 17 | 11 |
| Stepper DIR | 18 | 18 | 12 |
| Stepper ENABLE | 27 | 27 | 13 |
| Stepper MS1 | 22 | 22 | 15 |
| Emergency Stop | 23 | 23 | 16 |
| Status LED | 24 | 24 | 18 |
| I2C SDA | 2 | 2 | 3 |
| I2C SCL | 3 | 3 | 5 |

#### Power Distribution
| Component | Voltage | Current | Connector |
|-----------|---------|---------|-----------|
| Raspberry Pi | 5V | 3A | USB-C |
| Stepper Motors | 12V | 2A | 2-pin |
| Pressure Sensors | 5V | 50mA | 3-pin |
| ADC Module | 3.3V | 10mA | 4-pin |

### C. Maintenance Schedule

#### Daily Checks
- [ ] System startup
- [ ] Hardware connections
- [ ] Error logs
- [ ] Emergency stop
- [ ] Basic functionality

#### Weekly Checks
- [ ] Sensor calibration
- [ ] Motor operation
- [ ] System logs
- [ ] Data backup
- [ ] Performance test

#### Monthly Checks
- [ ] Full inspection
- [ ] Hardware cleaning
- [ ] Performance testing
- [ ] Software updates
- [ ] Documentation review

---

**⚠️ Safety Notice**: This is industrial hardware. Always follow proper safety procedures during installation and testing. Ensure all components are properly rated and installed according to manufacturer specifications.

**🔧 Support**: For hardware support, contact hardware-support@techmac.com or visit our documentation at https://github.com/your-org/air-leakage-test/docs/ 