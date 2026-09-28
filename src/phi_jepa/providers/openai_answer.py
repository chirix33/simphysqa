"""Frozen answer generation; typed binding validation is independent of prose."""
from dataclasses import asdict
import json

from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.readers import strict_json
from phi_jepa.inference.readout import BINDING, read_targets
from .contracts import ProviderFailure, FailureCode
from .openai_enrichment import OpenAIEnrichment, ENDPOINT, response_result


class AnswerParseFailure(ProviderFailure):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(FailureCode.INVALID_OUTPUT)


def answer_schema(problem):
    variants = []
    for target in problem.input['answer_spec']:
        props = {k: {'type': 'number' if k in ('start_time', 'end_time') else 'string', 'enum': [target[k]]} for k in BINDING}
        kind = target['answer_type']
        value = ({'type': 'array', 'items': {'type': 'number'}} if kind == 'vector' else
                 {'type': 'boolean' if kind == 'boolean' else 'number'})
        props.update(status={'type': 'string', 'enum': ['supported', 'unsupported']},
                     value={'anyOf': [value, {'type': 'null'}]}, reason={'type': ['string', 'null']})
        variants.append({'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False})
    return {'type': 'object', 'properties': {'plain_text_answer': {'type': 'string'},
            'targets': {'type': 'array', 'items': {'anyOf': variants}}},
            'required': ['plain_text_answer', 'targets'], 'additionalProperties': False}


def parse_answer(problem, text, outcomes, *, boolean_policy='readout'):
    if boolean_policy not in ('readout', 'direct_prediction'):
        raise ValueError('unknown_boolean_policy')
    try: result = strict_json(text)
    except (ValueError, json.JSONDecodeError): raise AnswerParseFailure('malformed_json') from None
    if not isinstance(result, dict) or set(result) != {'plain_text_answer', 'targets'} or type(result['plain_text_answer']) is not str or not isinstance(result['targets'], list):
        raise AnswerParseFailure('envelope')
    specs = {s['target_id']: s for s in problem.input['answer_spec']}
    rules = {o['target_id']: o for o in outcomes}
    seen = set()
    for row in result['targets']:
        if not isinstance(row, dict) or set(row) != set(BINDING) | {'status', 'value', 'reason'}:
            raise AnswerParseFailure('target_fields')
        ident = row['target_id']
        if ident not in specs or ident in seen: raise AnswerParseFailure('unknown_or_duplicate_target')
        seen.add(ident)
        spec = specs[ident]
        for key in BINDING:
            if row[key] != spec[key] or type(row[key]) is bool: raise AnswerParseFailure('binding_'+key)
        if row['status'] not in ('supported', 'unsupported'): raise AnswerParseFailure('status')
        if row['status'] == 'unsupported':
            if row['value'] is not None or type(row['reason']) is not str or not row['reason'].strip():
                raise AnswerParseFailure('unsupported_requires_null_and_reason')
        else:
            if row['reason'] is not None: raise AnswerParseFailure('supported_reason')
            from phi_jepa.inference.readout import finite
            value = row['value']
            kind = spec['answer_type']
            if kind == 'boolean': valid = type(value) is bool
            elif kind == 'number': valid = finite(value)
            elif kind == 'vector':
                observed = [m['value'] for m in problem.input['states'][-1]['measurements'] if (m['entity_id'], m['name']) == (spec['entity_id'], spec['quantity'])]
                valid = len(observed) == 1 and isinstance(observed[0], list) and isinstance(value, list) and len(value) == len(observed[0]) and all(map(finite, value))
            else: valid = False
            if not valid: raise AnswerParseFailure('value_type_or_shape')
        if spec['answer_type'] == 'boolean' and boolean_policy == 'readout':
            rule = rules.get(ident)
            if rule is None: raise AnswerParseFailure('missing_boolean_policy')
            if row['status'] != rule['status'] or row['value'] != rule['value']:
                raise AnswerParseFailure('boolean_policy_violation')
        elif ident in rules and rules[ident]['status'] == 'unsupported' and rules[ident]['source'] != 'control':
            if row['status'] != 'unsupported': raise AnswerParseFailure('unsupported_target_invention')
    if seen != set(specs): raise AnswerParseFailure('missing_target')
    return result


class OpenAIAnswer(OpenAIEnrichment):
    """Shares credential/transport/accounting code, never enrichment semantics."""
    def answer(self, problem, forecast, outcomes, *, condition, boolean_policy='readout', request_sink=None):
        if boolean_policy == 'direct_prediction' and (forecast is not None or outcomes):
            raise ValueError('direct_prediction_requires_public_only_inputs')
        if boolean_policy not in ('readout','direct_prediction'):
            raise ValueError('unknown_boolean_policy')
        if forecast is not None and canonical(read_targets(problem, forecast)) != canonical(outcomes):
            raise ValueError('output readout must match supplied public forecast')
        schema = answer_schema(problem)
        payload = {'model': self.config['model'], 'store': False,
            'instructions': self.asset['prompt'],
            'input': canonical({'public_problem': {'sample_id': problem.sample_id,
                'schema_version': problem.schema_version, 'input': problem.input},
                'physical_forecast': forecast, 'output_readout': outcomes}).decode(),
            'reasoning': {'effort': self.config['reasoning_effort']},
            'max_output_tokens': self.config['max_output_tokens'],
            'text': {'format': {'type': 'json_schema', 'name': 'named_physical_answer', 'strict': True, 'schema': schema}}}
        identity = {'kind': 'final_answer', 'implementation': 'p04a-answer-v1', 'endpoint': ENDPOINT,
                    'asset': self.asset, 'config': self.config, 'condition': condition, 'payload': payload}
        if boolean_policy != 'readout': identity['boolean_policy'] = boolean_policy
        if request_sink is not None:
            request_sink(identity)  # Public request only; never transport credentials.
        validate = lambda text: parse_answer(problem, text, outcomes, boolean_policy=boolean_policy)
        cached = self.cache.read(identity) if self.cache is not None else None
        if cached is not None:
            self.cache_hits += 1
            self._save_events()
            return validate(cached['text'])
        last = {}
        def operation(timeout):
            body = self.transport(payload, timeout)
            result = response_result(body)
            metadata = {'response_id': body.get('id'), 'returned_model': body.get('model'),
                        'request_sha256': digest(identity), 'usage': asdict(result.usage)}
            self.response_metadata.append(metadata)
            last.update(text=result.text, metadata=metadata)
            return result
        try:
            result = self.runner.run(digest(identity), operation, validate)
        finally:
            self._save_events()
        if self.cache is not None: self.cache.write(identity, last)
        return result
