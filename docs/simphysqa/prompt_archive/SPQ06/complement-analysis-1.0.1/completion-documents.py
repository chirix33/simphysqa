"""Completion documentation from actual settled analysis; no answering calls."""
from pathlib import Path
import json, hashlib, shutil
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
R=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
O=B/'complement-analysis-1.0.1'; RUN=B/'complement-execution-1.0.0'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def link(title,p):return f'[{title}](<{p.as_posix()}>)'
def fmt(v):return f'{v:.3f}' if v is not None else 'unavailable'
coverage=read(O/'coverage.json'); accounting=read(O/'final-accounting.json')
print('Analysis keys',accounting.keys())
# Publication requires this script to consume final settled evidence, never an intermediate forecast.
if not (O/'manifest.json').exists():raise ValueError('final analysis manifest missing')
archive=R/'docs/simphysqa/prompt_archive/SPQ06/complement-analysis-1.0.1'
archive.mkdir(exist_ok=False)
files=[(B/'complement-analysis-src-1.0.1/finish_complement.py','finish_complement.py','executed_central_analysis_no_model_calls'),(B/'complement-analysis-check-1.0.1.py','analysis-equivalence.py','executed_1600_core_row_equivalence'),(B/'test_complement_analysis_1_0_1.py','test_analysis.py','executed_five_offline_coverage_fixtures'),(B/'complement-preservation-final-1.0.0.py','preservation-check-failed.py','executed_helper_failed_on_incorrect_manifest_key_no_artifacts_changed'),(B/'complement-preservation-final-1.0.1.py','preservation-check.py','executed_historical_artifact_hash_verification'),(B/'complement-delivery-control-1.0.0.py','delivery-control.py','executed_bounded_documentation_hash_verification'),(Path(__file__),'completion-documents.py','executed_documentation_from_actual_receipts')]
index=[]
for source,name,kind in files:
 shutil.copyfile(source,archive/name);index.append({'file':name,'source':str(source),'sha256':sha(source),'kind':kind})
(archive/'file-index.json').write_text(json.dumps({'version':'1.0.1','entries':index,'worker_changed':False,'private_evidence_committed':False,'annotation_calls':0,'simulations':0},indent=2),encoding='utf8')
(archive/'README.md').write_text('''# Actual complement analysis procedures /1.0.1

These separately versioned procedures centrally assessed genuine immutable returns.
The prior prepared analysis /1.0.0 is preserved. Primary parsers, scorers and paired
stratified whole-group bootstrap remain unchanged. No answering workers or requests
were changed. No private gold, raw responses, checkpoints or credentials are committed.
See file-index.json, the completion review and the external immutable analysis receipt.
''',encoding='utf8')
report=['# SPQ06 authorized remaining-200 execution','',
'Branch `simphysqa-spq06`; execution implementation commit `bcf5ee7`, base `239cda5`. This report is committed locally with the final documentation commit; its exact identity is recorded in the external post-commit receipt. The branch remains unmerged and unpushed.','',
'The user explicitly authorized the eight frozen Ashraf combinations and prospectively revised cumulative Ashraf/shared ceilings to 126,000/226,800 seconds. Collaborator allocation remains 100,800 seconds. The same central ledger retains all prior charges, decisions and the historical 6,600-second unknown process charge. The result-import cutoff was explicitly revised to 2026-10-13 02:00 UTC (October 12, 21:00 Chicago), leaving 9h59 before the official submission deadline.','',
'The complement is exactly 200 frozen QA and distinct original trajectory groups, ten per domain–family cell and forty per family. Core and complement are disjoint from each other and the frozen development/audit/prompt-use exclusions. No score-based selection, substitution, retry, new data, annotation, simulation or collaborator inference occurred. Expansion was authorized after core results were available.','',
'## Actual coverage','',f'All eight combination coverage/accounting checks complete: **{coverage["all_eight_complete"]}**. Canonical failures remain assigned outcomes. Unsupported clarification routes are explicitly unexecuted, rather than authored continuations.','',
'| Condition | Representation | Initials | Supported continuations / imported | Unexecuted conditional | Coverage complete |', '|---|---|---:|---:|---:|---|']
for row in coverage['combinations']:
 report.append(f'| {row["condition_id"]} | {row["representation"]} | {row["initial_canonical"]}/200 | {row["supported_routes"]} / {row["conditional_canonical"]} | {row["unexecuted_conditional"]} | {row["execution_and_coverage_accounting_complete"]} |')
report+=['','| Condition | Input | Existing latency_seconds total (s) | Total stage timing (s) | Sampled device peak (MiB) | Successful stage samples |','|---|---|---:|---:|---:|---:|']
for row in coverage['combinations']:
 m=row['measurements']
 report.append(f'| {row["condition_id"]} | {row["representation"]} | {fmt(m["stage_latency_seconds"])} | {fmt(m["total_stage_seconds"])} | {m["device_sampled_peak_mib"] if m["device_sampled_peak_mib"] is not None else "unavailable"} | {m["successful_device_samples"] if m["successful_device_samples"] is not None else "unavailable"} |')
report+=['','| Executor | Cumulative accounted (s) | Ceiling (s) | Remaining (s) |','|---|---:|---:|---:|']
for row in accounting['allocations']:
 report.append(f'| {row["executor"]} | {row["accounted_seconds"]:.3f} | {row["ceiling_seconds"]:.3f} | {row["remaining_seconds"]:.3f} |')
report += ['',f'Shared accounted {accounting["accounted_seconds"]:.3f} / {accounting["shared_ceiling_seconds"]:.3f} seconds; remaining {accounting["remaining_seconds"]:.3f}. This snapshot follows analysis settlement; any final documentation/verification control has a separately saved subsequent accounting receipt.','']
runtime_records=[read(p) for p in sorted((RUN/'jobs').glob('*/worker-output/runtime.json'))]
loads=[r['load_seconds'] for r in runtime_records if isinstance(r.get('load_seconds'),(int,float))]
processes=read(O/'operational-accounting-before-final-settlement.json')['complement_processes']
known=[p[2] for p in processes if p[2] is not None]
report += [f'{len(processes)} complement process reservations; {len(known)} measured lifecycle receipts totaling {sum(known):.3f} seconds. Worker model-construction/load_seconds is available in {len(loads)} runtime receipts, totaling {sum(loads):.3f} seconds. These loading and stage timings are nested within lifecycle work and are not added to cumulative accounting again.','']
report += ['The existing latency_seconds field covers generation, output decoding and CUDA synchronization in these unchanged workers. It is not a separate decode or prefill measurement. Total-stage timing additionally covers rendering/tokenization and response processing according to the frozen instrumentation boundaries.','']
old_usage=read(RUN/'ledger-before.json')['accounted_seconds'] if 'accounted_seconds' in read(RUN/'ledger-before.json') else 58172.897
report += ['## Forecast and calendar reconciliation','',
f'Analysis-settled cumulative increment over the last verified core/recovery accounting point ({old_usage:.3f} seconds) is {accounting["accounted_seconds"]-old_usage:.3f} accounted seconds. This includes central work and the retained unknown routing-control reservation; it is not pure GPU kernel time. The original component forecast was 51,995.106 seconds plus 25% reserve (64,993.882 seconds). The separately preserved historical-repeat estimate was 51,572.897 seconds plus 25% reserve (64,466.121 seconds). Forecasts were estimates, never enlarged hard ceilings.','',
link('Original live forecast',RUN/'forecast-before.json')+' is the core-only historical basis. In the preserved forecast-after-budget artifact, its historical-repeat field includes the prospectively held 3,600-second final-analysis reservation; that field is not a clean core-only repeat prediction. Its separately computed component forecast and the original pre-revision historical estimate remain the interpretable estimates. The artifact is preserved rather than rewritten.','',
'The controller reduced final initial batches to 48, 41 and 11 and conditional batches to 35 plus four according to budget/calendar capacity, retaining frozen order. '+link('Analysis completion timestamp',O/'manifest.json')+' records actual return/import/analysis completion before the approved 02:00 UTC cutoff. No further Ashraf main work remains in this authorized complement. No two-machine completion forecast is asserted without collaborator measurements.','']
report+=['','## Evidence and scientific results','',
link('Paper tables and paired ablations',O/'paper-results.md')+'. '+link('Core 200',O/'core-analysis.json')+', '+link('complement 200',O/'complement-analysis.json')+', '+link('combined 400',O/'combined-analysis.json')+'. All assigned items remain in primary denominators. Combined intervals are recomputed from union records with twenty whole groups per domain–family stratum, 10,000 paired replicates and unchanged seed 20261009; CI endpoints are never averaged. Unexpanded conditions require common-core comparisons.','',
link('Central parsed records and scoring joins',O/'central-parsed-records.json')+', '+link('complement diagnostics',O/'complement-diagnostics.json')+', '+link('core diagnostics',O/'core-diagnostics.json')+'. Diagnostics distinguish generation noncompletion, JSON parsing, schema/type/unit/frame invalidity and valid-but-incorrect answers separately from primary scoring. Clarification first-turn and continuation validity remain separate. Human explanation prose adequacy is uncollected; automatic factual checks are not prose quality. Explicit query gaps establish no OOD claim.','',
'## Integrity, timing and operational limitations','',
link('Actual coverage, timing/tokens and sampled memory',O/'coverage.json')+', '+link('final accounting',O/'final-accounting.json')+', '+link('original ledger-row preservation',O/'original-ledger-preservation.json')+'. Process lifecycle and dispatcher overhead are charged once; nested stage/loading timings are not added again. Unknown charges retain full bounds. Device memory is a sampled device-wide high-water mark and can miss peaks; missing measurements are unavailable, not zero. Separate prefill/decode/TTFT and semantic refusal are not asserted as measured.','',
link('Latest delivery settlement',RUN/'final-delivery-1.0.0.json')+' adds the separately reserved final preservation/documentation verification controls to the preceding analysis accounting snapshot.','',
'The first normal fifty-item Qwen3-8B enriched batch passed actual return/import, token rendering, raw-output, measurement and central scoring-join checks. Routing then exposed a missing coordinator configuration in the first source snapshot. Exact existing configuration files were added in a separate coordinator snapshot; saved first responses were checked and routed without repeating any scientific stage. The original failure/pause record and full 600-second unknown central charge remain. Scientific worker/rendering/scoring behavior was unchanged.','',
'The outer monitoring shell ended with a Get-Content error caused by its log-tail path using 2026/10/09 instead of 2026-10-09. The actual serial controller log, execution-completion receipt and every immutable import establish successful controller completion. This log-tail error caused no model rerun or stage reservation.','',
link('First batch integrity receipt',RUN/'first-main-batch-integrity.json')+', '+link('dependency-only repair disposition',RUN/'coordinator-repair-disposition-1.0.1.json')+', '+link('analysis source/core equivalence',RUN/'analysis-source-equivalence-1.0.1.json')+'. Actual immutable imports and all fresh metadata/artifact/template/ModelConfig proofs remain in '+link('execution root',RUN)+'.','',
link('Final historical hash preservation check',RUN/'final-preservation-1.0.1.json')+' compares the preserved pre-recovery artifact inventory, execution freeze and original source/manifests. Mutable central ledger files are excluded from file hashing and checked by immutable original-row preservation instead. The first helper incorrectly addressed the identities map as hashes and failed before checking files; its log and full 300-second unknown reservation remain. The separately versioned corrected helper used the actual saved key.','',
'## Delivery and verification','',
link('Private audit bundle',O/'audit-bundle-1.0.0.zip')+', '+link('analysis manifest and file hashes',O/'manifest.json')+'. Exact request/raw examples are in '+link('examples',O/'exact-examples')+'. The public sealed base and complement overlay stay external; private evidence is not committed.','',
'Fifty relevant offline implementation tests, sixteen focused post-repair checks and five analysis fixtures passed. The 1,600 core item-condition rows were independently recomputed and their endpoints, completion, parsing and validity matched the original recovered analysis exactly. Original fixture/failure logs remain preserved; mock outputs are not inference evidence. See '+link('offline logs',B/'complement-live-offline-1.1.1.log')+', '+link('post-repair tests',B/'complement-postrepair-offline-1.0.0.log')+', '+link('analysis fixtures',B/'complement-analysis-fixtures-1.0.1.log')+'.','',
'The paper text describes the scientific protocol, actual balanced coverage and post-core expansion timing. Operational interruption/recovery/accounting history remains in execution records. No collaborator conditions or human ratings are inferred. No further answering is launched by this completion report.','']
(R/'docs/reviews/SPQ06_complement_execution.md').write_text('\n'.join(report),encoding='utf8')
commands='''# Complement execution commands and provenance

These are the actual bounded procedures; execution is already performed. Do not rerun
reserved keys. The controller selects only never-reserved keys and enforces the
approved cumulative ledger allocations and result-import cutoff. A rerun command
does not authorize extra attempts, later cutoffs or collaborator inference.

Use the existing CPU interpreter and immutable source paths listed below. WSL/GPU
bindings, pinned environments and fresh preflight receipts are saved in the run root.
'''
commands+='\n```powershell\n$spqCpu = "C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe"\n'
commands+=f'$env:PYTHONPATH = "{(B/"complement-live-src-1.0.1/src").as_posix()}"\n& $spqCpu "{(B/"complement-live-src-1.0.1/complement_run.py").as_posix()}" run\n'
commands+=f'$env:PYTHONPATH = "{(B/"complement-analysis-src-1.0.1/src").as_posix()}"\n& $spqCpu "{(B/"complement-analysis-src-1.0.1/finish_complement.py").as_posix()}" --output "{O.as_posix()}"\n```\n\n'
commands+='The analysis output uses exclusive creation: the completed root must not be overwritten. The analysis routine invokes no models. Immutable return export/import, request validation, central scoring and actual-history routing are called by the controller, with exact procedure hashes in the execution archive. Final settlement and manifests are linked in the completion review.\n'
(R/'docs/simphysqa/complement_execution_commands.md').write_text(commands,encoding='utf8')
progress=R/'docs/PROGRESS.md';text=progress.read_text(encoding='utf8')
prefix=f'''# Current completion — remaining-200 execution (12 October 2026)

Approved complement execution has settled and been centrally analyzed; all-eight
coverage/accounting complete: {coverage['all_eight_complete']}. The fixed core/complement/
union analyses preserve 200/200/400 assigned denominators and unchanged scoring and
paired stratified bootstrap. The expansion occurred after core results were available;
selection/order were frozen earlier. Collaborator work and human prose ratings remain
outside this completion. Original artifacts, reservations and unknown charges remain.

[Completion review](reviews/SPQ06_complement_execution.md),
[exact commands](simphysqa/complement_execution_commands.md),
[actual analysis archive](simphysqa/prompt_archive/SPQ06/complement-analysis-1.0.1/README.md).
Local final commit identity is in the external post-commit receipt. No push/merge/rebase.
Prior entries are preserved dated history.

---

'''
progress.write_text(prefix+text,encoding='utf8')
readme=R/'docs/README.md';text=readme.read_text(encoding='utf8')
text=text.replace('Serial execution is in progress; completed core200\nremains the fallback.',f'Complement execution is settled; complete eight-combination coverage: {coverage["all_eight_complete"]}. Core200\nremains preserved as the fallback.')
text=text.replace('| SPQ06 authorized complement execution |', '| SPQ06 actual complement execution | [Completion](reviews/SPQ06_complement_execution.md), [commands](simphysqa/complement_execution_commands.md) |\n| SPQ06 authorized complement execution |')
readme.write_text(text,encoding='utf8')
print('Created completion documents and actual analysis archive; no model calls.')
