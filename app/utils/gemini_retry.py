import time
import random
import logging

logger = logging.getLogger(__name__)

# Error codes/strings that indicate a transient, retryable condition
_RETRYABLE_CODES = {503, 429}
_RETRYABLE_STRINGS = ("unavailable", "resource_exhausted", "try again", "rate limit")


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception looks like a transient Gemini API error."""
    msg = str(exc).lower()
    # Check for numeric status codes embedded in the message
    for code in _RETRYABLE_CODES:
        if str(code) in str(exc):
            return True
    return any(s in msg for s in _RETRYABLE_STRINGS)


def call_with_retry(fn, *args, max_attempts: int = 3, base_delay: float = 10.0, **kwargs):
    """
    Call ``fn(*args, **kwargs)`` and retry up to ``max_attempts`` times on
    transient Gemini API errors (503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED).

    Back-off schedule (with ±20 % jitter):
        attempt 1 fails → wait ~10 s, retry
        attempt 2 fails → wait ~20 s, retry
        attempt 3 fails → raise

    Raises the last exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if not _is_retryable(exc):
                raise  # Non-transient — propagate immediately
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            jitter = delay * 0.2 * random.uniform(-1, 1)
            wait = delay + jitter
            print(
                f"  [Retry {attempt}/{max_attempts - 1}] Gemini returned transient error "
                f"({exc!s:.120}). Waiting {wait:.1f}s before retry..."
            )
            time.sleep(wait)

    raise last_exc
