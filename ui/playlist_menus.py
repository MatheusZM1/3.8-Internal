import os
import tkinter as tk
from tkinter import messagebox
from tkinter import StringVar
import customtkinter as ctk
import core
from . import TrackRow, PlaylistRow

RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

WHITE = "#ffffff"
VERY_LIGHT_GRAY = "#d9d9d9"
LIGHT_GRAY = "#565656"
GRAY = "#2b2b2b"
DARK_GRAY = "#242424"
BLACK = "#000000"
BLUE = "#1a6faf"
HOVER_BLUE = "#145a86"

class SavePlaylistDialog(ctk.CTkToplevel):
    def __init__(self, parent, playlist : core.Playlist, save=True):
        super().__init__(parent)

        self.parent = parent
        self.playlist = playlist
        self.save = save
        self.result = None

        title_text = "Save Playlist" if save else "Rename Playlist"
        self.title(title_text)
        self.geometry("350x140")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Title
        label_text = "Save Playlist" if save else "Rename Playlist"
        title_label = ctk.CTkLabel(self, text=label_text, font=ctk.CTkFont(size=16, weight="bold"))
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

        button_text = "Save" if save else "Rename"
        ctk.CTkButton(button_frame, text=button_text, width=90, command=self.save_playlist).pack(side="left", padx=5)
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
        if os.path.exists(filepath) and self.save:
            overwrite = messagebox.askyesno(
                "Overwrite Playlist",
                f'"{name}" already exists.\n\nOverwrite it?'
            )

            if not overwrite:
                return
        
        self.result = name
        if self.save:
            self.finish_save(name, filepath)
        else:
            self.destroy()
        
    def finish_save(self, name, filepath):
        """Finalizes the save operation after confirming overwrite if necessary."""
        self.playlist.name = name
        self.playlist.save(filepath)

        self.parent.set_playlist_name(name)
        self.destroy()

class ViewPlaylistsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        self.title("All Playlists")
        self.geometry("400x500")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Title
        title_label = ctk.CTkLabel(self, text="All Playlists", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(15, 10))

        # Playlists view
        self.playlists_frame = ctk.CTkScrollableFrame(self, fg_color=GRAY)
        self.playlists_frame.pack(fill="both", expand=True)

        self.selected_playlist_index = None  # Track the selected playlist index

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Load", width=90, command=self.load_playlist).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="View", width=90, command=self.view_playlist).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", width=90, command=self.destroy).pack(side="left", padx=5)

        # Center over parent
        self.update_idletasks()

        x = (parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2)
        y = (parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2)

        self.geometry(f"+{x}+{y}")
        self.setup_playlists_view()

    def setup_playlists_view(self):
        """Sets up the view for displaying available playlists."""
        # Clear existing widgets
        for widget in self.playlists_frame.winfo_children():
            widget.destroy()

        # Load playlists from the "playlists" directory
        playlist_dir = "playlists"
        if not os.path.exists(playlist_dir):
            os.makedirs(playlist_dir)

        playlist_files = [f for f in os.listdir(playlist_dir) if f.endswith(".json")]

        if not playlist_files:
            no_playlists_label = ctk.CTkLabel(self.playlists_frame, text="No playlists found.", font=ctk.CTkFont(size=14))
            no_playlists_label.pack(pady=20)
            return

        for index, filename in enumerate(playlist_files):
            filepath = os.path.join(playlist_dir, filename)
            playlist = core.Playlist.load(filepath)

            if playlist:
                playlist_row = PlaylistRow(self.playlists_frame, index, playlist.name, playlist.population, self.on_playlist_selected, self.handle_playlist_options)
                playlist_row.pack(fill="x", padx=10, pady=5)

    def on_playlist_selected(self, index):
        """Handles the logic when a playlist is selected from the view."""
        self.unhighlight_all_rows()
        self.playlists_frame.winfo_children()[index].set_active(True)
        self.selected_playlist_index = index

    def handle_playlist_options(self, index : int, action : core.PlaylistActions):
        """Routes the contextual menu actions for each playlist.""" 
        self.selected_playlist_index = index
        self.playlists_frame.winfo_children()[index].set_active(True) 
        
        match action:
            case core.PlaylistActions.LOAD:
                self.load_playlist()
            
            case core.PlaylistActions.VIEW:
                self.view_playlist()

            case core.PlaylistActions.RENAME:
                self.rename_playlist()

            case core.PlaylistActions.DELETE:
                self.delete_playlist()

    def unhighlight_all_rows(self):
        """Unhighlights all playlist rows in the view."""
        for widget in self.playlists_frame.winfo_children():
            if isinstance(widget, PlaylistRow):
                widget.set_active(False)

    def load_playlist(self):
        """Loads the selected playlist into the main application."""
        if self.selected_playlist_index is None:
            messagebox.showwarning("No Selection", "Please select a playlist to load.")
            return

        playlist_dir = "playlists"
        playlist_files = [f for f in os.listdir(playlist_dir) if f.endswith(".json")]
        selected_file = playlist_files[self.selected_playlist_index]
        filepath = os.path.join(playlist_dir, selected_file)

        loaded_playlist = core.Playlist.load(filepath)
        if loaded_playlist:
            self.parent.process_playlist(loaded_playlist)
            self.destroy()
        else:
            messagebox.showerror("Load Error", f"Failed to load playlist: {selected_file}")

    def view_playlist(self):
        """Opens a detailed view of the selected playlist."""
        if self.selected_playlist_index is None:
            messagebox.showwarning("No Selection", "Please select a playlist to view.")
            return

        playlist_dir = "playlists"
        playlist_files = [f for f in os.listdir(playlist_dir) if f.endswith(".json")]
        selected_file = playlist_files[self.selected_playlist_index]
        filepath = os.path.join(playlist_dir, selected_file)

        loaded_playlist = core.Playlist.load(filepath)
        if loaded_playlist:
            # Open a new dialog or window to display the playlist details
            PlaylistDetailsDialog(self, loaded_playlist)
        else:
            messagebox.showerror("Load Error", f"Failed to load playlist: {selected_file}")

    def rename_playlist(self):
        """Renames the selected playlist after user input."""
        if self.selected_playlist_index is None:
            messagebox.showwarning("No Selection", "Please select a playlist to rename.")
            return

        playlist_dir = "playlists"
        playlist_files = [f for f in os.listdir(playlist_dir) if f.endswith(".json")]
        selected_file = playlist_files[self.selected_playlist_index]
        filepath = os.path.join(playlist_dir, selected_file)

        loaded_playlist = core.Playlist.load(filepath)
        if not loaded_playlist:
            messagebox.showerror("Load Error", f"Failed to load playlist: {selected_file}")
            return

        # Open the SavePlaylistDialog with the loaded playlist
        dialog = SavePlaylistDialog(self, loaded_playlist, save=False)
        self.wait_window(dialog)

        new_name = dialog.result

        if new_name is None:
            return
        
        old_name = os.path.splitext(selected_file)[0]

        # Nothing to do if the name hasn't changed
        if new_name == old_name:
            return

        new_filepath = os.path.join(playlist_dir, f"{new_name}.json")

        # Ask before overwriting an existing playlist (same name already exists)
        if os.path.exists(new_filepath):
            overwrite = messagebox.askyesno(
                "Overwrite Playlist",
                f'"{new_name}" already exists.\n\nOverwrite it?'
            )

            if not overwrite:
                return

        try:
            loaded_playlist.name = new_name
            loaded_playlist.save(new_filepath)

            if os.path.exists(filepath):
                os.remove(filepath)

        except Exception as e:
            messagebox.showerror("Rename Error", f"Failed to rename playlist:\n{e}")
            return

        self.setup_playlists_view()

    def delete_playlist(self):
        """Deletes the selected playlist after user confirmation."""
        if self.selected_playlist_index is None:
            messagebox.showwarning("No Selection", "Please select a playlist to delete.")
            return

        playlist_dir = "playlists"
        playlist_files = [f for f in os.listdir(playlist_dir) if f.endswith(".json")]
        selected_file = playlist_files[self.selected_playlist_index]
        filepath = os.path.join(playlist_dir, selected_file)

        playlist_file_name = selected_file[:-5]  # Cut .json off for display

        confirm_delete = messagebox.askyesno(
            "Delete Playlist",
            f"Are you sure you want to delete '{playlist_file_name}'?"
        )

        if confirm_delete:
            try:
                os.remove(filepath)
                messagebox.showinfo("Deleted", f"Playlist '{playlist_file_name}' has been deleted.")
                self.setup_playlists_view()  # Refresh the view
                self.selected_playlist_index = None  # Reset selection
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete playlist: {e}")

        self.selected_playlist_index = None

class PlaylistDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, playlist : core.Playlist):
        super().__init__(parent)

        self.parent = parent
        self.playlist = playlist

        self.title(f"Playlist: {playlist.name}")
        self.geometry("400x400")
        self.resizable(False, False)

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Title
        title_label = ctk.CTkLabel(self, text=playlist.name, font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(15, 10))

        # Playlist view
        self.playlist_frame = ctk.CTkScrollableFrame(self, fg_color=GRAY)
        self.playlist_frame.pack(fill="both", expand=True)

        self.playlist_buttons = []

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
        self.setup_playlist_view()

    def setup_playlist_view(self):
        """Sets up the view for displaying available playlists."""
        # Clear existing widgets
        for row in self.playlist_buttons:
            row.destroy()
        self.playlist_buttons.clear()

        # Rebuild the list with TrackRow objects
        for index, song in enumerate(self.playlist.tracks):
            row = TrackRow(
                master=self.playlist_frame,
                index=index,
                title=song["title"],
                artist=song["artist"],
                click_callback=None,
                options_callback=self.handle_track_options,
                drag_callback=self.handle_row_drag,
                drop_callback=self.handle_row_drop,
                view_only=True
            )
            row.pack(fill="x", padx=5, pady=2)
            self.playlist_buttons.append(row)

    def handle_track_options(self, index : int, action : core.TrackActions):
        """Routes the contextual menu actions for each track."""        
        match action:           
            case core.TrackActions.REMOVE_FROM_PLAYLIST:
                pass
            
            case core.TrackActions.OPEN_IN_FOLDER:
                import subprocess
                track_path = self.playlist.tracks[index]["path"]
                safe_path = os.path.normpath(track_path)
                subprocess.Popen(f'explorer /select,"{safe_path}"')

    def handle_row_drag(self, row_widget, y_root):
        """Tracks mouse movement and instantly flips positions with adjacent neighbors."""
        # Determine which bucket we are sorting based on layout parent containers
        current_idx = row_widget.index

        # Check item directly above the moving item
        if current_idx > 0:
            above_row = self.playlist_buttons[current_idx - 1]
            above_center = above_row.winfo_rooty() + (above_row.winfo_height() / 2)
            if y_root < above_center:
                self.swap_rows(row_widget.master, current_idx, current_idx - 1)
                return

        # Check item directly below the moving item
        if current_idx < len(self.playlist_buttons) - 1:
            below_row = self.playlist_buttons[current_idx + 1]
            below_center = below_row.winfo_rooty() + (below_row.winfo_height() / 2)
            if y_root > below_center:
                self.swap_rows(row_widget.master, current_idx, current_idx + 1)
                return

    def swap_rows(self, master_frame, idx1, idx2):
        """Swaps data arrays and handles non-destructive, highly optimized UI adjustments."""

        buttons_list = self.playlist_buttons
        data_list = self.playlist.tracks

        # Keep a direct reference to the two widgets being altered
        moving_row = buttons_list[idx1]
        neighbor_row = buttons_list[idx2]

        # Swap raw data pointers
        data_list[idx1], data_list[idx2] = data_list[idx2], data_list[idx1]
        # Swap visual component array tracking addresses
        buttons_list[idx1], buttons_list[idx2] = buttons_list[idx2], buttons_list[idx1]

        # Explicitly update indices for only the two affected rows
        moving_row.index = idx2
        neighbor_row.index = idx1

        # Update text labels for only the two affected rows
        moving_row.index_label.configure(text=f"{idx2 + 1}")
        neighbor_row.index_label.configure(text=f"{idx1 + 1}")
        moving_row.index_label.update_idletasks()

        # Re-order via Tkinter's native before/after pack parameters, avoiding pack_forget lag
        if idx2 < idx1:
            # Moving up: Pack the moving row right before its upper neighbor
            moving_row.pack(before=neighbor_row)
        else:
            # Moving down: Pack the moving row right after its lower neighbor
            moving_row.pack(after=neighbor_row)

    def handle_row_drop(self, row_widget):
        """Locks elements down cleanly when user lets go of the mouse button."""
        
        # Instantly restore the row's true background style
        row_widget.set_active(False)

    def save_playlist(self):
        """Handles the logic for updating the playlist"""

        filepath = os.path.join("playlists", f"{self.playlist.name}.json")
        self.playlist.save(filepath)
        self.destroy()
