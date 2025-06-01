import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def is_valid_uuid(value: str):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = (
                request.headers.get("X-Session-ID") or
                request.cookies.get("session_id") or
                request.query_params.get("session_id")
        )
        if not session_id or not is_valid_uuid(session_id):
            session_id = str(uuid.uuid4())

        request.state.session_id = session_id

        response = await call_next(request)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=30 * 24 * 60 * 60,
            samesite="lax"
        )
        response.headers["X-Session-ID"] = session_id

        return response
