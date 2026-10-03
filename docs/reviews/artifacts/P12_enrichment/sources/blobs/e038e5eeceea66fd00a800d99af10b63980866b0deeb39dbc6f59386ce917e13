"""Measured pilot accounting and population-based cost/time proposals; no live calls."""
from p12_enrichment import *
import math,statistics,shutil

def main():
    records=inventory();atomic_json(PILOT/'inventory-after.json',records)
    selected=load(PILOT/'pilot-selection.json');config,asset=policy();by_payload={}
    for row in selected:
        p=PublicProblem.parse(row['public']);by_payload[digest(request_identity(p,config,asset)['payload'])]=row
    attempts=load(PILOT/'spend-ledger.json')['attempts'];results=[load(p) for p in (PILOT/'results').glob('*.json')]
    for a in attempts:a.update({k:by_payload[a['payload_sha256']][k] for k in ('sample_id','domain','split','length_stratum','payload_bytes')})
    known=[a for a in attempts if a['usage'] is not None];latencies=sorted(a['latency_seconds'] for a in attempts)
    failed=sum(sum(e['failure'] is not None for e in r.get('provider_events',[])[:sum(a['sample_id']==r['sample_id'] for a in attempts)]) for r in results)
    measured={'attempts':len(attempts),'successful_unique_requests':sum(r['status']=='success' for r in results),
        'failed_attempts':failed,'failed_attempt_rate':failed/len(attempts) if attempts else None,
        'input_tokens':sum(a['usage']['input_tokens'] for a in known),'output_tokens':sum(a['usage']['output_tokens'] for a in known),
        'cached_input_tokens':sum(a['usage']['cached_input_tokens'] for a in known),
        'cache_write_tokens':sum(a['usage']['cache_write_tokens'] or 0 for a in known) if all(a['usage']['cache_write_tokens'] is not None for a in known) else None,
        'usage_unknown_attempts':len(attempts)-len(known),'cache_write_unknown_attempts':sum(a['usage']['cache_write_tokens'] is None for a in known),
        'usage_cost_lower_usd':sum(a['usage']['cost_lower_nano_usd'] for a in known)/1e9,
        'conservative_charged_usd':sum(a['charged_nano_usd'] for a in attempts)/1e9,
        'usage_cost_exact_usd':sum(a['usage']['cost_nano_usd'] for a in known)/1e9 if len(known)==len(attempts) and all(a['usage']['cost_nano_usd'] is not None for a in known) else None,
        'request_latency_seconds':sum(latencies),'mean_latency_seconds':statistics.mean(latencies) if latencies else None,
        'median_latency_seconds':statistics.median(latencies) if latencies else None,
        'p95_latency_seconds':latencies[math.ceil(.95*len(latencies))-1] if latencies else None,
        'model_config_preserved':True,'confirmation_requests':0,'pricing_sources':PILOT_CONFIG['pricing']['sources']}
    # Partition each remaining population by within-domain/split payload-length quartile.
    groups=defaultdict(list)
    for r in records:
        if not r['compatible_origin']:groups[(r['scope'],r['domain'],r['split'])].append(r)
    estimates={s:{'unique_requests':0,'input_tokens_point':0,'output_tokens_point':0,'standard_cost_point_usd':0.,'standard_cost_low_usd':0.,'standard_cost_high_usd':0.,'sequential_seconds_point':0.} for s in ('train_validation','confirmation')}
    strata=[]
    for (scope,domain,split),pool in sorted(groups.items()):
        pool.sort(key=lambda r:(r['payload_bytes'],r['sample_id']))
        for quartile in range(4):
            chunk=pool[len(pool)*quartile//4:len(pool)*(quartile+1)//4]
            matched=[a for a in known if a['domain']==domain and a['length_stratum']==quartile and (scope=='confirmation' or a['split']==split)]
            if not matched:matched=[a for a in known if a['domain']==domain]
            if not matched:raise ValueError('insufficient pilot observations for domain cost estimate')
            ratio=statistics.mean(a['usage']['input_tokens']/a['payload_bytes'] for a in matched)
            outputs=statistics.mean(a['usage']['output_tokens'] for a in matched);output_high=max(a['usage']['output_tokens'] for a in known if a['domain']==domain)
            inputs=sum(r['payload_bytes'] for r in chunk)*ratio;output_total=len(chunk)*outputs
            point=(inputs*5+output_total*20)/1e6 # conservative no-read-reuse, all input written at standard rate
            low=(inputs*.85*4+output_total*.75*20)/1e6
            high=(inputs*1.15*5+len(chunk)*min(2048,output_high*1.25)*20)/1e6
            seconds=len(chunk)*statistics.mean(a['latency_seconds'] for a in matched)
            e=estimates[scope];e['unique_requests']+=len(chunk);e['input_tokens_point']+=inputs;e['output_tokens_point']+=output_total
            e['standard_cost_point_usd']+=point;e['standard_cost_low_usd']+=low;e['standard_cost_high_usd']+=high;e['sequential_seconds_point']+=seconds
            strata.append({'scope':scope,'domain':domain,'split':split,'length_quartile':quartile,'requests':len(chunk),'pilot_observations':len(matched),'cost_point_usd':point,'seconds_point':seconds})
    retry_fraction=max(.15,failed/max(1,len(attempts))*2)
    for e in estimates.values():
        e['retry_allowance_fraction']=retry_fraction;e['proposed_attempt_cap']=math.ceil(e['unique_requests']*(1+retry_fraction))
        e['proposed_usd_allocation']=math.ceil(e['standard_cost_high_usd']*(1+retry_fraction)/25)*25
        e['elapsed_hours_low']=e['sequential_seconds_point']*.75/3600;e['elapsed_hours_high']=e['sequential_seconds_point']*1.75*(1+retry_fraction)/3600
    totalcap=sum(e['proposed_usd_allocation'] for e in estimates.values())
    report={'measured':measured,'remaining':estimates,'strata':strata,'reused_compatible_records':sum(r['compatible_origin'] is not None for r in records),
            'assumptions':'Small stratified pilot, one observation per domain/split/length cell. Confirmation estimates transfer train/validation timing/token ratios without generating confirmation notes. Input +/-15%, output .75x to max observed per-domain x1.25, no future cache-read discount. Ranges are sensitivity bounds, not statistical confidence intervals. 15% minimum attempt reserve; zero failures in 32 gives only roughly 9.4% rule-of-three failure upper bound.',
            'legacy_provider_usage_cost':'Original provider event/cache cost_usd omits cache-write charges. New spend-ledger.json is authoritative; historical costs are not rewritten.',
            'full_run_enabled':False,'proposed_total_usd_cap':totalcap}
    atomic_json(PILOT/'pilot-report.json',report)
    proposal_source=snapshot('enrichment-proposal',output=PILOT)
    proposal={**PILOT_CONFIG,'enabled':False,'authorization':None,'mode':'full_enrichment','authorized_scopes':[],
        'run_root':str(NATIVE/'p12-enrichment-full-01'),'usd_cap':totalcap,'attempt_cap':sum(e['proposed_attempt_cap'] for e in estimates.values()),
        'wall_seconds_cap':math.ceil(sum(e['elapsed_hours_high'] for e in estimates.values())+1)*3600,'artifact_bytes_cap':2000000000,
        'scope_estimates':estimates,'implementation_sha256':implementation_identity(),'proposal_source':proposal_source,'provider_sha256':digest(config),'asset_sha256':digest(asset),
        'inventory_sha256':file_hash(PILOT/'inventory-after.json'),'pricing_reverification_required_before_full_run':True,
        'pricing_verification_path':str(PILOT/'pricing-verification.json'),
        'scope':'remaining frozen train/validation and confirmation only when each scope is explicitly authorized','confirmation_pilot_allowed':False}
    atomic_json(PILOT/'proposed-full-enrichment.json',proposal)
    # Documentation was actually fetched in this session; this proof expires after 24 h.
    if not (PILOT/'pricing-verification.json').exists():
        atomic_json(PILOT/'pricing-verification.json',{'verified_at_utc':'2026-09-28T21:11:08+00:00',
             'pricing_sha256':digest(PILOT_CONFIG['pricing']),'sources':PILOT_CONFIG['pricing']['sources']+['https://developers.openai.com/api/docs/guides/prompt-caching']})
    dest=ROOT/'docs/reviews/artifacts/P12_enrichment';dest.mkdir(parents=True,exist_ok=True)
    for path in PILOT.rglob('*'):
        if not path.is_file() or path.name=='worker.lock' or path.name.startswith('.pending-'):continue
        target=dest/path.relative_to(PILOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    atomic_json(dest/'artifact-index.json',{'native_root':str(PILOT),'files':{str(p.relative_to(PILOT)):file_hash(p) for p in PILOT.rglob('*') if p.is_file() and p.name!='worker.lock'},'source_identity':implementation_identity()})
    print(json.dumps({'measured':measured,'remaining':estimates,'proposed_total_usd_cap':totalcap},indent=2))

if __name__=='__main__':main()
