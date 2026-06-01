import os
import json
import customtkinter as ctk
from tkinter import filedialog  
from pygame import mixer
import mutagen
import io
from PIL import Image
import core

# Initialize the audio mixer
mixer.init()

CONFIG_FILE = "config.json"
WHITE = "#ffffff"
VERY_LIGHT_GRAY = "#d9d9d9"
LIGHT_GRAY = "#565656"
GRAY = "#2b2b2b"
DARK_GRAY = "#242424"
BLACK = "#000000"
BLUE = "#1a6faf"
HOVER_BLUE = "#145a86"

class PlaylistRow(ctk.CTkFrame):
    def __init__(self, master, index, title, artist, click_callback, options_callback):
        super().__init__(
            master,
            fg_color="transparent",
            height=48,
            corner_radius=6
        )
        self.pack_propagate(False)
        
        self.index = index
        self.click_callback = click_callback
        self.options_callback = options_callback

        self.index_label = ctk.CTkLabel(self, text=f"{index + 1}", font=("Arial", 13), text_color=VERY_LIGHT_GRAY, width=10, anchor="w")
        self.index_label.pack(side="left", padx=(10, 0))

        # Truncate Title and Artist names if they exceed character limits
        truncated_title = self.truncate_text(title, max_chars=40)
        truncated_artist = self.truncate_text(artist, max_chars=40)
        
        display_text = f"{truncated_title}\n{truncated_artist}".strip()

        # Setup the Text Label (Packed to the LEFT)
        self.label = ctk.CTkLabel(
            self,
            text=display_text,
            font=("Arial", 13),
            text_color=WHITE,
            anchor="w",
            justify="left"
        )
        # fill="both" and expand=True ensures the invisible text bounding box spans the remaining width, keeping the entire left side clickable!
        self.label.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # Options button (Packed to the RIGHT)
        self.btn_options = ctk.CTkButton(
            self,
            text="•••",
            width=30,
            height=30,
            fg_color="transparent",
            text_color=WHITE,
            font=("Arial", 12, "bold"),
            command=self.show_options_menu
        )
        self.btn_options.pack(side="right", padx=(0, 5))

        # Bind mouse interactions to the row container and the text label
        for widget in (self, self.index_label, self.label):
            widget.bind("<Enter>", self.on_hover)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_click)
            widget.bind("<Button-3>", self.show_options_menu)

        self.btn_options.bind("<Enter>", self.on_options_hover)
        self.btn_options.bind("<Leave>", self.on_options_leave)

        self.is_active_song = False

    def truncate_text(self, text, max_chars):
        """Helper method to slice string and append an ellipsis if it's too long."""
        if len(text) > max_chars:
            return text[:max_chars - 3].strip() + "..."
        return text

    def set_active(self, is_active):
        """Changes the row's styling depending on if it's the currently playing track."""
        self.is_active_song = is_active
        if is_active:
            self.configure(fg_color=BLUE)
            self.index_label.configure(text_color=WHITE)
            self.label.configure(text_color=WHITE)
            self.btn_options.configure(hover_color=HOVER_BLUE)
        else:
            self.configure(fg_color="transparent")
            self.index_label.configure(text_color=VERY_LIGHT_GRAY)
            self.label.configure(text_color=WHITE)
            self.btn_options.configure(hover_color=DARK_GRAY)

    def on_hover(self, event):
        """Highlight the background row when the cursor is over it."""
        if not self.is_active_song:
            self.configure(fg_color=LIGHT_GRAY)
            self.index_label.configure(text=f"▶")

    def on_leave(self, event):
        """Remove background highlight when cursor moves away."""
        if not self.is_active_song:
            self.configure(fg_color="transparent")
            self.index_label.configure(text=f"{self.index + 1}")
    
    def on_options_hover(self, event):
        """Change the options button color on hover."""
        if not self.is_active_song:
            self.configure(fg_color=LIGHT_GRAY)
            self.btn_options.configure(fg_color=GRAY)
        else:
            self.btn_options.configure(fg_color=HOVER_BLUE)

    def on_options_leave(self, event):
        """Remove background highlight when cursor moves away."""
        self.btn_options.configure(fg_color="transparent")
        if not self.is_active_song:
            self.configure(fg_color="transparent")

    def on_click(self, event):
        """Call playlist selection logic."""
        self.click_callback(self.index)
        self.index_label.configure(text=f"{self.index + 1}")

    def show_options_menu(self, event=None):
        """Creates a gorgeous, borderless dropdown menu to bypass Windows UI overrides."""
        # Create a top-level popup window
        menu = ctk.CTkToplevel(self)
        menu.withdraw() # Hide it instantly while configuring layout
        menu.overrideredirect(True) # Completely kills the OS title bar and native borders

        # Apply styling
        menu.configure(fg_color=DARK_GRAY, corner_radius=6 )

        # Dropdown options
        options = [
            ("Add to queue", core.TrackActions.ADD_TO_QUEUE),
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
                
            btn.pack(fill="x", padx=4, pady=row_pady)

        # If triggered by right-click, use the mouse position for more intuitive context menu placement
        # Otherwise, position the menu precisely right underneath the options icon button
        if event is not None:
            x = event.x_root
            y = event.y_root + 10
        else:
            x = self.btn_options.winfo_rootx()
            y = self.btn_options.winfo_rooty() + self.btn_options.winfo_height()

        # Geometry
        menu.geometry(f"160x{len(options) * 30 + 4}+{x}+{y}")
        
        # Smooth rendering and focus handling
        menu.deiconify()
        menu.attributes("-topmost", True)
        
        menu.after(10, menu.focus_set)

        def safe_close(event):
            # Only destroy if focus shifted to a completely different window instance
            if event.widget == menu:
                # Use after_idle so any click commands on the menu buttons 
                # register BEFORE the window vanishes entirely
                menu.after_idle(lambda: menu.destroy() if menu.winfo_exists() else None)

        menu.bind("<FocusOut>", safe_close)

    def handle_option(self, action : core.TrackActions):
        """Route the clicked option's event data."""
        self.options_callback(self.index, action)

class MusicPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Music Player")
        self.geometry("900x550")
        ctk.set_appearance_mode("dark")

        self.playlist = []
        self.playlist_buttons = []
        self.current_index = 0

        self.is_playing = False
        self.is_paused = False

        self.is_dragging_slider = False
        self.position_offset = 0.0

        self.SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg")

        self.setup_ui()
        self.load_saved_folder()

    def setup_ui(self):
        # =====================================================================
        # MASTER SPLIT CONTAINERS
        # =====================================================================
        # Left Container (Takes up 60% width, 92% height to leave room for window margins)
        self.playlist_frame = ctk.CTkScrollableFrame(self, label_text="Playlist", label_font=("Arial", 16, "bold"), fg_color=GRAY, label_fg_color=LIGHT_GRAY)
        self.playlist_frame.place(relx=0.02, rely=0.04, relwidth=0.56, relheight=0.92)

        # Right Container (Takes up 40% width, 92% height)
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.place(relx=0.60, rely=0.04, relwidth=0.4, relheight=0.92)

        # =====================================================================
        # RIGHT SIDE UI ELEMENTS (Moved inside self.right_container)
        # =====================================================================

        # Album Art
        self.album_art_frame = ctk.CTkFrame(self.right_container, width=250, height=250, fg_color=GRAY)
        self.album_art_frame.pack(pady=20)
        
        self.art_label = ctk.CTkLabel(self.album_art_frame, text="🎵", font=("Arial", 80))
        self.art_label.place(relx=0.5, rely=0.5, anchor="center")

        # Song title label
        self.track_label = ctk.CTkLabel(self.right_container, text="No Folder Loaded", font=("Arial", 18, "bold"), wraplength=320, justify="center")
        self.track_label.pack(pady=(5, 0))

        self.artist_label = ctk.CTkLabel(self.right_container, text="", font=("Arial", 14))
        self.artist_label.pack(pady=(2, 5))

        # Progress slider
        self.slider = ctk.CTkSlider(self.right_container, from_=0, to=1000, number_of_steps=1000, command=self.slider_event)
        self.slider.pack(fill="x", padx=40, pady=(15, 2))
        self.slider.set(0)

        # Track length labels frame
        self.time_frame = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.time_frame.pack(fill="x", padx=40, pady=(0, 10)) # Matches the slider's horizontal span

        # Track length labels
        self.current_time_label = ctk.CTkLabel(self.time_frame, text="00:00", font=("Arial", 12))
        self.current_time_label.pack(side="left")

        self.total_time_label = ctk.CTkLabel(self.time_frame, text="00:00", font=("Arial", 12))
        self.total_time_label.pack(side="right")

        # Bind mouse press and release to manage the dragging state safely
        self.slider.bind("<Button-1>", self.on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        # Control buttons frame
        self.controls_frame = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.controls_frame.pack(pady=(10, 0))

        self.btn_prev = ctk.CTkButton(self.controls_frame, text="⏮", width=60, font=("Arial", 20), fg_color=BLUE, hover_color=HOVER_BLUE, command=self.prev_song)
        self.btn_prev.grid(row=0, column=0, padx=10)

        self.btn_play = ctk.CTkButton(self.controls_frame, text="▶", width=80, font=("Arial", 20), fg_color=BLUE, hover_color=HOVER_BLUE, command=self.toggle_play)
        self.btn_play.grid(row=0, column=1, padx=10)

        self.btn_next = ctk.CTkButton(self.controls_frame, text="⏭", width=60, font=("Arial", 20), fg_color=BLUE, hover_color=HOVER_BLUE, command=self.next_song)
        self.btn_next.grid(row=0, column=2, padx=10)

        # Load folder button
        self.btn_open = ctk.CTkButton(self.right_container, text="Open Music Folder", font=("Arial", 14), fg_color=BLUE, hover_color=HOVER_BLUE, command=self.open_folder)
        self.btn_open.pack(pady=(10, 0))

        # Start the slider update loop
        self.update_slider()

    def save_folder_path(self, folder_path):
        """Saves the selected folder path to a JSON file."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"last_folder": folder_path}, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_saved_folder(self):
        """Reads the JSON file and automatically scans the folder if it exists."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    saved_path = config.get("last_folder", "")
                    
                    # Ensure the folder still exists on the system
                    if saved_path and os.path.exists(saved_path):
                        self.process_folder(saved_path)
            except Exception as e:
                print(f"Error loading config: {e}")

    def open_folder(self):
        # Open a native directory selection dialog
        folder_path = filedialog.askdirectory(title="Select Music Folder")
        if folder_path:
            self.process_folder(folder_path)
            self.save_folder_path(folder_path)  # Save this path for next time

    def process_folder(self, folder_path):
        self.playlist = []
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(self.SUPPORTED_EXTENSIONS):
                full_path = os.path.join(folder_path, file)

                # Default fallbacks if metadata tags are completely missing
                title = os.path.splitext(file)[0]
                artist = "Unknown Artist"
                length = 100.0  # Safe fallback length in seconds

                try:
                    audio = mutagen.File(full_path)
                    if audio is not None:
                        # Extract Track Length
                        if audio.info is not None:
                            length = audio.info.length
                            
                        # Extract Artist & Title from Metadata Tags
                        if hasattr(audio, "tags") and audio.tags:
                            # Handling MP3 ID3 Tags
                            if "TIT2" in audio.tags:  # Title frame
                                title = audio.tags["TIT2"].text[0]
                            if "TPE1" in audio.tags:  # Artist frame
                                artist = audio.tags["TPE1"].text[0]
                        else:
                            # Handling OGG / FLAC Vorbis Comments
                            if "title" in audio:
                                title = audio["title"][0]
                            if "artist" in audio:
                                artist = audio["artist"][0]
                except Exception as e:
                    print(f"Error reading tags for {file}: {e}")

                # Save EVERYTHING directly into your playlist data dictionary structure
                self.playlist.append({
                    "title": title, 
                    "artist": artist, 
                    "path": full_path,
                    "length": length
                })
        
        if self.playlist:
            mixer.music.stop()
            self.position_offset = 0.0  
            self.is_playing = False
            self.is_paused = False
            self.btn_play.configure(text="▶")
            
            self.current_index = 0
            self.load_song()
        else:
            self.track_label.configure(text="No supported audio files found")
            self.artist_label.configure(text="")

        self.update_playlist_ui()

    def format_time(self, seconds):
        """Converts seconds into a string formatted as MM:SS."""
        if seconds is None or seconds < 0:
            return "00:00"
            
        minutes, secs = divmod(int(seconds), 60)
        return f"{minutes:02d}:{secs:02d}"

    def load_song(self):
        if self.playlist:
            song = self.playlist[self.current_index]

            self.track_label.configure(text=song["title"])
            self.artist_label.configure(text=song["artist"])
            self.current_time_label.configure(text="00:00")
            self.total_time_label.configure(text=self.format_time(song["length"]))

            if os.path.exists(song["path"]):
                mixer.music.load(song["path"])
                audio = mutagen.File(song["path"])
                if audio is not None and audio.info is not None:
                    self.slider.configure(to=audio.info.length)
                else:
                    self.slider.configure(to=100)

                self.slider.set(0)
                self.position_offset = 0.0  # Reset offset for the fresh track
                self.is_paused = False

                self.set_album_art(audio)
                self.highlight_current_song()

    def set_album_art(self, audio):
        """Extracts cover art from audio metadata and updates the UI."""
        img_data = None

        if audio is not None:
            # 1. Check for MP3 ID3 tags (APIC)
            if hasattr(audio, "tags") and audio.tags:
                if "APIC:" in audio.tags:
                    img_data = audio.tags["APIC:"].data
                else:
                    for key in audio.tags.keys():
                        if "APIC" in key:
                            img_data = audio.tags[key].data
                            break
            
            # 2. Check for FLAC / OGG / WAV Vorbis Comments
            if not img_data and hasattr(audio, "pictures") and audio.pictures:
                img_data = audio.pictures[0].data

        if img_data:
            try:
                # Convert raw bytes into a PIL Image
                pil_image = Image.open(io.BytesIO(img_data))
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(250, 250))
                
                # Apply the new image
                self.art_label.configure(image=ctk_image, text="")
                self.art_label.image = ctk_image  # Keep reference
                self.album_art_frame.configure(fg_color="transparent")  # Remove background frame color
            except Exception as e:
                print(f"Error rendering album art: {e}")
                self.set_default_art()
        else:
            self.set_default_art()

    def set_default_art(self):
        """Safely clears old images and falls back to the music emoji."""
        # Clean up the reference tracking variable
        if hasattr(self.art_label, "image"):
            self.art_label.image = None
            
        # Directly clear the underlying Tkinter widget's image property before telling CustomTkinter to swap back to text.
        self.art_label._label.configure(image="") 
        
        # Now update the CustomTkinter wrapper safely
        self.art_label.configure(image=None, text="🎵", font=("Arial", 80))
        self.album_art_frame.configure(fg_color=GRAY)

    def update_playlist_ui(self):
        """Clears the scrollable frame and redraws all track rows using the helper class."""
        # 1. Destroy old row components to clear memory references cleanly
        for row in self.playlist_buttons:
            row.destroy()
        self.playlist_buttons.clear()

        # 2. Rebuild the list with our custom PlaylistRow objects
        for index, song in enumerate(self.playlist):
            row = PlaylistRow(
                master=self.playlist_frame,
                index=index,
                title=song["title"],
                artist=song["artist"],
                click_callback=self.play_selected_song,
                options_callback=self.handle_track_options
            )
            row.pack(fill="x", pady=2, padx=5)
            self.playlist_buttons.append(row)
            
        # 3. Highlight the initial song right out of the gate
        self.highlight_current_song()

    def play_selected_song(self, index):
        """Triggered when a user clicks a song row directly in the playlist."""
        self.current_index = index
        self.is_playing = False
        self.load_song()
        self.toggle_play()

    def highlight_current_song(self):
        """Loops through UI rows and updates their visual selection state."""
        for row in self.playlist_buttons:
            # If the row matches our current playing index, give it the active highlight theme
            is_current = (row.index == self.current_index)
            row.set_active(is_current)

    def handle_track_options(self, index, action : core.TrackActions):
        """Routes the contextual menu actions for each track."""
        print(f"Track Index {index} requested action: {action}")
        
        match action:
            case core.TrackActions.ADD_TO_QUEUE:
                return
                
            case core.TrackActions.SAVE_TO_PLAYLIST:
                return

            case core.TrackActions.OPEN_IN_FOLDER:
                import subprocess
                track_path = self.playlist[index]["path"]
                safe_path = os.path.normpath(track_path)
                subprocess.Popen(f'explorer /select,"{safe_path}"')

    def toggle_play(self):
        if not self.playlist:
            return

        if not self.is_playing:
            if self.is_paused:
                mixer.music.unpause()
            else:
                mixer.music.play()
                self.position_offset = 0.0  # Reset on a brand new song start
            
            self.btn_play.configure(text="⏸")
            self.is_playing = True
            self.is_paused = False
        else:
            mixer.music.pause()
            self.btn_play.configure(text="▶")
            self.is_playing = False
            self.is_paused = True

    def next_song(self):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.is_playing = False
            self.load_song()
            self.toggle_play()

    def prev_song(self):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.is_playing = False
            self.load_song()
            self.toggle_play()

    def on_slider_press(self, event):
        """Triggered when the user clicks down on the slider."""
        self.is_dragging_slider = True
        if self.is_playing:
            self.toggle_play()

    def on_slider_release(self, event):
        """Triggered when the user lets go of the slider."""
        if self.playlist:
            new_pos = self.slider.get()

            if not self.is_playing:
                self.toggle_play()
            
            mixer.music.set_pos(new_pos)
            
            mixer.music.play(start=new_pos) 
            self.position_offset = new_pos
            
            # Maintain active playback visual state if we were already playing
            if not self.is_paused:
                self.is_playing = True
                self.btn_play.configure(text="⏸")

        self.is_dragging_slider = False

    def slider_event(self, value):
        """Triggered continuously while dragging the slider knob."""
        self.current_time_label.configure(text=self.format_time(value))  # Update current time label in real-time as slider moves

    def update_slider(self):
        if self.is_playing and not self.is_paused and not self.is_dragging_slider:
            # Calculate the current position by adding the offset (where the song started) to the elapsed time from mixer.music.get_pos()
            current_pos = self.position_offset + (mixer.music.get_pos() / 1000)
            
            # Prevent slider from exceeding track boundaries
            if current_pos <= self.slider.cget("to"):
                self.slider.set(current_pos)
                self.current_time_label.configure(text=self.format_time(current_pos))
            else:
                self.slider.set(self.slider.cget("to"))
                self.current_time_label.configure(text=self.format_time(self.slider.cget("to")))
                self.next_song()  # Jump to next track when song finishes
        
        self.after(10, self.update_slider)  # Schedule the next slider update

# Main routine
if __name__ == "__main__":
    app = MusicPlayer()
    app.mainloop()