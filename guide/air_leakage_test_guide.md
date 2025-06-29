# 🔧 Air Leakage Test Application - Complete User Guide

## 📖 Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Application Interface](#application-interface)
6. [Test Operations](#test-operations)
7. [Reference Management](#reference-management)
8. [Settings & Configuration](#settings--configuration)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Safety Features](#safety-features)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Features](#advanced-features)
13. [Maintenance](#maintenance)

---

## 📋 Overview

The **Air Leakage Test Application** is a comprehensive system for conducting automated air leakage tests with real-time monitoring, data collection, and safety management. The enhanced version includes professional-grade features for industrial testing environments.

### Key Features
- ✅ **Automated Test Sequences** - Complete test automation with safety monitoring
- ✅ **Real-time Data Collection** - Live pressure and duration monitoring
- ✅ **Reference Management** - Store and manage test configurations
- ✅ **Safety System** - Multi-level safety monitoring and emergency stops
- ✅ **Global Keyboard Controls** - Professional keyboard shortcuts
- ✅ **Hardware Simulation** - Test without physical hardware
- ✅ **Data Export** - Export test results and logs
- ✅ **User Authentication** - Secure access to configuration areas

---

## 💻 System Requirements

### Hardware Requirements
- **Computer**: Windows/Linux PC with USB ports
- **Display**: Minimum 1024x768 resolution (touchscreen compatible)
- **Hardware Interface**: 
  - Raspberry Pi GPIO (for production)
  - ADC converter (ADS1115)
  - Stepper motor controller
  - Pressure sensors
  - Safety switches

### Software Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows 10/11, Linux (Raspberry Pi OS)
- **Dependencies**: Listed in `requirements.txt`

### Network Requirements (Optional)
- Internet connection for updates
- Local network for remote monitoring

---

## 🛠 Installation

### 1. Download and Extract
```bash
# Download the application files
cd /your/desired/directory
# Extract the application files here
```

### 2. Install Python Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Or install individually:
pip install Pillow>=8.0.0
pip install gpiod>=1.5.0
pip install Adafruit-ADS1x15>=1.0.2
pip install psutil>=5.8.0
```

### 3. Verify Installation
```bash
# Test the installation
python main.py --version
python main.py --simulate
```

### 4. Hardware Setup (Production Only)
1. Connect GPIO pins according to `hardware_config` in settings
2. Connect ADC for pressure sensing
3. Connect stepper motor controller
4. Install safety switches (emergency stop, door sensor)
5. Test all connections with simulation mode first

---

## 🚀 Getting Started

### First Launch
```bash
# Start in simulation mode (recommended for first time)
python main.py --simulate

# Normal operation (requires hardware)
python main.py

# Debug mode for troubleshooting
python main.py --debug
```

### Initial Setup
1. **Launch the application** in simulation mode
2. **Create your first reference** (test configuration)
3. **Test the interface** using keyboard shortcuts
4. **Configure hardware settings** (if using physical hardware)
5. **Run a test simulation** to verify operation

---

## 🖥 Application Interface

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [LOGO]              System Status: Ready    [Main|Ref|Set|Cal] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─── Test Parameters ────────────────────────────────────┐ │
│  │ Reference: TEST_001 │ Pressure: 2.5 bar │ Time: 10 min │ │
│  │ Position: 150 mm    │ Status: Ready      │             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Live Test Data ──────────────────────────────────────┐ │
│  │           [Pressure Gauge]    [Duration Gauge]          │ │
│  │               2.5 bar            10:00 min              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Controls ──────────────────────────────────────────┐  │
│  │ [Start Test] [Stop Test] [EMERGENCY STOP] │ Ref: ▼    │  │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Status: System Ready - Press Start to begin test          │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Tabs
- **Main**: Primary test interface
- **Reference**: Manage test configurations
- **Settings**: System configuration (password protected)
- **Calibration**: Hardware calibration (password protected)

---

## 🧪 Test Operations

### Creating a Test Reference

1. **Navigate to Reference Management**
   - Click "Reference" tab or press `F2`
   - Click "Add Reference"

2. **Fill in Test Parameters**
   ```
   Reference ID: TEST_001
   Position: 150.0 mm
   Pressure: 2.5 bar
   Time: 10.0 min
   Description: Standard leak test
   ```

3. **Validate and Save**
   - System validates input ranges automatically
   - Green checkmarks indicate valid fields
   - Click "Save Reference" when complete

### Running a Test

1. **Select Reference**
   - Use dropdown in main view
   - Or double-click reference in Reference tab

2. **Safety Check**
   - Ensure door is closed
   - Emergency stop is not activated
   - System shows "Ready" status

3. **Start Test**
   - Click "Start Test" or press `Ctrl+S`
   - Confirm test start in dialog
   - Monitor progress on live gauges

4. **Test Sequence**
   ```
   1. Move to home position
   2. Move to test position (150mm)
   3. Start motor/pump
   4. Monitor pressure and time
   5. Stop motor when complete
   6. Return to home position
   7. Save results
   ```

5. **Emergency Stop**
   - Press red "EMERGENCY STOP" button
   - Or press `Ctrl+E` hotkey
   - System stops immediately and safely

### Test Results

After test completion:
- **Results Summary**: Duration, final pressure, status
- **Data Export**: Pressure data, test log, statistics
- **File Location**: `test_results_YYYYMMDD_HHMMSS.json`

---

## 📁 Reference Management

### Reference Structure
```json
{
  "name": "TEST_001",
  "description": "Standard leak test",
  "parameters": {
    "position": 150.0,
    "target_pressure": 2.5,
    "inspection_time": 10.0
  },
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Parameter Limits
- **Position**: 65-200 mm
- **Pressure**: 0-4.5 bar
- **Time**: 0-120 minutes

### Reference Operations
- **Create**: Add new test configurations
- **Edit**: Modify existing references
- **Delete**: Remove unused references
- **Load**: Select active reference for testing
- **Export**: Save references to file

---

## ⚙️ Settings & Configuration

### Accessing Settings
1. Click "Settings" tab or press `F3`
2. Enter password: `Admin123`
3. Configure system parameters

### Configuration Sections

#### System Settings
```
Language: English/French/Arabic
Screen Timeout: 30 minutes
Auto-save Results: Enabled
```

#### Hardware Settings
```
Pressure Sensor Calibration
Motor Speed: 50 Hz
Safety Check Interval: 0.1 seconds
Emergency Timeout: 5 seconds
```

#### Safety Limits
```
Maximum Pressure: 5.0 bar
Minimum Pressure: -0.5 bar
Emergency Reset Delay: 5 seconds
```

### Configuration File
Settings are stored in `settings.json`:
```json
{
  "ui_enhancements": {
    "enable_global_escape": true,
    "enable_function_keys": true,
    "hotkeys": {
      "emergency_stop": "Ctrl+E",
      "quick_exit": "Ctrl+Q"
    }
  },
  "hardware_config": {
    "gpio_pins": {...},
    "adc_config": {...},
    "motor_config": {...}
  }
}
```

---

## ⌨️ Keyboard Shortcuts

### Global Shortcuts (Work Everywhere)
| Shortcut | Action | Description |
|----------|--------|-------------|
| `Escape` | Context Back/Exit | Smart navigation or exit |
| `Ctrl+E` | Emergency Stop | Immediate test stop |
| `Ctrl+Q` | Quick Exit | Exit application |
| `Ctrl+S` | Quick Start | Start test (if ready) |
| `Ctrl+R` | Quick Reference | Open reference dialog |

### Navigation Shortcuts
| Shortcut | Action | Description |
|----------|--------|-------------|
| `F1` | Main View | Go to test interface |
| `F2` | Reference View | Manage references |
| `F3` | Settings | System settings (with login) |
| `F4` | Calibration | Hardware calibration (with login) |

### Dialog Shortcuts
| Shortcut | Action | Description |
|----------|--------|-------------|
| `Enter` | Confirm/Save | Save current dialog |
| `Escape` | Cancel | Close dialog without saving |
| `Tab` | Next Field | Move to next input field |

### Debug Shortcuts
| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+D` | Debug Mode | Toggle debug interface |
| `Ctrl+C` | Toggle Cursor | Show/hide mouse cursor |

---

## 🛡️ Safety Features

### Multi-Level Safety System

#### Level 1: Critical Safety (Automatic Stop)
- **Emergency Button**: Physical emergency stop
- **Door Sensor**: Test chamber must be closed
- **Limit Switches**: Actuator position limits
- **Pressure Limits**: Maximum/minimum pressure thresholds

#### Level 2: Warning Conditions (Alert User)
- **Tank Level**: Minimum air supply level
- **Temperature**: System temperature monitoring
- **Communication**: Hardware connection status

#### Level 3: User Controls (Manual Override)
- **Software Emergency Stop**: `Ctrl+E` hotkey
- **Test Stop**: Stop button in interface
- **System Shutdown**: Safe application exit

### Safety Monitoring
```
Monitoring Frequency: 10 Hz (every 100ms)
Emergency Response Time: < 500ms
Safety Log Retention: 1000 events
Alert History: 100 recent alerts
```

### Emergency Procedures

#### Emergency Stop Activated
1. **Immediate Actions**:
   - All motors stop instantly
   - Actuator disables
   - Pressure vents (if configured)
   - Emergency logged

2. **Recovery Steps**:
   - Clear emergency condition
   - Wait 5 seconds
   - Reset emergency state
   - Perform safety check
   - Return to home position

#### System Fault
1. **Automatic Response**:
   - Test stops safely
   - System enters safe mode
   - Error logged with timestamp
   - User notification displayed

2. **User Actions**:
   - Review error message
   - Check hardware connections
   - Restart application if needed
   - Contact support if persistent

---

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version

# Check dependencies
pip list | grep -E "(Pillow|gpiod|Adafruit)"

# Run with debug info
python main.py --debug
```

#### Hardware Connection Issues
```bash
# Test in simulation mode
python main.py --simulate

# Check GPIO permissions (Linux)
sudo usermod -a -G gpio $USER

# Test hardware initialization
python -c "from hardware.hardware_manager import HardwareManager; h=HardwareManager(); print(h.init_gpio())"
```

#### Keyboard Shortcuts Not Working
1. **Check Focus**: Ensure application window has focus
2. **Check Bindings**: Look for error messages in console
3. **Test Individual Keys**: Try each shortcut separately
4. **Restart Application**: Close and reopen application

#### Test Sequence Fails
1. **Safety Check**: Verify all safety conditions
2. **Hardware Status**: Check all connections
3. **Reference Valid**: Ensure test parameters are valid
4. **Manual Mode**: Try manual position control
5. **Log Review**: Check test logs for details

### Error Messages

#### "Safety check failed: Door must be closed"
- **Cause**: Door sensor not activated
- **Solution**: Close test chamber door securely

#### "Emergency stop activated"
- **Cause**: Emergency button pressed or sensor fault
- **Solution**: Release emergency stop, wait 5 seconds, try again

#### "Failed to reach target position"
- **Cause**: Mechanical obstruction or motor fault
- **Solution**: Check actuator movement, verify motor power

#### "Hardware initialization failed"
- **Cause**: GPIO or ADC connection issue
- **Solution**: Check connections, run with `--simulate` flag

### Log Files
- **Application Log**: `logs/app_YYYYMMDD.log`
- **Safety Log**: `emergency_log.txt`
- **Test Results**: `test_results_*.json`

---

## 🚀 Advanced Features

### Command Line Options
```bash
# Show all options
python main.py --help

# Debug mode with verbose logging
python main.py --debug

# Hardware simulation for development
python main.py --simulate

# Combined debug and simulation
python main.py --debug --simulate

# Show version information
python main.py --version
```

### Hardware Simulation Mode
When running with `--simulate`:
- All hardware calls return mock values
- Safety checks are bypassed (with warnings)
- Test sequences run with simulated timing
- Useful for development and demonstration

### Data Export Formats
```json
{
  "test_results": {
    "test_id": "test_1234567890",
    "timestamp": "2024-01-15T10:30:00",
    "completed": true,
    "duration_minutes": 10.2,
    "final_pressure": 2.48,
    "parameters": {...}
  },
  "pressure_data": [
    {"timestamp": 0.0, "pressure": 0.0},
    {"timestamp": 0.1, "pressure": 0.1},
    ...
  ],
  "test_log": [
    {"timestamp": 0.0, "event": "Test started"},
    {"timestamp": 1.2, "event": "Target position reached"},
    ...
  ]
}
```

### API Integration (Future)
The application is designed for future API integration:
- REST API endpoints for remote control
- WebSocket for real-time monitoring
- Database connectivity for data persistence
- Mobile app integration capabilities

---

## 🔄 Maintenance

### Regular Maintenance Tasks

#### Daily
- [ ] Check system status on startup
- [ ] Verify safety systems function
- [ ] Review any error messages
- [ ] Clean test chamber if needed

#### Weekly
- [ ] Review test logs for patterns
- [ ] Check hardware connections
- [ ] Update references if needed
- [ ] Backup configuration files

#### Monthly
- [ ] Calibrate pressure sensors
- [ ] Check actuator movement accuracy
- [ ] Update software if available
- [ ] Archive old test results

### Backup Procedures

#### Configuration Backup
```bash
# Backup settings
cp settings.json settings_backup_$(date +%Y%m%d).json

# Backup references
python -c "import json; s=json.load(open('settings.json')); json.dump(s['references'], open('references_backup.json','w'), indent=4)"
```

#### System Backup
```bash
# Full application backup
tar -czf air_leakage_backup_$(date +%Y%m%d).tar.gz \
  *.py config/ ui/ hardware/ core/ utils/ settings.json logs/
```

#### Restore Procedures
```bash
# Restore settings
cp settings_backup_YYYYMMDD.json settings.json

# Restore full system
tar -xzf air_leakage_backup_YYYYMMDD.tar.gz
```

### Software Updates

#### Check for Updates
1. Review release notes
2. Backup current system
3. Test in simulation mode first
4. Apply updates during maintenance window

#### Update Process
```bash
# Backup current version
cp -r current_app backup_$(date +%Y%m%d)

# Apply updates
# ... follow update instructions ...

# Test updated version
python main.py --simulate --debug

# Restore if issues
# cp -r backup_YYYYMMDD/* current_app/
```

### Performance Monitoring

#### System Health Checks
- **Memory Usage**: Monitor for memory leaks
- **CPU Usage**: Check for performance issues
- **Disk Space**: Ensure adequate storage
- **Response Time**: Verify UI responsiveness

#### Performance Metrics
```python
# Check system performance
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```

---

## 📞 Support & Resources

### Getting Help
1. **Check this guide** for common solutions
2. **Review log files** for error details
3. **Test in simulation mode** to isolate issues
4. **Contact technical support** with log files

### Documentation
- **User Guide**: This document
- **API Reference**: `docs/api_reference.md`
- **Hardware Setup**: `docs/hardware_setup.md`
- **Developer Guide**: `docs/developer_guide.md`

### Version Information
- **Application**: Air Leakage Test v2.0 (Enhanced)
- **Python**: 3.7+ required
- **Last Updated**: 2024-01-15
- **Compatibility**: Raspberry Pi, Windows, Linux

### Contact Information
- **Technical Support**: [Your support contact]
- **Hardware Issues**: [Hardware support contact]
- **Software Updates**: [Update notification method]

---

## 📝 Appendix

### Appendix A: Hardware Wiring Diagram
```
GPIO Pin Assignments:
- Pin 4:  Door Closure Switch (Input)
- Pin 6:  Start Button (Input) 
- Pin 16: Stepper Pulse (Output)
- Pin 17: Emergency Button (Input, Inverted)
- Pin 20: Stepper Enable (Output)
- Pin 21: Stepper Direction (Output)
- Pin 22: Actuator Max Limit (Input)
- Pin 23: Tank Min Level (Input)
- Pin 24: Relay Control H300 (Output)
- Pin 27: Actuator Min Limit (Input)

I2C Connections:
- SDA: GPIO 2 (Pin 3)
- SCL: GPIO 3 (Pin 5)
- ADC: ADS1115 at address 0x48
```

### Appendix B: Default Settings
```json
{
  "validation_ranges": {
    "position": {"min": 65, "max": 200, "unit": "mm"},
    "pressure": {"min": 0, "max": 4.5, "unit": "bar"},
    "time": {"min": 0, "max": 120, "unit": "min"}
  },
  "safety_limits": {
    "max_pressure": 5.0,
    "emergency_timeout": 5.0,
    "monitoring_interval": 0.1
  }
}
```

### Appendix C: Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| E001 | GPIO initialization failed | Check hardware connections |
| E002 | ADC communication error | Verify I2C connections |
| E003 | Safety condition not met | Check safety switches |
| E004 | Motor movement timeout | Check actuator power |
| E005 | Pressure sensor fault | Calibrate pressure sensor |

---

**© 2024 Air Leakage Test Application - Enhanced Version**

*This guide covers all aspects of the enhanced Air Leakage Test Application. For additional support or custom modifications, please contact technical support.*