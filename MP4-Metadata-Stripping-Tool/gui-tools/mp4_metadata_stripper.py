#!/usr/bin/env python3
"""
MP4 Metadata Stripper - A GNOME-compatible GUI tool for stripping metadata from MP4 files
"""

import os
import sys
import subprocess
import gi

# Auto-detect DISPLAY variable if not set
if 'DISPLAY' not in os.environ:
    import glob
    x_sockets = glob.glob('/tmp/.X11-unix/X*')
    for socket in sorted(x_sockets):
        try:
            num = socket.split('X')[1] if 'X' in socket else None
            if num and num.isdigit():
                os.environ['DISPLAY'] = f':{num}'
                break
        except:
            continue
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class MP4MetadataStripper(Gtk.Window):
    def __init__(self):
        super().__init__(title="MP4 Metadata Stripper")
        
        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)
        
        # Main vertical box layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Title label
        title_label = Gtk.Label(label="<b>MP4 Metadata Stripper</b>", use_markup=True)
        title_label.set_markup("<b>MP4 Metadata Stripper</b>")
        main_box.pack_start(title_label, False, False, padding=10)
        
        # Browse frame
        browse_frame = Gtk.Frame(label="Browse Files/Directories")
        browse_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        browse_frame.add(browse_box)
        main_box.pack_start(browse_frame, False, False, padding=10)
        
        # Browse button (renamed to "Select Directory" for clarity)
        self.browse_btn = Gtk.Button(label="📁 Select Directory")
        self.browse_btn.connect("clicked", self.on_browse_clicked)
        browse_box.pack_start(self.browse_btn, False, False, padding=5)
        
        # Add directory button (renamed to "Select Another" for consistency)
        self.add_dir_btn = Gtk.Button(label="+ Select Another")
        self.add_dir_btn.connect("clicked", self.on_add_directory_clicked)
        browse_box.pack_start(self.add_dir_btn, False, False, padding=5)
        
        # File list frame
        list_frame = Gtk.Frame(label="Selected Files (MP4)")
        main_box.pack_start(list_frame, True, True, padding=10)
        
        self.file_store = Gtk.ListStore(str, str, bool)  # path, filename, selected
        
        self.file_tree = Gtk.TreeView(model=self.file_store)
        file_col = Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=0)
        select_cell = Gtk.CellRendererToggle()
        select_cell.connect("toggled", self.on_file_toggled)
        col_select = Gtk.TreeViewColumn("Select", select_cell, active=2)
        
        self.file_tree.append_column(file_col)
        self.file_tree.append_column(col_select)
        
        # Scrollable list view
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(300)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.file_tree)
        list_frame.add(scroll)
        
        # Progress frame
        progress_frame = Gtk.Frame(label="Progress")
        main_box.pack_start(progress_frame, False, False, padding=10)
        
        self.progress_bar = Gtk.ProgressBar()
        progress_frame.add(self.progress_bar)
        
        # Status label (using a Label in the box directly for reliable access)
        self.status_label = Gtk.Label(label="Ready")
        main_box.pack_start(self.status_label, False, False, padding=5)
        
        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(btn_box, False, False, padding=10)
        
        self.strip_btn = Gtk.Button(label="✂️ Strip Metadata")
        self.strip_btn.connect("clicked", self.on_strip_clicked)
        btn_box.pack_start(self.strip_btn, False, False, padding=5)
        
        # Select All button (new!)
        self.select_all_btn = Gtk.Button(label="☑ Select All")
        self.select_all_btn.connect("clicked", self.on_select_all_clicked)
        btn_box.pack_start(self.select_all_btn, False, False, padding=5)
        
        self.reset_btn = Gtk.Button(label="🔄 Reset")
        self.reset_btn.connect("clicked", self.on_reset_clicked)
        btn_box.pack_start(self.reset_btn, False, False, padding=5)
        
        # Check for required tools
        if not self.check_dependencies():
            import warnings
            print("Warning: Some dependencies may be missing. Install with:")
            print("  sudo apt install ffmpeg exiftool")
    
    def check_dependencies(self):
        """Check if required tools are available"""
        try:
            subprocess.run(['which', 'ffmpeg'], capture_output=True, check=True)
            return True
        except:
            import warnings
            return False
    
    def on_browse_clicked(self, button):
        """Open directory picker dialog to browse for MP4 files."""
        GLib.timeout_add(10, self.open_directory_picker, "Select Directory")
    
    def on_add_directory_clicked(self, button):
        """Open directory picker to add another directory."""
        GLib.timeout_add(10, self.open_directory_picker, "Select Another Folder")
    
    def open_directory_picker(self, title):
        """Show file chooser dialog using the most reliable GTK pattern."""
        
        # Create the dialog - use standard FileChooserDialog for better compatibility
        dialog = Gtk.FileChooserDialog(
            title=title,
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        # Add our custom buttons
        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Select", Gtk.ResponseType.OK)
        
        # Make modal - blocks interaction with main window until dialog closed
        dialog.set_modal(True)
        
        # Ensure dialog shows on top of main window
        dialog.set_transient_for(self)
        
        def on_response(dialog, response):
            """Handle user response - called automatically by GTK."""
            if response == Gtk.ResponseType.OK:
                path = dialog.get_filename()
                self.add_directory(path)
            
            # Destroy the dialog to clean up resources
            dialog.destroy()
        
        # Connect the response signal BEFORE running
        dialog.connect("response", on_response)
        
        # Make sure dialog is shown before we block on run()
        dialog.show_all()
        
        # Small timeout to allow window manager to show the dialog first
        GLib.timeout_add(20, lambda: None)
        
        # Run the dialog - this blocks until user responds and shows the window
        result = dialog.run()
        
        # Dialog should be destroyed by now, but ensure cleanup
        if 'dialog' in locals():
            try:
                dialog.hide()
                dialog.destroy()
            except:
                pass
        
        return False  # Don't run this again
    
    def add_directory(self, directory_path):
        """Scan and add MP4 files from a directory"""
        if not os.path.isdir(directory_path):
            return
        
        count = 0
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.mp4'):
                    full_path = os.path.join(root, file)
                    # Check if already exists
                    existing = False
                    for row in self.file_store:
                        if row[0] == full_path:
                            existing = True
                            break
                    if not existing:
                        # UNCHECKED by default - user must check what they want to process
                        self.file_store.append([full_path, file, False])
                        count += 1
        
        if count > 0:
            self.status_label.set_text(f"Added {count} MP4 file(s) from {directory_path}")

    def on_file_toggled(self, cell, path):
        """Toggle selection of a file"""
        iter = self.file_store.get_iter(path)
        self.file_store[iter][2] = not self.file_store[iter][2]
    
    def on_select_all_clicked(self, button):
        """Select all files in the list"""
        for row in self.file_store:
            row[2] = True  # Set selected to True for all rows
        
        count = len(list(self.file_store))
        self.status_label.set_text(f"Selected {count} file(s)")
    
    def on_strip_clicked(self, button):
        selected_files = []
        for row in self.file_store:
            if row[2]:  # If selected
                selected_files.append(row[0])
        
        if not selected_files:
            import warnings
            print("No files selected!")
            return
        
        total = len(selected_files)
        success = 0
        failed = 0
        
        for i, filepath in enumerate(selected_files):
            self.progress_bar.set_fraction(i / total)
            
            if self.strip_metadata(filepath):
                success += 1
            else:
                failed += 1
        
        self.status_label.set_text(f"Completed! Success: {success}, Failed: {failed}")
    
    def strip_metadata(self, filepath):
        """Strip metadata from MP4 file using ffmpeg"""
        try:
            # Create output path
            output_path = os.path.join(
                os.path.dirname(filepath), 
                "stripped_" + os.path.basename(filepath)
            )
            
            # Use ffmpeg to create a clean copy without metadata
            cmd = [
                'ffmpeg', '-y',  # Overwrite existing files
                '-i', filepath,
                '-c:v', 'copy',     # Copy video stream (no re-encoding)
                '-c:a', 'copy',     # Copy audio stream (if present)
                '-map_metadata', '-1',  # Strip all metadata
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"Error processing {filepath}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"Timeout processing {filepath}")
            return False
        except Exception as e:
            print(f"Exception processing {filepath}: {str(e)}")
            return False
    
    def on_reset_clicked(self, button):
        """Reset the application"""
        self.file_store.clear()
        self.progress_bar.set_fraction(0.0)
        self.status_label.set_text("Ready")


def main():
    app = MP4MetadataStripper()
    app.show_all()
    
    # Set default icon if available
    try:
        app.set_icon_from_file('/usr/share/icons/hicolor/256x256/apps/mp4-metadata-stripper.svg')
    except:
        pass
    
    print(f"Application started with DISPLAY={os.environ.get('DISPLAY')}")
    Gtk.main()

if __name__ == "__main__":
    main()
