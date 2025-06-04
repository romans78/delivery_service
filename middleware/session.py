import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def is_valid_uuid(value: str):
    """
        Validates whether a string is a properly formatted UUID.

        This function checks if the input string conforms to the UUID format.

        Args:
            value (str): The string to validate as UUID

        Returns:
            bool: True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class SessionMiddleware(BaseHTTPMiddleware):
    """
        Middleware for session management using UUID-based session identifiers.
    """
    async def dispatch(self, request: Request, call_next):
        """
            Process incoming request and attach session management.

            Args:
                request (Request): The incoming request
                call_next (Callable): The next middleware/handler in a chain

            Returns:
                Response: The processed response with session identifiers
        """
        session_id = (
                request.headers.get('X-Session-ID') or
                request.cookies.get('session_id') or
                request.query_params.get('session_id')
        )
        if not session_id or not is_valid_uuid(session_id):
            session_id = str(uuid.uuid4())

        request.state.session_id = session_id

        response = await call_next(request)

        response.set_cookie(
            key='session_id',
            value=session_id,
            httponly=True,
            max_age=30 * 24 * 60 * 60,
            samesite='lax'
        )
        response.headers['X-Session-ID'] = session_id

        return response
