"""Readable actual-result report from sealed central analysis; no model calls."""
from pathlib import Path
from simphysqa.execution_adapter import read, sha

BASE = Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN = BASE / 'main-ashraf-1.0.0'
PRIMARY = {'direct': 'typed_correct', 'predictive': 'typed_correct', 'counterfactual': 'typed_correct',
           'explanation': 'structured_facts_all_correct', 'clarification': 'resolved_answer_correct'}


def link(label, path):
    return f'[{label}](<{Path(path).as_posix()}>)'

def measured(value):
    return 'unavailable' if value is None else f'{value:.3f}'


def render(output):
    delivery = RUN / 'delivery-1.0.0'
    execution = read(delivery / 'actual-execution-results.json')
    analysis = read(delivery / 'ashraf-fixed-denominator-analysis.json')
    accounting = read(delivery / 'resource-accounting.json')
    preservation = read(delivery / 'preservation-after.json')
    prose = read(RUN / 'model-prose-packets-1.0.0/index.json')
    combos = execution['combinations']
    initials = sum(sum(m['initial_statuses'].values()) for m in combos)
    continuations = sum(sum(m['continuation_statuses'].values()) for m in combos)
    a = next(r for r in accounting['allocations'] if r['executor'] == 'Ashraf')
    c = next(r for r in accounting['allocations'] if r['executor'] == 'Collaborator')
    lines = [
        '# SPQ06 actual Ashraf main execution', '',
        f"Ashraf's eight frozen combinations produced {initials} initial and {continuations} conditional records "
        f"on the same 200 held-out QA/groups. Accounted main work is {a['accounted_seconds']:.3f} seconds "
        f"({a['accounted_seconds']/3600:.3f} hours) of72000. Collaborator inference remains unexecuted; "
        'this is Ashraf\'s share, not completion of all nine enriched conditions.', '',
        'The source base is8c901ee on simphysqa-spq06. The final local commit/branch state is recorded in '
        + link('post-commit receipt', delivery / 'git-completion.json') + '. No merge, rebase or push is authorized or performed.', '',
        '## Execution, coverage and reservations', '',
        '| Condition | Representation | Initial status counts | Conditional status counts | Unexecuted conditional | Process lifecycle s | Loading s | Sampled device peak MiB |',
        '| --- | --- | --- | --- | ---: | ---: | ---: | ---: |',
    ]
    for m in combos:
        lines.append(f"| {m['condition_id']} | {m['representation']} | {m['initial_statuses']} | {m['continuation_statuses']} | "
                     f"{m['conditional_unexecuted']} | {measured(m['adapter_process_lifecycle_seconds'])} | {measured(m['loading_seconds'])} | {m['sampled_stage_device_peak_mib'] if m['sampled_stage_device_peak_mib'] is not None else 'unavailable'} |")
    lines += ['',
        f"There are {execution['initial_reserved']} initial and {execution['continuation_reserved']} conditional reservations. "
        f"Canonical conflicts: {len(execution['conflicts'])}; invalid returned entries: {len(execution['invalid_returns'])}; "
        f"unknown process reservations: {accounting['unknown_processes']}. Every combination retains200 primary items, "
        'including failures. Clarification has40 possible continuations per combination; absent/unsupported actual '
        'first turns receive immutable unexecuted-conditional receipts. No authored assistant question, truncated '
        'history, repaired answer, replacement item or scientific retry is used.', '',
        'Llama CoT\'s missing development live stage2 remains historical. Actual main stage2 coverage is shown above; '
        'a combination with no completed continuation has no demonstrated completed main stage2. Its conservative '
        'continuation allowance stays unchanged.', '',
        'An abrupt PC restart interrupted the first Qwen3-8B direct structured-only batch. Its15 saved actual outputs were imported unchanged;35 reserved initials have no saved response and remain interrupted. The full6600s unknown process bound is retained. No failed key was reopened, moved, replaced or rerun. Missing initial clarification responses have explicit unexecuted-conditional receipts with null actual response. The primary denominator remains200 for this combination.', '',
        '## Fixed-denominator family results', '',
        'Each family has40 independent QA/groups, ten per domain. Values are balanced domain means with the '
        'unchanged paired whole-trajectory percentile bootstrap:10000 replicates, seed20261009, nominal marginal95% '
        'intervals. Main conditions share identical stratified group draws. No adequately powered cell-level or '
        'natural-release-frequency claim follows. Degenerate observed bootstrap support is flagged in the machine '
        'results and does not establish zero population uncertainty.', '',
        '| Condition | Representation | Family | Endpoint | Rate | 95% interval |',
        '| --- | --- | --- | --- | ---: | --- |',
    ]
    for s in analysis['uncertainty']['summaries']:
        if s['endpoint'] == PRIMARY[s['family']]:
            lo, hi = s['interval_95']
            lines.append(f"| {s['condition_id']} | {s['input_condition']} | {s['family']} | {s['endpoint']} | "
                         f"{s['balanced_domain_mean']:.3f} | [{lo:.3f}, {hi:.3f}] |")
    lines += ['',
        'Typed endpoints require correct values with unchanged units/frames/tolerances, strict Boolean types and '
        'sign-invariant quaternion angular distance. Exact per-target validity, correctness and numerical errors '
        'are retained in the private item rows; unavailable/invalid errors are null, never zero. No cross-unit error '
        'pooling or answer repair is performed. Parsing and typed validity are separate from correctness. Explanation '
        'reports six structured facts (intervention, fixed conditions, two supplied readouts, exact equality and '
        'existing-scorer distinguishability); this does not establish semantic/prose adequacy. All clarification '
        'gap-recognition, slot-match, premature-answer, routing and resolved-answer endpoints are available in the '
        'machine results. Scientific failures and execution/interface failures remain separately visible.', '',
        '## Matched representation ablations', '',
        'Differences are structured-only minus enriched on the same selected QA/groups and pinned condition. '
        'Negative values favor enriched on that endpoint. No extra independent items are created by conditions or turns. '
        'The Qwen3-8B direct structured-only primary difference includes35 power-loss missing responses as unsuccessful. '
        'That execution shortfall confounds interpretation as a pure language-enrichment effect; do not attribute its '
        'entire difference to input representation. The fixed denominator and paired uncertainty are preserved, '
        'with coverage and failure causes reported separately.', '',
        '| Condition | Family | Endpoint | Difference | Paired95% interval |',
        '| --- | --- | --- | ---: | --- |',
    ]
    for s in analysis['uncertainty']['paired_comparisons']:
        if s['condition_a'][1] == 'structured_only' and s['endpoint'] == PRIMARY[s['family']]:
            lo, hi = s['paired_interval_95']
            lines.append(f"| {s['condition_a'][0]} | {s['family']} | {s['endpoint']} | "
                         f"{s['difference_a_minus_b']:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")
    lines += ['',
        '## Accounting, provenance and limits', '',
        f"Ashraf remaining allocation: {a['remaining_seconds']:.3f}s. Collaborator allocation: "
        f"{c['remaining_seconds']:.3f}/100800s. Shared remaining: {accounting['remaining_seconds']:.3f}/172800s. "
        'Unused Ashraf time is not automatically reassigned. Development ledgers and their historical failures '
        'remain separate. No second-machine completion schedule is measured or inferred.', '',
        'Lifecycle accounting includes main preparation/preflight, package/artifact checks, loading, stages, '
        'teardown, measured dispatcher gaps and central work once. Generation and total-stage timings are nested '
        'process measurements, not additional charges. Unknown work retains its bound; observed overruns remain '
        'recorded. Final accounting/index receipt serialization follows the declared central timing boundary. '
        'Queue/transfer wait and software implementation are excluded. These are accounted work seconds, not '
        'measured GPU busy time. The prior17.041h Ashraf estimate and original200-versus400 forecast remain preserved; '
        'this separately versioned report provides actual elapsed components.', '',
        'Device-wide nvidia-smi memory is sampled at a requested0.5s interval and may miss peaks. Sample counts, '
        'timestamps, UUID, peak, errors and null/unavailable reasons are preserved. Torch process allocation is '
        'separate and can omit backend children. HF stop reasons are identified as derived token/EOS/deadline '
        'evidence; vLLM retains exposed backend reasons. No measured TTFT/prefill/decode split, inaccessible internal '
        'reasoning, GPU utilization integral or semantic refusal classifier is claimed.', '',
        f"Preservation checks cover {preservation['files_checked']} existing frozen/historical files; "
        f"all preserved: {preservation['all_preserved']}. The core/pool, all2200 initial package requests, worker/settings, "
        'templates, model/tokenizer revisions, quantization, precision, cutoffs, source evidence, scorers and '
        'uncertainty plan remain unchanged. Fresh GPU/artifact/template/runtime and exact ModelConfig checks precede '
        'scientific reservation; reviewed qualification mappings are adopted only for their exact supported identities.', '',
        'Condition comparisons concern the pinned artifacts and complete execution specifications. Model size, '
        'quantization/precision, backend, reasoning controls, decoding and output allowances differ across '
        'configured conditions; these results do not isolate a causal effect of scale or reasoning alone. '
        'Matched input ablations preserve the same condition settings and task facts, with the Qwen3-8B '
        'restart coverage limitation stated above. Unexecuted collaborator conditions remain unavailable.', '',
        'Central allocation guards, immutable hash-once transaction indexing and the conservative conflicting-lifecycle '
        'import fix are separately versioned outside the sealed public package.115 offline behavioral tests passed; '
        'the offline wheel build and byte-equality check passed. Sixteen restart/import/allocation regression checks (including three new recovery tests) passed after reboot. Earlier failed fixture expectations remain archived; no actual scientific attempt was retried. The earlier failing allocation test and corrected '
        'unexecuted analysis-draft syntax check remain archived. Actual main batch token/render/raw-output/memory/'
        'history/scoring-join verification receipts are separate empirical execution evidence.', '',
        '## Prospective prose assessment and remaining work', '',
        f"The frozen eight-task enriched prose subset provides {len(prose['available_responses'])} available actual "
        f"responses and {prose['missing_planned_count']} missing planned responses. P1/P2 forms are blank and "
        'uncollected. Private condition mappings stay separate. Review packets preserve returned words and parsed '
        'final objects; metadata blinding cannot prevent response wording from revealing reasoning mode. No human '
        'explanation-quality or annotation-acceptability result is claimed. The140-item annotation audit remains a '
        'different study with pending feedback; explicit query-gap clarification supports no OOD claim.', '',
        'The next execution work is collaborator qualification and separately authorized Gemma/DeepSeek issuance '
        'through the same ledger. Ashraf\'s reserved stages cannot be retried or replaced. No collaborator inference, '
        'paid annotation, simulation, new dataset generation or hosted answering occurs in this milestone.', '',
        '## Inspectable evidence and commands', '',
    ]
    for label, path in [
        ('Execution freeze', RUN / 'execution-freeze.json'),
        ('First normal main-batch integrity gate', RUN / 'first-main-batch-integrity.json'),
        ('Central orchestration compatibility overlay', RUN / 'orchestration-overlay-1.0.1.json'),
        ('Actual status, timing, memory and runtime records', delivery / 'actual-execution-results.json'),
        ('Fixed-denominator items and paired uncertainty', delivery / 'ashraf-fixed-denominator-analysis.json'),
        ('Accounting and remaining shared-work forecast', delivery / 'resource-accounting.json'),
        ('Final offline actual-evidence checks', delivery / 'final-offline-verification.json'),
        ('Power-loss recovery and preserved interrupted evidence', RUN / 'restart-recovery-1.0.0/recovery-receipt.json'),
        ('Frozen-artifact preservation', delivery / 'preservation-after.json'),
        ('Per-file executed/reused/deterministic mapping', delivery / 'per-file-procedure-index.json'),
        ('File hashes', delivery / 'file-index.json'),
        ('Central parsed actual responses', RUN / 'central-analysis-1.0.0/central-parsed-records.json'),
        ('Prospective model-answer prose entry point', RUN / 'model-prose-packets-1.0.0/README.md'),
        ('Commands', Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/docs/simphysqa/ashraf_main_commands.md')),
        ('Collaborator handoff', Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/docs/simphysqa/ashraf_main_handoff.md')),
    ]:
        lines.append('- ' + link(label, path))
    lines += ['', 'Examples below use the first saved Qwen3-8B-direct enriched batch. They are inspection links, '
              'not an additional sample or selected by accuracy.', '']
    first = RUN / 'jobs/001--qwen3_8b_direct--enriched--stage1'
    spec = read(BASE / 'execution-public-1.1.1/execution-spec.json')
    shown = set()
    for file in sorted((first / 'worker-output/results').glob('*.json')):
        raw = read(file)
        item = next(i for i in spec['items'] if i['sample_id'] == raw['sample_id'])
        if item['family'] in shown:
            continue
        shown.add(item['family'])
        lines.append('- ' + item['family'] + ': ' + raw['sample_id'] + ' — '
                     + link('exact executed request', first / 'worker-output/executed-requests' / file.name)
                     + ', ' + link('raw actual response', file))
    assert shown == set(PRIMARY)
    lines += ['', 'Package manifest SHA256: `' + sha(BASE / 'execution-public-1.1.1/package-manifest.json') + '`.', '']
    text = '\n'.join(lines)
    for old, new in {'of72000': 'of 72,000', 'is8c901ee': 'is 8c901ee',
                     'retains200': 'retains 200', 'has40': 'has 40', 'stage2': 'stage 2',
                     'bootstrap:10000': 'bootstrap: 10,000',
                     'seed20261009': 'seed 20261009', 'marginal95%': 'marginal 95%',
                     'Paired95%': 'Paired 95%', 'prior17.041h': 'prior 17.041h',
                     'all2200': 'all 2,200', 'package.115': 'package. 115',
                     'The140-item': 'The 140-item'}.items():
        text = text.replace(old, new)
    with Path(output).open('x', encoding='utf8') as f:
        f.write(text)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True)
    render(p.parse_args().output)
