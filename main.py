import os
import json
import customtkinter as ctk
from tkinter import filedialog  
from pygame import mixer
import mutagen
import random
import core
import ui

# Initialize the audio mixer
mixer.init()

WHITE = "#ffffff"
VERY_LIGHT_GRAY = "#d9d9d9"
LIGHT_GRAY = "#565656"
GRAY = "#2b2b2b"
DARK_GRAY = "#242424"
BLACK = "#000000"
BLUE = "#1a6faf"
HOVER_BLUE = "#145a86"

class MusicPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Music Player")
        ctk.set_appearance_mode("dark")

        window_width, window_height = 900, 570

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Initialise the pygame-based playback engine
        self.engine = core.PlaybackEngine()

        # Initialise the input manager to track key presses
        self.input_manager = core.InputManager(self)

        # Playlist
        self.loaded_playlist = core.Playlist()
        self.loaded_playlist_buttons = []

        # Playlist queue variables
        self.playlist_queue = core.Playlist()
        self.playlist_buttons = []
        self.current_index = 0

        # Queue variables
        self.queue_view_active = False

        # Slider variables
        self.is_dragging_slider = False
        self.was_playing_before_drag = False

        self.SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")

        self.setup_ui()

        self.config = core.ConfigSettings()
        self.load_last_used()

        # Bind events
        self.bind("<Configure>", self.on_window_configure)

        self.bind("<space>", lambda e: self.toggle_play())  # Play/pause
        self.bind("<Right>", lambda e: self.increment_slider(5))  # Fast forward 5 seconds
        self.bind("<Left>", lambda e: self.increment_slider(-5))  # Rewind 5 seconds

        self.bind("<XF86AudioNext>", lambda e: self.next_song())  # Next song
        self.bind("<XF86AudioPrev>", lambda e: self.prev_song())  # Previous song
        self.bind("<XF86AudioPlay>", lambda e: self.toggle_play())  # Play/pause

        self.bind("<Up>", lambda e: self.adjust_volume(5))  # Increase volume
        self.bind("<Down>", lambda e: self.adjust_volume(-5))  # Decrease volume
        self.bind("<m>", lambda e: self.toggle_volume_mute())  # Mute/unmute

    def on_window_configure(self, event=None):
        self.update_scrollbar_visibility(self.playlist_queue_frame if not self.queue_view_active else self.loaded_playlist_frame)

    def setup_ui(self):
        """Set up the app UI."""

        # Left container (Takes up 60% width, 92% height)
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.place(relx=0.02, rely=0.04, relwidth=0.56, relheight=0.92)

        # Visual toggle between Playlist and Queue views
        self.view_toggle = ctk.CTkSegmentedButton(self.left_panel, values=["Playlist: Untitled", "Queue"], command=self.switch_view,
            selected_color=BLUE, selected_hover_color=HOVER_BLUE, fg_color=GRAY,  unselected_color=GRAY, unselected_hover_color=LIGHT_GRAY,
            font=("Arial", 14, "bold"))
        self.view_toggle.pack(fill="x", pady=(0, 10))
        self.view_toggle.set("Playlist: Untitled")

        # Loaded playlist view
        self.loaded_playlist_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color=GRAY)

        # Playlist queue view
        self.playlist_queue_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color=GRAY)
        self.playlist_queue_frame.pack(fill="both", expand=True)

        # Playlist control buttons
        self.playlist_controls_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.playlist_controls_frame.pack(fill="x", pady=(4, 0))

        # Open folder button
        self.open_folder_button = ctk.CTkButton(self.playlist_controls_frame, width=30, height=30, command=self.open_folder,
                                text="Open Folder", font=("Arial", 12, "bold"), fg_color=BLUE, hover_color=HOVER_BLUE)
        self.open_folder_button.pack(side="left", padx=(0, 5))

        # Save playlist button
        self.save_playlist_button = ctk.CTkButton(self.playlist_controls_frame, width=30, height=30, command=self.save_folder_as_playlist,
                                text="Save Playlist", font=("Arial", 12, "bold"), fg_color=BLUE, hover_color=HOVER_BLUE)
        self.save_playlist_button.pack(side="left", padx=(0, 5))

        # View playlists button
        self.load_playlist_button = ctk.CTkButton(self.playlist_controls_frame, width=30, height=30, command=self.view_playlists,
                                text="View Playlists", font=("Arial", 12, "bold"), fg_color=BLUE, hover_color=HOVER_BLUE)
        self.load_playlist_button.pack(side="left", padx=(0, 5))

        # Shuffle playlist button
        self.shuffle_queue_button = ctk.CTkButton(self.playlist_controls_frame, width=30, height=30, command=self.shuffle_queue,
                                text="Shuffle Queue", font=("Arial", 12, "bold"), fg_color=BLUE, hover_color=HOVER_BLUE)
        self.shuffle_queue_button.pack(side="left", padx=(0, 5))

        # Right container (Takes up 40% width, 92% height)
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.place(relx=0.60, rely=0.04, relwidth=0.4, relheight=0.92)

        # Album art
        self.album_art_frame = ctk.CTkFrame(self.right_frame, width=250, height=250, fg_color=GRAY)
        self.album_art_frame.pack(pady=20)
        
        self.art_label = ctk.CTkLabel(self.album_art_frame, text="🎵", font=("Arial", 80))
        self.art_label.place(relx=0.5, rely=0.5, anchor="center")

        # Song title label
        self.track_label = ctk.CTkLabel(self.right_frame, text="No Folder Loaded", font=("Arial", 18, "bold"), wraplength=320, justify="center")
        self.track_label.pack(pady=(5, 0))

        self.artist_label = ctk.CTkLabel(self.right_frame, text="", font=("Arial", 14))
        self.artist_label.pack(pady=(2, 5))

        # Play elements frame
        self.play_elements_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.play_elements_frame.pack(side="bottom", fill="x", pady=(10, 0))

        # Horizontal layout frame for the slider and volume Button
        self.slider_row_frame = ctk.CTkFrame(self.play_elements_frame, fg_color="transparent")
        self.slider_row_frame.pack(fill="x", padx=40, pady=(15, 2))

        # Configure columns: column 1 (slider) stretches, columns 0 and 2 do not.
        self.slider_row_frame.grid_columnconfigure(0, minsize=30)
        self.slider_row_frame.grid_columnconfigure(1, weight=1)
        self.slider_row_frame.grid_columnconfigure(2, minsize=30)

        # Progress slider
        self.slider = ctk.CTkSlider(self.slider_row_frame, from_=0, to=1000, number_of_steps=1000, command=self.slider_event)
        self.slider.grid(row=0, column=1, sticky="ew")  # sticky="ew" makes it stretch horizontally
        self.slider.set(0)

        # Options button
        self.options_btn = ctk.CTkButton(self.slider_row_frame, text="⋮", width=30, font=("Arial", 20), 
                                    fg_color="transparent", hover_color=GRAY, command=self.open_options_menu)
        self.options_btn.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.volume_anchor = ctk.CTkFrame(self.slider_row_frame, fg_color="transparent")
        self.volume_anchor.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Volume Button
        self.volume_btn = ctk.CTkButton(self.volume_anchor, text="🔊", width=30, font=("Arial", 18), 
                                    fg_color="transparent", hover_color=GRAY, command=self.toggle_volume_mute)
        # Small padx on the left of the button just so it doesn't touch the slider tip
        self.volume_btn.pack()

        # Volume slider popup
        self.volume_popup = ctk.CTkToplevel(self)
        self.volume_popup.overrideredirect(True)
        self.volume_popup.withdraw()
        self.volume_popup.configure(fg_color=DARK_GRAY)

        # Volume slider
        self.volume_slider = ctk.CTkSlider(
            self.volume_popup,
            from_=0,
            to=100,
            orientation="vertical",
            command=self.set_volume
        )
        self.volume_slider.set(100)
        self.volume_slider.pack()

        # Volume slider pop up bindings
        self.volume_hide_job = None

        self.volume_btn.bind("<Enter>", self.show_volume_popup)
        self.volume_btn.bind("<Leave>", self.schedule_hide_volume_popup)

        self.volume_popup.bind("<Enter>", self.cancel_hide_volume_popup)
        self.volume_popup.bind("<Leave>", self.schedule_hide_volume_popup)

        self.volume_slider.bind("<ButtonPress-1>", self.cancel_hide_volume_popup)
        self.volume_slider.bind("<B1-Motion>", self.cancel_hide_volume_popup)

        # Track length labels frame
        self.time_frame = ctk.CTkFrame(self.play_elements_frame, fg_color="transparent")
        self.time_frame.pack(fill="x", padx=70, pady=(0, 10)) # Matches the slider's horizontal span

        # Track length labels
        self.current_time_label = ctk.CTkLabel(self.time_frame, text="00:00", font=("Arial", 12))
        self.current_time_label.pack(side="left")

        self.total_time_label = ctk.CTkLabel(self.time_frame, text="00:00", font=("Arial", 12))
        self.total_time_label.pack(side="right")

        # Bind mouse press and release to manage the dragging state safely
        self.slider.bind("<Button-1>", self.on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        # Control buttons frame
        self.controls_frame = ctk.CTkFrame(self.play_elements_frame, fg_color="transparent")
        self.controls_frame.pack(pady=(10, 0))

        self.btn_shuffle = ctk.CTkButton(self.controls_frame, text="🔀", width=40, font=("Arial", 20), fg_color=GRAY, hover_color=LIGHT_GRAY, 
                                    command=self.toggle_shuffle)
        self.btn_shuffle.grid(row=0, column=0, padx=8)

        self.btn_prev = ctk.CTkButton(self.controls_frame, text="⏮", width=40, font=("Arial", 20), fg_color=BLUE, hover_color=HOVER_BLUE,
                                    command=self.prev_song)
        self.btn_prev.grid(row=0, column=1, padx=8)

        self.btn_play = ctk.CTkButton(self.controls_frame, text="▶", width=45, font=("Arial", 20), fg_color=BLUE, hover_color=HOVER_BLUE, 
                                    command=self.toggle_play)
        self.btn_play.grid(row=0, column=2, padx=8)

        self.btn_next = ctk.CTkButton(self.controls_frame, text="⏭", width=40, font=("Arial", 20), fg_color=BLUE, hover_color=HOVER_BLUE, 
                                    command=self.next_song)
        self.btn_next.grid(row=0, column=3, padx=8)

        self.btn_loop = ctk.CTkButton(self.controls_frame, text="🔁", width=40, font=("Arial", 20), fg_color=GRAY, hover_color=LIGHT_GRAY, 
                                    command=self.toggle_loop)
        self.btn_loop.grid(row=0, column=4, padx=8)

        # Start the slider update loop
        self.update_slider()

    def load_last_used(self):
        """Load the last used folder or playlist based on the saved config."""
        # State is already loaded into self.config on instantiation
        if self.config.last_open == "folder":
            folder = self.config.last_folder
            if folder and os.path.exists(folder):
                self.process_folder(folder)

        elif self.config.last_open == "playlist":
            playlist_path = self.config.last_playlist
            if playlist_path and os.path.exists(playlist_path):
                playlist = core.Playlist.load(playlist_path)
                self.process_playlist(playlist)

    def save_folder_path(self, folder_path):
        """Saves the selected folder path."""
        self.config.set_folder(folder_path)


    def save_playlist_path(self, playlist_path):
        """Saves the selected playlist path."""
        self.config.set_playlist(playlist_path)

    def open_folder(self):
        """Open a native directory selection dialog."""
        folder_path = filedialog.askdirectory(title="Select Music Folder")
        if folder_path:
            self.process_folder(folder_path)
            self.save_folder_path(folder_path)  # Save this path for next time

    def save_folder_as_playlist(self):
        ui.SavePlaylistDialog(self, self.playlist_queue)

    def view_playlists(self):
        ui.ViewPlaylistsDialog(self)

    def shuffle_queue(self):
        random.shuffle(self.playlist_queue.tracks)

        # Check if playlist is not empty and respond appropriately
        if self.playlist_queue.is_populated():
            # Synchronize track collection to engine boundary layout
            self.engine.stop()
            self.engine.set_playlist(self.playlist_queue.tracks)
            self.current_index = 0
            self.engine.current_index = 0
            self.engine.load_track()
            self.engine.toggle_play()
            self.update_playlist_queue_ui()
            self.update_ui_for_current_track()
            self.switch_view("Queue")
            self.view_toggle.set("Queue")

    def process_folder(self, folder_path):
        """Process the a folder and add all supported audio files to the playlist."""
        self.loaded_playlist = core.Playlist()
        self.playlist_queue = core.Playlist()
        
        # Loop through each file in the processing folder
        for file in os.listdir(folder_path):
            if file.lower().endswith(self.SUPPORTED_EXTENSIONS):
                full_path = os.path.join(folder_path, file)

                # Default fallbacks if metadata tags are missing
                title = os.path.splitext(file)[0]
                artist = "Unknown Artist"
                length = 100.0

                try:
                    audio = mutagen.File(full_path)
                    if audio is not None:
                        # Extract Track Length
                        if audio.info is not None:
                            length = audio.info.length
                            
                        # Standardize the tags target (FLAC/MP3 use .tags, some OGG profiles map directly to audio)
                        tags = audio.tags if hasattr(audio, "tags") and audio.tags else audio
                        
                        if tags is not None:
                            # Title exraction
                            if "TIT2" in tags:        # MP3 ID3
                                title = tags["TIT2"].text[0]
                            elif "title" in tags:     # FLAC / OGG Vorbis
                                title = tags["title"][0]
                                
                            # Artist extraction
                            if "TPE1" in tags:        # MP3 ID3
                                artist = tags["TPE1"].text[0]
                            elif "artist" in tags:    # FLAC / OGG Vorbis
                                artist = tags["artist"][0]

                except Exception as e:
                    print(f"Error reading tags for {file}: {e}")

                # Add song to playlist in a dictionary structure
                self.loaded_playlist.add_track({
                    "title": title, 
                    "artist": artist, 
                    "path": full_path,
                    "length": length
                })

                self.playlist_queue.add_track({
                    "title": title, 
                    "artist": artist, 
                    "path": full_path,
                    "length": length
                })

        # Check if playlist is not empty and respond appropriately
        if self.loaded_playlist.is_populated():
            # Synchronize track collection to engine boundary layout
            self.engine.stop()
            self.engine.set_playlist(self.loaded_playlist.tracks)
            self.current_index = 0
            self.engine.current_index = 0
            self.engine.load_track()
            self.engine.toggle_play()
            self.update_ui_for_current_track()
        else:
            self.track_label.configure(text="No supported audio files found")
            self.artist_label.configure(text="")

        self.update_playlist_queue_ui()
        self.switch_view("Queue")
        self.view_toggle.set("Queue")

    def process_playlist(self, playlist):
        """Processes a loaded playlist and updates the engine and UI."""
        if playlist and playlist.is_populated():
            self.loaded_playlist = playlist
            self.playlist_queue = playlist
            self.engine.stop()
            self.engine.set_playlist(self.loaded_playlist.tracks)
            self.current_index = 0
            self.engine.current_index = 0
            self.engine.load_track()
            self.engine.toggle_play()
            self.update_loaded_playlist_ui()
            self.update_playlist_queue_ui()
            self.update_ui_for_current_track()
        else:
            self.track_label.configure(text="Playlist is empty or invalid")
            self.artist_label.configure(text="")
        self.switch_view(f"Playlist:")
        self.view_toggle.set(f"Playlist: {self.loaded_playlist.name}")

    def update_processed_playlist(self, playlist):
        if playlist and playlist.is_populated():
            self.loaded_playlist = playlist
            self.update_loaded_playlist_ui()
            self.view_toggle.set(f"Playlist: {self.loaded_playlist.name}")

    def switch_view(self, selected_view):
        if selected_view == "Queue":
            self.loaded_playlist_frame.pack_forget()
            self.playlist_queue_frame.pack(fill="both", expand=True, before=self.playlist_controls_frame)
            self.update_scrollbar_visibility(self.playlist_queue_frame)
            self.queue_view_active = True
        else:
            self.playlist_queue_frame.pack_forget()
            self.loaded_playlist_frame.pack(fill="both", expand=True, before=self.playlist_controls_frame)
            self.update_scrollbar_visibility(self.loaded_playlist_frame)
            self.queue_view_active = False

    def update_ui_for_current_track(self):
        """Unified presentation renderer mapping straight from engine truth properties."""
        song = self.engine.current_track
        if song:
            self.track_label.configure(text=song["title"])
            self.artist_label.configure(text=song["artist"])
            self.total_time_label.configure(text=core.format_time(song["length"]))
            self.slider.configure(to=song["length"])
            
            # Reset timeline layout cleanly if the song is resting at zero position
            if self.engine.get_current_position() <= 0.1:
                self.current_time_label.configure(text="00:00")
                self.slider.set(0)

            # Extract visual metadata assets
            self.set_album_art(song)
            self.highlight_current_song()

            # Synchronize presentation toggle characters
            if self.engine.is_playing:
                self.btn_play.configure(text="⏸")
            else:
                self.btn_play.configure(text="▶")

    def set_album_art(self, song):
        """Extracts cover art from audio metadata and updates the UI."""
        image = core.load_album_art(song["path"], (250, 250))

        if image:
            self.art_label.configure(image=image, text="")
            self.art_label.image = image
            self.album_art_frame.configure(fg_color="transparent")
        else:
            self.set_default_art()

    def set_default_art(self):
        """Safely clears old images and falls back to the music emoji."""
        # Clean up the reference tracking variable
        if hasattr(self.art_label, "image"):
            self.art_label.image = None
            
        # Directly clear the underlying Tkinter widget's image property swapping back to text.
        self.art_label._label.configure(image="") 
        self.art_label.configure(image=None, text="🎵", font=("Arial", 80))
        self.album_art_frame.configure(fg_color=GRAY)

    def get_visible_scroll_height(self, frame):
        frame.update_idletasks()
        canvas = frame._parent_canvas
        scaling = float(self.tk.call('tk', 'scaling'))
        return int(canvas.winfo_height() / scaling)

    def update_scrollbar_visibility(self, frame):
        if not frame.winfo_exists():
            return

        frame.update_idletasks()

        content_height = 52 * len(frame.winfo_children())
        viewport_height = self.get_visible_scroll_height(frame)

        needs_scroll = content_height > viewport_height

        if needs_scroll:
            frame.configure(scrollbar_button_color="#696969")
            frame.configure(scrollbar_button_hover_color="#878787")
        else:
           frame.configure(scrollbar_button_color=GRAY)
           frame.configure(scrollbar_button_hover_color=GRAY)

    def update_playlist_queue_ui(self):
        """Clears the scrollable frame and redraws all track rows using the helper class."""
        # Destroy old row components to clear memory references cleanly
        for row in self.playlist_buttons:
            row.destroy()
        self.playlist_buttons.clear()

        # Rebuild the list with TrackRow objects
        for index, song in enumerate(self.playlist_queue.tracks):
            row = ui.TrackRow(
                master=self.playlist_queue_frame,
                index=index,
                title=song["title"],
                artist=song["artist"],
                row_type=core.TrackRowType.QUEUE,
                click_callback=self.play_selected_song,
                options_callback=self.handle_track_options,
                drag_callback=self.handle_row_drag,
                drop_callback=self.handle_row_drop
            )
            row.pack(fill="x", padx=5, pady=2)
            self.playlist_buttons.append(row)

    def set_playlist_name(self, new_name):
        """Updates the playlist name and refreshes the UI."""
        self.loaded_playlist.name = new_name
        self.view_toggle.configure(values=[f"Playlist: {self.loaded_playlist.name}", "Queue"])

    def play_selected_song(self, index):
        """Plays a song directly from the playlist."""
        self.current_index = index
        self.engine.current_index = index
        self.engine.stop()
        self.engine.load_track()
        self.engine.toggle_play()
        self.update_ui_for_current_track()

    def highlight_current_song(self):
        """Loops through UI rows and updates their visual selection state."""
        for row in self.playlist_buttons:
            is_current = (row.index == self.current_index)
            row.set_active(is_current)

    def handle_track_options(self, index : int, action : core.TrackActions):
        """Routes the contextual menu actions for each track."""        
        match action:
            case core.TrackActions.PLAY_NEXT:
                track_to_add = self.loaded_playlist.tracks[index]
                self.playlist_queue.tracks.insert(self.current_index + 1, track_to_add)
                self.engine.set_playlist(self.playlist_queue.tracks)
                self.update_playlist_queue_ui()

            case core.TrackActions.ADD_TO_QUEUE:
                track_to_add = self.loaded_playlist.tracks[index]
                self.playlist_queue.add_track(track_to_add)
                self.engine.set_playlist(self.playlist_queue.tracks)
                self.update_playlist_queue_ui()

            case core.TrackActions.REMOVE_FROM_QUEUE:
                if 0 <= index < len(self.playlist_queue.tracks):
                    self.playlist_queue.remove_track(index)
                    self.engine.set_playlist(self.playlist_queue.tracks)
                    self.update_playlist_queue_ui()

                    if self.current_index == index:
                        self.current_index = max(0, self.current_index - 1)
                        self.engine.current_index = self.current_index

            case core.TrackActions.REMOVE_FROM_PLAYLIST:
                if 0 <= index < len(self.loaded_playlist.tracks):
                    self.loaded_playlist.remove_track(index)
                    self.update_loaded_playlist_ui()

                    # Save the updated playlist to disk
                    playlist_dir = "playlists"
                    filepath = os.path.join(playlist_dir, self.loaded_playlist.name + ".json")
                    self.loaded_playlist.save(filepath)

            case core.TrackActions.SAVE_TO_PLAYLIST:
                activity_queue = self.playlist_queue if self.queue_view_active else self.loaded_playlist
                ui.ViewPlaylistsDialog(self, activity_queue.tracks[index])

            case core.TrackActions.OPEN_IN_FOLDER:
                activity_queue = self.playlist_queue if self.queue_view_active else self.loaded_playlist
                track_path = activity_queue.tracks[index]["path"]
                core.open_in_folder(track_path)

    def update_loaded_playlist_ui(self):
        """Re-renders the loaded playlist view."""
        for row in self.loaded_playlist_buttons:
            row.destroy()
        self.loaded_playlist_buttons.clear()

        for index, song in enumerate(self.loaded_playlist.tracks):
            row = ui.TrackRow(
                master=self.loaded_playlist_frame,
                index=index,
                title=core.truncate_text(song["title"], 60),
                artist=core.truncate_text(song["artist"], 30),
                row_type=core.TrackRowType.VIEW_ONLY,
                click_callback=None,
                options_callback=self.handle_track_options,
                drag_callback=self.handle_row_drag,
                drop_callback=self.handle_row_drop
            )
            row.pack(fill="x", padx=5, pady=2)
            self.loaded_playlist_buttons.append(row)

        self.update_scrollbar_visibility(self.loaded_playlist_frame)

        # Refresh playlist name
        self.view_toggle.configure(values=[f"Playlist: {self.loaded_playlist.name}", "Queue"])

    def handle_row_drag(self, row_widget, y_root):
        """Tracks mouse movement and instantly flips positions with adjacent neighbors."""
        # Determine which bucket we are sorting based on layout parent containers
        if row_widget.master == self.loaded_playlist_frame:
            buttons_list = self.loaded_playlist_buttons
        else:
            buttons_list = self.playlist_buttons

        current_idx = row_widget.index

        # Check item directly above the moving item
        if current_idx > 0:
            above_row = buttons_list[current_idx - 1]
            above_center = above_row.winfo_rooty() + (above_row.winfo_height() / 2)
            if y_root < above_center:
                self.swap_rows(row_widget.master, current_idx, current_idx - 1)
                return

        # Check item directly below the moving item
        if current_idx < len(buttons_list) - 1:
            below_row = buttons_list[current_idx + 1]
            below_center = below_row.winfo_rooty() + (below_row.winfo_height() / 2)
            if y_root > below_center:
                self.swap_rows(row_widget.master, current_idx, current_idx + 1)
                return

    def swap_rows(self, master_frame, idx1, idx2):
        """Swaps data arrays and handles non-destructive, highly optimized UI adjustments."""

        if master_frame == self.loaded_playlist_frame:
            buttons_list = self.loaded_playlist_buttons
            data_list = self.loaded_playlist.tracks
        else:
            buttons_list = self.playlist_buttons
            data_list = self.playlist_queue.tracks

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
        row_widget.set_active(row_widget.is_active_song)

        # Determine which list is being referenced
        if row_widget.master == self.loaded_playlist_frame:
            buttons_list = self.loaded_playlist_buttons
        else:
            buttons_list = self.playlist_buttons

        # Scan the list to find the active song's new index position
        for row in buttons_list:
            if row.is_active_song:
                self.current_index = row.index
                self.engine.current_index = row.index
                break

    def toggle_play(self):
        """Toggle playback."""

        if not self.playlist_queue.is_populated():
            return

        self.engine.toggle_play()
        if self.engine.is_playing:
            self.btn_play.configure(text="⏸")
        else:
            self.btn_play.configure(text="▶")

    def toggle_loop(self):
        """Toggle playback loop."""

        if not self.engine.current_track:
            return

        self.engine.toggle_loop()
        if self.engine.is_looping:
            self.btn_loop.configure(fg_color=BLUE, hover_color=HOVER_BLUE)
        else:
            self.btn_loop.configure(fg_color=GRAY, hover_color=LIGHT_GRAY)

    def toggle_shuffle(self):
        """Toggle playback shuffle."""

        if not self.playlist_queue.is_populated():
            return

        self.engine.toggle_shuffle()
        if self.engine.is_shuffling:
            self.btn_shuffle.configure(fg_color=BLUE, hover_color=HOVER_BLUE)
        else:
            self.btn_shuffle.configure(fg_color=GRAY, hover_color=LIGHT_GRAY)

    def next_song(self):
        """Call the next song."""
        if self.playlist_queue.is_populated():
            self.engine.next_track()
            self.current_index = self.engine.current_index
            self.update_ui_for_current_track()

    def prev_song(self):
        """Call the previous song."""

        if self.playlist_queue.is_populated():
            if self.engine.get_current_position() <= 2.0:  # If the current track is at the beginning, go to the previous track
                self.engine.prev_track()
                self.current_index = self.engine.current_index
                self.update_ui_for_current_track()
            else:
                self.engine.replay_track()
        self.btn_play.configure(text="⏸")

    def on_slider_press(self, event):
        """Triggered when the user clicks down on the slider."""
        self.is_dragging_slider = True
        self.was_playing_before_drag = self.engine.is_playing
        if self.engine.is_playing:
            self.engine.toggle_play()
            self.btn_play.configure(text="▶")

    def on_slider_release(self, event):
        """Triggered when the user lets go of the slider."""
        if self.engine.current_track is not None:
            new_pos = self.slider.get()
            self.engine.seek(new_pos)
            
            # Continue playing track if it was playing before the drag started
            if getattr(self, "was_playing_before_drag", False):
                if not self.engine.is_playing:
                    self.engine.toggle_play()
            
            if self.engine.is_playing:
                self.btn_play.configure(text="⏸")
            else:
                self.btn_play.configure(text="▶")

        self.is_dragging_slider = False

    def slider_event(self, value):
        """Triggered continuously while dragging the slider knob."""
        self.current_time_label.configure(text=core.format_time(value))  # Update current time label in real-time as slider moves

    def update_slider(self):
        """Continously update the slider position."""

        # Only update the slider if music is playing, unpaused, and the user is not dragging the slider
        if self.engine.is_playing and not self.engine.is_paused and not self.is_dragging_slider:
            current_pos = self.engine.get_current_position()
            
            if current_pos == -1:
                self.next_song()
            elif self.engine.is_playing:
                max_duration = self.slider.cget("to")
                if current_pos <= max_duration:
                    self.slider.set(current_pos)
                    self.current_time_label.configure(text=core.format_time(current_pos))
        
        self.after(100, self.update_slider)  # Schedule the next slider update

    def increment_slider(self, increment):
        """Increment the slider position by a specified amount."""
        if self.engine.current_track is not None:
            new_pos = self.engine.get_current_position() + increment
            new_pos = max(0, min(new_pos, self.slider.cget("to")))  # Clamp to valid range
            self.engine.seek(new_pos)
            self.slider.set(new_pos)
            self.current_time_label.configure(text=core.format_time(new_pos))

    def open_options_menu(self):
            """Creates a borderless dropdown menu."""
    
            # Create a top-level popup window
            menu = ctk.CTkToplevel(self)
            menu.withdraw() # Hide it instantly while configuring layout
            menu.overrideredirect(True) # Completely kills the OS title bar and native borders
    
            # Apply styling
            menu.configure(fg_color=DARK_GRAY, corner_radius=6)
    
            # Dropdown options
            options = [
                ("Remove from queue", core.TrackActions.REMOVE_FROM_QUEUE),
                ("Save to a playlist", core.TrackActions.SAVE_TO_PLAYLIST),
                ("Open in folder", core.TrackActions.OPEN_IN_FOLDER)
            ]
    
            # Pack custom buttons as rows
            for i, (label, action) in enumerate(options):
                btn = ctk.CTkButton(menu, text=label, anchor="w",
                    fg_color="transparent", text_color=WHITE, hover_color=LIGHT_GRAY,
                    height=30, corner_radius=4, font=("Arial", 12),
                    command=lambda a=action: [menu.destroy(), self.handle_option(a)]
                )
                
                # Determine vertical padding based on position (no padding for inner elements)
                if i == 0:
                    row_pady = (2, 0)
                elif i == len(options) - 1:
                    row_pady = (0, 2)
                else:
                    row_pady = 0
                    
                btn.pack(fill="x", padx=2, pady=row_pady)
    
            # Position the menu precisely right underneath the options icon button
            x = self.options_btn.winfo_rootx()
            y = self.options_btn.winfo_rooty() - self.options_btn.winfo_height() - len(options) * 30 + 4
    
            # Geometry
            menu.geometry(f"160x{len(options) * 30 + 4}+{x}+{y}")
            
            # Smooth rendering and focus handling
            menu.deiconify()
            menu.attributes("-topmost", True)
            
            menu.after(10, menu.focus_set)
    
            def safe_close(event):
                # Only destroy if focus shifted to a completely different window instance
                if event.widget == menu:
                    # Determine the widget which is focused, and if it lives in the menu, do not close yet
                    next_focus = menu.focus_get()
                    if next_focus and next_focus.master == menu:
                        return
                    
                    # Use after_idle so any click commands on the menu buttons register before the window vanishes
                    menu.after_idle(lambda: menu.destroy() if menu.winfo_exists() else None)
    
            menu.bind("<FocusOut>", safe_close)
    
    def handle_option(self, action : core.TrackActions):
        """Route the clicked option's event data."""
        self.handle_track_options(self.current_index, action)

    def toggle_volume_mute(self):
        """Toggles the volume between muted and the last set volume."""
        if self.engine.is_muted:
            self.engine.unmute()
            self.volume_btn.configure(text="🔊")
            self.volume_slider.set(self.engine.slider_volume * 100)  # Restore the slider to the last volume level
        else:
            self.engine.mute()
            self.volume_btn.configure(text="🔇")
            self.volume_slider.set(0)  # Set the slider to 0 when muted

    def show_volume_popup(self, event=None):
        """Shows the volume popup and positions it relative to the volume button."""
        self.cancel_hide_volume_popup()

        self.update_idletasks()

        x = self.volume_anchor.winfo_rootx()
        y = self.volume_anchor.winfo_rooty()

        self.volume_popup.deiconify()
        self.volume_popup.attributes("-topmost", True)

        self.volume_popup.geometry(f"16x100+{x + 10}+{y - 120}")

    def hide_volume_popup(self):
        """Hides the volume popup and starts the fade-out effect."""
        self.volume_hide_job = None
        self.fade_out()

    def schedule_hide_volume_popup(self, event=None):
        """Schedules the volume popup to fade out after a short delay."""
        self.cancel_hide_volume_popup()
        self.volume_hide_job = self.after(300, self.hide_volume_popup)

    def cancel_hide_volume_popup(self, event=None):
        """Cancels any scheduled hide operation for the volume popup."""
        if self.volume_hide_job is not None:
            self.after_cancel(self.volume_hide_job)
            self.volume_hide_job = None

    def fade_out(self, step=0.08):
        """Gradually fades out the volume popup."""
        def _step(alpha):
            if not self.volume_popup.winfo_exists():
                return

            alpha -= step
            if alpha <= 0.0:
                self.volume_popup.withdraw()
                self.volume_popup.attributes("-alpha", 1.0)
                return

            self.volume_popup.attributes("-alpha", alpha)
            self.after(10, lambda: _step(alpha))

        _step(1.0)

    def set_volume(self, volume):
        """Sets the volume level."""
        self.engine.set_volume(volume / 100.0)  # Engine expects a value between 0.0 and 1.0
        if self.engine.is_muted:
            self.toggle_volume_mute()  # Unmute if the user adjusts the volume while muted

    def adjust_volume(self, increment):
        """Adjusts the volume by a specified amount."""
        new_volume = self.engine.slider_volume * 100 + increment
        new_volume = max(0, min(new_volume, 100))  # Clamp to valid range
        self.set_volume(new_volume)
        self.volume_slider.set(new_volume)

# Main routine
if __name__ == "__main__":
    app = MusicPlayer()
    app.mainloop()