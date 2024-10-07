from fastapi import HTTPException

from aiohttp import ClientSession


session = None

def init_session():
    global session
    session = ClientSession()


async def get_session() -> ClientSession:
    """Get the global session from the app state."""
    global session
    if session is None:
        raise HTTPException(status_code=500, detail="Session not initialized.")
    return session  # Return the session
