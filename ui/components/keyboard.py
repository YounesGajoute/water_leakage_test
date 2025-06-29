"""
Virtual Keyboard Component - Enhanced version with better layout and visibility
"""

import tkinter as tk


class VirtualKeyboard:
    """Virtual keyboard component for touch screen interfaces"""
    
    def __init__(self, parent, colors, callback=None):
        self.parent = parent
        self.colors = colors
        self.callback = callback
        self.is_uppercase = False
        self.keyboard_buttons = []
        
        # Define keyboard layouts
        self.lowercase_layout = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'DEL']
        ]
        
        self.uppercase_layout = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'DEL']
        ]

    def create(self):
        """Create the virtual keyboard with improved layout"""
        # Main keyboard container
        keyboard_frame = tk.Frame(self.parent, bg=self.colors['white'])
        keyboard_frame.pack(fill='x', pady=10)
        
        # Create instruction label
        instruction_label = tk.Label(
            keyboard_frame,
            text="Click on an input field above, then use the keyboard below to type",
            font=('Arial', 10),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        instruction_label.pack(pady=(0, 10))
        
        # Create keyboard buttons container
        keyboard_container = tk.Frame(keyboard_frame, bg=self.colors['white'])
        keyboard_container.pack()
        
        # Create keyboard buttons
        self.create_keyboard_buttons(keyboard_container)
        
        # Create bottom row with spacebar and special keys
        self.create_bottom_row(keyboard_container)
        
        print("Virtual keyboard created and ready")
        return keyboard_frame

    def create_keyboard_buttons(self, parent):
        """Create the main keyboard button grid with improved sizing"""
        self.keyboard_buttons = []
        layout = self.uppercase_layout if self.is_uppercase else self.lowercase_layout
        
        for row_index, row in enumerate(layout):
            button_row = []
            row_frame = tk.Frame(parent, bg=self.colors['white'])
            row_frame.pack(pady=3)  # Increased spacing between rows
            
            for key in row:
                # Determine button width based on key type
                if key in ['SHIFT', 'shift']:
                    btn_width = 8
                    btn_color = self.colors.get('warning', '#f59e0b')
                    text_color = self.colors['white']
                elif key == 'DEL':
                    btn_width = 8
                    btn_color = self.colors['error']
                    text_color = self.colors['white']
                else:
                    btn_width = 5  # Increased from 4 to 5 for better visibility
                    btn_color = self.colors['background']
                    text_color = self.colors['text_primary']
                
                btn = tk.Button(
                    row_frame,
                    text=key,
                    width=btn_width,
                    height=2,
                    font=('Arial', 11, 'bold'),  # Slightly larger font
                    bg=btn_color,
                    fg=text_color,
                    activebackground=self.colors['primary'],
                    activeforeground=self.colors['white'],
                    relief='raised',
                    bd=2,
                    command=lambda k=key: self.handle_key_press(k)
                )
                btn.pack(side='left', padx=2)
                button_row.append(btn)
                
                # Enhanced hover effects
                btn.bind('<Enter>', lambda e, b=btn: self.on_button_hover(b))
                btn.bind('<Leave>', lambda e, b=btn, original_bg=btn_color, original_fg=text_color: 
                        self.on_button_leave(b, original_bg, original_fg))
            
            self.keyboard_buttons.append(button_row)

    def create_bottom_row(self, parent):
        """Create the bottom row with spacebar and special keys"""
        bottom_frame = tk.Frame(parent, bg=self.colors['white'])
        bottom_frame.pack(pady=5)
        
        # Spacebar - much larger
        spacebar = tk.Button(
            bottom_frame,
            text="SPACE",
            width=25,  # Increased width
            height=2,
            font=('Arial', 12, 'bold'),
            bg=self.colors['background'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['primary'],
            activeforeground=self.colors['white'],
            relief='raised',
            bd=2,
            command=lambda: self.handle_key_press(' ')
        )
        spacebar.pack(side='left', padx=2)
        
        # Enter key (if callback is provided)
        if self.callback:
            enter_btn = tk.Button(
                bottom_frame,
                text="ENTER",
                width=10,
                height=2,
                font=('Arial', 12, 'bold'),
                bg=self.colors['primary'],
                fg=self.colors['white'],
                activebackground=self.colors['button_hover'],
                activeforeground=self.colors['white'],
                relief='raised',
                bd=2,
                command=self.callback
            )
            enter_btn.pack(side='left', padx=5)
            
            # Add enter button to hover effects
            enter_btn.bind('<Enter>', lambda e: enter_btn.config(bg=self.colors['button_hover']))
            enter_btn.bind('<Leave>', lambda e: enter_btn.config(bg=self.colors['primary']))
        
        # Clear key for convenience
        clear_btn = tk.Button(
            bottom_frame,
            text="CLEAR",
            width=8,
            height=2,
            font=('Arial', 11, 'bold'),
            bg=self.colors.get('warning', '#f59e0b'),
            fg=self.colors['white'],
            activebackground=self.colors.get('warning', '#f59e0b'),
            activeforeground=self.colors['white'],
            relief='raised',
            bd=2,
            command=self.clear_current_field
        )
        clear_btn.pack(side='left', padx=5)
        
        # Add hover effects for bottom row buttons
        for btn in [spacebar, clear_btn]:
            btn.bind('<Enter>', lambda e, b=btn: self.on_button_hover(b))
            btn.bind('<Leave>', lambda e, b=btn: self.on_button_leave_special(b))

    def handle_key_press(self, key):
        """Handle key press events with enhanced feedback"""
        print(f"Virtual keyboard: Key '{key}' pressed")
        
        if key in ['DEL', 'del']:
            # Backspace functionality
            self.on_backspace()
        elif key in ['SHIFT', 'shift']:
            # Toggle case and update keyboard
            self.is_uppercase = not self.is_uppercase
            self.update_keyboard_case()
            print(f"Keyboard case toggled to: {'UPPER' if self.is_uppercase else 'LOWER'}")
        else:
            # Add character with proper case
            if len(key) == 1:  # Only process single characters
                if self.is_uppercase:
                    key = key.upper()
                else:
                    key = key.lower()
                self.on_key_input(key)

    def update_keyboard_case(self):
        """Update keyboard case (uppercase/lowercase) with visual feedback"""
        layout = self.uppercase_layout if self.is_uppercase else self.lowercase_layout
        for row_index, row in enumerate(layout):
            for col_index, key in enumerate(row):
                if row_index < len(self.keyboard_buttons) and col_index < len(self.keyboard_buttons[row_index]):
                    button = self.keyboard_buttons[row_index][col_index]
                    button.configure(text=key)
                    
                    # Update SHIFT button appearance to show state
                    if key in ['SHIFT', 'shift']:
                        if self.is_uppercase:
                            button.configure(bg=self.colors['primary'], fg=self.colors['white'])
                        else:
                            button.configure(bg=self.colors.get('warning', '#f59e0b'), fg=self.colors['white'])

    def on_button_hover(self, button):
        """Handle button hover effect"""
        button.config(bg=self.colors['primary'], fg=self.colors['white'])

    def on_button_leave(self, button, original_bg, original_fg):
        """Handle button leave effect"""
        button.config(bg=original_bg, fg=original_fg)

    def on_button_leave_special(self, button):
        """Handle button leave effect for special buttons"""
        # Get the original color based on button text
        text = button.cget('text')
        if text == "SPACE":
            button.config(bg=self.colors['background'], fg=self.colors['text_primary'])
        elif text == "CLEAR":
            button.config(bg=self.colors.get('warning', '#f59e0b'), fg=self.colors['white'])
        elif text == "ENTER":
            button.config(bg=self.colors['primary'], fg=self.colors['white'])

    def clear_current_field(self):
        """Clear the current input field"""
        print("Clear button pressed")
        # This will be overridden by the parent dialog
        pass

    def on_key_input(self, key):
        """Override this method to handle key input"""
        print(f"Key pressed: {key}")

    def on_backspace(self):
        """Override this method to handle backspace"""
        print("Backspace pressed")

    def set_key_handler(self, key_handler):
        """Set a custom key handler function"""
        self.on_key_input = key_handler

    def set_backspace_handler(self, backspace_handler):
        """Set a custom backspace handler function"""
        self.on_backspace = backspace_handler

    def set_clear_handler(self, clear_handler):
        """Set a custom clear handler function"""
        self.clear_current_field = clear_handler

    def get_keyboard_state(self):
        """Get current keyboard state"""
        return {
            'is_uppercase': self.is_uppercase,
            'layout': 'uppercase' if self.is_uppercase else 'lowercase'
        }

    def reset_keyboard(self):
        """Reset keyboard to default state"""
        self.is_uppercase = False
        self.update_keyboard_case()
        print("Keyboard reset to lowercase")