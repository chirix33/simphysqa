"""Execute the hash-authorized numerical proposal without modifying its trainer."""
import argparse
import fcntl
import os
import resource
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

import p12_training_plan as planning
from p12_common import NATIVE, ROOT, digest, file_hash, load, save

PROPOSAL_SHA = '13cc4b3cbe8578abe22ebe8faa0987b2de2b3309639bf5e7a9988f4e0542add3'
APPROVED = NATIVE/'p12-approved-training-plan.json'
CONTROL = NATIVE/'p12-training-execution-01'
ORDER = ('driving', 'robotic_arm', 'object_pushing_stacking', 'tethered_load')
AUTHORIZATION = ('User explicitly authorized proposal SHA-256 '+PROPOSAL_SHA+
    ': training only, seed 11, batch 256, ten passes and documented final-batch exposure; '
    'validation-only selection; 14400 seconds total, 3600 per domain, 16000000000 artifact bytes, '
    'zero paid calls. Confirmation evaluation and local baseline generation disabled.')


def authorize():
    if file_hash(planning.PLAN_PATH) != PROPOSAL_SHA:
        raise ValueError('prepared proposal does not match user-authorized SHA-256')
    plan = load(planning.PLAN_PATH)
    planning.check_training_identity(plan)
    plan.update(training_enabled=True, training_authorization=AUTHORIZATION,
                authorized_proposal_sha256=PROPOSAL_SHA)
    planning.require_training_authorization(plan)
    if APPROVED.exists():
        if load(APPROVED) != plan:
            raise ValueError('existing approved copy differs; preserve and reconcile')
    else:
        save(APPROVED, plan)
    return plan


def byte_count(*roots):
    return sum(p.stat().st_size for root in roots if root.exists()
               for p in root.rglob('*') if p.is_file())


def current_progress(plan):
    progress = {}
    for domain in ORDER:
        folder = Path(plan['study_root'])/domain
        attempt = load(folder/'last-update-attempt.json') if (folder/'last-update-attempt.json').exists() else {}
        updates = attempt.get('update', 0) - (attempt.get('status') == 'reserved')
        progress[domain] = {'successful_updates': updates,
            'planned_updates': plan['domains'][domain]['optimizer_updates'],
            'completed_validation_sweeps': len(list((folder/'validation').glob('*.json'))),
            'complete': (folder/'complete.json').exists()}
    return progress


def stop_child(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def child_run(domain):
    plan = load(APPROVED)
    # Only the preflight report destination changes; PLAN_PATH and all inputs stay fixed.
    planning.PLAN_ROOT = CONTROL/'preflights'/domain
    import p12_train
    started = time.time()
    try:
        p12_train.train(plan, domain)
    finally:
        used = resource.getrusage(resource.RUSAGE_SELF)
        save(CONTROL/'resources'/f'{domain}.json', {
            'wall_seconds': time.time()-started, 'user_cpu_seconds': used.ru_utime,
            'system_cpu_seconds': used.ru_stime, 'peak_rss_bytes': used.ru_maxrss*1024})


def execute():
    CONTROL.mkdir(parents=True, exist_ok=True)
    with (CONTROL/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        plan = authorize()
        source = file_hash(__file__)
        window_path = CONTROL/'execution-window.json'
        if not window_path.exists():
            started = time.time()
            save(window_path, {'started_unix': started,
                'deadline_unix': started+plan['training_wall_seconds_cap'],
                'approved_plan_sha256': file_hash(APPROVED), 'launcher_sha256': source,
                'domain_order': list(ORDER), 'authorization': AUTHORIZATION,
                'branch': subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
                'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
            (CONTROL/'initial-git-status.txt').write_text(subprocess.check_output(
                ['git','status','--short'],cwd=ROOT,text=True))
            (CONTROL/'launcher.py').write_bytes(Path(__file__).read_bytes())
            save(CONTROL/'approved-plan.json', plan)
        window = load(window_path)
        if (window['approved_plan_sha256'], window['launcher_sha256']) != (file_hash(APPROVED), source):
            raise ValueError('execution source or approved plan changed')
        if (CONTROL/'completion.json').exists():
            print('Already complete; no optimizer updates.', flush=True)
            return
        if (CONTROL/'failure.json').exists():
            raise ValueError('previous stopped execution requires explicit reconciliation; no automatic retry')
        child = None
        domain = None
        try:
            if time.time() >= window['deadline_unix']:
                raise TimeoutError('total execution window expired; no renewal')
            planning.PLAN_ROOT = CONTROL/'preflights'/'initial'
            report = planning.preflight(plan)
            if not report['can_train'] or report['integrity_failures']:
                raise ValueError('approved preflight failed')
            print({'preflight': 'passed', 'missing': report['missing_identity_verified_contexts'],
                   'integrity_failures': report['integrity_failures']}, flush=True)
            for domain in ORDER:
                folder = Path(plan['study_root'])/domain
                if (folder/'complete.json').exists():
                    if load(folder/'complete.json')['plan_sha256'] != digest(plan):
                        raise ValueError('completed domain plan mismatch')
                    continue
                attempt_path = CONTROL/'attempts'/f'{domain}.json'
                if attempt_path.exists():
                    raise ValueError('unresolved domain dispatch; preserve progress for explicit reconciliation')
                started = time.time()
                deadline = min(window['deadline_unix'], started+plan['domains'][domain]['wall_seconds_cap'])
                if started >= deadline:
                    raise TimeoutError('total execution window expired before domain launch')
                if byte_count(Path(plan['study_root']), CONTROL) >= plan['artifact_bytes_cap']-100000000:
                    raise ValueError('aggregate artifact cap; checkpoint reserve exhausted')
                attempt = {'domain': domain, 'started_unix': started, 'deadline_unix': deadline,
                           'status': 'reserved', 'approved_plan_sha256': file_hash(APPROVED)}
                save(attempt_path, attempt)
                env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                           TOKENIZERS_PARALLELISM='false', PYTHONUNBUFFERED='1')
                with (CONTROL/f'{domain}.log').open('ab') as log:
                    child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                        'child', '--domain', domain], cwd=ROOT, env=env, stdout=log,
                        stderr=subprocess.STDOUT, start_new_session=True)
                    attempt.update(status='running', pid=child.pid)
                    save(attempt_path, attempt)
                    print({'domain': domain, 'pid': child.pid, 'deadline_unix': deadline}, flush=True)
                    last_print = 0
                    while child.poll() is None:
                        if time.time() >= deadline:
                            raise TimeoutError('domain or total wall cap reached: '+domain)
                        size = byte_count(Path(plan['study_root']), CONTROL)
                        if size >= plan['artifact_bytes_cap']-100000000:
                            raise ValueError('aggregate artifact cap; checkpoint reserve exhausted')
                        status = {'active_domain': domain, 'elapsed_seconds': time.time()-window['started_unix'],
                                  'artifact_bytes': size, 'domains': current_progress(plan)}
                        save(CONTROL/'status.json', status)
                        if time.time()-last_print >= 60:
                            print(status, flush=True)
                            last_print = time.time()
                        time.sleep(min(5, max(.01, deadline-time.time())))
                attempt.update(status='complete' if child.returncode == 0 else 'failed',
                               returncode=child.returncode, finished_unix=time.time(),
                               wall_seconds=time.time()-started)
                save(attempt_path, attempt)
                if child.returncode != 0 or not (folder/'complete.json').exists():
                    raise RuntimeError('domain did not complete: '+domain+'; inspect '+str(CONTROL/f'{domain}.log'))
                child = None
            save(CONTROL/'completion.json', {'approved_plan_sha256': file_hash(APPROVED),
                'wall_seconds': time.time()-window['started_unix'], 'finished_unix': time.time(),
                'domains': current_progress(plan), 'paid_calls': 0, 'evaluation_enabled': False,
                'artifact_bytes': byte_count(Path(plan['study_root']), CONTROL)})
            print(load(CONTROL/'completion.json'), flush=True)
        except BaseException as exc:
            if child is not None:
                stop_child(child)
            save(CONTROL/'failure.json', {'type': type(exc).__name__, 'message': str(exc),
                'domain': domain, 'finished_unix': time.time(),
                'wall_seconds': time.time()-window['started_unix'], 'domains': current_progress(plan)})
            traceback.print_exc()
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('run', 'child'))
    parser.add_argument('--domain', choices=ORDER)
    args = parser.parse_args()
    if args.command == 'child':
        child_run(args.domain)
    else:
        execute()
