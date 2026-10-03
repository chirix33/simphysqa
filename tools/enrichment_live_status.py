"""Read live process/lock state without trusting a pre-restart 'running' label."""
from enrichment_run_control import *
import fcntl

def lock_held(path):
    if not path.exists():return False
    with path.open('r') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return True
        fcntl.flock(handle,fcntl.LOCK_UN);return False

def effective_status(saved,process_matches,supervisor_locked):
    if saved=='running' and not (process_matches and supervisor_locked):return 'interrupted_or_stale'
    return saved

def main():
    value=load(RUN/'status.json');supervisor=load(RUN/'supervisor-status.json');pid=supervisor.get('pid')
    try:command=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,ProcessLookupError):command=[]
    matches=str(ROOT/'tools/enrichment_run_control.py').encode() in command and b'worker' in command
    held=lock_held(RUN/'supervisor.lock');deadline=load(RUN/'supervisor-budget.json')['deadline_unix']
    value['live_check']={'checked_at_utc':now(),'supervisor_process_matches':matches,'supervisor_lock_held':held,
        'provider_worker_lock_held':lock_held(RUN/'worker.lock'),
        'effective_status':effective_status(supervisor['status'],matches,held),
        'original_deadline_utc':datetime.fromtimestamp(deadline,timezone.utc).isoformat(),
        'deadline_hours_remaining':max(0,(deadline-time.time())/3600),
        'saved_status_age_seconds':(datetime.now(timezone.utc)-datetime.fromisoformat(value['updated_at_utc'])).total_seconds()}
    atomic_json(EXPORT/'live-status.json',value);print(json.dumps(value,indent=2))

if __name__=='__main__':main()
