import os
import tkinter as tk
from tkinter import messagebox
from tkinter import StringVar
import customtkinter as ctk
import core

RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

class SavePlaylistDialog(ctk.CTkToplevel):
    def __init__(self, parent, playlist : core.Playlist):
        super().__init__(parent)

        self.parent = parent
        self.playlist = playlist

        self.title("Save Playlist")
        self.geometry("350x140")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Title
        title_label = ctk.CTkLabel(self, text="Save Playlist", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(15, 10))

        # Name row
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(name_frame, text="Name:").pack(side="left")

        self.name_string = StringVar(value="")  # Name string
        self.name_string.trace_add("write", self.validate_name_entry)  # Make any changes to name string call a validation method

        self.name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_string)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.name_string.set(self.playlist.name)
        self.name_entry.focus()
        self.name_entry.select_range(0, "end")

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Save", width=90, command=self.save_playlist).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", width=90, command=self.destroy).pack(side="left", padx=5)

        # Center over parent
        self.update_idletasks()

        x = (parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2)
        y = (parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2)

        self.geometry(f"+{x}+{y}")

        self.after(100, self.focus_name_entry)

    def focus_name_entry(self):
        self.name_entry.focus_set()
        self.name_entry.select_range(0, "end")
        self.name_entry.icursor("end")

    def validate_name_entry(self, *args):
        """Validates the playlist name entry to ensure it only contains valid characters and is not too long."""
        entry = self.name_string.get()

        # Remove any invalid characters and length to 40 characters
        entry = ''.join(c for c in entry if c.isalnum() or c.isspace() or c in ('-', '_', '.', '(', ')', "'", '&'))[:40]

        if entry != self.name_string.get():
            self.name_string.set(entry)

    def save_playlist(self):
        """Handles the logic for saving the playlist, including checking for reserved names and confirming overwrites."""
        name = self.name_string.get().strip()
        name = " ".join(name.split())

        if name.upper() in RESERVED_NAMES:
            name = f"{name}_playlist"

        if not name:
            name = "Untitled"

        filepath = os.path.join("playlists", f"{name}.json")
        if os.path.exists(filepath):
            overwrite = messagebox.askyesno(
                "Overwrite Playlist",
                f'"{name}" already exists.\n\nOverwrite it?'
            )

            if not overwrite:
                return
        
        self.finish_save(name, filepath)
        
    def finish_save(self, name, filepath):
        """Finalizes the save operation after confirming overwrite if necessary."""
        self.playlist.name = name
        self.playlist.save(filepath)

        self.parent.set_playlist_name(name)
        self.destroy()

class LoadPlaylistDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        self.title("Load Playlist")
        self.geometry("400x500")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()

        x = (parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2)
        y = (parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2)

        self.geometry(f"+{x}+{y}")

