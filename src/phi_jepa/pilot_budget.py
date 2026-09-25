"""Single-worker persistent reservations for the explicitly authorized P08 pilot.

The supervisor enforces active-operation deadlines even inside native calls.
Unknown provider usage retains its entire reservation. No credentials are stored.
"""
from contextlib import contextmanager
import json
import time
from pathlib import Path
from phi_jepa.artifacts import canonical


class BudgetExceeded(RuntimeError): pass


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.pending'); pending.write_bytes(canonical(value)); pending.replace(path)


class PilotBudget:
    def __init__(self, directory, config):
        self.root = Path(directory); self.path = self.root / 'budget.json'; self.config = config
        if not self.path.exists():
            save(self.path, {'caps': config['caps'], 'seconds': {}, 'operations': [], 'provider': [], 'active': None, 'stopped': None})

    def read(self): return json.loads(self.path.read_text())

    def size(self): return sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())

    def check(self, reserve_bytes=0):
        state = self.read()
        if state['stopped']: raise BudgetExceeded(state['stopped'])
        if self.size() + reserve_bytes > self.config['caps']['artifact_bytes']: self.stop('artifact_bytes')
        for resource in ('gpu', 'cpu'):
            if state['seconds'].get(resource, 0) >= self.config['caps'][resource+'_seconds']: self.stop(resource+'_seconds')
        return state

    def stop(self, reason):
        state = self.read(); state['stopped'] = reason; save(self.path, state)
        raise BudgetExceeded(reason)

    @contextmanager
    def operation(self, name, resource, buckets=(), cap=None, reserve_bytes=0):
        state = self.check(reserve_bytes); assert state['active'] is None
        keys = [resource, *buckets]; limits = {**self.config['bucket_seconds'], 'gpu': self.config['caps']['gpu_seconds'], 'cpu': self.config['caps']['cpu_seconds']}
        remaining = min(limits[k] - state['seconds'].get(k, 0) for k in keys)
        if cap is not None: remaining = min(remaining, cap)
        if remaining <= 0: raise BudgetExceeded('component_time_budget:' + name)
        started = time.time(); entry = {'name': name, 'resource': resource, 'buckets': list(buckets), 'started': started, 'deadline': started + remaining}
        state['active'] = entry; save(self.path, state)
        try: yield
        finally:
            elapsed = time.time() - started; state = self.read()
            for key in keys: state['seconds'][key] = state['seconds'].get(key, 0) + elapsed
            state['operations'].append({**entry, 'seconds': elapsed}); state['active'] = None
            if state['seconds'][resource] >= self.config['caps'][resource+'_seconds']: state['stopped'] = resource+'_seconds'
            save(self.path, state)

    def transport(self, original):
        def bounded(payload, timeout):
            from phi_jepa.providers.openai_enrichment import response_result
            state = self.check(); caps = self.config['caps']
            # UTF-8 payload bytes plus a framing reserve conservatively bound input
            # tokens; output is the actual requested cap. Pricing basis inherited
            # from the accepted provider adapter: $4/$0.4 cached/$20 per million.
            inputs = len(canonical(payload)) + 4096; outputs = payload['max_output_tokens']
            cost = (inputs * 4 + outputs * 20) / 1e6
            rows = state['provider']
            totals = [sum(r[k] for r in rows) for k in ('charged_input', 'charged_output', 'charged_usd')]
            if len(rows) >= caps['provider_attempts'] or totals[0]+inputs > caps['provider_input_tokens'] or totals[1]+outputs > caps['provider_output_tokens'] or totals[2]+cost > caps['provider_usd']:
                self.stop('provider_reservation_cap')
            index = len(rows); rows.append({'model': payload['model'], 'reserved_input': inputs, 'reserved_output': outputs, 'reserved_usd': cost,
                'charged_input': inputs, 'charged_output': outputs, 'charged_usd': cost, 'usage_known': False, 'started': time.time()})
            save(self.path, state)
            started_cpu = time.process_time()
            try:
                body = original(payload, timeout); usage = response_result(body).usage
                state = self.read(); row = state['provider'][index]
                if usage.input_tokens is not None and usage.output_tokens is not None and usage.cost_usd is not None:
                    row.update(charged_input=usage.input_tokens, charged_output=usage.output_tokens, charged_usd=usage.cost_usd, usage_known=True,
                        returned_model=body.get('model'), response_id=body.get('id'))
                    if usage.input_tokens > inputs or usage.output_tokens > outputs or usage.cost_usd > cost: state['stopped'] = 'provider_reservation_violation'
                save(self.path, state); return body
            finally:
                state = self.read(); state['provider'][index]['wall_seconds'] = time.time()-state['provider'][index]['started']
                state['seconds']['cpu'] = state['seconds'].get('cpu', 0) + time.process_time()-started_cpu
                save(self.path, state)
        return bounded
