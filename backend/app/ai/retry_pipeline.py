import asyncio
import random
import time
import logging
from enum import Enum
from typing import Callable, Any, Type, Tuple, Optional
from app.ai.guardrails import DomainPolicyViolationException

logger = logging.getLogger("ai_retry_pipeline")

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerOpenException(RuntimeError):
    """Exception raised when the circuit breaker is OPEN and blocking calls."""
    pass

class CircuitBreaker:
    """
    Circuit Breaker preventing cascade failures for external LLM API endpoints.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def check_state(self) -> None:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("CircuitBreaker transitioned to HALF_OPEN state.")
            else:
                raise CircuitBreakerOpenException("CircuitBreaker is OPEN. LLM API calls temporarily suspended.")

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"CircuitBreaker failure threshold ({self.failure_threshold}) reached. Circuit OPENed.")

class RetryPipeline:
    """
    Provider-Independent Retry Pipeline featuring Exponential Backoff,
    Full Jitter, Circuit Breaker integration, and non-retryable exception filtering.
    """
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.2,
        max_delay: float = 3.0,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

        # Non-retryable exceptions (client errors, domain guardrail violations)
        self.non_retryable_exceptions: Tuple[Type[BaseException], ...] = (
            DomainPolicyViolationException,
            ValueError,
            TypeError
        )

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        self.circuit_breaker.check_state()
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                res = await func(*args, **kwargs)
                self.circuit_breaker.record_success()
                return res
            except self.non_retryable_exceptions as e:
                # Do NOT retry non-retryable exceptions (e.g. Domain Guardrail violations)
                raise e
            except Exception as e:
                last_exception = e
                self.circuit_breaker.record_failure()

                if attempt == self.max_retries:
                    break

                # Exponential backoff with full jitter
                delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                jittered_delay = random.uniform(0, delay)

                logger.warning(
                    f"LLM Provider API Call failed on attempt {attempt + 1}/{self.max_retries + 1}. "
                    f"Retrying in {jittered_delay:.2f}s... Error: {str(e)}"
                )
                await asyncio.sleep(jittered_delay)

        raise last_exception

retry_pipeline = RetryPipeline()
