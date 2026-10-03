"""Bounded, auditable attempt mechanics; no transport or hidden retries.

This is an offline-testable building block, not a live-call authorization gate.
An eventual adapter must enforce its separately configured token/spend budget
before dispatch. Missing usage remains unknown, never a measured zero.
"""
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Callable

from .contracts import AttemptResult, FailureCode, ProviderFailure, Usage, positive_int


@dataclass(frozen=True)
class AttemptPolicy:
    max_attempts_per_request: int
    max_total_attempts: int
    timeout_seconds: float

    def __post_init__(self):
        positive_int(self.max_attempts_per_request, 'max_attempts_per_request')
        positive_int(self.max_total_attempts, 'max_total_attempts')
        import math
        if type(self.timeout_seconds) not in (int, float) or not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError('finite positive timeout required')


class AttemptRunner:
    def __init__(self, policy: AttemptPolicy, *, event_sink=None):
        self.policy = policy
        self.events = []
        self.event_sink = event_sink

    def run(self, request_sha256: str, operation: Callable[[float], AttemptResult], validate):
        """Operation honors supplied timeout; only typed transport timeouts retry.

        Content failures are recorded once and never repaired. Adapter exceptions
        are sanitized and accounted, including unreported usage on timeouts.
        """
        for index in range(self.policy.max_attempts_per_request):
            if len(self.events) >= self.policy.max_total_attempts:
                raise ProviderFailure(FailureCode.BUDGET_EXHAUSTED)
            started = perf_counter()
            event = {'request_sha256': request_sha256, 'attempt': index + 1,
                     'failure': None, 'usage': asdict(Usage(None, None, None))}
            # Reserve before dispatch, including calls that fail or are interrupted.
            self.events.append(event)
            if self.event_sink is not None:
                self.event_sink()
            try:
                result = operation(self.policy.timeout_seconds)
                if not isinstance(result, AttemptResult):
                    raise ProviderFailure(FailureCode.INVALID_OUTPUT)
                event['usage'] = asdict(result.usage)
                if result.failure is not None:
                    raise ProviderFailure(result.failure)
                value = validate(result.text)
            except TimeoutError:
                event['failure'] = FailureCode.TIMEOUT.value
            except ProviderFailure as exc:
                event['failure'] = exc.code.value
                if exc.code != FailureCode.TIMEOUT:
                    raise
            except Exception:
                event['failure'] = FailureCode.INVALID_OUTPUT.value
                raise ProviderFailure(FailureCode.INVALID_OUTPUT) from None
            finally:
                event['wall_seconds'] = perf_counter() - started
                if self.event_sink is not None:
                    self.event_sink()
            if event['failure'] is None:
                return value
        raise ProviderFailure(FailureCode.RETRY_EXHAUSTED, cause=FailureCode.TIMEOUT)
