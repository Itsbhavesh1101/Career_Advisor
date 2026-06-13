from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


def _trace_id_for_request(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        return str(trace_id)
    generated = uuid4().hex
    request.state.trace_id = generated
    return generated


async def attach_trace_id_middleware(request: Request, call_next):
    trace_id = _trace_id_for_request(request)
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    trace_id: str,
    details: object | None = None,
) -> JSONResponse:
    payload: dict[str, object] = {
        "error": {
            "code": code,
            "message": message,
            "trace_id": trace_id,
        }
    }
    if details is not None:
        payload["error"]["details"] = details  # type: ignore[index]
    return JSONResponse(status_code=status_code, content=payload)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    trace_id = _trace_id_for_request(request)
    detail = exc.detail
    if isinstance(detail, str):
        message = detail
        details = None
    else:
        message = "Request failed"
        details = detail
    return _error_response(
        status_code=exc.status_code,
        code="http_error",
        message=message,
        trace_id=trace_id,
        details=details,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    trace_id = _trace_id_for_request(request)
    return _error_response(
        status_code=422,
        code="validation_error",
        message="Invalid request payload.",
        trace_id=trace_id,
        details=exc.errors(),
    )


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    trace_id = _trace_id_for_request(request)
    return _error_response(
        status_code=429,
        code="rate_limited",
        message="Too many requests. Please retry later.",
        trace_id=trace_id,
        details={"limit": str(exc.detail)},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = _trace_id_for_request(request)
    logger.exception("Unhandled API error trace_id=%s", trace_id)
    return _error_response(
        status_code=500,
        code="internal_error",
        message="Unexpected server error.",
        trace_id=trace_id,
    )
