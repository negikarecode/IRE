import time
import asyncio

class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter per integration connector endpoint.
    """
    def __init__(self, max_tokens: int = 100, refill_rate_per_sec: float = 10.0):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(max_tokens)
        self.last_refill = time.time()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + (elapsed * self.refill_rate))
        self.last_refill = now

    async def acquire(self) -> bool:
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False
