from enum import Enum, auto
import json
import io
import os
import mutagen
import customtkinter as ctk
from PIL import Image

CONFIG_FILE = "config.json"

class ConfigSettings:
    def __init__(self):
        self.last_folder = ""
        self.last_playlist = ""
        self.last_open = ""
        self.load()

    def load(self):
        """Loads configuration from JSON into class attributes."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.last_folder = data.get("last_folder", "")
                    self.last_playlist = data.get("last_playlist", "")
                    self.last_open = data.get("last_open", "")
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        """Saves current class attributes back to JSON."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(
                    {
                        "last_folder": self.last_folder,
                        "last_playlist": self.last_playlist,
                        "last_open": self.last_open,
                    },
                    f,
                    indent=4,
                )
        except Exception as e:
            print(f"Error saving config: {e}")

    def set_folder(self, folder_path):
        """Updates last_folder and saves state."""
        self.last_folder = folder_path
        self.last_open = "folder"
        self.save()

    def set_playlist(self, playlist_path):
        """Updates last_playlist and saves state."""
        self.last_playlist = playlist_path
        self.last_open = "playlist"
        self.save()

class TrackRowType(Enum):
    """Enum for track row types."""
    QUEUE = auto()
    VIEW_ONLY = auto()
    PLAYLIST_EXCLUSIVE_VIEW_ONLY = auto()

class TrackActions(Enum):
    """Enum for track action types."""
    PLAY_NEXT = auto()
    ADD_TO_QUEUE = auto()
    REMOVE_FROM_QUEUE = auto()
    SAVE_TO_PLAYLIST = auto()
    OPEN_IN_FOLDER = auto()
    REMOVE_FROM_PLAYLIST = auto()

class PlaylistActions(Enum):
    """Enum for playlist action types."""
    LOAD = auto()
    VIEW = auto()
    CHANGE_COVER = auto()
    RESET_COVER = auto()
    RENAME = auto()
    DELETE = auto()
    ADD_REMOVE_TRACK = auto()

def open_in_folder(path):
    """Opens the folder containing the specified file in the system's file explorer."""
    import subprocess
    safe_path = os.path.normpath(path)
    subprocess.Popen(f'explorer /select,"{safe_path}"')

def load_image(path, size):
    """Loads a normal image file and converts it into a CustomTkinter image."""
    try:
        pil_image = Image.open(path)
        pil_image = pil_image.convert("RGBA")

        return ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=size
        )

    except Exception as e:
        print(f"Error loading image '{path}': {e}")
        return None

def load_album_art(path, size):
    """
    Loads embedded album art from an audio file.

    Args:
        path: Path to the audio file.
        size: (width, height) tuple.

    Returns:
        CTkImage if artwork exists, otherwise None.
    """
    try:
        audio = mutagen.File(path)
        if audio is None:
            return None

        img_data = None

        # MP3 (ID3 APIC)
        if hasattr(audio, "tags") and audio.tags:
            if "APIC:" in audio.tags:
                img_data = audio.tags["APIC:"].data
            else:
                for key in audio.tags.keys():
                    if "APIC" in key:
                        img_data = audio.tags[key].data
                        break

        # FLAC / OGG
        if img_data is None and hasattr(audio, "pictures") and audio.pictures:
            img_data = audio.pictures[0].data

        if img_data is None:
            return None

        image = Image.open(io.BytesIO(img_data))
        return ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=size
        )

    except Exception as e:
        return None