"""New recovery analysis/audit bundle; immutable originals and unchanged scores."""
import sys,time,json,shutil,zipfile
from pathlib import Path
from collections import Counter
from simphysqa import execution_adapter as a,restart_execution as recovery,result_diagnostics as diagnostic
from simphysqa.main_analysis import paired_intervals
from simphysqa.heldout_scope import formal_scope
BASE=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
ORIGINAL=BASE/'main-ashraf-1.0.0';RUN=BASE/'restart-execution-1.0.0';CENTRAL=BASE/'central-main-1.0.0/main.sqlite';PACKAGE=BASE/'execution-public-1.1.1';REPO=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
SHARDS=['qwen3_8b_direct--enriched','qwen3_8b_thinking--enriched','llama31_8b_direct--enriched','llama31_8b_cot--enriched','qwen3_32b_awq_off--enriched','qwen3_32b_awq_on--enriched','qwen3_8b_direct--structured_only','qwen3_32b_awq_on--structured_only']
a.canonical_records=recovery.combined_records

def copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(Path(source).read_bytes())

def finish():
 if not (RUN/'execution-completion.json').exists() or (RUN/'QUEUE-PAUSED.json').exists():raise ValueError('recovery execution not complete')
 ledger=recovery.Ledger(CENTRAL);control=ledger.reserve_control('Ashraf','unchanged recovered central analysis, diagnostic classification, preservation and audit export',1800);start=time.monotonic()
 output=RUN/'delivery-1.0.0';output.mkdir(exist_ok=False)
 try:
  a.put(output/'analysis-procedure-freeze.json',{'sources':a.files(Path(__file__).parent),'diagnostics_sha256':a.sha(REPO/'src/simphysqa/result_diagnostics.py'),
   'unchanged_scoring_sources':{name:a.sha(REPO/'src/simphysqa'/(name+'.py')) for name in ('spq06','scoring','main_analysis','clarification_evaluation','explanation_evaluation')},'new_answering_calls':0})
  result=a.analysis_bridge(ledger,BASE/'main-run-preflight-1.0.0/main-run-plan.json',RUN/'central-analysis-1.0.0')
  rows=[r for r in result['items'] if r['condition_id']+'--'+r['input_condition'] in SHARDS]
  if len(rows)!=1600 or len({r['sample_id'] for r in rows})!=200:raise ValueError('fixed denominators changed')
  uncertainty=paired_intervals(rows);recovered={'version':'SPQ06-Ashraf-recovered-analysis/1.0.0','scope':'Ashraf share; explicitly post-result authorized external interruption recovery','items':rows,'uncertainty':uncertainty,'missing_collaborator_rows':600,'human_explanation_quality':'uncollected'}
  a.put(output/'recovered-fixed-denominator-analysis.json',recovered)
  oldpath=ORIGINAL/'delivery-1.0.0/ashraf-fixed-denominator-analysis.json';old=a.read(oldpath);copy(oldpath,output/'original-fixed-denominator-analysis.json')
  oldmap={(r['sample_id'],r['condition_id'],r['input_condition']):r for r in old['items']};eligible={r['key'] for r in ledger.freeze['eligible']}
  for r in rows:
   if a.stage_key(r['sample_id'],r['condition_id'],r['input_condition'],1) not in eligible and r!=oldmap[(r['sample_id'],r['condition_id'],r['input_condition'])]:raise ValueError('unaffected primary row changed')
  records=recovery.combined_records(ledger);oldrecords=recovery.original_records(ledger);plan=a.read(BASE/'main-run-preflight-1.0.0/main-run-plan.json');preparation=Path(plan['preparation']);scope=plan['generation_candidate_scope']
  diagnostic_sets={}
  with formal_scope(scope['candidates'],scope['excluded_groups']):
   for name,items,actual in [('original',old['items'],oldrecords),('recovered',rows,records)]:
    ds=[]
    for row in items:
     record=a.read(preparation/row['private_record']);first=actual.get(a.stage_key(row['sample_id'],row['condition_id'],row['input_condition'],1));second=actual.get(a.stage_key(row['sample_id'],row['condition_id'],row['input_condition'],2))
     ds.append(diagnostic.diagnose(record,row,first,second))
    diagnostic_sets[name]=diagnostic.summarize(ds);a.put(output/(name+'-reporting-diagnostics.json'),diagnostic_sets[name])
  def summary(data):return {(r['condition_id'],r['input_condition'],r['family'],r['endpoint']):r for r in data['uncertainty']['summaries']}
  originals=summary(old);comparisons=[]
  for key,r in summary(recovered).items():
   comparisons.append({'condition_id':key[0],'representation':key[1],'family':key[2],'endpoint':key[3],
    'original_rate':originals[key]['balanced_domain_mean'],'recovered_rate':r['balanced_domain_mean'],'original_interval_95':originals[key]['interval_95'],'recovered_interval_95':r['interval_95'],'fixed_family_denominator':40})
  pairs=[{'analysis_version':name,**p} for name,data in [('original',old),('recovered',recovered)] for p in data['uncertainty']['paired_comparisons'] if p['condition_a'][0]==p['condition_b'][0] and p['condition_a'][1]!=p['condition_b'][1]]
  coverage=[]
  for shard in SHARDS:
   cid,label=shard.split('--')
   for name,actual in [('original',oldrecords),('recovered',records)]:
    initials=[r for k,r in actual.items() if k.split('|')[1:3]==[cid,label] and k.endswith('|1')];seconds=[r for k,r in actual.items() if k.split('|')[1:3]==[cid,label] and k.endswith('|2')]
    coverage.append({'analysis_version':name,'condition_id':cid,'representation':label,'fixed_items':200,'initials_saved':len(initials),'initial_statuses':dict(Counter(r['completion_status'] for r in initials)),'initials_missing':200-len(initials),'continuations_saved':len(seconds),'continuation_statuses':dict(Counter(r['completion_status'] for r in seconds)),'possible_conditionals':40})
  a.put(output/'original-versus-recovered.json',{'coverage':coverage,'endpoints':comparisons,'paired_ablations':pairs,'scientific_scoring_changed':False,'exception_authorized_after_original_results':True,'selection_by_external_interruption_not_accuracy':True})
  recovery_raw=[r for k,r in records.items() if k in eligible or k[:-1]+'1' in eligible and k.endswith('|2')]
  runtimes=[a.read(p) for p in (RUN/'jobs').glob('*/worker-output/runtime.json')]
  a.put(output/'recovery-execution-measurements.json',{'actual_stage_count':len(recovery_raw),'initial_statuses':dict(Counter(r['completion_status'] for r in recovery_raw if r['stage']==1)),'continuation_statuses':dict(Counter(r['completion_status'] for r in recovery_raw if r['stage']==2)),
   'generation_latency_seconds':sum(r['latency_seconds'] for r in recovery_raw),'total_stage_seconds':sum(r['total_stage_seconds'] for r in recovery_raw),'input_tokens':sum(r['input_tokens'] for r in recovery_raw),'output_tokens':sum(r['output_tokens'] for r in recovery_raw),
   'loading_seconds':sum(r['load_seconds'] for r in runtimes),'termination_categories':dict(Counter(r['termination']['category'] for r in recovery_raw)),
   'memory_availability':dict(Counter(r['device_memory']['status'] for r in recovery_raw)),'sampled_stage_peak_mib':max((r['device_memory']['sampled_peak_mib'] for r in recovery_raw if r['device_memory']['sampled_peak_mib'] is not None),default=None),
   'memory_successful_samples':sum(r['device_memory']['successful_sample_count'] for r in recovery_raw),'sampled_peak_not_true_peak':True,'processes':[{'id':i,'bound':b,'actual':t,'state':s} for i,b,t,s in ledger.db.execute('SELECT p.id,p.bound,p.actual,p.state FROM processes p JOIN restart_processes r ON r.id=p.id')]})
  preserved=a.read(RUN/'preservation-before.json');changed=[p for p,h in preserved.items() if a.sha(p)!=h]
  original_sql=a.read(RUN/'original-ledger-snapshot.json');sql_changed=[]
  for table,oldrows in original_sql.items():
   now={tuple(r) for r in ledger.db.original.execute('SELECT * FROM '+table).fetchall()}
   if any(tuple(r) not in now for r in oldrows):sql_changed.append(table)
  if changed or sql_changed:raise ValueError('historical preservation failed')
  a.put(output/'preservation-after.json',{'files_checked':len(preserved),'changed':changed,'original_sql_tables_checked':list(original_sql),'original_sql_rows_changed':sql_changed,
   'original_unknown_process':ledger.db.original.execute('SELECT id,bound,actual,state FROM processes WHERE id=?',(ledger.freeze['eligible'][0]['original_process'],)).fetchone(),
   'all_preserved':True,'unchanged_selected_size':200,'unchanged_pool_size':400,'sealed_package_unchanged':True})
  bundle=RUN/'audit-bundle-1.0.0';bundle.mkdir()
  for p in output.iterdir():
   if p.is_file():copy(p,bundle/'analysis'/p.name)
  for source in [ORIGINAL/'delivery-1.0.0/resource-accounting.json',ORIGINAL/'central-analysis-1.0.0/central-parsed-records.json',ORIGINAL/'restart-recovery-1.0.0/recovery-receipt.json']:
   copy(source,bundle/'original'/source.name)
  for p in [RUN/'eligibility-freeze.json',RUN/'execution-completion.json',RUN/'saved-output-search.json',RUN/'original-ledger-snapshot.json']:
   copy(p,bundle/'recovery'/p.name)
  for rootname in ['import-receipts','verification','central-stage-records','routes','accounting']:
   for p in (RUN/rootname).rglob('*'):
    if p.is_file():copy(p,bundle/'recovery'/rootname/p.relative_to(RUN/rootname))
  copy(RUN/'central-analysis-1.0.0/central-parsed-records.json',bundle/'recovery/central-parsed-records.json')
  spec=a.read(PACKAGE/'execution-spec.json');examples=[]
  chosen=[next(r for r in ledger.freeze['eligible'] if r['family']==family)['key'] for family in ('predictive','counterfactual','explanation','clarification')]
  chosen.extend(next(a.stage_key(r['sample_id'],r['condition_id'],r['representation'],1) for r in diagnostic_sets['original']['items'] if r['condition_id']==cid and r['category']=='json_parsing_failure') for cid in ('llama31_8b_direct','llama31_8b_cot'))
  for key in chosen:
   source_set=RUN if key in eligible else ORIGINAL;sid,cid,label,stage=key.split('|');sources=[p for p in source_set.glob('jobs/*/worker-output/results/'+sid+'-stage1.json') if a.read(p).get('condition_id')==cid and a.read(p).get('representation')==label]
   if len(sources)!=1:raise ValueError('example raw source ambiguous')
   directory=bundle/'exact-examples'/(cid+'--'+label+'--'+sid);raw=sources[0];request=raw.parent.parent/'executed-requests'/raw.name;prompt=raw.parent.parent/'tokenized-prompts'/raw.name
   for p in [raw,request,prompt]:copy(p,directory/({'results':'raw-response.json','executed-requests':'request.json','tokenized-prompts':'rendered-token-ids.json'}[p.parent.name]))
   if a.sha(request)!=spec['requests'][key]['sha256']:raise ValueError('example original request bytes changed')
   examples.append({'key':key,'source_raw':str(raw),'raw_sha256':a.sha(raw),'request_sha256':a.sha(request),'path':str(directory.relative_to(bundle))})
  a.put(bundle/'exact-examples/index.json',examples)
  for name in ('restart_execution','result_diagnostics'):copy(REPO/'src/simphysqa'/(name+'.py'),bundle/'procedures'/(name+'.py'))
  for directory in [BASE/'restart-execution-src-1.0.0',Path(__file__).parent]:
   for p in directory.iterdir():
    if p.is_file():copy(p,bundle/'procedures'/p.name)
  for p in [BASE/'restart-execution-offline-1.0.1.log',BASE/'restart-diagnostics-offline-1.0.0.log',BASE/'restart-final-offline-1.0.0.log',BASE/'restart-history-offline-1.0.0.log',BASE/'restart-reporting-offline-1.0.1.log',RUN/'initial-offline-fixture-failure.json']:copy(p,bundle/'offline-tests'/p.name)
  ledger.settle_control(control,time.monotonic()-start);accounting=ledger.summary()
  oldaccount=a.read(ORIGINAL/'delivery-1.0.0/resource-accounting.json')
  a.put(output/'resource-accounting.json',{'current':accounting,'original':oldaccount,'additional_accounted_seconds':accounting['accounted_seconds']-oldaccount['accounted_seconds'],'original_6600_second_charge_unchanged':True})
  copy(output/'resource-accounting.json',bundle/'analysis/resource-accounting.json')
  a.put(bundle/'README.json',{'scope':'private organizer audit bundle','original_primary_analysis_preserved':True,'recovery_explicitly_authorized_after_results':True,'diagnostics_not_primary_rescoring':True,'request_raw_examples_exact_bytes':True,'no_human_ratings':True,'collaborator_not_executed':True,'accounting_boundary':'central parsing/scoring/diagnostics/preservation/example copying complete before final index and zip serialization; packaging overhead separately accounted'})
  mappings=[]
  for path,h in a.files(RUN).items():
   kind='recovery provenance/control/analysis evidence'
   if path.startswith('jobs/') and '/worker-output/results/' in path:kind='actual authorized recovery answering output'
   elif path.startswith('jobs/') and '/worker-output/executed-requests/' in path:kind='actual executed unchanged answering request'
   elif path.startswith('jobs/') and '/worker-output/tokenized-prompts/' in path:kind='deterministic rendering/tokenization of actual request'
   elif path.startswith(('returns/','immutable-imports/')):kind='transport copy; not an additional model call'
   elif path.startswith('central-analysis-'):kind='canonical projection and unchanged primary scoring'
   elif path.startswith('routes/'):kind='actual first-turn routing and preserved null-history linkage'
   mappings.append({'path':path,'sha256':h,'procedure_class':kind})
  a.put(bundle/'per-file-procedure-index.json',{'root':str(RUN),'files':mappings,'new_annotations':0,'new_simulations':0,'self_and_later_final_receipts_excluded':True})
  a.put(bundle/'file-manifest.json',{'files':a.files(bundle),'excludes_self':True})
  packaging=ledger.reserve_control('Ashraf','final recovery bundle hash verification and compression',600);packstart=time.monotonic()
  for name,h in a.read(bundle/'file-manifest.json')['files'].items():
   if a.sha(bundle/name)!=h:raise ValueError('bundle file hash changed')
  archive=RUN/'audit-bundle-1.0.0.zip';a.zip_export(bundle,archive)
  ledger.settle_control(packaging,time.monotonic()-packstart)
  a.put(RUN/'audit-export-receipt.json',{'archive':str(archive),'sha256':a.sha(archive),'bytes':archive.stat().st_size,'accounting':ledger.summary(),'all_manifest_hashes_verified':True,'final_packaging_control':packaging})
  a.put(RUN/'completion-accounting.json',ledger.summary());print('recovered stages',len(recovery_raw),'accounting',ledger.summary(),flush=True)
 except BaseException:
  if ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(control,)).fetchone()[0] is None:ledger.settle_control(control,time.monotonic()-start,'unknown')
  raise
 finally:ledger.db.close()
if __name__=='__main__':finish()
