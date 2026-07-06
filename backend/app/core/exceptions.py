"""Domain exceptions mapped to the standard API error envelope.

See docs/REST_API.md for the response format these translate to.
"""
from __future__ import annotations


class EchoBaseError(Exception):
    """Base class for errors that should surface as a structured API error."""

    status_code: int = 400
    code: str = "ERROR"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(EchoBaseError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(EchoBaseError):
    status_code = 409
    code = "CONFLICT"


class ValidationAppError(EchoBaseError):
    status_code = 422
    code = "VALIDATION_ERROR"


class AuthenticationError(EchoBaseError):
    status_code = 401
    code = "UNAUTHENTICATED"


class AuthorizationError(EchoBaseError):
    status_code = 403
    code = "FORBIDDEN"
