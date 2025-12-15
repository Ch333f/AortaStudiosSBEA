import time


def server_time() -> float:
    """
    Server-authoritative UTC time (seconds).
    """
    return time.time()
