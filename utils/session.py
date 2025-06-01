from fastapi import Request, Depends, HTTPException

def get_session_id(request: Request) -> str:
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        raise HTTPException(400, detail="Session ID is missing")
    return session_id