"""Create a separate per-domain numerical run from verified P11 public caches.

Does not train or call providers. Budgets apply when the operator starts stages.
"""
import argparse
import shutil
from pathlib import Path
from p10_common import ROOT, Run, load, save, digest, file_hash
from phi_jepa.integration.contracts import PublicProblem, validate_enrichment, enriched_context

DOMAINS = ('driving', 'object_pushing_stacking', 'robotic_arm', 'tethered_load')


def prepare(args, domain):
    native = Path('/home/aashraf/phi-jepa')
    source = native/'p11-tonight-01'
    name = f'{args.name}-{domain}'
    root = native/'manual-runs'/name
    config_path = ROOT/'configs/manual'/f'{name}.json'
    if root.exists() or config_path.exists():
        raise ValueError(f'Already exists: {name}. Resume with run_pipeline.py; do not reinitialize.')
    c = load(ROOT/'configs/qualification_p10.json')
    c.update(run_root=str(root), previous_run=str(source), export_directory=f'docs/reviews/artifacts/manual/{name}',
             domain=domain, reuse_selection=False, provider_enabled=False,
             numerical_updates=args.updates, checkpoint_milestones=sorted({max(1,args.updates//4),max(1,args.updates//2),args.updates}),
             numerical_job_seconds=args.cpu_minutes*60, mixed_horizon_equal_pair_sampling=True,
             context_source_roots=[str(source),str(native/'p10-qualification-01')],
             manual_source_cohort=args.cohort, full_study=False)
    c['caps'] = {'cpu_seconds':args.cpu_minutes*60,'gpu_seconds':args.gpu_minutes*60,'artifact_bytes':args.artifact_gb*10**9,
                 'provider_attempts':0,'provider_input_tokens':0,'provider_output_tokens':0,'provider_usd':0}
    rows = [r for r in load(source/'selected-public.json') if r['domain']==domain and
            (r['split']=='validation' or (r['split']=='train' and (args.cohort=='main' or r['appendix'])))]
    c['training_scenarios'] = len({r['scenario_id'] for r in rows if r['split']=='train'})
    c['validation_scenarios'] = len({r['scenario_id'] for r in rows if r['split']=='validation'})
    assert c['training_scenarios'] == (48 if args.cohort=='main' else 16) and c['validation_scenarios']==8
    assert not ({r['scenario_id'] for r in rows if r['split']=='train'} & {r['scenario_id'] for r in rows if r['split']=='validation'})
    # Check all cached information before creating the new run.
    settings = load(ROOT/'configs/model_context_p02b.json')['encoder']
    prior_settings=load(source/'encoding-report.json')['settings']
    if any(prior_settings.get(k)!=settings[k] for k in ('model','model_revision','tokenizer_revision','pooling','normalization','max_length','precision','embedding_width')):
        raise ValueError('Cached encoder configuration mismatch')
    for r in rows:
        p = PublicProblem.parse(r['public']); notes = load(source/'enrichment'/f'{p.sample_id}.json')
        validate_enrichment(p,notes)
        e = load(source/'embeddings/enriched'/f'{p.sample_id}.json')
        if e['context_sha256'] != digest(enriched_context(p,notes,p.input['observation_cutoff'])) or len(e['values'])!=settings['embedding_width']:
            raise ValueError('Cached public context identity mismatch')
    if args.dry_run:
        print(f'Validated {domain}: {len(rows)} public contexts; would create {config_path}; no writes/training/calls')
        return
    save(config_path,c); run = Run(config_path)
    for r in rows:run.layout().flatten(r['public']['input']['states'][-1],r['public']['input'])
    save(root/'selected-public.json',rows)
    save(root/'selection.json',{'release_identity':run.catalog().identity,'source_selection_sha256':file_hash(source/'selection.json'),
                               'rows':[{k:v for k,v in r.items() if k!='public'} for r in rows]})
    for split in ('train','validation'):
        refs = load(source/'private'/domain/f'{split}-references.json')
        save(root/'private'/f'{split}-references.json',{r['sample_id']:refs[r['sample_id']] for r in rows if r['split']==split})
    for r in rows:
        for relative in (f"enrichment/{r['sample_id']}.json",f"embeddings/enriched/{r['sample_id']}.json"):
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/relative,target)
    save(root/'encoding-report.json',{'settings':settings,'meaning':'Verified reused enriched embeddings; run encode for public-only ablation embeddings.'})
    save(root/'manual-preparation.json',{'source':str(source),'source_selection_sha256':file_hash(source/'selection.json'),
                                      'cohort':args.cohort,'new_provider_calls':0,'new_training_updates':0,
                                      'evaluation_note':'Validation is used for selection; these metrics are not a new sealed-test study.'})
    print(config_path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--name',required=True)
    p.add_argument('--domain',choices=(*DOMAINS,'all'),required=True)
    p.add_argument('--cohort',choices=['main','appendix'],default='main')
    p.add_argument('--updates',type=int,default=4000)
    p.add_argument('--cpu-minutes',type=int,required=True)
    p.add_argument('--gpu-minutes',type=int,required=True)
    p.add_argument('--artifact-gb',type=int,default=5)
    p.add_argument('--dry-run',action='store_true',help='Validate caches and configuration without creating a run')
    args=p.parse_args()
    if not args.name or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for ch in args.name):p.error('name must use lowercase letters, digits, hyphens or underscores')
    if min(args.updates,args.cpu_minutes,args.gpu_minutes,args.artifact_gb)<=0:p.error('budgets/updates must be positive')
    for domain in DOMAINS if args.domain=='all' else [args.domain]:prepare(args,domain)


if __name__=='__main__':main()
