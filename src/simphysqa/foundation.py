"""Read-only foundation inventory of accepted external exports. No generation or calls."""
import argparse
from collections import Counter
import csv
from hashlib import sha256
from pathlib import Path
from .io import ROOT, DOMAINS, canonical, digest, external, parse, read
from .spq01a import retained, verify_manifest


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


def inventory(artifacts, config_path=ROOT/'configs/simphysqa/development_artifacts.json', full_validation=False):
    config=read(config_path); artifacts=Path(artifacts).resolve()
    exclusions=read(ROOT/config['formal_exclusions'])
    excluded=exclusions['excluded_groups']
    if len(excluded)!=len(set(excluded)) or len(excluded)!=config['expected_excluded_groups']:
        raise ValueError('formal exclusion cardinality/uniqueness')
    items=[]; manifests={}; requests=0; continuations=0; blank_counts=Counter()
    conditions={c['condition_id'] for c in read(ROOT/'configs/simphysqa/evaluation.json')['conditions']}
    if len(conditions)!=config['expected_conditions']:raise ValueError('condition allocation')
    for alias,relative in config['roots'].items():
        root=artifacts/relative; info=verify_manifest(root)
        manifests[alias]={'path':relative,'manifest_sha256':file_hash(root/'manifest.json'),
                          'versions':info['versions']}
        packet_info=verify_manifest(root/'audit-development')
        assignments={a['sample_id']:a for a in packet_info['assignments']}
        records=[parse(line) for line in (root/'organizer-private/qa-records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        ids={r['sample_id'] for r in records}
        if len(records)!=len(ids) or ids!=set(assignments):raise ValueError('record/packet identity')
        for reviewer in ('R1','R2','R3'):
            with (root/f'audit-development/forms/{reviewer}.csv').open(newline='',encoding='utf-8') as stream:
                rows=list(csv.DictReader(stream))
            if len(rows)!=len(ids) or {r['sample_id'] for r in rows}!=ids:raise ValueError('form identity')
            for row in rows:
                if row['reviewer_id']!=reviewer or row['phase']!='development' or any(row[k] for k in ('judgment','criteria','error_categories','notes')):
                    raise ValueError('reviewer form is not independent blank development material')
            blank_counts[reviewer]+=len(rows)
        paths=[p for p in (root/'public-requests').glob('*.json') if p.name!='manifest.json']
        if {p.stem for p in paths}!=conditions:raise ValueError('missing prepared condition')
        for path in paths:
            prepared=read(path)
            if len(prepared)!=len(ids) or {q['sample_id'] for q in prepared}!=ids or any(q['tools']!=[] for q in prepared):
                raise ValueError('prepared request identity or tools')
            requests+=len(prepared)
        if alias=='clarifications':
            templates=list((root/'continuation-templates').glob('*.json'))
            if {p.stem for p in templates}!=conditions:raise ValueError('missing continuation condition')
            for path in templates:
                values=read(path)
                if len(values)!=len(ids) or {v['sample_id'] for v in values}!=ids:raise ValueError('continuation identity')
                continuations+=len(values)
        for record in records:
            if full_validation:
                from .dataset import validate
                validate(record)
            sid=record['sample_id']; group=record['trajectory_id']; metadata=record['private']['metadata']
            if group not in excluded or metadata['split_group_id']!=group:raise ValueError('group/exclusion changed')
            packet=assignments[sid]['packet_id']; initial='public-initial' if alias=='clarifications' else 'public-items'
            rels={'organizer_record':f'organizer-private/items/{sid}.json','public_view':f'{initial}/{sid}.json',
                  'audit_packet':f'audit-development/packets/{packet}.html'}
            if alias=='clarifications':rels['resolved_public_view']=f'public-resolved/{sid}.json'
            for value in rels.values():
                if value not in info['files']:raise ValueError('unmanifested indexed artifact')
            if canonical(read(root/rels['organizer_record']))!=canonical(record):raise ValueError('item/aggregate differs')
            inp=record['public']['input']
            cutoff=max(s['timestamp'] for s in inp['states'])
            if cutoff!=0.2:raise ValueError('established development observation cutoff changed')
            items.append({'sample_id':sid,'family':record['question_type'],'domain':inp['domain'],
                'group_id':group,'split':metadata['split'],'observation_cutoff_s':cutoff,
                'fresh_formal_excluded':True,'artifact_root':alias,'paths':rels,
                'sha256':{key:info['files'][value] for key,value in rels.items()},
                'record_sha256':digest(record),'human_assessment':'uncollected'})
    families=dict(Counter(i['family'] for i in items))
    if families!=config['expected_families'] or len({i['sample_id'] for i in items})!=56:raise ValueError('56-family identity allocation')
    if len({i['group_id'] for i in items})!=config['expected_groups']:raise ValueError('engineering group allocation')
    for domain in DOMAINS:
        if Counter(i['family'] for i in items if i['domain']==domain)!={'direct':4,'predictive':4,'counterfactual':2,'explanation':2,'clarification':2}:
            raise ValueError('domain allocation')
    if requests!=504 or continuations!=72 or dict(blank_counts)!={'R1':56,'R2':56,'R3':56}:raise ValueError('delivery allocation')
    return {'version':config['version'],'accepted_commit':config['accepted_commit'],
        'config_sha256':file_hash(config_path),'roots':config['roots'],'support':config['support'],
        'manifests':manifests,'formal_exclusions':exclusions,'items':sorted(items,key=lambda i:(i['domain'],i['family'],i['sample_id'])),
        'counts':{'items':56,'families':families,'groups':16,'domains':4,'formal_excluded_groups':20,
                  'prepared_initial_requests':requests,'conditional_templates':continuations,'blank_forms_per_reviewer':dict(blank_counts)},
        'population':'engineering development; not release-wide quality or OOD estimate',
        'formal_sample_exported':False,'executed_answering_interactions':0}


def markdown(index, artifacts):
    artifacts=Path(artifacts).resolve()
    lines=['# Authoritative development index — foundation/1.0.0','',
        '56 accepted engineering items across five families; 16 groups, all excluded from fresh formal sampling. '
        'Gold records and auditor packets are private. This index is organizer material, not model input.',
        '', 'Artifact aliases resolve below this machine root: `'+str(Path(artifacts).resolve())+'`. '
        'Portable relative aliases and per-file hashes are in development-index.json.', '',
        '| Domain | Family | Sample identity | Group / split | Public view | Private audit packet |',
        '|---|---|---|---|---|---|']
    for i in index['items']:
        root=Path(artifacts)/index['roots'][i['artifact_root']]
        pub=(root/i['paths']['public_view']).as_posix(); packet=(root/i['paths']['audit_packet']).as_posix()
        lines.append(f"| {i['domain']} | {i['family']} | {i['sample_id']} | {i['group_id']} / {i['split']} | [view]({pub}) | [packet]({packet}) |")
    lines+=['','All cutoffs remain 0.2 s. Three reviewer forms per export collectively cover 56 items each; all ratings remain blank.',
            '504 initial requests and 72 conditional continuation templates are prepared; no answering interaction has executed.', '',
            '## Export roots and versions','']
    for alias,value in index['manifests'].items():
        lines.append(f"- {alias}: `{value['path']}`; manifest SHA256 `{value['manifest_sha256']}`; versions `{value['versions']}`.")
    lines+=['','## Supporting artifact locations','']
    lines += [f'- {key}: `{value}`.' for key,value in index['support'].items()]
    lines+=['','## Fresh-formal exclusions','',
            '20 groups: four SPQ00 inspected groups plus sixteen SPQ01 engineering groups. Later families reuse these groups. '
            'Calibration/formal remain disjoint, with group-disjoint development exclusions. Group-then-question previews estimate a trajectory-balanced population.', '']
    lines += ['- `'+g+'`.' for g in index['formal_exclusions']['excluded_groups']]
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--validate-records',action='store_true')
    args=parser.parse_args(); index=inventory(args.artifacts,full_validation=args.validate_records)
    output=external(args.output)
    retained(output/'development-index.json',index)
    from .answer_export import retained_bytes
    retained_bytes(output/'development-index.md',markdown(index,args.artifacts).encode())
    print(canonical(index['counts']).decode(),end='')


if __name__=='__main__':main()
