"""Fresh-process deployment parity for all comparisons; public input/cache only."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.baselines.conventional import forecast
from phi_jepa.baselines.checkpoint import load_checkpoint

parser=argparse.ArgumentParser()
for name in ('run','profile','cache_dir'): parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
args=parser.parse_args(); root=Path(__file__).resolve().parents[1]; torch.set_num_threads(2)
summary=json.loads((args.run/'summary.json').read_text()); p=PublicProblem.parse(json.loads((args.run/'validation-public.json').read_text()))
manifest=json.loads((root/f'docs/reviews/artifacts/P02a/{p.input["domain"]}.state_plus_fixed_conditioning.json').read_text()); layout=StateLayout.from_manifest(manifest,digest(manifest))
context=json.loads((root/'configs/model_context_p02b.json').read_text())
encoder=ContextEncoder(QwenEncoder(str(args.cache_dir),runtime_versions=context['encoder']['runtime_versions'],load_model=False),FrozenOutputCache(args.profile/'embedding-cache'))
encoded=encoder.encode(p,p.input['observation_cutoff'],mode='enriched',enrichment=json.loads((args.profile/'enrichment'/(p.sample_id+'.json')).read_text()))
if not encoded.cache_hit: raise ValueError('cache_required')
result={}
for method in summary['methods']:
    model,_,_,_=load_checkpoint(args.run/method/'deployment',layout=layout,context_identity=summary['context_identity'],method=method,training=False)
    saved=json.loads((args.run/method/'trajectory.json').read_text()); grid=[p.input['observation_cutoff'],*[r['physical_time'] for r in saved['predictions']]]
    repeated,usage=forecast(model,p,torch.tensor([encoded.values]),grid)
    if canonical(asdict(repeated))!=canonical(saved): raise ValueError('baseline_fresh_process_parity')
    result[method]={'replay':'exact','usage':usage}
result['encoder_cache']=encoder.coverage
(args.run/'deployment-replay.json').write_bytes(canonical(result)); print(json.dumps(result))
