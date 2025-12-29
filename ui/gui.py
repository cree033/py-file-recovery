"""Graphical User Interface for the file recovery system"""

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

from controllers.recovery_controller import RecoveryController
from models.config import FileSignatures
from models.resource_config import ResourceConfig
from utils.encoding_utils import detect_encoding
from utils.file_utils import clean_filename
import threading
import os
import base64
import tempfile


class GUI:
    """Graphical User Interface for file recovery"""
    
    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter is not available. Install it or use CLI mode.")
        
        self.controller = RecoveryController()
        self.root = tk.Tk()
        self.root.title("File Recovery System")
        self.root.geometry("800x600")
        
        # Set application icon
        self._set_icon()
        
        self.is_scanning = False
        self.total_size = 0
        self.physical_drives_info = None  # Store physical drive info
        self.setup_ui()
    
    def setup_ui(self):
        """Sets up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Drive selection
        ttk.Label(main_frame, text="Drive:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(main_frame, textvariable=self.drive_var, width=30)
        self.drive_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="Refresh", command=self.refresh_drives).grid(row=0, column=2, padx=5)
        
        # Drive type
        self.drive_type_var = tk.StringVar(value="logical")
        ttk.Radiobutton(main_frame, text="Logical", variable=self.drive_type_var, 
                       value="logical", command=self.refresh_drives).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(main_frame, text="Physical", variable=self.drive_type_var, 
                       value="physical", command=self.refresh_drives).grid(row=1, column=1, sticky=tk.W)
        
        # Output directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_var, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5)
        
        # File types
        ttk.Label(main_frame, text="File Types:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.file_types_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_types_var, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(e.g: txt,pdf,doc or leave empty for all)").grid(row=4, column=1, sticky=tk.W)
        
        # Search pattern
        ttk.Label(main_frame, text="Search Pattern:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.search_var, width=40).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(e.g: *pass*.txt or %wall%)").grid(row=6, column=1, sticky=tk.W)
        
        # Options
        self.filter_system_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Filter system files", 
                       variable=self.filter_system_var).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Operation mode (Preview or Recover)
        ttk.Label(main_frame, text="Operation Mode:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.operation_mode_var = tk.StringVar(value="recover")
        operation_frame = ttk.Frame(main_frame)
        operation_frame.grid(row=8, column=1, sticky=tk.W)
        ttk.Radiobutton(operation_frame, text="Preview (List Only)", variable=self.operation_mode_var, 
                       value="preview").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(operation_frame, text="Recover Files", variable=self.operation_mode_var, 
                       value="recover").pack(side=tk.LEFT, padx=5)
        
        # Resource mode
        ttk.Label(main_frame, text="Resource Mode:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.resource_mode_var = tk.StringVar(value="balanced")
        resource_frame = ttk.Frame(main_frame)
        resource_frame.grid(row=9, column=1, sticky=tk.W)
        ttk.Radiobutton(resource_frame, text="Performance", variable=self.resource_mode_var, 
                       value="performance", command=self._update_memory_info).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(resource_frame, text="Balanced", variable=self.resource_mode_var, 
                       value="balanced", command=self._update_memory_info).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(resource_frame, text="Low Resources", variable=self.resource_mode_var, 
                       value="low", command=self._update_memory_info).pack(side=tk.LEFT, padx=5)
        
        # Memory info label
        self.memory_info_var = tk.StringVar(value="")
        self.memory_info_label = ttk.Label(main_frame, textvariable=self.memory_info_var, 
                                          foreground="blue", font=('Arial', 9))
        self.memory_info_label.grid(row=9, column=2, sticky=tk.W, padx=5)
        self._update_memory_info()  # Initial update
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_recovery)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_recovery, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Progress (moved above logs)
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.progress_percent_var = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_percent_var, font=('Arial', 10, 'bold')).grid(row=2, column=0, pady=2)
        
        # Preview/Results area
        results_label = ttk.Label(main_frame, text="Results / Log:")
        results_label.grid(row=12, column=0, sticky=(tk.W, tk.N), pady=5)
        
        # Create notebook for Preview and Log tabs
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.grid(row=12, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Log tab
        log_frame = ttk.Frame(self.results_notebook)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.results_notebook.add(log_frame, text="Log")
        
        # Preview tab (will be populated when in preview mode)
        self.preview_frame = ttk.Frame(self.results_notebook)
        self.preview_tree = None  # Will be created when needed
        self.preview_file_data = {}  # Store file data by item ID for recovery
        self.results_notebook.add(self.preview_frame, text="Preview")
        
        main_frame.rowconfigure(12, weight=1)
        
        # Initialize
        self.refresh_drives()
        self.log("GUI initialized. Ready to start recovery.")
    
    def _set_icon(self):
        """Sets the application icon"""
        try:
            # Try to create a simple icon using PIL if available
            try:
                from PIL import Image, ImageDraw
                
                # Create a simple icon: folder with recovery arrow
                icon_size = 64
                img = Image.new('RGBA', (icon_size, icon_size), (240, 240, 240, 255))
                draw = ImageDraw.Draw(img)
                
                # Draw a folder icon (recovery theme)
                # Folder base
                folder_points = [
                    (12, 20), (52, 20), (52, 24), (56, 24),
                    (56, 52), (12, 52)
                ]
                draw.polygon(folder_points, fill=(70, 130, 180), outline=(50, 100, 150), width=2)
                
                # Folder tab
                tab_points = [
                    (12, 20), (20, 20), (20, 16), (28, 16), (28, 20), (52, 20)
                ]
                draw.polygon(tab_points, fill=(90, 150, 200), outline=(50, 100, 150), width=2)
                
                # Recovery arrow (circular arrow pointing up)
                # Arrow body
                arrow_points = [
                    (32, 30), (40, 30), (40, 26), (44, 32),
                    (40, 38), (40, 34), (32, 34)
                ]
                draw.polygon(arrow_points, fill=(50, 205, 50), outline=(40, 180, 40), width=2)
                
                # Circular part of arrow
                draw.arc([28, 28, 44, 44], start=0, end=180, fill=(50, 205, 50), width=3)
                
                # Save to temporary file
                icon_path = os.path.join(tempfile.gettempdir(), 'recovery_icon.ico')
                # Save as ICO (PIL will handle multiple sizes automatically)
                img.save(icon_path, format='ICO')
                self.root.iconbitmap(icon_path)
                
            except ImportError:
                # PIL not available, try using Windows default icon or emoji
                try:
                    # Try to use a system icon
                    import sys
                    if sys.platform == 'win32':
                        # Use Windows default application icon
                        self.root.iconbitmap(default='')
                except:
                    # Last resort: use emoji in title (Windows 10+)
                    self.root.title("💾 File Recovery System")
        except Exception as e:
            # If all fails, just continue without icon
            pass
    
    def refresh_drives(self):
        """Refreshes the drive list"""
        drive_type = self.drive_type_var.get()
        drives = []
        
        if drive_type == "logical":
            drives = self.controller.list_logical_drives()
            drives = [f"{d}:" for d in drives]
        else:
            # Get physical drives with names
            drives_info = self.controller.list_physical_drives_with_names()
            if drives_info:
                # Store drive info for later use
                self.physical_drives_info = drives_info
                # Create display list with names
                drives = []
                for drive in drives_info:
                    model = drive.get('model', 'Unknown')
                    size_gb = ""
                    if 'size' in drive and drive['size']:
                        size_gb = f" ({drive['size'] / (1024**3):.2f} GB)"
                    drives.append(f"{drive['display_name']}{size_gb}")
            else:
                # Fallback to simple list
                drives = self.controller.list_physical_drives()
                self.physical_drives_info = None
        
        self.drive_combo['values'] = drives
        if drives:
            self.drive_var.set(drives[0])
    
    def browse_output(self):
        """Opens directory browser"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_var.set(directory)
    
    def _update_memory_info(self):
        """Updates the memory info label based on selected resource mode"""
        try:
            mode = self.resource_mode_var.get()
            if mode == "performance":
                config = ResourceConfig.create_performance_mode()
            elif mode == "low":
                config = ResourceConfig.create_low_resource_mode()
            else:  # balanced
                config = ResourceConfig.create_balanced_mode()
            
            if config.max_memory_mb:
                mem_gb = config.max_memory_mb / 1024
                total_mem_gb = ResourceConfig.get_available_memory_mb() / 1024
                percentage = (config.max_memory_mb / ResourceConfig.get_available_memory_mb()) * 100
                self.memory_info_var.set(f"→ Will use: {mem_gb:.1f} GB ({percentage:.0f}% of {total_mem_gb:.1f} GB RAM)")
            else:
                self.memory_info_var.set("→ No memory limit")
        except Exception as e:
            self.memory_info_var.set("→ Error calculating memory")
    
    def log(self, message):
        """Adds a message to the log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_recovery(self):
        """Starts the recovery process"""
        if self.is_scanning:
            return
        
        # Validate inputs
        drive = self.drive_var.get()
        if not drive:
            messagebox.showerror("Error", "Please select a drive")
            return
        
        # Get operation mode
        operation_mode = self.operation_mode_var.get()
        preview_mode = (operation_mode == "preview")
        
        output = self.output_var.get()
        if not preview_mode and not output:
            messagebox.showerror("Error", "Please select output directory")
            return
        
        # Get file types
        file_types = None
        types_input = self.file_types_var.get().strip()
        if types_input:
            file_types = [t.strip().lower() for t in types_input.split(',') if t.strip()]
            valid_types = FileSignatures.get_all_types()
            file_types = [t for t in file_types if t in valid_types]
            if not file_types:
                file_types = None
        
        # Get search pattern
        search_pattern = self.search_var.get().strip() or None
        
        # Build disk path
        drive_type = self.drive_type_var.get()
        if drive_type == "logical":
            disk_path = rf"\\.\{drive.replace(':', '')}:"
        else:
            # For physical drives, extract the actual drive name from display string
            if self.physical_drives_info:
                # Find the matching drive info
                selected_drive = None
                for drive_info in self.physical_drives_info:
                    size_gb = ""
                    if 'size' in drive_info and drive_info['size']:
                        size_gb = f" ({drive_info['size'] / (1024**3):.2f} GB)"
                    display_name = f"{drive_info['display_name']}{size_gb}"
                    if display_name == drive:
                        selected_drive = drive_info
                        break
                
                if selected_drive:
                    disk_path = rf"\\.\{selected_drive['name']}"
                else:
                    # Fallback: try to extract PhysicalDrive from display name
                    if "PhysicalDrive" in drive:
                        parts = drive.split(" - ")
                        if parts:
                            disk_path = rf"\\.\{parts[0]}"
                    else:
                        disk_path = rf"\\.\{drive}"
            else:
                # Fallback to simple path
                if "PhysicalDrive" in drive:
                    parts = drive.split(" - ")
                    if parts:
                        disk_path = rf"\\.\{parts[0]}"
                else:
                    disk_path = rf"\\.\{drive}"
        
        # Get resource config
        resource_mode = self.resource_mode_var.get()
        if resource_mode == "performance":
            resource_config = ResourceConfig.create_performance_mode()
        elif resource_mode == "low":
            resource_config = ResourceConfig.create_low_resource_mode()
        else:
            resource_config = ResourceConfig.create_balanced_mode()
        
        # Store disk path for later recovery
        self.last_disk_path = disk_path
        
        # Get disk size for progress calculation
        self.total_size = self.controller.get_disk_size(disk_path)
        
        # Initialize preview tree if in preview mode
        if preview_mode:
            self._setup_preview_tree()
        
        # Start recovery in separate thread
        self.is_scanning = True
        self.recovery_thread = None  # Store thread reference
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Update button text based on mode
        if preview_mode:
            self.start_button.config(text="Previewing...", state=tk.DISABLED)
        else:
            self.start_button.config(text="Recovering...", state=tk.DISABLED)
        
        # Initialize progress bar
        if self.total_size and self.total_size > 0:
            self.progress_bar.config(mode='determinate', maximum=100)
            self.progress_bar['value'] = 0
        else:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
        self.progress_percent_var.set("0%")
        
        def recovery_thread():
            try:
                def progress_callback(blocks, position, found, memory_usage=None):
                    mb_scanned = position / (1024 * 1024)
                    mem_info = f" | Memory: {memory_usage:.1f} MB" if memory_usage else ""
                    
                    # Calculate percentage
                    if self.total_size and self.total_size > 0:
                        percentage = (position / self.total_size) * 100
                        mb_total = self.total_size / (1024 * 1024)
                        self.progress_var.set(f"Blocks: {blocks:,} | Scanned: {mb_scanned:.1f} MB / {mb_total:.1f} MB | Found: {found}{mem_info}")
                        self.progress_bar['value'] = percentage
                        self.progress_percent_var.set(f"{percentage:.2f}%")
                    else:
                        self.progress_var.set(f"Blocks: {blocks:,} | Scanned: {mb_scanned:.1f} MB | Found: {found}{mem_info}")
                        # Use indeterminate mode if size unknown
                        if self.progress_bar['mode'] != 'indeterminate':
                            self.progress_bar.config(mode='indeterminate')
                            self.progress_bar.start()
                        self.progress_percent_var.set("Calculating...")
                    
                    self.log(f"Progress: {blocks:,} blocks scanned, {found} files found{mem_info}")
                
                self.log(f"Starting recovery from {disk_path}")
                self.log(f"Output directory: {output}")
                if file_types:
                    self.log(f"File types: {', '.join(file_types)}")
                if search_pattern:
                    self.log(f"Search pattern: {search_pattern}")
                self.log(f"Resource mode: {resource_mode}")
                if resource_config.max_memory_mb:
                    mem_gb = resource_config.max_memory_mb / 1024
                    percentage = (resource_config.max_memory_mb / ResourceConfig.get_available_memory_mb()) * 100
                    self.log(f"Memory limit: {resource_config.max_memory_mb} MB ({mem_gb:.1f} GB - {percentage:.0f}% of system RAM)")
                
                self.log(f"Operation mode: {'Preview (List Only)' if preview_mode else 'Recover Files'}")
                
                found = self.controller.start_recovery(
                    disk_path, output, file_types, search_pattern,
                    self.filter_system_var.get(), progress_callback, resource_config, preview_mode
                )
                
                # If preview mode, show results
                if preview_mode:
                    self._display_preview_results()
                
                if self.controller.recovery_service and self.controller.recovery_service.cancelled:
                    # Get preview list to show found files
                    preview_list = self.controller.get_preview_list()
                    
                    if preview_mode:
                        self.log(f"\n⚠️ Preview cancelled by user")
                        self.log(f"📄 Files found before cancellation: {found}")
                        # Display preview results if any files were found
                        if found > 0 and preview_list:
                            self._display_preview_results()
                            self.results_notebook.select(1)  # Switch to preview tab
                            messagebox.showinfo("Cancelled", 
                                              f"Preview was cancelled.\n{found} files found before cancellation.\n\n"
                                              f"Check the Preview tab to see the list of files.")
                        else:
                            messagebox.showinfo("Cancelled", f"Preview was cancelled.\n{found} files found before cancellation.")
                    else:
                        self.log(f"\n⚠️ Recovery cancelled by user")
                        self.log(f"📄 Files found before cancellation: {found}")
                        # Show found files even in recover mode
                        if found > 0 and preview_list:
                            self._setup_preview_tree()  # Ensure preview tree is set up
                            self._display_preview_results()
                            self.results_notebook.select(1)  # Switch to preview tab
                            messagebox.showinfo("Cancelled", 
                                              f"Recovery was cancelled.\n{found} files found before cancellation.\n\n"
                                              f"Check the Preview tab to see the list of files.\n"
                                              f"You can switch to Preview mode to recover them.")
                        else:
                            messagebox.showinfo("Cancelled", f"Recovery was cancelled.\n{found} files found before cancellation.")
                else:
                    if preview_mode:
                        self.log(f"\n✅ Preview completed!")
                        self.log(f"📄 Files found: {found}")
                        messagebox.showinfo("Preview Complete", f"Preview completed!\n{found} files found.\nCheck the Preview tab to see the list.")
                        self.results_notebook.select(1)  # Switch to preview tab
                    else:
                        self.log(f"\n✅ Recovery completed!")
                        self.log(f"📄 Files recovered: {found}")
                        messagebox.showinfo("Success", f"Recovery completed!\n{found} files recovered.")
                
            except Exception as e:
                if "cancelled" in str(e).lower() or (self.controller.recovery_service and self.controller.recovery_service.cancelled):
                    self.log(f"\n⚠️ Recovery cancelled")
                    # If in preview mode and files were found, show them
                    if preview_mode and self.controller.recovery_service:
                        preview_list = self.controller.get_preview_list()
                        if preview_list:
                            self.log(f"📋 Showing {len(preview_list)} files found...")
                            self._display_preview_results()
                            self.results_notebook.select(1)  # Switch to preview tab
                            messagebox.showinfo("Cancelled", 
                                              f"Recovery was cancelled.\n{len(preview_list)} files found.\n\n"
                                              f"Check the Preview tab to see the list of files.")
                        else:
                            messagebox.showinfo("Cancelled", "Recovery was cancelled.")
                    else:
                        messagebox.showinfo("Cancelled", "Recovery was cancelled.")
                else:
                    self.log(f"\n❌ Error: {e}")
                    messagebox.showerror("Error", f"Recovery failed:\n{e}")
            finally:
                # Stop progressbar immediately in main thread
                def cleanup_ui():
                    self.is_scanning = False
                    self.start_button.config(state=tk.NORMAL, text="Start")
                    self.stop_button.config(state=tk.DISABLED)
                    try:
                        if self.progress_bar['mode'] == 'indeterminate':
                            self.progress_bar.stop()
                        self.progress_bar['value'] = 0
                    except:
                        pass
                    self.progress_var.set("Ready")
                    self.progress_percent_var.set("0%")
                
                # Execute in main thread
                self.root.after(0, cleanup_ui)
        
        self.recovery_thread = threading.Thread(target=recovery_thread, daemon=True)
        self.recovery_thread.start()
    
    def _setup_preview_tree(self):
        """Sets up the preview tree view with selection checkboxes"""
        # Clear existing tree if any
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = ttk.Frame(self.preview_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button frame for actions
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="✓ Select All", 
                  command=self._select_all_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="✗ Deselect All", 
                  command=self._deselect_all_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="💾 Recover Selected", 
                  command=self._recover_selected_files).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.preview_status_var = tk.StringVar(value="0 files selected")
        ttk.Label(button_frame, textvariable=self.preview_status_var).pack(side=tk.RIGHT, padx=5)
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(main_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview with checkbox column
        self.preview_tree = ttk.Treeview(tree_frame, columns=('Select', 'Type', 'Size', 'Original Name', 'Position'), 
                                        show='tree headings', yscrollcommand=v_scrollbar.set,
                                        xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.config(command=self.preview_tree.yview)
        h_scrollbar.config(command=self.preview_tree.xview)
        
        # Configure columns
        self.preview_tree.heading('#0', text='#')
        self.preview_tree.heading('Select', text='✓')
        self.preview_tree.heading('Type', text='Type')
        self.preview_tree.heading('Size', text='Size')
        self.preview_tree.heading('Original Name', text='Original Name')
        self.preview_tree.heading('Position', text='Position (bytes)')
        
        self.preview_tree.column('#0', width=50, minwidth=50)
        self.preview_tree.column('Select', width=50, minwidth=50)
        self.preview_tree.column('Type', width=80, minwidth=80)
        self.preview_tree.column('Size', width=100, minwidth=100)
        self.preview_tree.column('Original Name', width=250, minwidth=150)
        self.preview_tree.column('Position', width=150, minwidth=100)
        
        # Bind click event to toggle selection
        self.preview_tree.bind('<Button-1>', self._on_preview_click)
        
        # Pack
        self.preview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Clear file data
        self.preview_file_data = {}
    
    def _display_preview_results(self):
        """Displays preview results in the tree view"""
        if not self.preview_tree:
            self._setup_preview_tree()
        
        # Clear existing items
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Clear file data
        self.preview_file_data = {}
        
        # Get preview list
        preview_list = self.controller.get_preview_list()
        
        # Populate tree
        for idx, file_info in enumerate(preview_list, 1):
            size_kb = file_info['size'] / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            
            item_id = self.preview_tree.insert('', tk.END, text=str(idx),
                                    values=(
                                        '☐',  # Unchecked checkbox
                                        file_info['type'].upper(),
                                        size_str,
                                        file_info['original_name'] or file_info['filename'],
                                        f"{file_info['position']:,}"
                                    ))
            
            # Store file data for recovery
            self.preview_file_data[item_id] = file_info
        
        # Update status
        self._update_preview_status()
        
        self.log(f"Preview: {len(preview_list)} files listed in Preview tab")
    
    def _on_preview_click(self, event):
        """Handles click on preview tree to toggle selection"""
        region = self.preview_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.preview_tree.identify_column(event.x, event.y)
            item = self.preview_tree.identify_row(event.y)
            
            # If clicked on Select column (column #1)
            if column == '#1' and item:
                current_values = list(self.preview_tree.item(item, 'values'))
                if current_values[0] == '☐':
                    current_values[0] = '☑'
                else:
                    current_values[0] = '☐'
                self.preview_tree.item(item, values=tuple(current_values))
                self._update_preview_status()
    
    def _select_all_preview(self):
        """Selects all files in preview"""
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, 'values'))
            values[0] = '☑'
            self.preview_tree.item(item, values=tuple(values))
        self._update_preview_status()
    
    def _deselect_all_preview(self):
        """Deselects all files in preview"""
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, 'values'))
            values[0] = '☐'
            self.preview_tree.item(item, values=tuple(values))
        self._update_preview_status()
    
    def _update_preview_status(self):
        """Updates the preview status label"""
        selected = 0
        total = 0
        for item in self.preview_tree.get_children():
            total += 1
            values = self.preview_tree.item(item, 'values')
            if values and values[0] == '☑':
                selected += 1
        self.preview_status_var.set(f"{selected} of {total} files selected")
    
    def _recover_selected_files(self):
        """Recovers only the selected files from preview"""
        # Get selected files
        selected_files = []
        for item in self.preview_tree.get_children():
            values = self.preview_tree.item(item, 'values')
            if values and values[0] == '☑' and item in self.preview_file_data:
                selected_files.append(self.preview_file_data[item])
        
        if not selected_files:
            messagebox.showwarning("Warning", "Please select at least one file to recover.")
            return
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select directory to save recovered files")
        if not output_dir:
            return
        
        # Confirm recovery
        if not messagebox.askyesno("Confirm", f"Recover {len(selected_files)} selected file(s)?"):
            return
        
        # Recover selected files
        self._recover_files_from_list(selected_files, output_dir)
    
    def _recover_files_from_list(self, file_list, output_dir):
        """Recovers files from a list of file info"""
        recovered = 0
        errors = 0
        
        self.log(f"\n💾 Starting recovery of {len(file_list)} file(s)...")
        self.log(f"📁 Output directory: {output_dir}")
        
        # Get the original disk path
        if not hasattr(self, 'last_disk_path'):
            messagebox.showerror("Error", "Cannot determine source disk. Please start a scan first.")
            return
        
        disk_path = self.last_disk_path
        
        try:
            with open(disk_path, "rb") as disk:
                for idx, file_info in enumerate(file_list, 1):
                    try:
                        # Seek to file position
                        disk.seek(file_info['position'])
                        
                        # Read file data (estimate size, read up to reasonable limit)
                        # For text files, read up to 1MB or until non-text
                        max_read = min(file_info['size'], 1024 * 1024)
                        data = disk.read(max_read)
                        
                        if not data:
                            continue
                        
                        # Detect encoding and decode
                        encoding, text = detect_encoding(data)
                        
                        if not text:
                            continue
                        
                        # Get filename
                        filename = file_info.get('original_name') or file_info.get('filename', 'recovered_file')
                        clean_name = clean_filename(filename)
                        if not clean_name:
                            clean_name = f"recovered_{recovered:05d}.{file_info.get('type', 'txt')}"
                        
                        # Ensure extension
                        if '.' not in clean_name:
                            clean_name += f".{file_info.get('type', 'txt')}"
                        
                        # Save file
                        base_path = os.path.join(output_dir, clean_name)
                        counter = 1
                        while os.path.exists(base_path):
                            name_base, ext = os.path.splitext(clean_name)
                            base_path = os.path.join(output_dir, f"{name_base}_{counter}{ext}")
                            counter += 1
                        
                        with open(base_path, "w", encoding="utf-8") as f:
                            f.write(text)
                        
                        recovered += 1
                        self.log(f"  [{idx}/{len(file_list)}] ✓ Recovered: {os.path.basename(base_path)}")
                        
                    except Exception as e:
                        errors += 1
                        self.log(f"  [{idx}/{len(file_list)}] ✗ Error recovering {file_info.get('filename', 'file')}: {e}")
        
        except PermissionError:
            messagebox.showerror("Error", "PERMISSION DENIED. Run as ADMINISTRATOR.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error accessing disk:\n{e}")
            return
        
        # Show results
        messagebox.showinfo("Recovery Completed", 
                          f"Recovery completed.\n\n"
                          f"✓ Files recovered: {recovered}\n"
                          f"✗ Errors: {errors}\n\n"
                          f"Location: {output_dir}")
        self.log(f"\n✅ Recovery completed: {recovered} file(s) recovered, {errors} error(s)")
    
    def stop_recovery(self):
        """Stops the recovery process"""
        if not self.is_scanning:
            return
        
        if messagebox.askyesno("Confirm Stop", "Are you sure you want to stop the recovery process?"):
            if self.controller.recovery_service:
                self.controller.recovery_service.cancel()
                self.log("⏹️ Stop requested. Waiting for current block to finish...")
                self.stop_button.config(state=tk.DISABLED)
                
                # Stop progressbar immediately - try direct stop first, then schedule in main thread
                try:
                    if self.progress_bar['mode'] == 'indeterminate':
                        self.progress_bar.stop()
                    self.progress_bar['value'] = 0
                    self.progress_var.set("Stopping...")
                    self.progress_percent_var.set("Stopping...")
                except:
                    pass
                
                # Also schedule in main thread to ensure it stops
                def stop_progressbar():
                    try:
                        if self.progress_bar['mode'] == 'indeterminate':
                            self.progress_bar.stop()
                        self.progress_bar['value'] = 0
                        self.progress_var.set("Stopping...")
                        self.progress_percent_var.set("Stopping...")
                    except:
                        pass
                
                self.root.after(0, stop_progressbar)
                
                # Wait for thread to finish and then show results (both preview and recover modes)
                def check_and_show_preview():
                    # Wait for recovery thread to finish (with timeout)
                    import time
                    max_wait = 5  # Maximum 5 seconds wait
                    waited = 0
                    while self.recovery_thread and self.recovery_thread.is_alive() and waited < max_wait:
                        time.sleep(0.1)
                        waited += 0.1
                    
                    # Check if there are preview results to show
                    if self.controller.recovery_service:
                        preview_list = self.controller.get_preview_list()
                        if preview_list:
                            # Schedule UI update in main thread
                            def show_preview():
                                self.log(f"📋 Showing {len(preview_list)} files found before stopping...")
                                # Ensure preview tree is set up
                                if not self.preview_tree:
                                    self._setup_preview_tree()
                                self._display_preview_results()
                                self.results_notebook.select(1)  # Switch to preview tab
                                self.log("✅ Files listed in Preview tab")
                            
                            self.root.after(0, show_preview)
                
                # Schedule preview display in background thread (for both modes)
                threading.Thread(target=check_and_show_preview, daemon=True).start()
    
    def run(self):
        """Runs the GUI"""
        self.root.mainloop()

