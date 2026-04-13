from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

rate_limiter = Limiter(key_func=get_remote_address)


def rate_limit(limit_string: str):
    """Dependency-based rate limit decorator."""
    return rate_limiter.limit(limit_string)
