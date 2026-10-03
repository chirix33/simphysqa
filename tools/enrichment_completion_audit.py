"""Final public-only cache and usage audit; never opens credentials or calls models."""
from enrichment_run_control import *
from phi_jepa.providers.enrichment_budget import measured_cost
from p10_common import guard_deployment_io

def main():
    guard_deployment_io();approved=load(APPROVED);completion=load(RUN/'completion.json')
    if completion['supervisor']['status']!='finished':raise ValueError('worker has not finished')
    ledger=load(RUN/'spend-ledger.json');attempts=ledger['attempts']
    if ledger['config_sha256']!=digest(approved):raise ValueError('approved budget identity mismatch')
    results=[load(p) for p in (RUN/'results').glob('*.json')];by_id={r['sample_id']:r for r in results}
    if len(by_id)!=len(results):raise ValueError('duplicate result')
    counts=Counter();scopes={};reasoning_tokens=0
    for a in attempts:
        scope=a['scope'];s=scopes.setdefault(scope,{'attempts_accounted':0,'known_responses':0,'unknown_attempts':0,'known_cost_nano_usd':0,
            'reserved_unknown_nano_usd':0,'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'cache_write_tokens':0,'provider_latency_seconds':0.})
        s['attempts_accounted']+=1
        if a['status']=='interruption_unknown':
            s['unknown_attempts']+=1;s['reserved_unknown_nano_usd']+=a['charged_nano_usd'];continue
        body=load(RUN/'responses'/f"{a['attempt_id']:04}.json");usage=measured_cost(body,approved['pricing'])
        if body['id']!=a['response_id'] or usage!=a['usage'] or usage['cost_nano_usd']!=a['charged_nano_usd']:raise ValueError('usage/response mismatch')
        s['known_responses']+=1;s['known_cost_nano_usd']+=usage['cost_nano_usd'];s['provider_latency_seconds']+=a['latency_seconds']
        for k in ('input_tokens','output_tokens','cached_input_tokens','cache_write_tokens'):s[k]+=usage[k]
        reasoning_tokens+=(body.get('usage',{}).get('output_tokens_details') or {}).get('reasoning_tokens',0)
    config,asset=policy();index=cache_index();coverage=[];missing=[];missing_public=[]
    for meta,p in public_population():
        scope='train_validation' if meta['split'] in ('train','validation') else 'confirmation'
        ident=request_identity(p,config,asset);notes,origin=compatible(p,config,asset,index)
        row={**meta,'scope':scope,'request_sha256':digest(ident),'compatible_origin':origin}
        coverage.append(row);counts[(scope,meta['domain'],meta['split'],'covered' if origin else 'missing')]+=1
        if origin and p.sample_id in by_id and by_id[p.sample_id]['status']=='success':
            saved=load(RUN/'enrichment'/(p.sample_id+'.json'))
            if saved!=notes:raise ValueError('saved notes differ from verified cache')
        if not origin:
            missing.append(row);missing_public.append(row|{'public':{'sample_id':p.sample_id,'schema_version':p.schema_version,'input':p.input}})
    total_known=sum(v['known_cost_nano_usd'] for v in scopes.values())/1e9
    total_unknown=sum(v['reserved_unknown_nano_usd'] for v in scopes.values())/1e9
    total=total_known+total_unknown
    if total>approved['usd_cap']:raise ValueError('aggregate cap exceeded')
    finished=completion['supervisor']['updated_at_utc'];started=approved['authorized_at_utc']
    report={'audited_at_utc':now(),'worker_finished_at_utc':finished,'scopes':scopes,'known_usage_cost_usd':total_known,
        'unknown_reserved_usd':total_unknown,'charged_or_reserved_usd':round(total,9),'remaining_original_usd_cap':round(approved['usd_cap']-total,9),
        'pilot_cost_usd_separate':1.284679,'combined_pilot_and_full_upper_usd':round(total+1.284679,9),'reasoning_tokens_within_output':reasoning_tokens,
        'elapsed_hours_including_restarts':(datetime.fromisoformat(finished)-datetime.fromisoformat(started)).total_seconds()/3600,
        'coverage':dict(Counter((r['scope']+'/covered' if r['compatible_origin'] else r['scope']+'/missing') for r in coverage)),
        'per_partition_coverage':{'/'.join(k):v for k,v in counts.items()},'missing':missing,
        'source_implementation_matches_approval':implementation_identity()==approved['implementation_sha256'],
        'approved_config_sha256':file_hash(APPROVED),'ledger_sha256':file_hash(RUN/'spend-ledger.json'),
        'audit_script_sha256':file_hash(__file__),'new_paid_calls':0,'all_enrichment_covered':not missing,
        'original_deadline_utc':datetime.fromtimestamp(load(RUN/'supervisor-budget.json')['deadline_unix'],timezone.utc).isoformat(),
        'deadline_expired_at_audit':time.time()>load(RUN/'supervisor-budget.json')['deadline_unix']}
    atomic_json(RUN/'completion-cache-coverage.json',coverage);atomic_json(RUN/'completion-audit.json',report)
    atomic_json(RUN/'recovery-public-selection.json',missing_public)
    proposal={'enabled':False,'authorization':None,'mode':'two_record_restart_recovery','run_root':str(NATIVE/'p12-enrichment-recovery-01'),
        'usd_cap':2,'attempt_cap':6,'wall_seconds_cap':1800,'artifact_bytes_cap':20000000,
        'aggregate_original_cap_usd':475,'prior_charged_and_reserved_usd':round(total,9),
        'maximum_combined_full_and_recovery_usd':round(total+2,9),'selection_sha256':file_hash(RUN/'recovery-public-selection.json'),
        'provider_config':PILOT_CONFIG['provider_config'],'provider_sha256':digest(config),'asset_sha256':digest(asset),
        'public_records':len(missing_public),'approved_scopes':['train_validation'],'pricing':approved['pricing'],
        'fresh_pricing_verification_required':True,'new_execution_window_required':True,
        'original_failures_and_reservations_preserved':True,'cached_successes_must_not_be_repeated':True}
    atomic_json(RUN/'proposed-recovery.json',proposal)
    for name in ('completion-cache-coverage.json','completion-audit.json','recovery-public-selection.json','proposed-recovery.json'):
        shutil.copyfile(RUN/name,EXPORT/name)
    shutil.copyfile(__file__,RUN/'completion-audit-source.py')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
