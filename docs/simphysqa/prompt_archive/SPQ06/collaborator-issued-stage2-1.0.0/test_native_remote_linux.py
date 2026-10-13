"""Linux CPU-only failure probes; no actual model/runtime/artifact calls."""
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import native_remote as remote

with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
    base=Path(temp);root=base/'public';root.mkdir()
    job={'issue':{'key':'SYNTHETIC-NOT-MAIN|fixture|enriched|2','process':'FIXTURE-NOT-MAIN',
                  'assignment':{'id':'FIXTURE-ASSIGNMENT'},'remote_executor_sha256':remote.sha(remote.__file__),'bound_seconds':1,
                  'cutoff_utc':'2099-01-01T00:00:00+00:00'},
         'condition':{'settings':{'max_seconds':0}},
         'device_lock_path':str(base/'fixed-host/device.lock'),'attempt_guard_path':str(base/'fixed-host/attempt.json')}
    remote.put(root/'jobs/probe/job.json',job);remote.put(root/'jobs/probe/route.json',{'status':'supported','fixture':True})
    remote.put(root/'manifest.json',{'files':{p.relative_to(root).as_posix():remote.sha(p) for p in root.rglob('*') if p.is_file()}})
    with patch.object(remote,'perform_preflight',side_effect=ValueError('SYNTHETIC failed metadata')),patch.object(remote.subprocess,'Popen') as popen:
        assert remote.run(root,'probe')==2
        assert popen.call_count==0
    receipt=remote.read(root/'runs/probe/process-receipt.json')
    assert receipt['inference_started'] is False and receipt['state']=='failed'
    remote.export(root,'probe',base/'metadata-failure-complete-return.zip')
    other=base/'copy';shutil.copytree(root,other)
    with patch.object(remote,'perform_preflight') as metadata,patch.object(remote.subprocess,'Popen') as popen:
        try:remote.run(other,'probe')
        except FileExistsError:pass
        else:raise AssertionError('copied handoff reopened reserved attempt')
        assert metadata.call_count==popen.call_count==0
    # Separate synthetic issue: hung metadata is cut off, without any answering call.
    slow=base/'slow';slow.mkdir();job['issue']['process']='FIXTURE-SLOW';job['attempt_guard_path']=str(base/'fixed-host/slow.json')
    remote.put(slow/'jobs/probe/job.json',job);remote.put(slow/'jobs/probe/route.json',{'fixture':True})
    remote.put(slow/'manifest.json',{'files':{p.relative_to(slow).as_posix():remote.sha(p) for p in slow.rglob('*') if p.is_file()}})
    with patch.object(remote,'perform_preflight',side_effect=lambda *args:time.sleep(5)),patch.object(remote.subprocess,'Popen') as popen:
        assert remote.run(slow,'probe')==2
        assert popen.call_count==0
    assert remote.read(slow/'runs/probe/process-receipt.json')['state']=='timed_out'
print('3 Linux CPU-only metadata/attempt/deadline probes passed; answering calls=0')
