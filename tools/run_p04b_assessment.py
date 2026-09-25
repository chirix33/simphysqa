"""One real training prediction reference and one validation assessment; no truth."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from phi_jepa.artifacts import canonical,digest,code_provenance
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import ReleaseCatalog,PublicInputReader,json_lines,file_hash
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.openai_judge import OpenAIJudge
from phi_jepa.providers.contracts import ProviderFailure
from phi_jepa.training.checkpoint import load_checkpoint
from phi_jepa.inference.rollout import rollout
from phi_jepa.inference.readout import named_forecast
from phi_jepa.solvers.rk4 import SolveStats
from phi_jepa.assessment.reference import ReferenceBank
from phi_jepa.assessment.checks import physical_checks,contract_score
from phi_jepa.assessment.fixed import combine,calibrate,apply_threshold,bounded_fallback,deterministic_answer
from phi_jepa.typed_evaluation import augmented_drift


def save(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_bytes(canonical(value)); tmp.replace(path)


def main():
    parser=argparse.ArgumentParser()
    for name in ('profile','training_run','answer_run','cache_dir','output'): parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=False); torch.set_num_threads(2)
    config=json.loads((root/'configs/assessment_p04b.json').read_text())
    context=json.loads((root/'configs/model_context_p02b.json').read_text())
    summary=json.loads((args.training_run/'summary.json').read_text())
    release=json.loads((root/'configs/model_training_p02a.json').read_text())
    catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
    selected=json.loads((args.profile/'selected-public.json').read_text())
    rows={r['split']:r for r in selected if r['domain']=='tethered_load'}
    domain='tethered_load'
    manifest=json.loads((root/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json').read_text())
    layout=StateLayout.from_manifest(manifest,digest(manifest))
    model,solver=load_checkpoint(args.training_run/'deployment',layout=layout,context_identity=summary['context_identity'],training=False)
    backend=QwenEncoder(str(args.cache_dir),runtime_versions=context['encoder']['runtime_versions'],load_model=False)
    encoder=ContextEncoder(backend,FrozenOutputCache(args.profile/'embedding-cache'))
    stats=SolveStats(); bank_rows=[]; problems={}; results={}; initial={}
    for split in ('train','validation'):
        p=PublicProblem.parse(rows[split]['public']); problems[split]=p
        path=catalog.verified_file(domain,split,'inputs.jsonl')
        verified=next(item for item in PublicInputReader(path,catalog.files(domain,split)['inputs.jsonl']['sha256']) if item.sample_id==p.sample_id)
        if verified!=p: raise ValueError('selected_public_identity')
        # Routing metadata only. No references.jsonl is opened in this process.
        meta=next(row['metadata'] for row in json_lines(catalog.verified_file(domain,split,'evaluator.jsonl')) if row['sample_id']==p.sample_id)
        if meta['split']!=split or meta['validation']['status']!='accepted': raise ValueError('source_split')
        enrichment=json.loads((args.profile/'enrichment'/(p.sample_id+'.json')).read_text())
        encoded=encoder.encode(p,p.input['observation_cutoff'],mode='enriched',enrichment=enrichment)
        if not encoded.cache_hit: raise ValueError('profile_requires_existing_encoder_cache')
        endpoint=max(t['end_time'] for t in p.input['answer_spec']); cutoff=p.input['observation_cutoff']
        grid=[round(i*.02,8) for i in range(round(cutoff/.02),round(endpoint/.02)+1)]
        if stats.solves+len(grid)-1>config['profile_budget']['max_ode_solves']: raise ValueError('solve_budget')
        e=torch.tensor([encoded.values])
        with torch.no_grad(): initial[split]=list(layout.flatten(p.input['states'][-1],p.input))+model.projection(e)[0].tolist()
        predicted=rollout(model,p,e,grid,solver,stats); results[split]=predicted
        save(args.output/(split+'-trajectory.json'),asdict(predicted))
        bank_rows.append({'sample_id':p.sample_id,'scenario_id':meta['base_scenario_id'],'split':split,
            'origin':'autonomous_prediction','domain':domain,'layout_sha256':layout.sha256,'cutoff':cutoff,
            'times':[r.physical_time for r in predicted.predictions],'trajectory':[list(r.values) for r in predicted.predictions],
            'embedding':list(encoded.values),'public_sha256':digest(p.input),'embedding_request_sha256':encoded.request_sha256})
    if canonical(asdict(results['validation']))!=(args.training_run/'autonomous-trajectory.json').read_bytes(): raise ValueError('checkpoint_validation_replay')
    checkpoint=json.loads((args.training_run/'deployment/latest.json').read_text())
    projection={k:sha256(v.detach().cpu().numpy().tobytes()).hexdigest() for k,v in model.projection.state_dict().items()}
    identity={'checkpoint_sha256':checkpoint['sha256'],'projection_sha256':digest(projection),
        'encoder_sha256':digest(summary['context_identity']),'solver_sha256':digest(asdict(solver)),
        'layout_sha256':layout.sha256,'profile_sha256':digest(config)}
    bank=ReferenceBank.build(identity,[bank_rows[0]]); bank.write(args.output/'bank')
    familiarity=bank.assess(bank_rows[1],layout,identity=identity)
    p=problems['validation']; forecast=named_forecast(p,layout,results['validation'])
    save(args.output/'named-forecast.json',forecast)
    checks=physical_checks(p,forecast,config['physical_checks'])
    contracts=contract_score(p,forecast,[])
    prompts=json.loads((root/'docs/assets/prompts.json').read_text())
    asset={'prompt':prompts['JUDGE_PROMPT'],'schema':json.loads((root/'docs/assets/judge_schema.json').read_text())}
    provider_config={'model':'gpt-5.6-sol','reasoning_effort':'medium','max_attempts_per_request':2,
        'max_total_attempts':config['profile_budget']['max_judge_attempts'],'max_output_tokens':config['profile_budget']['max_output_tokens'],'timeout_seconds':120}
    judge=OpenAIJudge(load_openai_key(root/'.env'),provider_config,asset,FrozenOutputCache(args.output/'judge-cache'),event_sink=lambda value:save(args.output/'ledger.json',value))
    try: semantic=judge.judge(p)
    except ProviderFailure as exc: semantic={'status':'unavailable','score':None,'reason':exc.code.value,'scope':'scenario_schema_v1'}
    assessment_identity={**identity,'bank_sha256':bank.sha256,'judge_asset_sha256':digest(asset),'judge_config_sha256':digest(provider_config)}
    assessed=combine(familiarity,contracts,semantic,profile=config,identity=assessment_identity)
    calibration=calibrate([],assessment_identity=assessment_identity,profile_sha256=digest(config),policy=config['calibration'],selection_scenarios=[bank_rows[1]['scenario_id']])
    assessed=apply_threshold(assessed,calibration)
    failure=bounded_fallback(None,failure='forecast_failure')  # deliberate offline branch, no fake model output
    answer_failure=bounded_fallback(forecast,failure='answer_failure',numeric_formatter=lambda value:deterministic_answer(p,value))
    drift=augmented_drift(layout,initial['validation'],results['validation'].predictions)
    save(args.output/'assessment.json',assessed); save(args.output/'physical-checks.json',checks)
    save(args.output/'calibration.json',calibration); save(args.output/'drift.json',drift)
    save(args.output/'failure-diagnostics.json',{'forecast_failure':failure,'answer_failure':answer_failure})
    save(args.output/'source.json',code_provenance())
    events=judge.runner.events
    report={'status':assessed['status'],'familiarity':familiarity,'contract':contracts,'judge':semantic,
        'physical_check_summary':{k:v for k,v in checks.items() if k!='checks'},'calibration_status':calibration['status'],
        'threshold_decision':assessed['threshold_decision'],'stats':stats.manifest(),'encoder_cache':encoder.coverage,
        'judge_calls':len(events),'input_tokens':sum(e['usage']['input_tokens'] or 0 for e in events),
        'output_tokens':sum(e['usage']['output_tokens'] or 0 for e in events),'usage_priced_cost_usd':sum(e['usage']['cost_usd'] or 0 for e in events),
        'training_updates':0,'bank_references':1,'validation_questions':1,'provider_config':provider_config,
        'validation_sample_id':p.sample_id,'validation_scenario_id':bank_rows[1]['scenario_id'],'domain':domain}
    save(args.output/'summary.json',report); print(json.dumps(report))


if __name__=='__main__': main()
