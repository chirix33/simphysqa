import sys,time,json
from pathlib import Path
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09');S=B/'complement-analysis-src-1.0.1'
sys.path.insert(0,str(S/'src'))
from simphysqa import complement_execution as c,restart_execution as recovery,execution_adapter as a
from simphysqa.main_analysis import assess
from simphysqa.heldout_scope import formal_scope
ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite');control=ledger.reserve_control('Ashraf','offline final-analysis source/config and preserved core primary-score equivalence',600);start=time.monotonic()
try:
 plan=a.read(B/'main-run-preflight-1.0.0/main-run-plan.json');manifest=a.read(B/'main-preparation-1.0.0/nested-200-manifest.json');scope=plan['generation_candidate_scope'];actual=recovery.combined_records(ledger)
 source=B/'restart-execution-1.0.0/central-analysis-1.0.0/analysis/main-analysis.json';previous=a.read(source);old={(r['sample_id'],r['condition_id'],r['input_condition']):r for r in previous['items']};checked=0
 with formal_scope(scope['candidates'],scope['excluded_groups']):
  for cid,label in c.COMBINATIONS:
   condition=next(r for r in plan['conditions'] if r['condition_id']==cid)
   for item in manifest['items']:
    sid=item['sample_id'];record=a.read(B/'main-preparation-1.0.0'/item['private_record'])
    if a.digest(record)!=item['record_sha256']:raise ValueError('private evidence changed')
    score=assess(record,condition,actual.get(a.stage_key(sid,cid,label,1)),actual.get(a.stage_key(sid,cid,label,2)));prior=old[(sid,cid,label)]
    for field in ('endpoints','completion_status','parsing','answer_valid'):
     if score[field]!=prior[field]:raise ValueError('preserved core mismatch '+sid+' '+field)
    checked+=1
 # Verify all copied scientific configs and scorer modules against existing repository.
 repo=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa');config={}
 for folder in ['configs/simphysqa','src/simphysqa']:
  for p in (S/folder).rglob('*'):
   if not p.is_file() or p.suffix=='.pyc' or '__pycache__' in p.parts:continue
   target=repo/p.relative_to(S)
   if a.sha(p)!=a.sha(target):raise ValueError('analysis science/source mismatch '+str(p))
   config[str(p)]=a.sha(p)
 ledger.settle_control(control,time.monotonic()-start)
 a.put(B/'complement-execution-1.0.0/analysis-source-equivalence-1.0.1.json',{'core_item_condition_rows_verified':checked,'primary_endpoints_parser_validity_generation_identical':True,'private_core_analysis_sha256':a.sha(source),'source_configuration_sha256':config,'inference_calls':0,'simulation_calls':0,'paid_annotation_calls':0,'control':control,'elapsed_seconds':time.monotonic()-start,'accounting':ledger.summary()})
 print(json.dumps({'checked':checked,'passed':True,'seconds':time.monotonic()-start}))
except BaseException:
 ledger.settle_control(control,time.monotonic()-start,'unknown');raise
finally:ledger.db.close()