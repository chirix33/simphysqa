"""Verify disabled-launch behavior and seal preparation evidence; no training."""
from p12_training_plan import *


def main():
    plan = load(PLAN_PATH);check_training_identity(plan)
    if plan['enabled'] or plan['training_enabled'] or plan['evaluation_enabled']:
        raise ValueError('preparation verification requires disabled proposal')
    root = Path(plan['study_root'])
    if root.exists():raise ValueError('study directory already exists; inspect without changing it')
    result = subprocess.run([sys.executable,str(ROOT/'tools/p12_train.py'),'train','--approved-plan',str(PLAN_PATH),'--domain','driving'],
                            cwd=ROOT,capture_output=True,text=True,timeout=30)
    if result.returncode == 0 or 'numerical-training authorization required' not in result.stderr:
        raise ValueError('disabled launch did not fail at authorization gate')
    if root.exists():raise ValueError('disabled launch created study artifacts')
    (PLAN_ROOT/'disabled-launch.log').write_text(result.stdout+result.stderr)
    old = plan['historical_proposal']
    if file_hash(old['path']) != old['sha256']:raise ValueError('historical proposal changed')
    preflight_report = load(PLAN_ROOT/'training-preflight.json')
    if not preflight_report['data_ready'] or preflight_report['can_train']:raise ValueError('unexpected readiness flags')
    report = {'prepared_plan_sha256':file_hash(PLAN_PATH),'training_implementation_sha256':plan['training_implementation_sha256'],
              'historical_proposal_sha256':old['sha256'],'historical_proposal_unchanged':True,
              'disabled_launch_rejected':True,'study_directory_exists':False,'training_started':False,
              'executed_optimizer_updates':0,'executed_training_pair_presentations':0,'paid_calls':0,
              'proposed_totals':{k:sum(d[k] for d in plan['domains'].values()) for k in
                                 ('scenarios','questions','pairs_per_pass','optimizer_updates','actual_pair_exposure','validation_questions')},
              'preflight_sha256':file_hash(PLAN_ROOT/'training-preflight.json')}
    save(PLAN_ROOT/'readiness-verification.json',report)
    export()
    helper=EXPORT/'reporting-source';helper.mkdir(exist_ok=True)
    for path in (Path(__file__), ROOT/'tests/test_p12_training_plan.py'):
        shutil.copyfile(path,helper/path.name)
    export()
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
