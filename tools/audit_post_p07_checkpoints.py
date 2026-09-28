"""Read-only CPU evidence from preserved update-1/update-2 custom checkpoints."""
import argparse
import gc
import json
import math
import sys
from hashlib import sha256
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import torch
from phi_jepa.baselines.custom_checkpoint import load_checkpoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); torch.set_num_threads(2)
    if args.output.exists(): raise FileExistsError(args.output)
    report = {'scope': 'existing checkpoints; CPU; no optimizer steps or model generation', 'methods': {}}
    for method in ('coconut_inspired_t5_gru', 'codi_inspired_t5_distillation'):
        directory = args.native_root / 'p06-correctness-02' / method
        checkpoint = directory / 'checkpoint'
        identity = json.loads((directory / 'checkpoint-identity.json').read_text())
        files = sorted(checkpoint.glob('*.pt')); assert len(files) == 2
        payloads = []
        for path in files:
            assert sha256(path.read_bytes()).hexdigest() == path.stem
            payloads.append((torch.load(path, map_location='cpu', weights_only=True), path.name))
        payloads.sort(key=lambda pair: pair[0]['updates'])
        (before, first), (after, last) = payloads
        assert (before['updates'], after['updates']) == (1, 2)
        restored, optimizer, updates = load_checkpoint(checkpoint, identity=identity, training=True)
        groups = {}
        for name, parameter in restored.named_parameters():
            group_name = 'shared_T5' if name.startswith('t5.') else name.split('.')[0]
            group = groups.setdefault(group_name, {'unique_parameters': 0, 'tensor_count': 0,
                'changed_tensors': 0, 'delta_squared_norm': 0., 'max_absolute_delta': 0.})
            a, b = before['model'][name], after['model'][name]
            assert torch.equal(parameter.detach(), b), name
            delta = b.float() - a.float()
            group['unique_parameters'] += parameter.numel(); group['tensor_count'] += 1
            group['changed_tensors'] += int(torch.count_nonzero(delta) > 0)
            group['delta_squared_norm'] += float(delta.double().square().sum())
            group['max_absolute_delta'] = max(group['max_absolute_delta'], float(delta.abs().max()))
        for group in groups.values(): group['delta_l2_norm'] = math.sqrt(group.pop('delta_squared_norm'))
        actual = {id(p) for group in optimizer.param_groups for p in group['params']}
        expected = {id(p) for p in restored.parameters() if p.requires_grad}
        assert actual == expected
        states_finite = all(torch.isfinite(value).all() for state in optimizer.state.values() for value in state.values() if isinstance(value, torch.Tensor))
        assert states_finite and all(torch.isfinite(p).all() for p in restored.parameters())
        fixed = list(restored.teacher_proj.parameters()) if hasattr(restored, 'teacher_proj') else []
        assert all(not p.requires_grad and id(p) not in actual for p in fixed)
        assert restored.t5.is_gradient_checkpointing
        report['methods'][method] = {'checkpoints': [first, last], 'updates_restored': updates,
            'state_dict_exact_restore': True, 'all_optimizer_and_model_states_finite': bool(states_finite),
            'optimizer_exact_trainable_membership': True, 'teacher_projection_excluded': bool(fixed) if fixed else None,
            'optimizer_step_values': sorted({float(s['step']) for s in optimizer.state.values()}),
            'gradient_checkpointing_restored': True, 'groups': groups,
            'saved_fit_history': json.loads((directory / 'fit-report.json').read_text())['history']}
        print(json.dumps({'method': method, 'groups': groups}), flush=True)
        del before, after, payloads, restored, optimizer; gc.collect()
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__': main()
