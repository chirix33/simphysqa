"""Blank blinded model-answer assessment forms and immutable submission import."""
from pathlib import Path
import argparse,csv,io,random
from .io import read,write,external,canonical,digest
from .formal_sampling import save_bytes,file_hash
from .spq01a import retained

COLUMNS=['assessor_id','assessment_id','sample_id','blind_condition','judgment','criterion_findings','error_categories','source_locations','claim_excerpts','comments']

def forms(subset,output):
    output=external(output);plan=read(subset);conditions=sorted(plan['conditions']);random.Random(20261009).shuffle(conditions)
    mapping={c:'M'+str(i+1).zfill(2) for i,c in enumerate(conditions)}
    retained(output/'private/condition-code-map.json',mapping);assignments=[]
    for item in plan['items']:
        for c in conditions:
            assignments.append({'assessment_id':'PROSE-'+digest({'sample_id':item['sample_id'],'condition':mapping[c]})[:16],
                'sample_id':item['sample_id'],'blind_condition':mapping[c],'source_private_record':item['private_record']})
    retained(output/'assignments.json',{'version':'SPQ06-model-prose-forms/1.0.0','subset_sha256':file_hash(subset),
        'items':assignments,'unique_qa_items':len(plan['items']),'conditions':len(conditions),'judgments_collected':0})
    for rid in ('P1','P2'):
        stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=COLUMNS,lineterminator='\n');writer.writeheader()
        for item in assignments:writer.writerow({**{k:item[k] for k in ('assessment_id','sample_id','blind_condition')},'assessor_id':rid})
        save_bytes(output/(rid+'.csv'),stream.getvalue().encode())
    print(canonical({'unique_tasks':len(plan['items']),'responses':len(assignments),'blank_assignments':len(assignments)*2,'collected':0}).decode())

def import_submission(root,form,rid,output):
    root=external(root);output=external(output);source=Path(form);blob=source.read_bytes();stream=io.StringIO(blob.decode('utf-8-sig'))
    reader=csv.DictReader(stream)
    if reader.fieldnames!=COLUMNS or rid not in ('P1','P2'):raise ValueError('form header/assessor identity mismatch')
    rows=list(reader);known={i['assessment_id']:i for i in read(root/'assignments.json')['items']}
    if len(rows)!=len(known) or len({r['assessment_id'] for r in rows})!=len(rows):raise ValueError('missing/duplicated assessment rows')
    collected=[]
    for r in rows:
        item=known.get(r['assessment_id'])
        if not item or r['assessor_id']!=rid or any(r[k]!=item[k] for k in ('sample_id','blind_condition')):raise ValueError('frozen assessment identity differs')
        if not r['judgment']:
            if any(r[k] for k in COLUMNS[5:]):raise ValueError('findings without primary judgment')
            continue
        if r['judgment'] not in ('adequate','material_error'):raise ValueError('unknown primary judgment')
        if r['judgment']=='material_error' and not all(r[k] for k in ('criterion_findings','error_categories','source_locations','claim_excerpts','comments')):raise ValueError('material finding lacks evidence')
        collected.append(r)
    save_bytes(output/'submissions'/rid/(file_hash(source)+'.csv'),blob)
    retained(output/'imports'/(rid+'-'+file_hash(source)+'.json'),{'assessor_id':rid,'submission_sha256':file_hash(source),'collected':len(collected),
        'missing':len(rows)-len(collected),'independent_rows':collected,'policy':'discussion/adjudication/rubric revisions separate; no frozen-output changes'})
    print(canonical({'collected':len(collected),'missing':len(rows)-len(collected)}).decode())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('forms','import'));p.add_argument('--subset',type=Path);p.add_argument('--root',type=Path);p.add_argument('--form',type=Path);p.add_argument('--assessor');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.command=='forms':forms(a.subset,a.output)
    else:import_submission(a.root,a.form,a.assessor,a.output)
