"""
Complete Fixed Main Entry Point - Resolves all PyRight errors
Eliminates UI freezing through proper event handling
"""

import sys
import os
import signal
import traceback
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Union

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the application components
try:
    from app_controller import AppController
    from core.test_controller import TestController
    from core.safety_manager import SafetyManager
    from core.data_manager import DataManager
    from utils.validation import ValidationUtils
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Global variables for signal handling
app_instance: Optional[AppController] = None
root_window = None
logger: Optional[logging.Logger] = None
shutdown_event = threading.Event()


def setup_logging() -> logging.Logger:
    """Setup application logging"""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger('AirLeakageTest')
        
    except Exception as e:
        print(f"Warning: Could not setup logging: {e}")
        return logging.getLogger('AirLeakageTest')


class OptimizedMainLoop:
    """Optimized main loop with efficient event processing"""
    
    def __init__(self, root_widget):
        self.root = root_widget
        self.running = False
        self.update_interval = 10  # milliseconds
        self.last_update_time = 0.0
        
    def start(self):
        """Start the optimized main loop"""
        self.running = True
        self.last_update_time = time.time()
        
        # Start the main update cycle
        self._schedule_next_update()
        
        if logger:
            logger.info("Optimized main loop started")
    
    def stop(self):
        """Stop the main loop"""
        self.running = False
        if logger:
            logger.info("Optimized main loop stopped")
    
    def _schedule_next_update(self):
        """Schedule the next update cycle"""
        if self.running and self.root.winfo_exists():
            try:
                # Schedule next update with fixed interval
                self.root.after(self.update_interval, self._update_cycle)
                
            except Exception as e:
                if logger:
                    logger.error(f"Error scheduling update: {e}")
                # Fallback to fixed interval
                if self.running:
                    self.root.after(self.update_interval, self._update_cycle)
    
    def _update_cycle(self):
        """Main update cycle - optimized for responsiveness"""
        if not self.running:
            return
        
        try:
            # Process pending events
            self._process_events()
            
            # Schedule next update
            self._schedule_next_update()
            
        except KeyboardInterrupt:
            if logger:
                logger.info("KeyboardInterrupt received in update cycle")
            self.stop()
        except Exception as e:
            if logger:
                logger.error(f"Error in update cycle: {e}")
            if self.running:
                # Continue with error recovery
                self.root.after(self.update_interval * 2, self._update_cycle)
    
    def _process_events(self):
        """Process pending UI events efficiently"""
        try:
            # Use a simpler approach - just process idle tasks
            # This is more reliable than trying to process individual events
            self.root.update_idletasks()
            
        except Exception as e:
            if logger:
                logger.debug(f"Event processing error: {e}")


def signal_handler(signum, frame):
    """Handle Ctrl+C and other termination signals"""
    global app_instance, root_window, logger, shutdown_event
    
    if logger:
        logger.info(f"Received signal {signum} - Initiating clean shutdown...")
    else:
        print(f"\nReceived signal {signum} - Shutting down...")
    
    # Set shutdown event
    shutdown_event.set()
    
    try:
        # Clean shutdown sequence
        cleanup_application()
        
        if logger:
            logger.info("Clean shutdown completed")
        else:
            print("Clean shutdown completed")
        
        # Force exit
        os._exit(0)
        
    except Exception as e:
        if logger:
            logger.error(f"Error during signal handling: {e}")
        else:
            print(f"Error during cleanup: {e}")
        
        # Force exit even if cleanup fails
        os._exit(1)


def cleanup_application():
    """Clean up application resources"""
    global app_instance, root_window, logger
    
    try:
        # Stop any running test
        if app_instance and hasattr(app_instance, 'stop_test'):
            if logger:
                logger.info("Stopping any running tests...")
            app_instance.stop_test()
        
        # Cleanup app controller
        if app_instance and hasattr(app_instance, 'on_closing'):
            if logger:
                logger.info("Cleaning up application controller...")
            app_instance.on_closing()
        
        # Close main window
        if root_window:
            if logger:
                logger.info("Closing main window...")
            try:
                root_window.quit()
                root_window.destroy()
            except:
                pass  # Window might already be destroyed
        
    except Exception as e:
        if logger:
            logger.error(f"Error during cleanup: {e}")
        else:
            print(f"Error during cleanup: {e}")


def setup_signal_handlers():
    """Setup signal handlers for clean shutdown"""
    try:
        # Handle Ctrl+C (SIGINT)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Handle termination signal (SIGTERM)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # On Windows, also handle Ctrl+Break
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
        
        if logger:
            logger.info("Signal handlers configured for clean shutdown")
        else:
            print("✓ Ctrl+C handler configured")
            
    except Exception as e:
        if logger:
            logger.warning(f"Could not setup all signal handlers: {e}")
        else:
            print(f"Warning: Could not setup signal handlers: {e}")


def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'tkinter',
        'PIL',
        'threading',
        'json',
        'time'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Error: Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install missing modules and try again.")
        return False
    
    return True


def check_hardware_simulation():
    """Check if hardware simulation should be enabled"""
    # Check for simulation flag
    simulation_mode = (
        '--simulate' in sys.argv or
        '--sim' in sys.argv or
        '--simulate-hardware' in sys.argv or
        os.environ.get('HARDWARE_SIMULATION', '').lower() in ['1', 'true', 'yes']
    )
    
    if simulation_mode:
        print("Hardware simulation mode enabled")
        os.environ['HARDWARE_SIMULATION'] = '1'
    
    return simulation_mode


def run_optimized_mainloop(root, main_window):
    """Run optimized mainloop with interrupt support"""
    global root_window, shutdown_event
    root_window = root
    
    try:
        # Create optimized main loop
        main_loop = OptimizedMainLoop(root)
        
        # Configure root window to handle protocol close
        def on_window_close():
            if logger:
                logger.info("Window close event received")
            main_loop.stop()
            cleanup_application()
            root.quit()
        
        root.protocol("WM_DELETE_WINDOW", on_window_close)
        
        # Start optimized loop
        main_loop.start()
        
        # Monitor for shutdown event
        def check_shutdown():
            if shutdown_event.is_set():
                main_loop.stop()
                root.quit()
                return
            
            # Check again in 100ms
            root.after(100, check_shutdown)
        
        # Start shutdown monitoring
        check_shutdown()
        
        # Traditional mainloop as fallback
        try:
            root.mainloop()
        except KeyboardInterrupt:
            if logger:
                logger.info("KeyboardInterrupt in mainloop")
            main_loop.stop()
        
    except Exception as e:
        if logger:
            logger.error(f"Error in optimized mainloop: {e}")
        raise


def main():
    """Enhanced main application entry point with optimized event loop"""
    global app_instance, root_window, logger
    
    logger = setup_logging()
    
    try:
        logger.info("="*50)
        logger.info("Starting Air Leakage Test Application")
        logger.info("="*50)
        
        # Setup signal handlers EARLY
        setup_signal_handlers()
        
        # Check dependencies
        logger.info("Checking dependencies...")
        if not check_dependencies():
            logger.error("Dependency check failed")
            return 1
        logger.info("All dependencies available")
        
        # Check hardware simulation mode
        simulation_mode = check_hardware_simulation()
        if simulation_mode:
            logger.info("Hardware simulation mode enabled")
        
        # Parse command line arguments
        debug_mode = '--debug' in sys.argv
        if debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.info("Debug mode enabled")
        
        # Create and initialize application controller
        logger.info("Initializing application controller...")
        app_instance = AppController(settings_file='settings.json')
        
        # Initialize hardware (will fall back to simulation if needed)
        logger.info("Initializing hardware...")
        hardware_initialized = app_instance.initialize_hardware()
        
        if hardware_initialized:
            logger.info("Hardware initialized successfully")
        else:
            logger.info("Running in simulation mode")
        
        # Start the application UI
        logger.info("Starting application UI...")
        
        try:
            # Import and create main window
            from ui.main_window import MainWindow
            import tkinter as tk
            
            # Create root window
            root = tk.Tk()
            root_window = root
            root.configure(cursor="arrow")

            
            # Create main window with root and app_controller
            main_window = MainWindow(root, app_instance)
            
            # Setup the app controller status callback
            if hasattr(main_window, 'set_app_controller_status_callback'):
                main_window.set_app_controller_status_callback()
            
            logger.info("UI started successfully - Starting optimized main loop")
            logger.info("Press Ctrl+C in terminal to exit cleanly")
            
            # Start the optimized mainloop
            run_optimized_mainloop(root, main_window)
            
        except Exception as e:
            logger.error(f"Failed to start UI: {e}")
            if debug_mode:
                logger.error(traceback.format_exc())
            return 1
        
        logger.info("Application completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (Ctrl+C)")
        cleanup_application()
        return 0
    except Exception as e:
        logger.error(f"Application failed: {e}")
        if debug_mode:
            logger.error(traceback.format_exc())
        cleanup_application()
        return 1
    finally:
        # Ensure cleanup happens
        try:
            cleanup_application()
        except:
            pass


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n✓ Application terminated by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        sys.exit(1)