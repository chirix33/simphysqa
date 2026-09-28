"""Persist a small mock-provider review set, not an empirical evaluation."""
import json
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_clarification import fixture,MockProvider,reply,review
from phi_jepa.inference.clarification import AttemptStore,ClarificationService
from phi_jepa.clarification_evaluation import evaluate_interaction,summarize_interactions
from phi_jepa.integration.readers import file_hash


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=ROOT/'docs/reviews/artifacts/P09_clarification')
    root=parser.parse_args().output
    root.mkdir(parents=True,exist_ok=True)
    p,f,rows,answer,request=fixture(); records=[]
    cases=[('useful','usable','BC means the boundary-crossing target already specified.'),
           ('no_question',None,None),('unavailable','unavailable',None),
           ('conflict','conflicting','The old public description is wrong, but also do not change it.'),
           ('changed_physical','changed_physical_assumptions','Change the support acceleration to twice the original value.'),
           ('supplied_outcome','outcome_supplying','I observed that the final boundary-crossing value is true.'),
           ('changed_task','changed_task_or_answer_definition','Use a new boundary threshold and answer at another time.'),
           ('unusable','unusable','I cannot interpret BC.'),
           ('unanswered',None,None),('failed_refinement','usable','BC means the boundary-crossing target already specified.')]
    for name,category,text in cases:
        refined=json.loads(json.dumps(answer)); refined['plain_text_answer']='The scripted reply clarified the abbreviation BC. The original sampled prediction and its limitations are unchanged.'
        provider=MockProvider([{'answer':answer,'clarification_request':None if name=='no_question' else request},
            TimeoutError('fixture timeout') if name=='failed_refinement' else refined])
        store=AttemptStore(root/'sessions'); service=ClarificationService(store,provider)
        snapshot=service.start(name,p,f,rows,mode='scripted_demo')
        if category:
            r=reply(text,mode='scripted_demo'); service.submit_reply(name,r)
            snapshot=service.review_and_refine(name,review(r,category))
        # Expected software routing labels are authored independently of mock
        # output; they are NOT independent scientific relevance/accuracy labels.
        row=evaluate_interaction(snapshot,task_sha256=snapshot['records']['created']['task_sha256'],
            review={'reviewer_id':'software-fixture-author','label_source':'software_fixture',
                    'trigger_relevant':None,'unnecessary_question':None,'reply_grounded':None})
        expected={'useful':'refined','no_question':'answered_without_clarification',
            'unavailable':'unresolved_reply_unavailable','conflict':'unresolved_conflicting_reply',
            'changed_physical':'reforecast_required','supplied_outcome':'unresolved_outcome_supplied',
            'changed_task':'revised_task_required','unusable':'unresolved_unusable_reply',
            'unanswered':'awaiting_reply','failed_refinement':'unresolved_refinement_failure'}[name]
        assert snapshot['status']==expected
        row['fixture_case']=name; row['expected_route']=expected
        records.append(row)
        (root/f'{name}.json').write_text(json.dumps({'evidence_kind':'software_fixture_only',
            'independently_reviewed_scientific_example':False,'snapshot':snapshot,'provider_payloads':provider.calls},indent=2)+'\n')
    (root/'evaluation.json').write_text(json.dumps({'rows':records,'summary':summarize_interactions(records),
        'empirical_answer_accuracy':None,'paid_calls':0,'independently_reviewed_examples':0},indent=2)+'\n')
    files={str(p.relative_to(root)):file_hash(p) for p in root.rglob('*.json') if p.name!='manifest.json'}
    (root/'manifest.json').write_text(json.dumps({'kind':'software_fixtures','files':files,'new_training':0,'paid_calls':0},indent=2)+'\n')
    print(json.dumps({'cases':len(records),'statuses':{r['fixture_case']:r['status'] for r in records}}))


if __name__=='__main__': main()
