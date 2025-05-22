import sys
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import signal
import shutil
import os
import piexif


def printExif(file):
    try:
        img = Image.open(file)
        data = img._getexif()
        if data is not None:
            print(f"EXIF data for {file}:")
            for tag, value in data.items():
                tag_name = TAGS.get(tag, tag)
                print(f"{tag_name}: {value}")
        else:
            print(f"No EXIF data found for {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")


def backup_file(file_path):
    """Create a backup of the file before modification"""
    backup_path = file_path + '.backup'
    shutil.copy2(file_path, backup_path)
    return backup_path


def restore_backup(file_path):
    """Restore from backup if something goes wrong"""
    backup_path = file_path + '.backup'
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        os.remove(backup_path)


def modify_metadata(file_path, tag_to_modify, new_value):
    try:
        # Create backup before modification
        backup_path = backup_file(file_path)
        
        try:
            # Load existing EXIF data
            exif_dict = piexif.load(file_path)
            
            # Find the tag ID from the tag name
            tag_id = None
            for tag, name in TAGS.items():
                if name == tag_to_modify:
                    tag_id = tag
                    break
                    
            if tag_id is None:
                raise ValueError(f"Tag {tag_to_modify} not found")
            
            # Special handling for GPS data
            if tag_to_modify == 'GPSInfo':
                try:
                    # Parse the GPS string into components
                    # Expected format: "N 45 51 22.39632 E 6 37 7.43052 1167.0"
                    parts = new_value.split()
                    if len(parts) != 9:
                        raise ValueError("GPS data must be in format: 'N 45 51 22.39632 E 6 37 7.43052 1167.0'")
                    
                    # Convert to proper GPS format
                    gps_info = {
                        1: parts[0].encode('utf-8'),  # N/S
                        2: (float(parts[1]), float(parts[2]), float(parts[3])),  # Latitude
                        3: parts[4].encode('utf-8'),  # E/W
                        4: (float(parts[5]), float(parts[6]), float(parts[7])),  # Longitude
                        5: b'\x00',  # Altitude reference
                        6: float(parts[8])  # Altitude
                    }
                    new_value = gps_info
                except Exception as e:
                    raise ValueError(f"Invalid GPS format: {e}")
            # Convert the new value to the appropriate type
            elif tag_to_modify in ['Make', 'Model', 'Software', 'DateTime', 
                               'DateTimeOriginal', 'DateTimeDigitized']:
                # These fields should be bytes
                new_value = new_value.encode('utf-8')
            elif tag_to_modify in ['FNumber', 'ApertureValue', 'MaxApertureValue', 
                                 'ExposureTime', 'ShutterSpeedValue', 'BrightnessValue',
                                 'ExposureBiasValue', 'FocalLength', 'DigitalZoomRatio']:
                # These fields should be rational numbers (tuples)
                try:
                    # Convert to float first
                    float_val = float(new_value)
                    # Convert to rational (numerator, denominator)
                    # For FNumber, multiply by 100 to preserve 2 decimal places
                    if tag_to_modify == 'FNumber':
                        new_value = (int(float_val * 100), 100)
                    else:
                        new_value = (int(float_val * 1000), 1000)
                except ValueError:
                    raise ValueError(f"Invalid number format for {tag_to_modify}")
            elif isinstance(new_value, str):
                try:
                    # Try to convert to int or float if possible
                    if '.' in new_value:
                        new_value = float(new_value)
                    else:
                        new_value = int(new_value)
                except ValueError:
                    # If conversion fails, keep as string
                    new_value = new_value.encode('utf-8')
            
            # Modify the metadata in the appropriate section
            if tag_id in piexif.TAGS["0th"]:
                exif_dict["0th"][tag_id] = new_value
            elif tag_id in piexif.TAGS["Exif"]:
                exif_dict["Exif"][tag_id] = new_value
            elif tag_id in piexif.TAGS["GPS"]:
                exif_dict["GPS"][tag_id] = new_value
            elif tag_id in piexif.TAGS["1st"]:
                exif_dict["1st"][tag_id] = new_value
            
            # Save the modified EXIF data
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file_path)
            
            return True
        except Exception as e:
            # If anything goes wrong, restore from backup
            restore_backup(file_path)
            raise e
        finally:
            # Clean up backup file if everything went well
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
    except Exception as e:
        print(f"Error modifying metadata: {e}")
        return False


def delete_metadata(file_path):
    try:
        # Create backup before deletion
        backup_path = backup_file(file_path)
        
        try:
            # Remove all EXIF data
            piexif.remove(file_path)
            return True
        except Exception as e:
            # If anything goes wrong, restore from backup
            restore_backup(file_path)
            raise e
        finally:
            # Clean up backup file if everything went well
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
    except Exception as e:
        print(f"Error deleting metadata: {e}")
        return False


class MetadataGUI:
    def __init__(self, root, initial_file=None):
        self.root = root
        self.root.title("Scorpion - Metadata Manager")
        self.root.geometry("800x600")
        
        # Set up cleanup handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        ttk.Label(self.main_frame, text="Select Image:").grid(row=0, column=0, sticky=tk.W)
        self.file_path = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        # Metadata display
        ttk.Label(self.main_frame, text="Metadata:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.metadata_text = tk.Text(self.main_frame, height=15, width=70)
        self.metadata_text.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Modification frame
        mod_frame = ttk.LabelFrame(self.main_frame, text="Modify Metadata", padding="5")
        mod_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(mod_frame, text="Tag:").grid(row=0, column=0, padx=5)
        self.tag_entry = ttk.Entry(mod_frame, width=30)
        self.tag_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(mod_frame, text="New Value:").grid(row=0, column=2, padx=5)
        self.value_entry = ttk.Entry(mod_frame, width=30)
        self.value_entry.grid(row=0, column=3, padx=5)
        
        # Buttons
        ttk.Button(mod_frame, text="Modify", command=self.modify_metadata).grid(row=0, column=4, padx=5)
        ttk.Button(mod_frame, text="Delete All Metadata", command=self.delete_metadata).grid(row=0, column=5, padx=5)
        
        # Load button
        ttk.Button(self.main_frame, text="Load Metadata", command=self.load_metadata).grid(row=4, column=0, columnspan=3, pady=10)
        
        # Load initial file if provided
        if initial_file:
            self.file_path.set(initial_file)
            self.load_metadata()
        
    def on_closing(self):
        """Handle window closing"""
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        self.on_closing()
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        if filename:
            self.file_path.set(filename)
            self.load_metadata()
    
    def load_metadata(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file first!")
            return
            
        self.metadata_text.delete(1.0, tk.END)
        try:
            img = Image.open(file_path)
            data = img._getexif()
            if data is not None:
                for tag, value in data.items():
                    tag_name = TAGS.get(tag, tag)
                    self.metadata_text.insert(tk.END, f"{tag_name}: {value}\n")
            else:
                self.metadata_text.insert(tk.END, "No EXIF data found")
        except Exception as e:
            self.metadata_text.insert(tk.END, f"Error: {str(e)}")
    
    def modify_metadata(self):
        file_path = self.file_path.get()
        tag = self.tag_entry.get()
        value = self.value_entry.get()
        
        if not all([file_path, tag, value]):
            messagebox.showwarning("Warning", "Please fill in all fields!")
            return
            
        if modify_metadata(file_path, tag, value):
            messagebox.showinfo("Success", "Metadata modified successfully!")
            self.load_metadata()
        else:
            messagebox.showerror("Error", "Failed to modify metadata")
    
    def delete_metadata(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file first!")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all metadata?"):
            if delete_metadata(file_path):
                messagebox.showinfo("Success", "Metadata deleted successfully!")
                self.load_metadata()
            else:
                messagebox.showerror("Error", "Failed to delete metadata")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # Command line interface
        try:
            if len(sys.argv) >= 2:
                for file in sys.argv[2:]:
                    printExif(file)
                    print('************************************')
            else:
                print("Add a path! EXAMPLE: python scorpion.py --cli ../img/animal.jpg")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Graphical interface
        root = tk.Tk()
        initial_file = sys.argv[1] if len(sys.argv) > 1 else None
        app = MetadataGUI(root, initial_file)
        root.mainloop()


if __name__ == "__main__":
    main()
