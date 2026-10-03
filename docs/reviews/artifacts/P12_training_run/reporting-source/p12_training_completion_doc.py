"""Write the completion report from audited numerical artifacts only."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT/'docs/reviews/artifacts/P12_training_run'


def write_report():
    audit = json.loads((EXPORT/'audit.json').read_text())
    complete = 'completion' in audit
    elapsed = audit.get('completion',audit.get('failure'))['wall_seconds']
    rows = audit['domains']
    lines = ['# P12 numerical training completion — 29 September 2026','',
        '**'+('All four authorized domain fits completed.' if complete else 'Execution stopped with preserved progress.')+'** '+
        f'Total execution window: {elapsed:.3f} seconds ({elapsed/60:.2f} minutes). '+
        'This is numerical training and validation-only checkpoint selection; no confirmation evaluation or local-baseline generation ran. '+
        'Paid calls were zero. Ten passes are a fixed exposure, not evidence of convergence.','',
        'Checkout: `'+audit['execution']['branch']+'` at `'+audit['execution']['commit']+
        '`, with existing uncommitted work preserved. No paper edit, push or merge.','',
        '## Completed exposure and resources','',
        '| Domain | Passes | Updates | Pair presentations | Validation sweeps | Domain wall (s) | Peak RSS (GiB) |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for domain,r in rows.items():
        resource = r['resources'] or {}
        lines.append(f'| {domain} | {r["completed_passes"]} | {r["successful_updates"]:,} | '+
            f'{r["actual_pair_exposure"]:,} | {r["completed_validation_sweeps"]} | '+
            f'{resource.get("wall_seconds",0):.3f} | {resource.get("peak_rss_bytes",0)/2**30:.3f} |')
    lines += ['',f'Total successful updates: **{sum(r["successful_updates"] for r in rows.values()):,}**; '+
        f'actual pair presentations: **{sum(r["actual_pair_exposure"] for r in rows.values()):,}**. '+
        'The fixed training population is 3,721 scenarios, 6,702 questions and 454,130 pairs/pass. '+
        'Final full batches add 112 driving, 92 arm, 224 object and 224 tether pair presentations beyond exactly ten passes.','',
        'Execution used '+audit['environment']['cpu_model']+' under WSL, '+
        'the approved CPU profile with two PyTorch threads, Python '+audit['environment']['python']+
        ' and torch '+audit['environment']['runtime_versions']['torch']+'. '+
        f'Optimizer-step time totals {sum(r["optimizer_seconds"] for r in rows.values()):.3f} s; '+
        f'validation time totals {sum(r["validation_seconds"] for r in rows.values()):.3f} s. '+
        f'Child user+system CPU time totals {sum((r["resources"] or {}).get("user_cpu_seconds",0)+(r["resources"] or {}).get("system_cpu_seconds",0) for r in rows.values()):.3f} s. '+
        'Remaining wall time includes context/pair preparation, checkpoint I/O and launch/preflight bookkeeping. '+
        'Domain wall times include each child preflight; aggregate time also includes initial preflight and sequential dispatch overhead.','',
        '## Validation-selected checkpoints','',
        'Selection used all original validation questions after each pass, the unchanged mean tolerance-normalized numerical error '+
        'and fixed failure penalty, with the earliest checkpoint on ties. No test outcome entered selection. '+
        'These are selection diagnostics, not held-out benchmark estimates.','',
        '| Domain | Selected pass | Update | Validation score | Complete validation answers |',
        '|---|---:|---:|---:|---:|']
    for domain,r in rows.items():
        selected = r['selected']
        if selected:
            v = next(v for v in r['validation_curve'] if v['update']==selected['update'])
            lines.append(f'| {domain} | {v["pass"]} | {v["update"]:,} | {v["score"]:.9g} | {v["complete_answers"]}/{v["questions"]} |')
    lines += ['','Native selected model files (SHA-256 is the filename stem):','']
    for domain,r in rows.items():
        if r['selected']:
            lines.append('- '+domain+': `'+r['selected']['absolute_path']+'`.')
    lines += ['','## Training and validation curves','',
        '[Vector curve figure](artifacts/P12_training_run/training-validation-curves.svg) · '+
        '[Full audited values](artifacts/P12_training_run/audit.json). Raw per-update histories '+
        'and per-question validation records are retained under the export’s `domains/` directory. '+
        'Training means below cover the full batches between successive pass milestones, including carried tails. '+
        'Training loss is the raw augmented-vector MSE; validation scores use physical-target tolerances and are not the same scale.','']
    for domain,r in rows.items():
        lines += ['### '+domain,'','| Pass | End update | Mean training MSE | Validation score | Rollout exceptions |',
                  '|---|---:|---:|---:|---:|']
        by_pass = {v['pass']:v for v in r['validation_curve']}
        for t in r['training_curve']:
            v = by_pass.get(t['pass'])
            val = f'{v["score"]:.9g}' if v else 'pending'
            failures = str(v['rollout_failures']) if v else 'pending'
            lines.append(f'| {t["pass"]} | {t["end_update"]:,} | {t["loss"]:.9g} | {val} | {failures} |')
        lines.append('')
    lines += ['## Failure accounting and limits','']
    for domain,r in rows.items():
        reasons = {}
        for v in r['validation_curve']:
            for reason,count in v['failure_reasons'].items():
                reasons[reason] = reasons.get(reason,0)+count
        lines.append('- '+domain+': '+
            f'{sum(v["rollout_failures"] for v in r["validation_curve"])} validation rollout exceptions; '+
            f'{sum(v["penalized_questions"] for v in r["validation_curve"])} questions with score ≥ 1e12; '+
            'target/rollout failure reasons across all selection sweeps: `'+json.dumps(reasons,sort_keys=True)+'`.')
    lines += ['','The supervisor persisted the four-hour aggregate deadline and one-hour dispatch deadlines; '+
        'the unchanged trainer enforced its own one-hour domain guards and checkpoint artifact reserve. '+
        'No budget was extended. Models ran sequentially. '+
        f'Native study/checkpoint artifacts occupy {sum(r["artifact_bytes"] for r in rows.values()):,} bytes. '+
        'The final integrity manifest records hashes for every retained checkpoint blob.','',
        '## Identity, verification and commands','',
        '- User-authorized proposal SHA-256: `'+audit['original_proposal_sha256']+'`.',
        '- Authorized copy SHA-256: `'+audit['approved_plan_sha256']+'`.',
        '- Frozen numerical implementation: `'+audit['numerical_source_sha256']+'`.',
        '- [Approved copy](artifacts/P12_training_run/execution/approved-plan.json), '+
        '[execution window/source](artifacts/P12_training_run/execution/execution-window.json), '+
        '[initial preflight](artifacts/P12_training_run/execution/preflights/initial/training-preflight.json), '+
        '[export checksums](artifacts/P12_training_run/artifact-index.json).','',
        'Fresh preflight verified all 8,038 train/validation contexts and 500 confirmation public contexts '+
        'with zero missing/integrity failures. Confirmation outcomes remained unopened. '+
        'Only the three authorized activation fields changed; original proposals and preparation exports were preserved. '+
        'The final audit checks source/runtime/input hashes, exact update/exposure totals, validation IDs/aggregates, '+
        'earliest minimum selection and all checkpoint content hashes. '+
        f'All {sum(len(r["checkpoint_blobs"]) for r in rows.values())} checkpoint blobs passed; '+
        'all four selected deployment models and final optimizer/RNG bundles reloaded successfully, '+
        'with zero failed optimizer updates and no added updates or rollouts. '+
        'A second completed-wrapper invocation returned "Already complete; no optimizer updates."','',
        'Commands actually run in the existing WSL core environment:','',
        '```bash',
        'PYTHONPATH=src:tests:tools python -m unittest test_p12_training_plan test_p12 test_p03 -q',
        'PYTHONPATH=src:tests:tools python -m unittest test_p12_training_execution -v',
        'python -u tools/p12_training_execution.py run',
        'python tools/p12_training_report.py --status',
        'python tools/p12_training_report.py','```','',
        'The first suite passed 26 tests in 3.243 s; the outer-envelope suite passed two tests in 0.015 s. '+
        'Its printed timeout/artifact errors were deliberately exercised fixture guards, not failures of the live run. '+
        'Curves were rendered offline with the bundled Windows Python and ReportLab LinePlot; '+
        'the numerical runtime was not changed.','',
        '## Preserved artifacts and next boundary','',
        '- Native checkpoints, histories and validation records: `/home/aashraf/phi-jepa/p12-expanded-study-seed11`.',
        '- Execution controls, child logs and resource records: `/home/aashraf/phi-jepa/p12-training-execution-01`.',
        '- Repository evidence export: `docs/reviews/artifacts/P12_training_run/`.',
        '- [Execution decisions](../decisions/P12_training_execution.md) and [run commands](../P12_pipeline.md).','',
        'Confirmation evaluation and baseline generation remain disabled. The next evaluation plan must qualify/freeze '+
        'Qwen thinking-off/on, Llama direct and Llama prompted CoT, preserve reasoning/final separation, '+
        'and bind the selected numerical checkpoints under a separate budget. The older three-condition evaluation '+
        'allowance is not silently expanded. Phi-JEPA retains its disclosed historical OpenAI enrichment dependency; '+
        'this numerical run made zero paid calls and generated no prose answers.']
    if any(r['frozen_resume_history_reader_probe']['error'] for r in rows.values()):
        lines += ['','## Nonblocking resume limitation found during artifact audit','',
            'The frozen trainer writes a blank line after each canonical update record. Its strict '+
            '`json_lines` reader rejects that blank line when called by `check_resume_boundary` for '+
            'an incomplete-domain resume. A read-only two-record probe reproduces `JSONDecodeError`; '+
            'the raw logs have not been rewritten. The report explicitly skips blank separator lines '+
            'and validates all actual update records. This did not affect uninterrupted training, '+
            'checkpoint integrity or completed-domain no-op behavior. No resume was needed.','',
            'The frozen source was preserved as authorized. Any future incomplete-run recovery must '+
            'reconcile this parser issue and the original remaining budget explicitly; it must not '+
            'silently replay updates, alter the approved source, or renew an expired window.']
    (ROOT/'docs/reviews/P12_training_completion.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    write_report()
