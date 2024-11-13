from aiohttp import ClientSession


session = None

def init_session():
    global session
    session = ClientSession()


def get_session() -> ClientSession:
    """Get the global session from the app state."""
    global session
    if session is None:
        session = ClientSession()
    return session  # Return the session
