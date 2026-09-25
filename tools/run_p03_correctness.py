"""Bounded Stage 3 correctness fit, not a benchmark or final-study launcher."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import torch

from phi_jepa.artifacts import canonical, digest, code_provenance
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import ReleaseCatalog, EvaluatorTruthReader, make_pairs, file_hash, forecast_states
from phi_jepa.models.augmented_ode import AugmentedODE, ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.solvers.rk4 import SolverSettings, SolveStats, rk4
from phi_jepa.training.pairs import PairTrainer, TrainingSettings
from phi_jepa.training.checkpoint import write_checkpoint, load_checkpoint
from phi_jepa.inference.rollout import rollout


def save(path, value):
    path.write_bytes(canonical(value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--cache-dir', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)  # never overwrite an experiment
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'configs/model_training_p03.json').read_text())
    context = json.loads((root / 'configs/model_context_p02b.json').read_text())
    source = code_provenance()
    limits = config['correctness_fit']
    if limits['max_pairs'] > 20 or limits['max_updates'] > 200 or limits['max_seconds'] > 900:
        raise ValueError('correctness fit exceeds authorized stage cap')
    torch.set_num_threads(2)
    torch.manual_seed(11)
    selected = json.loads((args.profile / 'selected-public.json').read_text())
    domain = limits['domain']
    selected = {row['split']: row for row in selected if row['domain'] == domain}
    problems = {split: PublicProblem.parse(row['public']) for split,row in selected.items()}
    audit = json.loads((root / 'docs/reviews/artifacts/P02a/export-audit.json').read_text())
    layout_file = root / f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json'
    layout = StateLayout.from_manifest(json.loads(layout_file.read_text()), audit['training_reader_real_export_smoke'][domain]['registry_sha256'])
    backend = QwenEncoder(args.cache_dir, runtime_versions=context['encoder']['runtime_versions'], load_model=False)
    encoder = ContextEncoder(backend, FrozenOutputCache(args.profile / 'embedding-cache'))
    encoded, enrichments = {}, {}
    for split,problem in problems.items():
        enrichments[split] = json.loads((args.profile / 'enrichment' / (problem.sample_id + '.json')).read_text())
        value = encoder.encode(problem, problem.input['observation_cutoff'], mode='enriched', enrichment=enrichments[split])
        if not value.cache_hit:
            raise ValueError('bounded fit requires verified existing frozen E cache')
        encoded[split] = value
    release = json.loads((root / 'configs/model_training_p02a.json').read_text())
    catalog = ReleaseCatalog(root / release['export_root'], release['export_index_sha256'], release['release_manifest_sha256'])
    problem, reference, identity = next(row for row in catalog.records(domain, 'train') if row[0].sample_id == problems['train'].sample_id)
    if problem != problems['train']:
        raise ValueError('selected train public identity mismatch')
    states = forecast_states(problem, reference)
    # Multiplicity is irrelevant to the explicitly selected unit weights. Keep
    # physical IDs and exact recorded adjacency; do not drop question contexts.
    counts = Counter({digest((domain, identity.group_id, a['timestamp'], b['timestamp'])): 1
                      for a,b in zip(states,states[1:])})
    provenance = {'release': catalog.identity, 'train_files': catalog.files(domain, 'train'),
        'weighting': config['weighting'], 'enrichment_sha256': digest(enrichments['train']),
        'context_request_sha256': encoded['train'].request_sha256, 'selection': limits['selection']}
    all_pairs = list(make_pairs(problem, reference, identity, layout, digest(provenance), counts,
        context_mode='enriched', enrichment=enrichments['train'], duplicate_policy=config['weighting']))
    pairs = all_pairs[:limits['max_pairs']]
    provenance['pair_ids'] = [p.pair_id for p in pairs]
    provenance['unique_transition_ids'] = sorted({p.transition_id for p in pairs})
    model = AugmentedODE(layout, ProjectionSettings(**config['projection']), ODESettings(**config['ode']))
    trainer = PairTrainer(model, SolverSettings(**config['solver']), TrainingSettings(**config['optimizer']))
    embeddings = torch.tensor([encoded['train'].values] * len(pairs), dtype=torch.float32)
    context_identity = digest({'encoder': context['encoder'], 'enrichment': context['enrichment_provider'],
                               'asset_sha256': file_hash(root / context['enrichment_asset'])})
    history = []
    started = time.perf_counter()
    for update in range(limits['max_updates']):
        if time.perf_counter() - started >= limits['max_seconds']:
            break
        # This correctness selection fits one batch; checkpoint sampler preserves
        # the exact epoch/position and all selected pair identities.
        history.append(trainer.step(pairs, embeddings))
        if update == 99:
            write_checkpoint(args.output / 'training', trainer, context_identity=context_identity,
                provenance=provenance, sampler_state={'epoch': update+1, 'position': 0,
                    'ordered_pair_ids': [p.pair_id for p in pairs], 'selection_history': ['declared_first_20']})
            trainer, sampler, restored_provenance = load_checkpoint(args.output / 'training', layout=layout,
                context_identity=context_identity, training=True)
            if sampler['epoch'] != update+1 or restored_provenance != provenance:
                raise ValueError('correctness-fit resume mismatch')
            model = trainer.model
    fit_seconds = time.perf_counter() - started
    train_pointer = write_checkpoint(args.output / 'training', trainer, context_identity=context_identity,
        provenance=provenance, sampler_state={'epoch': trainer.updates, 'position': 0,
            'ordered_pair_ids': [p.pair_id for p in pairs], 'selection_history': ['declared_first_20']})
    deploy_pointer = write_checkpoint(args.output / 'deployment', trainer, context_identity=context_identity,
        provenance={}, sampler_state={}, deployment=True)
    save(args.output / 'training-history.json', history)
    deploy_model, solver = load_checkpoint(args.output / 'deployment', layout=layout, context_identity=context_identity, training=False)
    public_validation = problems['validation']
    begin = public_validation.input['observation_cutoff']
    end = max(spec['end_time'] for spec in public_validation.input['answer_spec'])
    intervals = round((end - begin) / 0.02)
    grid = [round(begin + i * 0.02, 10) for i in range(intervals + 1)]
    grid[-1] = end
    val_e = torch.tensor([encoded['validation'].values], dtype=torch.float32)
    autonomous_stats = SolveStats()
    predicted = rollout(deploy_model, public_validation, val_e, grid, solver, autonomous_stats)
    save(args.output / 'autonomous-trajectory.json', asdict(predicted))
    # Evaluator-only truth is first accessed AFTER public-only rollout is saved.
    val_problem, val_reference, val_identity = next(row for row in EvaluatorTruthReader(catalog, domain, 'validation')
        if row[0].sample_id == public_validation.sample_id)
    if val_identity.group_id == identity.group_id or val_problem != public_validation:
        raise ValueError('validation selection identity/group leakage')
    val_states = forecast_states(val_problem, val_reference)
    if any(abs(s['timestamp'] - t) > 1e-9 for s,t in zip(val_states, grid)) or len(val_states) != len(grid):
        raise ValueError('external rollout grid does not align with evaluator states')
    numerical = torch.tensor([layout.flatten(s, val_problem.input) for s in val_states], dtype=torch.float32)
    next_values = torch.tensor([p.values for p in predicted.predictions])
    initial_p = deploy_model.projection(val_e).detach()
    error = (next_values[:, :layout.d] - numerical[1:]).square()
    diagnostic_stats = SolveStats()
    with torch.no_grad():
        x = torch.cat((numerical[:-1], initial_p.expand(len(grid)-1, -1)), dim=1)
        one_step = rk4(deploy_model, x, grid[:-1], grid[1:], solver, diagnostic_stats)
    one_error = (one_step[:, :layout.d] - numerical[1:]).square()
    identity_error = (numerical[:-1] - numerical[1:]).square()
    metrics = {'mode': 'one separate validation question; not benchmark performance',
        'sample_id': public_validation.sample_id, 'autonomous_numeric_mse': float(error.mean()),
        'autonomous_terminal_numeric_mse': float(error[-1].mean()),
        'recorded_input_one_step_numeric_mse': float(one_error.mean()),
        'identity_recorded_input_one_step_numeric_mse': float(identity_error.mean()),
        'context_drift_l2_by_horizon': (next_values[:, layout.d:] - initial_p).norm(dim=1).tolist(),
        'numeric_mse_by_horizon': error.mean(dim=1).tolist(),
        'autonomous_stats': autonomous_stats.manifest(), 'recorded_input_stats': diagnostic_stats.manifest()}
    save(args.output / 'validation-metrics.json', metrics)
    summary = {'phase': 'P03', 'source': source, 'script_sha256': file_hash(__file__),
        'config': config, 'config_sha256': digest(config), 'context_identity': context_identity,
        'training_questions': 1, 'training_scenarios': 1, 'training_examples': len(pairs),
        'unique_transitions': len({p.transition_id for p in pairs}), 'updates': trainer.updates,
        'fit_seconds': fit_seconds, 'initial_loss': history[0]['loss'], 'final_preupdate_loss': history[-1]['loss'],
        'training_stats': trainer.stats.manifest(), 'failed_updates': trainer.failed_updates,
        'training_checkpoint': train_pointer, 'deployment_checkpoint': deploy_pointer,
        'validation': metrics, 'encoder_cache': encoder.coverage, 'provenance': provenance,
        'full_training_launched': False, 'new_provider_calls': 0, 'new_encoder_calls': 0}
    save(args.output / 'summary.json', summary)
    print(json.dumps({k:v for k,v in summary.items() if k in ('updates','fit_seconds','initial_loss','final_preupdate_loss','training_stats')}))
    print(json.dumps({k:v for k,v in metrics.items() if not isinstance(v,list)}))


if __name__ == '__main__': main()
