"""
Hardware detection for Raspberry Pi and other platforms
"""

import os
import platform
import subprocess
from typing import Dict, Any, Optional


class HardwareDetector:
    """Detect hardware capabilities and platform information"""
    
    def __init__(self):
        self.platform_info = self._detect_platform()
        self.hardware_info = self._detect_hardware()
    
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform information"""
        info = {
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_raspberry_pi': False,
            'is_linux': False,
            'is_windows': False
        }
        
        # Detect Raspberry Pi
        if info['system'] == 'Linux':
            info['is_linux'] = True
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    if 'Raspberry Pi' in cpuinfo or 'BCM2708' in cpuinfo or 'BCM2709' in cpuinfo or 'BCM2711' in cpuinfo:
                        info['is_raspberry_pi'] = True
                        # Extract model info
                        for line in cpuinfo.split('\n'):
                            if line.startswith('Model'):
                                info['raspberry_pi_model'] = line.split(':')[1].strip()
                                break
            except:
                pass
        
        elif info['system'] == 'Windows':
            info['is_windows'] = True
        
        return info
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect hardware capabilities"""
        info = {
            'gpio_available': False,
            'i2c_available': False,
            'spi_available': False,
            'serial_available': False,
            'display_available': False
        }
        
        if self.platform_info['is_raspberry_pi']:
            # Check GPIO availability
            info['gpio_available'] = self._check_gpio_availability()
            
            # Check I2C availability
            info['i2c_available'] = self._check_i2c_availability()
            
            # Check SPI availability
            info['spi_available'] = self._check_spi_availability()
            
            # Check serial availability
            info['serial_available'] = self._check_serial_availability()
            
            # Check display availability
            info['display_available'] = self._check_display_availability()
        
        elif self.platform_info['is_windows']:
            # Windows simulation mode
            info['gpio_available'] = False
            info['i2c_available'] = False
            info['spi_available'] = False
            info['serial_available'] = True  # COM ports
            info['display_available'] = True
        
        return info
    
    def _check_gpio_availability(self) -> bool:
        """Check if GPIO is available on Raspberry Pi"""
        try:
            # Check if GPIO library can be imported
            if self.platform_info['is_raspberry_pi']:
                import RPi.GPIO as GPIO  # type: ignore
                return True
            else:
                return False
        except ImportError:
            return False
    
    def _check_i2c_availability(self) -> bool:
        """Check if I2C is available"""
        try:
            # Check if i2c-tools is installed
            result = subprocess.run(['i2cdetect', '-l'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_spi_availability(self) -> bool:
        """Check if SPI is available"""
        try:
            # Check if SPI devices exist
            return os.path.exists('/dev/spidev0.0')
        except:
            return False
    
    def _check_serial_availability(self) -> bool:
        """Check if serial ports are available"""
        try:
            # Check for serial devices
            if self.platform_info['is_raspberry_pi']:
                return os.path.exists('/dev/ttyUSB0') or os.path.exists('/dev/ttyAMA0')
            else:
                return True  # Assume available on other platforms
        except:
            return False
    
    def _check_display_availability(self) -> bool:
        """Check if display is available"""
        try:
            # Check if DISPLAY environment variable is set
            display = os.environ.get('DISPLAY')
            if display:
                return True
            
            # Check if running in X11
            if self.platform_info['is_linux']:
                result = subprocess.run(['xset', 'q'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            return False
        except:
            return False
    
    def get_recommended_mode(self) -> str:
        """Get recommended operation mode based on hardware detection"""
        if self.platform_info['is_raspberry_pi']:
            if self.hardware_info['gpio_available'] and self.hardware_info['i2c_available']:
                return 'hardware'
            else:
                return 'simulation'
        elif self.platform_info['is_windows']:
            return 'simulation'
        else:
            return 'simulation'
    
    def get_platform_summary(self) -> Dict[str, Any]:
        """Get platform summary for logging"""
        return {
            'platform': self.platform_info,
            'hardware': self.hardware_info,
            'recommended_mode': self.get_recommended_mode()
        }
    
    def print_detection_report(self):
        """Print hardware detection report"""
        print("Hardware Detection Report")
        print("=" * 50)
        print(f"Platform: {self.platform_info['system']} {self.platform_info['machine']}")
        print(f"Processor: {self.platform_info['processor']}")
        print(f"Python: {self.platform_info['python_version']}")
        
        if self.platform_info['is_raspberry_pi']:
            print(f"Raspberry Pi: {self.platform_info.get('raspberry_pi_model', 'Unknown')}")
        
        print("\nHardware Capabilities:")
        print(f"  GPIO: {'✓' if self.hardware_info['gpio_available'] else '✗'}")
        print(f"  I2C: {'✓' if self.hardware_info['i2c_available'] else '✗'}")
        print(f"  SPI: {'✓' if self.hardware_info['spi_available'] else '✗'}")
        print(f"  Serial: {'✓' if self.hardware_info['serial_available'] else '✗'}")
        print(f"  Display: {'✓' if self.hardware_info['display_available'] else '✗'}")
        
        print(f"\nRecommended Mode: {self.get_recommended_mode()}")
        print("=" * 50)


# Global detector instance
hardware_detector = HardwareDetector()


def get_hardware_info() -> Dict[str, Any]:
    """Get hardware information"""
    return hardware_detector.get_platform_summary()


def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi"""
    return hardware_detector.platform_info['is_raspberry_pi']


def is_hardware_available() -> bool:
    """Check if hardware mode is available"""
    return hardware_detector.get_recommended_mode() == 'hardware' 