"""Final bounded verification: unit tests, original export hashes, new provenance."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from phi_jepa.integration.readers import file_hash


def main():
    out=ROOT/'docs/reviews/artifacts/P09_clarification'
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')+os.pathsep+str(ROOT/'tests'),'CUDA_VISIBLE_DEVICES':'','HF_HUB_OFFLINE':'1'}
    modules=['test_post_p08_diagnosis','test_clarification','test_p04a','test_p04b']
    command=[sys.executable,'-m','unittest',*modules,'-v']; start=time.perf_counter()
    result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
    (out/'targeted_tests.txt').write_text(result.stdout+result.stderr)
    if result.returncode: raise RuntimeError('targeted_tests_failed_see_log')
    original=ROOT/'docs/reviews/artifacts/P08'; manifest=json.loads((original/'manifest.json').read_text()); verified=0
    for name,info in manifest['files'].items():
        sha=info['sha256'] if isinstance(info,dict) else info
        assert file_hash(original/name)==sha, name
        verified+=1
    diag=json.loads((ROOT/'docs/reviews/artifacts/Post_P08_diagnosis/manifest.json').read_text())
    for path,sha in diag['sources'].items(): assert file_hash(Path(path))==sha,path
    reviewed=out/'review-v2'; traces=json.loads((reviewed/'manifest.json').read_text())
    for name,sha in traces['files'].items(): assert file_hash(reviewed/name)==sha,name
    paths=[ROOT/'src/phi_jepa/inference/clarification.py',ROOT/'src/phi_jepa/providers/clarification.py',ROOT/'src/phi_jepa/clarification_evaluation.py',
        ROOT/'docs/assets/clarification_v1.json',*[ROOT/'tools'/name for name in ('clarification_reply.py','diagnose_post_p08.py','report_post_p08_diagnosis.py','review_clarification_fixtures.py','verify_post_p08_p09.py')],
        ROOT/'tests/test_clarification.py',ROOT/'tests/test_post_p08_diagnosis.py']
    subprocess.run([sys.executable,'-m','py_compile',*[str(p) for p in paths if p.suffix=='.py']],check=True,env=env)
    value={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        'command':command,'exit_code':result.returncode,'seconds':time.perf_counter()-start,
        'original_P08_export_files_verified':verified,'diagnosis_source_files_reverified':len(diag['sources']),
        'mock_trace_files_verified':len(traces['files']), 'source_files':{str(p.relative_to(ROOT)):file_hash(p) for p in paths},
        'tests_log_sha256':file_hash(out/'targeted_tests.txt'),'training_updates':0,'paid_calls':0,'new_model_generations':0,
        'original_reports_and_checkpoints_preserved':True,'compile_check':'passed'}
    (out/'final_verification.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k not in ('source_files','command')}))


if __name__=='__main__': main()
