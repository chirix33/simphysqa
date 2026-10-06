"""Inspect admitted public views only; never promote private events/outcomes."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
from itertools import chain
import argparse,math,time
from simphysqa.dataset import iter_source
from simphysqa.events import dec,POINTS,derive
from simphysqa.io import write,digest,DOMAINS,read

def inventory(release,plan_path,output):
    began=time.perf_counter();domains={d:{'qa_records':0,'groups':set(),'observed_timestamps':0,'cutoffs':Counter(),'relationships':Counter(),'records_with_active':0,'records_with_ended':0,'records_with_between':0} for d in DOMAINS}
    for record,location in chain.from_iterable(iter_source(file) for file in sorted(release.glob('**/shards/*.jsonl'))):
        inp=record['input'];domain=inp['domain']
        if domain not in domains:continue
        meta=record['metadata']
        if meta['validation']['status']!='accepted' or any(c['status']!='pass' for c in meta['validation']['checks']):raise ValueError('nonadmitted shard in public release scan')
        row=domains[domain];row['qa_records']+=1;row['groups'].add(meta['base_scenario_id']);row['observed_timestamps']+=len(inp['states']);row['cutoffs'][str(inp['observation_cutoff'])]+=1
        active=ended=between=False
        for event in inp['known_events']:
            start,end=dec(event['start_time']),dec(event['end_time'])
            for state in inp['states']:
                t=dec(state['timestamp'])
                if t>dec(inp['observation_cutoff']):raise ValueError('public state beyond established cutoff')
                if event['type']=='scheduled_intervention':
                    relationship='scheduled_future' if t<start else 'scheduled_empty_interval' if start==end else 'scheduled_active' if t<end else 'scheduled_interval_ended'
                elif event['type'] in POINTS and start==end:relationship='declared_point_future' if t<start else 'declared_point_at_timestamp' if t==start else 'declared_point_past'
                else:relationship='temporal_semantics_unresolved'
                row['relationships'][relationship]+=1;active|=relationship=='scheduled_active';ended|=relationship=='scheduled_interval_ended'
            for left,right in zip(inp['states'],inp['states'][1:]):
                l,r=dec(left['timestamp']),dec(right['timestamp'])
                if event['type']=='scheduled_intervention':between|=max(l,start)<min(r,end) or l<start<r or l<end<r
                elif event['type'] in POINTS:between|=l<start<r
        row['records_with_active']+=active;row['records_with_ended']+=ended;row['records_with_between']+=between
    for row in domains.values():
        row['trajectory_groups']=len(row.pop('groups'));row['cutoffs']=dict(row['cutoffs']);row['relationships']=dict(row['relationships'])
    proposal=[]
    for pair in read(plan_path)['pairs'][:4]:
        r=pair['source_wrapper'];inp=r['public']['input'];start=inp['known_events'][0]['start_time'];saved=r['private']['metadata']['simulation']['saved_state_interval_s']
        cutoff=round(math.ceil(start/saved)*saved,10)
        proposal.append({'proposal_id':'spq-event-view-proposal-'+digest({'parent':r['sample_id'],'cutoff':cutoff})[:24],
            'domain':inp['domain'],'parent_sample_id':r['sample_id'],'parent_group_id':r['trajectory_id'],
            'established_cutoff':inp['observation_cutoff'],'proposed_new_view_cutoff':cutoff,
            'status':'proposal_only_new_identity_not_exported','conditions':'Separate authorization, public-view construction/annotation validation and retained later target required; established QA unchanged.'})
    report={'version':'spq02-public-event-coverage/1.0.0','sampling_frame':'all actual admitted shards in the four-domain release; records and groups distinguished','domains':domains,
        'private_reference_events_or_states_used_for_coverage':False,'wall_seconds':time.perf_counter()-began,'new_view_proposals':proposal,'new_simulations':0}
    write(output,report);print(domains)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();inventory(a.release,a.plan,a.output)
