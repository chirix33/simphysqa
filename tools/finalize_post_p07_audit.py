"""Hash the new audit bundle and verify preserved P07 source evidence, offline."""
import json
import subprocess
from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root / 'docs/reviews/artifacts/Post_P07'
manifest_path = output / 'manifest.json'
if manifest_path.exists(): raise FileExistsError(manifest_path)


def identity(path):
    with path.open('rb') as stream:
        hasher = sha256()
        while block := stream.read(1024 * 1024): hasher.update(block)
    return {'sha256': hasher.hexdigest(), 'bytes': path.stat().st_size}


preserved = json.loads((root / 'docs/reviews/artifacts/P07/sources.json').read_text())
for filename, expected in preserved.items():
    actual = identity(Path(filename))
    assert actual['sha256'] == expected['sha256'], filename
paths = [*output.glob('*'), *root.glob('docs/reviews/Post_P07*.md'),
    root / 'docs/decisions/Post_P07_focused_audit.md', root / 'docs/PROGRESS.md',
    *root.glob('tools/*post_p07*.py'), root / 'src/phi_jepa/coordinate_diagnostics.py',
    root / 'src/phi_jepa/integration/readers.py', root / 'src/phi_jepa/baselines/custom_t5.py',
    root / 'src/phi_jepa/baselines/custom_checkpoint.py',
    root / 'tests/test_post_p07_audit.py', root / 'tests/test_p02a.py']
manifest = {
    'date': '2026-09-25',
    'implementation_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip(),
    'local_origin_tracking_commit': subprocess.check_output(['git', 'rev-parse', 'origin/full-phi-jepa-from-dataset'], cwd=root, text=True).strip(),
    'remote_refreshed': False, 'audit_committed_or_pushed': False,
    'preserved_P07_source_files_verified': len(preserved),
    'empirical_optimizer_updates': 0, 'new_encoder_forwards': 0,
    'new_generations': 0, 'new_provider_calls': 0,
    'native_numerical_diagnostics': '/home/aashraf/phi-jepa/post-p07-audit-02',
    'native_checkpoint_diagnostics': '/home/aashraf/phi-jepa/post-p07-audit-01',
    'files': {str(path.relative_to(root)): identity(path) for path in sorted(set(paths)) if path.is_file()},
}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'preserved_sources_verified': len(preserved), 'new_bundle_files': len(manifest['files']), 'head': manifest['implementation_commit']}))
