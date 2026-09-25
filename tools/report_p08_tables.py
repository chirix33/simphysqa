"""Readable saved-result tables; no fitting, inference, thresholding or paid calls."""
from collections import defaultdict,Counter
import math
from p08_common import *

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',*['| '+' | '.join(str(x) for x in row)+' |' for row in rows]])
def f(value): return '—' if value is None else f'{value:.7g}'
def pooled(values): return math.sqrt(sum(v*v for v in values)/len(values)) if values else None

def main():
    b=budget(); provenance('result_tables')
    with b.operation('saved_result_tables','cpu'):
        out=RUN/'evaluation'; rows=load(out/'numerical-summary.json'); aggregate={m:load(out/'numerical'/m/'aggregate.json') for m in CONFIG['numerical_methods']}
        text=['# P08 coordinate and named physical errors','All eight frozen validation questions remain in the denominator. Each successful rollout has 40 forecast samples on the external 0.22–1.00 s grid. Raw numerical MSE mixes units; it is not a physical accuracy score. No coordinates are reset or rescaled. One-step diagnostics consume recorded current states, while autonomous forecasts consume only their initial permitted observation and then predictions.','## Raw numerical and coordinate-group MSE',
            table(['Method','Mode','Raw numerical MSE','Fixed contribution (127)','Physical contribution (11)','Time/index contribution (2)'],[
                [method,mode,f(v.get('raw_numerical_mse')),*[f(v.get('groups',{}).get(g,{}).get('raw_numerical_mse_contribution')) for g in ('fixed_conditioning','physical','time_index')]]
                for method,data in aggregate.items() for mode,v in data.items() if mode in ('one_step','autonomous')]),
            'Contributions sum to raw MSE and each divides by d=140. Full per-coordinate units, target/prediction ranges, squared errors and contribution fractions are in `numerical/<method>/aggregate.json`; each question has a separate JSON alongside it.',
            '## Largest primary coordinate contributions',table(['Mode','Coordinate','Unit','Target range','Prediction range','Contribution','Fraction'],[
                [mode,r['name'],r['unit'],str(r['target_range']),str(r['prediction_range']),f(r['raw_numerical_mse_contribution']),f(r['fraction_of_raw_mse'])]
                for mode in ('one_step','autonomous') for r in sorted(aggregate['phi_jepa'][mode]['coordinates'],key=lambda x:x['raw_numerical_mse_contribution'],reverse=True)[:8]])]
        physical=[]; endpoints=[]
        for method in [*CONFIG['numerical_methods'],'hold_last_diagnostic']:
            metrics=defaultdict(list); errors=defaultdict(list)
            for row in [r for r in rows if r['method']=='phi_jepa']:
                record=load(out/'hold-last'/f"{row['sample_id']}.json") if method=='hold_last_diagnostic' else load(out/'numerical'/method/f"{row['sample_id']}.json")
                for metric in record['physical']['metrics']:
                    if metric['valid']==metric['eligible']: metrics[(metric['entity_id'],metric['quantity'],metric['unit'])].append(metric['rmse_valid_only'])
                targets=record.get('answer_readout',record.get('targets'))['targets']
                for target in targets:
                    if target['answer_type']!='boolean' and target['status']=='valid': errors[(target['target_id'],target['unit'])].append(target['error'])
            physical.extend([method,entity,quantity,unit,len(values),f(pooled(values))] for (entity,quantity,unit),values in metrics.items())
            endpoints.extend([method,target,unit,len(values),f(sum(values)/len(values)),f(max(values))] for (target,unit),values in errors.items())
        text+=['## Autonomous physical trajectory errors',
            'Pooled RMSE over the same 8×40 samples. Vector errors are Euclidean norms in native units. Valid-question counts are shown explicitly; failures are not converted to zero. Hold-last is an evaluation diagnostic, not a new trained/paper baseline.',
            table(['Method','Entity','Quantity','Unit','Valid / 8','Pooled RMSE'],physical),
            '## Queried endpoint errors','Mean and maximum absolute/Euclidean errors at T=1 s, with unchanged answer tolerances.',
            table(['Method','Target','Unit','Valid / 8','Mean error','Maximum error'],endpoints),
            '## Named one-step physical errors','Derived from the coordinate MSEs against FP32 training-format references; the autonomous table uses the original saved reference precision. This precision distinction is explicit and does not change time alignment.',
            table(['Method','Entity','Quantity','Unit','Valid / 8','Pooled one-step RMSE'],[
                [method,entity,quantity,unit,len(vals),f(pooled(vals))] for (method,entity,quantity,unit),vals in _one_step_groups(out).items()])]
        (out/'coordinate_and_physical_errors.md').write_text('\n\n'.join(text)+'\n')
        diagnostics=load(out/'generation-diagnostics.json'); custom=load(out/'custom-answers.json')['summary']; group=defaultdict(list)
        for r in diagnostics: group[(r['method'],r['phase'],r['branch'])].append(r)
        notes=['# P08 generation diagnostics','Diagnostic rows are six checks on one repeatedly trained training example. Broader rows are eight distinct held-out scenarios from a separate fresh initialization. Hybrid reuses existing student/teacher outputs; it is not an additional generation call. Hybrid label success does not guarantee a valid teacher explanation; the teacher branch is reported separately.',
            table(['Method','Phase','Branch','Expected','Attempted','Typed valid','EOS','At token cap','Missing EOS','Fallback attempts','Recoveries','Complete answers'],[
                [*key,len(v),sum(x['attempted'] for x in v),sum(x['valid_typed_output'] for x in v),sum(x['EOS_terminated'] is True for x in v) if key[2]!='hybrid' else 'branch-specific',sum(x['token_cap_termination'] is True for x in v) if key[2]!='hybrid' else 'branch-specific',sum(x['missing_EOS'] is True for x in v) if key[2]!='hybrid' else 'branch-specific',sum(x['fallback_attempted'] for x in v),sum(x['fallback_recovered'] for x in v),sum(x['complete_success'] for x in v)] for key,v in group.items()]),
            '## Training-only milestone accuracy',table(['Method / branch','Update','Complete / 1','Correct targets / 4','Typed valid','EOS','Failure reason'],[
                [r['method']+'/'+r['branch'],r['milestone'],int(r['complete_success']),r['correct_targets'],r['valid_typed_output'],r['EOS_terminated'],r['reason']] for r in diagnostics if r['phase']=='diagnostic']),
            '## Failure categories',table(['Method','Phase','Branch','Reason','Count'],[[*key,reason,count] for key,v in group.items() for reason,count in Counter(x['reason'] for x in v if not x['valid_typed_output']).items()]),
            '## Validation answers',table(['Method','Complete / 8','Numeric correct / 24','Boolean coverage / 8','Boolean correct / supported'],[
                [r['method'],r['complete_successes'],r['common_numeric_correct'],r['boolean_supported'],str(r['boolean_correct'])+'/'+str(r['boolean_supported'])] for r in load(out/'provider-answers.json')['summary']]),
            'Public-only Booleans are explicitly unsupported by that control policy. Forecast conditions apply qualified deterministic public rules. Compare their common 24 numerical targets separately; full answers keep all 32 target components and all eight questions. Custom typed-answer conditions are separate direct-generative baselines, including their Boolean predictions and all failures.']
        (out/'generation_diagnostics.md').write_text('\n\n'.join(notes)+'\n')
        save(out/'physical-table-rows.json',{'trajectories':physical,'endpoints':endpoints})

def _one_step_groups(out):
    groups=defaultdict(list)
    for r in load(out/'one-step-physical.json'):
        if 'rmse' in r: groups[(r['method'],r['entity_id'],r['quantity'],r['unit'])].append(r['rmse'])
    return groups

if __name__=='__main__': main()
