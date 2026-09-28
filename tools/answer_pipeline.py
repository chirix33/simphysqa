"""WSL question-to-answer comparisons using existing checkpoints by default.

Workers isolate public inference from optional evaluator access. Historical runs
are read-only. No training, provider attempt or parser repair happens implicitly.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from p10_common import ROOT, QualificationBudget, digest, file_hash, guard_deployment_io, load, save
from replay_pipeline import ALIASES, NATIVE, RUNS, ReadOnlyRun, output_path
from prepare_manual_pipeline import DOMAINS

METHODS = ('phi_jepa', 'vanilla_llm', 'coconut', 'codi', 'text_ode', 'lr', 'rnn', 'no_enrichment', 'no_text_conditioning')


def select_rows(rows, domains, count=3, sample_ids=None, cohort='main', split='test_id'):
    eligible = [r for r in rows if r['domain'] in domains and r['split'] == split
                and (cohort == 'main' or r['appendix'])]
    eligible.sort(key=lambda r: (r['domain'], not r.get('prepared_p11', True), r['sample_id']))
    if sample_ids:
        if len(set(sample_ids)) != len(sample_ids):
            raise ValueError('duplicate_sample_id')
        selected = [r for r in eligible if r['sample_id'] in sample_ids]
        missing = set(sample_ids) - {r['sample_id'] for r in selected}
        if missing:
            raise ValueError('Samples outside selected cached domain/cohort/split: ' + ', '.join(sorted(missing)))
        return selected
    if count < 1:
        raise ValueError('questions_per_domain_must_be_positive')
    selected = []
    for domain in domains:
        matches = [r for r in eligible if r['domain'] == domain]
        if len(matches) < count:
            raise ValueError(f'{domain}: requested {count}, available {len(matches)}; use list')
        selected.extend(matches[:count])
    return selected


def route(method, domain, cohort, training_config=None):
    if method == 'vanilla_llm':
        return {'kind': 'direct', 'available': True}
    if method in ('coconut', 'codi'):
        folder = RUNS['p11']/'custom'/method
        return {'kind': 'custom', 'folder': str(folder), 'available': (folder/'selected.json').exists(),
                'training_cohort': 'P11 appendix: 16 training trajectories per domain'}
    if training_config:
        c = load(training_config)
        if domain != c['domain']:
            return {'kind': 'numeric', 'available': False, 'reason': 'training_config_domain_mismatch'}
        folder = Path(c['run_root'])
        variant = ALIASES[method].removeprefix('continued_')
        # The fresh RNN variant has no bias-initialization prefix.
        if method == 'rnn': variant = 'constant_context_text_rnn'
    elif method == 'phi_jepa':
        folder = RUNS['p11']/'models'/cohort/domain
        variant = 'phi_jepa'
    else:
        folder = RUNS['p10']
        variant = ALIASES[method]
        if domain != 'tethered_load':
            return {'kind': 'numeric', 'available': False, 'reason': 'no_checkpoint_for_domain'}
    selected = folder/'numerical'/variant/'selected.json'
    return {'kind': 'numeric', 'folder': str(folder), 'variant': variant, 'available': selected.exists(),
            'reason': None if selected.exists() else 'no_checkpoint_for_domain',
            'solver': load(training_config)['solver'] if training_config else {'method': 'rk4', 'substeps': 1}}


class ReadThroughCache:
    """Validate exact request/output hashes; never write historical caches."""
    def __init__(self, destination, sources):
        from phi_jepa.providers.cache import FrozenOutputCache
        self.local = FrozenOutputCache(destination)
        self.sources = [FrozenOutputCache(p) for p in sources]
        self.hit = None

    def read(self, identity):
        for cache in [self.local, *self.sources]:
            result = cache.read(identity)
            if result is not None:
                self.hit = {'path': str(cache.root/(digest(identity)+'.json')), 'metadata': result.get('metadata')}
                self.local.write(identity, result)
                return result
        return None

    def write(self, identity, value):
        self.local.write(identity, value)


def forecast_worker(job, dest):
    guard_deployment_io()
    import torch
    from p10_inference import load_selected, predict
    from phi_jepa.integration.contracts import PublicProblem, enriched_context, validate_enrichment
    torch.set_num_threads(2)
    row = job['row']; sid = row['sample_id']; routing = job['route']
    context_root = Path(job.get('context_root', str(RUNS['p11'])))
    run = ReadOnlyRun('p11', row['domain'], job['cohort'])
    run.source = context_root
    run.root = Path(routing['folder']); run.c = {'solver': routing['solver']}
    model, solver, model_job = load_selected(run, routing['variant'])
    mode = model_job['context_identity']['mode']
    problem = PublicProblem.parse(row['public'])
    # Check public-cache binding before numerical deployment.
    notes = load(context_root/'enrichment'/f'{sid}.json') if mode == 'enriched' and model_job['method'] != 'no_text_conditioning' else None
    if notes is not None: validate_enrichment(problem, notes)
    if model_job['method'] != 'no_text_conditioning':
        encoder = model_job['context_identity']['encoder']
        recorded = load(context_root/'encoding-report.json')['settings']
        if any(encoder[k] != recorded[k] for k in ('model', 'model_revision', 'tokenizer_revision', 'pooling', 'normalization', 'max_length', 'precision', 'embedding_width')):
            raise ValueError('checkpoint_encoder_cache_mismatch')
        embedding = load(context_root/'embeddings'/mode/f'{sid}.json')
        context = (enriched_context(problem, notes, problem.input['observation_cutoff']) if mode == 'enriched'
                   else problem.context(problem.input['observation_cutoff']))
        if embedding['context_sha256'] != digest(context):
            raise ValueError('embedding_public_context_mismatch')
        save(dest/'embedding.json', embedding)
    if notes is not None: save(dest/'enrichment.json', notes)
    context_config = load(ROOT/'configs/model_context_p02b.json')
    save(dest/'context_config.json', context_config)
    save(dest/'enrichment_prompt.json', load(ROOT/context_config['enrichment_asset']))
    pointer = run.root/'numerical'/routing['variant']/'selected.json'
    save(dest/'selected_checkpoint.json', load(pointer))
    save(dest/'model_job.json', model_job)
    result = predict(run, model, solver, model_job, row)
    result['checkpoint_sha256'] = load(pointer)['checkpoint']['sha256']
    save(dest/'forecast.json', result)


def answer_worker(job, dest, output):
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.providers.openai_answer import OpenAIAnswer
    from phi_jepa.providers.credentials import load_openai_key
    direct = job['method'] == 'vanilla_llm'
    forecast = None; outcomes = []
    if not direct:
        record = load(dest/'forecast.json')
        if record['status'] != 'success':
            save(dest/'answer.json', {'status': 'forecast_failure', 'answer': None, 'reason': record.get('reason')})
            return
        forecast, outcomes = record['named'], record['readout']
    c = load(output/'config.json')
    # Read credentials only in the explicitly enabled provider process, before
    # installing the deployment guard. Cache-only runs need no credentials.
    key = load_openai_key(ROOT/'.env') if c['caps']['provider_usd'] > 0 else 'cache-only-no-network'
    guard_deployment_io()
    asset_path = ROOT/'docs/assets'/('p11_direct_answer_v1.json' if direct else 'p04a_answer_v1.json')
    asset = load(asset_path)
    pc = {**load(ROOT/'configs/baselines_p05b.json')['answer_profile'], 'max_attempts_per_request': 1}
    condition = 'direct_llm' if direct else ('main_phi' if job['cohort'] == 'main' else 'appendix_phi') if job['method'] == 'phi_jepa' else job['method']
    policy = 'direct_prediction' if direct else 'readout'
    fresh = c['vanilla_answers' if direct else 'phi_answers'] == 'fresh'
    cache = None if fresh else ReadThroughCache(output/'answer_cache', [RUNS['p11']/'answer_cache', RUNS['p10']/'answer_cache'])
    obj = OpenAIAnswer(key, pc, asset, cache, event_sink=lambda value: save(dest/'provider_ledger.json', value))
    budget = QualificationBudget(output, c)
    bounded = budget.transport(obj._http)

    blocked = []

    def transport(payload, timeout):
        if c['caps']['provider_usd'] <= 0:
            blocked.append('fresh_generation_requires_positive_api_budget' if fresh else 'cache_miss: fresh answer requires --max-api-usd greater than zero')
            raise RuntimeError('cache_miss: fresh answer requires --max-api-usd greater than zero')
        return bounded(payload, timeout)

    obj.transport = transport
    save(dest/'prompt.json', asset)
    start = time.perf_counter()
    try:
        answer = obj.answer(PublicProblem.parse(job['row']['public']), forecast, outcomes,
                            condition=condition, boolean_policy=policy,
                            request_sink=lambda value: save(dest/'request.json', value))
        result = {'status': 'success', 'answer': answer}
    except Exception as exc:
        reason = blocked[0] if blocked else budget.read().get('stopped') or getattr(exc, 'reason', str(exc))
        result = {'status': ('budget_required' if fresh else 'cache_miss') if blocked else 'answer_failure', 'answer': None, 'reason': reason, 'error_type': type(exc).__name__}
        historical = RUNS['p11']/'answers'/condition/f"{job['row']['sample_id']}.json"
        if historical.exists():
            prior = load(historical)
            if prior.get('public_sha256') == digest(job['row']['public']) and prior.get('forecast_sha256') == digest(forecast):
                save(dest/'historical_answer_attempt.json', prior)
                result['historical_attempt'] = {'status': prior['status'], 'reason': prior.get('reason'),
                                                'meaning': 'Previous run only; no new attempt charged here'}
    hit = cache.hit if cache is not None else None
    result.update(condition=condition, boolean_policy=policy, provider_profile=pc,
                  origin='validated_cache' if hit else 'not_generated' if blocked else 'fresh_provider_generation' if result['status'] == 'success' else 'provider_attempt_or_failure', cache=hit,
                  requested_answer_mode='fresh' if fresh else 'prefer_cache',
                  response_metadata=obj.response_metadata, elapsed_seconds=time.perf_counter()-start)
    save(dest/'answer.json', result)


def custom_worker(job, dest):
    guard_deployment_io()
    import torch
    from transformers import AutoTokenizer
    from phi_jepa.baselines.custom_checkpoint import load_checkpoint
    from phi_jepa.baselines.custom_io import TextCodec, decode_result, public_text
    from phi_jepa.integration.contracts import PublicProblem, validate_enrichment
    torch.set_num_threads(2)
    folder = Path(job['route']['folder']); selected = load(folder/'selected.json')
    settings = load(ROOT/'configs/custom_p06.json')
    codec = TextCodec(AutoTokenizer.from_pretrained(settings['model'], revision=settings['revision'],
                      cache_dir=str(NATIVE/'model-cache'), local_files_only=True))
    p = PublicProblem.parse(job['row']['public'])
    notes = load(Path(job.get('context_root', str(RUNS['p11'])))/'enrichment'/f'{p.sample_id}.json'); validate_enrichment(p, notes)
    branch = 'coconut' if job['method'] == 'coconut' else 'student'
    text = public_text(p, notes['notes'], branch=branch)
    tokens = codec.tokens(text, settings['max_input_tokens'])
    save(dest/'prompt.json', {'branch': branch, 'text': text, 'input_token_ids': tokens})
    model, _, _ = load_checkpoint(folder/selected['directory'], identity=load(folder/'identity.json'), device='cuda', training=False)
    generation = load(ROOT/'configs/qualification_p10.json')['generation']
    ids = torch.tensor([tokens], device='cuda')
    with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
        generated = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), branch=branch, generation=generation)[0].tolist()
    result = decode_result(codec, generated, p, teacher=branch == 'coconut')
    eos = codec.tokenizer.eos_token_id in generated
    result.update(token_ids=generated, EOS_terminated=eos, missing_EOS=not eos,
                  token_cap_termination=not eos and len(generated)-1 >= generation['max_new_tokens'],
                  generation=generation, checkpoint=selected, model=settings['model'], revision=settings['revision'],
                  teacher_inference_calls=0, origin='fresh_local_generation')
    save(dest/'answer.json', result)


def evaluate_run(output):
    """Only this separately launched process opens evaluator references."""
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.typed_evaluation import evaluate_targets, trajectory_errors
    from phi_jepa.capabilities import target_coverage
    c = load(output/'config.json'); records = []; physical = []; coverage = []; gold = {}
    reference_paths = {d: RUNS['p11']/'private'/d/f"{c['split']}-references.json" for d in c['domains']}
    if c.get('inventory_source') == 'release':
        from answer_inventory import catalog
        cat = catalog(); selected = {r['sample_id'] for r in load(output/'selection.json')}
        refs = {d: {p.sample_id: ref for p, ref, identity in cat.records(d, c['split']) if p.sample_id in selected} for d in c['domains']}
        reference_paths = {d: cat.verified_file(d, c['split'], 'references.jsonl') for d in c['domains']}
    else:
        refs = {d: load(path) for d, path in reference_paths.items()}
    reference_hashes = {d: file_hash(path) for d, path in reference_paths.items()}
    for row in load(output/'selection.json'):
        p = PublicProblem.parse(row['public']); ref = refs[row['domain']][p.sample_id]
        gold[p.sample_id] = gold_record(row, ref, reference_paths[row['domain']], reference_hashes[row['domain']])
        for method in c['methods']:
            dest = output/row['domain']/p.sample_id/method
            result = load(dest/'answer.json'); answer = result.get('answer')
            metric = evaluate_targets(p, ref, answer['targets'] if answer else [], method=method,
                                      failure=None if answer else result.get('reason', result['status']))
            metric.update(domain=row['domain'], typed_output_valid=answer is not None, generation_status=result['status'])
            records.append(metric)
            fp = dest/'forecast.json'
            if fp.exists():
                f = load(fp)
                physical.append({'sample_id': p.sample_id, 'domain': row['domain'], 'method': method,
                    **trajectory_errors(f.get('named', {}).get('states', []), ref['states'], mode='autonomous')})
                coverage.extend({'sample_id': p.sample_id, 'method': method, **v} for v in target_coverage(p, f.get('readout', [])))
    save(output/'evaluation/answers.json', records)
    save(output/'evaluation/physical_errors.json', physical)
    save(output/'evaluation/coverage.json', coverage)
    # The existing deployment I/O guard forbids every path containing "private".
    # These are evaluator outputs only, never a model/provider input artifact.
    save(output/'evaluation/private/gold_answers.json', gold)


def gold_record(row, reference, source, source_sha256):
    """Export only requested typed gold labels, without future trajectories."""
    from phi_jepa.inference.readout import BINDING
    labels = reference['structured_label']
    indexed = {t['target_id']: t for t in labels}
    specs = row['public']['input']['answer_spec']
    if len(indexed) != len(labels) or set(indexed) != {s['target_id'] for s in specs}:
        raise ValueError('gold_target_identity')
    targets = []
    for spec in specs:
        label = indexed[spec['target_id']]
        if (label['unit'], label['frame']) != (spec['unit'], spec['frame']):
            raise ValueError('gold_target_binding')
        targets.append({**{k: spec[k] for k in BINDING}, 'value': label['value'],
                        'absolute_tolerance': spec['absolute_tolerance'],
                        'relative_tolerance': spec['relative_tolerance']})
    return {'sample_id': row['sample_id'], 'scenario_id': row['scenario_id'], 'domain': row['domain'],
            'split': row['split'], 'public_sha256': digest(row['public']), 'targets': targets,
            'source': str(source), 'source_sha256': source_sha256,
            'purpose': 'Evaluator reference for comparison after inference; never model input'}


def markdown_cell(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, allow_nan=False)
    return text.replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')


def gold_comparison(row, gold, results):
    """Display original typed values; failed outputs never receive guessed values."""
    if gold['public_sha256'] != digest(row['public']):
        raise ValueError('gold_public_identity_mismatch')
    columns = ['Target', 'Query / time (s)', 'Unit', 'Frame', 'Gold answer', *results]
    lines = ['| ' + ' | '.join(map(markdown_cell, columns)) + ' |',
             '| ' + ' | '.join('---' for _ in columns) + ' |']
    for target in gold['targets']:
        values = [target['target_id'], f"{target['query_kind']}: {target['start_time']}–{target['end_time']}",
                  target['unit'], target['frame'], target['value']]
        for result in results.values():
            answer = result.get('answer')
            matches = [t for t in answer['targets'] if t['target_id'] == target['target_id']] if answer else []
            if result['status'] != 'success' or not answer:
                value = f"{result['status']}: {result.get('reason', 'no valid answer')}"
            elif len(matches) != 1:
                value = 'failure: missing or duplicate target'
            elif matches[0]['status'] != 'supported':
                value = f"{matches[0]['status']}: {matches[0].get('reason', 'unavailable')}"
            else:
                value = matches[0]['value']
            values.append(value)
        lines.append('| ' + ' | '.join(map(markdown_cell, values)) + ' |')
    return lines


def prose(result):
    answer = result.get('answer')
    if not answer:
        return f"No valid final answer. Status: {result['status']}. Reason: {result.get('reason', 'unspecified')}."
    if 'plain_text_answer' in answer: return answer['plain_text_answer']
    # Transparent presentation of custom typed output, not another model call or
    # parser repair. Student objective and official scores remain unchanged.
    lines = ['Display rendering of valid typed predictions (not model-generated prose):']
    for t in answer['targets']:
        lines.append(f"{t['entity_id']} {t['quantity']}: {json.dumps(t['value'])} {t['unit']}.")
    if answer.get('explanation'): lines.append('Model description: ' + answer['explanation'])
    return '\n\n'.join(lines)


def report(output):
    c = load(output/'config.json'); rows = load(output/'selection.json')
    ep = output/'evaluation/answers.json'; metrics = load(ep) if ep.exists() else []
    lookup = {(r['sample_id'], r['method']): r for r in metrics}
    gold_path = output/'evaluation/private/gold_answers.json'
    gold = load(gold_path) if gold_path.exists() else {}
    lines = ['# Question and answer comparison', '',
        'Same selected public question for every requested method. Numerical inference is fresh; each answer records cache reuse or fresh generation.', '',
        f"Answer policy: vanilla={c['vanilla_answers']}; Phi-JEPA/numerical methods={c['phi_answers']}. Shared provider cap: USD {c['caps']['provider_usd']}.", '',
        'Phi-JEPA uses qualified forecast/readout Boolean outputs; vanilla GPT-5.6 Sol may attempt all requested components directly. Unsupported components and failures remain in denominators.', '',
        'Assessment is partial and uncalibrated. Human-reviewed clarification is separate and is not invoked.', '']
    summary = []
    for method in c['methods']:
        ms = [m for m in metrics if m['method'] == method]
        results = [load(output/r['domain']/r['sample_id']/method/'answer.json') for r in rows]
        item = {'method': method, 'questions': len(rows), 'valid_answers': sum(bool(r.get('answer')) for r in results),
                'statuses': dict(Counter(r['status'] for r in results)),
                'complete_successes': sum(m['complete_success'] for m in ms) if ms else None,
                'unsupported_targets': sum(t['status'] == 'unsupported' for m in ms for t in m['targets']) if ms else None}
        summary.append(item)
        lines.append(f"- {method}: {item['valid_answers']}/{len(rows)} valid answers; complete correct: {item['complete_successes'] if ms else 'not evaluated'}; statuses: {item['statuses']}")
    for row in rows:
        sid = row['sample_id']; lines += ['', f"## {row['domain']} — {sid}", '', row['public']['input']['question'], '',
                                         f"Scenario: `{row['scenario_id']}`; partition: `{row['split']}`."]
        if sid in gold:
            results = {m: load(output/row['domain']/sid/m/'answer.json') for m in c['methods']}
            comparison = gold_comparison(row, gold[sid], results)
            lines += ['', '### Gold and predicted answers', '',
                      'Gold values are evaluator references added after inference. Values retain their original precision.', '',
                      *comparison, '', '[Typed gold answers](evaluation/private/gold_answers.json)']
            print(f"\nGold comparison — {row['domain']} / {sid}\n" + '\n'.join(comparison))
        else:
            lines += ['', 'Gold answers unavailable: evaluation has not exported references for this case.']
        for method in c['methods']:
            path = output/row['domain']/sid/method/'answer.json'; result = load(path)
            lines += ['', f'### {method}', '', prose(result), '', f"Origin: {result.get('origin', result['status'])}. [Raw answer]({path.relative_to(output).as_posix()})"]
            if (sid, method) in lookup:
                metric = lookup[(sid, method)]
                lines += ['', f"Strict evaluation: {'complete correct' if metric['complete_success'] else 'not completely correct'}; {sum(t['success'] for t in metric['targets'])}/{metric['eligible_targets']} target components correct."]
            (path.parent/'answer.txt').write_text(prose(result)+'\n', encoding='utf-8')
    budget = load(output/'budget.json')
    summary_record = {'methods': summary, 'provider_attempts': len(budget['provider']),
        'charged_usd': sum(p['charged_usd'] for p in budget['provider']),
        'charged_input_tokens': sum(p['charged_input'] for p in budget['provider']),
        'charged_output_tokens': sum(p['charged_output'] for p in budget['provider']),
        'cost_basis': 'Existing conservative provider accounting; estimates, not an invoice',
        'local_operations': budget['operations'], 'assessment': 'not_recomputed_underlying_system_partial_uncalibrated',
        'gold_answers': {'exported_questions': len(gold), 'path': str(gold_path) if gold else None},
        'evaluation': 'complete' if len(metrics) == len(rows)*len(c['methods']) else 'not_complete'}
    save(output/'summary.json', summary_record)
    (output/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(summary_record, indent=2)); print(f'Questions and answers: {output / "report.md"}')


def launch(output, command, name, env_name='phi-core', timeout=600, gpu=False):
    logs = output/'logs'; logs.mkdir(exist_ok=True)
    start = time.perf_counter()
    state = load(output/'budget.json'); resource = 'gpu' if gpu or env_name != 'phi-core' else 'cpu'
    remaining = state['caps'][resource+'_seconds'] - state['seconds'].get(resource, 0)
    artifact_bytes = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    if remaining <= 0 or artifact_bytes >= state['caps']['artifact_bytes']:
        (logs/f'{name}.log').write_text(resource+'_time_cap_or_artifact_cap\n')
        return 125
    timeout = min(timeout, remaining)
    env = {**os.environ, 'HF_HUB_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false'}
    if resource == 'cpu': env['CUDA_VISIBLE_DEVICES'] = ''
    with (logs/f'{name}.log').open('w') as stream:
        try:
            p = subprocess.run([str(NATIVE/'.venvs'/env_name/'bin/python'), *command], cwd=ROOT,
                               env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            code = p.returncode
        except subprocess.TimeoutExpired: code = 124
    elapsed = time.perf_counter()-start
    state = load(output/'budget.json')
    state['seconds'][resource] = state['seconds'].get(resource, 0) + elapsed
    state['operations'].append({'name': name, 'environment': env_name, 'elapsed_seconds': elapsed, 'exit_code': code})
    save(output/'budget.json', state)
    return code


def archive_source(output):
    paths = [*ROOT.glob('src/phi_jepa/**/*.py'), *ROOT.glob('tools/*.py'),
             *ROOT.glob('configs/*.json'), *ROOT.glob('docs/assets/*.json')]
    sources = {str(p.relative_to(ROOT)): file_hash(p) for p in paths}
    for p in paths:
        target = output/'source/blobs'/sources[str(p.relative_to(ROOT))]
        if not target.exists(): target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(p.read_bytes())
    save(output/'source/identity.json', {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                                      'files': sources, 'meaning': 'Current working-tree content, including uncommitted changes'})


def verify_resume_source(output):
    for relative, expected in load(output/'source/identity.json')['files'].items():
        path = ROOT/relative
        if not path.exists() or file_hash(path) != expected:
            raise ValueError('Source changed since run; use a new output directory: ' + relative)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['list', 'run', 'train-and-run', 'evaluate', '_forecast', '_answer', '_custom', '_enrich', '_encode'])
    p.add_argument('--domains', nargs='+', choices=[*DOMAINS, 'all'], default=['all'])
    p.add_argument('--methods', nargs='+', choices=METHODS, default=['phi_jepa', 'vanilla_llm'])
    p.add_argument('--questions-per-domain', type=int, default=3)
    p.add_argument('--sample-id', action='append')
    p.add_argument('--cohort', choices=['main', 'appendix'], default='main')
    p.add_argument('--inventory', choices=['auto', 'p11', 'release'], default='auto')
    p.add_argument('--dry-run', action='store_true', help='Validate selection and show counts without creating files or running models/providers')
    p.add_argument('--split', choices=['test_id', 'validation', 'train'], default='test_id')
    p.add_argument('--output', type=Path)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--skip-evaluation', action='store_true')
    p.add_argument('--max-api-usd', type=float, default=5)
    p.add_argument('--vanilla-answers', choices=['fresh', 'cache'], default='fresh')
    p.add_argument('--phi-answers', choices=['fresh', 'cache'], default='cache')
    p.add_argument('--max-provider-attempts', type=int, default=120)
    p.add_argument('--max-input-tokens', type=int, default=2000000)
    p.add_argument('--max-output-tokens', type=int, default=100000)
    p.add_argument('--training-config', type=Path)
    p.add_argument('--job', type=Path, help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.command in ('_enrich', '_encode'):
        import answer_context
        getattr(answer_context, args.command[1:])(args.output)
        return
    if args.command.startswith('_'):
        job = load(args.job); dest = args.job.parent
        try:
            if args.command == '_forecast': forecast_worker(job, dest)
            elif args.command == '_answer': answer_worker(job, dest, args.output)
            else: custom_worker(job, dest)
        except Exception as exc:
            save(dest/'answer.json', {'status': 'worker_failure', 'answer': None,
                                     'reason': str(exc), 'error_type': type(exc).__name__})
            raise
        return
    if args.command == 'evaluate':
        if not args.output: p.error('evaluate requires --output of an existing comparison')
        evaluate_run(args.output); report(args.output); return
    domains = list(DOMAINS) if 'all' in args.domains else list(dict.fromkeys(args.domains))
    if len(set(args.methods)) != len(args.methods): p.error('duplicate method')
    from answer_inventory import inventory
    expanded = args.inventory == 'release' or (args.command == 'list' and args.inventory == 'auto' and args.cohort == 'main')
    if expanded and args.cohort == 'appendix': p.error('appendix preserves its matched P11 cohort; use --cohort main for release cases')
    pool = inventory(domains, args.split, expand=expanded)
    try:
        rows = select_rows(pool, domains, args.questions_per_domain, args.sample_id, args.cohort, args.split) if args.command != 'list' else pool
    except ValueError as exc:
        if args.inventory == 'auto' and args.cohort == 'main' and not expanded and args.questions_per_domain > 0:
            expanded = True; pool = inventory(domains, args.split, expand=True)
            try: rows = select_rows(pool, domains, args.questions_per_domain, args.sample_id, args.cohort, args.split)
            except ValueError as full_exc: p.error(str(full_exc))
        else: p.error(str(exc))
    if args.command == 'list':
        rows = [r for r in pool if r['domain'] in domains and r['split'] == args.split and (args.cohort == 'main' or r['appendix'])]
        for r in sorted(rows, key=lambda r: (r['domain'], r['sample_id'])):
            print(f"{r['domain']}\t{r['sample_id']}\t{r['public']['input']['question']}")
        print(json.dumps({d: {m: route(m, d, args.cohort) for m in METHODS} for d in domains}, indent=2))
        return
    print(json.dumps({'inventory': 'release' if expanded else 'p11', 'selected_questions': dict(Counter(r['domain'] for r in rows)),
                      'prepared_p11_questions': sum(r.get('prepared_p11', True) for r in rows),
                      'available_questions': dict(Counter(r['domain'] for r in pool if r['domain'] in domains and r['split'] == args.split))}), flush=True)
    if args.dry_run: return
    if not args.output: p.error('run requires a new --output directory (or --resume)')
    if args.max_api_usd < 0 or not __import__('math').isfinite(args.max_api_usd): p.error('invalid API budget')
    if min(args.max_provider_attempts, args.max_input_tokens, args.max_output_tokens) < 0: p.error('negative provider cap')
    output = args.output.expanduser().resolve()
    if args.resume:
        output_path(output/'new-path-safety-check')
        if not (output/'config.json').exists(): p.error('no comparison to resume')
        verify_resume_source(output)
    else:
        output = output_path(output); output.mkdir(parents=True)
    if args.command == 'train-and-run':
        if not args.training_config: p.error('train-and-run requires --training-config; see docs/Run_answers_WSL.md')
        tc = load(args.training_config)
        if domains != [tc['domain']]: p.error('train-and-run requires its one explicit config domain')
        if any(m in ('coconut', 'codi') for m in args.methods): p.error('custom retraining uses the existing explicit custom training pipeline; this mode trains numerical methods')
        if Path(tc['run_root']).resolve().is_relative_to(RUNS['p10']) or Path(tc['run_root']).resolve().is_relative_to(RUNS['p11']):
            p.error('training requires a new manual run, never a historical run')
    c = {'domains': domains, 'methods': args.methods, 'cohort': args.cohort, 'split': args.split,
         'sample_ids': [r['sample_id'] for r in rows], 'selection_rule': 'prepared P11 cases first, then lexicographic sample ID within original partition; no outcome access',
         'inventory_source': 'release' if expanded else 'p11',
         'vanilla_answers': args.vanilla_answers, 'phi_answers': args.phi_answers,
         'training_config': str(args.training_config.resolve()) if args.training_config else None,
         'training_config_sha256': file_hash(args.training_config) if args.training_config else None,
         'export_directory': str(output/'export_unused'),
         'caps': {'provider_usd': args.max_api_usd, 'provider_attempts': args.max_provider_attempts,
                  'provider_input_tokens': args.max_input_tokens, 'provider_output_tokens': args.max_output_tokens,
                  'artifact_bytes': 2*10**9, 'cpu_seconds': 3600, 'gpu_seconds': 3600}}
    if args.resume and load(output/'config.json') != c: p.error('resume requires identical selection/methods/budgets/config')
    save(output/'config.json', c); save(output/'selection.json', rows)
    QualificationBudget(output, c)
    if not args.resume: archive_source(output)
    lock = output/'.running'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        if args.command == 'train-and-run':
            from p10_common import Run
            from run_pipeline import launch as train_stage
            run = Run(args.training_config)
            train_stage(run, 'encode')
            for method in args.methods:
                if method == 'vanilla_llm': continue
                variant = route(method, domains[0], args.cohort, args.training_config)['variant']
                train_stage(run, 'numerical', variant)
            save(output/'training.json', {'config': str(args.training_config.resolve()), 'budget': run.b.read(), 'root': str(run.root)})
        if set(args.methods) - {'vanilla_llm', 'no_text_conditioning'}:
            launch(output, [str(Path(__file__)), '_enrich', '--output', str(output)], 'context-enrichment', timeout=3600)
            launch(output, [str(Path(__file__)), '_encode', '--output', str(output)], 'context-encoding', gpu=True, timeout=3600)
        for row in rows:
            case = output/row['domain']/row['sample_id']; save(case/'public.json', row['public'])
            (case/'question.txt').write_text(row['public']['input']['question']+'\n', encoding='utf-8')
            print(f"{row['domain']} {row['sample_id']}: {row['public']['input']['question']}", flush=True)
            for method in args.methods:
                dest = case/method; dest.mkdir(exist_ok=True)
                if (dest/'answer.json').exists(): continue  # failures are retained too
                routing = route(method, row['domain'], args.cohort, args.training_config)
                job = {'row': row, 'method': method, 'route': routing, 'cohort': args.cohort, 'context_root': str(output/'context')}
                save(dest/'job.json', job)
                if not routing['available']:
                    save(dest/'answer.json', {'status': 'unavailable', 'answer': None, 'reason': routing.get('reason', 'checkpoint_unavailable')})
                    continue
                common = ['--job', str(dest/'job.json'), '--output', str(output)]
                code = 0
                if routing['kind'] == 'numeric' and not (dest/'forecast.json').exists():
                    code = launch(output, [str(Path(__file__)), '_forecast', *common], f'{row["sample_id"]}-{method}-forecast')
                if code == 0:
                    custom = routing['kind'] == 'custom'
                    code = launch(output, [str(Path(__file__)), '_custom' if custom else '_answer', *common],
                                  f'{row["sample_id"]}-{method}-answer',
                                  ('phi-coconut-custom' if method == 'coconut' else 'phi-codi-custom') if custom else 'phi-core')
                if not (dest/'answer.json').exists():
                    save(dest/'answer.json', {'status': 'worker_failure', 'answer': None, 'reason': f'exit_{code}; see logs'})
                print(method + ': ' + prose(load(dest/'answer.json')), flush=True)
        if not args.skip_evaluation:
            launch(output, [str(Path(__file__)), 'evaluate', '--output', str(output)], 'evaluation')
        report(output)
        verify_resume_source(output)
        answers = [load(output/r['domain']/r['sample_id']/m/'answer.json') for r in rows for m in args.methods]
        save(output/'completion.json', {'status': 'complete' if all(a['status'] == 'success' for a in answers) else 'complete_with_failures',
             'requested_answers': len(answers), 'valid_answers': sum(bool(a.get('answer')) for a in answers),
             'training': args.command == 'train-and-run', 'historical_evidence_modified': False})
    finally:
        os.close(fd); lock.unlink()


if __name__ == '__main__': main()
