"""Append the approved audit evidence to a new immutable pilot bundle."""
import argparse,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical,write_run,read_run,code_provenance
from export_p07_pilot import publish
p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[1]; evidence=root/'docs/reviews/artifacts/P07'; payloads,original=read_run(args.source)
audit=json.loads((evidence/'output-and-split-audit.json').read_text())
if audit['status']!='passed' or audit['whole_scenario_exclusion']['overlapping_training_questions']: raise ValueError('audit_gate')
test_text=(evidence/'tests-final.log').read_text()
if 'Ran 119 tests' not in test_text or not test_text.rstrip().endswith('OK'): raise ValueError('tests_gate')
payloads['output-and-split-audit.json']=audit
payloads['final-test-evidence.json']={'command':"CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -m unittest discover -s tests -p 'test_p*.py' -v",'log':test_text,'sha256':hashlib.sha256(test_text.encode()).hexdigest()}
payloads['control-interpretation.json']={
    'without_fixed_assessment':{'prediction_changed':False,'answer_changed':False,'diagnostic_computation_changed':True,'distinct_effective_accuracy_ablation':False},
    'without_fallback':{'prediction_changed':False,'answer_changed':False,'no_op':True,'distinct_effective_accuracy_ablation':False},
    'independent_observations_added':0}
payloads['scope-approval.json']={'status':'explicitly_approved_by_user','scope':'existing bounded tether pilot, seed 11, 20-transition selection, existing held-out question/checkpoints; correctness and resources only','full_study_authorized':False,'new_training_or_generation':False,'prior_export_reporting_recovery':True,'prior_export_sha256':args.source.name,'requirements':'whole-scenario exclusion; target/EOS/masking/stopping/parser audit; all failures retained; separate fallback attempts/recoveries; teacher costs; no convergence/rankings; proposed broader budget only'}
payloads['next-budget-proposal.json']={'status':'proposed_not_launched','markdown':(root/'docs/reviews/P07_next_budget_proposal.md').read_text()}
payloads['final-source-inventory.json']={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for pattern in ('src/phi_jepa/baselines/*.py','tools/*p06*','tools/*p07*','configs/*p06*','configs/*p07*','tests/test_p06.py') for path in root.glob(pattern) if path.is_file()}
run=write_run(args.output,payloads,{'stage':'P07_final','source':code_provenance(),'prior_export':str(args.source),'bounded_pilot_complete':True,'full_study_pending':True})
publish(root,run,payloads,elapsed=None,recovered=True)
print(json.dumps({'final_export':str(run),'payloads':len(payloads),'bounded_pilot_complete':True,'full_study_pending':True}))
