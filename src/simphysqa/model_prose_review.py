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

def packets(root,run,output):
    """Future actual model responses, blinded metadata; never invent missing text."""
    from .main_analysis import unique_result
    from html import escape
    root=external(root);run=external(run);output=external(output);plan=read(run/'main-run-plan.json')
    if not list(run.glob('jobs/*/reservations/*.json')):raise ValueError('no executed main responses; cannot create human answer packets from plans')
    preparation=Path(plan['preparation']);mapping=read(root/'private/condition-code-map.json');reverse={v:k for k,v in mapping.items()}
    index=[];links=[]
    for item in read(root/'assignments.json')['items']:
        cid=reverse[item['blind_condition']];sid=item['sample_id'];actual,h=unique_result(run,cid,'enriched',sid,1)
        request=read(preparation/'public'/str(plan['size'])/'enriched'/cid/(sid+'.json'))
        packet={'assessment_id':item['assessment_id'],'sample_id':sid,'blind_condition':item['blind_condition'],
            'public_task_messages':request['messages'],'actual_raw_response':actual['raw_output'] if actual else None,
            'completion_status':actual['completion_status'] if actual else 'missing_or_interrupted_unknown',
            'response_origin':'actual_saved_model_output' if actual else 'unavailable_no_text_substitute',
            'review_scope':'supplied comparison, factual faithfulness, supported interpretation, uncertainty and readable explanation; model metadata blinded'}
        name=item['assessment_id'];retained(output/'packets'/(name+'.json'),packet)
        save_bytes(output/'packets'/(name+'.html'),('<!doctype html><meta charset="utf-8"><title>'+name+'</title><h1>'+name+'</h1><p>Independent model-answer prose review. Metadata blinded; raw text unchanged. Missing response is unavailable, never adequate by default.</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+escape(canonical(packet).decode())+'</pre>').encode())
        index.append({**item,'actual_condition_id':cid,'raw_result_file_sha256':h,'public_request_file_sha256':file_hash(preparation/'public'/str(plan['size'])/'enriched'/cid/(sid+'.json'))})
        links.append('<li><a href="packets/'+name+'.html">'+escape(item['blind_condition']+' / '+sid)+'</a></li>')
    retained(output/'private/source-index.json',index)
    save_bytes(output/'INDEX.html',('<!doctype html><meta charset="utf-8"><h1>Blinded independent prose review</h1><p>Use separate P1/P2 forms before discussion. Raw self-identification, if present, is retained and may unblind; report it separately.</p><ul>'+''.join(links)+'</ul>').encode())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('forms','import','packets'));p.add_argument('--subset',type=Path);p.add_argument('--root',type=Path);p.add_argument('--run',type=Path);p.add_argument('--form',type=Path);p.add_argument('--assessor');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.command=='forms':forms(a.subset,a.output)
    elif a.command=='import':import_submission(a.root,a.form,a.assessor,a.output)
    else:packets(a.root,a.run,a.output)
