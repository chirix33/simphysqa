"""Readable focused primary pages from exact exported fields; no model/simulation."""
import argparse
from html import escape
from pathlib import Path
from simphysqa.io import canonical,read,external
from simphysqa.formal_live import execution_plan
from simphysqa.formal_scope import formal_scope
from simphysqa.formal_delivery import packet_for
from simphysqa.formal_sampling import save_bytes


def pre(value):return '<pre>'+escape(canonical(value).decode())+'</pre>'
def details(title,value):return '<details><summary>'+escape(title)+'</summary>'+pre(value)+'</details>'
def plain(value):return escape(value) if isinstance(value,str) else escape(canonical(value).decode().strip())
STYLE='body{max-width:1100px;margin:2em auto;font:17px system-ui;line-height:1.45}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #ccc;padding:.4em;text-align:left}article{border-top:2px solid #aaa;margin-top:2em;padding-top:1em}details{margin:.7em 0}code{overflow-wrap:anywhere}.event{background:#f5f6f8;padding:1em;margin:.8em 0}a{color:#1853a8}'


def item(packet):
    inp=packet['structured_inputs'];lang=packet['language_annotations'];family=packet['question_type'];pid=packet['packet_id']
    body='<p><a href="../review-index.html">All audit items</a> · <a href="../reviewer-guide.md">Guide</a></p><h1>'+pid+'</h1>'
    body+='<p>'+plain(inp['domain'])+' / '+family+' · sample '+plain(packet['sample_id'])+' · group '+plain(packet['verification']['metadata']['split_group_id'])+' · split '+plain(packet['verification']['metadata']['split'])+'</p>'
    body+='<h2>Question and canonical type</h2><p>'+plain(packet['qa']['question'])+'</p><p>Canonical question_type: <strong>'+family+'</strong></p>'
    if family=='explanation':
        body+='<h3>Intentionally supplied comparison outcomes</h3><p>These are separately supplied explanation-task inputs. They are not observed prefix states.</p>'+pre(inp['supplied_comparison'])+details('Explanation task declarations',inp['explanation_task'])
    if family=='counterfactual':body+=details('Counterfactual task declaration',inp['counterfactual'])
    if family=='clarification':
        stages=packet['two_stage_task']
        body+='<h3>Initial question/view</h3><p>'+plain(stages['initial_view']['input']['question'])+'</p>'+details('Complete initial public view',stages['initial_view'])
        body+='<h3>Authored reference clarification</h3><p>'+plain(stages['reference_clarification_question'])+'</p><p>Authored reference; no answering-model conversation was executed.</p>'
        body+='<h3>Recorded authored reply</h3>'+pre(stages['recorded_reply'])
        body+='<h3>Resolved question/view</h3><p>'+plain(stages['resolved_view']['input']['resolved_question'])+'</p>'+details('Complete resolved public view',stages['resolved_view'])
    body+='<h2>Physical/global context</h2><p>'+plain(inp['global_context'])+'</p>'
    body+='<p>Observation cutoff: '+plain(inp['observation_cutoff'])+' s. Coordinate convention: '+plain(inp['coordinate_convention'])+'</p>'
    body+='<h2>Observed-window trajectory language</h2><p>'+plain(lang['trajectory']['text'])+'</p>'+details('Trajectory source bindings and status',lang['trajectory'])
    body+='<h2>Original declarations supporting descriptions</h2><p>Declared schedules are not proof of observed application or causal effects.</p>'+details('Original event schedule / known_events',inp['known_events'])+details('Controller declarations',inp['controller'])+details('Entities and physical properties',inp['entities'])
    by_state={t['state_id']:t for t in lang['timestamps']}
    body+='<h2>Every saved public state</h2>'
    for state in inp['states']:
        sentence=by_state[state['state_id']]
        body+='<article><h3>'+plain(state['timestamp'])+' s · '+plain(state['state_id'])+'</h3>'
        body+='<h4>Generated timestamp language</h4><p>'+plain(sentence['text'])+'</p>'+details('Timestamp language bindings and status',sentence)
        body+='<h4>Original state.context</h4><p>'+plain(state['context'])+'</p>'
        body+='<h4>Linked events at this state</h4>'
        if not state['linked_events']:body+='<p>No linked events. This state is retained.</p>'
        for event in state['linked_events']:
            body+='<section class="event"><p><strong>'+plain(event['temporal_relationship'])+'</strong> · '+plain(event['event_type'])+' · description status '+plain(event['event_description_status'])+'</p><p>'+plain(event['event_description'])+'</p><p>event_id: '+plain(event['event_id'])+' · link_id: '+plain(event['link_id'])+'</p><p>Targets: '+plain(event['target_entity_ids'])+'</p>'+details('Complete linked event, matching and description bindings',event)+'</section>'
        body+='<details><summary>All relevant measurements (exact typed source values, units and frames)</summary><table><tr><th>Entity</th><th>Quantity</th><th>Value</th><th>Unit</th><th>Frame</th></tr>'
        for m in state['measurements']:body+='<tr>'+''.join('<td>'+plain(m[k])+'</td>' for k in ('entity_id','name','value','unit','frame'))+'</tr>'
        body+='</table></details>'+details('All original relations',state['relations'])+'</article>'
    body+='<h2>Source and extra evidence</h2><p><a href="../focused-items/'+pid+'.json">Focused machine-readable extraction</a> · <a href="../public-items/'+packet['sample_id']+'.json">Exact public model view</a></p><p><a href="../auditor-only/'+pid+'.html">Auditor-only gold and private verification</a> (optional corroboration outside primary scope)</p>'
    return ('<!doctype html><meta charset="utf-8"><title>'+pid+'</title><style>'+STYLE+'</style>'+body).encode()


def build(run,output):
    output=external(output);plan=execution_plan(run);links=[]
    with formal_scope(plan['candidates'],plan['excluded_groups']):
        for c in plan['candidates']:
            case=run/'cases'/c['candidate_id']
            if not (case/'status.json').exists() or read(case/'status.json')['status']!='completed':continue
            packet,_=packet_for(read(case/'record.json'));pid=packet['packet_id']
            save_bytes(output/'review-pages'/(pid+'.html'),item(packet))
            links.append('<li><a href="review-pages/'+pid+'.html">'+plain(c['cell']+' / '+pid)+'</a></li>')
    ready=len(links)==140
    body='<h1>SPQ05 focused human audit</h1><p>'+('140 frozen distinct QA. R1, R2 and R3 independently inspect this same140-item list;420 individual ratings. Reviewer identity mapping is not assumed.' if ready else str(len(links))+'/140 complete items; formal review cannot begin.')+'</p>'
    body+='<p>Primary scope: physical/global context, observed trajectory language, question wording/type, generated timestamp language and state-event descriptions. Gold answers and private traces/outcomes remain separate optional corroboration. Generator identity is blinded.</p><p>Independent original submissions precede discussion. Blank forms are uncollected. Do not edit frozen packets. No model performance, agreement or acceptance is claimed. Results concern this balanced audit design, not natural record-weighted release quality; seven items/cell do not power subgroup claims.</p><p><a href="reviewer-guide.md">Reviewer guide</a> · <a href="analysis-specification.md">Analysis specification</a> · <a href="focused.json">JSON extraction</a> · <a href="focused.jsonl">JSONL extraction</a> · <a href="rating-import-commands.txt">Import commands</a></p>'
    if ready:body+='<p>Separate blank forms: <a href="forms/R1.csv">R1</a> · <a href="forms/R2.csv">R2</a> · <a href="forms/R3.csv">R3</a>. Each contains identical140 assignments.</p>'
    body+='<ul>'+''.join(links)+'</ul>'
    save_bytes(output/'review-index.html',('<!doctype html><meta charset="utf-8"><title>SPQ05 primary review</title><style>'+STYLE+'</style>'+body).encode())
    print(canonical({'readable_pages':len(links),'final140_pending_manifest_verification':ready,'new_calls':0}).decode())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.run,a.output)
