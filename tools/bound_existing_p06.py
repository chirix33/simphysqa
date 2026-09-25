"""Attach a hard cap to an already-running P06 process via a Linux pidfd."""
import argparse,json,os,select,signal,time
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--pid',type=int,required=True); p.add_argument('--report',type=Path,required=True); p.add_argument('--cap-seconds',type=int,default=900); args=p.parse_args()
proc=Path('/proc')/str(args.pid); command=(proc/'cmdline').read_bytes().split(b'\0')
if not any(x.endswith(b'/python') for x in command[:1]) or b'tools/run_p06_custom.py' not in command or b'qualify' not in command: raise ValueError('not_owned_p06_qualification')
fd=os.pidfd_open(args.pid); ticks=int((proc/'stat').read_text().split()[21]); uptime=float(Path('/proc/uptime').read_text().split()[0]); elapsed=uptime-ticks/os.sysconf('SC_CLK_TCK')
remaining=max(0,args.cap_seconds-elapsed)
if not select.select([fd],[],[],remaining)[0]:
    signal.pidfd_send_signal(fd,signal.SIGTERM)
    if not select.select([fd],[],[],10)[0]: signal.pidfd_send_signal(fd,signal.SIGKILL)
    value=json.loads(args.report.read_text()); value.update(status='failed',failure_type='WallClockBudgetExceeded',reason='hard_subprocess_qualification_cap',seconds=max(elapsed,args.cap_seconds),peak_allocated_bytes=None,peak_reserved_bytes=None)
    args.report.write_text(json.dumps(value,sort_keys=True)); print('P06 qualification time cap enforced')
else: print('P06 qualification exited within cap')
os.close(fd)
