"""
Complete Fixed Reference Dialog - Resolves all PyRight errors
Non-blocking validation and save operations to prevent UI freezing
"""

import tkinter as tk
# import tkinter.messagebox as messagebox  # Removed messagebox import
import re
import time
import threading
from typing import Optional, Callable, Dict, Any
from ..components.keyboard import VirtualKeyboard
from utils.validation import ValidationUtils


class NonBlockingReferenceDialog:
    """Enhanced dialog with non-blocking operations to prevent UI freezing"""
    
    def __init__(self, app_controller, colors, existing_ref=None, callback=None):
        self.app_controller = app_controller
        self.colors = colors
        self.existing_ref = existing_ref
        self.callback = callback
        
        # Dialog state
        self.dialog: Optional[tk.Toplevel] = None
        self.root: Optional[tk.Toplevel] = None
        self.is_editing = bool(existing_ref)
        self.validation_enabled = True
        self._save_in_progress = False
        
        # Variables for entry fields
        self.ref_id_var = tk.StringVar()
        self.position_var = tk.StringVar()
        self.pressure_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.description_var = tk.StringVar()
        
        # UI components
        self.active_entry: Optional[tk.Entry] = None
        self.entry_widgets: Dict[str, tk.Entry] = {}
        self.validation_labels: Dict[str, tk.Label] = {}
        self.keyboard: Optional[VirtualKeyboard] = None
        self.save_btn: Optional[tk.Button] = None
        self.progress_frame: Optional[tk.Frame] = None
        self.progress_label: Optional[tk.Label] = None
        self.progress_dots: Optional[tk.Label] = None
        self.status_label: Optional[tk.Label] = None
        self.main_container: Optional[tk.Frame] = None
        self.container: Optional[tk.Frame] = None
        
        # Validation state - start with True for editing mode
        self.field_valid: Dict[str, bool] = {
            'ref_id': self.is_editing,  # True if editing, False if new
            'position': False,
            'pressure': False,
            'time': False
        }
        
        # Async validation
        self._validation_queue: list[str] = []
        self._validation_thread: Optional[threading.Thread] = None
        self._validation_lock = threading.Lock()
        
        # Create dialog
        self.create_dialog()
        
        # Start validation thread
        self._start_validation_thread()
        
        # Pre-fill if editing existing reference
        if existing_ref:
            self.prefill_form()
        else:
            # Set focus to first field and enable validation
            if self.root:
                self.root.after(100, lambda: self.set_active_entry(self.entry_widgets['ref_id']))

    def create_dialog(self):
        """Create the enhanced dialog window"""
        self.dialog = tk.Toplevel()
        self.dialog.title("Edit Reference" if self.is_editing else "Add Reference")
        
        # Configure dialog window
        self.dialog.attributes('-topmost', True)
        self.dialog.overrideredirect(True)
        self.dialog.configure(bg=self.colors['white'])
        
        # Make it fullscreen
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        self.dialog.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Store reference to root for later use
        self.root = self.dialog
        
        # Bind keys
        self.dialog.bind('<Escape>', self.handle_escape)
        self.dialog.bind('<Return>', lambda e: self.try_save_reference())
        self.dialog.focus_set()
        
        # Create main container
        self.main_container = tk.Frame(self.dialog, bg=self.colors['background'])
        self.main_container.pack(fill='both', expand=True)
        
        # Create centered content container
        self.container = tk.Frame(
            self.main_container, 
            bg=self.colors['white'],
            highlightbackground=self.colors['border'],
            highlightthickness=2,
            relief='raised'
        )
        self.container.place(relx=0.5, rely=0.5, anchor='center', width=1000, height=950)
        
        # Create UI elements
        self.create_header()
        self.create_form()
        self.create_keyboard()
        self.create_footer()

    def create_header(self):
        """Create dialog header with progress indicator"""
        if not self.container:
            return
            
        header_frame = tk.Frame(self.container, bg=self.colors['primary'], height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Title
        title_text = "Edit Reference" if self.is_editing else "Add New Reference"
        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=('Arial', 18, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        title_label.pack(side='left', padx=20, pady=15)
        
        # Progress indicator (initially hidden)
        self.progress_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        self.progress_frame.pack(side='left', padx=20, pady=15)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Saving...",
            font=('Arial', 12),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        
        # Simple progress indicator using labels
        self.progress_dots = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 12),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        
        # Initially hide progress
        self.hide_progress()
        
        # Close button
        close_btn = tk.Button(
            header_frame,
            text="X",
            font=('Arial', 16, 'bold'),
            bg=self.colors['error'],
            fg=self.colors['white'],
            relief='flat',
            width=3,
            command=self.close_dialog
        )
        close_btn.pack(side='right', padx=20, pady=15)

    def create_form(self):
        """Create the input form with async validation"""
        if not self.container:
            return
            
        form_frame = tk.Frame(self.container, bg=self.colors['white'])
        form_frame.pack(fill='x', pady=15, padx=40)
        
        # Create entry rows
        self.create_entry_row(
            form_frame, 
            "Reference ID:", 
            self.ref_id_var,
            'ref_id',
            disabled=self.is_editing,
            help_text="Unique identifier (letters, numbers, underscore only)"
        )
        
        self.create_entry_row(
            form_frame, 
            "Position (mm):", 
            self.position_var,
            'position',
            help_text="Test position (65-200 mm)"
        )
        
        self.create_entry_row(
            form_frame, 
            "Pressure (bar):", 
            self.pressure_var,
            'pressure',
            help_text="Target pressure (0-4.5 bar)"
        )
        
        self.create_entry_row(
            form_frame, 
            "Time (min):", 
            self.time_var,
            'time',
            help_text="Inspection duration (0-120 minutes)"
        )
        
        self.create_entry_row(
            form_frame, 
            "Description:", 
            self.description_var,
            'description',
            help_text="Optional description"
        )

    def create_entry_row(self, parent: tk.Widget, label_text: str, variable: tk.StringVar, 
                        field_name: str, disabled: bool = False, help_text: str = ""):
        """Create an entry row with async validation"""
        row_frame = tk.Frame(parent, bg=self.colors['white'])
        row_frame.pack(fill='x', pady=8)

        # Label
        label = tk.Label(
            row_frame,
            text=label_text,
            font=('Arial', 12, 'bold'),
            width=18,
            anchor='e',
            bg=self.colors['white'],
            fg=self.colors['text_primary']
        )
        label.pack(side='left', padx=10)

        # Entry container
        entry_container = tk.Frame(row_frame, bg=self.colors['white'])
        entry_container.pack(side='left', fill='x', expand=True, padx=10)

        # Entry widget
        entry = tk.Entry(
            entry_container,
            textvariable=variable,
            font=('Arial', 12),
            width=25,
            state='disabled' if disabled else 'normal',
            bg='#f0f0f0' if disabled else 'white',
            relief='solid',
            bd=1
        )
        entry.pack(fill='x', pady=1)
        
        # Bind events for async validation
        if not disabled:
            entry.bind('<Button-1>', lambda e, entry=entry, field=field_name: self.set_active_entry(entry))
            entry.bind('<KeyRelease>', lambda e, field=field_name: self.queue_validation(field))
            entry.bind('<FocusOut>', lambda e, field=field_name: self.queue_validation(field))
            
            # Also bind to variable changes
            variable.trace_add('write', lambda *args, field=field_name: self.queue_validation(field))

        # Validation label with status indicator
        validation_frame = tk.Frame(entry_container, bg=self.colors['white'])
        validation_frame.pack(fill='x')
        
        validation_label = tk.Label(
            validation_frame,
            text="",
            font=('Arial', 9),
            bg=self.colors['white'],
            fg=self.colors['error'],
            anchor='w'
        )
        validation_label.pack(side='left', fill='x', expand=True)
        
        # Help text
        if help_text:
            help_label = tk.Label(
                entry_container,
                text=help_text,
                font=('Arial', 8),
                bg=self.colors['white'],
                fg=self.colors['text_secondary'],
                anchor='w'
            )
            help_label.pack(fill='x')

        # Store references
        self.entry_widgets[field_name] = entry
        self.validation_labels[field_name] = validation_label

    def create_keyboard(self):
        """Create the virtual keyboard"""
        if not self.container:
            return
            
        keyboard_container = tk.Frame(self.container, bg=self.colors['white'])
        keyboard_container.pack(fill='x', pady=10, padx=20)
        
        # Keyboard label
        keyboard_label = tk.Label(
            keyboard_container,
            text="Virtual Keyboard - Click on a field above to type",
            font=('Arial', 12, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        keyboard_label.pack(pady=(0, 10))
        
        # Keyboard frame
        keyboard_frame = tk.Frame(keyboard_container, bg=self.colors['white'])
        keyboard_frame.pack(fill='x')
        
        # Create virtual keyboard
        self.keyboard = VirtualKeyboard(keyboard_frame, self.colors, callback=self.try_save_reference)
        self.keyboard.set_key_handler(self.handle_key_input)
        self.keyboard.set_backspace_handler(self.handle_backspace)
        keyboard_widget = self.keyboard.create()

    def create_footer(self):
        """Create footer with buttons and status"""
        if not self.container:
            return
            
        footer_frame = tk.Frame(self.container, bg=self.colors['background'], height=80)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        # Button container
        button_container = tk.Frame(footer_frame, bg=self.colors['background'])
        button_container.pack(expand=True, fill='both')
        
        # Save button
        self.save_btn = tk.Button(
            button_container,
            text="Save Reference" if not self.is_editing else "Update Reference",
            width=18,
            height=2,
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white'],
            activebackground=self.colors['button_hover'],
            relief='flat',
            command=self.save_reference_async,
            state='normal'
        )
        self.save_btn.pack(side='left', padx=20, pady=20)
        
        # Validate button
        validate_btn = tk.Button(
            button_container,
            text="Check Fields",
            width=12,
            height=2,
            font=('Arial', 12),
            bg=self.colors['background'],
            fg=self.colors['primary'],
            activebackground=self.colors['primary'],
            activeforeground=self.colors['white'],
            relief='flat',
            command=self.validate_all_fields_async
        )
        validate_btn.pack(side='left', padx=10, pady=20)
        
        # Clear button
        clear_btn = tk.Button(
            button_container,
            text="Clear All",
            width=12,
            height=2,
            font=('Arial', 12),
            bg=self.colors.get('warning', '#f59e0b'),
            fg=self.colors['white'],
            relief='flat',
            command=self.clear_all_fields
        )
        clear_btn.pack(side='left', padx=10, pady=20)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            width=12,
            height=2,
            font=('Arial', 12),
            bg=self.colors['error'],
            fg=self.colors['white'],
            relief='flat',
            command=self.close_dialog
        )
        cancel_btn.pack(side='right', padx=20, pady=20)
        
        # Status label
        self.status_label = tk.Label(
            button_container,
            text="Ready - Fill in the required fields",
            font=('Arial', 10),
            bg=self.colors['background'],
            fg=self.colors['text_primary']
        )
        self.status_label.pack(side='bottom', pady=10)

    def _start_validation_thread(self):
        """Start background validation thread"""
        self._validation_thread = threading.Thread(
            target=self._validation_worker,
            daemon=True,
            name="ValidationWorker"
        )
        self._validation_thread.start()

    def _validation_worker(self):
        """Background worker for validation operations"""
        while True:
            try:
                # Check if we have validation requests
                with self._validation_lock:
                    if not self._validation_queue:
                        time.sleep(0.1)  # Wait for requests
                        continue
                    
                    # Get unique field names (avoid duplicate validation)
                    fields_to_validate = list(set(self._validation_queue))
                    self._validation_queue.clear()
                
                # Process validations
                for field_name in fields_to_validate:
                    if self.dialog and self.dialog.winfo_exists():
                        # Schedule UI update on main thread
                        if self.root:
                            self.root.after_idle(self._validate_field_sync, field_name)
                    
                time.sleep(0.05)  # Small delay to batch requests
                
            except Exception as e:
                print(f"Error in validation worker: {e}")
                time.sleep(1)

    def queue_validation(self, field_name: str):
        """Queue field for async validation"""
        with self._validation_lock:
            if field_name not in self._validation_queue:
                self._validation_queue.append(field_name)

    def _validate_field_sync(self, field_name: str):
        """Validate field synchronously (called from main thread)"""
        try:
            if field_name not in self.validation_labels:
                return
                
            validation_label = self.validation_labels[field_name]
            
            if field_name == 'ref_id':
                value = self.ref_id_var.get().strip()
                if not value:
                    self.field_valid[field_name] = False
                    validation_label.config(text="Required", fg=self.colors['error'])
                elif not re.match(r'^[a-zA-Z0-9_]+$', value):
                    self.field_valid[field_name] = False
                    validation_label.config(text="Only letters, numbers, underscore", fg=self.colors['error'])
                elif not self.is_editing and value in self.app_controller.settings.get('references', {}):
                    self.field_valid[field_name] = False
                    validation_label.config(text="ID already exists", fg=self.colors['error'])
                else:
                    self.field_valid[field_name] = True
                    validation_label.config(text="✓", fg=self.colors.get('success', '#10b981'))
            
            elif field_name == 'position':
                value = self.position_var.get().strip()
                if not value:
                    self.field_valid[field_name] = False
                    validation_label.config(text="Required", fg=self.colors['error'])
                else:
                    try:
                        num_val = float(value)
                        if 65 <= num_val <= 200:
                            self.field_valid[field_name] = True
                            validation_label.config(text="✓", fg=self.colors.get('success', '#10b981'))
                        else:
                            self.field_valid[field_name] = False
                            validation_label.config(text="Must be 65-200 mm", fg=self.colors['error'])
                    except ValueError:
                        self.field_valid[field_name] = False
                        validation_label.config(text="Must be a number", fg=self.colors['error'])
            
            elif field_name == 'pressure':
                value = self.pressure_var.get().strip()
                if not value:
                    self.field_valid[field_name] = False
                    validation_label.config(text="Required", fg=self.colors['error'])
                else:
                    try:
                        num_val = float(value)
                        if 0 <= num_val <= 4.5:
                            self.field_valid[field_name] = True
                            validation_label.config(text="✓", fg=self.colors.get('success', '#10b981'))
                        else:
                            self.field_valid[field_name] = False
                            validation_label.config(text="Must be 0-4.5 bar", fg=self.colors['error'])
                    except ValueError:
                        self.field_valid[field_name] = False
                        validation_label.config(text="Must be a number", fg=self.colors['error'])
            
            elif field_name == 'time':
                value = self.time_var.get().strip()
                if not value:
                    self.field_valid[field_name] = False
                    validation_label.config(text="Required", fg=self.colors['error'])
                else:
                    try:
                        num_val = float(value)
                        if 0 < num_val <= 120:
                            self.field_valid[field_name] = True
                            validation_label.config(text="✓", fg=self.colors.get('success', '#10b981'))
                        else:
                            self.field_valid[field_name] = False
                            validation_label.config(text="Must be 0-120 min", fg=self.colors['error'])
                    except ValueError:
                        self.field_valid[field_name] = False
                        validation_label.config(text="Must be a number", fg=self.colors['error'])
            
            # Update button state after validation
            self.update_save_button_state()
            
        except Exception as e:
            print(f"Error validating field {field_name}: {e}")

    def validate_all_fields_async(self):
        """Validate all fields asynchronously"""
        required_fields = ['ref_id', 'position', 'pressure', 'time']
        
        for field in required_fields:
            self.queue_validation(field)
        
        # Update status
        if self.status_label:
            self.status_label.config(
                text="Validating fields...",
                fg=self.colors['text_secondary']
            )
        
        # Check results after short delay
        if self.root:
            self.root.after(200, self._check_validation_results)

    def _check_validation_results(self):
        """Check validation results and update UI"""
        required_fields = ['ref_id', 'position', 'pressure', 'time']
        all_valid = all(self.field_valid.get(field, False) for field in required_fields)
        
        if self.status_label:
            if all_valid:
                self.status_label.config(
                    text="All fields are valid - Ready to save!",
                    fg=self.colors.get('success', '#10b981')
                )
            else:
                invalid_fields = [field for field in required_fields if not self.field_valid.get(field, False)]
                self.status_label.config(
                    text=f"Please fix: {', '.join(invalid_fields)}",
                    fg=self.colors['error']
                )

    def update_save_button_state(self):
        """Update save button state"""
        if not self.save_btn or self._save_in_progress:
            return
            
        required_fields = ['ref_id', 'position', 'pressure', 'time']
        all_valid = all(self.field_valid.get(field, False) for field in required_fields)
        
        if all_valid:
            self.save_btn.config(
                state='normal', 
                bg=self.colors['primary'],
                text="Save Reference" if not self.is_editing else "Update Reference"
            )
        else:
            self.save_btn.config(state='normal')  # Keep enabled but show status

    def show_progress(self):
        """Show progress indicator"""
        if self.progress_label and self.progress_dots:
            self.progress_label.pack(side='left')
            self.progress_dots.pack(side='left', padx=5)
            self._animate_progress()

    def hide_progress(self):
        """Hide progress indicator"""
        if self.progress_label and self.progress_dots:
            self.progress_label.pack_forget()
            self.progress_dots.pack_forget()

    def _animate_progress(self):
        """Animate progress dots"""
        if self._save_in_progress and self.progress_dots and self.progress_dots.winfo_exists():
            current_text = self.progress_dots.cget('text')
            if len(current_text) >= 3:
                new_text = ""
            else:
                new_text = current_text + "."
            
            self.progress_dots.config(text=new_text)
            if self.root:
                self.root.after(500, self._animate_progress)

    def save_reference_async(self):
        """Save reference asynchronously to prevent UI freezing"""
        if self._save_in_progress:
            return
        
        print("Starting async save operation")
        
        # Show progress
        self._save_in_progress = True
        if self.save_btn:
            self.save_btn.config(state='disabled', text="Saving...")
        self.show_progress()
        
        def _save_worker():
            """Background worker for save operation"""
            try:
                # Validate all fields first
                required_fields = ['ref_id', 'position', 'pressure', 'time']
                
                # Force validation of all fields
                for field in required_fields:
                    if self.root:
                        self.root.after_idle(self.queue_validation, field)
                
                # Wait a moment for validation to complete
                time.sleep(0.2)
                
                # Check if all required fields are valid
                all_valid = all(self.field_valid.get(field, False) for field in required_fields)
                
                if not all_valid:
                    invalid_fields = [field for field in required_fields if not self.field_valid.get(field, False)]
                    error_msg = f"Please fix the following fields: {', '.join(invalid_fields)}"
                    if self.root:
                        self.root.after_idle(self._save_error, error_msg)
                    return
                
                # Get values
                ref_id = self.ref_id_var.get().strip()
                position = float(self.position_var.get().strip())
                pressure = float(self.pressure_var.get().strip())
                time_val = float(self.time_var.get().strip())
                description = self.description_var.get().strip()
                
                # Create reference data
                ref_data = {
                    "name": ref_id,
                    "description": description or f"Reference {ref_id}",
                    "parameters": {
                        "position": position,
                        "target_pressure": pressure,
                        "inspection_time": time_val
                    },
                    "created_at": self.app_controller.settings['references'].get(ref_id, {}).get('created_at', time.time()),
                    "updated_at": time.time()
                }
                
                # Use async settings manager if available
                if hasattr(self.app_controller, 'settings_manager') and hasattr(self.app_controller.settings_manager, 'add_reference_async'):
                    # Async save
                    operation_id = self.app_controller.settings_manager.add_reference_async(
                        ref_id, 
                        ref_data,
                        callback=self._save_callback
                    )
                else:
                    # Fallback to synchronous save
                    if 'references' not in self.app_controller.settings:
                        self.app_controller.settings['references'] = {}
                        
                    self.app_controller.settings['references'][ref_id] = ref_data
                    self.app_controller.settings['last_reference'] = ref_id
                    
                    # Update current reference
                    if hasattr(self.app_controller, 'current_reference'):
                        self.app_controller.current_reference = ref_id
                    
                    # Save settings
                    success = self.app_controller.save_settings()
                    
                    if success:
                        if self.root:
                            self.root.after_idle(self._save_success, ref_id)
                    else:
                        if self.root:
                            self.root.after_idle(self._save_error, "Failed to save settings to file")
                
            except ValueError as ve:
                error_msg = f"Invalid input values: {str(ve)}"
                if self.root:
                    self.root.after_idle(self._save_error, error_msg)
            except Exception as e:
                error_msg = f"Failed to save reference: {str(e)}"
                if self.root:
                    self.root.after_idle(self._save_error, error_msg)
        
        # Start save operation in background thread
        save_thread = threading.Thread(target=_save_worker, daemon=True, name="ReferenceSave")
        save_thread.start()

    def _save_callback(self, success: bool, message: str):
        """Callback for async save operation"""
        if success:
            ref_id = self.ref_id_var.get().strip()
            if self.root:
                self.root.after_idle(self._save_success, ref_id)
        else:
            if self.root:
                self.root.after_idle(self._save_error, message)

    def _save_success(self, ref_id: str):
        """Handle successful save (called on main thread)"""
        try:
            self._save_in_progress = False
            self.hide_progress()
            
            action = "updated" if self.is_editing else "created"
            # Remove messagebox - just log success
            print(f"Success: Reference '{ref_id}' has been {action} successfully!")
            
            # Close dialog
            self.close_dialog()
            
            # Call callback if provided
            if self.callback:
                self.callback()
                
        except Exception as e:
            print(f"Error in save success handler: {e}")

    def _save_error(self, error_message: str):
        """Handle save error (called on main thread)"""
        try:
            self._save_in_progress = False
            self.hide_progress()
            
            # Reset button
            if self.save_btn:
                self.save_btn.config(
                    state='normal',
                    text="Save Reference" if not self.is_editing else "Update Reference"
                )
            
            # Remove messagebox - just log error
            print(f"Save Error: {error_message}")
            
        except Exception as e:
            print(f"Error in save error handler: {e}")

    def prefill_form(self):
        """Pre-fill form with existing reference data"""
        try:
            if self.existing_ref and self.existing_ref in self.app_controller.settings['references']:
                ref_data = self.app_controller.settings['references'][self.existing_ref]
                params = ref_data.get('parameters', {})
                
                self.ref_id_var.set(self.existing_ref)
                self.position_var.set(str(params.get('position', '')))
                self.pressure_var.set(str(params.get('target_pressure', '')))
                self.time_var.set(str(params.get('inspection_time', '')))
                self.description_var.set(ref_data.get('description', ''))
                
                # Mark all fields as valid for editing
                for field in self.field_valid:
                    self.field_valid[field] = True
                
                # Update button state
                self.update_save_button_state()
                
                print(f"Pre-filled form for editing reference: {self.existing_ref}")
                
        except Exception as e:
            print(f"Error prefilling form: {e}")

    def set_active_entry(self, entry: tk.Entry):
        """Set the active entry field"""
        self.active_entry = entry
        
        # Reset all entries to normal
        for field_name, widget in self.entry_widgets.items():
            if widget['state'] != 'disabled':
                widget.config(bg='white', relief='solid', bd=1)
        
        # Highlight active entry
        entry.config(bg=self.colors['status_bg'], relief='solid', bd=2)
        entry.focus_set()

    def handle_key_input(self, key: str):
        """Handle virtual keyboard input"""
        if self.active_entry and self.active_entry['state'] != 'disabled':
            current = self.active_entry.get()
            self.active_entry.delete(0, tk.END)
            self.active_entry.insert(0, current + key)
            
            # Trigger async validation
            field_name = self.get_field_name_from_entry(self.active_entry)
            if field_name:
                self.queue_validation(field_name)

    def handle_backspace(self):
        """Handle backspace from virtual keyboard"""
        if self.active_entry and self.active_entry['state'] != 'disabled':
            current = self.active_entry.get()
            if current:
                self.active_entry.delete(0, tk.END)
                self.active_entry.insert(0, current[:-1])
                
                # Trigger async validation
                field_name = self.get_field_name_from_entry(self.active_entry)
                if field_name:
                    self.queue_validation(field_name)

    def get_field_name_from_entry(self, entry: tk.Entry) -> Optional[str]:
        """Get field name from entry widget"""
        for field_name, widget in self.entry_widgets.items():
            if widget == entry:
                return field_name
        return None

    def try_save_reference(self):
        """Try to save reference (bound to Enter key)"""
        if not self._save_in_progress:
            self.save_reference_async()

    def clear_all_fields(self):
        """Clear all form fields"""
        # Remove confirmation dialog - just clear directly
        self.ref_id_var.set('')
        self.position_var.set('')
        self.pressure_var.set('')
        self.time_var.set('')
        self.description_var.set('')
        
        # Reset validation
        for field_name in self.field_valid:
            self.field_valid[field_name] = False
            if field_name in self.validation_labels:
                self.validation_labels[field_name].config(text="")
        
        self.update_save_button_state()
        print("All fields cleared")

    def handle_escape(self, event):
        """Handle escape key"""
        if not self._save_in_progress:
            self.close_dialog()

    def close_dialog(self):
        """Close the dialog with cleanup"""
        try:
            if self._save_in_progress:
                # Remove confirmation dialog - just cancel save and close
                print("Save operation cancelled by user")
                self._save_in_progress = False
            
            if self.dialog:
                self.dialog.destroy()
                print("Dialog closed")
                
        except Exception as e:
            print(f"Error closing dialog: {e}")


# Backward compatibility wrapper
class ReferenceDialog(NonBlockingReferenceDialog):
    """Backward compatible reference dialog"""
    pass