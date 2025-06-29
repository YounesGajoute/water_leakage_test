"""
Enhanced Login Dialog - Fixed Split View Issue
Properly clears existing content before showing login interface
"""

import tkinter as tk
import hashlib
from ..components.keyboard import VirtualKeyboard
from .password_change_dialog import show_password_change_dialog


class LoginInterface:
    """Login interface for protected pages - Fixed version"""
    
    def __init__(self, main_window, callback, target_page):
        self.main_window = main_window
        self.callback = callback
        self.target_page = target_page
        self.colors = main_window.colors
        
        self.password = ""
        
        # Store the previous view for restoration if cancelled
        self.previous_view = getattr(main_window, 'current_view', 'Main')
        
        # Clear existing content and create login interface
        self.create_login_interface()

    def create_login_interface(self):
        """Create the login interface - Fixed to properly clear content"""
        # CRITICAL FIX: Clear existing content first
        self.clear_existing_content()
        
        # Update main window state
        self.main_window.current_view = f"Login_{self.target_page}"
        self.main_window.update_navigation_state(None)  # Deactivate all nav buttons
        
        # Create login frame in the cleared content container
        self.login_frame = tk.Frame(self.main_window.content_container, 
                                   bg=self.colors['white'],
                                   highlightbackground=self.colors['border'],
                                   highlightthickness=1)
        self.login_frame.pack(fill='both', expand=True, pady=20, padx=20)
        
        # Setup key bindings for login interface
        self.setup_login_key_bindings()
        
        # Create header with title and back button
        self.create_header()
        
        # Create password input section
        self.create_password_section()
        
        # Create virtual keyboard
        self.create_keyboard()
        
        print(f"Login interface created for {self.target_page} - content cleared properly")

    def clear_existing_content(self):
        """Clear existing content from the content container"""
        try:
            # This is the critical fix - clear all existing widgets
            for widget in self.main_window.content_container.winfo_children():
                widget.destroy()
            print("Existing content cleared from content container")
        except Exception as e:
            print(f"Error clearing content: {e}")

    def setup_login_key_bindings(self):
        """Setup key bindings for login interface"""
        # Bind Escape to go back to main view
        self.login_frame.bind('<Escape>', self.handle_login_escape)
        
        # Bind Enter to verify password
        self.login_frame.bind('<Return>', lambda e: self.verify_password())
        
        # Make login frame focusable and set focus
        self.login_frame.focus_set()
        
        # Ensure main window also gets the escape binding
        self.main_window.root.bind('<Escape>', self.handle_login_escape)
        
        print("Login interface key bindings established")

    def handle_login_escape(self, event=None):
        """Handle Escape key press in login context"""
        print("Escape pressed in login interface - returning to previous view")
        self.go_back()

    def create_header(self):
        """Create header with back button and title"""
        header_frame = tk.Frame(self.login_frame, bg=self.colors['white'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Back button with enhanced styling
        back_btn = tk.Button(header_frame,
                           text="← Back (ESC)",
                           font=('Arial', 12, 'bold'),
                           bg=self.colors['background'],
                           fg=self.colors['primary'],
                           activebackground=self.colors['primary'],
                           activeforeground=self.colors['white'],
                           relief='flat',
                           padx=15,
                           pady=8,
                           command=self.go_back)
        back_btn.pack(side='left', padx=10)
        
        # Title with better spacing
        title = tk.Label(header_frame,
                        text=f"Enter Password for {self.target_page}",
                        bg=self.colors['white'],
                        fg=self.colors['primary'],
                        font=('Arial', 18, 'bold'))
        title.pack(pady=15)
        
        # Security notice
        notice = tk.Label(header_frame,
                         text="Protected area - Administrator access required",
                         bg=self.colors['white'],
                         fg=self.colors['text_secondary'],
                         font=('Arial', 10))
        notice.pack(pady=(0, 10))

    def create_password_section(self):
        """Create password input section with password hint"""
        password_container = tk.Frame(self.login_frame, bg=self.colors['white'])
        password_container.pack(pady=30)
        
        # Password input frame with border
        password_frame = tk.Frame(password_container, 
                                 bg=self.colors['white'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1,
                                 relief='solid')
        password_frame.pack(pady=10, padx=20)
        
        # Password label
        pwd_label = tk.Label(password_frame,
                           text="Password:",
                           font=('Arial', 14, 'bold'),
                           bg=self.colors['white'],
                           fg=self.colors['text_primary'])
        pwd_label.pack(pady=(15, 5))
        
        # Password entry with better styling
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(password_frame,
                                     textvariable=self.password_var,
                                     show='*',
                                     font=('Arial', 16),
                                     width=20,
                                     justify='center',
                                     relief='solid',
                                     bd=1,
                                     highlightthickness=2,
                                     highlightcolor=self.colors['primary'])
        self.password_entry.pack(pady=10, padx=15)
        
        # Bind Enter key to password entry
        self.password_entry.bind('<Return>', lambda e: self.verify_password())
        self.password_entry.bind('<Button-1>', lambda e: self.password_entry.focus_set())
        
        # Character counter (helpful for users)
        self.char_count_label = tk.Label(password_frame,
                                       text="0 characters",
                                       font=('Arial', 9),
                                       bg=self.colors['white'],
                                       fg=self.colors['text_secondary'])
        self.char_count_label.pack()
        
        # Update character count as user types
        self.password_var.trace_add('write', self.update_char_count)
        
        # Error message label with better styling
        self.error_label = tk.Label(password_frame,
                                  text="",
                                  bg=self.colors['white'],
                                  fg=self.colors['error'],
                                  font=('Arial', 12),
                                  wraplength=300)
        self.error_label.pack(pady=(5, 15))

    def create_keyboard(self):
        """Create virtual keyboard for password input"""
        keyboard_frame = tk.Frame(self.login_frame, bg=self.colors['white'])
        keyboard_frame.pack(pady=20)
        
        # Keyboard title
        keyboard_title = tk.Label(keyboard_frame,
                                 text="Virtual Keyboard",
                                 font=('Arial', 12, 'bold'),
                                 bg=self.colors['white'],
                                 fg=self.colors['primary'])
        keyboard_title.pack(pady=(0, 10))
        
        # Create virtual keyboard
        self.keyboard = VirtualKeyboard(keyboard_frame, self.colors, callback=self.verify_password)
        self.keyboard.set_key_handler(self.handle_key_input)
        self.keyboard.set_backspace_handler(self.handle_backspace)
        keyboard_widget = self.keyboard.create()
        
        # Create control buttons with better layout
        self.create_control_buttons(keyboard_frame)

    def create_control_buttons(self, parent):
        """Create control buttons with improved layout"""
        control_frame = tk.Frame(parent, bg=self.colors['white'])
        control_frame.pack(pady=30)
        
        # Button container for centering
        button_container = tk.Frame(control_frame, bg=self.colors['white'])
        button_container.pack()
        
        # Login button with enhanced styling
        login_btn = tk.Button(button_container,
                            text="🔓 Login",
                            width=15,
                            height=2,
                            font=('Arial', 12, 'bold'),
                            bg=self.colors['primary'],
                            fg=self.colors['white'],
                            activebackground=self.colors['button_hover'],
                            activeforeground=self.colors['white'],
                            relief='flat',
                            command=self.verify_password)
        login_btn.pack(side='left', padx=10)
        
        # Clear button
        clear_btn = tk.Button(button_container,
                            text="🗑️ Clear",
                            width=12,
                            height=2,
                            font=('Arial', 12),
                            bg=self.colors['background'],
                            fg=self.colors['text_primary'],
                            activebackground=self.colors['primary'],
                            activeforeground=self.colors['white'],
                            relief='flat',
                            command=self.clear_password)
        clear_btn.pack(side='left', padx=10)
        
        # Change Password button
        change_pwd_btn = tk.Button(button_container,
                                 text="🔒 Change Password",
                                 width=18,
                                 height=2,
                                 font=('Arial', 12, 'bold'),
                                 bg=self.colors['warning'],
                                 fg=self.colors['white'],
                                 activebackground='#d97706',
                                 activeforeground=self.colors['white'],
                                 relief='flat',
                                 command=self.change_password)
        change_pwd_btn.pack(side='left', padx=10)
        
        # Cancel button with enhanced styling
        cancel_btn = tk.Button(button_container,
                             text="❌ Cancel (ESC)",
                             width=18,
                             height=2,
                             font=('Arial', 12, 'bold'),
                             bg=self.colors['error'],
                             fg=self.colors['white'],
                             activebackground='#dc2626',
                             activeforeground=self.colors['white'],
                             relief='flat',
                             command=self.go_back)
        cancel_btn.pack(side='left', padx=10)

    def handle_key_input(self, key):
        """Handle keyboard input"""
        current = self.password_var.get()
        self.password_var.set(current + key)
        # Clear any previous error
        self.error_label.config(text="")

    def handle_backspace(self):
        """Handle backspace key"""
        current = self.password_var.get()
        if current:
            self.password_var.set(current[:-1])
        # Clear any previous error
        self.error_label.config(text="")

    def clear_password(self):
        """Clear password field and errors"""
        self.password_var.set('')
        self.error_label.config(text="")
        self.password_entry.focus_set()

    def change_password(self):
        """Open password change dialog"""
        try:
            # Show the password change dialog
            result = show_password_change_dialog(self.main_window.root, self.main_window.app_controller, self.colors)
            
            if result:
                self.error_label.config(text="Password changed successfully! Please login with new password.", fg=self.colors['success'])
                self.password_var.set('')
                self.password_entry.focus_set()
            else:
                # Password change was cancelled, just clear any error
                self.error_label.config(text="")
                
        except Exception as e:
            print(f"Error opening password change dialog: {e}")
            self.error_label.config(text=f"Error: {str(e)}", fg=self.colors['error'])

    def verify_password(self):
        """Verify entered password against stored hash"""
        entered_password = self.password_var.get().strip()
        
        print(f"Password verification attempt for {self.target_page}")
        print(f"Entered: '{entered_password}' (length: {len(entered_password)})")
        
        # Get stored password hash from app controller
        stored_hash = self.main_window.app_controller.settings.get("password_hash", "")
        
        # If no password is set, use default "Admin123"
        if not stored_hash:
            default_password = "Admin123"
            stored_hash = hashlib.sha256(default_password.encode()).hexdigest()
            # Save the default password hash
            self.main_window.app_controller.settings["password_hash"] = stored_hash
            self.main_window.app_controller.save_settings()
        
        # Hash the entered password
        entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()
        
        if entered_hash == stored_hash:
            print("Password verified successfully")
            self.success_login()
        else:
            print("Password verification failed")
            
            # Provide helpful feedback
            if len(entered_password) == 0:
                error_msg = "Please enter a password"
            else:
                error_msg = "Incorrect password. Please try again."
            
            self.show_error(error_msg)
            self.password_var.set('')
            self.password_entry.focus_set()

    def show_error(self, message):
        """Show error message with visual feedback"""
        self.error_label.config(text=message, fg=self.colors['error'])
        
        # Add visual feedback - briefly change entry border color
        original_bg = self.password_entry.cget('bg')
        self.password_entry.config(highlightbackground=self.colors['error'])
        
        # Reset after 2 seconds
        self.main_window.root.after(2000, lambda: self.password_entry.config(
            highlightbackground=self.colors['primary']
        ))

    def success_login(self):
        """Handle successful login"""
        try:
            # Clear the login interface
            self.login_frame.destroy()
            
            # Restore main window key bindings
            self.main_window.root.unbind('<Escape>')
            self.main_window.setup_global_bindings()
            
            # Show the target page
            self.callback(self.target_page)
            
            print(f"Successfully logged in and navigated to {self.target_page}")
            
        except Exception as e:
            print(f"Error during successful login: {e}")
            self.go_back()

    def go_back(self):
        """Return to previous view - Fixed to properly restore state"""
        try:
            # Clear the login interface
            if hasattr(self, 'login_frame') and self.login_frame.winfo_exists():
                self.login_frame.destroy()
            
            # Restore main window key bindings
            self.main_window.root.unbind('<Escape>')
            self.main_window.setup_global_bindings()
            
            # Return to the previous view (usually Main)
            if self.previous_view == "Main":
                self.main_window.show_main_view()
            elif self.previous_view == "Reference":
                self.main_window.show_reference_view()
            else:
                # Default to main view
                self.main_window.show_main_view()
            
            print(f"Returned to {self.previous_view} view from login")
            
        except Exception as e:
            print(f"Error returning from login: {e}")
            # Emergency fallback - force main view
            try:
                self.main_window.show_main_view()
            except:
                pass

    def __del__(self):
        """Cleanup when interface is destroyed"""
        try:
            if hasattr(self, 'login_frame') and self.login_frame.winfo_exists():
                self.login_frame.destroy()
        except:
            pass

    def update_char_count(self, *args):
        """Update character count display"""
        count = len(self.password_var.get())
        
        if count == 0:
            text = "Enter password"
            color = self.colors['text_secondary']
        else:
            text = f"{count} characters"
            color = self.colors['text_secondary']
        
        if hasattr(self, 'char_count_label'):
            self.char_count_label.config(text=text, fg=color)