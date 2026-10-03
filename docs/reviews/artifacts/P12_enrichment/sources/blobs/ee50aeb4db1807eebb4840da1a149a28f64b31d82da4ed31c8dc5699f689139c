"""Output-only, public-rule readout. No simulator/evaluator imports or state repair.

Event outputs are sampled approximations (20 ms, no interpolation), not exact
continuous-time recovery. Only exact versioned public rule text is qualified.
"""
from copy import deepcopy
import math

from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import PhysicalRollout, PublicProblem, reject_private

CONVENTION = 'Right-handed world x-forward/y-left/z-up; quaternion xyzw; unwrapped right-hand joint angles; all channels SI.'
NUMERIC_RULE = 'Read the named channel at the requested absolute time. Unwrapped angles; quaternion xyzw compared by sign-invariant rotation angle; other vectors by Euclidean norm.'
RULES = {
    'joint_limit_by_T': ('robotic_arm', 'arm', 'Either joint reaches magnitude 2.8rad; contact onset rearmed below 2.795rad.'),
    'boundary_crossed': ('tethered_load', 'load', 'Load COM crosses x=0.1m with 0.005m hysteresis after cutoff.'),
    'left_table': ('object_pushing_stacking', 'block_2', 'Upper block COM outside table footprint [-2,2] x [-2,2].'),
    'stopped_by_T': ('driving', 'car', 'Absolute forward speed <0.02 m/s and planar speed <0.03 m/s for 0.2s; earliest qualifying interval end <=T.'),
}
BINDING = ('target_id', 'entity_id', 'quantity', 'answer_type', 'unit', 'frame', 'query_kind', 'start_time', 'end_time')
SAMPLING = {'interval_seconds': 0.02, 'interpolation': 'none',
    'limitation': 'Events and duration breaks between samples can be missed; no exact continuous-time event recovery.'}


class InvalidForecast(ValueError):
    """Malformed/foreign/nonfinite predictions, distinct from unsupported target."""


class Unsupported(ValueError):
    pass


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def channel(state, entity, name, unit, frame, width=None):
    matches = [m for m in state['measurements'] if (m['entity_id'], m['name']) == (entity, name)]
    if len(matches) != 1:
        raise Unsupported('missing_or_duplicate_channel')
    m = matches[0]
    if (m['unit'], m['frame']) != (unit, frame):
        raise Unsupported('channel_unit_or_frame')
    value = m['value']
    if width is None:
        if not finite(value): raise Unsupported('channel_not_finite_scalar')
    elif not isinstance(value, list) or len(value) != width or not all(map(finite, value)):
        raise Unsupported('channel_vector_shape_or_value')
    return value


def named_forecast(problem: PublicProblem, layout, rollout: PhysicalRollout, *, diagnostic=False, numerical_only=False):
    """Map registered measurement columns only; never expose P/fixed conditioning.

    External solver time is authoritative. Predicted timestamp/step-index remain
    unchanged in the caller's full augmented trajectory, not physical channels.
    """
    required_mode = 'recorded_input_one_step_diagnostic' if diagnostic else 'autonomous'
    if rollout.sample_id != problem.sample_id or rollout.mode != required_mode:
        raise InvalidForecast('sample_or_mode')
    inp = problem.input
    try:
        layout.flatten(inp['states'][-1], inp)  # exact structure/unit/frame registry
    except ValueError:
        raise InvalidForecast('public_layout_binding') from None
    columns = {path: i for i, (path, _) in enumerate(layout.entries)}
    templates = []
    for m in inp['states'][-1]['measurements']:
        if type(m['value']) is bool: continue
        base = (('key', 'state'), ('key', 'measurements'), ('quantity', m['entity_id'], m['name']), ('key', 'value'))
        paths = [base + (('index', i),) for i in range(len(m['value']))] if isinstance(m['value'], list) else [base]
        if any(p not in columns for p in paths): raise InvalidForecast('unregistered_measurement')
        templates.append((m, [columns[p] for p in paths]))
    rows, previous = [], inp['observation_cutoff']
    for p in rollout.predictions:
        if p.layout_sha256 != layout.sha256 or p.d != layout.d or p.physical_time <= previous:
            raise InvalidForecast('layout_or_time')
        if len(p.values) != (layout.d if numerical_only else 2*layout.d) or not all(map(finite, p.values)):
            raise InvalidForecast('shape_or_nonfinite')
        measures = []
        for m, indices in templates:
            result = deepcopy(m)
            values = [p.values[i] for i in indices]
            result['value'] = values if isinstance(m['value'], list) else values[0]
            measures.append(result)
        rows.append({'timestamp': p.physical_time, 'measurements': measures})
        previous = p.physical_time
    return {'sample_id': problem.sample_id, 'layout_sha256': layout.sha256,
            'source': 'recorded_input_one_step_diagnostic' if diagnostic else 'autonomous_numeric_forecast',
            'states': rows, 'sampling': SAMPLING.copy()}


def regular(states, start, end):
    if not states or abs(states[0]['timestamp']-start) > 1e-8 or abs(states[-1]['timestamp']-end) > 1e-8:
        raise Unsupported('time_coverage')
    if any(abs(b['timestamp']-a['timestamp']-.02) > 1e-8 for a,b in zip(states, states[1:])):
        raise Unsupported('requires_complete_0.02_second_grid')


def target_result(target, status, value=None, reason=None, *, source, evidence=None):
    return {**{k: target[k] for k in BINDING}, 'status': status, 'value': value,
            'reason': reason, 'source': source, 'evidence': evidence,
            'rule_sha256': digest({k: target[k] for k in ('rule_id', 'rule_definition')})}


def read_targets(problem: PublicProblem, payload):
    """No reference, Boolean labels or private event log accepted by this API."""
    inp = problem.input
    if payload.get('source') == 'recorded_input_one_step_diagnostic':
        raise InvalidForecast('recorded_input_diagnostic_is_not_autonomous_answer')
    try: reject_private(payload)
    except ValueError: raise InvalidForecast('private_forecast_payload') from None
    if payload['sample_id'] != problem.sample_id: raise InvalidForecast('sample')
    forecast = payload['states']
    last = inp['observation_cutoff']
    for row in forecast:
        if not finite(row['timestamp']) or row['timestamp'] <= last: raise InvalidForecast('time')
        for m in row['measurements']:
            v = m['value']; values = v if isinstance(v, list) else [v]
            if not values or not all(map(finite, values)): raise InvalidForecast('nonfinite_or_nonnumeric')
        last = row['timestamp']
    results = []
    for target in inp['answer_spec']:
        is_bool = target['answer_type'] == 'boolean'
        source = 'sampled_public_rule' if is_bool else 'numeric_forecast'
        evidence = None
        try:
            t = target['end_time']
            if target['query_kind'] != 'at_time' or target['start_time'] != t or not finite(t) or t <= inp['observation_cutoff']:
                raise Unsupported('query_or_time')
            if target['rule_id'] != 'terminal_readout_v1': raise Unsupported('rule_version')
            if inp['coordinate_convention'] != CONVENTION: raise Unsupported('coordinate_convention')
            endpoints = [r for r in forecast if abs(r['timestamp']-t) <= 1e-8]
            if len(endpoints) != 1: raise Unsupported('endpoint_time_coverage')
            endpoint = endpoints[0]
            name = target['quantity']
            if not is_bool:
                if target['answer_type'] not in ('number', 'vector') or target['rule_definition'] != NUMERIC_RULE:
                    raise Unsupported('numeric_type_or_rule')
                matches = [m for m in inp['states'][-1]['measurements'] if (m['entity_id'], m['name']) == (target['entity_id'], name)]
                if len(matches) != 1: raise Unsupported('unregistered_target')
                observed = matches[0]['value']
                if (target['answer_type'] == 'vector') != isinstance(observed, list): raise Unsupported('target_type')
                width = len(observed) if isinstance(observed, list) else None
                value = channel(endpoint, target['entity_id'], name, target['unit'], target['frame'], width)
                evidence = [t, t]
            else:
                if name in ('stable_stack', 'support_lost'): raise Unsupported('missing_contact_force_and_history')
                if name not in RULES: raise Unsupported('unqualified_boolean_rule')
                domain, entity, rule = RULES[name]
                if (inp['domain'], target['entity_id'], target['unit'], target['frame'], target['rule_definition']) != (domain, entity, '1', 'world', rule):
                    raise Unsupported('boolean_binding_or_rule')
                if name == 'left_table':
                    pos = channel(endpoint, entity, 'position', 'm', 'world', 3)
                    value = abs(pos[0]) > 2 or abs(pos[1]) > 2
                    evidence = [t, t]  # endpoint only, not an accumulated event
                else:
                    history = inp['states']
                    future = [s for s in forecast if s['timestamp'] <= t+1e-8]
                    if name == 'boundary_crossed':
                        states = [history[-1], *future]
                        regular(states, inp['observation_cutoff'], t)
                        xs = [channel(s, entity, 'position', 'm', 'world', 3)[0] for s in states]
                        # Public rule does not specify the latch for an already
                        # crossed initial position. Qualify only observed rearm.
                        if xs[0] >= .095: raise Unsupported('initial_crossing_state_not_qualified')
                        armed, value = True, False
                        for x in xs[1:]:
                            if x > .105 and armed: value, armed = True, False
                            if x < .095: armed = True
                    else:
                        states = [*history, *future]
                        regular(states, 0., t)  # establish initial event/dwell state
                        if name == 'joint_limit_by_T':
                            armed, value = True, False
                            for s in states:
                                angles = [abs(channel(s, j, 'angle', 'rad', 'joint_local')) for j in ('joint_1', 'joint_2')]
                                if max(angles) >= 2.8 and armed: value, armed = True, False
                                if max(angles) < 2.795: armed = True
                        else:
                            start, value = None, False
                            for s in states:
                                forward = channel(s, entity, 'forward_velocity', 'm/s', 'world')
                                velocity = channel(s, entity, 'velocity', 'm/s', 'world', 3)
                                good = abs(forward) < .02 and math.hypot(*velocity[:2]) < .03
                                if good and start is None: start = s['timestamp']
                                if not good: start = None
                                if start is not None and s['timestamp']-start >= .2-1e-10: value = True
                    evidence = [states[0]['timestamp'], t]
            results.append(target_result(target, 'supported', value, source=source, evidence=evidence))
        except Unsupported as exc:
            results.append(target_result(target, 'unsupported', reason=str(exc), source=source))
    return results
