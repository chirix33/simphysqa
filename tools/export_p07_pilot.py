"""Freeze existing bounded pilot evidence; no training, provider or truth access."""
import argparse,json,sys,time,hashlib
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical,digest,code_provenance,write_run,read_run
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.baselines.controls import runtime_control


def load(path): return json.loads(path.read_text())


def publish(root,result,payloads,*,elapsed,recovered=False):
    verified,_=read_run(result)
    if verified!=payloads: raise ValueError('export_roundtrip')
    table=[{'method':name,'numeric_complete':r['numerical']['complete_success'] if r['numerical'] else None,'answer_complete':r['answer']['complete_success'],'valid_targets':r['answer']['valid_targets'],'eligible_targets':r['answer']['eligible_targets']} for name,r in payloads['method-results.json'].items()]
    evidence=root/'docs/reviews/artifacts/P07'; evidence.mkdir(parents=True,exist_ok=True)
    for name in ('method-results.json','runtime-controls.json','provider-costs.json','native-io.json','scope-and-counts.json','sources.json'): (evidence/name).write_bytes(canonical(payloads[name]))
    (evidence/'export.json').write_bytes(canonical({'native_run':str(result),'manifest_sha256':result.name,'payloads':len(payloads),'roundtrip_verified':True,'elapsed_seconds':elapsed,'recovered_reporting_failure':recovered,'table':table}))
    print(json.dumps({'run':str(result),'payloads':len(payloads),'table':table,'costs':payloads['provider-costs.json'],'io':payloads['native-io.json'],'recovered_reporting_failure':recovered}),flush=True)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--native-root',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); parser.add_argument('--recover',type=Path); args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]; artifacts=root/'docs/reviews/artifacts'; c=load(root/'configs/pilot_p07.json'); start=time.perf_counter()
    if args.recover:
        payloads,_=read_run(args.recover)
        if payloads['scope-and-counts.json']['manifest']!=c: raise ValueError('recovery_scope_identity')
        publish(root,args.recover,payloads,elapsed=None,recovered=True); return
    runs={k:args.native_root/v for k,v in c['native_runs'].items()}; payloads={}; sources={}
    def keep(name,path):
        if time.perf_counter()-start>c['additional_budget']['max_seconds']: raise TimeoutError('pilot_export_cap')
        payloads[name]=load(path); sources[str(path)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
        return payloads[name]
    configs={p.name:load(p) for p in sorted((root/'configs').glob('*.json')) if p.name in ('pilot_p07.json','model_context_p02b.json','model_training_p02a.json','model_training_p03.json','answer_p04a.json','assessment_p04b.json','baselines_p05b.json','ablations_p05b.json','custom_p06.json')}
    payloads['frozen-configurations.json']=configs
    primary=keep('primary-training-summary.json',runs['primary']/'summary.json')
    if (primary['training_examples'],primary['training_questions'],primary['unique_transitions'])!=(20,1,20): raise ValueError('training_selection_changed')
    keep('primary-training-history.json',runs['primary']/'training-history.json')
    keep('primary-autonomous-augmented.json',runs['primary']/'autonomous-trajectory.json')
    keep('primary-validation-diagnostics.json',runs['primary']/'validation-metrics.json')
    for name in ('named-forecast','physical-checks','drift','assessment','calibration','offline-replay','evaluation','summary'):
        keep('assessment-'+name+'.json',runs['assessment']/(name+'.json'))
    for name in ('public','predicted','public_only','reversed_forecast','cache-replay','summary','numeric-readout'):
        keep('answer-'+name+'.json',runs['answers']/(name+'.json'))
    evaluator=keep('primary-evaluation.json',artifacts/'P04b/evaluation-summary.json')
    methods={'phi_jepa':{'numerical':evaluator['target_metrics']['raw_numeric_and_rule_readout']['question'],
        'answer':evaluator['target_metrics']['predicted']['question'],'physical_metrics':evaluator['autonomous']['metrics'],
        'training_effort':{'updates':primary['updates'],'examples':20,'questions':1,'loss':'full augmented adjacent MSE'}}}
    for key in ('comparators','retraining_ablations'):
        summary=keep(key+'-training-summary.json',runs[key]/'summary.json')
        evaluated=keep(key+'-evaluation.json',runs[key]/'evaluation.json')
        keep(key+'-answer-summary.json',runs[key]/'answer-summary.json')
        for method in summary['config']['methods']:
            result=evaluated[method]
            methods[method]={'numerical':result['numeric_and_rule_targets'],'answer':result['final_answer_targets'],'physical_metrics':result['autonomous_physical_metrics'],'physical_checks':result['physical_checks'],'training_effort':summary['methods'][method]}
            for filename in ('trajectory.json','named-forecast.json','readout.json','answer.json','per-time-errors.json'):
                keep(method+'-'+filename,runs[key]/method/filename)
        keep(key+'-deployment-replay.json',runs[key]/'deployment-replay.json')
    custom=keep('custom-evaluation.json',runs['custom_baselines']/'evaluation.json')
    for method in configs['custom_p06.json']['methods']:
        for phase in ('qualify','fit','infer'):
            report=keep(method+'-'+phase+'.json',runs['custom_baselines']/method/(phase+'-report.json'))
            if report['status']!='success': raise ValueError('custom_stage_not_finished')
        keep(method+'-generations.json',runs['custom_baselines']/method/'generations.json')
        keep(method+'-checkpoint-identity.json',runs['custom_baselines']/method/'checkpoint-identity.json')
    for result in custom['per_question']:
        if result['split']=='validation': methods[result['method']]={'numerical':None,'answer':result,'physical_metrics':None,'training_effort':{'updates':2,'questions':1,'loss':'method-specific CE/alignment, not numerical MSE'}}
    if set(methods)!=set(c['methods']): raise ValueError('pilot_method_denominator')
    for result in methods.values():
        if result['answer']['sample_id']!=c['validation_sample_id'] or result['answer']['eligible_questions']!=1 or result['answer']['eligible_targets']!=4: raise ValueError('pilot_heldout_identity')
    problem=PublicProblem.parse(payloads['answer-public.json']); forecast=payloads['assessment-named-forecast.json']; cached_answer=payloads['answer-predicted.json']['answer']
    counters={'cached_answer_reads':0,'cached_assessment_reads':0,'new_provider_calls':0}
    def answer(supplied,outcomes):
        if digest(supplied)!=digest(forecast): raise ValueError('runtime_control_forecast_changed')
        counters['cached_answer_reads']+=1; return deepcopy(cached_answer)
    def assess(): counters['cached_assessment_reads']+=1; return deepcopy(payloads['assessment-assessment.json'])
    controls={}
    for name in ('without_fixed_assessment','without_fallback'):
        result=runtime_control(name,problem,forecast,checkpoint_sha256=primary['deployment_checkpoint']['file'].split('.')[0],assess=assess,answer=answer,assessment_active=True,fallback_active=False)
        if result['failure'] or result['answer']!=cached_answer: raise ValueError('runtime_control_replay')
        controls[name]={'execution':result,'answer_metrics_reused':methods['phi_jepa']['answer'],'new_independent_observations':0}
    controls['public_only_answer']={'answer':evaluator['target_metrics']['public_only']['question'],'limitation':'Boolean forced unsupported under public-only primary readout policy; numeric comparison separate'}
    controls['reversed_forecast_diagnostic']={'answer':evaluator['target_metrics']['reversed_forecast']['question'],'kind':'runtime diagnostic, not retraining'}
    payloads['runtime-controls.json']={'controls':controls,'counts':counters}
    payloads['method-results.json']=methods
    # Existing billed work across stages, not new pilot spend or per-method shared-cost allocation.
    provider=load(artifacts/'P02b/provider-summary.json'); costs=[{'phase':'P02b','calls':len(provider['events']),'cost_usd':sum(e['usage']['cost_usd'] for e in provider['events']),'input_tokens':sum(e['usage']['input_tokens'] for e in provider['events']),'output_tokens':sum(e['usage']['output_tokens'] for e in provider['events'])}]
    for phase,path,calls_key in [('P04a',artifacts/'P04a/summary.json','attempts'),('P04b',artifacts/'P04b/summary.json','judge_calls'),('P05b',artifacts/'P05b/answer-summary.json','attempts'),('P05b_ablations',artifacts/'P05b/ablations/answer-summary.json','attempts')]:
        row=load(path); costs.append({'phase':phase,'calls':row[calls_key],'cost_usd':row['usage_priced_cost_usd'],'input_tokens':row['input_tokens'],'output_tokens':row['output_tokens']})
    payloads['provider-costs.json']={'existing_phase_costs':costs,'existing_total_usd':sum(r['cost_usd'] for r in costs),'existing_calls':sum(r['calls'] for r in costs),'new_pilot_calls':0,'new_pilot_cost_usd':0,'meaning':'includes shared four-domain enrichment qualification; not a per-tether-method cost estimate'}
    io=[]
    for checkpoint_dir in (runs['primary']/'deployment',runs['custom_baselines']/'codi_inspired_t5_distillation'/'checkpoint'):
        pointer=load(checkpoint_dir/'latest.json'); path=checkpoint_dir/pointer['file']; passes=[]
        for i in range(2):
            when=time.perf_counter()
            with path.open('rb') as stream: measured=hashlib.file_digest(stream,'sha256').hexdigest()
            passes.append(time.perf_counter()-when)
            if measured!=path.stem: raise ValueError('checkpoint_sha256')
        io.append({'path':str(path),'bytes':path.stat().st_size,'sha256':measured,'read_and_hash_seconds':passes,'cache_state':'OS cache not controlled; first and second observed passes only'})
    payloads['native-io.json']=io
    sources.update({str(root/'configs'/name):{'sha256':hashlib.sha256((root/'configs'/name).read_bytes()).hexdigest()} for name in configs})
    payloads['sources.json']=sources
    payloads['scope-and-counts.json']={'manifest':c,'counts':{'training_questions':1,'training_scenarios':1,'question_pairs':20,'unique_physical_transitions':20,'validation_questions':1,'validation_scenarios':1,'future_timepoints':40,'targets_per_question':4},'confidence_intervals':'unavailable: one independent validation scenario','export_seconds_before_verification':time.perf_counter()-start}
    result=write_run(args.output,payloads,{'stage':'P07','source':code_provenance(),'scope':c,'retrospective_freeze':True})
    publish(root,result,payloads,elapsed=time.perf_counter()-start)


if __name__=='__main__': main()
