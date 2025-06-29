 # hardware/sensor_manager.py
import threading
import time
from queue import Queue


class SensorManager:
    def __init__(self, hardware_manager):
        self.hardware = hardware_manager
        self.pressure_queue = Queue()
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start sensor monitoring in a separate thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_sensors, daemon=True)
            self.monitor_thread.start()
            print("Sensor monitoring started")
    
    def stop_monitoring(self):
        """Stop sensor monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        print("Sensor monitoring stopped")
    
    def _monitor_sensors(self):
        """Internal monitoring loop"""
        while self.monitoring:
            try:
                # Read pressure
                pressure = self.hardware.read_pressure()
                if pressure is not None:
                    self.pressure_queue.put(pressure)
                
                # Monitor safety conditions
                self._check_safety_sensors()
                
                time.sleep(0.1)  # 10Hz monitoring rate
                
            except Exception as e:
                print(f"Sensor monitoring error: {e}")
                time.sleep(1)  # Delay on error
    
    def _check_safety_sensors(self):
        """Check safety sensor states"""
        try:
            # Check emergency button
            if self.hardware.input_lines['emergency_btn'].get_value():
                self.hardware.emergency_stop = True
                print("Emergency button pressed!")
            
            # Check door closure
            if not self.hardware.input_lines['door_close'].get_value():
                print("Warning: Door is open")
            
            # Check tank level
            if not self.hardware.input_lines['tank_min'].get_value():
                print("Warning: Tank level low")
                
        except Exception as e:
            print(f"Safety sensor check error: {e}")
    
    def get_latest_pressure(self):
        """Get the latest pressure reading"""
        try:
            if not self.pressure_queue.empty():
                return self.pressure_queue.get()
            return None
        except Exception as e:
            print(f"Error getting pressure: {e}")
            return None
    
    def get_sensor_states(self):
        """Get current state of all sensors"""
        states = {}
        try:
            for sensor_name in self.hardware.input_lines:
                states[sensor_name] = self.hardware.input_lines[sensor_name].get_value()
            return states
        except Exception as e:
            print(f"Error reading sensor states: {e}")
            return {}
    
    def is_home_position(self):
        """Check if actuator is at home position"""
        try:
            return self.hardware.input_lines['actuator_min'].get_value()
        except Exception as e:
            print(f"Error checking home position: {e}")
            return False
    
    def is_max_position(self):
        """Check if actuator is at max position"""
        try:
            return self.hardware.input_lines['actuator_max'].get_value()
        except Exception as e:
            print(f"Error checking max position: {e}")
            return False