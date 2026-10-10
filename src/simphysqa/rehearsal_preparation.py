"""Prepare a bounded DEVELOPMENT rehearsal proposal only. Never executes a model."""
import argparse
from pathlib import Path
from .execution_readiness import read, put, sha, files, validate_package, assert_public
from .main_public import request_from


def prepare(pilot, package, output):
    pilot, package, output = map(Path, (pilot, package, output))
    validate_package(package); output.mkdir(parents=True, exist_ok=False)
    plan = read(pilot / 'pilot-plan.json'); spec = read(package / 'execution-spec.json')
    # Engineering examples fixed by domain/family before reading model responses.
    cells = [('robotic_arm', 'direct'), ('driving', 'predictive'), ('object_pushing_stacking', 'counterfactual'),
             ('tethered_load', 'explanation'), ('robotic_arm', 'clarification')]
    selected = [next(item for item in plan['selected'] if (item['domain'], item['family']) == cell) for cell in cells]
    mappings = []; per_shard = []
    for shard in spec['shards']:
        cid, label = shard['condition_id'], shard['representation']
        condition = read(package / spec['conditions'][cid]['path']); requests = []
        for item in selected:
            sid = item['sample_id']; original = pilot / 'public-requests' / cid / (sid + '.json')
            q, projection = request_from(read(original), label == 'structured_only'); assert_public(q)
            relative = f'public/{cid}--{label}/{sid}.json'; put(output / relative, q)
            requests.append(relative); mappings.append({'path': relative, 'source_public_request_sha256': sha(original), 'projection': projection,
                'procedure_sha256': sha(Path(__file__).parent / 'main_public.py'), 'status': 'unexecuted_development_rehearsal_request'})
        maximum = condition['settings']['max_seconds']; per_shard.append({'condition_id': cid, 'representation': label, 'owner': None,
            'initial_requests': 5, 'maximum_actual_supported_continuations': 1, 'processes_maximum': 2, 'requests': requests,
            'maximum_seconds': maximum * 6 + 600 * 2, 'stage_seconds': maximum, 'qualification': 'fresh hardware/runtime and render/stop metadata before rehearsal; task execution evidence afterward'})
    proposed = {'version': 'SPQ06-rehearsal-proposal/1.0.0', 'execution_scope': 'development_rehearsal', 'authorization': 'NOT_AUTHORIZED_NOT_EXECUTED',
        'pilot_plan_sha256': sha(pilot / 'pilot-plan.json'), 'main_package_sha256': sha(package / 'package-manifest.json'), 'selected': selected,
        'initial_request_ceiling': 55, 'conditional_request_ceiling': 11, 'total_request_ceiling': 66,
        'aggregate_seconds_ceiling': sum(shard['maximum_seconds'] for shard in per_shard), 'process_loading_seconds': 600,
        'shards': per_shard, 'new_model_calls': 0, 'owners_assigned': 0, 'main_accounting': 'separate; no real main keys/tickets/ledger',
        'bootstrap': 'Later separately authorized development coordinator issues runtime_qualified contexts restricted to these development IDs and at most six stages/condition/representation. Main job issuer/importer require task_qualified and main scope. No main ledger or return import for rehearsal.',
        'failure_policy': 'single attempt/stage, never-reserved-only resume, raw/partial failures and unknown work retained; supported actual clarification only; no authored substitute or accuracy acceptance threshold',
        'limitations': 'five engineering tasks span four domains, not a balanced quality estimate; conditional path remains unexercised when the actual first response is unsupported; record it explicitly'}
    assert proposed['aggregate_seconds_ceiling'] == 28320
    put(output / 'proposal.json', proposed); put(output / 'file-generation-index.json', {'mappings': mappings})
    put(output / 'manifest.json', {'files': files(output), 'model_calls': 0, 'authorization': proposed['authorization']})
    return proposed


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--pilot', required=True); p.add_argument('--package', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); result = prepare(a.pilot, a.package, a.output)
    print('Prepared unexecuted proposal:', result['initial_request_ceiling'], 'initials;', result['conditional_request_ceiling'], 'conditional;', result['aggregate_seconds_ceiling'], 'seconds.')
