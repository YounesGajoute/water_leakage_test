#!/usr/bin/env python3
"""
Development Setup Script for Air Leakage Test Application

This script sets up the development environment for the industrial
air leakage test application.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("Error: Python 3.7+ is required")
        sys.exit(1)
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")


def setup_virtual_environment():
    """Create and activate virtual environment."""
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        run_command("python3 -m venv venv")
    
    # Activate virtual environment
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
    else:  # Unix/Linux
        activate_script = "source venv/bin/activate"
    
    print("Virtual environment created/activated")


def install_dependencies():
    """Install Python dependencies."""
    print("Installing dependencies...")
    
    # Upgrade pip
    run_command("pip install --upgrade pip")
    
    # Install production dependencies
    run_command("pip install -r requirements.txt")
    
    # Install development dependencies
    run_command("pip install -r requirements-dev.txt")


def setup_git_hooks():
    """Setup Git hooks for development."""
    print("Setting up Git hooks...")
    
    # Install pre-commit hooks
    run_command("pre-commit install")


def setup_configuration():
    """Setup configuration files."""
    print("Setting up configuration...")
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create example configuration if it doesn't exist
    example_config = config_dir / "settings.example.json"
    if not example_config.exists():
        with open(example_config, "w") as f:
            f.write('''{
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
  },
  "test": {
    "default_pressure": 50.0,
    "default_duration": 30,
    "default_tolerance": 2.0
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log"
  },
  "simulation": {
    "enabled": false
  }
}''')
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    run_command("pytest tests/ -v", check=False)


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup development environment")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-hooks", action="store_true", help="Skip Git hooks setup")
    args = parser.parse_args()
    
    print("Setting up Air Leakage Test Application development environment...")
    
    # Check Python version
    check_python_version()
    
    # Setup virtual environment
    setup_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Setup configuration
    setup_configuration()
    
    # Setup Git hooks
    if not args.skip_hooks:
        setup_git_hooks()
    
    # Run tests
    if not args.skip_tests:
        run_tests()
    
    print("\nDevelopment environment setup complete!")
    print("\nNext steps:")
    print("1. Activate virtual environment: source venv/bin/activate")
    print("2. Configure hardware settings in config/settings.json")
    print("3. Run the application: python main.py")
    print("4. For hardware simulation: python main.py --simulation-mode")


if __name__ == "__main__":
    main() 