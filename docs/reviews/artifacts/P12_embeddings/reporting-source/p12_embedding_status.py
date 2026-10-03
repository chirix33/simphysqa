"""Read-only embedding status, including a live lock check after WSL restarts."""
from p12_common import load
from p12_embeddings import RUN
from collections import Counter
import json


def main():
    import fcntl
    active = False
    path = RUN/'worker.lock'
    if path.exists():
        with path.open('r') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(handle, fcntl.LOCK_UN)
            except BlockingIOError:
                active = True
    records = [load(p) for p in (RUN/'attempts').glob('*.json')]
    counts = Counter(r['status'] for r in records)
    cfg = load(RUN/'config.json')
    saved = load(RUN/'status.json') if (RUN/'status.json').exists() else {}
    report = {'worker_lock_held': active, 'saved_status': saved.get('status'),
              'new_vectors_saved': counts['success'], 'attempt_statuses': dict(counts),
              'reused_vectors': sum(cfg['reuse_counts'].values()),
              'new_vectors_by_scope_domain': dict(Counter(r['scope']+'/'+r['domain'] for r in records if r['status'] == 'success')),
              'known_encoding_seconds': sum(r['seconds'] for r in records if r['status'] == 'success'),
              'reserved_or_failed_seconds': sum(r['seconds'] for r in records if r['status'] != 'success'),
              'stale_running_label': not active and saved.get('status') in ('running', 'waiting_for_gpu'),
              'completion_record_present': (RUN/'completion.json').exists(),
              'final_audit_present': (RUN/'audit.json').exists(), 'status_check_model_calls': 0, 'status_check_paid_calls': 0}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
