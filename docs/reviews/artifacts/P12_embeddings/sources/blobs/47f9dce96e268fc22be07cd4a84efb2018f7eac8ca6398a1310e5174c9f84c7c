"""Immutable boundaries for active model-training contract 2.0.0-candidate.1."""
from dataclasses import dataclass
import json
import math
from phi_jepa.artifacts import canonical, digest

DOMAINS = frozenset(('robotic_arm', 'driving', 'object_pushing_stacking', 'tethered_load'))
SPLITS = frozenset(('train', 'validation', 'test_id', 'ood_parameter_extrapolation',
                    'ood_unseen_combination', 'ood_timed_event'))
INPUT_KEYS = frozenset(('answer_spec', 'controller', 'coordinate_convention', 'domain',
    'entities', 'global_context', 'known_events', 'observation_cutoff', 'question', 'states', 'task_type'))
FORBIDDEN = frozenset(('reference', 'metadata', 'label', 'structured_label', 'explanation',
    'solution_trace', 'gold_answer', 'answer', 'predicted_label', 'predictions', 'A'))

def reject_private(value):
    if isinstance(value, dict):
        if FORBIDDEN.intersection(value):
            raise ValueError('answer-bearing/private field in public context')
        for item in value.values(): reject_private(item)
    elif isinstance(value, list):
        for item in value: reject_private(item)

@dataclass(frozen=True)
class PublicProblem:
    sample_id: str
    schema_version: str
    input_json: str

    @classmethod
    def parse(cls, envelope):
        if set(envelope) != {'sample_id', 'schema_version', 'input'}:
            raise ValueError('public envelope must contain only input and public identity')
        inp = envelope['input']
        if set(inp) != INPUT_KEYS or inp['domain'] not in DOMAINS:
            raise ValueError('unsupported public layout/domain')
        if envelope['schema_version'] != '1.0.0' or not isinstance(envelope['sample_id'], str):
            raise ValueError('unsupported public identity')
        reject_private(inp)
        times = [s['timestamp'] for s in inp['states']]
        cutoff = inp['observation_cutoff']
        if not times or any(type(t) not in (int, float) or not math.isfinite(t) for t in [*times, cutoff]):
            raise ValueError('invalid public time')
        if any(b <= a for a, b in zip(times, times[1:])) or times[-1] != cutoff:
            raise ValueError('public history must end at cutoff in increasing time order')
        return cls(envelope['sample_id'], envelope['schema_version'], canonical(inp).decode())

    @property
    def input(self):
        return json.loads(self.input_json)

    def context(self, start_time):
        inp = self.input
        if start_time < inp['observation_cutoff']:
            raise ValueError('earlier pairs require a separately reviewed causal context policy')
        return canonical({'Q': inp.pop('question'), 'C': inp}).decode()

@dataclass(frozen=True)
class Identity:
    sample_id: str
    scenario_id: str
    group_id: str
    domain: str
    split: str

@dataclass(frozen=True)
class RecordedPair:
    identity: Identity
    pair_id: str
    transition_id: str
    start_time: float
    end_time: float
    start_state_id: str
    end_state_id: str
    n_current: tuple
    n_next: tuple
    context_json: str
    registry_sha256: str
    provenance_sha256: str
    weight: float
    context_mode: str = 'public_base_for_offline_audit'

    @property
    def dt(self): return self.end_time - self.start_time

@dataclass(frozen=True)
class FullAugmentedPrediction:
    layout_sha256: str
    d: int
    values: tuple
    physical_time: float

    def __post_init__(self):
        if self.d <= 0 or len(self.values) != 2 * self.d:
            raise ValueError('augmented prediction requires width 2d')
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in (*self.values, self.physical_time)):
            raise ValueError('nonfinite/invalid prediction')

    def feedback(self):
        """Return all predicted coordinates, including predicted context coordinates."""
        return self.values

@dataclass(frozen=True)
class PhysicalRollout:
    sample_id: str
    predictions: tuple[FullAugmentedPrediction, ...]
    mode: str = 'autonomous'

@dataclass(frozen=True)
class TypedAnswer:
    sample_id: str
    named_predictions_json: str
    nonnumeric_status: str = 'pending_policy'

@dataclass(frozen=True)
class StageFailure:
    stage: str
    sample_id: str | None
    code: str
    message: str

def derived_identity(value):
    return digest(value)

def validate_enrichment(problem, proposed):
    """Candidate interface only: immutable public problem + separate text notes.

    Structural provenance is not proof that generated prose is true. No provider
    dispatch is implemented, and notes are not automatically used as E input.
    """
    if set(proposed) != {'public_input', 'notes'}:
        raise ValueError('enrichment must be separate from original facts')
    reject_private(proposed)
    if canonical(proposed['public_input']).decode() != problem.input_json:
        raise ValueError('enrichment changed immutable public facts')
    if not isinstance(proposed['notes'], list) or any(type(n) is not str for n in proposed['notes']):
        raise ValueError('enrichment notes must be text; no invented numeric schema')
    return canonical(proposed).decode()

def enriched_context(problem, proposed, start_time):
    validate_enrichment(problem, proposed)
    context = json.loads(problem.context(start_time))
    context['public_enrichment'] = proposed['notes']
    return canonical(context).decode()
