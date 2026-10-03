"""Explicit OpenAI Responses transport with public-only content and usage ledger.

No tools, stored conversations, SDK retry layer, repair or private-value lookup.
The configured profile caps are engineering bounds under the user's unrestricted
budget authorization. HTTP failures are sanitized; response bodies never enter
errors/logs. Cache hits retain originating usage without charging it again.
"""
from dataclasses import asdict
import json
import socket
from urllib import error, request

from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.readers import strict_json
from .attempts import AttemptPolicy, AttemptRunner
from .context import parse_notes
from .contracts import AttemptResult, FailureCode, ProviderFailure, Usage


ENDPOINT = 'https://api.openai.com/v1/responses'


def response_result(body):
    """Parse Responses structure while retaining usage on refusal/incompleteness."""
    raw_usage = body.get('usage') or {}
    inputs, outputs = raw_usage.get('input_tokens'), raw_usage.get('output_tokens')
    cached = (raw_usage.get('input_tokens_details') or {}).get('cached_tokens', 0)
    # Documented standard <=272k input pricing; no cache writes or tools requested.
    cost = None
    if type(inputs) is int and type(outputs) is int and type(cached) is int and 0 <= cached <= inputs <= 272000:
        cost = ((inputs - cached) * 4 + cached * 0.4 + outputs * 20) / 1_000_000
    usage = Usage(inputs, outputs, cost)
    parts = [part for item in body.get('output', []) if item.get('type') == 'message'
             for part in item.get('content', [])]
    if any(p.get('type') == 'refusal' for p in parts):
        return AttemptResult(usage, failure=FailureCode.REFUSAL)
    if body.get('status') != 'completed':
        return AttemptResult(usage, failure=FailureCode.INCOMPLETE_JSON)
    texts = [p.get('text') for p in parts if p.get('type') == 'output_text']
    if len(texts) != 1 or not isinstance(texts[0], str):
        return AttemptResult(usage, failure=FailureCode.INCOMPLETE_JSON)
    return AttemptResult(usage, text=texts[0])


class OpenAIEnrichment:
    def __init__(self, key, config, asset, cache, *, transport=None, event_sink=None, ledger=None):
        if not key:
            raise ProviderFailure(FailureCode.MISSING_CREDENTIALS)
        self._key = key
        self.config = config
        self.asset = asset
        self.cache = cache
        self.transport = transport or self._http
        self.event_sink = event_sink
        self.cache_hits = 0
        self.response_metadata = list((ledger or {}).get('responses', []))
        self.runner = AttemptRunner(AttemptPolicy(
            config['max_attempts_per_request'], config['max_total_attempts'], config['timeout_seconds']),
            event_sink=self._save_events)
        self.runner.events = list((ledger or {}).get('events', []))

    def _save_events(self):
        if self.event_sink is not None:
            self.event_sink({'events': self.runner.events, 'responses': self.response_metadata,
                             'cache_hits_this_process': self.cache_hits})

    def _http(self, payload, timeout):
        req = request.Request(ENDPOINT, data=canonical(payload), method='POST', headers={
            'Authorization': 'Bearer ' + self._key, 'Content-Type': 'application/json'})
        # Disable redirects: credentials must only reach the fixed OpenAI endpoint.
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        try:
            with request.build_opener(NoRedirect).open(req, timeout=timeout) as response:
                return strict_json(response.read().decode('utf-8'))
        except error.HTTPError as exc:
            code = (FailureCode.MISSING_CREDENTIALS if exc.code in (401, 403)
                    else FailureCode.RATE_LIMIT if exc.code == 429
                    else FailureCode.PROVIDER_UNAVAILABLE)
            raise ProviderFailure(code) from None
        except (TimeoutError, socket.timeout):
            raise TimeoutError() from None
        except error.URLError:
            raise ProviderFailure(FailureCode.TRANSPORT) from None

    def enrich(self, problem, start_time):
        context = problem.context(start_time)  # no reference or evaluator handle
        payload = {'model': self.config['model'], 'store': False,
            'instructions': self.asset['prompt'], 'input': context,
            'reasoning': {'effort': self.config['reasoning_effort']},
            'max_output_tokens': self.config['max_output_tokens'],
            'text': {'format': {'type': 'json_schema', 'name': 'public_context_notes',
                               'strict': True, 'schema': self.asset['schema']}}}
        identity = {'kind': 'public_enrichment', 'implementation': 'p02b-responses-v1',
                    'endpoint': ENDPOINT, 'asset': self.asset, 'config': self.config, 'payload': payload}
        cached = self.cache.read(identity) if self.cache is not None else None

        def validate(text):
            proposal = parse_notes(problem, text)
            if len(proposal['notes']) > 4 or any(len(note) > 400 for note in proposal['notes']):
                raise ProviderFailure(FailureCode.INVALID_OUTPUT)
            return proposal

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
            proposal = self.runner.run(digest(identity), operation, validate)
        finally:
            self._save_events()
        if self.cache is not None:
            self.cache.write(identity, last)
        return proposal
