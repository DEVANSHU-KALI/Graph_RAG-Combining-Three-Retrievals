# backend/core/middleware.py

import time

from backend.core.logging import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Start timer
        start_time = time.time()

        # Log incoming request
        logger.info(f"{request.method} request received at {request.url.path}")

        # Process request
        response = await call_next(request)

        # Calculate execution time
        process_time = time.time() - start_time

        # Log response status and execution time
        logger.info(
            f"{request.method} {request.url.path} "
            f"completed with status code {response.status_code} "
            f"in {process_time:.4f} seconds"
        )

        return response
