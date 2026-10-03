import time


class RateLimiter:
    def __init__(
        self,
        window_seconds: int,
        auth_limit: int,
        default_limit: int,
    ):
        self.window_seconds = window_seconds
        self.auth_limit = auth_limit
        self.default_limit = default_limit
        self.requests: dict[str, tuple[int, float]] = {}

    def _cleanup(self, now: float) -> None:
        expired_clients = [
            client_id
            for client_id, (_, window_start) in self.requests.items()
            if now - window_start >= self.window_seconds
        ]

        for client_id in expired_clients:
            del self.requests[client_id]

    def check(self, client_id: str, limit: int) -> tuple[bool, int]:
        now = time.monotonic()

        self._cleanup(now)

        if client_id not in self.requests:
            self.requests[client_id] = (1, now)
            return True, self.window_seconds

        count, window_start = self.requests[client_id]

        elapsed = now - window_start

        if count >= limit:
            retry_after = int(self.window_seconds - elapsed) + 1
            return False, retry_after

        self.requests[client_id] = (count + 1, window_start)

        return True, int(self.window_seconds - elapsed) + 1