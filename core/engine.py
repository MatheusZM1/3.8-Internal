import os
from pygame import mixer

class PlaybackEngine:
    def __init__(self):
        # Initialize the audio mixer inside the engine
        mixer.init()
        
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.position_offset = 0.0

    def set_playlist(self, playlist, start_index=0):
        """Populates the engine's playlist and resets the tracking states."""
        self.playlist = playlist
        self.current_index = start_index if playlist else 0
        self.stop()

    @property
    def current_track(self):
        """Returns the dictionary data of the currently active track."""
        if self.playlist and 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def load_track(self):
        """Loads the current track file into the mixer without playing it yet."""
        track = self.current_track
        if track and os.path.exists(track["path"]):
            mixer.music.load(track["path"])
            self.position_offset = 0.0
            self.is_paused = False
            return track
        return None

    def toggle_play(self):
        """Toggles play/pause states. Returns True if playing, False if paused."""
        if not self.playlist:
            return False

        if not self.is_playing:
            if self.is_paused:
                mixer.music.unpause()
            else:
                # Brand new playback start
                mixer.music.play()
                self.position_offset = 0.0
            
            self.is_playing = True
            self.is_paused = False
        else:
            mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
            
        return self.is_playing

    def next_track(self):
        """Cycles to the next index and plays it."""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.is_playing = False
            self.load_track()
            self.toggle_play()
        return self.current_track

    def prev_track(self):
        """Cycles to the previous index and plays it."""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.is_playing = False
            self.load_track()
            self.toggle_play()
        return self.current_track

    def seek(self, position):
        """Jumps to a specific timestamp in seconds and updates offsets."""
        if self.playlist:
            mixer.music.play(start=position)
            self.position_offset = position
            
            # If the track was paused when dragged, match that execution state
            if self.is_paused:
                mixer.music.pause()
                self.is_playing = False
            else:
                self.is_playing = True

    def stop(self):
        """Hard stops playback and completely resets positional memory."""
        mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.position_offset = 0.0

    def get_current_position(self):
        """
        Calculates the real-time position. 
        Returns current time in seconds, or -1 if the song ended/errored out.
        """
        if not self.is_playing and not self.is_paused:
            return 0.0
            
        mixer_time = mixer.music.get_pos()
        if mixer_time == -1:
            return -1  # Signal to the UI loop that the track naturally finished
            
        return self.position_offset + (mixer_time / 1000.0)