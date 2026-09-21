"""
Custom exception classes and global exception handlers.
All API errors return consistent JSON error responses.
"""
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


# ─── Custom Exception Classes ─────────────────────────────────────────────────

class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "APP_ERROR",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.extra = extra or {}
        super().__init__(detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, "UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Permission denied") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, "FORBIDDEN")


class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource", detail: str | None = None) -> None:
        msg = detail or f"{resource} not found"
        super().__init__(status.HTTP_404_NOT_FOUND, msg, "NOT_FOUND")


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, "CONFLICT")


class ValidationException(AppException):
    def __init__(self, detail: str, errors: list | None = None) -> None:
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail,
            "VALIDATION_ERROR",
            {"errors": errors or []},
        )


class ServiceUnavailableException(AppException):
    def __init__(self, service: str = "External service", detail: str | None = None) -> None:
        msg = detail or f"{service} is currently unavailable"
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, msg, "SERVICE_UNAVAILABLE")


class LLMUnavailableException(ServiceUnavailableException):
    def __init__(self, detail: str = "LLM service is unavailable") -> None:
        super().__init__("LLM", detail)


class InsufficientDataException(AppException):
    def __init__(self, detail: str = "Insufficient data for this operation") -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, "INSUFFICIENT_DATA")


# ─── Error Response Builder ───────────────────────────────────────────────────

def _error_response(
    status_code: int,
    error_code: str,
    detail: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "success": False,
        "error": {"code": error_code, "message": detail},
    }
    if extra:
        content["error"]["details"] = extra
    return JSONResponse(status_code=status_code, content=content)


# ─── Exception Handlers ───────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application exception",
            extra={
                "error_code": exc.error_code,
                "path": request.url.path,
                "detail": exc.detail,
            },
        )
        return _error_response(exc.status_code, exc.error_code, exc.detail, exc.extra or None)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        logger.debug("Request validation error", extra={"errors": errors, "path": request.url.path})
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Request validation failed",
            {"errors": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception",
            extra={"path": request.url.path, "method": request.method},
        )
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "An unexpected error occurred",
        )
