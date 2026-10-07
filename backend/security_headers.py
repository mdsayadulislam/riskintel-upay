"""
RiskIntel upay - Production Security Headers Middleware
File: backend/security_headers.py

Enforces defensive HTTP response headers to protect against clickjacking,
MIME sniffing, XSS, and unencrypted transport vulnerabilities.
Injects correlation request IDs (X-Request-ID) into every transaction.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.config import IS_PRODUCTION


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Starlette middleware injecting security headers into all HTTP responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or propagate correlation request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        # Store in request state for downstream handlers and audit logging
        request.state.request_id = request_id

        response: Response = await call_next(request)

        # Injected Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Standard Content Security Policy for API Services
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
        )

        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Prevent browser/proxy caching on API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response

