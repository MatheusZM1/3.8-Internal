import customtkinter as ctk
import core

CONFIG_FILE = "config.json"
WHITE = "#ffffff"
VERY_LIGHT_GRAY = "#d9d9d9"
LIGHT_GRAY = "#565656"
GRAY = "#2b2b2b"
DARK_GRAY = "#242424"
BLACK = "#000000"
BLUE = "#1a6faf"
HOVER_BLUE = "#145a86"

class TrackRow(ctk.CTkFrame):
    def __init__(self, master, index, title, artist, click_callback, options_callback, queue_row=False):
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
        self.queue_row = queue_row

        self.index_label = ctk.CTkLabel(self, text=f"{index + 1}", font=("Arial", 13), text_color=VERY_LIGHT_GRAY, width=10, anchor="w")
        self.index_label.pack(side="left", padx=(10, 0))

        # Truncate title and artist names if they exceed character limits
        truncated_title = core.truncate_text(title, max_chars=40)
        truncated_artist = core.truncate_text(artist, max_chars=40)
        
        display_text = f"{truncated_title}\n{truncated_artist}".strip()

        # Setup the text label
        self.label = ctk.CTkLabel(
            self,
            text=display_text,
            font=("Arial", 13),
            text_color=WHITE,
            anchor="w",
            justify="left"
        )
        # fill="both" and expand=True ensures the invisible text bounding box spans the remaining width, keeping the entire left side clickable
        self.label.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # Options button
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

        # Bind mouse interactions to the row container, index and text labels
        for widget in (self, self.index_label, self.label):
            widget.bind("<Enter>", self.on_hover)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_click)
            widget.bind("<Button-3>", self.show_options_menu)

        self.btn_options.bind("<Enter>", self.on_options_hover)
        self.btn_options.bind("<Leave>", self.on_options_leave)

        self.is_active_song = False

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
        if self.winfo_exists():
            try:
                self.index_label.configure(text=f"{self.index + 1}")
            except Exception:
                pass

    def show_options_menu(self, event=None):
        """Creates a borderless dropdown menu."""

        # Create a top-level popup window
        menu = ctk.CTkToplevel(self)
        menu.withdraw() # Hide it instantly while configuring layout
        menu.overrideredirect(True) # Completely kills the OS title bar and native borders

        # Apply styling
        menu.configure(fg_color=DARK_GRAY, corner_radius=6 )

        # Dropdown options
        if self.queue_row:
            options = [
                ("Remove from queue", core.TrackActions.REMOVE_FROM_QUEUE),
                ("Save to a playlist", core.TrackActions.SAVE_TO_PLAYLIST),
                ("Open in folder", core.TrackActions.OPEN_IN_FOLDER)
            ]
        else:
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
                # Determine the widget which is focused, and if it lives in the menu, do not close yet
                next_focus = menu.focus_get()
                if next_focus and next_focus.master == menu:
                    return
                
                # Use after_idle so any click commands on the menu buttons register before the window vanishes
                menu.after_idle(lambda: menu.destroy() if menu.winfo_exists() else None)

        menu.bind("<FocusOut>", safe_close)

    def handle_option(self, action : core.TrackActions):
        """Route the clicked option's event data."""
        self.options_callback(self.index, action)