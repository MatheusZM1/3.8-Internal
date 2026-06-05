def truncate_text(text, max_chars):
    """Helper method to slice string and append an ellipsis if it's too long."""
    if len(text) > max_chars:
        return text[:max_chars - 3].strip() + "..."
    return text