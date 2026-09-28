"""Post-generation evaluator-only paired diagnostic. Never imported by inference."""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.readers import ReleaseCatalog, EvaluatorTruthReader


def score(problem, reference, rows):
    expected=problem.input['answer_spec']
    gold={r['target_id']:r for r in reference['structured_label']}
    actual={r['target_id']:r for r in rows}
    details=[]
    for spec in expected:
        ident=spec['target_id']; row=actual.get(ident)
        result={'target_id':ident,'answer_type':spec['answer_type'],'unit':spec['unit'],
            'status':row['status'] if row else 'generation_failure','error':None,'success':False}
        if row and row['status']=='supported':
            value,truth=row['value'],gold[ident]['value']
            if spec['answer_type']=='boolean': error=0. if value is truth else 1.
            elif isinstance(truth,list):
                if spec['quantity']=='orientation':
                    norm=lambda x:math.sqrt(sum(v*v for v in x))
                    a,b=norm(value),norm(truth)
                    error=None if a==0 or b==0 else 2*math.acos(min(1.,abs(sum(x*y for x,y in zip(value,truth))/(a*b))))
                    result['error_unit']='rad_rotation'
                else: error=math.sqrt(sum((a-b)**2 for a,b in zip(value,truth)))
            else: error=abs(value-truth)
            result['error']=error
            result['success']=error is not None and error<=spec['absolute_tolerance']
        details.append(result)
    boolean=[r for r in details if r['answer_type']=='boolean']
    supported=[r for r in boolean if r['status']=='supported']
    return {'targets':details,'eligible_questions':1,'eligible_targets':len(details),
        'supported_targets':sum(r['status']=='supported' for r in details),
        'boolean_eligible':len(boolean),'boolean_supported':len(supported),
        'boolean_coverage':len(supported)/len(boolean) if boolean else None,
        'boolean_accuracy_supported':sum(r['success'] for r in supported)/len(supported) if supported else None,
        'complete_answer_success_all_eligible':int(all(r['success'] for r in details))}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    identity=json.loads((args.run/'identity.json').read_text())
    answers=json.loads((args.run/'results.json').read_text())
    release=json.loads((root/'configs/model_training_p02a.json').read_text())
    catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
    problem,reference,group=next(r for r in EvaluatorTruthReader(catalog,'tethered_load','validation') if r[0].sample_id==identity['sample_id'])
    if digest(problem.input)!=identity['public_sha256']: raise ValueError('public identity mismatch')
    results={k:score(problem,reference,v['answer']['targets'] if v['status']=='success' else []) for k,v in answers.items()}
    results['raw_numeric_and_rule_readout']=score(problem,reference,json.loads((args.run/'numeric-readout.json').read_text()))
    report={'scope':'one validation question/scenario; no model selection or final tests',
        'source_answers_sha256':digest(answers),'split_group_id':group.group_id,'conditions':results}
    (args.run/'paired-metrics.json').write_bytes(canonical(report))
    print(json.dumps(report))


if __name__=='__main__': main()
