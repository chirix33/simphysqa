"""Evaluator-only baseline forecast/answer metrics; all failures retained."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import ReleaseCatalog,EvaluatorTruthReader
from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors,grouped_summary
from phi_jepa.assessment.checks import physical_checks

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); parser.add_argument('--primary-answer-run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; config=json.loads((args.run/'summary.json').read_text())['config']; checks_config=json.loads((root/'configs/assessment_p04b.json').read_text())['physical_checks']
p=PublicProblem.parse(json.loads((args.run/'validation-public.json').read_text()))
release=json.loads((root/'configs/model_training_p02a.json').read_text()); catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
verified,reference,identity=next(r for r in EvaluatorTruthReader(catalog,p.input['domain'],'validation') if r[0].sample_id==p.sample_id)
if verified!=p: raise ValueError('evaluation_public_identity')
summary=json.loads((args.run/'summary.json').read_text())
if summary['provenance']['training_scenario']==identity.group_id: raise ValueError('train_validation_scenario_overlap')
results={}
for method in config['methods']:
    forecast=json.loads((args.run/method/'named-forecast.json').read_text()); readout=json.loads((args.run/method/'readout.json').read_text())
    answer=json.loads((args.run/method/'answer.json').read_text())
    numeric=evaluate_targets(p,reference,readout,method=method)
    generated=evaluate_targets(p,reference,answer['answer']['targets'] if answer['status']=='success' else [],method=method+'_final_answer',failure=answer.get('reason'))
    for row in (numeric,generated): row.update(scenario_id=identity.group_id,domain=identity.domain,distribution='id')
    trajectory=trajectory_errors(forecast['states'],reference['states'],mode='autonomous')
    checks=physical_checks(p,forecast,checks_config)
    results[method]={'numeric_and_rule_targets':numeric,'final_answer_targets':generated,
        'numeric_summary':grouped_summary([numeric]),'answer_summary':grouped_summary([generated]),
        'autonomous_physical_metrics':trajectory['metrics'],'physical_checks':{k:v for k,v in checks.items() if k!='checks'}}
    (args.run/method/'per-time-errors.json').write_bytes(canonical(trajectory))
direct=json.loads((args.primary_answer_run/'public_only.json').read_text())
direct_report=evaluate_targets(p,reference,direct['answer']['targets'] if direct['status']=='success' else [],method='direct_frozen_llm_public_only')
results['direct_frozen_llm_public_only']={'targets':direct_report,'source':'exact existing P04a public-only validation answer; no new call or training',
    'limitation':'Boolean outputs constrained to unsupported by the approved readout policy; not an unrestricted Boolean solver comparison'}
(args.run/'evaluation.json').write_bytes(canonical(results))
print(json.dumps({m:{'numeric_complete':r['numeric_and_rule_targets']['complete_success'],'answer_complete':r['final_answer_targets']['complete_success'],
    'numeric_errors':{t['target_id']:t['error'] for t in r['numeric_and_rule_targets']['targets']}} for m,r in results.items() if 'numeric_and_rule_targets' in r}))
