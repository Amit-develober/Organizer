import os
import shutil
import json
import mimetypes
import time
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Initialize mimetypes and add a few missing common ones if needed
mimetypes.init()
mimetypes.add_type('image/webp', '.webp')

# Define categories based on mime types
CATEGORIES = {
    'Images': ['image/'],
    'Videos': ['video/'],
    'Audio': ['audio/'],
    'Documents': [
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument', 
        'text/plain', 'application/vnd.ms-excel', 
        'application/vnd.ms-powerpoint', 'application/rtf',
        'application/csv', 'text/csv'
    ],
    'Archives': [
        'application/zip', 'application/x-tar', 
        'application/gzip', 'application/x-rar', 
        'application/x-7z', 'application/x-bzip2',
        'application/java-archive'
    ],
    'Code': [
        'text/x-python', 'text/html', 'text/css', 
        'application/javascript', 'text/javascript', 
        'application/json', 'text/xml', 'text/x-c',
        'text/x-java', 'application/x-sh', 'text/markdown'
    ]
}

# Prefixes for the auto-renaming feature
PREFIXES = {
    'Images': 'photo',
    'Videos': 'video',
    'Audio': 'audio',
    'Documents': 'doc',
    'Archives': 'archive',
    'Code': 'code',
    'Other': 'misc',
    'All_Files': 'file'
}

def get_category(mime_type):
    """Detects the category of a file based on its mime type."""
    if not mime_type:
        return 'Other'
    for category, identifiers in CATEGORIES.items():
        for identifier in identifiers:
            if mime_type.startswith(identifier):
                return category
    return 'Other'

class FileSortrApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup main window
        self.title("FileSortr")
        self.geometry("900x750")
        self.minsize(850, 700)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A") # Slate 900

        self.selected_folder = None
        self.log_file = "fileSortr_log.json"

        self.setup_ui()

    def setup_ui(self):
        """Initializes the customtkinter GUI elements."""
        
        # Configure fonts
        self.title_font = ctk.CTkFont(family="Inter", size=26, weight="bold")
        self.subtitle_font = ctk.CTkFont(family="Inter", size=13)
        self.header_font = ctk.CTkFont(family="Inter", size=14, weight="bold")
        self.body_font = ctk.CTkFont(family="Inter", size=13)
        self.code_font = ctk.CTkFont(family="Consolas", size=11)

        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=30, pady=25)

        # --- Header ---
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="✨ FileSortr", font=self.title_font, text_color="#818CF8")
        self.title_lbl.pack(anchor="w")
        
        self.subtitle_lbl = ctk.CTkLabel(self.header_frame, text="Keep your directory clean and organized automatically.", font=self.subtitle_font, text_color="#94A3B8")
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # --- Card 1: Folder Selection ---
        self.folder_card = ctk.CTkFrame(self.main_container, fg_color="#1E293B", border_color="#334155", border_width=1, corner_radius=12)
        self.folder_card.pack(fill="x", pady=(0, 15), ipady=10)
        
        self.folder_header = ctk.CTkLabel(self.folder_card, text="📁 Source Folder", font=self.header_font, text_color="#F8FAFC")
        self.folder_header.pack(anchor="w", padx=20, pady=(15, 10))

        self.folder_select_frame = ctk.CTkFrame(self.folder_card, fg_color="transparent")
        self.folder_select_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.btn_select = ctk.CTkButton(
            self.folder_select_frame, 
            text="Choose Folder...", 
            font=self.body_font,
            fg_color="#4F46E5", 
            hover_color="#4338CA", 
            command=self.select_folder,
            height=36,
            corner_radius=8
        )
        self.btn_select.pack(side="left", padx=(0, 15))

        self.lbl_folder = ctk.CTkLabel(
            self.folder_select_frame, 
            text="No folder selected", 
            font=self.body_font,
            text_color="#64748B",
            anchor="w"
        )
        self.lbl_folder.pack(side="left", fill="x", expand=True)

        # --- Card 2: Settings & Switches ---
        self.settings_card = ctk.CTkFrame(self.main_container, fg_color="#1E293B", border_color="#334155", border_width=1, corner_radius=12)
        self.settings_card.pack(fill="x", pady=(0, 15), ipady=10)

        self.settings_header = ctk.CTkLabel(self.settings_card, text="⚙️ Organization Rules", font=self.header_font, text_color="#F8FAFC")
        self.settings_header.pack(anchor="w", padx=20, pady=(15, 10))

        # We can use a grid layout for settings to make it look clean
        self.settings_grid = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        self.settings_grid.pack(fill="x", padx=20, pady=(0, 10))
        self.settings_grid.columnconfigure((0, 1), weight=1, uniform="equal")

        # Variables for settings
        self.sort_type_var = ctk.BooleanVar(value=True)
        self.sort_year_var = ctk.BooleanVar(value=True)
        self.auto_rename_var = ctk.BooleanVar(value=False)
        self.dry_run_var = ctk.BooleanVar(value=True)

        # Styles for switches
        switch_args = {
            "font": self.body_font,
            "text_color": "#E2E8F0",
            "progress_color": "#6366F1",
            "button_color": "#818CF8",
            "button_hover_color": "#4F46E5"
        }

        self.switch_type = ctk.CTkSwitch(self.settings_grid, text="Categorize by File Type (Images, Docs, etc.)", variable=self.sort_type_var, **switch_args)
        self.switch_type.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.switch_year = ctk.CTkSwitch(self.settings_grid, text="Sub-sort by Year (Modified Date)", variable=self.sort_year_var, **switch_args)
        self.switch_year.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        self.switch_rename = ctk.CTkSwitch(self.settings_grid, text="Auto-rename files with type-specific prefixes", variable=self.auto_rename_var, **switch_args)
        self.switch_rename.grid(row=1, column=0, sticky="w", padx=10, pady=10)

        self.switch_dry_run = ctk.CTkSwitch(
            self.settings_grid, 
            text="Dry-run Mode (Preview changes without moving files)", 
            variable=self.dry_run_var, 
            progress_color="#F59E0B",
            button_color="#FBBF24",
            button_hover_color="#D97706",
            font=self.body_font,
            text_color="#E2E8F0"
        )
        self.switch_dry_run.grid(row=1, column=1, sticky="w", padx=10, pady=10)

        # --- Action Bar ---
        self.action_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.action_frame.pack(side="bottom", fill="x", pady=(10, 0))

        self.btn_run = ctk.CTkButton(
            self.action_frame, 
            text="🚀 Run Organizer", 
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#10B981", 
            hover_color="#059669", 
            command=self.run_organizer, 
            height=44,
            corner_radius=8
        )
        self.btn_run.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_undo = ctk.CTkButton(
            self.action_frame, 
            text="⏪ Undo Last Run", 
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#EF4444", 
            hover_color="#DC2626", 
            command=self.undo_last_run, 
            height=44,
            corner_radius=8
        )
        self.btn_undo.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # --- Card 3: Preview Panel ---
        self.preview_card = ctk.CTkFrame(self.main_container, fg_color="#1E293B", border_color="#334155", border_width=1, corner_radius=12)
        self.preview_card.pack(fill="both", expand=True, pady=(0, 10), ipady=10)

        self.preview_header = ctk.CTkLabel(self.preview_card, text="🖥️ Process Console", font=self.header_font, text_color="#F8FAFC")
        self.preview_header.pack(anchor="w", padx=20, pady=(15, 5))

        # Text box style
        self.preview_box = ctk.CTkTextbox(
            self.preview_card, 
            state="disabled", 
            font=self.code_font,
            fg_color="#0F172A", 
            text_color="#38BDF8", # Sky blue console text
            border_color="#334155",
            border_width=1,
            corner_radius=8
        )
        self.preview_box.pack(pady=10, padx=20, fill="both", expand=True)

        # Progress bar integrated neatly at the bottom of preview
        self.progress_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 5))
        
        self.progress = ctk.CTkProgressBar(self.progress_frame, progress_color="#10B981", fg_color="#334155", height=8, corner_radius=4)
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)

    def select_folder(self):
        """Opens a dialog for the user to select the target directory."""
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder = Path(folder).resolve()
            self.lbl_folder.configure(text=str(self.selected_folder), text_color="#38BDF8")
            self.log_preview(f"Folder selected: {self.selected_folder}\nReady to run...", append=False)

    def log_preview(self, msg, append=True):
        """Writes text into the preview textbox."""
        self.preview_box.configure(state="normal")
        if not append:
            self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", msg + "\n")
        self.preview_box.see("end")
        self.preview_box.configure(state="disabled")
        self.update_idletasks() # Refresh UI

    def run_organizer(self):
        """Main logical function to scan, rename, and move files based on user settings."""
        if not self.selected_folder:
            messagebox.showwarning("Warning", "Please select a folder first.")
            return

        self.log_preview("Starting scan...", append=False)
        
        # Scan for all files (non-recursive, ignoring the log file)
        files_to_process = [f for f in self.selected_folder.iterdir() if f.is_file() and f.name != self.log_file]
        
        if not files_to_process:
            self.log_preview("No files found to organize.")
            return

        total_files = len(files_to_process)
        self.progress.set(0)
        
        log_data = []
        
        # Initialize counter for auto-renaming
        rename_counters = {cat: 1 for cat in CATEGORIES.keys()}
        rename_counters['Other'] = 1
        rename_counters['All_Files'] = 1

        # Fetch settings from GUI
        dry_run = self.dry_run_var.get()
        sort_type = self.sort_type_var.get()
        sort_year = self.sort_year_var.get()
        auto_rename = self.auto_rename_var.get()

        for idx, file_path in enumerate(files_to_process):
            try:
                # 1. Detect file type using mimetypes
                mime_type, _ = mimetypes.guess_type(str(file_path))
                category = get_category(mime_type) if sort_type else "All_Files"
                
                # 2. Determine year based on last modified date
                year = ""
                if sort_year:
                    mtime = os.path.getmtime(file_path)
                    year = str(datetime.fromtimestamp(mtime).year)
                
                # 3. Determine destination directory
                dest_dir = self.selected_folder
                if sort_type:
                    dest_dir = dest_dir / category
                if sort_year:
                    dest_dir = dest_dir / year
                    
                # 4. Generate new filename if Auto-rename is enabled
                new_name = file_path.name
                if auto_rename:
                    ext = file_path.suffix.lower()
                    prefix = PREFIXES.get(category, 'file')
                    new_name = f"{prefix}_{rename_counters[category]:03d}{ext}"
                    rename_counters[category] += 1
                
                dest_path = dest_dir / new_name

                # 5. Detect duplicate file (same name and size in destination)
                if dest_path.exists() and dest_path != file_path:
                    if dest_path.stat().st_size == file_path.stat().st_size:
                        self.log_preview(f"[SKIP] Duplicate detected: '{file_path.name}' already exists in '{dest_dir.relative_to(self.selected_folder)}'.")
                        continue
                    else:
                        # Filename collision but different size: append a copy number
                        base = dest_path.stem
                        ext = dest_path.suffix
                        copy_num = 1
                        while dest_path.exists():
                            new_name = f"{base}_copy{copy_num}{ext}"
                            dest_path = dest_dir / new_name
                            copy_num += 1

                # Display the preview
                self.log_preview(f"{file_path.name}  -->  {dest_path.relative_to(self.selected_folder)}")

                # 6. Perform the move if not in dry-run mode
                if not dry_run:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.move(str(file_path), str(dest_path))
                        # Log paths for potential Undo operation
                        log_data.append({
                            "original": str(file_path),
                            "new": str(dest_path)
                        })
                    except PermissionError:
                        self.log_preview(f"[ERROR] Permission denied (file in use?): {file_path.name}")
                    except Exception as e:
                        self.log_preview(f"[ERROR] Could not move {file_path.name}: {str(e)}")

            except Exception as e:
                self.log_preview(f"[ERROR] Failed to process {file_path.name}: {str(e)}")
            
            # Update Progress Bar
            self.progress.set((idx + 1) / total_files)

        # 7. Finalize operations
        if not dry_run and log_data:
            log_path = self.selected_folder / self.log_file
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=4)
            self.log_preview(f"\n[DONE] Successfully organized {len(log_data)} files.\nUndo log saved as '{self.log_file}'.")
            
        elif dry_run:
            self.log_preview("\n[DRY RUN COMPLETE] No files were actually moved. Toggle off 'Dry-run Mode' to execute.")

    def undo_last_run(self):
        """Reverses the last organization run using the saved JSON log."""
        if not self.selected_folder:
            messagebox.showwarning("Warning", "Please select a folder first.")
            return
            
        log_path = self.selected_folder / self.log_file
        if not log_path.exists():
            messagebox.showinfo("Info", "No log file found in selected folder. Cannot undo.")
            return
            
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read log file: {str(e)}")
            return
            
        if not log_data:
            self.log_preview("Log is empty. Nothing to undo.", append=False)
            return
            
        self.log_preview("Starting undo process...", append=False)
        self.progress.set(0)
        total = len(log_data)
        
        success_count = 0
        
        # Iterate backwards to avoid path issues
        for idx, entry in enumerate(reversed(log_data)):
            orig_path = Path(entry['original'])
            new_path = Path(entry['new'])
            
            if new_path.exists():
                try:
                    orig_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(new_path), str(orig_path))
                    self.log_preview(f"[UNDO] {new_path.name}  -->  {orig_path.relative_to(self.selected_folder)}")
                    success_count += 1
                except PermissionError:
                    self.log_preview(f"[ERROR] Permission denied: {new_path.name}")
                except Exception as e:
                    self.log_preview(f"[ERROR] Could not restore {new_path.name}: {str(e)}")
            else:
                self.log_preview(f"[WARNING] File not found at destination, skipping: {new_path.name}")
                
            self.progress.set((idx + 1) / total)

        # Clean up any leftover empty directories created during sort
        for entry in log_data:
            new_path = Path(entry['new'])
            try:
                # Remove year directory if empty
                if new_path.parent.exists() and not any(new_path.parent.iterdir()):
                    new_path.parent.rmdir()
                # Remove category directory if empty
                if new_path.parent.parent.exists() and not any(new_path.parent.parent.iterdir()):
                    new_path.parent.parent.rmdir()
            except:
                pass # Silently ignore directory removal errors (e.g. if not empty)
                
        # Delete log file if fully successful
        if success_count == total:
            log_path.unlink(missing_ok=True)
            self.log_preview("\n[DONE] Undo complete. All files have been restored.")
        else:
            self.log_preview(f"\n[PARTIAL] Restored {success_count}/{total} files. Some errors occurred.")


if __name__ == "__main__":
    app = FileSortrApp()
    app.mainloop()
