"""SPQ05 protocol freeze and request estimates. No provider or simulator execution."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import random
import subprocess

from .annotation import PROMPT, payload, reservation, schema
from .dataset import SourceLocation, migrate
from .io import ROOT, DOMAINS, QUESTION_TYPES, canonical, digest, external, parse, read
from .spq01a import retained, verify_manifest


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def candidates(rows, excluded, seed, per_cell=7, reserves=7):
    """Random disjoint family pools, one random source QA per group, bounded reserves."""
    if per_cell != 7 or reserves != 7:
        raise ValueError("frozen 7+7 cell allocation required")
    by_domain = {domain: defaultdict(list) for domain in DOMAINS}
    seen = set()
    groups = {}
    rejected = []
    for row in rows:
        if row['sample_id'] in seen:
            raise ValueError('duplicate source sample')
        seen.add(row['sample_id'])
        group = row['group_id']
        identity = (row['domain'], row['split'], row['trajectory_id'])
        if group in groups and groups[group] != identity:
            raise ValueError('group crosses domain/split/trajectory')
        groups[group] = identity
        if group in excluded or row['trajectory_id'] in excluded:
            rejected.append({'sample_id': row['sample_id'], 'group_id': group,
                             'reason': 'authoritative_development_exclusion'})
        else:
            if row['question_type'] != 'predictive':
                raise ValueError('source frame contains unsupported task')
            by_domain[row['domain']][group].append(row)
    rng = random.Random(seed)
    selected = []
    pool_counts = {}
    for domain in DOMAINS:
        order = sorted(by_domain[domain])
        rng.shuffle(order)
        pools = {family: [] for family in QUESTION_TYPES}
        for i, group in enumerate(order):
            family = QUESTION_TYPES[i % len(QUESTION_TYPES)]
            source = rng.choice(sorted(by_domain[domain][group], key=lambda r: r['sample_id']))
            pools[family].append(source)
        for family in QUESTION_TYPES:
            cell = domain + '/' + family
            pool_counts[cell] = len(pools[family])
            if len(pools[family]) < per_cell + reserves:
                raise ValueError('insufficient source groups for frozen cell: ' + cell)
            for rank, source in enumerate(pools[family][:per_cell + reserves], 1):
                selected.append({'candidate_id': 'SPQ05-C-' + digest({'cell': cell, 'rank': rank,
                                 'source': source['sample_id'], 'seed': seed})[:20],
                                 'cell': cell, 'domain': domain, 'question_type': family,
                                 'rank': rank, 'role': 'primary' if rank <= per_cell else 'reserve',
                                 'source': source})
    if len({c['source']['group_id'] for c in selected}) != len(selected):
        raise ValueError('candidate group duplication')
    return selected, rejected, pool_counts


def source_record(row):
    source = row['source']
    path = Path(source['path'])
    if file_hash(path) != source['file_sha256']:
        raise ValueError('source shard changed')
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    record = parse(lines[source['line'] - 1])
    if digest(record) != source['record_sha256']:
        raise ValueError('source record changed')
    if (record['sample_id'], record['metadata']['split_group_id'], record['metadata']['split'],
        record['input']['domain'], record['input']['observation_cutoff']) != (
        row['sample_id'], row['group_id'], row['split'], row['domain'], row['observation_cutoff']):
        raise ValueError('source inventory identity mismatch')
    return migrate(record, SourceLocation(source['path'], source['line'], source['file_sha256']))


def prepare(inventory, artifacts, output):
    """Read saved evidence, freeze protocol before any live qualification, fail closed."""
    output = external(output)
    config = read(ROOT/'configs/simphysqa/formal_audit.json')
    provider = read(ROOT/config['provider_config'])
    simulation = read(ROOT/config['simulation_config'])
    # Freeze only known settings. This command never loads credentials.
    if config['new_live_budget'] is not None:
        raise ValueError('preparation budget changed; new version/runner qualification required')
    verify_manifest(inventory)
    summary = read(inventory/'summary.json')
    hashes = read(inventory/'source-files.json')
    for name, expected in hashes.items():
        if file_hash(name) != expected:
            raise ValueError('release source preservation failure: ' + name)
    data_root = Path(summary['data_root'])
    if file_hash(data_root/'release-manifest.json') != summary['release_manifest_sha256']:
        raise ValueError('release manifest changed')
    exclusions = read(ROOT/config['exclusions'])
    rows = [parse(line) for line in (inventory/'records.jsonl').read_text(encoding='utf-8').splitlines() if line]
    if len(rows) != summary['records'] or len({r['group_id'] for r in rows}) != summary['groups']:
        raise ValueError('source frame cardinality changed')
    selected, rejected, pools = candidates(rows, set(exclusions['excluded_groups']), config['seed'])
    # Inspect only saved accounting, not provider credentials or additional outcome values.
    attempts = [read(p) for p in sorted((artifacts/'spq01/annotation-job/attempts').glob('*.json'))]
    accounting = read(artifacts/'spq01/annotation-job/summaries/002.json')
    simulation_reservations = list((artifacts/'spq02/runs/executions').glob('*/reservation.json'))
    if not attempts or not simulation_reservations:
        raise ValueError('historical budget evidence missing')
    used_initial = sum(a['initial_request'] for a in attempts)
    if used_initial != 16 or len(simulation_reservations) != 32:
        raise ValueError('historical usage changed; reassess capacity explicitly')
    # Later report-only commits do not change the scientific producer of saved output.
    # The complete file pins below still reject any changed scientific code/config.
    producer = (read(output/'protocol.json')['producer_commit'] if (output/'protocol.json').exists()
                else subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    pins = [ROOT/'dataset.schema.json', ROOT/'configs/simphysqa/formal_audit.json',
            ROOT/'docs/prompts/SPQ05_formal_audit.md']
    pins += sorted((ROOT/'src/simphysqa').glob('*.py')) + sorted((ROOT/'src/simphysqa').glob('*.json'))
    pins += sorted((ROOT/'docs/simphysqa').glob('formal_*.md'))
    pins += [ROOT/config['provider_config'], ROOT/config['simulation_config'], ROOT/config['exclusions']]
    identity = {'version': config['version'], 'producer_commit': producer, 'configuration': config,
                'pins': {p.relative_to(ROOT).as_posix(): file_hash(p) for p in pins},
                'inventory_manifest_sha256': file_hash(inventory/'manifest.json'),
                'frame_sha256': file_hash(inventory/'records.jsonl'),
                'release_manifest_sha256': summary['release_manifest_sha256'],
                'source_files_sha256': digest(hashes), 'exclusions_sha256': digest(exclusions),
                'candidate_order_sha256': digest(selected), 'provider_settings': {
                    k: v for k, v in provider.items() if k != 'credential_reference_file'},
                'prompt_sha256': digest(PROMPT), 'annotation_schema_sha256': digest(schema()),
                'original_simulation_limits': simulation['limits']}
    retained(output/'protocol.json', identity)  # First durable write before source qualification/dry-run.
    retained(output/'candidate-order.json', selected)
    retained(output/'source-frame-summary.json', {'summary': summary, 'pool_counts': pools,
             'source_files_verified': len(hashes), 'excluded_records': len(rejected),
             'excluded_groups': sorted(set(r['group_id'] for r in rejected)),
             'eligible_source_groups': summary['groups'] - len(set(r['group_id'] for r in rejected))})
    retained(output/'source-file-hashes.json', hashes)
    ledger = [{'stage': 'frame', 'status': 'excluded', **r} for r in rejected]
    sizes = []
    for candidate in selected:
        wrapper = source_record(candidate['source'])
        body = payload(wrapper, provider)
        bound = reservation(body, provider)
        retained(output/'organizer-private/prepared-requests'/(candidate['candidate_id']+'.json'), body)
        sizes.append({'candidate_id': candidate['candidate_id'], 'cell': candidate['cell'],
                      'rank': candidate['rank'], 'role': candidate['role'], 'request_bytes': len(canonical(body)),
                      'request_sha256': digest(body), **bound})
        ledger.append({'candidate_id': candidate['candidate_id'], 'cell': candidate['cell'],
                       'rank': candidate['rank'], 'source_admission': 'verified_saved_source',
                       'status': 'pending_budget', 'family_eligibility': 'not_yet_qualified',
                       'annotation_attempts': 0, 'simulation_executions': 0,
                       'reason': 'new initial-request allowance absent; original simulation ceiling consumed'})
    retained(output/'candidate-eligibility-failure-ledger.json', ledger)
    # Distinct file, exact JSONL, no field coercion.
    save_bytes(output/'candidate-ledger.jsonl', b''.join(canonical(r) for r in ledger))
    primary = [s for s in sizes if s['role'] == 'primary']
    def estimate(items):
        return {'requests': len(items), 'maximum_attempts_including_one_repair': 2*len(items),
                'input_token_upper_bound': sum(s['input_token_upper_bound'] for s in items),
                'output_token_limit': sum(s['output_token_limit'] for s in items),
                'initial_full_reservation_usd': sum(s['usd'] for s in items),
                'twice_initial_reservation_usd_excluding_repair_feedback': 2*sum(s['usd'] for s in items)}
    preflight = {'version': config['version'], 'status': 'blocked_budget_not_ready_for_review',
                 'model': provider['model'], 'reasoning_effort': provider['reasoning_effort'],
                 'max_output_tokens': provider['max_output_tokens'], 'timeout_seconds': provider['timeout_seconds'],
                 'primary': estimate(primary), 'bounded_candidates_including_reserves': estimate(sizes),
                 'pricing_status': 'historical_2026-10-04_reservation_rates_not_current_quote; refresh_before_live',
                 'repair_reservation': 'recompute actual feedback payload at admission; twice-initial is not a hard upper bound',
                 'prior_usage': {'initial_requests': used_initial, 'annotation_attempts': len(attempts),
                                 'saved_accounting': accounting, 'simulation_executions': len(simulation_reservations)},
                 'authorized_limits': {'annotation': provider['budget'], 'simulation': simulation['limits']},
                 'remaining_initial_requests': max(0, provider['budget']['initial_requests']-used_initial),
                 'remaining_simulation_executions': max(0, simulation['limits']['maximum_simulation_executions']-len(simulation_reservations)),
                 'simulation_requirements': {'primary_cf_and_explanation_pairs': 56,
                                             'coarse_and_fine_factual_and_omission_per_pair': 4,
                                             'primary_cf_and_explanation_executions': 224,
                                             'primary_with_all_clarification_pairs': 336,
                                             'candidate_cap_with_all_clarification_pairs': 672,
                                             'reuse': 'reuse verified matching saved evidence if present; exclusions prohibit development pairs'},
                 'qualification_attrition': 'unmeasured; all 28 primary clarification candidates pending; retain every attempt separately',
                 'executed_annotation_requests': 0, 'new_simulation_executions': 0,
                 'new_spend_usd': 0, 'items': sizes}
    retained(output/'preflight.json', preflight)
    shortfall = {'status': 'implemented_pending_validation', 'target_items': 140,
                 'complete_formal_packets': 0, 'shortfall': 140, 'final_manifest_frozen': False,
                 'formal_ratings_collected': 0, 'clarification_attrition': None,
                 'reason': '140 fresh groups need up to 140 new initial annotations; prior 16 initial calls and 32 simulations already consumed',
                 'required_decision': 'explicit additional bounded annotation and simulation budget; credentials accessed only by authorized live runner',
                 'protocol_sha256': digest(identity), 'preflight_sha256': digest(preflight)}
    retained(output/'shortfall.json', shortfall)
    for name in ('formal_protocol.md', 'formal_reviewer_guide.md', 'formal_analysis.md'):
        save_bytes(output/name, (ROOT/'docs/simphysqa'/name).read_bytes())
    from .focused_audit import COLUMNS
    import csv, io
    for reviewer in config['reviewers']:
        buffer = io.StringIO(newline='')
        csv.writer(buffer, lineterminator='\n').writerow(COLUMNS)
        save_bytes(output/'form-templates'/(reviewer+'.csv'), buffer.getvalue().encode())
    save_bytes(output/'index.html', (
        '<!doctype html><meta charset="utf-8"><title>SPQ05 preparation</title><h1>SPQ05: preparation, review blocked</h1>'
        '<p>0/140 formal packets; no human ratings. Three forms will cover identical items after final freeze. No calibration.</p>'
        '<ul><li><a href="protocol.json">Frozen protocol</a></li><li><a href="candidate-order.json">Candidate/reserve ordering</a></li>'
        '<li><a href="preflight.json">Non-secret preflight</a></li><li><a href="shortfall.json">Shortfall</a></li>'
        '<li><a href="formal_reviewer_guide.md">Reviewer guide</a></li><li><a href="formal_analysis.md">Analysis</a></li></ul>'
        '<p>Header-only form-templates are not assigned reviewer forms. Do not begin formal review.</p>').encode())
    files = {p.relative_to(output).as_posix(): file_hash(p) for p in sorted(output.rglob('*'))
             if p.is_file() and p.name != 'manifest.json'}
    retained(output/'manifest.json', {'version': config['version'], 'purpose': 'SPQ05_frozen_preparation_no_live_execution',
             'protocol_sha256': digest(identity), 'files': files, 'complete_formal_packets': 0})
    return {k: v for k, v in preflight.items() if k not in ('items', 'prior_usage')}


def save_bytes(path, data):
    path = external(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('resume content mismatch: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(canonical(prepare(args.inventory, args.artifacts, args.output)).decode(), end='')


if __name__ == '__main__':
    main()
