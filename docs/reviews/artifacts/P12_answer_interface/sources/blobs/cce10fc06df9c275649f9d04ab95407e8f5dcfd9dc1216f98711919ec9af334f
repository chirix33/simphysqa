"""Lossless public-metadata adapter. No forecasts, references, or value repair."""
import json
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import strict_json
from phi_jepa.inference.readout import BINDING
from .openai_answer import parse_answer, AnswerParseFailure

VERSION = 'p12-compact-interface-v1'


def specs_for(problem):
    if type(problem) is not PublicProblem:
        raise ValueError('public-only input required')
    specs = problem.input['answer_spec']
    if not specs or len({s['target_id'] for s in specs}) != len(specs):
        raise ValueError('invalid public target identities')
    return specs


def value_schema(problem, spec):
    kind = spec['answer_type']
    if kind in ('number', 'boolean'):
        return {'type': kind}
    if kind != 'vector':
        raise ValueError('unknown answer type')
    observed = [m['value'] for m in problem.input['states'][-1]['measurements']
                if (m['entity_id'], m['name']) == (spec['entity_id'], spec['quantity'])]
    if len(observed) != 1 or not isinstance(observed[0], list) or not observed[0]:
        raise ValueError('public vector dimension unavailable')
    n = len(observed[0])
    return {'type': 'array', 'items': {'type': 'number'}, 'minItems': n, 'maxItems': n}


def compact_schema(problem):
    props = {}
    for spec in specs_for(problem):
        supported = {'status': {'const': 'supported'}, 'value': value_schema(problem, spec),
                     'reason': {'type': 'null'}}
        unsupported = {'status': {'const': 'unsupported'}, 'value': {'type': 'null'},
                       'reason': {'type': 'string', 'pattern': r'.*\S.*'}}
        props[spec['target_id']] = {'anyOf': [
            {'type': 'object', 'properties': p, 'required': list(p), 'additionalProperties': False}
            for p in (supported, unsupported)]}
    return {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}


def compact_messages(problem, instruction):
    specs = specs_for(problem)
    header = ['TEMPORAL TASK', f"PUBLIC OBSERVATION CUTOFF: {problem.input['observation_cutoff']} seconds.",
              'REQUESTED ABSOLUTE PREDICTION TIMES (seconds from initialization), in output key order:']
    header.extend(f"{s['target_id']}: {s['query_kind']} [{s['start_time']}, {s['end_time']}]; "
                  f"type={s['answer_type']}, unit={s['unit']}" for s in specs)
    content = '\n'.join(header) + '\n\n' + canonical({
        'public_problem': problem.input, 'required_answer_schema': compact_schema(problem)}).decode()
    return [{'role': 'system', 'content': instruction}, {'role': 'user', 'content': content}]


def adapt_answer(problem, text):
    specs = specs_for(problem)
    try:
        compact = strict_json(text)
    except ValueError as exc:
        raise AnswerParseFailure('compact_json:' + str(exc)) from None
    if type(compact) is not dict:
        raise AnswerParseFailure('compact_object_required')
    expected = {s['target_id'] for s in specs}
    if set(compact) - expected:
        raise AnswerParseFailure('compact_unknown_target')
    if expected - set(compact):
        raise AnswerParseFailure('compact_missing_target')
    targets = []
    for spec in specs:
        value = compact[spec['target_id']]
        if type(value) is not dict or set(value) != {'status', 'value', 'reason'}:
            raise AnswerParseFailure('compact_target_fields')
        targets.append({**{k: spec[k] for k in BINDING}, **value})
    # Empty narrative is explicit; the adapter does not invent model prose or predictions.
    # allow_nan keeps overflow visible to the unchanged strict canonical parser.
    return parse_answer(problem, json.dumps({'plain_text_answer': '', 'targets': targets}),
                        [], boolean_policy='direct_prediction')
