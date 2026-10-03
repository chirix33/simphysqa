"""Crash-durable single-worker money/attempt reservations for public enrichment."""
from pathlib import Path
import json,os,tempfile,time
from phi_jepa.artifacts import canonical,digest

class EnrichmentBudgetStop(RuntimeError):pass

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.pending-')
    try:
        with os.fdopen(fd,'wb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def reservation(payload,prices):
    inputs=len(canonical(payload))+4096;outputs=payload['max_output_tokens']
    if inputs>prices['short_context_input_limit']:raise EnrichmentBudgetStop('input upper bound outside verified short-context price tier')
    if payload['model']!=prices['model'] or payload.get('tools'):raise EnrichmentBudgetStop('unpriced model or tool')
    # Rates are USD per million; nanodollars/token = rate * 1000.
    cost=inputs*prices['reservation_input_usd_per_million']*1000+outputs*prices['reservation_output_usd_per_million']*1000
    return inputs,outputs,int(cost)

def measured_cost(body,prices):
    usage=body.get('usage') or {};inputs=usage.get('input_tokens');outputs=usage.get('output_tokens')
    cached=(usage.get('input_tokens_details') or {}).get('cached_tokens',0)
    writes=(usage.get('input_tokens_details') or {}).get('cache_write_tokens')
    tier=body.get('service_tier','default')
    if not all(type(n) is int and n>=0 for n in (inputs,outputs,cached)) or cached>inputs:return None
    if body.get('model')!=prices['model'] or inputs>prices['short_context_input_limit']:return None
    if tier=='default':rates=prices['standard_usd_per_million']
    elif tier in ('fast','priority'):rates=prices['fast_usd_per_million']
    else:return None
    if writes is not None and (type(writes) is not int or writes<0 or writes+cached>inputs):return None
    def cost(w):return round(((inputs-cached-w)*rates['input']+cached*rates['cached_input']+w*rates['cache_write']+outputs*rates['output'])*1000)
    return {'input_tokens':inputs,'output_tokens':outputs,'cached_input_tokens':cached,'service_tier':tier,
            'cache_write_tokens':writes,'cost_nano_usd':cost(writes) if writes is not None else None,
            'cost_lower_nano_usd':cost(writes if writes is not None else 0),
            'cost_upper_nano_usd':cost(writes if writes is not None else inputs-cached)}

class EnrichmentBudget:
    def __init__(self,root,config,scope=None):
        self.root=Path(root);self.path=self.root/'spend-ledger.json';self.config=config;self.scope=scope
        if scope is not None and scope not in config.get('scope_estimates',{}):raise EnrichmentBudgetStop('unbudgeted scope')
        if not self.path.exists():atomic_json(self.path,{'config_sha256':digest(config),'attempts':[],'stopped':None})
        if self.read()['config_sha256']!=digest(config):raise EnrichmentBudgetStop('budget configuration changed on resume')
    def read(self):return json.loads(self.path.read_text())
    def transport(self,original):
        def bounded(payload,timeout):
            state=self.read();rows=state['attempts'];inputs,outputs,cost=reservation(payload,self.config['pricing'])
            def deny(reason):
                state['stopped']=reason;atomic_json(self.path,state);raise EnrichmentBudgetStop(reason)
            if state['stopped']:raise EnrichmentBudgetStop(state['stopped'])
            if any(r['status']=='reserved' for r in rows):deny('unresolved prior dispatch requires reconciliation')
            if len(rows)>=self.config['attempt_cap']:deny('attempt cap reached')
            if sum(r['charged_nano_usd'] for r in rows)+cost>round(self.config['usd_cap']*1e9):deny('USD cap reservation refused')
            if self.scope is not None:
                allocation=self.config['scope_estimates'][self.scope];scoped=[r for r in rows if r.get('scope')==self.scope]
                if len(scoped)>=allocation['proposed_attempt_cap']:deny('scope attempt cap reached')
                if sum(r['charged_nano_usd'] for r in scoped)+cost>round(allocation['proposed_usd_allocation']*1e9):deny('scope USD cap reservation refused')
            if sum(r.get('latency_seconds',0) for r in rows)>=self.config['wall_seconds_cap']:deny('time cap reached')
            if sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())+10000000>self.config['artifact_bytes_cap']:raise EnrichmentBudgetStop('artifact cap reached')
            index=len(rows);row={'attempt_id':index+1,'payload_sha256':digest(payload),'reserved_input_tokens':inputs,'reserved_output_tokens':outputs,
                'reserved_nano_usd':cost,'charged_nano_usd':cost,'status':'reserved','usage':None,'started_unix':time.time()}
            if self.scope is not None:row['scope']=self.scope
            rows.append(row);atomic_json(self.path,state);start=time.perf_counter()
            try:
                body=original(payload,min(timeout,self.config['wall_seconds_cap']-sum(r.get('latency_seconds',0) for r in rows)))
                atomic_json(self.root/'responses'/f'{index+1:04}.json',body)
                row.update(status='response_received',usage=measured_cost(body,self.config['pricing']),response_id=body.get('id'),returned_model=body.get('model'),provider_status=body.get('status'))
                if row['usage'] is not None:
                    row['charged_nano_usd']=row['usage']['cost_upper_nano_usd']
                    if row['usage']['input_tokens']>inputs or row['usage']['output_tokens']>outputs or row['charged_nano_usd']>cost:
                        state['stopped']='reservation violated';raise EnrichmentBudgetStop(state['stopped'])
                if body.get('model')!=self.config['pricing']['model']:state['stopped']='unexpected returned enrichment model';raise EnrichmentBudgetStop(state['stopped'])
                return body
            except BaseException as exc:
                if row['status']=='reserved':row.update(status='transport_failure',failure_type=type(exc).__name__)
                raise
            finally:
                row['latency_seconds']=time.perf_counter()-start;atomic_json(self.path,state)
        return bounded
