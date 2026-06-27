import os
import random
from pygame import mixer

class PlaybackEngine:
    def __init__(self):
        # Initialize the audio mixer inside the engine
        mixer.init()
        
        self.playlist = []
        self.queue = []
        self.current_index = 0

        self.active_track = None
        self.playing_from_queue = False
        self.queue_head_removed = False

        self.is_playing = False
        self.is_paused = False
        self.is_looping = False
        self.is_shuffling = False
        self.position_offset = 0.0

        self.slider_volume = 1.0
        self.is_muted = False

    def set_playlist(self, playlist, start_index=0):
        """Populates the engine's playlist and resets the tracking states."""
        self.playlist = playlist
        self.current_index = start_index if playlist else 0
        self.stop()

    @property
    def current_track(self):
        """Returns the dictionary data of the currently loaded track."""
        return self.active_track

    def load_track(self, track=None):
        """
        Loads the a track file into the mixer without playing it yet.
        If a track argument is not provided, load the track at the current index in the playlist.
        """
        if track is not None:
            self.active_track = track
        else:
            if self.playlist and 0 <= self.current_index < len(self.playlist):
                self.active_track = self.playlist[self.current_index]
            else:
                self.active_track = None

        if self.active_track and os.path.exists(self.active_track["path"]):
            mixer.music.load(self.active_track["path"])
            self.position_offset = 0.0
            self.is_paused = False
            return self.active_track
        return None

    def toggle_play(self):
        """Toggles play/pause states. Returns True if playing, False if paused."""
        if not self.active_track:
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
    
    def toggle_loop(self):
        """Toggles looping on/off."""
        self.is_looping = not self.is_looping

    def toggle_shuffle(self):
        """Toggles shuffle on/off. When shuffle is turned on, the playlist order is randomized."""
        self.is_shuffling = not self.is_shuffling

    def next_track(self):
        """Cycles forward. Automatically checks from the queue first."""        
        if self.is_looping:
            self.stop()
            self.load_track()
            self.toggle_play()
            return self.current_track

        if self.playing_from_queue and self.queue:
            if not self.queue_head_removed:
                self.queue.pop(0)
            self.playing_from_queue = False
            self.queue_head_removed = False

        if self.queue:
            # Pull the new first item off the top of the queue
            next_up = self.queue[0]
            self.playing_from_queue = True
            self.current_index = 0
            self.is_playing = False
            self.load_track(track=next_up)
            self.toggle_play()
        elif self.playlist:
            # Shuffle or standard playlist progression loop
            if self.is_shuffling:
                while True:                    
                    random_index = random.randint(0, len(self.playlist) - 1)
                    if random_index != self.current_index and len(self.playlist) > 1:  # Avoid repeating the same track when shuffling
                        break
                self.current_index = random_index
            else:
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
        if self.active_track:
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
    
    def mute(self):
        """Mutes the audio."""
        mixer.music.set_volume(0.0)
        self.is_muted = True

    def unmute(self):
        """Unmutes the audio."""
        mixer.music.set_volume(self.slider_volume)
        self.is_muted = False