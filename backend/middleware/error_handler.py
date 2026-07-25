"""Global exception handling.

Catches anything not already handled at the route level so the API
never leaks a raw traceback to a client, per the security mandate
in Part 2 ("Never expose stack traces").

IMPORTANT: FastAPI's built-in HTTPException handler is bypassed when
you register a bare `Exception` handler. We must explicitly re-register
the HTTPException handler FIRST so that route-level 401/409/etc. responses
are returned correctly and are not swallowed by the catch-all 500 handler.
"""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse

from core.exceptions import WingmanError

logger = logging.getLogger("wingman")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Re-register FastAPI's default HTTPException handler.

        Without this, the generic Exception handler below intercepts all
        HTTPException instances (including 401 from auth routes) and
        returns 500 instead of the intended status code.
        """
        return await http_exception_handler(request, exc)

    @app.exception_handler(WingmanError)
    async def handle_domain_error(_: Request, exc: WingmanError) -> JSONResponse:
        logger.warning("Domain error: %s", exc)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"},
        )
