"""Frozen answer adapter for v1 clarification; one transport dispatch, no retry.

Constructing this adapter performs no IO. Live authorization/budget reservation
must be supplied explicitly by the application; it is not implied by old P08
configs. Mock transports use the identical payload and parsing boundaries.
"""
import json
from phi_jepa.artifacts import digest, canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.inference.clarification import Completion
from phi_jepa.providers.openai_answer import answer_schema
from phi_jepa.providers.openai_enrichment import ENDPOINT, response_result


def initial_schema(problem):
    text = {'type':'string'}
    strings = {'type':'array','items':text}
    props = {'missing_or_ambiguous_information':text, 'affected_target_ids':strings,
             'resolution_rationale':text, 'question':text, 'public_evidence_paths':strings,
             'readout_evidence_target_ids':strings}
    request = {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
    return {'type':'object','properties':{'answer':answer_schema(problem),
            'clarification_request':{'anyOf':[request,{'type':'null'}]}},
            'required':['answer','clarification_request'],'additionalProperties':False}


class FrozenClarificationAnswer:
    def __init__(self, *, config, asset, transport, authorize_and_reserve):
        if config.get('model') != 'gpt-5.6-sol' or config.get('max_attempts_per_request') != 1:
            raise ValueError('settled_frozen_answer_model_single_attempt_required')
        if asset.get('version') != 'clarification-v1' or not callable(authorize_and_reserve):
            raise ValueError('versioned_prompt_and_explicit_budget_boundary_required')
        if type(config.get('max_output_tokens')) is not int or config['max_output_tokens']<=0:
            raise ValueError('generation_limit_required')
        if not isinstance(config.get('timeout_seconds'), (int,float)) or config['timeout_seconds']<=0:
            raise ValueError('timeout_required')
        self.config = json.loads(canonical(config)); self.asset = json.loads(canonical(asset))
        self.transport, self.reserve = transport, authorize_and_reserve
        self.identity = {'implementation':'clarification-v1','endpoint':ENDPOINT,
            'config':self.config,'asset_sha256':digest(self.asset),
            'snapshot_limitation':'Configured frozen alias; provider may not expose immutable weights.'}

    def complete(self, stage, original, context):
        if stage not in ('initial','refinement'):
            raise ValueError('unknown_clarification_stage')
        problem = PublicProblem.parse(original['public_problem'])
        schema = initial_schema(problem) if stage=='initial' else answer_schema(problem)
        payload = {'model':self.config['model'],'store':False,'instructions':self.asset[stage],
            'input':canonical({'original_evidence':original,'attributed_interaction':context}).decode(),
            'reasoning':{'effort':self.config['reasoning_effort']},
            'max_output_tokens':self.config['max_output_tokens'],
            'text':{'format':{'type':'json_schema','name':'clarification_'+stage,'strict':True,'schema':schema}}}
        # Caller must refuse unapproved work and reserve worst-case token/spend
        # bounds. An exception dispatches nothing and is recorded as failure.
        self.reserve(stage, payload)
        body = self.transport(payload, self.config['timeout_seconds'])
        result = response_result(body)
        return Completion(result.text,result.usage,body.get('id'),body.get('model'),
                          result.failure.value if result.failure else None)
