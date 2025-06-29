"""
Complete Fixed Reference View - Resolves all PyRight errors
Implements chunked loading and async operations for large datasets
"""

import tkinter as tk
from tkinter import ttk
# from tkinter import ttk, messagebox  # Removed messagebox import
import threading
import time
from typing import Dict, List, Any, Optional

# Import the fixed reference dialog
try:
    from ..dialogs.reference_dialog import ReferenceDialog  # type: ignore
except ImportError:
    try:
        from ui.dialogs.reference_dialog import ReferenceDialog  # type: ignore
    except ImportError:
        # Fallback - create a dummy class
        class ReferenceDialog:
            def __init__(self, *args, **kwargs):
                print("ReferenceDialog not available - using fallback")


class OptimizedReferenceView:
    """Reference view with optimized tree population and async operations"""
    
    def __init__(self, parent, app_controller, colors):
        self.parent = parent
        self.app_controller = app_controller
        self.colors = colors
        
        # View state
        self.reference_frame: Optional[tk.Frame] = None
        self.references_tree: Optional[ttk.Treeview] = None
        self._loading = False
        self._load_cancelled = False
        
        # Async loading
        self._load_thread: Optional[threading.Thread] = None
        self._chunk_size = 50  # Load references in chunks
        self._load_delay = 0.01  # Small delay between chunks
        
        # Progress tracking
        self.progress_label: Optional[tk.Label] = None
        self.loading_indicator: Optional[tk.Label] = None
        self.loading_frame: Optional[tk.Frame] = None

    def show(self):
        """Display the reference management view"""
        try:
            # Create reference management frame
            self.reference_frame = tk.Frame(self.parent, bg=self.colors['white'])
            self.reference_frame.pack(fill='both', expand=True, pady=10)
            
            # Create header
            self.create_header()
            
            # Create button controls
            self.create_button_controls()
            
            # Create references table
            self.create_references_table()
            
            # Start async population
            self.populate_references_async()
            
        except Exception as e:
            print(f"Error in reference view show method: {e}")
            import traceback
            traceback.print_exc()

    def create_header(self):
        """Create the header section with loading indicator"""
        if not self.reference_frame:
            return
            
        header_frame = tk.Frame(self.reference_frame, bg=self.colors['white'])
        header_frame.pack(fill='x', padx=20, pady=10)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Reference Management", 
            font=('Arial', 18, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(side='left')
        
        # Loading indicator frame
        self.loading_frame = tk.Frame(header_frame, bg=self.colors['white'])
        self.loading_frame.pack(side='left', padx=20)
        
        # Loading label (initially hidden)
        self.loading_indicator = tk.Label(
            self.loading_frame,
            text="Loading references...",
            font=('Arial', 10),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        
        # Progress label (initially hidden)
        self.progress_label = tk.Label(
            self.loading_frame,
            text="",
            font=('Arial', 9),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        
        # Instructions
        instructions = tk.Label(
            header_frame,
            text="Manage test references - Double-click to load - Use keyboard shortcuts (Ctrl+R for quick add)",
            font=('Arial', 10),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        instructions.pack(side='right', padx=20)

    def create_button_controls(self):
        """Create the button control section"""
        if not self.reference_frame:
            return
            
        button_frame = tk.Frame(self.reference_frame, bg=self.colors['white'])
        button_frame.pack(fill='x', padx=20, pady=5)
        
        # Add Reference Button
        add_ref_btn = tk.Button(button_frame,
                                text="Add Reference (Ctrl+R)",
                                bg=self.colors['primary'],
                                fg=self.colors['white'],
                                activebackground=self.colors['button_hover'],
                                font=('Arial', 14, 'bold'),
                                width=18,
                                relief='flat',
                                command=self.open_add_reference_dialog)
        add_ref_btn.pack(side='left', padx=5)
        
        # Edit Reference Button
        edit_ref_btn = tk.Button(button_frame,
                                text="Edit Selected",
                                bg=self.colors.get('warning', '#f59e0b'),
                                fg=self.colors['white'],
                                activebackground=self.colors['button_hover'],
                                font=('Arial', 14, 'bold'),
                                width=15,
                                relief='flat',
                                command=self.open_edit_reference_dialog)
        edit_ref_btn.pack(side='left', padx=5)
        
        # Delete Reference Button
        delete_ref_btn = tk.Button(button_frame,
                                   text="Delete Selected",
                                   bg=self.colors['error'],
                                   fg=self.colors['white'],
                                   activebackground=self.colors['button_hover'],
                                   font=('Arial', 14, 'bold'),
                                   width=15,
                                   relief='flat',
                                   command=self.open_delete_reference_dialog)
        delete_ref_btn.pack(side='left', padx=5)
        
        # Load Reference Button
        load_ref_btn = tk.Button(button_frame,
                                text="Load Selected",
                                bg=self.colors.get('success', '#10b981'),
                                fg=self.colors['white'],
                                activebackground=self.colors['button_hover'],
                                font=('Arial', 14, 'bold'),
                                width=15,
                                relief='flat',
                                command=self.load_selected_reference_button)
        load_ref_btn.pack(side='left', padx=5)
        
        # Refresh Button
        refresh_btn = tk.Button(button_frame,
                               text="Refresh",
                               bg=self.colors['background'],
                               fg=self.colors['primary'],
                               activebackground=self.colors['primary'],
                               activeforeground=self.colors['white'],
                               font=('Arial', 14, 'bold'),
                               width=10,
                               relief='flat',
                               command=self.refresh_view_async)
        refresh_btn.pack(side='left', padx=5)

    def create_references_table(self):
        """Create the references table using Treeview with virtual scrolling"""
        if not self.reference_frame:
            return
            
        # Treeview Style
        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Arial', 14, 'bold'), padding=10)
        
        # Create frame for treeview and scrollbar
        tree_frame = tk.Frame(self.reference_frame, bg=self.colors['white'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # References Treeview with optimized columns
        self.references_tree = ttk.Treeview(
            tree_frame, 
            columns=('Name', 'Position', 'Pressure', 'Time', 'Description', 'Status'), 
            show='headings', 
            style="Treeview"
        )
        
        # Define headings
        self.references_tree.heading('Name', text='Reference ID')
        self.references_tree.heading('Position', text='Position (mm)')
        self.references_tree.heading('Pressure', text='Pressure (bar)')
        self.references_tree.heading('Time', text='Time (min)')
        self.references_tree.heading('Description', text='Description')
        self.references_tree.heading('Status', text='Status')
        
        # Set column widths
        self.references_tree.column('Name', width=150)
        self.references_tree.column('Position', width=120)
        self.references_tree.column('Pressure', width=120)
        self.references_tree.column('Time', width=100)
        self.references_tree.column('Description', width=200)
        self.references_tree.column('Status', width=100)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.references_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.references_tree.xview)
        
        self.references_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for better control
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.references_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Bind events
        self.references_tree.bind('<Double-1>', self.load_selected_reference)
        self.references_tree.bind('<Button-3>', self.show_context_menu)  # Right-click menu
        
        # Bind selection change for responsive UI
        self.references_tree.bind('<<TreeviewSelect>>', self.on_selection_change)

    def show_loading_indicator(self, show: bool = True):
        """Show or hide loading indicator"""
        if not self.loading_indicator or not self.progress_label:
            return
            
        if show:
            self.loading_indicator.pack(side='left')
            self.progress_label.pack(side='left', padx=5)
        else:
            self.loading_indicator.pack_forget()
            self.progress_label.pack_forget()

    def update_progress(self, current: int, total: int):
        """Update progress indicator"""
        if self.progress_label and self.progress_label.winfo_exists():
            progress_text = f"({current}/{total})"
            self.progress_label.config(text=progress_text)

    def populate_references_async(self):
        """Populate references asynchronously to prevent UI freezing"""
        if self._loading:
            return
        
        self._loading = True
        self._load_cancelled = False
        self.show_loading_indicator(True)
        
        def _load_worker():
            """Background worker for loading references"""
            try:
                # Get references from settings
                references = self.app_controller.settings.get('references', {})
                
                # Get current reference from app controller (more reliable)
                current_ref = None
                if hasattr(self.app_controller, 'current_reference'):
                    current_ref = self.app_controller.current_reference
                
                # Fallback to settings if app controller doesn't have it
                if not current_ref:
                    current_ref = self.app_controller.settings.get('last_reference')
                
                # Convert to list for chunked processing
                ref_items = list(references.items())
                total_refs = len(ref_items)
                
                if total_refs == 0:
                    # No references to load
                    self.parent.after_idle(self._populate_complete, [])
                    return
                
                # Process in chunks to prevent UI freezing
                processed_items = []
                
                for i in range(0, total_refs, self._chunk_size):
                    if self._load_cancelled:
                        break
                    
                    # Process chunk
                    chunk = ref_items[i:i + self._chunk_size]
                    chunk_data = []
                    
                    for ref_id, ref_data in chunk:
                        try:
                            params = ref_data.get('parameters', {})
                            description = ref_data.get('description', '')
                            status = "Active" if ref_id == current_ref else "Available"
                            
                            item_data = {
                                'ref_id': ref_id,
                                'position': f"{params.get('position', 'N/A'):.1f}" if isinstance(params.get('position'), (int, float)) else 'N/A',
                                'pressure': f"{params.get('target_pressure', 'N/A'):.1f}" if isinstance(params.get('target_pressure'), (int, float)) else 'N/A',
                                'time': f"{params.get('inspection_time', 'N/A'):.1f}" if isinstance(params.get('inspection_time'), (int, float)) else 'N/A',
                                'description': description,
                                'status': status
                            }
                            
                            chunk_data.append(item_data)
                            
                        except Exception as e:
                            print(f"Error processing reference {ref_id}: {e}")
                            continue
                    
                    processed_items.extend(chunk_data)
                    
                    # Update progress on main thread
                    current_count = min(i + self._chunk_size, total_refs)
                    self.parent.after_idle(self.update_progress, current_count, total_refs)
                    
                    # Small delay to allow UI updates
                    if not self._load_cancelled:
                        time.sleep(self._load_delay)
                
                # Complete loading on main thread
                if not self._load_cancelled:
                    self.parent.after_idle(self._populate_complete, processed_items)
                else:
                    self.parent.after_idle(self._populate_cancelled)
                    
            except Exception as e:
                print(f"Error in reference loading worker: {e}")
                import traceback
                traceback.print_exc()
                self.parent.after_idle(self._populate_error, str(e))
        
        # Start loading in background thread
        self._load_thread = threading.Thread(target=_load_worker, daemon=True, name="ReferenceLoader")
        self._load_thread.start()

    def _populate_complete(self, processed_items: List[Dict[str, Any]]):
        """Complete population on main thread"""
        try:
            # Check if the view is still valid
            if not self.reference_frame or not self.reference_frame.winfo_exists():
                print("Reference frame no longer exists, skipping population")
                self._loading_complete()
                return
            
            # Clear existing items efficiently
            if self.references_tree and self.references_tree.winfo_exists():
                try:
                    children = self.references_tree.get_children()
                    if children:
                        self.references_tree.delete(*children)
                except Exception as e:
                    print(f"Error clearing tree items: {e}")
                    # If we can't access the tree, it might be destroyed
                    self._loading_complete()
                    return
            else:
                print("References tree no longer exists, skipping population")
                self._loading_complete()
                return
            
            # If no items to process, complete immediately
            if not processed_items:
                self._loading_complete()
                return
            
            # Get current reference for highlighting
            current_ref = None
            if hasattr(self.app_controller, 'current_reference'):
                current_ref = self.app_controller.current_reference
            
            # Add items in batches to maintain responsiveness
            batch_size = 20
            
            def add_batch(start_index: int):
                try:
                    # Check if widgets still exist
                    if not self.reference_frame or not self.reference_frame.winfo_exists():
                        print("Reference frame destroyed during batch processing")
                        self._loading_complete()
                        return
                        
                    if not self.references_tree or not self.references_tree.winfo_exists():
                        print("References tree destroyed during batch processing")
                        self._loading_complete()
                        return
                        
                    end_index = min(start_index + batch_size, len(processed_items))
                    
                    for i in range(start_index, end_index):
                        # Check again before each item
                        if not self.references_tree.winfo_exists():
                            print("References tree destroyed during item processing")
                            break
                            
                        item_data = processed_items[i]
                        
                        try:
                            item_id = self.references_tree.insert('', 'end', values=(
                                str(item_data['ref_id']),  # Ensure ref_id is string
                                item_data['position'],
                                item_data['pressure'],
                                item_data['time'],
                                item_data['description'],
                                item_data['status']
                            ))
                            
                            # Highlight active reference
                            if item_data['ref_id'] == current_ref:
                                self.references_tree.selection_set(item_id)
                                self.references_tree.focus(item_id)
                                # Ensure the item is visible
                                self.references_tree.see(item_id)
                        except Exception as e:
                            print(f"Error inserting item {i}: {e}")
                            break
                    
                    # Schedule next batch if more items to process
                    if end_index < len(processed_items) and self.references_tree.winfo_exists():
                        # Use after instead of after_idle to prevent blocking
                        self.parent.after(1, lambda idx=end_index: add_batch(idx))
                    else:
                        # All items processed
                        self._loading_complete()
                        
                except Exception as e:
                    print(f"Error adding batch: {e}")
                    self._loading_complete()
            
            # Start adding batches with a small delay to ensure UI is ready
            self.parent.after(10, lambda: add_batch(0))
                
        except Exception as e:
            print(f"Error completing population: {e}")
            self._loading_complete()

    def _populate_cancelled(self):
        """Handle cancelled loading"""
        self._loading_complete()
        print("Reference loading cancelled")

    def _populate_error(self, error_message: str):
        """Handle loading error"""
        self._loading_complete()
        print(f"Reference loading error: {error_message}")
        
        # Remove messagebox - just log the error
        print(f"Error loading references: {error_message}")

    def _loading_complete(self):
        """Cleanup after loading completion"""
        self._loading = False
        self._load_cancelled = False
        self.show_loading_indicator(False)
        
        # Synchronize current reference
        self._sync_current_reference()
        
        print("Reference loading completed")

    def _sync_current_reference(self):
        """Synchronize current reference between app controller and settings"""
        try:
            # Get current reference from app controller
            current_ref = None
            if hasattr(self.app_controller, 'current_reference'):
                current_ref = self.app_controller.current_reference
                if current_ref:
                    current_ref = str(current_ref)  # Ensure it's a string
            
            # Get last reference from settings
            last_ref = self.app_controller.settings.get('last_reference')
            if last_ref:
                last_ref = str(last_ref)  # Ensure it's a string
            
            # If app controller has a reference but settings don't, update settings
            if current_ref and current_ref != last_ref:
                self.app_controller.settings['last_reference'] = current_ref
                # Don't save here to avoid blocking UI
                
            # If settings have a reference but app controller doesn't, update app controller
            elif last_ref and not current_ref:
                if hasattr(self.app_controller, 'current_reference'):
                    self.app_controller.current_reference = last_ref
                    
        except Exception as e:
            print(f"Error synchronizing current reference: {e}")

    def cancel_loading(self):
        """Cancel ongoing loading operation"""
        if self._loading:
            self._load_cancelled = True
            print("Reference loading cancelled by user")

    def refresh_view_async(self):
        """Refresh the reference view asynchronously"""
        if self._loading:
            self.cancel_loading()
            # Wait a moment for cancellation to complete
            self.parent.after(100, self.populate_references_async)
        else:
            self.populate_references_async()

    def on_selection_change(self, event):
        """Handle tree selection change for responsive UI"""
        # This method can be used for real-time updates without blocking
        pass

    def show_context_menu(self, event):
        """Show right-click context menu"""
        try:
            if not self.references_tree:
                return
                
            # Select the item under cursor
            item = self.references_tree.identify_row(event.y)
            if item:
                self.references_tree.selection_set(item)
                
                # Create context menu
                context_menu = tk.Menu(self.parent, tearoff=0)
                context_menu.add_command(label="Load Reference", command=self.load_selected_reference_button)
                context_menu.add_command(label="Edit Reference", command=self.open_edit_reference_dialog)
                context_menu.add_separator()
                context_menu.add_command(label="Delete Reference", command=self.open_delete_reference_dialog)
                context_menu.add_separator()
                context_menu.add_command(label="Refresh List", command=self.refresh_view_async)
                
                # Show menu
                context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def get_selected_reference(self) -> Optional[str]:
        """Get the currently selected reference ID"""
        try:
            if not self.references_tree or not self.references_tree.winfo_exists():
                return None
                
            selected = self.references_tree.selection()
            if not selected:
                return None
                
            item = self.references_tree.item(selected[0])
            if not item or 'values' not in item or not item['values']:
                return None
                
            ref_id = item['values'][0]  # Reference ID is first column
            
            # Ensure ref_id is a string
            ref_id = str(ref_id)
            
            # Debug: Print what we're looking for
            print(f"Looking for reference: '{ref_id}' (type: {type(ref_id)})")
            
            # Refresh settings from settings manager to ensure we have latest data
            self._refresh_settings_from_manager()
            
            # Validate that the reference exists in settings
            references = self.app_controller.settings.get('references', {})
            print(f"Available references in settings: {list(references.keys())}")
            print(f"Reference types in settings: {[type(k) for k in references.keys()]}")
            
            if ref_id not in references:
                print(f"Warning: Selected reference '{ref_id}' not found in settings")
                print(f"Settings keys: {list(references.keys())}")
                return None
                
            return ref_id
            
        except Exception as e:
            print(f"Error getting selected reference: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _force_reload_treeview(self):
        """Force reload the treeview from current settings"""
        try:
            print("Forcing treeview reload from settings...")
            
            # Clear current treeview
            if self.references_tree and self.references_tree.winfo_exists():
                children = self.references_tree.get_children()
                if children:
                    self.references_tree.delete(*children)
            
            # Reload from settings
            self.populate_references_async()
            
        except Exception as e:
            print(f"Error forcing treeview reload: {e}")

    def _validate_treeview_against_settings(self):
        """Validate that treeview items match what's in settings"""
        try:
            if not self.references_tree or not self.references_tree.winfo_exists():
                return
                
            # Get current treeview items
            tree_items = []
            for item_id in self.references_tree.get_children():
                item = self.references_tree.item(item_id)
                if item['values']:
                    # Ensure reference ID is a string
                    ref_id = str(item['values'][0])
                    tree_items.append(ref_id)
            
            # Get settings references
            references = self.app_controller.settings.get('references', {})
            settings_items = [str(k) for k in references.keys()]  # Convert all to strings
            
            print(f"Treeview items: {tree_items}")
            print(f"Settings items: {settings_items}")
            
            # Check for mismatches
            tree_set = set(tree_items)
            settings_set = set(settings_items)
            
            missing_in_settings = tree_set - settings_set
            missing_in_treeview = settings_set - tree_set
            
            if missing_in_settings:
                print(f"Items in treeview but missing in settings: {missing_in_settings}")
                # Force reload if there are mismatches
                self._force_reload_treeview()
                return False
                
            if missing_in_treeview:
                print(f"Items in settings but missing in treeview: {missing_in_treeview}")
                # Force reload if there are mismatches
                self._force_reload_treeview()
                return False
                
            if not missing_in_settings and not missing_in_treeview:
                print("Treeview and settings are in sync")
                return True
                
        except Exception as e:
            print(f"Error validating treeview against settings: {e}")
            return False

    def _force_reload_app_controller_settings(self):
        """Force reload app controller settings from settings manager"""
        try:
            print("Forcing app controller settings reload...")
            
            if hasattr(self.app_controller, 'settings_manager'):
                # Force reload settings from file
                if hasattr(self.app_controller.settings_manager, 'load_settings'):
                    success = self.app_controller.settings_manager.load_settings()
                    print(f"Settings manager load result: {success}")
                
                # Update app controller settings reference
                if hasattr(self.app_controller.settings_manager, 'settings'):
                    self.app_controller.settings = self.app_controller.settings_manager.settings
                    print("App controller settings updated from manager")
                    
                    # Also update current reference if needed
                    if hasattr(self.app_controller, 'current_reference'):
                        last_ref = self.app_controller.settings.get('last_reference')
                        if last_ref and self.app_controller.current_reference != last_ref:
                            self.app_controller.current_reference = last_ref
                            print(f"Updated app controller current_reference to: {last_ref}")
                
            else:
                print("No settings manager available")
                
        except Exception as e:
            print(f"Error forcing app controller settings reload: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_settings_from_manager(self):
        """Refresh settings from the settings manager to ensure we have latest data"""
        try:
            if hasattr(self.app_controller, 'settings_manager'):
                # Force reload settings from file
                if hasattr(self.app_controller.settings_manager, 'load_settings'):
                    self.app_controller.settings_manager.load_settings()
                
                # Update app controller settings reference
                if hasattr(self.app_controller.settings_manager, 'settings'):
                    self.app_controller.settings = self.app_controller.settings_manager.settings
                    
                print("Settings refreshed from manager")
                
                # Validate treeview against refreshed settings
                self._validate_treeview_against_settings()
                
        except Exception as e:
            print(f"Error refreshing settings: {e}")

    def open_add_reference_dialog(self):
        """Open dialog to add a new reference"""
        try:
            print("Opening add reference dialog...")
            dialog = ReferenceDialog(
                self.app_controller, 
                self.colors, 
                callback=self.refresh_view_async
            )
            if hasattr(dialog, 'dialog'):
                print("Reference dialog created successfully")
        except Exception as e:
            print(f"Error opening add reference dialog: {e}")
            # Remove messagebox - just log the error
            print(f"Could not open reference dialog: {str(e)}")

    def open_edit_reference_dialog(self):
        """Open dialog to edit selected reference"""
        try:
            selected_ref = self.get_selected_reference()
            if not selected_ref:
                # Remove messagebox - just log the warning
                print("No reference selected for editing")
                return
            
            print(f"Opening edit dialog for reference: {selected_ref}")
            dialog = ReferenceDialog(
                self.app_controller, 
                self.colors,
                existing_ref=selected_ref,
                callback=self.refresh_view_async
            )
            if hasattr(dialog, 'dialog'):
                print(f"Edit dialog created for {selected_ref}")
        except Exception as e:
            print(f"Error opening edit reference dialog: {e}")
            # Remove messagebox - just log the error
            print(f"Could not open edit dialog: {str(e)}")

    def open_delete_reference_dialog(self):
        """Open dialog to delete a reference with async operation"""
        try:
            selected_ref = self.get_selected_reference()
            if not selected_ref:
                # Remove messagebox - just log the warning
                print("No reference selected for deletion")
                return
            
            # Remove confirmation dialog - just delete directly
            print(f"Deleting reference: {selected_ref}")
            self._delete_reference_async(selected_ref)
                
        except Exception as e:
            print(f"Error in delete reference: {e}")
            # Remove messagebox - just log the error
            print(f"Error deleting reference: {str(e)}")

    def _delete_reference_async(self, ref_id: str):
        """Delete reference asynchronously"""
        def _delete_worker():
            try:
                # Use async delete if available
                if hasattr(self.app_controller, 'settings_manager') and hasattr(self.app_controller.settings_manager, 'delete_reference_async'):
                    operation_id = self.app_controller.settings_manager.delete_reference_async(
                        ref_id,
                        callback=self._delete_callback
                    )
                else:
                    # Fallback to synchronous delete
                    success = self.app_controller.delete_reference(ref_id)
                    self.parent.after_idle(self._delete_callback, success, f"Reference '{ref_id}' {'deleted' if success else 'deletion failed'}")
                    
            except Exception as e:
                error_msg = f"Error deleting reference: {e}"
                self.parent.after_idle(self._delete_callback, False, error_msg)
        
        # Start delete operation in background
        delete_thread = threading.Thread(target=_delete_worker, daemon=True, name="ReferenceDelete")
        delete_thread.start()

    def _delete_callback(self, success: bool, message: str):
        """Callback for delete operation"""
        if success:
            # Reset current reference if deleted
            selected_ref = message.split("'")[1] if "'" in message else ""
            if hasattr(self.app_controller, 'current_reference') and self.app_controller.current_reference == selected_ref:
                self.app_controller.current_reference = None
            
            # Refresh the view
            self.refresh_view_async()
            
            # Remove messagebox - just log success
            print(f"Success: {message}")
        else:
            # Remove messagebox - just log error
            print(f"Error: {message}")

    def _show_load_feedback(self, ref_id: str, success: bool = True):
        """Show visual feedback for reference loading"""
        try:
            if not self.references_tree or not self.references_tree.winfo_exists():
                return
                
            # Ensure ref_id is a string for comparison
            ref_id = str(ref_id)
                
            # Find the item in the tree
            for item_id in self.references_tree.get_children():
                item = self.references_tree.item(item_id)
                if item['values'] and str(item['values'][0]) == ref_id:
                    if success:
                        # Highlight the loaded reference briefly
                        self.references_tree.selection_set(item_id)
                        self.references_tree.focus(item_id)
                        self.references_tree.see(item_id)
                        
                        # Flash the item briefly
                        self.parent.after(100, lambda: self._flash_item(item_id))
                    break
                    
        except Exception as e:
            print(f"Error showing load feedback: {e}")

    def _flash_item(self, item_id: str):
        """Flash an item briefly to show it's been loaded"""
        try:
            if not self.references_tree or not self.references_tree.winfo_exists():
                return
                
            # This is a simple visual feedback - in a more sophisticated UI,
            # you might change colors or add animations
            self.references_tree.selection_set(item_id)
            self.references_tree.focus(item_id)
            
        except Exception as e:
            print(f"Error flashing item: {e}")

    def _validate_reference_data(self, ref_id: str) -> bool:
        """Validate that reference data is properly formatted"""
        try:
            # Ensure ref_id is a string
            ref_id = str(ref_id)
            
            references = self.app_controller.settings.get('references', {})
            if ref_id not in references:
                return False
                
            ref_data = references[ref_id]
            
            # Check required fields
            if 'parameters' not in ref_data:
                print(f"Reference '{ref_id}' missing parameters")
                return False
                
            params = ref_data['parameters']
            required_params = ['position', 'target_pressure', 'inspection_time']
            
            for param in required_params:
                if param not in params:
                    print(f"Reference '{ref_id}' missing parameter: {param}")
                    return False
                    
                # Validate parameter types and ranges
                value = params[param]
                if not isinstance(value, (int, float)):
                    print(f"Reference '{ref_id}' parameter '{param}' is not numeric: {value}")
                    return False
                    
                # Basic range validation
                if param == 'position' and (value < 0 or value > 300):
                    print(f"Reference '{ref_id}' position out of range: {value}")
                    return False
                elif param == 'target_pressure' and (value < 0 or value > 5):
                    print(f"Reference '{ref_id}' pressure out of range: {value}")
                    return False
                elif param == 'inspection_time' and (value < 0 or value > 120):
                    print(f"Reference '{ref_id}' inspection time out of range: {value}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Error validating reference data: {e}")
            return False

    def _force_main_view_refresh(self):
        """Force refresh of the main view to show updated reference data"""
        try:
            if hasattr(self.app_controller, 'main_window'):
                main_window = self.app_controller.main_window
                
                # Try different refresh methods
                if hasattr(main_window, 'refresh_current_view'):
                    main_window.refresh_current_view()
                elif hasattr(main_window, 'show_main_view'):
                    # Force refresh by switching back to main view
                    main_window.show_main_view()
                elif hasattr(main_window, 'main_view') and main_window.main_view:
                    # Try to refresh the main view directly
                    if hasattr(main_window.main_view, 'update_test_parameters'):
                        main_window.main_view.update_test_parameters()
                    elif hasattr(main_window.main_view, 'refresh'):
                        main_window.main_view.refresh()
                        
        except Exception as e:
            print(f"Error forcing main view refresh: {e}")

    def load_selected_reference(self, event=None):
        """Load the selected reference from the treeview"""
        try:
            selected_ref = self.get_selected_reference()
            if not selected_ref:
                if event:  # Only show warning if triggered by user action
                    print("No reference selected for loading")
                return
            
            # Check if reference exists in settings
            references = self.app_controller.settings.get('references', {})
            if selected_ref not in references:
                print(f"Reference '{selected_ref}' not found in settings, attempting to refresh...")
                
                # Try to force reload app controller settings
                self._force_reload_app_controller_settings()
                
                # Check again after refresh
                references = self.app_controller.settings.get('references', {})
                if selected_ref not in references:
                    print(f"Reference '{selected_ref}' still not found after refresh")
                    
                    # Debug the current state
                    self.debug_app_controller_settings()
                    
                    # Update status in main window if available
                    if hasattr(self.app_controller, 'main_window') and self.app_controller.main_window:
                        main_window = self.app_controller.main_window
                        if hasattr(main_window, 'update_system_status'):
                            main_window.update_system_status(f"Reference '{selected_ref}' not found in settings", "error")
                    return
                else:
                    print(f"Reference '{selected_ref}' found after refresh")
            
            # Validate reference data
            if not self._validate_reference_data(selected_ref):
                print(f"Reference '{selected_ref}' has invalid data")
                # Update status in main window if available
                if hasattr(self.app_controller, 'main_window') and self.app_controller.main_window:
                    main_window = self.app_controller.main_window
                    if hasattr(main_window, 'update_system_status'):
                        main_window.update_system_status(f"Reference '{selected_ref}' has invalid data", "error")
                return
            
            # Update reference selection in app controller
            success = self.app_controller.set_current_reference(selected_ref)
            
            if success:
                print(f"Successfully loaded reference: {selected_ref}")
                
                # Show visual feedback
                self._show_load_feedback(selected_ref, True)
                
                # Update status in main window if available
                if hasattr(self.app_controller, 'main_window') and self.app_controller.main_window:
                    main_window = self.app_controller.main_window
                    if hasattr(main_window, 'update_system_status'):
                        main_window.update_system_status(f"Reference '{selected_ref}' loaded", "success")
                
                # Refresh the reference view to show active status
                self.refresh_view_async()
                
                print(f"Reference '{selected_ref}' is now active and ready for testing")
                
                # Force refresh main view
                self._force_main_view_refresh()
                
                # Update app controller status if method exists
                if hasattr(self.app_controller, 'update_status'):
                    self.app_controller.update_status(f"Reference '{selected_ref}' loaded successfully", "info")
                    
            else:
                print(f"Failed to load reference '{selected_ref}'")
                # Show visual feedback for failure
                self._show_load_feedback(selected_ref, False)
                
                # Update status in main window if available
                if hasattr(self.app_controller, 'main_window') and self.app_controller.main_window:
                    main_window = self.app_controller.main_window
                    if hasattr(main_window, 'update_system_status'):
                        main_window.update_system_status(f"Failed to load reference '{selected_ref}'", "error")
                
        except Exception as e:
            print(f"Error loading reference: {e}")
            import traceback
            traceback.print_exc()
            
            # Update status in main window if available
            if hasattr(self.app_controller, 'main_window') and self.app_controller.main_window:
                main_window = self.app_controller.main_window
                if hasattr(main_window, 'update_system_status'):
                    main_window.update_system_status(f"Error loading reference: {str(e)}", "error")

    def load_selected_reference_button(self):
        """Load selected reference (button version)"""
        self.load_selected_reference()

    def refresh_view(self):
        """Refresh the reference view (synchronous version for compatibility)"""
        self.refresh_view_async()

    def get_reference_count(self) -> int:
        """Get the number of references"""
        return len(self.app_controller.settings.get('references', {}))

    def get_loading_status(self) -> Dict[str, Any]:
        """Get current loading status"""
        thread_active = False
        if self._load_thread:
            thread_active = self._load_thread.is_alive()
            
        return {
            'loading': self._loading,
            'cancelled': self._load_cancelled,
            'thread_active': thread_active
        }

    def cleanup(self):
        """Cleanup resources when view is destroyed"""
        try:
            # Cancel any ongoing loading
            if self._loading:
                self.cancel_loading()
            
            # Wait for thread to finish
            if self._load_thread and self._load_thread.is_alive():
                self._load_thread.join(timeout=1)
            
            print("Reference view cleanup completed")
            
        except Exception as e:
            print(f"Error during reference view cleanup: {e}")

    def destroy(self):
        """Destroy the view and cleanup resources"""
        try:
            # Cancel any ongoing operations
            self.cleanup()
            
            # Destroy the frame if it exists
            if self.reference_frame and self.reference_frame.winfo_exists():
                self.reference_frame.destroy()
            
            print("Reference view destroyed")
            
        except Exception as e:
            print(f"Error destroying reference view: {e}")

    # Legacy method for backward compatibility
    def populate_references_tree(self):
        """Legacy method for backward compatibility"""
        self.populate_references_async()

    def get_current_reference_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded reference"""
        try:
            info = {
                'app_controller_ref': None,
                'settings_ref': None,
                'ref_data': None,
                'is_valid': False
            }
            
            # Get reference from app controller
            if hasattr(self.app_controller, 'current_reference'):
                info['app_controller_ref'] = self.app_controller.current_reference
            
            # Get reference from settings
            info['settings_ref'] = self.app_controller.settings.get('last_reference')
            
            # Get reference data if available
            current_ref = info['app_controller_ref'] or info['settings_ref']
            if current_ref:
                references = self.app_controller.settings.get('references', {})
                if current_ref in references:
                    info['ref_data'] = references[current_ref]
                    info['is_valid'] = self._validate_reference_data(current_ref)
            
            return info
            
        except Exception as e:
            print(f"Error getting current reference info: {e}")
            return {
                'app_controller_ref': None,
                'settings_ref': None,
                'ref_data': None,
                'is_valid': False,
                'error': str(e)
            }

    def debug_app_controller_settings(self):
        """Debug method to check app controller settings loading"""
        try:
            print("=== App Controller Settings Debug ===")
            
            # Check if app controller has settings
            if hasattr(self.app_controller, 'settings'):
                print(f"App controller has settings: {type(self.app_controller.settings)}")
                print(f"Settings keys: {list(self.app_controller.settings.keys())}")
                
                # Check references specifically
                references = self.app_controller.settings.get('references', {})
                print(f"References in app controller: {list(references.keys())}")
                
                # Check last reference
                last_ref = self.app_controller.settings.get('last_reference')
                print(f"Last reference in settings: {last_ref}")
                
            else:
                print("App controller has no settings attribute")
            
            # Check settings manager
            if hasattr(self.app_controller, 'settings_manager'):
                print(f"Settings manager type: {type(self.app_controller.settings_manager)}")
                
                if hasattr(self.app_controller.settings_manager, 'settings'):
                    manager_settings = self.app_controller.settings_manager.settings
                    print(f"Manager settings keys: {list(manager_settings.keys())}")
                    
                    manager_refs = manager_settings.get('references', {})
                    print(f"Manager references: {list(manager_refs.keys())}")
                    
                    manager_last_ref = manager_settings.get('last_reference')
                    print(f"Manager last reference: {manager_last_ref}")
                    
            else:
                print("App controller has no settings_manager attribute")
                
            # Check current reference
            if hasattr(self.app_controller, 'current_reference'):
                print(f"App controller current_reference: {self.app_controller.current_reference}")
            else:
                print("App controller has no current_reference attribute")
                
            print("=====================================")
            
        except Exception as e:
            print(f"Error in debug_app_controller_settings: {e}")
            import traceback
            traceback.print_exc()

    def debug_reference_state(self):
        """Debug method to print current reference state"""
        try:
            info = self.get_current_reference_info()
            print("=== Reference State Debug ===")
            print(f"App Controller Reference: {info['app_controller_ref']}")
            print(f"Settings Reference: {info['settings_ref']}")
            print(f"Is Valid: {info['is_valid']}")
            if info['ref_data']:
                print(f"Reference Data: {info['ref_data']}")
            print("=============================")
            
            # Also debug app controller settings
            self.debug_app_controller_settings()
            
        except Exception as e:
            print(f"Error in debug_reference_state: {e}")


# Backward compatibility wrapper
class ReferenceView(OptimizedReferenceView):
    """Backward compatible reference view"""
    pass