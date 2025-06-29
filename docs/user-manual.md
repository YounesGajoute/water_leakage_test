# User Manual - Air Leakage Test Application

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface](#user-interface)
4. [Test Procedures](#test-procedures)
5. [Configuration](#configuration)
6. [Data Management](#data-management)
7. [Safety Procedures](#safety-procedures)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## Introduction

The Air Leakage Test Application is a professional-grade industrial system designed for automated air leakage testing in manufacturing environments. This application provides precise control over stepper motors, pressure sensors, and safety systems while maintaining comprehensive data logging and export capabilities.

### Key Features

- **Automated Testing**: Fully automated test sequences with configurable parameters
- **Real-time Monitoring**: Live pressure graphs and system status
- **Safety Systems**: Comprehensive safety monitoring with emergency shutdown
- **Data Management**: Export test results to multiple formats
- **Touchscreen Interface**: Optimized for industrial touchscreens
- **Hardware Simulation**: Development and testing without hardware

## Getting Started

### System Requirements

#### Hardware Requirements
- Raspberry Pi 4 (4GB RAM recommended) or Raspberry Pi 3B+
- Touchscreen Display (7" or larger recommended)
- Stepper Motors with appropriate drivers
- Pressure Sensors (ADC-compatible)
- Emergency Stop Button
- Power Supply (5V/3A minimum)

#### Software Requirements
- Python 3.7+ (3.8+ recommended)
- Raspberry Pi OS (Bullseye or newer)
- GPIO Libraries: `gpiod`, `RPi.GPIO`

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/air-leakage-test.git
   cd air-leakage-test
   ```

2. **Install Dependencies**
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
   sudo raspi-config
   # Enable I2C and SPI interfaces
   ```

5. **Setup Permissions**
   ```bash
   sudo usermod -a -G gpio $USER
   sudo chmod 666 /dev/i2c-1
   ```

6. **Configure Application**
   ```bash
   cp config/settings.example.json config/settings.json
   # Edit settings.json with your hardware configuration
   ```

7. **Launch Application**
   ```bash
   python main.py
   ```

## User Interface

### Main Screen

The main screen provides access to all primary functions:

- **Test Control**: Start, stop, and pause tests
- **Real-time Monitoring**: Live pressure graphs and system status
- **Configuration**: Access to settings and calibration
- **Data Management**: Export and view test results
- **Safety Status**: Emergency stop and safety system status

### Navigation

- **Touch Navigation**: Tap buttons and menu items
- **Swipe Gestures**: Swipe between screens (if supported)
- **Keyboard Shortcuts**: Available for advanced users
- **Emergency Stop**: Large red button always accessible

### Screen Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Emergency Stop]                    [Settings] [Help]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Start Test]  [Stop Test]  [Pause]  [Calibrate]       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Pressure Graph                    │   │
│  │                                               │   │
│  │                                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Status: [Ready]  Pressure: [0.0 PSI]  Time: [00:00]   │
│                                                         │
│  [Test Results]  [Export Data]  [System Health]        │
└─────────────────────────────────────────────────────────┘
```

## Test Procedures

### Manual Test

1. **Prepare System**
   - Ensure all hardware is connected and powered
   - Verify safety systems are active
   - Check pressure sensor calibration

2. **Configure Test Parameters**
   - Set target pressure (e.g., 50 PSI)
   - Set test duration (e.g., 30 seconds)
   - Set tolerance limits (e.g., ±2 PSI)

3. **Start Test**
   - Press "Start Test" button
   - Monitor real-time pressure graph
   - Watch for any safety alerts

4. **Monitor Results**
   - Observe pressure readings
   - Check for leaks (pressure drop)
   - Monitor test duration

5. **Complete Test**
   - Test automatically stops after duration
   - Review results and pass/fail status
   - Save or export data as needed

### Batch Test

1. **Configure Batch Parameters**
   - Set number of tests
   - Define test sequence
   - Set intervals between tests

2. **Start Batch**
   - Press "Start Batch" button
   - System automatically runs all tests
   - Monitor progress and results

3. **Review Results**
   - View summary of all tests
   - Identify patterns or issues
   - Export batch results

### Continuous Test

1. **Configure Continuous Mode**
   - Set monitoring interval
   - Define alert thresholds
   - Configure data logging

2. **Start Monitoring**
   - Press "Start Continuous" button
   - System continuously monitors pressure
   - Alerts on threshold violations

3. **Monitor and Respond**
   - Watch for pressure changes
   - Respond to alerts
   - Review logged data

## Configuration

### Hardware Configuration

Edit `config/settings.json` to configure your hardware:

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

Configure test parameters in the UI or settings:

- **Test Pressure**: Target pressure for leakage testing
- **Test Duration**: Duration of each test cycle
- **Tolerance**: Acceptable pressure drop percentage
- **Sample Rate**: Data sampling frequency
- **Safety Limits**: Maximum pressure and time limits

### User Preferences

- **Display Settings**: Screen brightness, timeout
- **Units**: PSI, kPa, Bar
- **Language**: Interface language
- **Data Format**: CSV, JSON, Excel
- **Auto-save**: Automatic data saving

## Data Management

### Test Results

Test results include:

- **Test Parameters**: Pressure, duration, tolerance
- **Pressure Data**: Time-series pressure readings
- **Test Status**: Pass/fail with reasons
- **Timestamps**: Start and end times
- **Operator**: User who ran the test
- **Hardware Status**: System health during test

### Data Export

Export data in multiple formats:

#### CSV Export
```csv
Timestamp,Pressure_PSI,Status,Notes
2024-06-29 10:30:00,50.2,Pass,Test completed successfully
2024-06-29 10:30:01,49.8,Pass,Pressure within tolerance
```

#### JSON Export
```json
{
  "test_id": "TEST_20240629_103000",
  "parameters": {
    "target_pressure": 50.0,
    "duration": 30,
    "tolerance": 2.0
  },
  "results": {
    "status": "PASS",
    "final_pressure": 49.8,
    "pressure_drop": 0.2
  }
}
```

#### Excel Export
- Multiple worksheets for different data types
- Charts and graphs
- Summary statistics
- Quality control reports

### Data Storage

- **Local Storage**: Data stored on Raspberry Pi
- **Backup**: Automatic backup to external storage
- **Retention**: Configurable data retention policies
- **Security**: Encrypted storage for sensitive data

## Safety Procedures

### Emergency Procedures

#### Emergency Stop
1. **Immediate Action**: Press the large red emergency stop button
2. **System Response**: All motors stop, pressure released
3. **Safety Check**: Verify all systems are in safe state
4. **Investigation**: Determine cause of emergency
5. **Reset**: Only reset after safety clearance

#### Pressure Overload
1. **Automatic Response**: System automatically stops
2. **Pressure Release**: Safety valves open
3. **Alert**: System displays warning message
4. **Investigation**: Check for system faults
5. **Recovery**: Reset after pressure normalization

### Safety Checks

#### Pre-Test Safety Checklist
- [ ] Emergency stop button functional
- [ ] Pressure relief valves operational
- [ ] All safety systems active
- [ ] Hardware connections secure
- [ ] Power supply stable
- [ ] No visible damage or leaks

#### During Test Safety Monitoring
- [ ] Monitor pressure readings
- [ ] Watch for unusual behavior
- [ ] Check system temperature
- [ ] Verify motor operation
- [ ] Monitor for error messages

#### Post-Test Safety Verification
- [ ] Verify all systems stopped
- [ ] Check for any damage
- [ ] Review safety system logs
- [ ] Document any incidents
- [ ] Reset for next test

### Safety Training

#### Required Training
- Basic system operation
- Emergency procedures
- Safety system operation
- Hardware maintenance
- Troubleshooting procedures

#### Certification
- Operator certification required
- Annual safety training
- Incident response training
- Hardware-specific training

## Troubleshooting

### Common Issues

#### Hardware Issues

**Problem**: Hardware not detected
- **Check**: Physical connections
- **Verify**: Power supply
- **Test**: Individual components
- **Solution**: Reconnect or replace hardware

**Problem**: Incorrect pressure readings
- **Check**: Sensor calibration
- **Verify**: ADC connections
- **Test**: Known pressure source
- **Solution**: Recalibrate sensors

**Problem**: Motor not moving
- **Check**: Motor driver connections
- **Verify**: Power supply voltage
- **Test**: Individual motor phases
- **Solution**: Check wiring or replace driver

#### Software Issues

**Problem**: Application won't start
- **Check**: Python installation
- **Verify**: Dependencies installed
- **Test**: Run in simulation mode
- **Solution**: Reinstall dependencies

**Problem**: UI not responding
- **Check**: Touchscreen calibration
- **Verify**: Display settings
- **Test**: Keyboard input
- **Solution**: Recalibrate touchscreen

**Problem**: Data not saving
- **Check**: Disk space
- **Verify**: File permissions
- **Test**: Manual file creation
- **Solution**: Free disk space or fix permissions

### Error Messages

#### Common Error Messages

**"Hardware not detected"**
- Check hardware connections
- Verify power supply
- Test in simulation mode

**"Pressure sensor error"**
- Check sensor wiring
- Verify ADC configuration
- Recalibrate sensor

**"Emergency stop activated"**
- Check emergency stop button
- Verify safety system status
- Reset after safety clearance

**"System overload"**
- Check system resources
- Verify hardware status
- Restart application

### Debug Mode

Enable debug logging for troubleshooting:

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/debug.log"
  }
}
```

### Support Resources

- **Documentation**: User manual and technical guides
- **Online Support**: GitHub issues and discussions
- **Technical Support**: tech-support@techmac.com
- **Emergency Support**: +1-555-SECURITY

## Maintenance

### Regular Maintenance

#### Daily Maintenance
- [ ] Check system startup
- [ ] Verify hardware connections
- [ ] Review error logs
- [ ] Test emergency stop
- [ ] Clean touchscreen

#### Weekly Maintenance
- [ ] Calibrate pressure sensors
- [ ] Check motor operation
- [ ] Review system logs
- [ ] Backup data
- [ ] Update software if needed

#### Monthly Maintenance
- [ ] Full system inspection
- [ ] Hardware cleaning
- [ ] Performance testing
- [ ] Security updates
- [ ] Documentation review

### Calibration Procedures

#### Pressure Sensor Calibration

1. **Prepare Calibration Equipment**
   - Known pressure source
   - Calibration certificate
   - Stable environment

2. **Run Calibration Sequence**
   - Zero point calibration
   - Span calibration
   - Linearity check

3. **Verify Results**
   - Check calibration accuracy
   - Document calibration data
   - Update configuration

#### Motor Calibration

1. **Position Calibration**
   - Home position setting
   - Step accuracy verification
   - Speed calibration

2. **Performance Testing**
   - Load testing
   - Speed testing
   - Accuracy verification

### Software Updates

#### Update Procedures

1. **Backup Current System**
   - Backup configuration files
   - Export important data
   - Document current settings

2. **Install Updates**
   - Download new version
   - Install dependencies
   - Update configuration

3. **Verify Installation**
   - Test all functionality
   - Verify hardware compatibility
   - Check data integrity

#### Rollback Procedures

1. **Identify Issue**
   - Document problem
   - Check error logs
   - Determine cause

2. **Restore Previous Version**
   - Restore backup
   - Reinstall previous version
   - Verify functionality

3. **Document Incident**
   - Record what happened
   - Update procedures
   - Notify support team

### Performance Monitoring

#### System Performance

Monitor key performance indicators:

- **Startup Time**: Should be < 30 seconds
- **Memory Usage**: Should be < 500MB
- **CPU Usage**: Should be < 50% average
- **Response Time**: Should be < 1 second

#### Hardware Performance

- **Motor Performance**: Speed and accuracy
- **Sensor Accuracy**: Pressure reading precision
- **System Reliability**: Uptime and error rates
- **Safety System**: Response time and reliability

---

## Appendices

### A. Quick Reference

#### Keyboard Shortcuts
- `Ctrl+Q`: Quit application
- `Ctrl+S`: Save current data
- `Ctrl+E`: Export data
- `Ctrl+C`: Cancel current operation
- `F1`: Help
- `F2`: Settings

#### Emergency Contacts
- **Technical Support**: tech-support@techmac.com
- **Safety Issues**: safety@techmac.com
- **Emergency**: +1-555-SECURITY

### B. Configuration Reference

#### Settings File Structure
```json
{
  "hardware": { /* Hardware configuration */ },
  "test": { /* Test parameters */ },
  "safety": { /* Safety settings */ },
  "logging": { /* Logging configuration */ },
  "ui": { /* User interface settings */ }
}
```

#### Hardware Pin Assignments
- **Stepper Motor 1**: GPIO 17, 18, 27, 22
- **Pressure Sensor**: I2C SDA/SCL
- **Emergency Stop**: GPIO 23
- **Status LED**: GPIO 24

### C. Troubleshooting Guide

#### Diagnostic Commands
```bash
# Check hardware status
python -c "from hardware import check_hardware; check_hardware()"

# Test pressure sensor
python -c "from hardware import test_sensor; test_sensor()"

# Verify GPIO configuration
python -c "from hardware import verify_gpio; verify_gpio()"
```

#### Log File Locations
- **Application Logs**: `logs/app.log`
- **Error Logs**: `logs/error.log`
- **Debug Logs**: `logs/debug.log`
- **Hardware Logs**: `logs/hardware.log`

---

**⚠️ Safety Notice**: This is industrial control software. Always follow proper safety procedures and ensure all hardware is properly installed and tested before operation. Never operate without proper training and safety equipment.

**📞 Support**: For technical support, contact tech-support@techmac.com or visit our documentation at https://github.com/your-org/air-leakage-test/docs/ 