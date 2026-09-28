"""Forward-only Stage 3 checkpoint parity, refinement and Q/C sensitivity.

No training or evaluator/reference handle; original numeric trajectory is saved
by the already completed public-only forecast run.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import torch
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.training.checkpoint import load_checkpoint
from phi_jepa.inference.rollout import rollout
from phi_jepa.solvers.rk4 import SolveStats, SolverSettings

parser = argparse.ArgumentParser()
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--profile', type=Path, required=True)
parser.add_argument('--cache-dir', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
torch.set_num_threads(2)
summary = json.loads((args.run / 'summary.json').read_text())
domain = summary['config']['correctness_fit']['domain']
manifest = json.loads((root / f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json').read_text())
layout = StateLayout.from_manifest(manifest, digest(manifest))
context = json.loads((root / 'configs/model_context_p02b.json').read_text())
backend = QwenEncoder(args.cache_dir, runtime_versions=context['encoder']['runtime_versions'], load_model=False)
encoder = ContextEncoder(backend, FrozenOutputCache(args.profile / 'embedding-cache'))
selected = json.loads((args.profile / 'selected-public.json').read_text())
row = next(r for r in selected if r['domain'] == domain and r['split'] == 'validation')
problem = PublicProblem.parse(row['public'])
enrichment = json.loads((args.profile / 'enrichment' / (problem.sample_id+'.json')).read_text())
e = encoder.encode(problem, problem.input['observation_cutoff'], mode='enriched', enrichment=enrichment)
changed = problem.input
changed['question'] += ' Explain how the explicitly scheduled control affects the requested quantity.'
alternative = PublicProblem.parse({'sample_id': problem.sample_id, 'schema_version': problem.schema_version, 'input': changed})
alt = encoder.encode(alternative, changed['observation_cutoff'], mode='enriched',
    enrichment={'public_input': alternative.input, 'notes': enrichment['notes']})
if not e.cache_hit or not alt.cache_hit:
    raise ValueError('verified prior context cache required')
model, solver = load_checkpoint(args.run / 'deployment', layout=layout,
                               context_identity=summary['context_identity'], training=False)
original = json.loads((args.run / 'autonomous-trajectory.json').read_text())
grid = [problem.input['observation_cutoff'], *[p['physical_time'] for p in original['predictions']]]
stats = SolveStats()
repeat = rollout(model, problem, torch.tensor([e.values]), grid, solver, stats)
if canonical(asdict(repeat)) != canonical(original):
    raise ValueError('real checkpoint fresh-process parity failure')
counterfactual = rollout(model, alternative, torch.tensor([alt.values]), grid, solver, stats)
refined = rollout(model, problem, torch.tensor([e.values]), grid, SolverSettings(solver.substeps*2), stats)
def values(result): return torch.tensor([p.values for p in result.predictions])
base, different, fine = values(repeat), values(counterfactual), values(refined)
result = {'checkpoint_fresh_process_parity': 'exact', 'refinement_substeps': solver.substeps*2,
    'refinement_max_abs_coordinate_delta': float((base-fine).abs().max()),
    'question_change_max_abs_numeric_delta': float((base[:, :layout.d]-different[:, :layout.d]).abs().max()),
    'question_change_terminal_numeric_l2_delta': float((base[-1, :layout.d]-different[-1, :layout.d]).norm()),
    'stats': stats.manifest(), 'encoder_cache': encoder.coverage,
    'claim': 'forward-only diagnostics of tiny fitted checkpoint, not established contextual reasoning'}
(args.run / 'checkpoint-diagnostics.json').write_bytes(canonical(result))
print(json.dumps(result))
