 # hardware/motor_controller.py
import time
import threading
from .hardware_manager import MotorState


class MotorController:
    def __init__(self, hardware_manager):
        self.hardware = hardware_manager
        self.motor_state = MotorState()
        self.STEPS_PER_MM = 380.95
        self.current_position = 0
        
    def move_to_position(self, target_position, emergency_check_callback=None):
        """Move stepper motor to target position with safety checks"""
        try:
            print(f"Moving to position: {target_position}mm")
            
            # Enable stepper motor (active low)
            self.hardware.output_lines['stepper_enable'].set_value(0)
            time.sleep(0.5)
            
            # Set direction and verify
            self.hardware.output_lines['stepper_dir'].set_value(1)
            time.sleep(0.1)
            
            # Calculate steps
            steps_to_move = int((target_position - 40) * self.STEPS_PER_MM)
            print(f"Steps to move: {steps_to_move}")
            
            # Move with emergency stop check
            for step in range(steps_to_move):
                # Check emergency stop if callback provided
                if emergency_check_callback and emergency_check_callback():
                    print("Movement interrupted by emergency stop or test end")
                    return False
                    
                # Check limit switch
                if self.hardware.input_lines['actuator_max'].get_value():
                    print("Max limit reached")
                    return False
                    
                # Generate step pulse with longer timing
                self.hardware.output_lines['stepper_pulse'].set_value(1)
                time.sleep(0.001)
                self.hardware.output_lines['stepper_pulse'].set_value(0)
                time.sleep(0.001)
                
                # Print progress every 1000 steps
                if step % 1000 == 0:
                    print(f"Completed {step} steps of {steps_to_move}")
            
            # Disable stepper motor
            time.sleep(0.1)
            self.hardware.output_lines['stepper_enable'].set_value(1)
            self.current_position = target_position
            print("Move to position completed")
            return True
            
        except Exception as e:
            print(f"Error moving to position: {e}")
            # Safety disable
            self.hardware.output_lines['stepper_enable'].set_value(1)
            return False
    
    def move_to_home(self):
        """Return stepper motor to home position with improved error handling"""
        try:
            print("Starting homing sequence")
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                # Enable stepper motor (active low)
                self.hardware.output_lines['stepper_enable'].set_value(0)
                time.sleep(0.1)
                
                # Set direction toward home
                self.hardware.output_lines['stepper_dir'].set_value(0)
                time.sleep(0.1)
                
                # Move until home switch is triggered or timeout
                start_time = time.time()
                timeout = 120  # 120 seconds timeout
                
                while not self.hardware.input_lines['actuator_min'].get_value():
                    if time.time() - start_time > timeout:
                        print(f"Homing attempt {retry_count + 1} timed out")
                        break
                        
                    self.hardware.output_lines['stepper_pulse'].set_value(1)
                    time.sleep(0.002)
                    self.hardware.output_lines['stepper_pulse'].set_value(0)
                    time.sleep(0.002)
                    
                # Check if homing was successful
                if self.hardware.input_lines['actuator_min'].get_value():
                    # Disable stepper motor
                    self.hardware.output_lines['stepper_enable'].set_value(1)
                    self.current_position = 0
                    print("Homing completed successfully")
                    return True
                    
                retry_count += 1
                time.sleep(1)  # Wait before retry
            
            raise RuntimeError(f"Failed to home after {max_retries} attempts")
            
        except Exception as e:
            print(f"Error during homing: {e}")
            # Safety disable
            self.hardware.output_lines['stepper_enable'].set_value(1)
            return False
    
    def start_motor(self):
        """Start motor using H300 relay"""
        try:
            self.hardware.output_lines['relay_control_h300'].set_value(1)
            self.motor_state.set_running(True)
            print("Motor started")
            return True
        except Exception as e:
            print(f"Error starting motor: {e}")
            return False
    
    def stop_motor(self):
        """Stop motor using H300 relay"""
        try:
            self.hardware.output_lines['relay_control_h300'].set_value(0)
            self.motor_state.set_running(False)
            print("Motor stopped")
            return True
        except Exception as e:
            print(f"Error stopping motor: {e}")
            return False
    
    def emergency_stop(self):
        """Emergency stop all motor operations"""
        try:
            # Stop motor immediately
            self.hardware.output_lines['relay_control_h300'].set_value(0)
            self.hardware.output_lines['stepper_enable'].set_value(1)
            self.motor_state.set_running(False)
            print("Emergency stop executed")
            return True
        except Exception as e:
            print(f"Error during emergency stop: {e}")
            return False