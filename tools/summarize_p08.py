"""Final evaluator-only summaries; no model/provider calls or checkpoint selection."""
from collections import Counter,defaultdict
from copy import deepcopy
import math
import shutil
from p08_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.inference.readout import read_targets
from phi_jepa.typed_evaluation import evaluate_targets,physical_error


def score(problem,reference,result,method):
    failure=(result.get('reason') or result.get('status')) if result and result.get('status')!='success' else None
    if result is None: failure='not_attempted_or_not_completed'
    rows=result['answer']['targets'] if result and result.get('answer') else []
    return evaluate_targets(problem,reference,rows,method=method,failure=failure)


def summarize(rows):
    return {'eligible_questions':len(rows),'complete_successes':sum(r['complete_success'] for r in rows),
        'valid_targets':sum(r['valid_targets'] for r in rows),'eligible_targets':sum(r['eligible_targets'] for r in rows),
        'boolean_eligible':sum(r['boolean_eligible'] for r in rows),'boolean_supported':sum(r['boolean_supported'] for r in rows),
        'boolean_correct':sum(r['boolean_correct'] for r in rows)}


def main():
    b=budget(); provenance('final_evaluation'); selected=public_records(); byid={r['sample_id']:r for r in selected}
    refs={**load(RUN/'private/train-references.json'),**load(RUN/'private/validation-references.json')}
    results=[]; gen_diagnostics=[]; custom_learning={}
    with b.operation('final_evaluation_and_export','cpu'):
        for short,method in [('coconut','coconut_inspired_t5_gru'),('codi','codi_inspired_t5_distillation')]:
            for phase in ('diagnostic','broad'):
                folder=RUN/'custom'/method/phase; custom_learning[short+'_'+phase]={'history':load(folder/'history.json') if (folder/'history.json').exists() else [],
                    'eval_losses':load(folder/'eval-losses.json') if (folder/'eval-losses.json').exists() else [],'fit':load(folder/'fit.json') if (folder/'fit.json').exists() else None}
                expected=([ (u,byid[CONFIG['diagnostic_sample']]) for u in CONFIG['diagnostic_milestones']] if phase=='diagnostic' else
                    [(custom_learning[short+'_'+phase]['fit']['updates'] if custom_learning[short+'_'+phase]['fit'] else CONFIG['custom_broad_updates'],r) for r in selected if r['split']=='validation'])
                for update,row in expected:
                    sid=row['sample_id']; p=PublicProblem.parse(row['public']); path=folder/'generations'/f'{update}-{sid}.json'; generation=load(path) if path.exists() else None
                    branches=('coconut',) if short=='coconut' else ('student','teacher','hybrid')
                    for branch in branches:
                        result=(generation.get('hybrid') if branch=='hybrid' else generation['branches'].get(branch)) if generation else None
                        record=score(p,refs[sid],result,short+'_'+branch)
                        record.update(phase=phase,split=row['split'],milestone=update,scenario_id=row['scenario_id'])
                        results.append(record)
                        gen_diagnostics.append({'method':short,'phase':phase,'branch':branch,'sample_id':sid,'split':row['split'],'milestone':update,
                            'attempted':result is not None,'valid_typed_output':result is not None and result['status']=='success',
                            'EOS_terminated':result.get('EOS_terminated') if result else None,'missing_EOS':result.get('missing_EOS') if result else None,
                            'token_cap_termination':result.get('token_cap_termination') if result else None,'reason':result.get('reason') if result else 'not_attempted_or_not_completed',
                            'fallback_attempted':result.get('fallback_attempted',False) if result else False,'fallback_recovered':result.get('fallback_used',False) if result else False,
                            'cost':({'seconds':generation['hybrid_seconds'],'calls':2,'student_generation_reused':True} if branch=='hybrid' else generation['costs'].get(branch)) if generation else None,
                            'correct_targets':sum(t['success'] for t in record['targets']),'eligible_targets':record['eligible_targets'],'complete_success':record['complete_success']})
        answer_records=[]; controls=[]; answer_forecast_differences=[]
        for row in selected:
            if row['split']!='validation': continue
            sid=row['sample_id']; p=PublicProblem.parse(row['public'])
            for method in [*CONFIG['numerical_methods'],'public_only','reversed_forecast']:
                path=RUN/'answers'/method/f'{sid}.json'; value=load(path) if path.exists() else None
                record=score(p,refs[sid],value,method); record.update(scenario_id=row['scenario_id'],split='validation'); answer_records.append(record)
                if value and value['status']=='success':
                    readout={r['target_id']:r for r in value.get('outcomes',[])}
                    specs={r['target_id']:r for r in p.input['answer_spec']}
                    for answer in value['answer']['targets']:
                        original=readout.get(answer['target_id']); spec=specs[answer['target_id']]
                        if original and original['status']==answer['status']=='supported' and spec['answer_type']!='boolean':
                            answer_forecast_differences.append({'method':method,'sample_id':sid,'target_id':answer['target_id'],'unit':spec['unit'],
                                'difference':physical_error(answer['value'],original['value'],spec['quantity'])[0],
                                'meaning':'LLM answer minus supplied readout diagnostic; does not replace original numerical predictions'})
            original=load(RUN/'numerical/phi_jepa/forecasts'/f'{sid}.json')
            if original['status']=='success':
                reversed_payload=deepcopy(original['named'])
                for a,z in zip(reversed_payload['states'],reversed(original['named']['states'])): a['measurements']=deepcopy(z['measurements'])
                reverse=read_targets(p,reversed_payload)
                for spec,a,z in zip(p.input['answer_spec'],original['readout'],reverse):
                    truth=next(t['value'] for t in refs[sid]['structured_label'] if t['target_id']==spec['target_id'])
                    tolerance=spec['absolute_tolerance']+spec['relative_tolerance']*(math.hypot(*truth) if isinstance(truth,list) else abs(truth))
                    delta=physical_error(a['value'],z['value'],spec['quantity'])[0] if a['status']==z['status']=='supported' else None
                    controls.append({'sample_id':sid,'target_id':spec['target_id'],'unit':spec['unit'],'type':spec['answer_type'],'supported':delta is not None,
                        'original':a['value'],'reversed':z['value'],'change':delta,'tolerance':tolerance,'change_over_tolerance':delta/tolerance if delta is not None and tolerance else None,
                        'output_no_op':a['status']==z['status'] and a['value']==z['value']})
        groups=defaultdict(list)
        for r in results: groups[(r['phase'],r['split'],r['method'],r['milestone'] if r['phase']=='diagnostic' else 'final')].append(r)
        custom_summary=[{'phase':k[0],'split':k[1],'method':k[2],'milestone':k[3],**summarize(v)} for k,v in groups.items()]
        answers_summary=[{'method':method,**summarize([r for r in answer_records if r['method']==method])} for method in [*CONFIG['numerical_methods'],'public_only','reversed_forecast']]
        # Common numeric-target comparisons retain failures; Boolean policy separate.
        for summary in answers_summary:
            targets=[t for r in answer_records if r['method']==summary['method'] for t in r['targets'] if t['answer_type']!='boolean']
            summary.update(common_numeric_eligible=len(targets),common_numeric_correct=sum(t['success'] for t in targets))
        save(RUN/'evaluation/custom-answers.json',{'per_question_milestone':results,'summary':custom_summary})
        save(RUN/'evaluation/generation-diagnostics.json',gen_diagnostics)
        save(RUN/'evaluation/provider-answers.json',{'per_question':answer_records,'summary':answers_summary})
        save(RUN/'evaluation/answer-forecast-differences.json',answer_forecast_differences)
        save(RUN/'evaluation/controls.json',{'reversal':controls,'without_fallback':'primary answer/trajectory no-op when no technical fallback active; no new independent output; this does not describe the separately measured CODI hybrid teacher fallback',
            'without_assessment':'removes assessment metadata; partial fixed assessment does not control answer/trajectory','common_numeric_targets':'three named numeric targets per question; preserve all 24 components per condition'})
        labels=Counter(str(t['value']) for r in selected if r['split']=='validation' for t in refs[r['sample_id']]['structured_label'] if type(t['value']) is bool)
        save(RUN/'evaluation/validation-label-distribution.json',{'boolean_labels':dict(labels),'scope':'evaluator-only description of frozen selection; not used to choose data/checkpoints/thresholds','horizons':[r['horizon'] for r in selected if r['split']=='validation']})
        curves={method:load(RUN/'numerical'/method/'history.json') for method in CONFIG['numerical_methods']}
        save(RUN/'evaluation/learning-curves.json',{'numerical':curves,'custom':custom_learning})
        one_step_physical=[]
        for method in CONFIG['numerical_methods']:
            for row in selected:
                if row['split']!='validation': continue
                detail=load(RUN/'evaluation/numerical'/method/f"{row['sample_id']}.json")['one_step']
                if 'coordinates' not in detail:
                    one_step_physical.append({'method':method,'sample_id':row['sample_id'],'status':'failure'}); continue
                channels=defaultdict(list)
                for col in detail['coordinates']:
                    if col['group']=='physical':
                        quantity=next(part for part in col['name'].split('/') if part.startswith('quantity:'))
                        channels[(quantity,col['unit'])].append(col['coordinate_mse'])
                one_step_physical.extend({'method':method,'sample_id':row['sample_id'],'channel':name,'entity_id':name.split(':')[1],'quantity':name.split(':')[2],'unit':unit,
                    'rmse':math.sqrt(sum(values)),'target_precision':'training FP32 targets','mode':'recorded_input_one_step_diagnostic',
                    'meaning':'scalar absolute or vector Euclidean RMSE, derived exactly from component mean squared errors'} for (name,unit),values in channels.items())
        save(RUN/'evaluation/one-step-physical.json',one_step_physical)
        independent=[]
        for short,method in [('coconut','coconut_inspired_t5_gru'),('codi','codi_inspired_t5_distillation')]:
            first=load(RUN/'custom'/method/'diagnostic/initialization.json'); second=load(RUN/'custom'/method/'broad/initialization.json')
            independent.append({'method':short,'same_seeded_initial_values':first['parameter_hashes']==second['parameter_hashes'],
                'separate_fresh_processes_and_initialization':True,'diagnostic_final_not_loaded_by_broad':True})
        save(RUN/'evaluation/initialization-check.json',independent)
    accounting=b.read(); charges=accounting['provider']; accounting['provider_totals']={'attempts':len(charges),
        'input_tokens_charged':sum(r['charged_input'] for r in charges),'output_tokens_charged':sum(r['charged_output'] for r in charges),
        'usd_charged':sum(r['charged_usd'] for r in charges),'unknown_usage_attempts':sum(not r['usage_known'] for r in charges)}
    accounting['native_artifact_bytes']=b.size(); save(RUN/'evaluation/resource-accounting.json',accounting)
    print(json.dumps({'custom':custom_summary,'answers':answers_summary,'resources':accounting['provider_totals'],'seconds':accounting['seconds']}),flush=True)


if __name__=='__main__': main()
