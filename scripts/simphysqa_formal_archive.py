"""SPQ05 provenance supplement; prior sealed archive is inherited read-only."""
import argparse
from hashlib import sha256
from pathlib import Path
import subprocess

from simphysqa.formal_sampling import save_bytes, file_hash
from simphysqa.io import ROOT, canonical, digest, external, read
from simphysqa.spq01a import retained, verify_manifest


def build(previous, preparation, check, output):
    output = external(output)
    prior = verify_manifest(previous)
    prep = verify_manifest(preparation)
    saved = verify_manifest(check)
    producer = (read(output/'file-generation-index.json')['producer_commit']
                if (output/'file-generation-index.json').exists() else
                subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip())
    mappings = []
    for alias, root, manifest in (('preparation', preparation, prep), ('development_extraction_check', check, saved)):
        for name, value in manifest['files'].items():
            if name.startswith('organizer-private/prepared-requests/'):
                mode = 'prepared_annotation_request_unexecuted'
            elif name.startswith('auditor-only/'):
                mode = 'reused_exact_saved_development_packet'
            elif name.startswith('forms/') or name.startswith('form-templates/'):
                mode = 'deterministic_blank_forms_uncollected'
            else:
                mode = 'deterministic_offline_procedure'
            mappings.append({'path': str((root/name).resolve()), 'sha256': value,
                'mode': mode, 'source_scope': alias,
                'producer_files': ['src/simphysqa/formal_sampling.py'] if alias == 'preparation'
                     else ['src/simphysqa/focused_audit.py'],
                'executed_provider_request': False, 'formal_audit_item': False})
    for relative in ('docs/prompts/SPQ05_formal_audit.md', 'docs/simphysqa/formal_protocol.md',
                     'docs/simphysqa/formal_reviewer_guide.md', 'docs/simphysqa/formal_analysis.md',
                     'configs/simphysqa/formal_audit.json', 'src/simphysqa/formal_sampling.py',
                     'src/simphysqa/focused_audit.py', 'scripts/simphysqa_formal_archive.py'):
        path = ROOT/relative
        save_bytes(output/'procedures'/path.name, path.read_bytes())
    lineage = {'version': 'simphysqa-SPQ05-provenance-supplement/1.0.0',
        'producer_commit': producer,
        'inherits': {'path': str(previous.resolve()), 'manifest_sha256': file_hash(previous/'manifest.json'),
                     'index_sha256': file_hash(previous/'file-generation-index.json'),
                     'historical_executed_requests': 16,
                     'policy': 'sealed prior archive unchanged; prior executed/reuse mappings remain authoritative'},
        'new_executed_annotation_requests': 0, 'prepared_annotation_requests': 280,
        'new_simulations': 0, 'new_answering_requests': 0, 'human_ratings': 0,
        'per_file_generation_index': mappings,
        'reuse_note': 'Development packet measurement prose retains original executed-request lineage through inherited1.0.7 mappings. These excluded groups are never formal items.'}
    retained(output/'file-generation-index.json', lineage)
    save_bytes(output/'README.md', (
        '# SPQ05 provenance supplement /1.0.0\n\n'
        'Inherits the sealed SPQ04 archive1.0.7 without modification. Per-file hashes classify '
        '280 unexecuted annotation payloads, offline procedures, reused excluded development packets '
        'and blank forms. New executed annotation requests/simulations/answering requests/ratings:0.\n\n'
        'No final140 packet set exists. Private packet evidence remains outside this supplement. '
        'Hashes/paths are organizer provenance, not public answering inputs.\n').encode())
    files = {p.relative_to(output).as_posix(): file_hash(p) for p in sorted(output.rglob('*'))
             if p.is_file() and p.name != 'manifest.json'}
    retained(output/'manifest.json', {'version': lineage['version'], 'files': files,
                                    'index_sha256': digest(lineage), 'inherited_manifest_sha256': file_hash(previous/'manifest.json')})
    return {'indexed_new_files': len(mappings), 'executed_new_requests': 0,
            'inherited_sealed_files': len(prior['files'])}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ('previous','preparation','check','output'):
        p.add_argument('--'+key, type=Path, required=True)
    a=p.parse_args()
    print(canonical(build(a.previous,a.preparation,a.check,a.output)).decode(), end='')
