"""Seal completed preparation evidence after the audit log has closed; no models."""
from p12_common import *
from p12_embeddings import RUN, EXPORT, frozen_config
from phi_jepa.providers.enrichment_budget import atomic_json
import shutil


def main():
    cfg = frozen_config();audit = load(RUN/'audit.json');completion = load(RUN/'completion.json')
    paths = sorted((RUN/'attempts').glob('*.json'));rows = [load(p) for p in paths]
    if len(rows) != cfg['maximum_model_calls'] or any(r['status'] != 'success' for r in rows):
        raise ValueError('preparation attempts incomplete')
    if audit['missing'] or not audit['all_attempts_successful'] or completion['status'] != 'complete':
        raise ValueError('final audit incomplete')
    if abs(sum(r['seconds'] for r in rows)-audit['encoding_seconds']) > 1e-6:
        raise ValueError('attempt cost accounting mismatch')
    atomic_json(RUN/'attempt-index.json', {'files': {str(p.relative_to(RUN)): file_hash(p) for p in paths},
                                         'count': len(paths), 'all_successful': True})
    for path in [*RUN.glob('*.json'), *RUN.glob('*.log')]:
        shutil.copyfile(path, EXPORT/path.name)
    helper_root = EXPORT/'reporting-source';helper_root.mkdir(exist_ok=True)
    helpers = [Path(__file__), ROOT/'tools/p12_embedding_status.py', ROOT/'tests/test_p12_embeddings.py']
    for path in helpers:shutil.copyfile(path, helper_root/path.name)
    atomic_json(EXPORT/'artifact-index.json', {'native_root': str(RUN),
        'files': {str(p.relative_to(EXPORT)): file_hash(p) for p in EXPORT.rglob('*') if p.is_file() and p.name != 'artifact-index.json'}})
    print({'attempts_verified': len(paths), 'additional_model_calls': 0, 'paid_calls': 0})


if __name__ == '__main__':
    main()
