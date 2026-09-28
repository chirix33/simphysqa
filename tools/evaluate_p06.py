"""Evaluator-only baseline answers: references never reach generation."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import ReleaseCatalog
from phi_jepa.typed_evaluation import evaluate_targets

p=argparse.ArgumentParser(); p.add_argument('--run',type=Path,required=True); p.add_argument('--profile',type=Path,required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[1]; c=json.loads((root/'configs/custom_p06.json').read_text()); release=json.loads((root/'configs/model_training_p02a.json').read_text())
for method in c['methods']:
    report=args.run/method/'infer-report.json'
    if not report.exists() or json.loads(report.read_text()).get('status')=='started': raise ValueError('generation_attempt_not_finished')
catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
public={r['public']['sample_id']:r for r in json.loads((args.profile/'public-prepared.json').read_text()) if r['public']['input']['domain']=='tethered_load'}
metrics=[]
for method in c['methods']:
    directory=args.run/method; generations=json.loads((directory/'generations.json').read_text()) if (directory/'generations.json').exists() else []
    results={r['sample_id']:r for r in generations}
    for sid,row in public.items():
        problem=PublicProblem.parse(row['public']); _,reference,identity=next(r for r in catalog.records('tethered_load',row['split']) if r[0].sample_id==sid)
        found=results.get(sid)
        names={'coconut':'coconut_explanation_and_label'} if method.startswith('coconut') else {'student':'codi_student_only_primary','hybrid':'codi_teacher_explanation_student_label_hybrid'}
        for branch,name in names.items():
            result=(found.get('hybrid') if branch=='hybrid' else found['branches'].get(branch)) if found else None
            failure=result.get('reason') or result['status'] if result and result['status']!='success' else ('generation_not_run' if not result else None)
            evaluated=evaluate_targets(problem,reference,result['answer']['targets'] if result and result.get('answer') else [],method=name,failure=failure)
            evaluated.update(split=row['split'],scenario_id=identity.group_id,scope='bounded correctness, not benchmark',forecast_metrics=None,
                fallback_used=result.get('fallback_used',False) if result else False,fallback_attempted=result.get('fallback_attempted',False) if result else False)
            metrics.append(evaluated)
summary=[]
for split in ('train','validation'):
    for method in c['inference_conditions']:
        rows=[r for r in metrics if r['split']==split and r['method']==method]
        summary.append({'split':split,'method':method,'eligible_questions':len(rows),'complete_successes':sum(r['complete_success'] for r in rows),'valid_targets':sum(r['valid_targets'] for r in rows),'eligible_targets':sum(r['eligible_targets'] for r in rows),'fallback_count':sum(r['fallback_used'] for r in rows),'fallback_attempts':sum(r['fallback_attempted'] for r in rows)})
(args.run/'evaluation.json').write_bytes(canonical({'per_question':metrics,'summary':summary})); print(json.dumps(summary))
