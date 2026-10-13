"""Verify recovery raw hashes and export reporting/accounting addendum; no inference."""
import time,json,zipfile
from pathlib import Path
from simphysqa import complement_execution as c,execution_adapter as a,result_diagnostics as d
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN=B/'complement-execution-1.0.0'; O=B/'complement-analysis-1.0.1'; REC=B/'restart-execution-1.0.0'; OUT=B/'complement-closure-1.0.1'
ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite'); control=ledger.reserve_control('Ashraf','final recovery raw-hash and paper diagnostic verification/export',300);started=time.monotonic()
try:
 OUT.mkdir(exist_ok=False)
 index=a.read(REC/'postcommit-file-index.json')['files'];bad=[]
 for name,expected in index.items():
  p=Path(name);p=p if p.is_absolute() else REC/p
  if not p.is_file() or a.sha(p)!=expected:bad.append(str(p))
 old=a.read(REC/'central-analysis-1.0.0/analysis/main-analysis.json')['items'];new=a.read(O/'core-analysis.json')['items']
 lookup={(r['sample_id'],r['condition_id'],r['input_condition']):r for r in new};raw_mismatch=[]
 for row in [r for r in old if (r['condition_id'],r['input_condition']) in c.COMBINATIONS]:
  key=(row['sample_id'],row['condition_id'],row['input_condition'])
  for field in ('raw_initial_result_sha256','raw_continuation_result_sha256'):
   if row[field]!=lookup[key][field]:raw_mismatch.append([list(key),field])
 if bad or raw_mismatch:raise ValueError('recovered core evidence changed: '+str((bad+raw_mismatch)[:5]))
 a.put(OUT/'recovered-core-preservation.json',{'recovery_files_checked':len(index),'changed':bad,'core_rows_checked':len(new),'raw_initial_and_continuation_hash_mismatches':raw_mismatch,'primary_scoring_unchanged':True})
 diagnostic=d.summarize(a.read(O/'core-diagnostics.json')['items']+a.read(O/'complement-diagnostics.json')['items'])
 a.put(OUT/'combined-reporting-diagnostics.json',diagnostic)
 text=['# Scientific outcomes and interface diagnostics','',
 'All eight Ashraf combinations evaluate the same 400 assigned QA, 80 per family and twenty original groups per domain-family cell. The complement was executed after core scores were available, using the already frozen pool/order. Primary scoring and fixed denominators are unchanged. The tables below separate interface/generation failures from valid-but-incorrect answers; they do not infer correctness from a parsing failure. Counts are item-level first-stage categories, not additional independent samples. Clarification continuation categories are separate.','',
 'Automatic explanation factual checks do not establish prose adequacy. Explicit query gaps support no OOD claim. Other conditions require common-core comparisons. Raw parsing surfaces are descriptive diagnostics; fenced JSON plus trailing prose remains rejected by the primary parser.','',
 '| Condition | Input | Assigned | First-stage category | Count |', '|---|---|---:|---|---:|']
 for row in diagnostic['summaries']:
  for category,count in row['first_stage_categories'].items():text.append(f'| {row["condition_id"]} | {row["representation"]} | {row["fixed_items"]} | {category} | {count} |')
 text += ['', '| Condition | Input | Clarification continuation category | Count |', '|---|---|---|---:|']
 for row in diagnostic['summaries']:
  for category,count in row['clarification_continuation_categories'].items():text.append(f'| {row["condition_id"]} | {row["representation"]} | {category} | {count} |')
 text += ['', '| Condition | Input | Parsing failure surface | Count |', '|---|---|---|---:|']
 for row in diagnostic['summaries']:
  for category,count in row['parser_failure_surfaces'].items():text.append(f'| {row["condition_id"]} | {row["representation"]} | {category} | {count} |')
 (OUT/'paper-diagnostics.md').write_text('\n'.join(text),encoding='utf8')
 a.put(OUT/'accounting-before-final-settlement.json',{'summary':ledger.summary(),'current_export_control_is_reserved':control,'final_settlement_is_separate':'accounting.json'})
 a.put(OUT/'provenance.json',{'procedure_sha256':a.sha(Path(__file__)),'main_audit_sha256':a.sha(O/'audit-bundle-1.0.0.zip'),'immutable_analysis_manifest_sha256':a.sha(O/'manifest.json'),'recovery_file_index_sha256':a.sha(REC/'postcommit-file-index.json'),'model_calls':0})
 with zipfile.ZipFile(OUT/'audit-addendum.zip','x',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(OUT.glob('*.json')):z.write(p,p.name)
  z.write(OUT/'paper-diagnostics.md','paper-diagnostics.md')
  for p in [RUN/'final-delivery-1.0.0.json',RUN/'final-preservation-1.0.1.json',B/'complement-preservation-final-1.0.0.log',B/'complement-preservation-final-1.0.1.log',Path(__file__)]:z.write(p,'closure-records/'+p.name)
 ledger.settle_control(control,time.monotonic()-started,'complete')
 a.put(OUT/'accounting.json',ledger.summary())
 a.put(OUT/'manifest.json',{'files':a.files(OUT),'audit_addendum_sha256':a.sha(OUT/'audit-addendum.zip'),'main_audit_sha256':a.sha(O/'audit-bundle-1.0.0.zip'),'accounting':ledger.summary()})
 print(a.canonical({'recovery_files_preserved':len(index),'core_raw_hashes_preserved':len(new),'accounting':ledger.summary()}).decode())
except BaseException:
 if ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(control,)).fetchone()[0] is None:ledger.settle_control(control,time.monotonic()-started,'unknown')
 raise
finally:ledger.db.close()
