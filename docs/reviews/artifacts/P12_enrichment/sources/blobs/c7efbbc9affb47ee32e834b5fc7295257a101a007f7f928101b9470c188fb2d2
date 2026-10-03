"""Complete public serialization, strict note parsing and frozen E caching.

Free-text notes can be structurally validated, not certified true or answer-free
by a JSON validator. Live enrichment and its semantic qualification remain gated.
No unknown-slot filling or extraction is implicitly enabled by this module.
"""
from dataclasses import asdict, dataclass
import math

from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import PublicProblem, enriched_context, validate_enrichment
from phi_jepa.integration.readers import strict_json
from .contracts import FailureCode, FrozenEncoderBackend, ProviderFailure


def parse_notes(problem: PublicProblem, response: str):
    """Provider returns notes only; original input is reconstructed by us.

    No provider can replace leaves, units, IDs, list membership or numeric slots.
    The returned envelope is compatible with the existing P02a reader.
    """
    try:
        result = strict_json(response)
    except (ValueError, TypeError):
        raise ProviderFailure(FailureCode.MALFORMED_JSON) from None
    if not isinstance(result, dict) or 'notes' not in result:
        raise ProviderFailure(FailureCode.INCOMPLETE_JSON)
    if set(result) != {'notes'}:
        raise ProviderFailure(FailureCode.INVALID_OUTPUT)
    proposal = {'public_input': problem.input, 'notes': result['notes']}
    try:
        validate_enrichment(problem, proposal)
    except (ValueError, TypeError):
        raise ProviderFailure(FailureCode.INVALID_OUTPUT) from None
    return proposal


@dataclass(frozen=True)
class EncodingResult:
    values: tuple[float, ...]
    token_count: int
    context_sha256: str
    request_sha256: str
    cache_hit: bool


class ContextEncoder:
    def __init__(self, backend: FrozenEncoderBackend, cache=None):
        self.backend = backend
        self.cache = cache
        self.coverage = {'requests': 0, 'accepted': 0, 'overlength': 0,
                         'cache_hits': 0, 'model_calls': 0, 'failures': 0}
        self.token_lengths = []

    def encode(self, problem, start_time, *, mode, enrichment=None):
        self.coverage['requests'] += 1
        try:
            return self._encode(problem, start_time, mode=mode, enrichment=enrichment)
        except Exception:
            self.coverage['failures'] += 1
            raise

    def _encode(self, problem, start_time, *, mode, enrichment):
        if mode == 'enriched':
            if enrichment is None:
                raise ProviderFailure(FailureCode.MISSING_BINDING)
            text = enriched_context(problem, enrichment, start_time)
        elif mode == 'public_base_for_offline_audit' and enrichment is None:
            text = problem.context(start_time)
        else:
            raise ValueError('explicit context mode/enrichment required')
        settings = self.backend.settings
        tokens = tuple(self.backend.tokenize(text))
        if not tokens or any(type(t) is not int or t < 0 for t in tokens):
            raise ProviderFailure(FailureCode.INVALID_OUTPUT)
        length = len(tokens)
        self.token_lengths.append(length)
        if length > settings.max_length:
            self.coverage['overlength'] += 1
            raise ProviderFailure(FailureCode.OVERLENGTH)
        request = {'kind': 'frozen_E', 'version': 1, 'settings': asdict(settings),
                   'serialization': 'P02a-Q-C-enrichment-v1', 'context_mode': mode,
                   'text': text, 'tokens_sha256': digest(tokens)}
        cached = self.cache.read(request) if self.cache is not None else None
        hit = cached is not None
        if hit:
            if not isinstance(cached, dict) or set(cached) != {'values', 'token_count'} or cached['token_count'] != length:
                raise ProviderFailure(FailureCode.CACHE_INTEGRITY)
            values = cached['values']
        else:
            self.coverage['model_calls'] += 1
            values = self.backend.encode_tokens(tokens)
        if not isinstance(values, (list, tuple)) or len(values) != settings.embedding_width or any(
                type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ProviderFailure(FailureCode.CACHE_INTEGRITY if hit else FailureCode.INVALID_OUTPUT)
        if not hit and self.cache is not None:
            self.cache.write(request, {'values': list(values), 'token_count': length})
        self.coverage['accepted'] += 1
        self.coverage['cache_hits'] += int(hit)
        return EncodingResult(tuple(values), length, digest(text), digest(request), hit)
