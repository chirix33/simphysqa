"""Locate original completed jobs; emit pinned export commands or export only.

Never constructs tickets, qualifications, requests, runtime or process evidence.
Never invokes an answering worker or changes any ledger.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time
import zipfile


def read(p):
    return json.loads(Path(p).read_bytes())


def sha(p):
    digest = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def put(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(v, f, indent=2)
        f.write('\n')


def discover(roots):
    tickets, packages, visited, count = set(), set(), set(), 0
    excluded = {'.git', '.cache', '.venv', '.venvs', 'node_modules', '__pycache__', 'models', 'weights', 'blobs', 'snapshots'}
    for root in roots:
        root = Path(root).expanduser().resolve(strict=True)
        for directory, dirs, names in os.walk(root, followlinks=False):
            directory = Path(directory).resolve()
            if directory in visited:
                dirs[:] = []
                continue
            visited.add(directory)
            count += 1
            if count > 100000:
                raise ValueError('bounded search exhausted; pass the specific completed-job/package roots')
            dirs[:] = [d for d in dirs if d not in excluded and not (directory / d).is_symlink()]
            if 'ticket.json' in names:
                tickets.add(directory)
                dirs[:] = []
            if 'package-manifest.json' in names and (directory / 'procedures/public_executor.py').is_file():
                packages.add(directory)
                dirs[:] = []
    return sorted(tickets), sorted(packages)


def check_job(job, expected):
    required = ['ticket.json', 'assignment.json', 'qualification.json', 'bindings.json', 'condition.json',
                'execution-context.json', 'launch.json', 'pre-reservation-preflight.json', 'process-receipt.json',
                'worker-output/runtime.json']
    ticket = read(job / 'ticket.json')
    process = ticket.get('id')
    wanted = {r['key']: r for r in expected['results'] if r['process_reservation'] == process}
    if not wanted:
        return None
    missing = [n for n in required if not (job / n).is_file()]
    if set(ticket.get('keys', [])) != set(wanted):
        missing.append('ticket key coverage differs from the supplied original raw results')
    for key, row in wanted.items():
        stem = key.split('|')[0] + '-stage1.json'
        for folder in ('results', 'executed-requests', 'tokenized-prompts'):
            p = job / 'worker-output' / folder / stem
            if not p.is_file():
                missing.append(p.relative_to(job).as_posix())
        result = job / 'worker-output/results' / stem
        if result.is_file() and sha(result) != row['result_file_sha256']:
            missing.append('original raw bytes differ: ' + stem)
    if (job / 'condition.json').is_file() and read(job / 'condition.json').get('backend') == 'llama.cpp':
        missing.extend(n for n in ('worker-output/server-launch.json', 'worker-output/cuda-device-preflight.json') if not (job / n).is_file())
    return {'process_reservation': process, 'job': str(job), 'keys': sorted(wanted), 'missing': missing}


def inventory(a):
    expected = read(a.expected)
    jobs, packages = discover(a.search_root)
    package_by_hash = {}
    for p in packages:
        package_by_hash.setdefault(sha(p / 'package-manifest.json'), []).append(p)
    result = []
    for job in jobs:
        row = check_job(job, expected)
        if row is None:
            continue
        if not row['missing']:
            bindings, launch = read(job / 'bindings.json'), read(job / 'launch.json')
            candidates = package_by_hash.get(launch.get('package_sha256'), [])
            if not candidates:
                row['missing'].append('original package matching launch.package_sha256')
            else:
                package = candidates[0]
                row['package'] = str(package)
                row['package_sha256'] = launch['package_sha256']
                row['interpreter'] = bindings.get('interpreter')
                if not row['interpreter'] or not Path(row['interpreter']).is_file():
                    row['missing'].append('original pinned bindings.interpreter unavailable')
        if not row['missing']:
            row['export_command'] = shlex.join([row['interpreter'], str(Path(row['package']) / 'procedures/public_executor.py'),
                                               'return', '--job', row['job'], '--output', str(Path(a.export_root).resolve() / row['process_reservation'])])
        result.append(row)
    required_processes = {r['process_reservation'] for r in expected['results']}
    found = {r['process_reservation'] for r in result}
    duplicate = sorted(p for p in found if sum(r['process_reservation'] == p for r in result) > 1)
    report = {'version': 'SPQ06-original-return-recovery/1.0.0', 'jobs': result,
              'missing_processes': sorted(required_processes - found), 'duplicate_job_locations': duplicate,
              'expected_index_sha256': sha(a.expected), 'export_root': str(Path(a.export_root).resolve()),
              'answering_calls': 0, 'status': 'ready_to_export' if not (required_processes - found or duplicate or any(r['missing'] for r in result)) else 'missing_original_evidence'}
    put(a.output, report)
    for row in result:
        if row.get('export_command'):
            print(row['export_command'])
    print(json.dumps({k: report[k] for k in ('status', 'missing_processes', 'duplicate_job_locations')}))


def export(a):
    expected, inv = read(a.expected), read(a.inventory)
    if inv['expected_index_sha256'] != sha(a.expected) or inv['status'] != 'ready_to_export':
        raise ValueError('complete unique original job inventory required; no missing provenance will be manufactured')
    export_root = Path(inv['export_root'])
    export_root.mkdir(parents=True, exist_ok=False)
    logs = []
    for row in inv['jobs']:
        job, package = Path(row['job']), Path(row['package'])
        current = check_job(job, expected)
        if current is None or current['missing']:
            raise ValueError('original job changed/incomplete: ' + str(job))
        if sha(package / 'package-manifest.json') != row['package_sha256']:
            raise ValueError('original package identity changed')
        manifest = read(package / 'package-manifest.json')
        for name, h in manifest['files'].items():
            p = (package / name).resolve()
            if package.resolve() not in p.parents or sha(p) != h:
                raise ValueError('original sealed package changed: ' + name)
        bindings = read(job / 'bindings.json')
        if bindings['interpreter'] != row['interpreter']:
            raise ValueError('pinned interpreter changed')
        # These filenames are never expected job evidence; do not export secrets/private data.
        prohibited = [p for p in job.rglob('*') if p.is_file() and (p.name.lower() in ('.env', 'openai_key.txt', 'credentials.json')
                      or p.suffix.lower() in ('.sqlite', '.pem', '.key') or any(v in p.parts for v in ('organizer-private', 'private')))]
        if prohibited:
            raise ValueError('nonpublic files in job; report for scoped export before sharing')
        argv = [bindings['interpreter'], str(package / 'procedures/public_executor.py'), 'return', '--job', str(job),
                '--output', str(export_root / row['process_reservation'])]
        started = time.monotonic()
        proc = subprocess.run(argv, env={**os.environ, **bindings.get('environment', {}), 'PYTHONDONTWRITEBYTECODE': '1'},
                              capture_output=True, text=True, timeout=300)
        logs.append({'argv': argv, 'returncode': proc.returncode, 'export_elapsed_seconds': time.monotonic() - started})
        if proc.returncode:
            put(export_root / 'export-failure.json', logs)
            raise ValueError('original exporter failed; preserve partial export, never rerun inference')
    put(export_root / 'export-commands.json', logs)
    zip_path = export_root.with_suffix('.zip')
    with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(export_root.rglob('*')):
            if p.is_file():
                archive.write(p, p.relative_to(export_root).as_posix())
    print(json.dumps({'return_zip': str(zip_path), 'sha256': sha(zip_path), 'jobs': len(logs), 'answering_calls': 0}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    i = sub.add_parser('inventory')
    i.add_argument('--search-root', action='append', required=True)
    i.add_argument('--expected', required=True)
    i.add_argument('--output', required=True)
    i.add_argument('--export-root', required=True)
    e = sub.add_parser('export')
    e.add_argument('--expected', required=True)
    e.add_argument('--inventory', required=True)
    a = p.parse_args()
    inventory(a) if a.command == 'inventory' else export(a)
