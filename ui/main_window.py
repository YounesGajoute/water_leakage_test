"""
Enhanced Main Window for Air Leakage Test Application
Complete corrected version with all errors resolved
"""

import tkinter as tk
# import tkinter.messagebox as messagebox  # Removed messagebox import
import tkinter.simpledialog as simpledialog
import os
import sys

# Handle PIL import with proper error handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available - logo functionality disabled")

# Import application views and dialogs with proper error handling
try:
    from .views.main_view import MainView
    from .views.reference_view import ReferenceView
    from .views.settings_view import SettingsView
    from .views.calibration_view import CalibrationView
    from .dialogs.login_dialog import LoginInterface
    from .dialogs.reference_dialog import ReferenceDialog
except ImportError:
    # Fallback imports for different project structures
    try:
        from ui.views.main_view import MainView
        from ui.views.reference_view import ReferenceView
        from ui.views.settings_view import SettingsView
        from ui.views.calibration_view import CalibrationView
        from ui.dialogs.login_dialog import LoginInterface
        from ui.dialogs.reference_dialog import ReferenceDialog
    except ImportError:
        print("Warning: Could not import all view modules - using fallback mode")
        # Set None for missing modules
        MainView = None
        ReferenceView = None
        SettingsView = None
        CalibrationView = None
        LoginInterface = None
        ReferenceDialog = None


class MainWindow:
    """Enhanced Main Window with global controls and better state management"""
    
    def __init__(self, root, app_controller):
        self.root = root
        self.app_controller = app_controller
        self.colors = self.setup_colors()
        
        # Set this window as the main window reference in app controller
        if hasattr(self.app_controller, 'main_window'):
            self.app_controller.main_window = self
        
        # Enhanced state tracking
        self.current_view = None
        self.previous_view = None
        self.active_dialogs = []
        
        # View instances
        self.main_view = None
        self.reference_view = None
        self.settings_view = None
        self.calibration_view = None
        
        # UI components
        self.nav_button_widgets = {}
        self.status_indicator = None
        self.status_text = None
        
        # Image reference to prevent garbage collection
        self._logo_image_ref = None
        
        # Configure main window
        self.configure_window()
        
        # Setup main layout
        self.setup_main_layout()
        
        # Initialize views
        self.initialize_views()
        
        # Setup enhanced global key bindings
        self.setup_global_bindings()
        
        # Show initial view
        self.show_main_view()
        
        print("✅ Enhanced Main Window initialized with global controls")

    def setup_colors(self):
        """Initialize enhanced color scheme"""
        # Default colors
        default_colors = {
            'primary': '#00B2E3',
            'background': '#f8fafc',
            'white': '#ffffff',
            'text_primary': '#1e293b',
            'text_secondary': '#64748b',
            'error': '#ef4444',
            'border': '#e2e8f0',
            'status_bg': '#e0f2f7',
            'button_hover': '#0891b2',
            'success': '#10b981',
            'warning': '#f59e0b'
        }
        try:
            # Try to get colors from settings manager
            if hasattr(self.app_controller, 'settings_manager'):
                ui_config = self.app_controller.settings_manager.get('ui_config', {})
                colors = ui_config.get('colors', {})
                # Fill in any missing keys with defaults
                for k, v in default_colors.items():
                    if k not in colors:
                        colors[k] = v
                return colors
        except Exception:
            pass
        return default_colors

    def configure_window(self):
        """Configure main window settings"""
        # Full screen configuration
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none")
        self.root.overrideredirect(True)
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Configure background
        self.root.configure(bg=self.colors['background'])
        
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def setup_global_bindings(self):
        """Setup enhanced global key bindings - Updated to be callable"""
        try:
            # Clear any existing bindings first
            self.root.unbind_all('<Escape>')
            self.root.unbind_all('<Control-q>')
            self.root.unbind_all('<Control-e>')
            
            # Primary global bindings
            self.root.bind('<Escape>', self.handle_escape_key)
            self.root.bind('<Control-q>', self.handle_quit_shortcut)
            self.root.bind('<Control-e>', self.handle_emergency_stop)
            
            # Function keys for navigation
            self.root.bind('<F1>', lambda e: self.show_main_view())
            self.root.bind('<F2>', lambda e: self.show_reference_view())
            self.root.bind('<F3>', lambda e: self.show_login_page("Settings"))
            self.root.bind('<F4>', lambda e: self.show_login_page("Calibration"))
            
            # Quick action shortcuts
            self.root.bind('<Control-s>', self.handle_quick_start_test)
            self.root.bind('<Control-r>', self.handle_quick_reference)
            
            # Debug and development shortcuts
            self.root.bind('<Control-d>', self.toggle_debug_mode)
            self.root.bind('<Control-c>', self.toggle_cursor)
            
            # Window management
            self.root.bind('<Alt-F4>', self.handle_alt_f4)
            
            # Make sure the root has focus for key bindings
            self.root.focus_set()
            
            print("✅ Enhanced global key bindings setup complete")
            
        except Exception as e:
            print(f"Warning: Could not setup all key bindings: {e}")

    def handle_escape_key(self, event):
        """Enhanced escape key handling based on current context"""
        try:
            print(f"Escape key pressed - Current view: {self.current_view}")
            
            # Priority 1: Close active dialogs
            if self.active_dialogs:
                dialog = self.active_dialogs[-1]
                if hasattr(dialog, 'destroy'):
                    dialog.destroy()
                    self.active_dialogs.remove(dialog)
                return
            
            # Priority 2: Handle login context
            if hasattr(self, 'current_view') and self.current_view and self.current_view.startswith('Login_'):
                print("In login context - escape will be handled by login interface")
                return
            
            # Priority 3: Handle running test
            if hasattr(self.app_controller, 'is_testing') and getattr(self.app_controller, 'is_testing', False):
                self.show_stop_test_confirmation()
                return
            
            # Priority 4: Navigate back or exit based on current view
            if self.current_view == "Main":
                self.show_exit_confirmation()
            else:
                # Return to main view from other views
                print("Returning to main view via Escape")
                self.show_main_view()
                
        except Exception as e:
            print(f"Error handling escape key: {e}")

    def handle_emergency_stop(self, event):
        """Handle emergency stop activation"""
        try:
            # Show emergency notification
            self.show_emergency_notification()
            
            # Stop any running test
            if hasattr(self.app_controller, 'handle_emergency'):
                self.app_controller.handle_emergency("Emergency stop activated via Ctrl+E")
            
            # Reset UI state
            self.emergency_reset()
            
            # Return to main view
            self.show_main_view()
            
        except Exception as e:
            print(f"Error handling emergency stop: {e}")

    def handle_quit_shortcut(self, event):
        """Handle quit shortcut"""
        self.show_exit_confirmation()

    def handle_quick_start_test(self, event):
        """Quick start test from any view"""
        try:
            if self.current_view != "Main":
                self.show_main_view()
            
            # Wait a moment for view to load, then start test
            self.root.after(100, self.quick_start_test)
            
        except Exception as e:
            print(f"Error in quick start test: {e}")

    def quick_start_test(self):
        """Actually start the test"""
        try:
            if self.main_view and hasattr(self.main_view, 'start_test'):
                self.main_view.start_test()
            elif hasattr(self.app_controller, 'start_test'):
                self.app_controller.start_test()
        except Exception as e:
            print(f"Error starting test: {e}")

    def handle_quick_reference(self, event):
        """Quick reference management"""
        try:
            self.show_reference_view()
        except Exception as e:
            print(f"Error showing reference view: {e}")

    def toggle_debug_mode(self, event):
        """Toggle debug mode"""
        try:
            print("Debug mode toggled")
            # Add debug functionality here
        except Exception as e:
            print(f"Error toggling debug mode: {e}")

    def toggle_cursor(self, event):
        """Toggle cursor visibility"""
        try:
            current_cursor = self.root.config('cursor')
            new_cursor = "none" if current_cursor != "none" else "arrow"
            self.root.config(cursor=new_cursor)
            print(f"Cursor toggled to: {new_cursor}")
        except Exception as e:
            print(f"Error toggling cursor: {e}")

    def handle_alt_f4(self, event):
        """Handle Alt+F4"""
        self.show_exit_confirmation()

    def show_stop_test_confirmation(self):
        """Show confirmation dialog for stopping test"""
        try:
            # Remove messagebox confirmation - just stop the test directly
            if hasattr(self.app_controller, 'stop_test'):
                self.app_controller.stop_test()
            if self.main_view and hasattr(self.main_view, 'stop_test'):
                self.main_view.stop_test()
            print("Test stopped by user")
            self.update_system_status("Test stopped", "info")
        except Exception as e:
            print(f"Error stopping test: {e}")

    def show_exit_confirmation(self):
        """Show exit confirmation dialog"""
        try:
            # Remove messagebox confirmation - just exit directly
            self.exit_application()
        except Exception as e:
            print(f"Error during exit: {e}")

    def show_emergency_notification(self):
        """Show emergency notification"""
        try:
            # Remove messagebox - just log and update status
            print("EMERGENCY STOP ACTIVATED - System returning to main view")
            self.update_system_status("EMERGENCY STOP - System returning to main view", "error")
        except Exception as e:
            print(f"Error handling emergency notification: {e}")

    def register_dialog(self, dialog):
        """Register a dialog for escape key handling"""
        if dialog not in self.active_dialogs:
            self.active_dialogs.append(dialog)

    def close_all_dialogs(self):
        """Close all active dialogs"""
        for dialog in self.active_dialogs[:]:
            try:
                if hasattr(dialog, 'destroy'):
                    dialog.destroy()
            except:
                pass
        self.active_dialogs.clear()

    def exit_application(self):
        """Clean exit of the application"""
        try:
            # Close all dialogs
            self.close_all_dialogs()
            
            # Stop any running test
            if hasattr(self.app_controller, 'stop_test'):
                self.app_controller.stop_test()
            
            # Cleanup app controller
            if hasattr(self.app_controller, 'cleanup'):
                self.app_controller.cleanup()
            
            # Destroy the window
            self.root.destroy()
            
        except Exception as e:
            print(f"Error during exit: {e}")
            # Force exit
            self.root.destroy()

    def setup_main_layout(self):
        """Setup the main layout structure"""
        # Main container
        self.main_container = tk.Frame(self.root, bg=self.colors['background'])
        self.main_container.grid(row=0, column=0, sticky='nsew')
        
        # Configure grid weights
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Create header
        self.create_header()
        
        # Create content area
        self.content_container = tk.Frame(self.main_container, bg=self.colors['background'])
        self.content_container.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        # Configure content grid
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    def check_logo_availability(self):
        """Check if logo file is available"""
        logo_paths = [
            "ui/assets/logo.png",  # Primary path
            "assets/logo.png",
            "logo.png",
            "../ui/assets/logo.png",  # Try relative path
            "./ui/assets/logo.png"    # Try current directory
        ]
        
        for path in logo_paths:
            if os.path.exists(path):
                print(f"Logo found at: {path}")
                return path
        print("Logo not found in any expected location")
        return None

    def create_header(self):
        """Create the application header"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['white'], height=80)
        header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 0))
        header_frame.grid_propagate(False)
        
        # Configure header grid
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Check logo availability first
        logo_path = self.check_logo_availability()
        
        # Load and display logo
        logo_photo = self.load_and_resize_logo()
        if logo_photo:
            logo_label = tk.Label(
                header_frame,
                image=logo_photo,
                bg=self.colors['white']
            )
            # Keep a reference to prevent garbage collection
            logo_label.image = logo_photo  # type: ignore
            print("Logo image displayed successfully")
        else:
            # Fallback to emoji if logo not available
            logo_label = tk.Label(
                header_frame,
                text="🔧",  # Using emoji as fallback
                font=('Arial', 24),
                bg=self.colors['white'],
                fg=self.colors['primary']
            )
            print("Using emoji fallback for logo")
        logo_label.grid(row=0, column=0, padx=(20, 10), pady=20)
        
        # System status indicator
        self.create_system_status_indicator(header_frame)
        
        # Navigation buttons
        nav_container = tk.Frame(header_frame, bg=self.colors['white'])
        nav_container.grid(row=0, column=3, padx=(0, 20), pady=20)
        
        self.create_navigation_buttons(nav_container)

    def create_system_status_indicator(self, parent):
        """Create system status indicator"""
        status_frame = tk.Frame(parent, bg=self.colors['white'])
        status_frame.grid(row=0, column=2, padx=20, pady=20)
        
        # Status indicator
        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=('Arial', 16),
            bg=self.colors['white'],
            fg=self.colors['success']
        )
        self.status_indicator.pack()
        
        # Status text
        self.status_text = tk.Label(
            status_frame,
            text="Ready",
            font=('Arial', 10),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        self.status_text.pack()

    def create_navigation_buttons(self, nav_container):
        """Create navigation buttons"""
        buttons = [
            ("Main", "Main Test"),
            ("Reference", "References"),
            ("Settings", "Settings"),
            ("Calibration", "Calibration")
        ]
        
        for i, (key, text) in enumerate(buttons):
            btn = tk.Button(
                nav_container,
                text=text,
                font=('Arial', 10, 'bold'),
                bg=self.colors['primary'],
                fg=self.colors['white'],
                activebackground=self.colors['button_hover'],
                activeforeground=self.colors['white'],
                relief='flat',
                padx=15, pady=5,
                command=lambda k=key: self.handle_navigation(k)
            )
            btn.pack(side='left', padx=5)
            
            # Store button reference
            self.nav_button_widgets[key] = btn
            
            # Add hover effects
            btn.bind('<Enter>', lambda e, b=btn: self.on_button_hover(b))
            btn.bind('<Leave>', lambda e, b=btn: self.on_button_leave(b))

    def load_and_resize_logo(self):
        """Load and resize logo image"""
        try:
            if PIL_AVAILABLE:
                # Try to load logo from various locations
                logo_paths = [
                    "ui/assets/logo.png",  # Primary path
                    "assets/logo.png",
                    "logo.png",
                    "../ui/assets/logo.png",  # Try relative path
                    "./ui/assets/logo.png"    # Try current directory
                ]
                
                for path in logo_paths:
                    print(f"Trying to load logo from: {path}")
                    if os.path.exists(path):
                        print(f"Found logo at: {path}")
                        image = Image.open(path)
                        # Resize to appropriate size
                        image = image.resize((420, 70), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        self._logo_image_ref = photo  # Keep reference
                        print(f"Logo loaded successfully from: {path}")
                        return photo
                    else:
                        print(f"Logo not found at: {path}")
                
                print("Logo not found in any of the expected locations")
                return None
            else:
                print("PIL not available - cannot load logo image")
                return None
                
        except Exception as e:
            print(f"Error loading logo: {e}")
            import traceback
            traceback.print_exc()
            return None

    def on_button_hover(self, button):
        """Handle button hover effect"""
        button.configure(bg=self.colors['button_hover'])

    def on_button_leave(self, button):
        """Handle button leave effect"""
        button.configure(bg=self.colors['primary'])

    def update_navigation_state(self, active_view):
        """Update navigation button states - Enhanced version"""
        try:
            for key, button in self.nav_button_widgets.items():
                if key == active_view:
                    button.configure(bg=self.colors['button_hover'])
                else:
                    button.configure(bg=self.colors['primary'])
        except Exception as e:
            print(f"Error updating navigation state: {e}")

    def update_system_status(self, status, level="info"):
        """Update system status display"""
        try:
            color_map = {
                'info': self.colors['success'],
                'warning': self.colors['warning'],
                'error': self.colors['error']
            }
            
            if self.status_indicator:
                self.status_indicator.configure(fg=color_map.get(level, self.colors['success']))
            
            if self.status_text:
                self.status_text.configure(text=status)
                
        except Exception as e:
            print(f"Error updating system status: {e}")

    def initialize_views(self):
        """Initialize view instances"""
        try:
            # Initialize views as None - they will be created when needed
            self.main_view = None
            self.reference_view = None
            self.settings_view = None
            self.calibration_view = None
            
        except Exception as e:
            print(f"Error initializing views: {e}")

    def handle_navigation(self, button_text):
        """Handle navigation button clicks"""
        try:
            if button_text == "Main":
                self.show_main_view()
            elif button_text == "Reference":
                self.show_reference_view()
            elif button_text == "Settings":
                self.show_login_page("Settings")
            elif button_text == "Calibration":
                self.show_login_page("Calibration")
                
        except Exception as e:
            print(f"Error handling navigation: {e}")

    def show_login_page(self, target_page):
        """Show login page for protected areas - Improved version"""
        try:
            print(f"Showing login page for {target_page}")
            
            # Store current view for restoration if login is cancelled
            self.previous_view = self.current_view
            
            if LoginInterface is not None:
                # Create login interface - it will handle clearing content
                login_dialog = LoginInterface(self, self.show_protected_page, target_page)
                
                # Update navigation state to show we're in login mode
                self.update_navigation_state(None)
                self.update_system_status(f"Login required for {target_page}", "warning")
                
            else:
                # No login interface available - show page directly
                print("LoginInterface not available - showing page directly")
                self.show_protected_page(target_page)
                
        except Exception as e:
            print(f"Error showing login page: {e}")
            # Fallback - show protected page directly
            self.show_protected_page(target_page)

    def show_protected_page(self, page_name):
        """Show protected page after successful login"""
        try:
            print(f"Showing protected page: {page_name}")
            
            if page_name == "Settings":
                self.show_settings_view()
            elif page_name == "Calibration":
                self.show_calibration_view()
            else:
                print(f"Unknown protected page: {page_name}")
                self.show_main_view()
                
        except Exception as e:
            print(f"Error showing protected page: {e}")
            self.show_main_view()

    def hide_all_views(self):
        """Hide all current views"""
        try:
            # Cleanup reference view specifically since it has async operations
            if self.current_view == "Reference" and self.reference_view and hasattr(self.reference_view, 'cleanup'):
                self.reference_view.cleanup()
            
            # Clear all widgets from content container
            for widget in self.content_container.winfo_children():
                try:
                    widget.destroy()
                except Exception as e:
                    print(f"Error destroying widget: {e}")
                    
        except Exception as e:
            print(f"Error hiding views: {e}")

    def show_main_view(self):
        """Show main test view"""
        try:
            self.hide_all_views()
            self.current_view = "Main"
            self.update_navigation_state("Main")
            
            if MainView is not None:
                self.main_view = MainView(self.content_container, self.app_controller, self.colors)
                self.main_view.show()
            else:
                self.create_fallback_main_view()
            
            self.update_system_status("Main Test View", "info")
            
        except Exception as e:
            print(f"Error showing main view: {e}")
            self.create_fallback_main_view()

    def show_reference_view(self):
        """Show reference management view"""
        try:
            self.hide_all_views()
            self.current_view = "Reference"
            self.update_navigation_state("Reference")
            
            if ReferenceView is not None:
                self.reference_view = ReferenceView(self.content_container, self.app_controller, self.colors)
                self.reference_view.show()
            else:
                self.create_fallback_reference_view()
            
            self.update_system_status("Reference Management", "info")
            
        except Exception as e:
            print(f"Error showing reference view: {e}")
            self.create_fallback_reference_view()

    def show_settings_view(self):
        """Show settings view"""
        try:
            self.hide_all_views()
            self.current_view = "Settings"
            self.update_navigation_state("Settings")
            
            if SettingsView is not None:
                self.settings_view = SettingsView(self.content_container, self.app_controller, self.colors)
                self.settings_view.show()
            else:
                self.create_fallback_settings_view()
            
            self.update_system_status("Settings Configuration", "info")
            
        except Exception as e:
            print(f"Error showing settings view: {e}")
            self.create_fallback_settings_view()

    def show_calibration_view(self):
        """Show calibration view"""
        try:
            self.hide_all_views()
            self.current_view = "Calibration"
            self.update_navigation_state("Calibration")
            
            if CalibrationView is not None:
                self.calibration_view = CalibrationView(self.content_container, self.app_controller, self.colors)
                self.calibration_view.show()
            else:
                self.create_fallback_calibration_view()
            
            self.update_system_status("System Calibration", "info")
            
        except Exception as e:
            print(f"Error showing calibration view: {e}")
            self.create_fallback_calibration_view()

    def open_add_reference_dialog(self):
        """Open dialog to add a new reference"""
        try:
            if ReferenceDialog is not None:
                dialog = ReferenceDialog(self.app_controller, self.colors, callback=self.refresh_current_view)
                if hasattr(dialog, 'dialog'):
                    self.register_dialog(dialog.dialog)
            else:
                # Remove messagebox - just log the error
                print("Reference dialog functionality is not available - Module could not be imported")
                self.update_system_status("Reference dialog unavailable", "warning")
        except Exception as e:
            print(f"Error opening add reference dialog: {e}")

    def refresh_current_view(self):
        """Refresh the current view"""
        try:
            if self.current_view == "Main" and self.main_view:
                if hasattr(self.main_view, 'update_test_parameters'):
                    self.main_view.update_test_parameters()
            elif self.current_view == "Reference" and self.reference_view:
                if hasattr(self.reference_view, 'refresh_view'):
                    self.reference_view.refresh_view()
        except Exception as e:
            print(f"Error refreshing view: {e}")

    def create_fallback_main_view(self):
        """Create fallback main view when MainView is not available"""
        fallback_frame = tk.Frame(self.content_container, bg=self.colors['white'])
        fallback_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(
            fallback_frame,
            text="Main Test View",
            font=('Arial', 18, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        ).pack(pady=20)
        
        tk.Label(
            fallback_frame,
            text="Enhanced features active:\n• Global escape key\n• Emergency stop (Ctrl+E)\n• Quick navigation (F1-F4)\n• Test controls (Ctrl+S)",
            font=('Arial', 12),
            bg=self.colors['white'],
            fg=self.colors['text_primary'],
            justify='left'
        ).pack(pady=10)

    def create_fallback_reference_view(self):
        """Create fallback reference view"""
        fallback_frame = tk.Frame(self.content_container, bg=self.colors['white'])
        fallback_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(
            fallback_frame,
            text="Reference Management",
            font=('Arial', 18, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        ).pack(pady=20)
        
        tk.Label(
            fallback_frame,
            text="Reference management functionality will be available\nwhen ReferenceView module is properly imported.",
            font=('Arial', 12),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        ).pack(pady=10)

    def create_fallback_settings_view(self):
        """Create fallback settings view"""
        fallback_frame = tk.Frame(self.content_container, bg=self.colors['white'])
        fallback_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(
            fallback_frame,
            text="Settings",
            font=('Arial', 18, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        ).pack(pady=20)
        
        tk.Label(
            fallback_frame,
            text="Settings configuration will be available\nwhen SettingsView module is properly imported.",
            font=('Arial', 12),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        ).pack(pady=10)

    def create_fallback_calibration_view(self):
        """Create fallback calibration view"""
        fallback_frame = tk.Frame(self.content_container, bg=self.colors['white'])
        fallback_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(
            fallback_frame,
            text="Calibration",
            font=('Arial', 18, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        ).pack(pady=20)
        
        tk.Label(
            fallback_frame,
            text="System calibration functionality will be available\nwhen CalibrationView module is properly imported.",
            font=('Arial', 12),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        ).pack(pady=10)

    # Additional helper methods for better state management

    def get_current_view_name(self):
        """Get the current view name"""
        return getattr(self, 'current_view', 'Unknown')

    def is_in_login_mode(self):
        """Check if currently in login mode"""
        return (hasattr(self, 'current_view') and 
                self.current_view and 
                self.current_view.startswith('Login_'))

    def restore_previous_view(self):
        """Restore the previous view (used by login cancellation)"""
        try:
            if hasattr(self, 'previous_view') and self.previous_view:
                if self.previous_view == "Main":
                    self.show_main_view()
                elif self.previous_view == "Reference":
                    self.show_reference_view()
                else:
                    self.show_main_view()
            else:
                self.show_main_view()
        except Exception as e:
            print(f"Error restoring previous view: {e}")
            self.show_main_view()

    # Additional utility methods for enhanced functionality
    def set_app_controller_status_callback(self):
        """Set this window as the status callback for the app controller"""
        if hasattr(self.app_controller, 'set_status_callback'):
            self.app_controller.set_status_callback(self.update_system_status)

    def update_test_display(self, pressure=None, duration=None):
        """Update test displays if main view is active"""
        try:
            if self.main_view and hasattr(self.main_view, 'update_pressure_display') and pressure is not None:
                self.main_view.update_pressure_display(pressure)
            if self.main_view and hasattr(self.main_view, 'update_duration_display') and duration is not None:
                self.main_view.update_duration_display(duration)
        except Exception as e:
            print(f"Error updating test display: {e}")

    def emergency_reset(self):
        """Reset UI state after emergency"""
        try:
            if self.main_view and hasattr(self.main_view, 'reset_ui_state'):
                self.main_view.reset_ui_state()
            self.update_system_status("Emergency reset - System ready", "warning")
        except Exception as e:
            print(f"Error in emergency reset: {e}")