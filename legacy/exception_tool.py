def try_pass(func):
    """Try and pass if exception incurs"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            return None
    return wrapper