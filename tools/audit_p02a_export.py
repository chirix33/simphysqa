"""Read-only P02a audit. Outputs compact derived evidence, never trajectories."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import platform
import subprocess
import time
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.contracts import DOMAINS
from phi_jepa.integration.layout import StateLayout, rows
from phi_jepa.integration.readers import ReleaseCatalog, file_hash, forecast_states, TrainingSequenceReader

def audit(root, config, output):
    start = time.perf_counter()
    cfg = json.loads(config.read_text())
    source_paths = [*sorted(Path('src/phi_jepa/integration').glob('*.py')),Path(__file__)]
    starting_sources = {str(p):file_hash(p) for p in source_paths}
    starting_config_hash = file_hash(config)
    catalog = ReleaseCatalog(root,cfg['export_index_sha256'],cfg['release_manifest_sha256'])
    checked = catalog.verify_all_checksums(cfg['checksums_sha256'])
    output.mkdir(parents=True,exist_ok=True)
    layouts = {}
    for domain in sorted(DOMAINS):
        problem,_,_ = next(catalog.records(domain,'train'))
        inp = problem.input
        for scope in ('state_only','state_plus_fixed_conditioning'):
            layout = StateLayout.build(inp['states'][-1],inp,scope,'train')
            layouts[domain,scope] = layout
            (output/f'{domain}.{scope}.json').write_bytes(canonical(layout.manifest()))
    results = {}
    groups = {}
    samples = set()
    pair_total = 0
    for domain,split in sorted(catalog.partitions):
        counts = Counter()
        transitions = Counter()
        transition_truth = {}
        local_groups = set()
        lengths = defaultdict(list)
        intervals = Counter()
        boolean_targets = Counter()
        event_types = Counter()
        for problem,ref,identity in catalog.records(domain,split):
            if problem.sample_id in samples: raise ValueError('cross-partition duplicate sample')
            samples.add(problem.sample_id)
            previous = groups.setdefault(identity.group_id,(domain,split))
            if previous != (domain,split): raise ValueError('cross-partition group leakage')
            if identity.scenario_id != identity.group_id: raise ValueError('unexpected scenario/group distinction')
            local_groups.add(identity.group_id)
            inp = problem.input
            states = forecast_states(problem,ref)
            state_layout = layouts[domain,'state_only']
            fixed_layout = layouts[domain,'state_plus_fixed_conditioning']
            for s in inp['states']:
                state_layout.flatten(s,inp)
            # Validate every state; fixed context once plus exact state layout thereafter.
            fixed_layout.flatten(states[0],inp)
            vectors = [state_layout.flatten(s,inp) for s in states]
            for i,(a,b) in enumerate(zip(states,states[1:])):
                key = (identity.group_id,a['timestamp'],b['timestamp'])
                truth = (vectors[i],vectors[i+1])
                if key in transition_truth and transition_truth[key] != truth:
                    raise ValueError('overlapping question horizons disagree on physical transition')
                transition_truth[key] = truth
                transitions[key] += 1
                intervals[format(b['timestamp']-a['timestamp'],'.12g')] += 1
            counts['questions'] += 1
            counts['question_conditioned_pairs'] += len(states)-1
            counts['public_history_states'] += len(inp['states'])
            lengths['context_characters'].append(len(problem.context(inp['observation_cutoff'])))
            lengths['label_characters'].append(len(ref['label']))
            lengths['explanation_characters'].append(len(ref['explanation']))
            for target in inp['answer_spec']:
                if target['answer_type'] == 'boolean': boolean_targets[target['target_id']] += 1
            event_types.update(e['type'] for e in ref['events'])
        expected = catalog.partitions[domain,split]['counts']
        if counts['questions'] != expected['questions'] or len(local_groups) != expected['admitted']:
            raise ValueError('counts disagree with frozen export index')
        results[f'{domain}/{split}'] = dict(counts,scenarios=len(local_groups),unique_transitions=len(transitions),
            transition_multiplicity=dict(Counter(transitions.values())),interval_seconds=dict(intervals),
            boolean_targets=dict(boolean_targets),reference_event_types=dict(event_types),
            lengths={k:{'min':min(v),'max':max(v),'mean':sum(v)/len(v)} for k,v in lengths.items()})
        pair_total += counts['question_conditioned_pairs']
        print(f'{domain}/{split}: {counts["questions"]} questions, {counts["question_conditioned_pairs"]} pairs, {len(transitions)} unique',flush=True)
    totals = {s:sum(v['questions'] for k,v in results.items() if k.endswith('/'+s)) for s in ('train','validation')}
    totals['held_out'] = len(samples)-sum(totals.values())
    if (len(groups),len(samples),totals) != (6340,11105,{'train':6702,'validation':1336,'held_out':3067}):
        raise ValueError('reported admitted totals do not match local export')
    reader_smoke = {}
    for domain in sorted(DOMAINS):
        layout = layouts[domain,cfg['numerical_scope']]
        pair = next(iter(TrainingSequenceReader(catalog,domain,layout,
            duplicate_policy='inverse_transition_multiplicity',context_mode='public_base_for_offline_audit')))
        reader_smoke[domain] = {'pair_id':pair.pair_id,'transition_id':pair.transition_id,
            'registry_sha256':pair.registry_sha256,'provenance_sha256':pair.provenance_sha256,
            'd':len(pair.n_current),'dt':pair.dt,'weight':pair.weight}
    if starting_sources != {str(p):file_hash(p) for p in source_paths} or starting_config_hash != file_hash(config):
        raise ValueError('source/config changed during audit; rerun against stable source')
    result = dict(status='passed',root=str(catalog.root),source_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        python=platform.python_version(),runtime=platform.platform(),config_sha256=file_hash(config),
        source_files={str(p):file_hash(p) for p in sorted(Path('src/phi_jepa/integration').glob('*.py'))},
        audit_script_sha256=file_hash(Path(__file__)),checksummed_files=checked,
        scenarios=len(groups),questions=len(samples),question_partitions=totals,
        all_partitions_candidate_pairs=pair_total,partitions=results,
        active_scope=cfg['numerical_scope'],training_reader_real_export_smoke=reader_smoke,
        candidate_dimensions={d:{s:layouts[d,s].d for s in ('state_only','state_plus_fixed_conditioning')} for d in sorted(DOMAINS)},
        token_lengths='not_measured: no selected tokenizer downloaded or called',
        weighting='proposed inverse transition multiplicity, retaining each question context',
        validation_test_mode='evaluator-only recorded-state diagnostics; not autonomous forecasts',
        wall_seconds=time.perf_counter()-start)
    (output/'export-audit.json').write_bytes(canonical(result))
    hashes={p.name:file_hash(p) for p in sorted(output.glob('*.json')) if p.name!='CHECKSUMS.json'}
    (output/'CHECKSUMS.json').write_bytes(canonical(hashes))
    print(json.dumps({k:v for k,v in result.items() if k in ('status','scenarios','questions','question_partitions','wall_seconds','checksummed_files')},indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=Path('configs/model_training_p02a.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/reviews/artifacts/P02a'))
    args=parser.parse_args()
    audit(args.root,args.config,args.output)
