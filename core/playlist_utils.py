import os
import json

class Playlist:
    def __init__(self, name="Untitled"):
        self.name = name
        self.art_path = None
        self.tracks = []

    def add_track(self, track_data):
        self.tracks.append(track_data)

    def remove_track(self, index):
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)

    def is_populated(self):
        return len(self.tracks) > 0
    
    @property
    def population(self):
        return len(self.tracks)

    def save(self, filepath):
        data = {
            "name": self.name,
            "art_path": self.art_path,
            "tracks": self.tracks
        }

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving playlist: {e}")

    @classmethod
    def load(cls, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading playlist: {e}")
            return None

        playlist = cls(name=data.get("name", "Untitled"))
        playlist.art_path = data.get("art_path", None)
        playlist.tracks = data.get("tracks", [])
        return playlist