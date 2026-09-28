"""Select existing release public inputs without opening reference answers."""
from p10_common import ROOT, load, digest, file_hash, ReleaseCatalog
from replay_pipeline import RUNS
from phi_jepa.integration.readers import PublicInputReader, json_lines


def catalog():
    c = load(ROOT/'configs/model_training_p02a.json')
    return ReleaseCatalog(ROOT/c['export_root'], c['export_index_sha256'], c['release_manifest_sha256'])


def inventory(domains, split, *, expand=False):
    prepared = load(RUNS['p11']/'selected-public.json')
    if not expand:
        return prepared
    cat = catalog(); indexed = {r['sample_id']: r for r in prepared}; rows = []
    known_non_test = {r['scenario_id'] for r in prepared if r['split'] != 'test_id'}
    for domain in domains:
        # This preparation-only reader uses partition/scenario metadata, never
        # reference labels, future trajectories or evaluation scores.
        metadata = {r['sample_id']: r['metadata'] for r in json_lines(cat.verified_file(domain, split, 'evaluator.jsonl'))}
        path = cat.verified_file(domain, split, 'inputs.jsonl')
        public_sha256 = file_hash(path)
        for p in PublicInputReader(path, public_sha256):
            meta = metadata[p.sample_id]
            if meta['split'] != split or meta['validation']['status'] != 'accepted' or meta['record_origin'] != 'simulation':
                raise ValueError('release_partition_identity_mismatch')
            if split == 'test_id' and meta['base_scenario_id'] in known_non_test:
                raise ValueError('heldout_scenario_overlaps_training_or_selection')
            public = {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}
            old = indexed.get(p.sample_id)
            if old and digest(old['public']) != digest(public):
                raise ValueError('prepared_public_release_mismatch')
            rows.append({'sample_id': p.sample_id, 'scenario_id': meta['base_scenario_id'],
                         'split_group': meta['split_group_id'], 'split': split, 'domain': domain,
                         'public': public, 'appendix': bool(old and old['appendix']),
                         'prepared_p11': old is not None, 'release_identity': cat.identity,
                         'public_file_sha256': public_sha256})
    return rows
