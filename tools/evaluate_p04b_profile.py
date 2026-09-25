"""Separate evaluator: typed metrics and recorded-input diagnostic, never deployment."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import PhysicalRollout,FullAugmentedPrediction
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import ReleaseCatalog,EvaluatorTruthReader,forecast_states
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.training.checkpoint import load_checkpoint
from phi_jepa.solvers.rk4 import rk4,SolveStats
from phi_jepa.inference.readout import named_forecast,read_targets
from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors,grouped_summary
from phi_jepa.assessment.fixed import deterministic_answer

parser=argparse.ArgumentParser()
for name in ('run','profile','training_run','answer_run','cache_dir'): parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
args=parser.parse_args(); root=Path(__file__).resolve().parents[1]; torch.set_num_threads(2)
summary=json.loads((args.run/'summary.json').read_text()); domain=summary['domain']
release=json.loads((root/'configs/model_training_p02a.json').read_text())
catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
p,reference,identity=next(r for r in EvaluatorTruthReader(catalog,domain,'validation') if r[0].sample_id==summary['validation_sample_id'])
named=json.loads((args.run/'named-forecast.json').read_text()); answers=json.loads((args.answer_run/'results.json').read_text())
outputs={'raw_numeric_and_rule_readout':read_targets(p,named)}
for method,result in answers.items(): outputs[method]=result['answer']['targets'] if result['status']=='success' else []
target_metrics={}
for method,rows in outputs.items():
    report=evaluate_targets(p,reference,rows,method=method)
    report.update(scenario_id=identity.group_id,domain=domain,distribution='id')
    target_metrics[method]={'question':report,'summary':grouped_summary([report])}
autonomous=trajectory_errors(named['states'],reference['states'],mode='autonomous')
manifest=json.loads((root/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json').read_text())
layout=StateLayout.from_manifest(manifest,digest(manifest))
training_summary=json.loads((args.training_run/'summary.json').read_text())
model,solver=load_checkpoint(args.training_run/'deployment',layout=layout,context_identity=training_summary['context_identity'],training=False)
context=json.loads((root/'configs/model_context_p02b.json').read_text())
encoder=ContextEncoder(QwenEncoder(str(args.cache_dir),runtime_versions=context['encoder']['runtime_versions'],load_model=False),FrozenOutputCache(args.profile/'embedding-cache'))
encoded=encoder.encode(p,p.input['observation_cutoff'],mode='enriched',enrichment=json.loads((args.profile/'enrichment'/(p.sample_id+'.json')).read_text()))
if not encoded.cache_hit: raise ValueError('cache_required')
states=forecast_states(p,reference); inp=p.input; stats=SolveStats()
with torch.no_grad():
    current=torch.tensor([layout.flatten(s,inp) for s in states[:-1]])
    embedding=torch.tensor([encoded.values]*len(current)); projected=model.projection(embedding)
    predicted=rk4(model,torch.cat((current,projected),dim=-1),[s['timestamp'] for s in states[:-1]],[s['timestamp'] for s in states[1:]],solver,stats)
diagnostic=PhysicalRollout(p.sample_id,tuple(FullAugmentedPrediction(layout.sha256,layout.d,tuple(v),s['timestamp']) for v,s in zip(predicted.tolist(),states[1:])),'recorded_input_one_step_diagnostic')
diagnostic_named=named_forecast(p,layout,diagnostic,diagnostic=True)
one_step=trajectory_errors(diagnostic_named['states'],reference['states'],mode='recorded_input_one_step_diagnostic')
report={'scope':'one validation scenario; no final test or calibration selection', 'target_metrics':target_metrics,
    'autonomous':autonomous,'recorded_input_one_step_diagnostic':one_step,'diagnostic_stats':stats.manifest(),
    'encoder_cache':encoder.coverage,'deterministic_answer_fallback':deterministic_answer(p,named)}
(args.run/'evaluation.json').write_bytes(canonical(report))
print(json.dumps({'autonomous':autonomous['metrics'],'recorded_input_one_step_diagnostic':one_step['metrics'],'diagnostic_stats':stats.manifest()}))
