"""Conservative recovery of this audited restart, without replaying unknown requests."""
from enrichment_run_control import *
from phi_jepa.providers.enrichment_budget import measured_cost
import fcntl

def main(expected_sha,expected_successes,sid,archive_tag):
    approved=load(APPROVED)
    if implementation_identity()!=approved['implementation_sha256'] or file_hash(ROOT/'tools/enrichment_run_control.py')!=approved['supervisor_sha256']:
        raise ValueError('approved source identity changed')
    if time.time()>=load(RUN/'supervisor-budget.json')['deadline_unix']:raise ValueError('original deadline expired')
    proof=load(approved['pricing_verification_path'])
    if (datetime.now(timezone.utc)-datetime.fromisoformat(proof['verified_at_utc'])).total_seconds()>=86400:raise ValueError('price proof expired')
    with (RUN/'supervisor.lock').open('a') as supervisor_lock,(RUN/'worker.lock').open('a') as worker_lock:
        fcntl.flock(supervisor_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(worker_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=load(RUN/'spend-ledger.json');rows=state['attempts']
        if file_hash(RUN/'spend-ledger.json')!=expected_sha or any(r['status'] not in ('response_received','interruption_unknown') for r in rows):raise ValueError('audited ledger changed')
        if state['config_sha256']!=digest(approved):raise ValueError('budget configuration changed')
        results=[load(p) for p in (RUN/'results').glob('*.json')]
        successes=[r for r in results if r['status']=='success']
        unknowns={r['sample_id'] for r in rows if r['status']=='interruption_unknown'}
        if len(successes)!=expected_successes or any(r['status']!='success' and r['sample_id'] not in unknowns for r in results):raise ValueError('audited result set changed')
        for row in rows:
            if row['status']=='interruption_unknown':
                if row['charged_nano_usd']!=row['reserved_nano_usd']:raise ValueError('previous unknown reserve changed')
                continue
            body=load(RUN/'responses'/f"{row['attempt_id']:04}.json")
            if body['id']!=row['response_id'] or measured_cost(body,approved['pricing'])!=row['usage']:raise ValueError('response/charge mismatch')
        for result in successes:
            cache=load(RUN/'context_cache'/(result['request_sha256']+'.json'))
            if cache['request_sha256']!=result['request_sha256'] or digest(cache['output'])!=cache['output_sha256']:raise ValueError('cache mismatch')
            if not (RUN/'enrichment'/(result['sample_id']+'.json')).exists():raise ValueError('notes missing')
        if (RUN/'results'/(sid+'.json')).exists():raise ValueError('orphan already reconciled')
        orphan=load(RUN/'provider_ledgers'/(sid+'.json'))
        if len(orphan['events'])!=1 or orphan['responses'] or orphan['events'][0]['usage']['input_tokens'] is not None:raise ValueError('orphan evidence changed')
        record=next(r for r in load(PILOT/'inventory-after.json') if r['sample_id']==sid)
        if orphan['events'][0]['request_sha256']!=record['request_sha256']:raise ValueError('orphan public identity mismatch')
        reserve_inputs=record['payload_bytes']+4096;reserve_outputs=policy()[0]['max_output_tokens'];prices=approved['pricing']
        if reserve_inputs>prices['short_context_input_limit']:raise ValueError('unpriced context')
        reserved=int((reserve_inputs*prices['reservation_input_usd_per_million']+reserve_outputs*prices['reservation_output_usd_per_million'])*1000)
        if '/' in archive_tag or '\\' in archive_tag or not archive_tag.startswith('recovery-'):raise ValueError('invalid archive tag')
        if len(rows)+1>approved['attempt_cap'] or sum(r['charged_nano_usd'] for r in rows)+reserved>approved['usd_cap']*1e9:raise ValueError('insufficient remaining global budget')
        if sum(r['charged_nano_usd'] for r in rows if r['scope']=='train_validation')+reserved>approved['scope_estimates']['train_validation']['proposed_usd_allocation']*1e9:raise ValueError('scope budget exhausted')
        archive=RUN/archive_tag;archive.mkdir(exist_ok=False)
        for name in ('spend-ledger.json','supervisor-status.json','supervisor-budget.json','status.json','launch.json'):
            if (RUN/name).exists():shutil.copyfile(RUN/name,archive/name)
        shutil.copyfile(RUN/'provider_ledgers'/(sid+'.json'),archive/'orphan-provider-ledger.json')
        # The ledger entry precedes dispatch in the adapter. Power loss cannot
        # prove whether this last request reached the service, so charge its full
        # reservation and do not replay it automatically.
        rows.append({'attempt_id':len(rows)+1,'scope':'train_validation','status':'interruption_unknown',
            'possible_attempt':True,'request_sha256':record['request_sha256'],'sample_id':sid,
            'reserved_input_tokens':reserve_inputs,'reserved_output_tokens':reserve_outputs,
            'reserved_nano_usd':reserved,'charged_nano_usd':reserved,'usage':None,
            'latency_unknown':True,'failure_type':'WorkstationRestartUnknownDispatch','recovered_at_utc':now()})
        atomic_json(RUN/'spend-ledger.json',state)
        atomic_json(RUN/'results'/(sid+'.json'),{'sample_id':sid,'scope':'train_validation','domain':record['domain'],'split':record['split'],
            'status':'failure','failure':'workstation_restart_unknown_dispatch_not_replayed','request_sha256':record['request_sha256'],
            'provider_events':orphan['events'],'recovery_reservation_usd':reserved/1e9})
        atomic_json(RUN/'supervisor-status.json',{'status':'interrupted','failure':'workstation restart; audited recovery complete','updated_at_utc':now()})
        evidence={'at_utc':now(),'verified_successes':expected_successes,'verified_usage_cost_usd':sum(r['charged_nano_usd'] for r in rows if r['status']=='response_received')/1e9,
            'charged_and_reserved_usd':sum(r['charged_nano_usd'] for r in rows)/1e9,
            'unknown_dispatch_sample_id':sid,'reserved_unknown_usd':reserved/1e9,'unknown_request_replayed':False,
            'caps_config_and_deadline_unchanged':True,'approved_config_sha256':file_hash(APPROVED),
            'prior_ledger_sha256':file_hash(archive/'spend-ledger.json'),'recovered_ledger_sha256':file_hash(RUN/'spend-ledger.json'),
            'source_sha256':file_hash(__file__)}
        atomic_json(archive/'reconciliation.json',evidence);atomic_json(EXPORT/(archive_tag+'-reconciliation.json'),evidence)
        shutil.copyfile(__file__,archive/'reconcile.py');print(json.dumps(evidence,indent=2));summary()

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--expected-ledger-sha256',required=True);parser.add_argument('--expected-successes',type=int,required=True)
    parser.add_argument('--sample-id',required=True);parser.add_argument('--archive-tag',required=True)
    args=parser.parse_args();main(args.expected_ledger_sha256,args.expected_successes,args.sample_id,args.archive_tag)
