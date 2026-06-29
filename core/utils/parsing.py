def safe_int(value, default=0):
    """
    Safely parse an integer from a string or other value.
    Returns the default if parsing fails.
    """
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default
