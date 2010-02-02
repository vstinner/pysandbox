def _safe_open(open):
    def safe_open(filename, mode='r', buffering=0):
        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")
        return open(filename, mode, buffering)
    return safe_open

safe_open = _safe_open(open)

