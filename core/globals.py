from enum import Enum, auto

class TrackActions(Enum):
    """Enum for track action types."""
    ADD_TO_QUEUE = auto()
    REMOVE_FROM_QUEUE = auto()
    SAVE_TO_PLAYLIST = auto()
    REMOVE_FROM_MIX = auto()
    OPEN_IN_FOLDER = auto()
    REMOVE_FROM_PLAYLIST = auto()

class PlaylistActions(Enum):
    """Enum for playlist action types."""
    LOAD = auto()
    VIEW = auto()
    RENAME = auto()
    DELETE = auto()