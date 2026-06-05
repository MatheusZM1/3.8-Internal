def truncate_text(text, max_chars):
    """Helper method to slice string and append an ellipsis if it's too long."""
    if len(text) > max_chars:
        return text[:max_chars - 3].strip() + "..."
    return text

def format_time(seconds):
    """Converts seconds into a string formatted as MM:SS."""
    if seconds is None or seconds < 0:
        return "00:00"
    
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"