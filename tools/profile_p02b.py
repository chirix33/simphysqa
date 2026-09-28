"""Stage 2 only: public token coverage, bounded enrichment, frozen-E/P profile.

No training sequences, evaluator references, ODE or future-stage implementation.
Full provider payloads and embeddings stay in the supplied ignored/native output.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from phi_jepa.artifacts import canonical, digest, code_provenance
from phi_jepa.integration.contracts import DOMAINS, PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import ReleaseCatalog, PublicInputReader, file_hash
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.contracts import ProviderFailure
from phi_jepa.providers.qwen import QwenEncoder, REVISION


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.pending')
    temporary.write_bytes(canonical(value))
    temporary.replace(path)


def selection(root, output, backend):
    cfg = json.loads((root / 'configs/model_training_p02a.json').read_text())
    catalog = ReleaseCatalog(root / cfg['export_root'], cfg['export_index_sha256'], cfg['release_manifest_sha256'])
    summary, selected = {}, []
    for domain in sorted(DOMAINS):
        for split in ('train', 'validation'):
            path = catalog.verified_file(domain, split, 'inputs.jsonl')
            lengths, longest = [], None
            for problem in PublicInputReader(path, file_hash(path)):
                text = problem.context(problem.input['observation_cutoff'])
                length = len(backend.tokenize(text))
                lengths.append(length)
                if longest is None or length > longest[0]:
                    longest = (length, problem)
            if len(lengths) != catalog.partitions[domain, split]['counts']['questions']:
                raise ValueError('public partition count mismatch')
            summary[f'{domain}/{split}'] = {'count': len(lengths), 'minimum': min(lengths),
                'maximum': max(lengths), 'mean': sum(lengths) / len(lengths),
                'overlength': sum(n > backend.settings.max_length for n in lengths),
                'public_file_sha256': file_hash(path)}
            selected.append({'domain': domain, 'split': split, 'base_token_count': longest[0],
                'public': {'sample_id': longest[1].sample_id, 'schema_version': longest[1].schema_version,
                           'input': longest[1].input}})
            print(json.dumps({'partition': f'{domain}/{split}', **summary[f'{domain}/{split}']}), flush=True)
    save(output / 'selected-public.json', selected)
    return {'partitions': summary, 'selection': 'longest base token count per domain/train-or-validation',
        'selected': [{'sample_id': row['public']['sample_id'], 'domain': row['domain'], 'split': row['split'],
                      'base_token_count': row['base_token_count']} for row in selected],
        'encoder_settings': asdict(backend.settings), 'context_mode': 'public_base_for_offline_audit'}


def provider_profile(root, output, config):
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
    rows = json.loads((output / 'selected-public.json').read_text())
    asset = json.loads((root / config['enrichment_asset']).read_text())
    ledger_path = output / 'provider-ledger.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else None
    prior_attempts = len((ledger or {}).get('events', []))
    provider = OpenAIEnrichment(load_openai_key(root / '.env'), config['enrichment_provider'], asset,
        FrozenOutputCache(output / 'enrichment-cache'),
        event_sink=lambda events: save(ledger_path, events), ledger=ledger)
    outcomes = []
    for row in rows:
        problem = PublicProblem.parse(row['public'])
        try:
            enrichment = provider.enrich(problem, problem.input['observation_cutoff'])
            save(output / 'enrichment' / (problem.sample_id + '.json'), enrichment)
            outcomes.append({'sample_id': problem.sample_id, 'status': 'success',
                             'enrichment_sha256': digest(enrichment)})
        except ProviderFailure as exc:
            outcomes.append({'sample_id': problem.sample_id, 'status': 'failed', 'code': exc.code.value})
            # Stop on global provider access/configuration failure. Other samples
            # remain explicitly not attempted; no fixture substitution.
            if exc.code.value in ('missing_credentials', 'provider_unavailable', 'rate_limit', 'transport'):
                break
        finally:
            save(output / 'provider-outcomes.json', outcomes)
    return {'outcomes': outcomes, 'expected_samples': len(rows), 'not_attempted': len(rows) - len(outcomes),
        'events': provider.runner.events, 'responses': provider.response_metadata, 'cache_hits': provider.cache_hits,
        'prior_attempts': prior_attempts, 'new_attempts': len(provider.runner.events) - prior_attempts}


def encoder_profile(root, output, config, backend, mode):
    import torch
    from phi_jepa.models.context_projection import ContextProjection, ProjectionSettings
    rows = json.loads((output / 'selected-public.json').read_text())
    audit = json.loads((root / 'docs/reviews/artifacts/P02a/export-audit.json').read_text())
    encoder = ContextEncoder(backend, FrozenOutputCache(output / 'embedding-cache'))
    outcomes = []
    torch.cuda.reset_peak_memory_stats()
    for row in rows:
        problem = PublicProblem.parse(row['public'])
        domain, cutoff = row['domain'], problem.input['observation_cutoff']
        path = root / f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json'
        layout = StateLayout.from_manifest(json.loads(path.read_text()),
            audit['training_reader_real_export_smoke'][domain]['registry_sha256'])
        enrichment = None
        if mode == 'enriched':
            enrichment = json.loads((output / 'enrichment' / (problem.sample_id + '.json')).read_text())
        started = time.perf_counter()
        encoded = encoder.encode(problem, cutoff, mode=mode, enrichment=enrichment)
        elapsed = time.perf_counter() - started
        projection = ContextProjection(layout, ProjectionSettings(1024))
        e = torch.tensor([encoded.values], dtype=torch.float32)
        p = projection(e)
        p.sum().backward()
        # A real public control perturbation checks E/P sensitivity only. No
        # forecast claim and no modification of the saved public input.
        changed = problem.input
        changed['question'] += ' Explain how the explicitly scheduled control affects the requested quantity.'
        alternative = PublicProblem.parse({'sample_id': problem.sample_id, 'schema_version': problem.schema_version, 'input': changed})
        alt_enrichment = None if enrichment is None else {'public_input': alternative.input, 'notes': enrichment['notes']}
        alt = encoder.encode(alternative, cutoff, mode=mode, enrichment=alt_enrichment)
        alternative_p = projection(torch.tensor([alt.values], dtype=torch.float32))
        warm_started = time.perf_counter()
        warm = encoder.encode(problem, cutoff, mode=mode, enrichment=enrichment)
        warm_elapsed = time.perf_counter() - warm_started
        if not warm.cache_hit or warm.values != encoded.values:
            raise ValueError('frozen E cache round trip failed')
        if any(param.requires_grad or param.grad is not None for param in backend.encoder.parameters()):
            raise ValueError('encoder not frozen')
        record = {'sample_id': problem.sample_id, 'domain': domain, 'split': row['split'],
            'context_mode': mode, 'token_count': encoded.token_count, 'd': layout.d,
            'encoder_l2_norm': float(e.norm()), 'projection_l2_norm': float(p.detach().norm()),
            'projection_gradient_l2_norm': float(projection.linear.weight.grad.norm()),
            'question_perturbation_projection_l2': float((p - alternative_p).detach().norm()),
            'cold_or_existing_cache_seconds': elapsed, 'initial_cache_hit': encoded.cache_hit,
            'warm_cache_seconds': warm_elapsed, 'request_sha256': encoded.request_sha256}
        outcomes.append(record)
        print(json.dumps(record), flush=True)
        save(output / ('encoder-outcomes-' + mode + '.json'), outcomes)
    return {'outcomes': outcomes, 'coverage': encoder.coverage,
        'cuda_peak_allocated_bytes': torch.cuda.max_memory_allocated(),
        'cuda_peak_reserved_bytes': torch.cuda.max_memory_reserved(),
        'gpu': torch.cuda.get_device_name(), 'model_parameters': sum(p.numel() for p in backend.encoder.parameters()),
        'encoder_settings': asdict(backend.settings), 'claim': 'frozen E and untrained P mechanics/sensitivity; no ODE predictions'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('coverage', 'provider', 'encode-base', 'encode-enriched'), required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cache-dir', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'configs/model_context_p02b.json').read_text())
    started = time.perf_counter()
    provenance = {'config_sha256': digest(config), 'source': code_provenance(),
                  'script_sha256': file_hash(__file__), 'python': platform.python_version()}
    if args.mode == 'provider':
        if not config['live_enabled']:
            raise ValueError('live provider disabled')
        result = provider_profile(root, args.output, config)
    else:
        backend = QwenEncoder(args.cache_dir, runtime_versions=config['encoder']['runtime_versions'],
                              load_model=args.mode != 'coverage')
        if args.mode == 'coverage':
            result = selection(root, args.output, backend)
        else:
            result = encoder_profile(root, args.output, config, backend,
                'enriched' if args.mode == 'encode-enriched' else 'public_base_for_offline_audit')
    result.update(wall_seconds=time.perf_counter() - started, provenance=provenance)
    save(args.output / (args.mode + '-summary.json'), result)
    print(json.dumps({'mode': args.mode, 'wall_seconds': result['wall_seconds'], 'status': 'finished'}))


if __name__ == '__main__':
    main()
