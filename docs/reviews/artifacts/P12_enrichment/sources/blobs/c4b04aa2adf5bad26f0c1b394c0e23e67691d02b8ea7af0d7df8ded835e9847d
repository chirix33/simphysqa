"""Provider-independent settings and sanitized failures for P02b.

Adapters must report usage even for refused/malformed responses, disable hidden
SDK retries, and accept only the explicitly supplied public request. No adapter
or model download is selected by these contracts.
"""
from dataclasses import asdict, dataclass
from enum import StrEnum
import math
from typing import Protocol

from phi_jepa.artifacts import digest


class FailureCode(StrEnum):
    REFUSAL = 'refusal'
    MALFORMED_JSON = 'malformed_json'
    INCOMPLETE_JSON = 'incomplete_json'
    MISSING_BINDING = 'missing_binding'
    INCOMPATIBLE_UNITS = 'incompatible_units'
    TIMEOUT = 'timeout'
    MISSING_CREDENTIALS = 'missing_credentials'
    RETRY_EXHAUSTED = 'retry_exhausted'
    OVERLENGTH = 'overlength'
    INVALID_OUTPUT = 'invalid_output'
    CACHE_INTEGRITY = 'cache_integrity'
    BUDGET_EXHAUSTED = 'budget_exhausted'
    PROVIDER_UNAVAILABLE = 'provider_unavailable'
    RATE_LIMIT = 'rate_limit'
    TRANSPORT = 'transport'


class ProviderFailure(RuntimeError):
    """Never copy provider exceptions, URLs, credentials or raw payloads here."""
    def __init__(self, code: FailureCode, *, cause: FailureCode | None = None):
        self.code = code
        self.cause = cause
        super().__init__(code.value)


def positive_int(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f'{name} must be a positive integer')


@dataclass(frozen=True)
class EncoderSettings:
    provider: str
    model: str
    model_revision: str
    tokenizer_revision: str
    implementation_revision: str
    pooling: str
    max_length: int
    precision: str
    normalization: str
    embedding_width: int
    mode: str  # fixture or local; fixtures can never impersonate selected models

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name not in ('max_length', 'embedding_width') and (
                    not isinstance(value, str) or not value.strip() or value in ('main', 'latest')):
                raise ValueError(f'explicit pinned setting required: {name}')
        for name in ('max_length', 'embedding_width'):
            positive_int(getattr(self, name), name)
        if self.mode not in ('fixture', 'local'):
            raise ValueError('explicit encoder mode required')

    @property
    def sha256(self):
        return digest(asdict(self))


class FrozenEncoderBackend(Protocol):
    """Token IDs include special tokens. Implementations must never truncate.

    encode_tokens runs frozen/eval, returns one finite vector, and performs no
    implicit network operations. The exact tokenizer/model/preprocessing is
    bound by settings. Real adapters still require model-specific validation.
    """
    settings: EncoderSettings

    def tokenize(self, text: str) -> tuple[int, ...]: ...
    def encode_tokens(self, tokens: tuple[int, ...]) -> tuple[float, ...]: ...


@dataclass(frozen=True)
class Usage:
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None

    def __post_init__(self):
        for value in (self.input_tokens, self.output_tokens):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('invalid usage')
        if self.cost_usd is not None and (type(self.cost_usd) not in (int, float)
                or not math.isfinite(self.cost_usd) or self.cost_usd < 0):
            raise ValueError('invalid cost')


@dataclass(frozen=True)
class AttemptResult:
    usage: Usage
    text: str | None = None
    failure: FailureCode | None = None

    def __post_init__(self):
        if (self.text is None) == (self.failure is None):
            raise ValueError('exactly one of response text or typed failure is required')
