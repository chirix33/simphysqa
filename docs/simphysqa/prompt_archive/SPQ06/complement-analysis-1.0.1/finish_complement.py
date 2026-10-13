"""Actual complement analysis /1.0.1. No inference and unchanged primary scorers."""
import argparse,csv,io,json,time,zipfile
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from simphysqa import execution_adapter as a,main_record_index,restart_execution,complement_execution as c,result_diagnostics as diagnostics
from simphysqa.main_analysis import assess,paired_intervals
from simphysqa.heldout_scope import formal_scope
from simphysqa.complement_preparation import ledger_snapshot
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN=B/'complement-execution-1.0.0';PREP=B/'main-preparation-1.0.0';OVERLAY=B/'complement-preparation-1.0.1'
COMB=c.COMBINATIONS

def metrics(records,keys):
 raws=[records[k] for k in keys if k in records];memory=[r['device_memory'] for r in raws if r.get('device_memory')]
 def total(field):
  vals=[r[field] for r in raws if isinstance(r.get(field),(float,int))];return sum(vals) if vals else None
 return {'canonical_stages':len(raws),'completion_statuses':dict(Counter(r['completion_status'] for r in raws)),
 'stage_latency_seconds':total('latency_seconds'),'total_stage_seconds':total('total_stage_seconds'),'input_tokens':total('input_tokens'),'output_tokens':total('output_tokens'),
 'memory_statuses':dict(Counter(m.get('status','unknown') for m in memory)),
 'device_sampled_peak_mib':max((m['sampled_peak_mib'] for m in memory if m.get('sampled_peak_mib') is not None),default=None),
 'successful_device_samples':sum(m.get('successful_sample_count',0) for m in memory) if memory else None,
 'memory_limitation':'device-wide sampled high-water mark, not continuous/process allocation; peaks can be missed',
 'termination_categories':dict(Counter(r.get('termination',{}).get('category','unavailable') for r in raws))}

def complete_coverage(initials,conditional,stages,routes,records):
 """Qualified coverage includes canonical failed outputs, excludes unresolved bytes."""
 supported=[k for k in conditional if k in routes and routes[k]['status']=='supported']
 known=lambda k:k in stages and stages[k][3] not in ('reserved_unknown','unknown','interrupted')
 return all(known(k) and k in records for k in initials) and all(k in routes for k in conditional) and all(known(k) and k in records for k in supported)


def finish(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
 ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite');freeze=a.read(RUN/'execution-freeze.json')
 try:
  core=restart_execution.combined_records(ledger);extension=main_record_index.canonical_records(ledger)
  if set(core)&set(extension):raise ValueError('core/complement stage identity overlap')
  manifest=a.read(PREP/'nested-200-manifest.json');cm=a.read(OVERLAY/'complement-manifest.json')
  if {r['group_id'] for r in manifest['items']}&{r['group_id'] for r in cm['items']}:raise ValueError('core/complement groups overlap')
  plan=a.read(B/'main-run-preflight-1.0.0/main-run-plan.json');scope=plan['generation_candidate_scope']
  rows={'core':[],'complement':[]};diagnostic_rows={'core':[],'complement':[]};parsed=[]
  with formal_scope(scope['candidates'],scope['excluded_groups']):
   for subset,items,records in [('core',manifest['items'],core),('complement',cm['items'],extension)]:
    for cid,label in COMB:
     condition=next(x for x in plan['conditions'] if x['condition_id']==cid)
     for item in items:
      sid=item['sample_id'];record=a.read(PREP/item['private_record'])
      if a.digest(record)!=item['record_sha256']:raise ValueError('private scoring evidence changed')
      first=records.get(a.stage_key(sid,cid,label,1));second=records.get(a.stage_key(sid,cid,label,2))
      row={**item,'condition_id':cid,'input_condition':label,**assess(record,condition,first,second),
      'raw_initial_result_sha256':a.digest(first) if first else None,'raw_continuation_result_sha256':a.digest(second) if second else None}
      rows[subset].append(row);diagnostic_rows[subset].append(diagnostics.diagnose(record,row,first,second))
      from simphysqa.spq06 import parse_answer
      for stage,raw in [(1,first),(2,second)]:
       if raw is None:continue
       value=None;diag=None;error=None
       try:value,diag=parse_answer(raw['raw_output'])
       except (ValueError,TypeError) as exc:error=str(exc)
       parsed.append({'subset':subset,'stage_key':a.stage_key(sid,cid,label,stage),'raw_result_sha256':a.digest(raw),'parsed_response':value,'parser_diagnostics':diag,'parser_error':error,'primary_item':row})
  # Assert core scoring did not change, rather than modifying preserved core outputs.
  previous_path=B/'restart-execution-1.0.0/central-analysis-1.0.0/analysis/main-analysis.json'
  previous=a.read(previous_path);old={(r['sample_id'],r['condition_id'],r['input_condition']):r for r in previous['items']}
  for r in rows['core']:
   prior=old[(r['sample_id'],r['condition_id'],r['input_condition'])]
   for field in ('endpoints','completion_status','parsing','answer_valid'):
    if r[field]!=prior[field]:raise ValueError('core primary changed: '+field)
  with (output/'original-recovered-core-analysis.json').open('xb') as f:f.write(previous_path.read_bytes())
  processes=ledger.db.execute('SELECT id,bound,actual,state FROM processes WHERE assignment IN (SELECT id FROM assignments WHERE owner=?)',('Ashraf',)).fetchall()
  own=a.read(RUN/'assignment.json')['id'];own_processes=ledger.db.execute('SELECT id,bound,actual,state FROM processes WHERE assignment=?',(own,)).fetchall()
  stage_rows=ledger.db.execute('SELECT key,process,request_hash,state FROM stages').fetchall();stages={r[0]:r for r in stage_rows}
  routes={k:json.loads(body) for k,body in ledger.db.execute('SELECT key,body FROM routes')}
  coverage=[]
  for cid,label in COMB:
   initials=[a.stage_key(r['sample_id'],cid,label,1) for r in cm['items']];conditional=[a.stage_key(r['sample_id'],cid,label,2) for r in cm['items'] if r['family']=='clarification']
   supported=[k for k in conditional if k in routes and routes[k]['status']=='supported']
   settled_initials=sum(k in stages and stages[k][3] not in ('reserved_unknown','unknown','interrupted') for k in initials)
   accounted_complete=settled_initials==200 and complete_coverage(initials,conditional,stages,routes,extension)
   allkeys=initials+conditional
   coverage.append({'condition_id':cid,'representation':label,'assigned_items':200,'initial_reserved':sum(k in stages for k in initials),'initial_canonical':sum(k in extension for k in initials),
   'initial_dispositions':dict(Counter(stages[k][3] if k in stages else 'never_reserved' for k in initials)),
   'conditional_routes':sum(k in routes for k in conditional),'supported_routes':len(supported),'unexecuted_conditional':sum(k in routes and routes[k]['status']!='supported' for k in conditional),
   'conditional_reserved':sum(k in stages for k in conditional),'conditional_canonical':sum(k in extension for k in conditional),
   'execution_and_coverage_accounting_complete':accounted_complete,'measurements':metrics(extension,allkeys)})
  full=all(r['execution_and_coverage_accounting_complete'] for r in coverage) and all(p[2] is not None and p[3] not in ('unknown','interrupted') for p in own_processes)
  outputs={}
  for subset,data in [('core',rows['core']),('complement',rows['complement']),('combined',rows['core']+rows['complement'])]:
   result={'version':'SPQ06-complement-analysis/1.0.1','subset':subset,'items':data,'independent_items':200 if subset!='combined' else 400,
   'actual_execution_coverage_complete':True if subset=='core' else full,'fixed_assigned_denominators':True,
   'uncertainty':paired_intervals(data,replicates=10000,seed=20261009),'model_calls':0,'post_core_results_expansion':True,
   'unchanged_scorers':True,'human_prose_quality':'uncollected','collaborator_extension':'not authorized/executed; comparisons remain on common core200',
   'coverage':coverage if subset!='core' else None}
   a.put(output/(subset+'-analysis.json'),result);outputs[subset]=result
  for subset in ('core','complement'):a.put(output/(subset+'-diagnostics.json'),diagnostics.summarize(diagnostic_rows[subset]))
  a.put(output/'central-parsed-records.json',{'items':parsed,'primary_parser_unchanged':True,'parser_scorer_sha256':{name:a.sha(Path(__file__).parent/'src/simphysqa'/(name+'.py')) for name in ('spq06','main_analysis','scoring','explanation_evaluation','clarification_evaluation')}})
  a.put(output/'coverage.json',{'combinations':coverage,'all_eight_complete':full,'assigned_complement_unique_items':200,'actual_core_items':200,'combined_assigned_unique_items':400,'no_collaborator_extension':True})
  # Paper tables and prose intentionally exclude operational interruption/accounting history.
  complete_combinations={(r['condition_id'],r['representation']) for r in coverage if r['execution_and_coverage_accounting_complete']}
  text=['# Ashraf evaluation tables','', 'The 400-item pool and nested 200-item core were frozen before answering. The decision to execute the remaining 200 items was made after core results were available. Items were not selected or replaced using model scores. The eight Ashraf condition/representation combinations share the same balanced items. Other conditions require comparisons on the common core 200.','', 'Automatic explanation factual checks do not measure prose adequacy; human judgments remain uncollected. Clarification is explicit query-gap behavior and supports no OOD claim.','']
  text+=['The core and complement each contain 40 items per family and ten groups per domain-family cell. The complete union contains 80 items per family and twenty groups per cell. Each condition/representation retains its fixed 200 or 400 assigned-item denominator. Bootstrap draws are paired whole-trajectory samples within domain-family strata, with seed 20261009 and 10,000 replicates. Intervals are descriptive and marginal, not multiplicity-adjusted. Degenerate observed bootstrap support does not establish zero population uncertainty.','']
  for subset in ('core','complement','combined'):
   result=outputs[subset];text += [f'## {subset}: {result["independent_items"]} assigned unique items', '', 'Execution/coverage accounting complete: '+str(result['actual_execution_coverage_complete'])+'. Missing and failed items retain primary denominators.', '', '| Condition | Input | Family | Endpoint | Estimate | 95% interval |', '|---|---|---|---|---:|---|']
   for x in result['uncertainty']['summaries']:
    if subset=='combined' and (x['condition_id'],x['input_condition']) not in complete_combinations:continue
    if x['endpoint'] not in ('typed_correct','structured_facts_all_correct','reply_routed','resolved_answer_correct'):continue
    lo,hi=x['interval_95'];text.append(f'| {x["condition_id"]} | {x["input_condition"]} | {x["family"]} | {x["endpoint"]} | {100*x["balanced_domain_mean"]:.1f}% | [{100*lo:.1f}, {100*hi:.1f}]% |')
   text+=['','| Matched ablation | Family | Endpoint | Structured minus enriched | Paired 95% interval |','|---|---|---|---:|---|']
   for x in result['uncertainty']['paired_comparisons']:
    if subset=='combined' and (tuple(x['condition_a']) not in complete_combinations or tuple(x['condition_b']) not in complete_combinations):continue
    if x['condition_a'][1]!='structured_only' or x['endpoint'] not in ('typed_correct','structured_facts_all_correct','reply_routed','resolved_answer_correct'):continue
    lo,hi=x['paired_interval_95'];text.append(f'| {x["condition_a"][0]} | {x["family"]} | {x["endpoint"]} | {100*x["difference_a_minus_b"]:.1f} pp | [{100*lo:.1f}, {100*hi:.1f}] pp |')
   text+=['']
  (output/'paper-results.md').write_text('\n'.join(text),encoding='utf8')
  # Before/after original rows must remain, except explicitly revised current ceiling rows.
  before=a.read(RUN/'ledger-before.json');after=ledger_snapshot(ledger.path);preserved={}
  for table,oldrows in before['table_rows'].items():
   if table=='meta':oldrows=[r for r in oldrows if r[0]!='ceiling']
   elif table=='executor_allocations':oldrows=[r for r in oldrows if r[0]!='Ashraf']
   newrows={a.canonical(r) for r in after['table_rows'].get(table,[])};preserved[table]=all(a.canonical(r) in newrows for r in oldrows)
  if not all(preserved.values()):raise ValueError('original ledger rows not preserved')
  baseline=a.read(B/'complement-delivery-1.0.0/preservation.json')
  a.put(output/'original-ledger-preservation.json',{'original_rows_preserved':preserved,'only_current_approved_ceiling_rows_revised':True,'historical_6600_charge_retained':True,'baseline_receipt_sha256':a.sha(B/'complement-delivery-1.0.0/preservation.json')})
  a.put(output/'operational-accounting-before-final-settlement.json',{'summary':ledger.summary(),'complement_processes':own_processes,'nested_stage_timing_not_added_to_lifecycle':True,'paper_prose_excludes_operational_history':True})
  examples=[]
  for cid,label in COMB:
   for family in ('direct','predictive','counterfactual','explanation','clarification'):
    item=next(r for r in cm['items'] if r['family']==family);key=a.stage_key(item['sample_id'],cid,label,1)
    initial=a.read(OVERLAY/'public'/a.read(OVERLAY/'public/execution-inputs.json')['requests'][key]['path']);raw=extension.get(key)
    a.put(output/'exact-examples'/f'{cid}--{label}--{family}.json',{'stage_key':key,'exact_request':initial,'exact_response_record':raw,'response_not_invented':True})
  bundle_manifest={'version':'SPQ06-complement-audit/1.0.0','original_core_analysis_sha256':a.sha(previous_path),'scope':c.SCOPE,'post_core_results_expansion':True,'private_audit_material':True,'paths':{}}
  bundle=output/'audit-bundle-1.0.0.zip'
  with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
   roots=[(output,'analyses'),(RUN/'import-receipts','import-receipts'),(RUN/'central-stage-records','central-stage-records'),(RUN/'accounting-snapshots','accounting-snapshots'),(RUN/'returns','actual-return-envelopes'),(RUN/'preflights','fresh-preflights'),(RUN/'qualification','qualification'),(RUN/'routes','actual-routing'),(RUN/'verification','token-measurement-checks')]
   for root,label in roots:
    for file in sorted(root.rglob('*')) if root.exists() else []:
     if not file.is_file() or file==bundle:continue
     name=label+'/'+file.relative_to(root).as_posix();bundle_manifest['paths'][name]=a.sha(file);archive.write(file,name)
   for file in [RUN/'execution-freeze.json',RUN/'budget-revision.json',RUN/'registration.json',RUN/'assignment.json',RUN/'ledger-before.json']:
    name='authorization-accounting/'+file.name;bundle_manifest['paths'][name]=a.sha(file);archive.write(file,name)
   archive.writestr('audit-file-manifest.json',a.canonical(bundle_manifest))
  a.put(output/'audit-export-receipt.json',{'path':str(bundle),'sha256':a.sha(bundle),'bytes':bundle.stat().st_size,'files':len(bundle_manifest['paths']),'private_audit_material':True,'operational_record_not_paper_narrative':True})
  ledger.settle_control(freeze['analysis_control'],time.monotonic()-started,'complete')
  a.put(output/'final-accounting.json',ledger.summary())
  a.put(output/'manifest.json',{'files':a.files(output),'complete_eight_combination_extension':full,'unchanged_core_primary':True,'completed_utc':datetime.now(timezone.utc).isoformat()})
  print(json.dumps({'full_coverage':full,'core':len(core),'complement':len(extension),'analysis':str(output),'accounting':ledger.summary()}),flush=True)
 except BaseException:
  # Unknown actual analysis work retains its bound; no silent replacement release.
  if ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(freeze['analysis_control'],)).fetchone()[0] is None:ledger.settle_control(freeze['analysis_control'],time.monotonic()-started,'unknown')
  raise
 finally:ledger.db.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);finish(p.parse_args().output)