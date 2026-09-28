"""Future calibration/OOD manifests only; no reference outcomes or calls."""
from p11_common import *
from phi_jepa.integration.readers import json_lines
from collections import defaultdict

def seal():
    cat=catalog();plan=load(OUT/'plan.json');rows=load(OUT/'selected-public.json');result={}
    for domain in plan['cohorts']:
        result[domain]={};selection={r['scenario_id'] for r in rows if r['domain']==domain and r['split']=='validation'}
        for split in ('validation','ood_parameter_extrapolation','ood_unseen_combination','ood_timed_event'):
            groups=defaultdict(list)
            for row in json_lines(cat.verified_file(domain,split,'evaluator.jsonl')):groups[row['metadata']['base_scenario_id']].append(row['sample_id'])
            ordered=sorted((g for g in groups if g not in selection),key=lambda g:digest(f'p11-sealed|11|{domain}|{split}|{g}'))[:20]
            result[domain]['calibration' if split=='validation' else split]={'scenario_ids':ordered,'sample_ids':[sid for g in ordered for sid in groups[g]],'status':'sealed_not_evaluated','reference_outcomes_opened':False,'selection_excluded':sorted(selection) if split=='validation' else []}
    save(OUT/'sealed_inventory.json',{'release_identity':cat.identity,'plan_sha256':file_hash(OUT/'plan.json'),'domains':result,'old_P10_inventory_preserved':True,'calibration_executed':False})

if __name__=='__main__':seal()
