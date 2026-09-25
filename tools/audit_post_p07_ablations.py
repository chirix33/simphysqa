"""Verify preserved independent ablation weights and pathway identities offline."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import torch
from phi_jepa.artifacts import digest
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import file_hash
from phi_jepa.models.augmented_ode import AugmentedODE, ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.baselines.conventional import NumericalComparator, BaselineSettings


def load(path): return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--native-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    torch.set_num_threads(2); root = Path(__file__).resolve().parents[1]
    data = load(root / 'docs/reviews/artifacts/P02a/tethered_load.state_plus_fixed_conditioning.json')
    layout = StateLayout.from_manifest(data, digest(data))
    primary_dir = args.native_root / 'p03-correctness-01'
    run = args.native_root / 'p05b-ablations-01'; summary = load(run / 'summary.json')
    primary_pointer = load(primary_dir / 'deployment/latest.json')
    primary = torch.load(primary_dir / 'deployment' / primary_pointer['file'], weights_only=True, map_location='cpu')
    report = {'primary_checkpoint': primary_pointer['sha256'], 'methods': {}}
    for method in ('no_enrichment', 'no_text_conditioning'):
        pointer = load(run / method / 'deployment/latest.json'); path = run / method / 'deployment' / pointer['file']
        assert file_hash(path) == pointer['sha256']
        bundle = torch.load(path, weights_only=True, map_location='cpu')
        state = bundle['state']; identity = bundle['manifest']['context_identity']
        assert identity == summary['identities'][method]
        if method == 'no_enrichment':
            assert identity['generated_enrichment'] == 'excluded'
            assert identity['context_mode'] == 'public_base_for_offline_audit'
            fresh = AugmentedODE(layout, ProjectionSettings(1024, seed=11), ODESettings(hidden_width=128, seed=11))
            assert any(not torch.equal(v, primary['state'][k]) for k, v in state.items())
            public = PublicProblem.parse(load(run / 'validation-public.json'))
            assert 'public_enrichment' not in json.loads(public.context(public.input['observation_cutoff']))
        else:
            assert all(identity[k] is None for k in ('encoder', 'projection', 'contextual_state'))
            assert all('projection' not in k for k in state)
            fresh = NumericalComparator(layout, BaselineSettings(method, embedding_width=0, hidden_width=128, seed=11))
            assert fresh.projection is None
        changed = [k for k, v in state.items() if not torch.equal(v, fresh.state_dict()[k])]
        assert changed and pointer['sha256'] != primary_pointer['sha256']
        training_pointer = load(run / method / 'training/latest.json')
        training = torch.load(run / method / 'training' / training_pointer['file'], weights_only=True, map_location='cpu')
        provenance = training['provenance']
        assert not provenance['primary_weights_loaded']
        assert set(provenance['transition_ids']) == set(load(primary_dir / 'summary.json')['provenance']['unique_transition_ids'])
        report['methods'][method] = {'checkpoint_sha256': pointer['sha256'], 'context_identity': identity,
            'state_width': summary['methods'][method]['state_width'],
            'changed_from_own_seeded_initialization': changed,
            'parameters': sum(p.numel() for p in fresh.parameters()), 'training': summary['methods'][method],
            'independent_initialization_source': 'tools/run_p05b_ablations.py; new constructor before each training loop',
            'same_primary_physical_transitions': True, 'training_provenance': provenance,
            'earlier_exact_deployment_replay': load(run / 'deployment-replay.json')[method]}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: {'checkpoint': v['checkpoint_sha256'], 'changed_tensors': len(v['changed_from_own_seeded_initialization']), 'parameters': v['parameters']} for k,v in report['methods'].items()}))


if __name__ == '__main__': main()
