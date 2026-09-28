"""Run-local public enrichment and frozen embedding preparation; no training."""
from dataclasses import asdict
from p10_common import ROOT, load, save, digest, guard_deployment_io, QualificationBudget
from replay_pipeline import RUNS, NATIVE
from phi_jepa.integration.contracts import PublicProblem, validate_enrichment, enriched_context

ENCODER_KEYS = ('model', 'model_revision', 'tokenizer_revision', 'pooling', 'normalization', 'max_length', 'precision', 'embedding_width')


def modes(config, row):
    requested = set(config['methods']) - {'vanilla_llm', 'no_text_conditioning'}
    if row['domain'] != 'tethered_load' and not config.get('training_config'):
        requested &= {'phi_jepa', 'coconut', 'codi'}
    return (['enriched'] if requested - {'no_enrichment'} else []) + (['public_base_for_offline_audit'] if 'no_enrichment' in requested else [])


def enrich(output):
    from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.cache import FrozenOutputCache
    c = load(output/'config.json'); settings = load(ROOT/'configs/model_context_p02b.json')
    key = load_openai_key(ROOT/'.env') if c['caps']['provider_usd'] > 0 else None
    guard_deployment_io(); budget = QualificationBudget(output, c)
    for row in load(output/'selection.json'):
        if 'enriched' not in modes(c, row): continue
        p = PublicProblem.parse(row['public']); sid = p.sample_id
        dest = output/'context/enrichment'/f'{sid}.json'
        failure = output/'context/failures'/f'{sid}.json'
        if dest.exists() or failure.exists(): continue
        try:
            reused = False
            for source in RUNS.values():
                path = source/'enrichment'/f'{sid}.json'
                if path.exists():
                    notes = load(path); validate_enrichment(p, notes); save(dest, notes); reused = True; break
            if reused: continue
            if key is None: raise ValueError('missing_enrichment_cache_requires_positive_api_budget')
            pc = {**settings['enrichment_provider'], 'max_attempts_per_request': 1}
            obj = OpenAIEnrichment(key, pc, load(ROOT/settings['enrichment_asset']),
                    FrozenOutputCache(output/'context/provider_cache'),
                    event_sink=lambda value, sid=sid: save(output/'context/provider_ledgers'/f'{sid}.json', value))
            obj.transport = budget.transport(obj._http)
            save(dest, obj.enrich(p, p.input['observation_cutoff']))
        except Exception as exc:
            save(failure, {'status': 'context_unavailable', 'reason': budget.read().get('stopped') or str(exc)})


def encode(output):
    from phi_jepa.providers.context import ContextEncoder
    from phi_jepa.providers.qwen import QwenEncoder
    from phi_jepa.providers.cache import FrozenOutputCache
    guard_deployment_io()
    c = load(output/'config.json'); expected = load(ROOT/'configs/model_context_p02b.json')['encoder']
    root = output/'context'; backend = None
    # Same pinned identity as selected checkpoints; actual backend settings are
    # recorded if local encoding is needed. All statistics/weights stay frozen.
    recorded = load(RUNS['p11']/'encoding-report.json')['settings']
    if any(recorded[k] != expected[k] for k in ENCODER_KEYS): raise ValueError('encoder_identity_changed')
    save(root/'encoding-report.json', {'settings': recorded})
    for row in load(output/'selection.json'):
        p = PublicProblem.parse(row['public']); sid = p.sample_id
        for mode in modes(c, row):
            dest = root/'embeddings'/mode/f'{sid}.json'; failure = root/'failures'/f'{sid}-{mode}.json'
            if dest.exists() or failure.exists(): continue
            try:
                notes = load(root/'enrichment'/f'{sid}.json') if mode == 'enriched' else None
                text = enriched_context(p, notes, p.input['observation_cutoff']) if notes else p.context(p.input['observation_cutoff'])
                reused = False
                for source in RUNS.values():
                    path = source/'embeddings'/mode/f'{sid}.json'
                    if not path.exists(): continue
                    settings = load(source/'encoding-report.json')['settings']; cached = load(path)
                    if any(settings[k] != expected[k] for k in ENCODER_KEYS) or cached['context_sha256'] != digest(text): continue
                    save(dest, cached); reused = True; break
                if reused: continue
                if backend is None:
                    backend = QwenEncoder(str(NATIVE/'model-cache'), runtime_versions=expected['runtime_versions'])
                    encoder = ContextEncoder(backend, FrozenOutputCache(root/'embedding_cache'))
                    save(root/'encoding-report.json', {'settings': asdict(backend.settings)})
                value = encoder.encode(p, p.input['observation_cutoff'], mode=mode, enrichment=notes)
                save(dest, asdict(value))
            except Exception as exc:
                save(failure, {'status': 'context_unavailable', 'reason': str(exc)})
