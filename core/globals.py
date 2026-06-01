from enum import Enum, auto

class TrackActions(Enum):
    """Enum for track action types."""
    ADD_TO_QUEUE = auto()
    SAVE_TO_PLAYLIST = auto()
    OPEN_IN_FOLDER = auto()