"""One-question, one-reply clarification using immutable forecast evidence.

No evaluator, predictor, retrieval or training dependencies. Free-text semantics
are adjudicated by a recorded human review, never by a keyword guess or an OOD
score. Unknown/unreviewed replies cannot dispatch refinement. The caller is
responsible for authenticating actual-user and reviewer identities.
"""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from time import perf_counter
from typing import Protocol

from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.contracts import PublicProblem, reject_private
from phi_jepa.integration.readers import strict_json
from phi_jepa.inference.readout import read_targets
from phi_jepa.providers.contracts import Usage
from phi_jepa.providers.openai_answer import parse_answer

VERSION = 'clarification-v1'
MODES = {'autonomous', 'scripted_demo', 'actual_interactive'}
ROUTES = {
    'usable': 'ready_to_refine',
    'changed_physical_assumptions': 'reforecast_required',
    'changed_task_or_answer_definition': 'revised_task_required',
    'conflicting': 'unresolved_conflicting_reply',
    'unusable': 'unresolved_unusable_reply',
    'unavailable': 'unresolved_reply_unavailable',
    'outcome_supplying': 'unresolved_outcome_supplied',
}


def now():
    return datetime.now(timezone.utc).isoformat()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def pointer(document, path):
    """Only existing RFC6901 evidence; absent fields cite their existing parent."""
    if not isinstance(path, str) or not path.startswith('/'):
        raise ValueError('evidence_pointer_required')
    node = document
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        try:
            node = node[int(part)] if isinstance(node, list) else node[part]
        except (KeyError, IndexError, TypeError, ValueError):
            raise ValueError('evidence_pointer_not_found') from None
    return node


def validate_request(request, original):
    if request is None:
        return None
    keys = {'missing_or_ambiguous_information', 'affected_target_ids', 'resolution_rationale', 'question', 'public_evidence_paths', 'readout_evidence_target_ids'}
    if not isinstance(request, dict) or set(request) != keys:
        raise ValueError('clarification_request_fields')
    for key in ('missing_or_ambiguous_information', 'resolution_rationale', 'question'):
        if not nonempty(request[key]):
            raise ValueError('specific_information_and_resolution_required')
    specs = {s['target_id'] for s in original['public_problem']['input']['answer_spec']}
    ids = request['affected_target_ids']
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids) or len(set(ids)) != len(ids) or not set(ids) <= specs:
        raise ValueError('affected_target_binding')
    paths = request['public_evidence_paths']
    if not isinstance(paths, list) or not paths:
        raise ValueError('public_grounding_required')
    for path in paths:
        if not isinstance(path, str) or not path.startswith('/public_problem/input/'):
            raise ValueError('public_grounding_only_no_assessment_trigger')
        pointer(original, path)
    readout_ids = request['readout_evidence_target_ids']
    if not isinstance(readout_ids, list) or any(not isinstance(x, str) for x in readout_ids) or not set(readout_ids) <= set(ids):
        raise ValueError('readout_evidence_binding')
    # Missing contact/support capability is not a gap a user reply can repair.
    specs_by_id = {s['target_id']: s for s in original['public_problem']['input']['answer_spec']}
    if any(specs_by_id[x]['quantity'] in ('stable_stack', 'support_lost') for x in ids):
        raise ValueError('missing_contact_capability_is_not_clarification')
    return json.loads(canonical(request))


@dataclass(frozen=True)
class Reply:
    text: str | None
    source: str  # actual_user or scripted_demo; other sources need future authorization
    actor_id: str
    message_id: str
    received_at: str
    channel: str

    def validate(self, mode):
        if mode == 'autonomous':
            raise ValueError('autonomous_attempt_cannot_consume_reply')
        expected = 'actual_user' if mode == 'actual_interactive' else 'scripted_demo'
        if self.source != expected or any(not nonempty(getattr(self, k)) for k in ('actor_id', 'message_id', 'received_at', 'channel')):
            raise ValueError('reply_provenance_required')
        if self.text is not None and not nonempty(self.text):
            raise ValueError('empty_reply_use_explicit_unavailable')


@dataclass(frozen=True)
class ReplyReview:
    category: str
    reason: str
    reviewer_id: str
    reviewed_at: str
    reply_quote: str | None
    preserves_task: bool
    preserves_physical_assumptions: bool
    no_conflict: bool
    no_supplied_outcome: bool
    resolves_requested_gap: bool

    def validate(self, reply):
        if self.category not in ROUTES or any(not nonempty(getattr(self, k)) for k in ('reason', 'reviewer_id', 'reviewed_at')):
            raise ValueError('explicit_human_reply_review_required')
        flags = ('preserves_task', 'preserves_physical_assumptions', 'no_conflict', 'no_supplied_outcome', 'resolves_requested_gap')
        if any(type(getattr(self, k)) is not bool for k in flags):
            raise ValueError('review_flags_must_be_boolean')
        if reply.text is None:
            if self.category != 'unavailable' or self.reply_quote is not None:
                raise ValueError('unavailable_reply_cannot_be_used')
        elif not nonempty(self.reply_quote) or self.reply_quote not in reply.text:
            raise ValueError('review_requires_exact_reply_evidence')
        if self.category == 'usable' and not all(getattr(self, k) for k in flags):
            raise ValueError('usable_reply_must_preserve_task_and_assumptions')


class ReplySource(Protocol):
    """Replaceable boundary; v1 only admits actual users or labeled demos."""
    def receive(self, request: dict) -> Reply: ...


@dataclass(frozen=True)
class Completion:
    text: str | None
    usage: Usage
    response_id: str | None = None
    returned_model: str | None = None
    failure: str | None = None


class AnswerProvider(Protocol):
    identity: dict
    def complete(self, stage: str, original: dict, context: dict) -> Completion: ...


class AttemptStore:
    """Append-only hash-chained journal, exclusive writer lock, no replayed calls.

    A process crash leaves a call reservation unresolved. It is never retried by
    this attempt. A stale lock also fails closed and needs operator inspection.
    """
    def __init__(self, root):
        self.root = Path(root)

    def directory(self, attempt_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', attempt_id):
            raise ValueError('invalid_attempt_id')
        return self.root / attempt_id

    @contextmanager
    def lock(self, attempt_id, *, create=False):
        directory = self.directory(attempt_id)
        if create:
            directory.mkdir(parents=True, exist_ok=False)
        path = directory / '.lock'
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            yield
        finally:
            os.close(fd)
            path.unlink()

    def events(self, attempt_id):
        result = []; previous = None
        for index, path in enumerate(sorted(self.directory(attempt_id).glob('*.json'))):
            event = strict_json(path.read_text(encoding='utf-8'))
            sha = event.pop('sha256')
            if event['sequence'] != index or event['previous'] != previous or digest(event) != sha or path.name != f'{index:04d}.json':
                raise ValueError('clarification_journal_integrity')
            event['sha256'] = sha; result.append(event); previous = sha
        return result

    def append(self, attempt_id, kind, data):
        events = self.events(attempt_id)
        event = {'sequence':len(events), 'previous':events[-1]['sha256'] if events else None,
                 'at':now(), 'kind':kind, 'data':data}
        event['sha256'] = digest(event)
        path = self.directory(attempt_id) / f'{len(events):04d}.json'
        with path.open('xb') as f:
            f.write(canonical(event)); f.flush(); os.fsync(f.fileno())

    def snapshot(self, attempt_id):
        events = self.events(attempt_id)
        if not events or events[0]['kind'] != 'created':
            raise ValueError('missing_attempt_creation')
        data = {e['kind']: e['data'] for e in events}
        reserved = [e for e in events if e['kind'] == 'call_reserved']
        finished = [e for e in events if e['kind'] == 'call_finished']
        status = data.get('status', {}).get('value', 'created')
        if len(reserved) > len(finished):
            status = 'unresolved_call_in_flight_or_interrupted'
        usage = {}
        for k in ('input_tokens', 'output_tokens', 'cost_usd'):
            values = [e['data']['usage'][k] for e in finished]
            usage[k] = sum(values) if len(finished)==len(reserved) and all(x is not None for x in values) else None
        return {'attempt_id':attempt_id, 'status':status, 'records':data,
                'call_attempts':len(reserved), 'total_usage':usage,
                'call_latency_seconds':sum(e['data']['latency_seconds'] for e in finished),
                'journal_head':events[-1]['sha256']}


class ClarificationService:
    def __init__(self, store: AttemptStore, provider: AnswerProvider):
        self.store, self.provider = store, provider

    def _status(self, ident, status):
        self.store.append(ident, 'status', {'value':status})

    def _call(self, ident, stage, original, context):
        # Reserve durably BEFORE dispatch, including timeouts, malformed outputs,
        # and uncertain process interruption. No automatic retry exists.
        self.store.append(ident, 'call_reserved', {'stage':stage, 'provider':self.provider.identity,
            'input_sha256':digest({'original':original,'context':context})})
        started = perf_counter()
        try:
            result = self.provider.complete(stage, json.loads(canonical(original)), json.loads(canonical(context)))
            if not isinstance(result, Completion) or not isinstance(result.usage, Usage):
                raise ValueError('invalid_completion')
        except Exception:
            result = Completion(None, Usage(None,None,None), failure='provider_exception')
        self.store.append(ident, 'call_finished', {'stage':stage, **asdict(result), 'latency_seconds':perf_counter()-started})
        return result

    def start(self, attempt_id, problem, forecast, outcomes, *, mode='actual_interactive'):
        if mode not in MODES:
            raise ValueError('explicit_evaluation_mode_required')
        reject_private(forecast)
        reject_private(outcomes)
        if forecast is None or canonical(read_targets(problem, forecast)) != canonical(outcomes):
            raise ValueError('existing_forecast_and_matching_readout_required')
        original = {'public_problem':{'sample_id':problem.sample_id,'schema_version':problem.schema_version,'input':problem.input},
                    'physical_forecast':forecast,'output_readout':outcomes}
        original = json.loads(canonical(original))
        with self.store.lock(attempt_id, create=True):
            self.store.append(attempt_id, 'created', {'version':VERSION,'mode':mode,'original_sha256':digest(original),
                'task_sha256':digest(original['public_problem']), 'provider_identity':self.provider.identity})
            self.store.append(attempt_id, 'original', original)
            result = self._call(attempt_id, 'initial', original, {})
            if result.failure or result.text is None:
                self._status(attempt_id, 'unresolved_initial_failure')
            else:
                try:
                    value = strict_json(result.text)
                    if not isinstance(value, dict) or set(value) != {'answer','clarification_request'}:
                        raise ValueError('initial_envelope')
                    answer = parse_answer(problem, json.dumps(value['answer']), outcomes)
                    self.store.append(attempt_id, 'initial_answer', answer)
                    request = validate_request(value['clarification_request'], original)
                    self.store.append(attempt_id, 'clarification_request', request)
                    self._status(attempt_id, 'awaiting_reply' if request is not None else 'answered_without_clarification')
                except (ValueError, TypeError, KeyError, RuntimeError):
                    self._status(attempt_id, 'unresolved_invalid_initial_output')
        return self.store.snapshot(attempt_id)

    def submit_reply(self, attempt_id, reply: Reply):
        with self.store.lock(attempt_id):
            snap = self.store.snapshot(attempt_id)
            if snap['status'] != 'awaiting_reply' or 'reply' in snap['records']:
                raise ValueError('only_one_reply_to_one_pending_question')
            reply.validate(snap['records']['created']['mode'])
            self.store.append(attempt_id, 'reply', asdict(reply))
            self._status(attempt_id, 'unresolved_reply_unavailable' if reply.text is None else 'awaiting_reply_review')
        return self.store.snapshot(attempt_id)

    def review_and_refine(self, attempt_id, review: ReplyReview):
        with self.store.lock(attempt_id):
            snap = self.store.snapshot(attempt_id); records = snap['records']
            if snap['status'] not in ('awaiting_reply_review','unresolved_reply_unavailable') or 'reply_review' in records:
                raise ValueError('reply_review_not_pending_or_already_consumed')
            reply = Reply(**records['reply']); review.validate(reply)
            self.store.append(attempt_id, 'reply_review', asdict(review))
            if review.category != 'usable':
                self._status(attempt_id, ROUTES[review.category])
            else:
                if digest(self.provider.identity) != digest(records['created']['provider_identity']):
                    self._status(attempt_id, 'unresolved_provider_identity_changed')
                    return self.store.snapshot(attempt_id)
                original = records['original']
                if digest(original) != records['created']['original_sha256']:
                    raise ValueError('original_evidence_changed')
                context = {k:records[k] for k in ('initial_answer','clarification_request','reply')}
                context['reply_review'] = asdict(review)
                result = self._call(attempt_id, 'refinement', original, context)
                if result.failure or result.text is None:
                    self._status(attempt_id, 'unresolved_refinement_failure')
                else:
                    try:
                        problem = PublicProblem.parse(original['public_problem'])
                        answer = parse_answer(problem, result.text, original['output_readout'])
                        rules = {r['target_id']:r for r in original['output_readout']}
                        # A reply is explanatory context, not an alternative forecast.
                        for row in answer['targets']:
                            rule = rules[row['target_id']]
                            if row['status']=='supported' and (rule['status']!='supported' or canonical(row['value'])!=canonical(rule['value'])):
                                raise ValueError('refinement_cannot_replace_forecast_values')
                        self.store.append(attempt_id, 'refined_answer', answer)
                        self._status(attempt_id, 'refined')
                    except (ValueError, TypeError, KeyError, RuntimeError):
                        self._status(attempt_id, 'unresolved_invalid_refinement')
        return self.store.snapshot(attempt_id)
