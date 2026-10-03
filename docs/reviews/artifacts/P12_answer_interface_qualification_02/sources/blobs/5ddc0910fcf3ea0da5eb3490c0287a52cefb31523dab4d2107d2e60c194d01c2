"""Outcome-blind preparation for two DISABLED four-condition qualifications.

This tool cannot generate model outputs or open references. Execution requires a
separate authorization and a bounded launcher bound to the prepared manifest.
"""
from dataclasses import asdict, replace
from pathlib import Path
from itertools import zip_longest
from importlib.metadata import version
import argparse
import json
import shutil
import subprocess

from p12_common import ROOT, OUT, NATIVE, load, save, catalog
from p12_answer_interface import ASSET, LOCK, RUN as HISTORICAL, settings_and_tokenizer, sources
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import file_hash
from phi_jepa.providers.constrained_local import prepare_request, decoder_schema
from phi_jepa.providers.compact_answer import adapt_answer, value_schema
from phi_jepa.providers.explicit_reasoning import DELIMITER, COT_INSTRUCTION

DEST = ROOT / 'docs/reviews/artifacts/P12_answer_interface_followup_v3'
CONDITIONS = ('qwen3_8b_direct', 'qwen3_8b_thinking', 'llama31_8b_direct', 'llama31_8b_cot')
DOMAINS = ('driving', 'object_pushing_stacking', 'robotic_arm', 'tethered_load')
SELECTION_SEED = 'p12-interface-fresh-validation-v1-seed11'


def settings(condition):
    old = 'llama31_8b_direct' if condition == 'llama31_8b_cot' else condition
    cfg, tokenizer = settings_and_tokenizer(old)
    reasoning = condition in ('qwen3_8b_thinking', 'llama31_8b_cot')
    return replace(cfg, max_new_tokens=4096 if reasoning else 1024,
                   max_seconds=240 if reasoning else 120), tokenizer


def source_files():
    files = sources()
    for path in (Path(__file__), ROOT/'tests/test_p12_explicit_reasoning.py',
                 ROOT/'tests/test_p12_followup.py'):
        files[str(path.relative_to(ROOT))] = file_hash(path)
    return files


def select_fresh(development):
    """Use validation public inputs and identity metadata, never reference files."""
    previous = load(OUT/'previously-inspected-scenarios.json')
    exclusion = previous + development
    excluded = {r[k] for r in exclusion for k in ('scenario_id', 'split_group') if r.get(k)}
    cat = catalog()
    chosen, evidence = [], {}
    for domain in DOMAINS:
        public_path = cat.verified_file(domain, 'validation', 'inputs.jsonl')
        meta_path = cat.verified_file(domain, 'validation', 'evaluator.jsonl')
        evidence[domain] = {'inputs_sha256': file_hash(public_path), 'metadata_sha256': file_hash(meta_path)}
        candidates = []
        with public_path.open() as inputs, meta_path.open() as metadata:
            for a, b in zip_longest(inputs, metadata):
                if a is None or b is None:
                    raise ValueError('unaligned public/metadata files')
                public, meta = json.loads(a), json.loads(b)
                p = PublicProblem.parse(public)
                m = meta['metadata']
                if meta['sample_id'] != p.sample_id or m['split'] != 'validation':
                    raise ValueError('invalid validation identity')
                scenario, group = m['base_scenario_id'], m['split_group_id']
                if scenario in excluded or group in excluded:
                    continue
                candidates.append(dict(public=public, sample_id=p.sample_id, scenario_id=scenario,
                    split_group=group, split='validation', domain=domain, distribution=m['distribution'],
                    public_sha256=digest(public)))
        # Stable hash ordering is independent of answer values, errors, and input length.
        candidates.sort(key=lambda r: digest([SELECTION_SEED, domain, r['scenario_id'], r['sample_id']]))
        selected = []
        for r in candidates:
            if r['scenario_id'] in excluded or r['split_group'] in excluded:
                continue
            selected.append(r)
            excluded.update((r['scenario_id'], r['split_group']))
            if len(selected) == 2:
                break
        if len(selected) != 2:
            raise ValueError('insufficient unexposed validation scenario groups')
        chosen.extend(selected)
    return chosen, {'selection_seed': SELECTION_SEED, 'rule': 'two distinct scenario groups per domain, ascending seeded SHA256',
        'prior_exposure_manifest_sha256': file_hash(OUT/'previously-inspected-scenarios.json'),
        'excluded_identity_count': len({r[k] for r in exclusion for k in ('scenario_id','split_group') if r.get(k)}),
        'excluded_identities': sorted({r[k] for r in exclusion for k in ('scenario_id','split_group') if r.get(k)}),
        'source_files': evidence,
        'scope': 'Fresh to this answer-interface check and disjoint from known inspection manifest plus reused eight. '
                 'The validation partition has been used for numerical checkpoint selection; not globally unseen data.'}


def budget_spec():
    return dict(maximum_attempts=32, maximum_rounds=1, requests_per_condition=8,
        model_window_seconds=7200, maximum_per_request_time_sum_seconds=5760,
        loading_setup_and_overhead_allowance_seconds=1440, paid_api_calls=0,
        allowance_semantics='Upper bounds, not forced generation lengths. Reasoning and final share one output-token/time allowance.',
        window_policy='One persisted deadline starts before first tokenizer/model load. All loading, compiler setup, '
                      'constraint processing, transfers, serialization and inter-request work count. Resumes never reset it. '
                      'Abort remaining requests if overhead exceeds 1440 seconds or a full request allowance cannot fit. '
                      'A supervisor must enforce request and shared wall deadlines; Transformers max_time alone is a soft limit.',
        attempt_policy='Durably count each attempt before generation. Interrupted, failed and retried attempts consume the cap. '
                       'No retries or second round planned; no repair, forced boundary, answer-only second call or resampling.',
        loading_policy='Sequential conditions, batch size one, one GPU model at a time. Wait outside the window for embedding '
                       'or other active GPU work to finish. Include any repeated loading after interruption in the same allowance.')


def manifest(kind, rows, conditions, files, requests, audit):
    return dict(version='p12-interface-followup-v3-four-conditions', kind=kind, enabled=False,
        execution_authorized=False, status='prepared_offline_model_validation_pending',
        proposed_run_root=str(NATIVE / ('p12-answer-interface-qualification-02' if kind == 'development' else 'p12-answer-interface-fresh-validation-01')),
        conditions=conditions, budget=budget_spec(), final_interface='v1.1-order-preserved-CPU-mask',
        model_lock_sha256=file_hash(LOCK), prompt_sha256=file_hash(ASSET),
        dependency_lock_sha256=file_hash(ROOT/'configs/p12_answer_interface_dependencies.lock.txt'),
        cot_prompt=COT_INSTRUCTION, cot_delimiter=DELIMITER,
        source_files=files, source_sha256=digest(files), selection_sha256=digest(rows),
        request_manifest=requests, selection_audit=audit,
        runtime={p:version(p) for p in ('torch','transformers','tokenizers','safetensors','xgrammar')},
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        generation_order=list(CONDITIONS),
        final_boundary='Native </think> for Qwen thinking; exact explicit delimiter for Llama CoT. '
            'Unconstrained reasoning; grammar only after boundary. Validate a boundary-token JSON suffix verbatim. '
            'Missing/duplicate boundary, invalid suffix, exhausted token/time budget, or invalid canonical answer is a failure.',
        archive_policy='Preserve all v1/v1.1 historical requests, outputs, source snapshots and failures. Separate versioned run roots.',
        freeze_policy='This manifest, exact messages/token IDs, schema, adapter, decoder, sampling and cohort are frozen before '
            'any generation or output inspection. Any revision requires a new version before fresh-check generation; never overwrite '
            'observed fresh-check results or silently reuse their cohort as fresh.',
        prerequisite=('Separate explicit authorization of this revised bounded proposal.' if kind == 'development' else
            'Development qualification completed; inspect completion/boundary failures first, affirm unchanged frozen configuration, '
            'then separate authorization. If configuration changes, version and freeze it before any fresh outputs.'),
        stop_policy='No score-directed prompt tuning. Inspect completion/boundary failures before proposing 8192 tokens; '
            'no automatic increase. No paid calls, training, expanded study, confirmation outcomes or test evaluation.',
        reporting=dict(separate_conditions=list(CONDITIONS), planned_denominator=8,
            fields=['attempted','EOS_completed','syntax_valid','strict_contract_valid','supported/eligible_targets',
                'abstentions/eligible_targets','numeric_correct/eligible_and_evaluated','boolean_correct/eligible_and_evaluated',
                'whole_answer_correct/8_including_failures','per_quantity_MAE_RMSE_with_evaluated_counts',
                'exact_any_observed_repetition/supported','exact_hold_last_repetition/supported','hold_last_scores',
                'input_output_reasoning_final_token_counts','boundary_token_overlap_bytes','latency_min_median_p95_max_sum',
                'load_setup_constraint_and_total_wall_time','peak_allocated_reserved_and_process_GPU_memory',
                'missing_duplicate_boundary_invalid_suffix_token_time_runtime_failures','retries_and_repairs'],
            scorer='Existing canonical parser and typed evaluator/tolerances unchanged. References opened only by separate evaluator after generation.',
            usefulness='Parsing or all-unsupported outputs alone cannot establish useful forecasting. Reused-eight qualification cannot complete fresh validation.'),
        execution_launcher_status='Not authorized. Before launch bind a supervised launcher to this manifest; do not use the historical runner/budget.')


def verify():
    index = load(DEST/'freeze.json')
    for rel, sha in index['files'].items():
        if file_hash(ROOT/rel) != sha:
            raise ValueError('frozen artifact changed: ' + rel)
    if source_files() != index['source_files']:
        raise ValueError('frozen source changed')
    for kind in ('development','fresh-validation'):
        cfg = load(DEST/kind/'plan.json')
        if cfg['enabled'] or cfg['execution_authorized']:
            raise ValueError('preparation must remain disabled')
    print(json.dumps(dict(status='frozen_preparation_verified', model_generations=0, freeze_sha256=file_hash(DEST/'freeze.json'))))


def prepare():
    from p10_common import guard_deployment_io
    import xgrammar as xgr
    from transformers import AutoConfig
    if (DEST/'freeze.json').exists():
        verify()
        return
    before = file_hash(HISTORICAL/'budget.json')
    development = load(HISTORICAL/'diagnostic-public.json')
    if len(development) != 8 or any(r['split'] != 'validation' for r in development):
        raise ValueError('exact original eight required')
    fresh, selection_audit = select_fresh(development)
    # Cohort selection needs evaluator *identity metadata* for scenario groups.
    # No reference file is opened. Rendering/decoding starts only after this
    # deployment guard, which also prohibits reopening that metadata file.
    guard_deployment_io()
    assert not ({r['split_group'] for r in development} & {r['split_group'] for r in fresh})
    cohorts = {'development':development, 'fresh-validation':fresh}
    files = source_files()
    conditions, request_indexes, checks = {}, {k:[] for k in cohorts}, []
    for c in CONDITIONS:
        cfg, tokenizer = settings(c)
        conditions[c] = {'settings':asdict(cfg), 'explicit_cot':c=='llama31_8b_cot',
            'reasoning_mode':'explicit_prompt' if c=='llama31_8b_cot' else ('native_qwen' if cfg.enable_thinking else 'direct')}
        config = AutoConfig.from_pretrained(cfg.model, revision=cfg.revision, cache_dir=str(NATIVE/'model-cache'), local_files_only=True)
        compiler = xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(tokenizer, vocab_size=config.vocab_size,
            stop_token_ids=tokenizer.eos_token_id))
        for kind, rows in cohorts.items():
            for row in rows:
                p = PublicProblem.parse(row['public'])
                request = json.loads(canonical(prepare_request(tokenizer, p, load(ASSET)['prompt'], cfg, c=='llama31_8b_cot')))
                compiled = compiler.compile_json_schema(decoder_schema(request, p))
                for abstain in (False, True):
                    dummy = {}
                    for s in p.input['answer_spec']:
                        vs = value_schema(p,s)
                        val = False if s['answer_type']=='boolean' else ([0.]*vs['minItems'] if s['answer_type']=='vector' else 0.)
                        dummy[s['target_id']] = dict(status='unsupported' if abstain else 'supported',
                            value=None if abstain else val, reason='Offline unrelated dummy' if abstain else None)
                    text = json.dumps(dummy)
                    matcher = xgr.GrammarMatcher(compiled)
                    if not all(matcher.accept_token(t) for t in tokenizer.encode(text,add_special_tokens=False)) or not matcher.accept_token(tokenizer.eos_token_id):
                        raise ValueError('actual-tokenizer grammar qualification failed')
                    adapt_answer(p,text)
                path = DEST/kind/'requests'/c/(p.sample_id+'.json')
                save(path,request)
                request_indexes[kind].append(dict(condition=c,sample_id=p.sample_id,
                    path=str(path.relative_to(ROOT)), sha256=file_hash(path), input_tokens=len(request['input_token_ids']),
                    output_token_reserve=cfg.max_new_tokens, supported_and_unsupported_dummy_paths=True))
                checks.append((kind,c,p.sample_id))
        print(c + ': both cohorts, both dummy grammar branches passed',flush=True)
    original = ROOT/'configs/p12_answer_interface_followup.proposed.json'
    archive = DEST/'historical-proposal-v2.json'
    if not archive.exists():
        archive.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(original,archive)
    for kind, rows in cohorts.items():
        save(DEST/kind/'public-cohort.json',rows)
        cfg = manifest(kind,rows,conditions,files,request_indexes[kind],selection_audit if kind=='fresh-validation' else
            {'historical_selection_sha256':file_hash(HISTORICAL/'diagnostic-public.json'), 'rule':'exact reused eight, no reselection'})
        save(DEST/kind/'plan.json',cfg)
        save(original if kind=='development' else ROOT/'configs/p12_answer_interface_fresh_validation.proposed.json',cfg)
    assert file_hash(HISTORICAL/'budget.json') == before
    save(DEST/'offline-verification.json',dict(model_generations=0, request_checks=len(checks),
        dummy_grammar_branch_checks=2*len(checks), historical_budget_unchanged_sha256=before,
        boundary_test_command='python -m unittest test_p12_explicit_reasoning test_p12_answer_interface test_p12 test_p11 -q',
        actual_boundary='Pinned Llama tokenizer; streaming marker, merged newline, and >{ vocabulary-token suffix paths tested.',
        limitation='XGrammar 0.1.19 private _debug_accept_string API is pinned and tested; runtime upgrade requires requalification. '
            'Leading JSON envelope whitespace in the boundary token is retained raw and ignored for grammar priming. '
            'The boundary token was sampled as reasoning; an illegal answer suffix fails, without repair.',
        numerical_results='Not run. Dummy values are contract tests, never forecasting results.'))
    for rel, sha in files.items():
        blob = DEST/'sources/blobs'/sha
        if not blob.exists():
            blob.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/rel,blob)
    artifacts = {str(p.relative_to(ROOT)):file_hash(p) for p in DEST.rglob('*') if p.is_file()}
    for p in (original, ROOT/'configs/p12_answer_interface_fresh_validation.proposed.json'):
        artifacts[str(p.relative_to(ROOT))] = file_hash(p)
    save(DEST/'freeze.json',dict(version='p12-four-condition-pre-execution-freeze-v1', files=artifacts,
        source_files=files, source_sha256=digest(files), model_generations=0))
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('prepare','verify'))
    args = parser.parse_args()
    globals()[args.stage]()
