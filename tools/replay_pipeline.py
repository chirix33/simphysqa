"""Manual checkpoint replay. Historical runs are read-only; no paid calls/training."""
import argparse
import json
import time
from pathlib import Path

from p10_common import ROOT, digest, file_hash, guard_deployment_io, load, StateLayout

NATIVE = Path('/home/aashraf/phi-jepa')
RUNS = {'p10': NATIVE/'p10-qualification-01', 'p11': NATIVE/'p11-tonight-01'}
ALIASES = {
    'phi_jepa': 'continued_biasinit_conditioned_full',
    'text_ode': 'continued_biasinit_constant_context_text_ode',
    'lr': 'fixed_projection_lr',
    'rnn': 'continued_constant_context_text_rnn',
    'no_enrichment': 'continued_biasinit_no_enrichment',
    'no_text_conditioning': 'continued_biasinit_no_text_conditioning',
}


class ReadOnlyRun:
    def __init__(self, study, domain, cohort, source=None):
        self.source = source or RUNS[study]
        self.domain = domain
        self.root = self.source/'models'/cohort/domain if study == 'p11' else self.source
        self.c = load(self.source/'config.json') if study == 'p10' else {'solver': {'method': 'rk4', 'substeps': 1}}

    def layout(self):
        manifest = load(ROOT/f'docs/reviews/artifacts/P02a/{self.domain}.state_plus_fixed_conditioning.json')
        return StateLayout.from_manifest(manifest, digest(manifest))

    def embedding(self, sid, mode='enriched'):
        return load(self.source/'embeddings'/mode/f'{sid}.json')['values']


def choose_rows(args):
    if args.study == 'p10' and args.domain != 'tethered_load' and not args.config:
        raise ValueError('P10 comparison checkpoints cover tethered_load only')
    split = args.split or ('test_id' if args.study == 'p11' else 'validation')
    rows = load(args.source_root/'selected-public.json')
    return [r for r in rows if r['public']['input']['domain'] == args.domain
            and r['split'] == split
            and (args.study == 'p10' or args.cohort == 'main' or r['appendix'])]


def output_path(value):
    path = Path(value).expanduser().resolve()
    protected = [*RUNS.values(), ROOT/'docs/reviews/artifacts/P10', ROOT/'docs/reviews/artifacts/P11']
    if any(path.is_relative_to(p.resolve()) for p in protected):
        raise ValueError('Use a new output directory outside historical runs/exports')
    if path.exists():
        raise ValueError('Output already exists; choose a new filename')
    return path


def write_new(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(record, stream, indent=2, allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'forecast', 'generate', 'saved', 'summary'])
    parser.add_argument('--study', choices=RUNS, default='p11')
    parser.add_argument('--domain', choices=['driving', 'object_pushing_stacking', 'robotic_arm', 'tethered_load'], default='tethered_load')
    parser.add_argument('--cohort', choices=['main', 'appendix'], default='main')
    parser.add_argument('--split', choices=['train', 'validation', 'test_id'])
    parser.add_argument('--sample-id')
    parser.add_argument('--index', type=int, default=0)
    parser.add_argument('--methods', nargs='+', default=['phi_jepa'], help='phi_jepa; P10 also text_ode lr rnn no_enrichment no_text_conditioning, or all')
    parser.add_argument('--custom', choices=['coconut', 'codi'])
    parser.add_argument('--output')
    parser.add_argument('--config', type=Path, help='Read a new manual run instead of historical P10/P11')
    args = parser.parse_args()
    if args.config:
        config = load(args.config)
        args.study = 'p10'
        args.domain = config['domain']
        args.source_root = Path(config['run_root'])
    else:
        args.source_root = RUNS[args.study]
    if args.command == 'summary':
        # Explicitly separate evaluator-results view; never called by inference.
        print(json.dumps(load(args.source_root/'evaluation/summary.json'), indent=2))
        return
    guard_deployment_io()
    rows = choose_rows(args)
    if args.command == 'list':
        for i, row in enumerate(rows):
            quantities = ','.join(t['quantity'] for t in row['public']['input']['answer_spec'])
            print(f"{i}\t{row['sample_id']}\t{row['scenario_id']}\t{row['split']}\t{quantities}")
        return
    if args.sample_id:
        matches = [r for r in rows if r['sample_id'] == args.sample_id]
        if not matches: parser.error('Sample is not in the selected domain/cohort/split')
        row = matches[0]
    else:
        if not 0 <= args.index < len(rows): parser.error('Index outside selection; use list first')
        row = rows[args.index]
    sid = row['sample_id']
    source = args.source_root
    if args.command == 'saved':
        paths = list((source/'answers').glob(f'*/{sid}.json'))
        if args.study == 'p11': paths += list((source/'custom').glob(f'*/test_generations/{sid}.json'))
        print(json.dumps({'sample_id': sid, 'meaning': 'Previously saved outputs, not fresh generation',
                         'outputs': {str(p.relative_to(source)): load(p) for p in paths}}, indent=2))
        return
    if not args.output: parser.error('forecast/generate requires --output pointing to a new file')
    destination = output_path(args.output)
    if destination.is_relative_to(source.resolve()):
        parser.error('Replay output must be outside its source run')
    import torch
    torch.set_num_threads(2)
    started = time.time()
    record = {'study': args.study, 'domain': args.domain, 'cohort': args.cohort,
              'sample_id': sid, 'scenario_id': row['scenario_id'], 'split': row['split'],
              'public': row['public'], 'public_sha256': digest(row['public']),
              'training': False, 'provider_calls': 0, 'reference_access': False, 'results': {}}
    if args.command == 'forecast':
        from p10_inference import load_selected, predict
        run = ReadOnlyRun(args.study, args.domain, args.cohort, source)
        methods = list(ALIASES) if args.methods == ['all'] and args.study == 'p10' else ['phi_jepa'] if args.methods == ['all'] else args.methods
        for method in methods:
            if method not in ALIASES or (args.study == 'p11' and method != 'phi_jepa'):
                parser.error('P11 numerical method: phi_jepa. Other numerical baselines: --study p10 --domain tethered_load')
        for method in methods:
            variant = ALIASES[method] if args.study == 'p10' else 'phi_jepa'
            if args.config:
                variant = variant.removeprefix('continued_')
            try:
                model, solver, job = load_selected(run, variant)
                selected = load(run.root/'numerical'/variant/'selected.json')
                result = predict(run, model, solver, job, row)
                result['checkpoint_sha256'] = selected['checkpoint']['sha256']
                result['embedding_sha256'] = (file_hash(source/'embeddings'/job['context_identity']['mode']/f'{sid}.json')
                                              if job['method'] != 'no_text_conditioning' else None)
                del model
            except (ValueError, RuntimeError, FileNotFoundError) as exc:
                result = {'status': 'failure', 'reason': str(exc)}
            record['results'][method] = result
    else:
        if args.study != 'p11' or args.cohort != 'appendix' or not args.custom:
            parser.error('generate requires --study p11 --cohort appendix --custom coconut|codi')
        from transformers import AutoTokenizer
        from phi_jepa.baselines.custom_checkpoint import load_checkpoint
        from phi_jepa.baselines.custom_io import TextCodec, decode_result
        from phi_jepa.integration.contracts import PublicProblem
        from p10_custom import inputs
        folder = source/'custom'/args.custom
        selected = load(folder/'selected.json')
        model, _, _ = load_checkpoint(folder/selected['directory'], identity=load(folder/'identity.json'), device='cuda', training=False)
        settings = load(ROOT/'configs/custom_p06.json')
        codec = TextCodec(AutoTokenizer.from_pretrained(settings['model'], revision=settings['revision'], cache_dir=str(NATIVE/'model-cache'), local_files_only=True))
        token_row = next(r for r in load(source/'custom-public.json') if r['sample_id'] == sid)
        branch = 'coconut' if args.custom == 'coconut' else 'student'
        with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
            ids = model.generate(**inputs(token_row, branch), branch=branch, generation=load(ROOT/'configs/qualification_p10.json')['generation'])[0].tolist()
        result = decode_result(codec, ids, PublicProblem.parse(row['public']), teacher=args.custom == 'coconut')
        eos = codec.tokenizer.eos_token_id in ids
        result.update(token_ids=ids, EOS_terminated=eos, token_cap_termination=not eos and len(ids)-1 >= 2048,
                      checkpoint_sha256=selected['checkpoint']['sha256'], teacher_inference_calls=0)
        record['results'][args.custom] = result
    record['elapsed_seconds'] = time.time()-started
    write_new(destination, record)
    print(json.dumps({'output': str(destination), 'sample_id': sid, 'elapsed_seconds': record['elapsed_seconds'],
                      'results': {m: {'status': v['status'], 'reason': v.get('reason'), 'readout': v.get('readout'), 'answer': v.get('answer')} for m, v in record['results'].items()}}, indent=2))
    if any(v['status'] != 'success' for v in record['results'].values()): raise SystemExit(1)


if __name__ == '__main__':
    main()
