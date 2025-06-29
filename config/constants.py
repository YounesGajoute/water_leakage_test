 # -*- coding: utf-8 -*-
"""
Constants for Air Leakage Test Application
"""

# Application Constants
APP_CONSTANTS = {
    'APP_NAME': 'TechMac - Air Leakage Test',
    'VERSION': '1.0.0',
    'AUTHOR': 'TechMac',
    'SETTINGS_FILE': 'settings.json',
    'LOG_FILE': 'app.log',
    'BACKUP_EXTENSION': '.backup'
}

# UI Constants
UI_CONSTANTS = {
    'WINDOW_TITLE': 'TechMac - Air Leakage Test',
    'FULLSCREEN': True,
    'CURSOR_VISIBLE': False,
    'GAUGE_SIZE': 400,
    'GAUGE_RADIUS': 160,
    'GAUGE_ARC_WIDTH': 15,
    'GAUGE_TICK_COUNT': 31,
    'GAUGE_MAJOR_TICK_INTERVAL': 5,
    'KEYBOARD_LAYOUTS': {
        'lowercase': [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'DEL']
        ],
        'uppercase': [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'DEL']
        ]
    },
    'NAVIGATION_BUTTONS': ["Main", "Settings", "Calibration", "Reference"],
    'BUTTON_SIZES': {
        'nav_button': {'width': 15, 'height': 3},
        'control_button': {'width': 12, 'height': 2},
        'keyboard_key': {'width': 4, 'height': 2},
        'keyboard_special': {'width': 8, 'height': 2}
    }
}

# Hardware Constants
HARDWARE_CONSTANTS = {
    'GPIO_CHIP': 'gpiochip0',
    'ADC_ADDRESS': 0x48,
    'ADC_BUSNUM': 1,
    'STEPS_PER_MM': 380.95,
    'VOLTAGE_RANGE': 4.096,
    'ADC_RESOLUTION': 32767.0,
    'PRESSURE_OFFSET': -0.579,
    'PRESSURE_MULTIPLIER': 1.286,
    'PRESSURE_ADJUSTMENT': -0.2,
    'STEPPER_PULSE_DELAY': 0.001,
    'STEPPER_SETTLE_DELAY': 0.1,
    'HOME_POSITION_OFFSET': 40,
    'MONITORING_FREQUENCY': 10,  # Hz
    'TIMEOUT_VALUES': {
        'homing': 120,  # seconds
        'movement': 60,  # seconds
        'test_max': 7200  # seconds (2 hours)
    }
}

# Test Parameters
TEST_CONSTANTS = {
    'PRESSURE_LIMITS': {
        'min': 0.0,
        'max': 4.5,
        'unit': 'bar'
    },
    'POSITION_LIMITS': {
        'min': 65,
        'max': 200,
        'unit': 'mm'
    },
    'TIME_LIMITS': {
        'min': 0.1,
        'max': 120.0,
        'unit': 'min'
    },
    'GAUGE_RANGES': {
        'pressure': {
            'min': 0.0,
            'max': 4.5,
            'unit': 'bar',
            'precision': 2
        },
        'duration': {
            'min': 0.0,
            'max': 120.0,
            'unit': 'min',
            'precision': 1
        }
    }
}

# Communication Constants
COMM_CONSTANTS = {
    'MODBUS_RTU': {
        'baudrate': 9600,
        'bytesize': 8,
        'parity': 'N',
        'stopbits': 2,
        'timeout': 1.0
    },
    'H300_REGISTERS': {
        'command': 0x2000,
        'frequency': 0x2001,
        'command_source': 0xF002,
        'frequency_source': 0xF003,
        'status': 0x00,
        'voltage': 0x02,
        'current': 0x04,
        'run_status': 0x61
    },
    'H300_COMMANDS': {
        'stop': 0x0006,
        'forward': 0x0001,
        'reverse': 0x0002
    }
}

# Safety Constants
SAFETY_CONSTANTS = {
    'EMERGENCY_STOP_PIN': 17,
    'DOOR_SENSOR_PIN': 4,
    'SAFETY_CHECK_INTERVAL': 0.1,  # seconds
    'EMERGENCY_ACTIONS': [
        'stop_motor',
        'disable_outputs',
        'return_home',
        'alert_user'
    ],
    'REQUIRED_SAFETY_CONDITIONS': [
        'door_closed',
        'emergency_stop_clear',
        'tank_level_ok'
    ]
}

# File Constants
FILE_CONSTANTS = {
    'LOGO_FILE': 'logo.png',
    'SETTINGS_FILE': 'settings.json',
    'LOG_DIRECTORY': 'logs',
    'BACKUP_DIRECTORY': 'backups',
    'EXPORT_DIRECTORY': 'exports',
    'ALLOWED_EXTENSIONS': ['.json', '.txt', '.log'],
    'FILE_PERMISSIONS': 0o666
}

# Error Messages
ERROR_MESSAGES = {
    'hardware': {
        'gpio_init_failed': 'GPIO initialization failed. Check hardware connections.',
        'adc_init_failed': 'ADC initialization failed. Check I2C connections.',
        'motor_init_failed': 'Motor initialization failed. Check motor connections.',
        'sensor_read_failed': 'Sensor reading failed. Check sensor connections.',
        'emergency_stop': 'Emergency stop activated. Reset before continuing.',
        'safety_violation': 'Safety conditions not met. Check door and safety systems.'
    },
    'ui': {
        'invalid_input': 'Invalid input provided. Please check your entries.',
        'reference_not_selected': 'Please select a reference before starting the test.',
        'login_failed': 'Incorrect password. Please try again.',
        'navigation_error': 'Navigation error occurred. Please try again.'
    },
    'test': {
        'test_failed': 'Test sequence failed. Check hardware and try again.',
        'timeout': 'Operation timed out. Please check system status.',
        'position_error': 'Failed to reach target position. Check actuator.',
        'pressure_error': 'Pressure reading error. Check pressure sensor.'
    },
    'settings': {
        'load_failed': 'Failed to load settings. Using defaults.',
        'save_failed': 'Failed to save settings. Changes may be lost.',
        'validation_failed': 'Settings validation failed. Check input values.',
        'reference_exists': 'Reference ID already exists. Please use a different ID.'
    }
}

# Success Messages
SUCCESS_MESSAGES = {
    'test_complete': 'Test completed successfully.',
    'reference_saved': 'Reference saved successfully.',
    'settings_saved': 'Settings saved successfully.',
    'hardware_initialized': 'Hardware initialized successfully.',
    'system_ready': 'System ready - Press Start to begin test.',
    'home_position_reached': 'Home position reached successfully.'
}

# Status Messages
STATUS_MESSAGES = {
    'initializing': 'Initializing system...',
    'hardware_check': 'Checking hardware connections...',
    'safety_check': 'Performing safety checks...',
    'moving_home': 'Moving to home position...',
    'moving_position': 'Moving to test position...',
    'test_running': 'Test in progress...',
    'test_stopping': 'Stopping test...',
    'returning_home': 'Returning to home position...',
    'system_ready': 'System ready for operation.'
}