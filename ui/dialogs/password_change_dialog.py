"""
Password Change Dialog
A modal dialog for changing system password with validation and feedback
"""

import tkinter as tk
import hashlib
import platform
from ..components.keyboard import VirtualKeyboard


class PasswordChangeDialog:
    """Modal dialog for changing system password"""
    
    def __init__(self, parent, app_controller, colors=None):
        print("PasswordChangeDialog.__init__() called")
        self.parent = parent
        self.app_controller = app_controller
        self.colors = colors or self.get_default_colors()
        self.result = None
        
        print("Creating Toplevel window...")
        # Create modal window with enhanced fullscreen compatibility
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Password")
        self.dialog.geometry("600x700")
        self.dialog.configure(bg=self.colors['white'])
        self.dialog.resizable(False, False)
        
        # Enhanced fullscreen compatibility
        self.dialog.attributes('-topmost', True)
        # Note: -alwaysontop is Windows-specific, removed for cross-platform compatibility
        
        # Platform-specific enhancements
        if platform.system() == "Linux":
            # Linux-specific: ensure proper window stacking
            self.dialog.attributes('-type', 'dialog')
        elif platform.system() == "Windows":
            # Windows-specific: can use additional attributes
            try:
                self.dialog.attributes('-alwaysontop', True)
            except tk.TclError:
                pass  # Ignore if not supported
        
        print("Setting up modal behavior...")
        # Enhanced modal behavior for fullscreen applications
        self.dialog.transient(parent)
        
        # For fullscreen applications, try non-modal approach first
        print("Attempting non-modal approach for fullscreen compatibility")
        try:
            # Don't use grab_set() initially - try without it
            # self.dialog.grab_set()  # Commented out for fullscreen compatibility
            print("Using non-modal approach (no grab_set)")
        except tk.TclError:
            print("Warning: grab_set failed, using alternative approach")
            # Alternative approach for fullscreen compatibility
            self.dialog.attributes('-topmost', True)
        
        # Center the window
        self.center_window()
        
        # Password variables
        self.current_password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.status_var = tk.StringVar()
        
        # Track which field is active
        self.active_field = 'current'
        
        print("Creating interface...")
        # Create the interface
        self.create_interface()
        
        # Setup key bindings
        self.setup_key_bindings()
        
        # Focus on first field
        self.current_password_entry.focus_set()
        
        print("PasswordChangeDialog initialization complete")

    def get_default_colors(self):
        """Default color scheme if none provided"""
        return {
            'primary': '#00B2E3',
            'secondary': '#6B7280',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'white': '#FFFFFF',
            'background': '#f8fafc',
            'border': '#d1d5db',
            'text_primary': '#1f2937',
            'text_secondary': '#6b7280',
            'button_hover': '#0091cc'
        }

    def center_window(self):
        """Center the dialog window"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300)
        y = (self.dialog.winfo_screenheight() // 2) - (350)
        self.dialog.geometry(f"600x700+{x}+{y}")

    def create_interface(self):
        """Create the dialog interface"""
        # Header
        self.create_header()
        
        # Password fields
        self.create_password_fields()
        
        # Virtual keyboard
        self.create_keyboard()
        
        # Buttons
        self.create_buttons()
        
        # Status
        self.create_status()

    def create_header(self):
        """Create dialog header"""
        header_frame = tk.Frame(self.dialog, bg=self.colors['primary'], height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title = tk.Label(header_frame,
                        text="🔒 Change Password",
                        bg=self.colors['primary'],
                        fg=self.colors['white'],
                        font=('Arial', 18, 'bold'))
        title.pack(expand=True)
        
        subtitle = tk.Label(header_frame,
                           text="Update your system password",
                           bg=self.colors['primary'],
                           fg=self.colors['white'],
                           font=('Arial', 11))
        subtitle.pack()

    def create_password_fields(self):
        """Create password input fields"""
        fields_frame = tk.Frame(self.dialog, bg=self.colors['white'])
        fields_frame.pack(fill='x', padx=30, pady=20)
        
        # Current password
        self.create_password_field(fields_frame, "Current Password:", 
                                 self.current_password_var, 'current')
        
        # New password
        self.create_password_field(fields_frame, "New Password:", 
                                 self.new_password_var, 'new')
        
        # Confirm password
        self.create_password_field(fields_frame, "Confirm New Password:", 
                                 self.confirm_password_var, 'confirm')

    def create_password_field(self, parent, label_text, text_var, field_name):
        """Create a single password field"""
        field_frame = tk.Frame(parent, bg=self.colors['white'])
        field_frame.pack(fill='x', pady=10)
        
        # Label
        label = tk.Label(field_frame,
                        text=label_text,
                        font=('Arial', 12, 'bold'),
                        bg=self.colors['white'],
                        fg=self.colors['text_primary'])
        label.pack(anchor='w')
        
        # Entry with border
        entry_container = tk.Frame(field_frame,
                                  bg=self.colors['white'],
                                  highlightbackground=self.colors['border'],
                                  highlightthickness=1,
                                  relief='solid')
        entry_container.pack(fill='x', pady=5)
        
        entry = tk.Entry(entry_container,
                        textvariable=text_var,
                        show='*',
                        font=('Arial', 14),
                        bg=self.colors['white'],
                        fg=self.colors['text_primary'],
                        relief='flat',
                        highlightthickness=0,
                        bd=10)
        entry.pack(fill='x', padx=10, pady=10)
        
        # Store reference based on field name
        if field_name == 'current':
            self.current_password_entry = entry
        elif field_name == 'new':
            self.new_password_entry = entry
        elif field_name == 'confirm':
            self.confirm_password_entry = entry
        
        # Bind focus events
        entry.bind('<FocusIn>', lambda e, f=field_name: self.set_active_field(f))
        entry.bind('<Return>', self.change_password)

    def create_keyboard(self):
        """Create virtual keyboard"""
        keyboard_frame = tk.Frame(self.dialog, bg=self.colors['background'])
        keyboard_frame.pack(fill='x', padx=20, pady=10)
        
        # Create virtual keyboard with correct constructor signature
        self.keyboard = VirtualKeyboard(
            keyboard_frame, 
            self.colors, 
            callback=self.change_password
        )
        
        # Set up keyboard handlers
        self.keyboard.set_key_handler(self.handle_key_input)
        self.keyboard.set_backspace_handler(self.handle_backspace)
        self.keyboard.set_clear_handler(self.clear_all_fields)
        
        # Create the keyboard widget
        keyboard_widget = self.keyboard.create()

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = tk.Frame(self.dialog, bg=self.colors['white'])
        button_frame.pack(fill='x', padx=30, pady=20)
        
        # Change password button
        change_btn = tk.Button(button_frame,
                              text="✓ Change Password",
                              command=self.change_password,
                              font=('Arial', 12, 'bold'),
                              bg=self.colors['success'],
                              fg=self.colors['white'],
                              activebackground='#059669',
                              activeforeground=self.colors['white'],
                              relief='flat',
                              padx=20,
                              pady=10)
        change_btn.pack(side='left', padx=(0, 10))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame,
                              text="✗ Cancel",
                              command=self.cancel,
                              font=('Arial', 12, 'bold'),
                              bg=self.colors['error'],
                              fg=self.colors['white'],
                              activebackground='#dc2626',
                              activeforeground=self.colors['white'],
                              relief='flat',
                              padx=20,
                              pady=10)
        cancel_btn.pack(side='right')

    def create_status(self):
        """Create status display"""
        status_frame = tk.Frame(self.dialog, bg=self.colors['white'])
        status_frame.pack(fill='x', padx=30, pady=(0, 20))
        
        self.status_label = tk.Label(status_frame,
                                    textvariable=self.status_var,
                                    font=('Arial', 11),
                                    bg=self.colors['white'],
                                    fg=self.colors['text_secondary'],
                                    wraplength=500)
        self.status_label.pack()

    def setup_key_bindings(self):
        """Setup keyboard bindings"""
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.bind('<Return>', lambda e: self.change_password())

    def set_active_field(self, field_name):
        """Set which field is currently active"""
        self.active_field = field_name
        self.clear_status()

    def handle_key_input(self, key):
        """Handle virtual keyboard input"""
        if self.active_field == 'current':
            current = self.current_password_var.get()
            self.current_password_var.set(current + key)
        elif self.active_field == 'new':
            current = self.new_password_var.get()
            self.new_password_var.set(current + key)
        elif self.active_field == 'confirm':
            current = self.confirm_password_var.get()
            self.confirm_password_var.set(current + key)
        
        self.clear_status()

    def handle_backspace(self):
        """Handle backspace from virtual keyboard"""
        if self.active_field == 'current':
            current = self.current_password_var.get()
            if current:
                self.current_password_var.set(current[:-1])
        elif self.active_field == 'new':
            current = self.new_password_var.get()
            if current:
                self.new_password_var.set(current[:-1])
        elif self.active_field == 'confirm':
            current = self.confirm_password_var.get()
            if current:
                self.confirm_password_var.set(current[:-1])
        
        self.clear_status()

    def clear_all_fields(self):
        """Clear all password fields"""
        self.current_password_var.set('')
        self.new_password_var.set('')
        self.confirm_password_var.set('')
        self.clear_status()
        self.current_password_entry.focus_set()

    def clear_status(self):
        """Clear status message"""
        self.status_var.set('')

    def show_status(self, message, status_type='info'):
        """Show status message with appropriate color"""
        self.status_var.set(message)
        
        if status_type == 'success':
            color = self.colors['success']
        elif status_type == 'error':
            color = self.colors['error']
        elif status_type == 'warning':
            color = self.colors['warning']
        else:
            color = self.colors['text_secondary']
        
        self.status_label.config(fg=color)

    def change_password(self, event=None):
        """Change the password with validation"""
        try:
            current = self.current_password_var.get().strip()
            new_pwd = self.new_password_var.get().strip()
            confirm = self.confirm_password_var.get().strip()
            
            # Validate current password
            if not current:
                self.show_status("Current password required", 'error')
                self.current_password_entry.focus_set()
                return
            
            # Get stored password hash
            stored_hash = self.app_controller.settings.get("password_hash", "")
            current_hash = hashlib.sha256(current.encode()).hexdigest()
            
            if current_hash != stored_hash:
                self.show_status("Current password is incorrect", 'error')
                self.current_password_entry.focus_set()
                return
            
            # Validate new password
            if not new_pwd:
                self.show_status("New password required", 'error')
                self.new_password_entry.focus_set()
                return
            
            if len(new_pwd) < 6:
                self.show_status("Password too short (minimum 6 characters)", 'error')
                self.new_password_entry.focus_set()
                return
            
            if new_pwd != confirm:
                self.show_status("New passwords do not match", 'error')
                self.confirm_password_entry.focus_set()
                return
            
            # Check if new password is same as current
            new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
            if new_hash == stored_hash:
                self.show_status("New password must be different from current password", 'error')
                self.new_password_entry.focus_set()
                return
            
            # Update password
            self.app_controller.settings["password_hash"] = new_hash
            self.app_controller.save_settings()
            
            # Show success and close after delay
            self.show_status("Password changed successfully!", 'success')
            self.result = True
            
            # Close dialog after brief delay
            self.dialog.after(1500, self.close_success)
            
        except Exception as e:
            self.show_status(f"Error changing password: {str(e)}", 'error')

    def close_success(self):
        """Close dialog after successful password change"""
        self.dialog.grab_release()
        self.dialog.destroy()

    def cancel(self):
        """Cancel password change"""
        self.result = False
        self.dialog.grab_release()
        self.dialog.destroy()

    def show(self):
        """Show the dialog and return result"""
        print("PasswordChangeDialog.show() called")
        try:
            # Check if dialog exists
            if not hasattr(self, 'dialog') or not self.dialog:
                print("Error: Dialog not created")
                return False
            
            print(f"Dialog exists: {self.dialog}")
            print(f"Dialog state: {self.dialog.state()}")
            
            # Aggressive visibility approach for fullscreen applications
            print("Making dialog visible...")
            
            # Step 1: Force the dialog to be on top
            self.dialog.attributes('-topmost', True)
            # Note: -alwaysontop is Windows-specific, removed for cross-platform compatibility
            
            # Step 2: Show the dialog
            self.dialog.deiconify()
            
            # Step 3: Force it to the front
            self.dialog.lift()
            self.dialog.focus_force()
            
            # Step 4: Update and force redraw
            self.dialog.update_idletasks()
            self.dialog.update()
            
            # Step 5: Additional visibility checks with multiple attempts
            self.dialog.after(50, self._force_visibility_attempt_1)
            self.dialog.after(150, self._force_visibility_attempt_2)
            self.dialog.after(300, self._force_visibility_attempt_3)
            
            # Step 6: Final visibility check
            self.dialog.after(500, self._final_visibility_check)
            
            # Add timeout mechanism (increased to 10 seconds)
            self.dialog.after(10000, self._timeout_handler)
            
            print("Dialog should now be visible")
            print(f"Dialog state after show: {self.dialog.state()}")
            print("Waiting for dialog to close...")
            
            # Wait for dialog to close
            self.dialog.wait_window()
            
            print(f"Dialog closed, result: {self.result}")
            return self.result
            
        except Exception as e:
            print(f"Error in show() method: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _force_visibility_attempt_1(self):
        """First attempt to force visibility"""
        try:
            if hasattr(self, 'dialog') and self.dialog and self.dialog.winfo_exists():
                print("Visibility attempt 1: Force to top")
                self.dialog.lift()
                self.dialog.focus_force()
                self.dialog.update()
        except Exception as e:
            print(f"Error in visibility attempt 1: {e}")

    def _force_visibility_attempt_2(self):
        """Second attempt to force visibility"""
        try:
            if hasattr(self, 'dialog') and self.dialog and self.dialog.winfo_exists():
                print("Visibility attempt 2: Deiconify and lift")
                self.dialog.deiconify()
                self.dialog.lift()
                self.dialog.focus_force()
                self.dialog.update()
        except Exception as e:
            print(f"Error in visibility attempt 2: {e}")

    def _force_visibility_attempt_3(self):
        """Third attempt to force visibility"""
        try:
            if hasattr(self, 'dialog') and self.dialog and self.dialog.winfo_exists():
                print("Visibility attempt 3: Full visibility reset")
                self.dialog.withdraw()
                self.dialog.deiconify()
                self.dialog.lift()
                self.dialog.focus_force()
                self.dialog.update()
        except Exception as e:
            print(f"Error in visibility attempt 3: {e}")

    def _final_visibility_check(self):
        """Final check to ensure dialog is visible"""
        try:
            if hasattr(self, 'dialog') and self.dialog and self.dialog.winfo_exists():
                if not self.dialog.winfo_viewable():
                    print("WARNING: Dialog still not viewable after all attempts!")
                    print("Trying emergency visibility fix...")
                    # Emergency fix: try to force it visible
                    self.dialog.attributes('-topmost', True)
                    self.dialog.deiconify()
                    self.dialog.lift()
                    self.dialog.focus_force()
                    self.dialog.update()
                else:
                    print("SUCCESS: Dialog is now viewable!")
                    # Now that it's visible, try to make it modal
                    self.dialog.after(1000, self._enable_modal_behavior)
        except Exception as e:
            print(f"Error in final visibility check: {e}")

    def _enable_modal_behavior(self):
        """Enable modal behavior after dialog is visible"""
        try:
            if hasattr(self, 'dialog') and self.dialog and self.dialog.winfo_exists():
                print("Attempting to enable modal behavior...")
                try:
                    self.dialog.grab_set()
                    print("Modal behavior enabled successfully")
                except tk.TclError:
                    print("Modal behavior could not be enabled, continuing without it")
        except Exception as e:
            print(f"Error enabling modal behavior: {e}")

    def _timeout_handler(self):
        """Handle timeout if dialog doesn't close properly"""
        try:
            if hasattr(self, 'dialog') and self.dialog and self.dialog.winfo_exists():
                print("Dialog timeout - forcing close")
                self.result = False
                self.dialog.grab_release()
                self.dialog.destroy()
        except Exception as e:
            print(f"Error in timeout handler: {e}")


def show_password_change_dialog(parent, app_controller, colors=None):
    """Convenience function to show password change dialog"""
    print("Creating password change dialog...")
    print(f"Parent window: {parent}")
    print(f"Parent window type: {type(parent)}")
    
    try:
        # Check if parent is valid
        if not parent or not parent.winfo_exists():
            print("Error: Parent window is not valid")
            return False
        
        dialog = PasswordChangeDialog(parent, app_controller, colors)
        print("Password change dialog created successfully")
        print("Showing password change dialog...")
        result = dialog.show()
        print(f"Password change dialog closed with result: {result}")
        return result
    except Exception as e:
        print(f"Error in show_password_change_dialog: {e}")
        import traceback
        traceback.print_exc()
        return False 