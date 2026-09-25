"""Real public registry bindings with synthetic hold-last predictions, not accuracy."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import PublicProblem,PhysicalRollout,FullAugmentedPrediction
from phi_jepa.integration.layout import StateLayout
from phi_jepa.inference.readout import named_forecast,read_targets

parser=argparse.ArgumentParser(); parser.add_argument('--profile',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
selected=json.loads((args.profile/'selected-public.json').read_text())
result={}
for row in selected:
    if row['split']!='validation': continue
    p=PublicProblem.parse(row['public']); inp=p.input
    manifest=json.loads((root/f'docs/reviews/artifacts/P02a/{row["domain"]}.state_plus_fixed_conditioning.json').read_text())
    layout=StateLayout.from_manifest(manifest,digest(manifest))
    vals=layout.flatten(inp['states'][-1],inp)+(0.,)*layout.d
    grid=[round(i*.02,8) for i in range(round(inp['observation_cutoff']/.02)+1,round(max(t['end_time'] for t in inp['answer_spec'])/.02)+1)]
    synthetic=PhysicalRollout(p.sample_id,tuple(FullAugmentedPrediction(layout.sha256,layout.d,vals,t) for t in grid))
    mapped=named_forecast(p,layout,synthetic); outputs=read_targets(p,mapped)
    result[row['domain']]={'sample_id':p.sample_id,'layout_sha256':layout.sha256,
        'named_channels':len(mapped['states'][0]['measurements']),
        'targets':[{k:o[k] for k in ('target_id','answer_type','status','reason')} for o in outputs]}
report={'scope':'four real public validation schemas with synthetic constant predictions; binding/support checks only, no empirical accuracy', 'domains':result}
args.output.write_bytes(canonical(report)); print(json.dumps(report))
