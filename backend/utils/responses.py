"""
Modern API response utilities with consistent structure and typing.
"""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .time_utils import now as harare_now


class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ApiResponse:
    """Standard API response structure."""
    status: str
    data: Any = None
    message: Optional[str] = None
    timestamp: str = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = harare_now().isoformat()

    @classmethod
    def success(cls, data: Any = None, message: str = "Operation successful") -> "ApiResponse":
        """Create a successful response."""
        return cls(
            status=ResponseStatus.SUCCESS.value,
            data=data,
            message=message
        )

    @classmethod
    def error(cls, message: str, data: Any = None) -> "ApiResponse":
        """Create an error response."""
        return cls(
            status=ResponseStatus.ERROR.value,
            data=data,
            message=message
        )

    @classmethod
    def warning(cls, message: str, data: Any = None) -> "ApiResponse":
        """Create a warning response."""
        return cls(
            status=ResponseStatus.WARNING.value,
            data=data,
            message=message
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ErrorResponse:
    """Enhanced error response with debugging information."""
    error: str
    message: str
    status_code: int
    timestamp: str = None
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = harare_now().isoformat()

    @classmethod
    def validation_error(cls, message: str, details: Dict[str, Any] = None) -> "ErrorResponse":
        """Create a validation error response."""
        return cls(
            error="ValidationError",
            message=message,
            status_code=400,
            details=details
        )

    @classmethod
    def not_found(cls, resource: str = "Resource") -> "ErrorResponse":
        """Create a not found error response."""
        return cls(
            error="NotFound",
            message=f"{resource} not found",
            status_code=404
        )

    @classmethod
    def unauthorized(cls, message: str = "Authentication required") -> "ErrorResponse":
        """Create an unauthorized error response."""
        return cls(
            error="Unauthorized",
            message=message,
            status_code=401
        )

    @classmethod
    def forbidden(cls, message: str = "Insufficient permissions") -> "ErrorResponse":
        """Create a forbidden error response."""
        return cls(
            error="Forbidden",
            message=message,
            status_code=403
        )

    @classmethod
    def rate_limit_exceeded(cls, retry_after: int = None) -> "ErrorResponse":
        """Create a rate limit error response."""
        details = {"retry_after": retry_after} if retry_after else None
        return cls(
            error="RateLimitExceeded",
            message="Too many requests",
            status_code=429,
            details=details
        )

    @classmethod
    def internal_error(cls, message: str = "Internal server error") -> "ErrorResponse":
        """Create an internal server error response."""
        return cls(
            error="InternalError",
            message=message,
            status_code=500
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PaginatedResponse:
    """Paginated response structure."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None

    @classmethod
    def from_pagination(cls, pagination, items: List[Any]) -> "PaginatedResponse":
        """Create paginated response from Flask-SQLAlchemy pagination object."""
        return cls(
            items=items,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pagination.pages,
            has_next=pagination.has_next,
            has_prev=pagination.has_prev,
            next_page=pagination.next_num if pagination.has_next else None,
            prev_page=pagination.prev_num if pagination.has_prev else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert paginated response to dictionary."""
        return asdict(self)


def create_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    headers: Dict[str, str] = None
):
    """
    Create a standardized Flask response.

    Args:
        data: Response data
        message: Response message
        status_code: HTTP status code
        headers: Additional headers

    Returns:
        Flask response object
    """
    from flask import jsonify, make_response

    response = ApiResponse.success(data=data, message=message)
    flask_response = make_response(jsonify(response.to_dict()), status_code)

    # Add any custom headers
    if headers:
        for key, value in headers.items():
            flask_response.headers[key] = value

    return flask_response


def create_error_response(
    error: str,
    message: str,
    status_code: int = 400,
    details: Dict[str, Any] = None,
    headers: Dict[str, str] = None
):
    """
    Create a standardized error response.

    Args:
        error: Error type
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        headers: Additional headers

    Returns:
        Flask response object
    """
    from flask import jsonify, make_response

    error_response = ErrorResponse(
        error=error,
        message=message,
        status_code=status_code,
        details=details
    )
    flask_response = make_response(jsonify(error_response.to_dict()), status_code)

    # Add any custom headers
    if headers:
        for key, value in headers.items():
            flask_response.headers[key] = value

    return flask_response
