"""Historical source/cohort reconciliation using manifests and IDs, not test outcomes."""
from p12_common import *
from collections import defaultdict,Counter
from phi_jepa.integration.readers import json_lines
import re

def main():
    roots=[p for p in NATIVE.iterdir() if p.is_dir() and p.name.startswith(('p07','post-p07','p08','p10','p11'))]
    roots.extend(p for p in (NATIVE/'manual-outputs').iterdir() if p.is_dir())
    evidence=defaultdict(set);history=[]
    def walk(value,path):
        if isinstance(value,dict):
            if str(value.get('split','')).startswith(('test','ood_')):
                for k in ('sample_id','scenario_id','base_scenario_id','split_group'):
                    if isinstance(value.get(k),str):evidence[value[k]].add(str(path))
            for item in value.values():walk(item,path)
        elif isinstance(value,list):
            for item in value:walk(item,path)
    for root in roots:
        for name in ('selection.json','selected-public.json'):
            if (root/name).exists():walk(load(root/name),root/name)
        # Conservative: a cached/selected test item also counts as inspected.
        for p in root.rglob('*.json'):
            if re.fullmatch('[0-9a-f]{32}',p.stem):evidence[p.stem].add(str(p))
        stages=[]
        for p in [*root.glob('sources/*.json'),*root.glob('source/identity.json')]:
            identity=load(p);files=identity.get('files',{});verified=0;bad=[]
            for name,sha in files.items():
                blob=p.parent/'blobs'/sha
                if blob.exists() and file_hash(blob)==sha:verified+=1
                else:bad.append(name)
            stages.append({'manifest':str(p),'sha256':file_hash(p),'base_commit':identity.get('commit'),
                           'archived_files_verified':verified,'missing_or_mismatched_blobs':bad,
                           'entrypoints':{k:v for k,v in files.items() if k in ('tools/p11_numerical.py','tools/answer_pipeline.py','configs/study_p11_frozen.json','configs/model_context_p02b.json')}})
        history.append({'root':str(root),'source_stages':stages,
                        'configurations':{n:file_hash(root/n) for n in ('plan.json','config.json','selection.json','execution.json') if (root/n).exists()}})
    cat=catalog();exposed=[];unused=[]
    for domain,split in sorted(cat.partitions):
        if split in ('train','validation'):continue
        for record in json_lines(cat.verified_file(domain,split,'evaluator.jsonl')):
            m=record['metadata'];sid=record['sample_id'];scenario=m['base_scenario_id'];group=m['split_group_id']
            sources=set().union(*(evidence[x] for x in (sid,scenario,group)))
            row={'sample_id':sid,'scenario_id':scenario,'split_group':group,'domain':domain,'split':split,'distribution':m['distribution']}
            if sources:exposed.append(row|{'evidence':sorted(sources)})
            else:unused.append(row)
    # Propagate any exposure to all questions/horizons in that simulation.
    exposed_groups={r['scenario_id'] for r in exposed}
    newly=[r for r in unused if r['scenario_id'] in exposed_groups]
    exposed.extend(r|{'evidence':['another question in the same simulation was inspected']} for r in newly)
    unused=[r for r in unused if r['scenario_id'] not in exposed_groups]
    frozen=load(OUT/'confirmation-cohort.json')
    overlap=[r['sample_id'] for r in frozen if r['scenario_id'] in exposed_groups]
    if overlap:raise ValueError('frozen confirmation overlaps historical exposure: '+str(overlap))
    save(OUT/'previously-inspected-scenarios.json',exposed)
    save(OUT/'historical-reconciliation.json',{'runs':history,'inspected_questions':len(exposed),
        'inspected_scenarios':len(exposed_groups),'per_domain':dict(Counter(r['domain'] for r in exposed)),
        'policy':'conservative union of selected test IDs and artifact filenames; scenario-wide exclusion; no test reference values read',
        'confirmation_overlap':overlap,'unused_questions':len(unused),
        'reviewed_commit':'b2c19e096dadbac27d4bf6d56d10fb765a545419','current_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
    selected=[]
    for path in (NATIVE/'p11-tonight-01/models').rglob('selected.json'):
        if path.parent.name!='phi_jepa':continue
        v=load(path);checkpoint=path.parent/v['directory']/v['checkpoint']['file']
        selected.append({'selected_manifest':str(path),'manifest_sha256':file_hash(path),'checkpoint':str(checkpoint),
                         'verified':file_hash(checkpoint)==v['checkpoint']['sha256'],'selection':v})
    save(OUT/'historical-selected-checkpoints.json',selected)
    print({'inspected_questions':len(exposed),'inspected_scenarios':len(exposed_groups),'confirmation_overlap':overlap,'checkpoints_verified':sum(r['verified'] for r in selected)})
    print({'source_blob_gaps_by_run':{r['root']:sum(len(s['missing_or_mismatched_blobs']) for s in r['source_stages']) for r in history if any(s['missing_or_mismatched_blobs'] for s in r['source_stages'])}})

if __name__=='__main__':main()
