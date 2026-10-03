from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.rate_limiter import RateLimiter


class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

        self.rate_limiter = RateLimiter(
            window_seconds=settings.rate_limit_window_seconds,
            auth_limit=settings.rate_limit_auth,
            default_limit=settings.rate_limit_default,
        )

    async def dispatch(self, request: Request, call_next):
        client_id = request.client.host

        if request.url.path.startswith("/api/v1/auth/"):
            limit = settings.rate_limit_auth
        else:
            limit = settings.rate_limit_default

        allowed, retry_after = self.rate_limiter.check(
            client_id,
            limit,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)