"""
Navigation Component - Navigation bar for the application
"""

import tkinter as tk


class NavigationBar:
    """Navigation bar component"""
    
    def __init__(self, parent, colors, navigation_handler=None):
        self.parent = parent
        self.colors = colors
        self.navigation_handler = navigation_handler
        self.nav_buttons = {}

    def create(self, buttons_config):
        """
        Create navigation bar with specified buttons
        
        Args:
            buttons_config: List of button configurations
                           [{"text": "Main", "command": callback}, ...]
        """
        nav_container = tk.Frame(self.parent, bg=self.colors['background'])
        nav_container.pack(side='right', padx=20)
        
        for config in buttons_config:
            button = tk.Button(nav_container,
                              text=config['text'],
                              width=15,
                              height=3,
                              bg=self.colors['background'],
                              fg=self.colors['primary'],
                              activebackground=self.colors['primary'],
                              activeforeground=self.colors['white'],
                              relief='flat',
                              bd=0,
                              font=('Arial', 12, 'bold'),
                              command=config.get('command', lambda: None))
            button.pack(side='left', padx=5)
            
            # Store button reference
            self.nav_buttons[config['text']] = button
            
            # Hover effects
            button.bind('<Enter>', lambda e, b=button: self.on_button_hover(b))
            button.bind('<Leave>', lambda e, b=button: self.on_button_leave(b))
        
        return nav_container

    def create_default(self):
        """Create default navigation bar"""
        default_config = [
            {"text": "Main", "command": lambda: self.handle_navigation("Main")},
            {"text": "Settings", "command": lambda: self.handle_navigation("Settings")},
            {"text": "Calibration", "command": lambda: self.handle_navigation("Calibration")},
            {"text": "Reference", "command": lambda: self.handle_navigation("Reference")}
        ]
        return self.create(default_config)

    def handle_navigation(self, page_name):
        """Handle navigation button clicks"""
        if self.navigation_handler:
            self.navigation_handler(page_name)
        else:
            print(f"Navigation to {page_name}")

    def on_button_hover(self, button):
        """Button hover effect"""
        button.config(bg=self.colors['primary'], fg='white')

    def on_button_leave(self, button):
        """Button leave effect"""
        button.config(bg=self.colors['background'], fg=self.colors['primary'])

    def set_active_button(self, button_text):
        """Set a button as active (highlighted)"""
        for text, button in self.nav_buttons.items():
            if text == button_text:
                button.config(bg=self.colors['primary'], fg='white')
            else:
                button.config(bg=self.colors['background'], fg=self.colors['primary'])

    def enable_button(self, button_text, enabled=True):
        """Enable or disable a navigation button"""
        if button_text in self.nav_buttons:
            state = 'normal' if enabled else 'disabled'
            self.nav_buttons[button_text].config(state=state)

    def update_button_text(self, old_text, new_text):
        """Update button text"""
        if old_text in self.nav_buttons:
            button = self.nav_buttons[old_text]
            button.config(text=new_text)
            # Update dictionary key
            self.nav_buttons[new_text] = self.nav_buttons.pop(old_text)