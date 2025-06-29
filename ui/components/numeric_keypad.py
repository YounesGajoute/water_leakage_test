"""
Numeric Keypad Component - For precise numeric input in calibration
"""

import tkinter as tk
import re


class NumericKeypad:
    """Numeric keypad component for precise numeric input"""
    
    def __init__(self, parent, colors, callback=None, allow_negative=True, decimal_places=3):
        self.parent = parent
        self.colors = colors
        self.callback = callback
        self.allow_negative = allow_negative
        self.decimal_places = decimal_places
        
        # Current input state
        self.current_value = ""
        self.target_entry = None
        self.keypad_buttons = []
        
        # Keypad layout
        self.keypad_layout = [
            ['7', '8', '9', 'DEL'],
            ['4', '5', '6', 'CLR'],
            ['1', '2', '3', 'ENT'],
            ['±', '0', '.', '←']
        ]

    def create(self):
        """Create the numeric keypad"""
        # Main keypad container
        keypad_frame = tk.Frame(self.parent, bg=self.colors['white'])
        keypad_frame.pack(padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            keypad_frame,
            text="Numeric Keypad",
            font=('Arial', 12, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 10))
        
        # Current value display
        self.value_display = tk.Label(
            keypad_frame,
            text="0.000",
            font=('Arial', 16, 'bold'),
            bg=self.colors['background'],
            fg=self.colors['text_primary'],
            relief='sunken',
            bd=2,
            width=12,
            anchor='e',
            padx=10,
            pady=5
        )
        self.value_display.pack(pady=(0, 10))
        
        # Create keypad buttons
        buttons_frame = tk.Frame(keypad_frame, bg=self.colors['white'])
        buttons_frame.pack()
        
        self.create_keypad_buttons(buttons_frame)
        
        # Instructions
        instruction_label = tk.Label(
            keypad_frame,
            text="Click input field, then use keypad",
            font=('Arial', 9),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        instruction_label.pack(pady=(10, 0))
        
        return keypad_frame

    def create_keypad_buttons(self, parent):
        """Create the keypad button grid"""
        self.keypad_buttons = []
        
        for row_index, row in enumerate(self.keypad_layout):
            button_row = []
            row_frame = tk.Frame(parent, bg=self.colors['white'])
            row_frame.pack(pady=2)
            
            for key in row:
                # Determine button properties
                if key.isdigit() or key == '.':
                    # Number and decimal buttons
                    btn_width = 4
                    btn_color = self.colors['background']
                    text_color = self.colors['text_primary']
                    font_weight = 'normal'
                elif key == 'ENT':
                    # Enter button
                    btn_width = 4
                    btn_color = self.colors['primary']
                    text_color = self.colors['white']
                    font_weight = 'bold'
                elif key in ['DEL', 'CLR']:
                    # Delete/Clear buttons
                    btn_width = 4
                    btn_color = self.colors['error']
                    text_color = self.colors['white']
                    font_weight = 'bold'
                elif key == '±':
                    # Plus/minus button
                    btn_width = 4
                    btn_color = self.colors.get('warning', '#f59e0b')
                    text_color = self.colors['white']
                    font_weight = 'bold'
                else:
                    # Other special buttons
                    btn_width = 4
                    btn_color = self.colors.get('warning', '#f59e0b')
                    text_color = self.colors['white']
                    font_weight = 'bold'
                
                btn = tk.Button(
                    row_frame,
                    text=key,
                    width=btn_width,
                    height=2,
                    font=('Arial', 12, font_weight),
                    bg=btn_color,
                    fg=text_color,
                    activebackground=self.colors['button_hover'],
                    activeforeground=self.colors['white'],
                    relief='raised',
                    bd=2,
                    command=lambda k=key: self.handle_key_press(k)
                )
                btn.pack(side='left', padx=1)
                button_row.append(btn)
                
                # Add hover effects
                btn.bind('<Enter>', lambda e, b=btn, orig_bg=btn_color: self.on_button_hover(b))
                btn.bind('<Leave>', lambda e, b=btn, orig_bg=btn_color, orig_fg=text_color: 
                        self.on_button_leave(b, orig_bg, orig_fg))
            
            self.keypad_buttons.append(button_row)

    def handle_key_press(self, key):
        """Handle keypad button press"""
        try:
            if key.isdigit():
                # Number input
                self.add_digit(key)
            elif key == '.':
                # Decimal point
                self.add_decimal()
            elif key == 'DEL':
                # Delete last character
                self.delete_last()
            elif key == 'CLR':
                # Clear all
                self.clear_all()
            elif key == '±':
                # Toggle sign
                self.toggle_sign()
            elif key == '←':
                # Backspace
                self.delete_last()
            elif key == 'ENT':
                # Enter/confirm
                self.confirm_value()
            
            # Update display
            self.update_display()
            
        except Exception as e:
            print(f"Error handling key press: {e}")

    def add_digit(self, digit):
        """Add a digit to current value"""
        # Limit total length
        if len(self.current_value.replace('-', '').replace('.', '')) >= 8:
            return
        
        if self.current_value == "0":
            self.current_value = digit
        else:
            self.current_value += digit

    def add_decimal(self):
        """Add decimal point"""
        # Only allow one decimal point
        if '.' not in self.current_value:
            if not self.current_value or self.current_value == '-':
                self.current_value += '0.'
            else:
                self.current_value += '.'

    def delete_last(self):
        """Delete last character"""
        if self.current_value:
            self.current_value = self.current_value[:-1]
            if not self.current_value or self.current_value == '-':
                self.current_value = "0"

    def clear_all(self):
        """Clear all input"""
        self.current_value = "0"

    def toggle_sign(self):
        """Toggle positive/negative sign"""
        if not self.allow_negative:
            return
        
        if self.current_value and self.current_value != "0":
            if self.current_value.startswith('-'):
                self.current_value = self.current_value[1:]
            else:
                self.current_value = '-' + self.current_value

    def confirm_value(self):
        """Confirm and apply the current value"""
        try:
            if self.target_entry and self.current_value:
                # Validate and format the value
                value = float(self.current_value) if self.current_value else 0.0
                formatted_value = f"{value:.{self.decimal_places}f}"
                
                # Set the value in target entry
                if hasattr(self.target_entry, 'delete') and hasattr(self.target_entry, 'insert'):
                    self.target_entry.delete(0, tk.END)
                    self.target_entry.insert(0, formatted_value)
                elif hasattr(self.target_entry, 'set'):
                    # For StringVar or DoubleVar
                    self.target_entry.set(value)
                
                # Trigger callback if provided
                if self.callback:
                    self.callback(value)
                
                # Visual feedback
                self.flash_display()
                
        except ValueError:
            # Invalid number, flash red
            self.flash_display(error=True)
        except Exception as e:
            print(f"Error confirming value: {e}")

    def update_display(self):
        """Update the value display"""
        display_text = self.current_value if self.current_value else "0"
        
        # Add decimal places for display
        try:
            if '.' in display_text:
                # Ensure proper decimal places
                num_value = float(display_text)
                display_text = f"{num_value:.{self.decimal_places}f}"
            else:
                # Add decimal if it's a whole number
                if display_text not in ['0', '-', '']:
                    num_value = float(display_text)
                    display_text = f"{num_value:.{self.decimal_places}f}"
        except ValueError:
            pass
        
        self.value_display.config(text=display_text)

    def flash_display(self, error=False):
        """Flash the display for feedback"""
        original_bg = self.value_display.cget('bg')
        original_fg = self.value_display.cget('fg')
        
        if error:
            flash_bg = self.colors['error']
            flash_fg = self.colors['white']
        else:
            flash_bg = self.colors['primary']
            flash_fg = self.colors['white']
        
        # Flash effect
        self.value_display.config(bg=flash_bg, fg=flash_fg)
        self.value_display.after(200, lambda: self.value_display.config(bg=original_bg, fg=original_fg))

    def set_target_entry(self, entry_widget):
        """Set the target entry widget to update"""
        self.target_entry = entry_widget
        
        # Load current value from entry if it exists
        try:
            if hasattr(entry_widget, 'get'):
                current = entry_widget.get()
                if current:
                    self.current_value = str(float(current))
                else:
                    self.current_value = "0"
            else:
                self.current_value = "0"
        except (ValueError, AttributeError):
            self.current_value = "0"
        
        self.update_display()

    def set_value(self, value):
        """Set a specific value in the keypad"""
        try:
            self.current_value = str(float(value))
            self.update_display()
        except (ValueError, TypeError):
            self.current_value = "0"
            self.update_display()

    def get_value(self):
        """Get current numeric value"""
        try:
            return float(self.current_value) if self.current_value else 0.0
        except ValueError:
            return 0.0

    def on_button_hover(self, button):
        """Handle button hover effect"""
        button.config(bg=self.colors['button_hover'], fg=self.colors['white'])

    def on_button_leave(self, button, original_bg, original_fg):
        """Handle button leave effect"""
        button.config(bg=original_bg, fg=original_fg)

    def reset(self):
        """Reset keypad to initial state"""
        self.current_value = "0"
        self.target_entry = None
        self.update_display()

    def set_decimal_places(self, places):
        """Set number of decimal places"""
        self.decimal_places = max(0, min(6, places))
        self.update_display()

    def set_allow_negative(self, allow):
        """Enable/disable negative numbers"""
        self.allow_negative = allow
        if not allow and self.current_value.startswith('-'):
            self.current_value = self.current_value[1:]
            self.update_display()


class NumericInputDialog:
    """Dialog for numeric input using the keypad"""
    
    def __init__(self, parent, colors, title="Enter Value", initial_value=0.0, 
                 min_value=None, max_value=None, decimal_places=3):
        self.parent = parent
        self.colors = colors
        self.title = title
        self.initial_value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self.decimal_places = decimal_places
        
        self.result = None
        self.dialog = None
        
        self.create_dialog()

    def create_dialog(self):
        """Create the numeric input dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("320x400")
        self.dialog.configure(bg=self.colors['white'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (320 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"320x400+{x}+{y}")
        
        # Title
        title_label = tk.Label(
            self.dialog,
            text=self.title,
            font=('Arial', 14, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=15)
        
        # Value range info
        if self.min_value is not None or self.max_value is not None:
            range_text = "Range: "
            if self.min_value is not None:
                range_text += f"{self.min_value:.{self.decimal_places}f}"
            else:
                range_text += "∞"
            range_text += " to "
            if self.max_value is not None:
                range_text += f"{self.max_value:.{self.decimal_places}f}"
            else:
                range_text += "∞"
            
            range_label = tk.Label(
                self.dialog,
                text=range_text,
                font=('Arial', 10),
                bg=self.colors['white'],
                fg=self.colors['text_secondary']
            )
            range_label.pack(pady=(0, 10))
        
        # Create keypad
        self.keypad = NumericKeypad(
            self.dialog, 
            self.colors, 
            decimal_places=self.decimal_places
        )
        keypad_widget = self.keypad.create()
        
        # Set initial value
        self.keypad.set_value(self.initial_value)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=self.colors['white'])
        button_frame.pack(pady=15)
        
        ok_btn = tk.Button(
            button_frame,
            text="OK",
            font=('Arial', 11, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white'],
            width=10,
            command=self.ok_clicked
        )
        ok_btn.pack(side='left', padx=10)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=('Arial', 11),
            bg=self.colors['background'],
            fg=self.colors['text_primary'],
            width=10,
            command=self.cancel_clicked
        )
        cancel_btn.pack(side='left', padx=10)
        
        # Bind keys
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())

    def ok_clicked(self):
        """Handle OK button"""
        try:
            value = self.keypad.get_value()
            
            # Validate range
            if self.min_value is not None and value < self.min_value:
                # Remove messagebox dependency - use print and visual feedback
                print(f"Value must be at least {self.min_value:.{self.decimal_places}f}")
                self.keypad.flash_display(error=True)
                return
            
            if self.max_value is not None and value > self.max_value:
                # Remove messagebox dependency - use print and visual feedback
                print(f"Value must be at most {self.max_value:.{self.decimal_places}f}")
                self.keypad.flash_display(error=True)
                return
            
            self.result = value
            if self.dialog is not None:
                self.dialog.destroy()
            
        except Exception as e:
            # Remove messagebox dependency - use print and visual feedback
            print(f"Invalid input: {str(e)}")
            self.keypad.flash_display(error=True)

    def cancel_clicked(self):
        """Handle Cancel button"""
        self.result = None
        if self.dialog is not None:
            self.dialog.destroy()


# Helper function for easy numeric input
def get_numeric_input(parent, colors, title="Enter Value", initial_value=0.0, 
                     min_value=None, max_value=None, decimal_places=3):
    """
    Helper function to get numeric input using keypad dialog
    
    Returns:
        float or None: The entered value, or None if cancelled
    """
    dialog = NumericInputDialog(
        parent, colors, title, initial_value, 
        min_value, max_value, decimal_places
    )
    parent.wait_window(dialog.dialog)
    return dialog.result 