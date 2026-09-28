"""Software fixtures only. Mock completions are not empirical clarification evidence."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from test_p04a import example, llm_result, replace_input
from phi_jepa.artifacts import digest
from phi_jepa.inference.readout import read_targets, NUMERIC_RULE
from phi_jepa.inference.clarification import (AttemptStore, ClarificationService,
    Completion, Reply, ReplyReview, validate_request, ROUTES)
from phi_jepa.providers.contracts import Usage
from phi_jepa.providers.clarification import FrozenClarificationAnswer
from phi_jepa.clarification_evaluation import evaluate_interaction, summarize_interactions, evaluate_original_reference

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    p,f=example(); inp=p.input
    inp['question']='Explain load position and BC at the requested time; BC is an undefined abbreviation in this wording.'
    numeric=deepcopy(inp['answer_spec'][0]); numeric.update(target_id='load:position',quantity='position',answer_type='vector',unit='m',rule_definition=NUMERIC_RULE)
    inp['answer_spec'].append(numeric); p=replace_input(p,inp)
    rows=read_targets(p,f); answer=llm_result(p,rows)
    request={'missing_or_ambiguous_information':'What BC abbreviates in the public question.',
        'affected_target_ids':[inp['answer_spec'][0]['target_id']],
        'resolution_rationale':'Clarifies the wording of the explanation without altering the already specified event or its value.',
        'question':'Does BC refer to the boundary-crossing target already listed?',
        'public_evidence_paths':['/public_problem/input/question','/public_problem/input/answer_spec/0'],
        'readout_evidence_target_ids':[inp['answer_spec'][0]['target_id']]}
    return p,f,rows,answer,request


class MockProvider:
    identity={'kind':'software_fixture','model':'mock_frozen_answer','version':1}
    def __init__(self, values): self.values=list(values); self.calls=[]
    def complete(self, stage, original, context):
        self.calls.append({'stage':stage,'original':deepcopy(original),'context':deepcopy(context)})
        value=self.values.pop(0)
        if isinstance(value,BaseException): raise value
        if isinstance(value,Completion): return value
        return Completion(json.dumps(value),Usage(10,20,0.),'mock-response','mock_frozen_answer')


def reply(text='BC means the boundary-crossing target already specified.', mode='actual_interactive'):
    return Reply(text,'actual_user' if mode=='actual_interactive' else 'scripted_demo','fixture-user','fixture-message','2026-09-25T12:00:00+00:00','software_fixture')


def review(r,category='usable'):
    return ReplyReview(category,'Synthetic human-review fixture for routing behavior.','fixture-reviewer','2026-09-25T12:01:00+00:00',r.text,
        category!='changed_task_or_answer_definition',category!='changed_physical_assumptions',category!='conflicting',category!='outcome_supplying',category=='usable')


class ClarificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store=AttemptStore(self.tmp.name); self.p,self.f,self.rows,self.answer,self.req=fixture()

    def start(self,values=None,mode='actual_interactive'):
        self.provider=MockProvider(values or [{'answer':self.answer,'clarification_request':self.req},self.answer])
        self.service=ClarificationService(self.store,self.provider)
        return self.service.start('attempt',self.p,self.f,self.rows,mode=mode)

    def test_useful_reply_two_calls_immutable_evidence_and_separate_records(self):
        before=self.start(); r=reply(); self.service.submit_reply('attempt',r)
        refined=deepcopy(self.answer); refined['plain_text_answer']='The user clarified that BC means boundary crossing; the original prediction is unchanged.'
        self.provider.values=[refined]
        after=self.service.review_and_refine('attempt',review(r))
        self.assertEqual(after['status'],'refined'); self.assertEqual(after['call_attempts'],2)
        self.assertEqual(after['total_usage'],{'input_tokens':20,'output_tokens':40,'cost_usd':0.})
        for key in ('original','initial_answer','clarification_request'):
            self.assertEqual(before['records'][key],after['records'][key])
        self.assertNotEqual(after['records']['initial_answer'],after['records']['refined_answer'])
        self.assertEqual(self.provider.calls[0]['original'],self.provider.calls[1]['original'])
        self.assertEqual(self.provider.calls[1]['context']['reply']['source'],'actual_user')
        self.assertNotIn('reference',self.provider.calls[1]['original'])

    def test_no_question_no_refinement(self):
        result=self.start([{'answer':self.answer,'clarification_request':None}])
        self.assertEqual(result['status'],'answered_without_clarification')
        with self.assertRaises(ValueError): self.service.submit_reply('attempt',reply())
        self.assertEqual(len(self.provider.calls),1)

    def test_all_nonusable_categories_route_without_second_call(self):
        for category,status in ROUTES.items():
            if category=='usable': continue
            with self.subTest(category=category),tempfile.TemporaryDirectory() as temp:
                s=ClarificationService(AttemptStore(temp),MockProvider([{'answer':self.answer,'clarification_request':self.req}]))
                s.start('a',self.p,self.f,self.rows)
                r=reply(None if category=='unavailable' else 'A reply whose interpretation requires recorded human review.')
                s.submit_reply('a',r); result=s.review_and_refine('a',review(r,category))
                self.assertEqual(result['status'],status); self.assertEqual(result['call_attempts'],1)

    def test_raw_free_text_waits_for_review_no_keyword_guess(self):
        self.start(); result=self.service.submit_reply('attempt',reply('Actually change everything; this is usable clarification!'))
        self.assertEqual(result['status'],'awaiting_reply_review'); self.assertEqual(result['call_attempts'],1)

    def test_usable_requires_all_recorded_attestations_and_exact_quote(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r)
        for bad in (replace(review(r),no_supplied_outcome=False),replace(review(r),reply_quote='not in reply'),replace(review(r),preserves_task=1)):
            with self.assertRaises(ValueError): self.service.review_and_refine('attempt',bad)
        self.assertEqual(self.store.snapshot('attempt')['call_attempts'],1)

    def test_one_reply_one_refinement_across_restarts(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r)
        service=ClarificationService(AttemptStore(self.tmp.name),self.provider)
        with self.assertRaises(ValueError): service.submit_reply('attempt',r)
        service.review_and_refine('attempt',review(r))
        with self.assertRaises(ValueError): service.review_and_refine('attempt',review(r))
        with self.assertRaises(FileExistsError): service.start('attempt',self.p,self.f,self.rows)
        self.assertEqual(len(self.provider.calls),2)

    def test_question_must_have_exact_public_grounding_and_affected_target(self):
        original={'public_problem':{'input':self.p.input}}
        for field,value in [('public_evidence_paths',['/assessment/score']),('public_evidence_paths',['/public_problem/input/missing']),('affected_target_ids',['foreign']),('resolution_rationale',''),('public_evidence_paths',[])]:
            bad=deepcopy(self.req); bad[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError): validate_request(bad,original)

    def test_no_score_or_assessment_input_in_provider_payload(self):
        self.start()
        self.assertEqual(set(self.provider.calls[0]['original']),{'public_problem','physical_forecast','output_readout'})

    def test_contact_capability_cannot_trigger_question(self):
        p,f=example('stable_stack'); req=deepcopy(self.req); req['affected_target_ids']=[p.input['answer_spec'][0]['target_id']]; req['readout_evidence_target_ids']=req['affected_target_ids']
        with self.assertRaisesRegex(ValueError,'contact'): validate_request(req,{'public_problem':{'input':p.input}})
        inp=p.input; inp['answer_spec'].append(self.p.input['answer_spec'][1])
        req['affected_target_ids']=[req['affected_target_ids'][0],'load:position']
        with self.assertRaisesRegex(ValueError,'contact'): validate_request(req,{'public_problem':{'input':inp}})

    def test_unsupported_cannot_be_invented_even_after_reply(self):
        p,f=example('stable_stack'); inp=p.input
        inp['answer_spec'].append(self.p.input['answer_spec'][1]); p=replace_input(p,inp); rows=read_targets(p,f)
        ans=llm_result(p,rows); req=deepcopy(self.req); req['affected_target_ids']=['load:position']; req['readout_evidence_target_ids']=[]
        provider=MockProvider([{'answer':ans,'clarification_request':req}]); service=ClarificationService(self.store,provider)
        service.start('attempt',p,f,rows); r=reply(); service.submit_reply('attempt',r)
        bad=deepcopy(ans); bad['targets'][0].update(status='supported',value=False,reason=None); provider.values=[bad]
        self.assertEqual(service.review_and_refine('attempt',review(r))['status'],'unresolved_invalid_refinement')

    def test_refinement_cannot_replace_numeric_forecast(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r)
        bad=deepcopy(self.answer); bad['targets'][1]['value']=[99.,0.,1.]; self.provider.values=[bad]
        result=self.service.review_and_refine('attempt',review(r))
        self.assertEqual(result['status'],'unresolved_invalid_refinement'); self.assertNotIn('refined_answer',result['records'])

    def test_second_question_or_schema_change_is_invalid_refinement(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r)
        self.provider.values=[{'answer':self.answer,'clarification_request':self.req}]
        self.assertEqual(self.service.review_and_refine('attempt',review(r))['status'],'unresolved_invalid_refinement')

    def test_initial_failure_keeps_raw_response_and_usage(self):
        result=self.start([{'malformed':'response'}]); self.assertEqual(result['status'],'unresolved_invalid_initial_output')
        self.assertEqual(result['total_usage']['output_tokens'],20)
        self.assertIn('malformed',result['records']['call_finished']['text'])

    def test_timeout_failure_unknown_usage_no_retry(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r); self.provider.values=[TimeoutError('secret-not-to-log')]
        result=self.service.review_and_refine('attempt',review(r))
        self.assertEqual(result['status'],'unresolved_refinement_failure'); self.assertIsNone(result['total_usage']['cost_usd'])
        self.assertNotIn('secret-not-to-log',json.dumps(result))
        with self.assertRaises(ValueError): self.service.review_and_refine('attempt',review(r))
        self.assertEqual(len(self.provider.calls),2)

    def test_reserved_interrupted_call_is_not_replayed(self):
        self.start()
        with self.store.lock('attempt'):
            self.store.append('attempt','call_reserved',{'stage':'refinement','provider':self.provider.identity})
        snap=self.store.snapshot('attempt'); self.assertEqual(snap['status'],'unresolved_call_in_flight_or_interrupted')
        self.assertIsNone(snap['total_usage']['input_tokens'])
        with self.assertRaises(ValueError): self.service.submit_reply('attempt',reply())

    def test_journal_tampering_and_concurrent_write_fail_closed(self):
        self.start()
        with self.store.lock('attempt'):
            with self.assertRaises(FileExistsError): self.service.submit_reply('attempt',reply())
        path=self.store.directory('attempt')/'0001.json'; value=json.loads(path.read_text()); value['data']['public_problem']['input']['question']='modified'; path.write_text(json.dumps(value))
        with self.assertRaises(ValueError): self.store.snapshot('attempt')

    def test_provider_identity_change_prevents_refinement(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r)
        provider=MockProvider([self.answer]); provider.identity={'different':'model'}
        result=ClarificationService(self.store,provider).review_and_refine('attempt',review(r))
        self.assertEqual(result['status'],'unresolved_provider_identity_changed'); self.assertEqual(len(provider.calls),0)

    def test_private_forecast_and_foreign_readout_rejected_before_calls(self):
        provider=MockProvider([]); service=ClarificationService(self.store,provider)
        bad=deepcopy(self.f); bad['reference']={'states':[]}
        with self.assertRaises(ValueError): service.start('a',self.p,bad,self.rows)
        rows=deepcopy(self.rows); rows[0]['value']=not rows[0]['value']
        with self.assertRaises(ValueError): service.start('b',self.p,self.f,rows)
        self.assertEqual(provider.calls,[])

    def test_demo_actual_autonomous_provenance_cannot_mix(self):
        self.start(mode='scripted_demo')
        with self.assertRaises(ValueError): self.service.submit_reply('attempt',reply())
        self.service.submit_reply('attempt',reply(mode='scripted_demo'))
        with tempfile.TemporaryDirectory() as temp:
            s=ClarificationService(AttemptStore(temp),MockProvider([{'answer':self.answer,'clarification_request':self.req}]))
            s.start('a',self.p,self.f,self.rows,mode='autonomous')
            with self.assertRaises(ValueError): s.submit_reply('a',reply())

    def test_evaluation_keeps_unanswered_failures_and_unknown_labels(self):
        snap=self.start(); task=snap['records']['created']['task_sha256']
        row=evaluate_interaction(snap,task_sha256=task,before={'complete_success':False})
        summary=summarize_interactions([row])[0]
        self.assertEqual(summary['eligible_attempts'],1); self.assertEqual(summary['unanswered_requests'],1)
        self.assertEqual(summary['refined_success_over_all'],0); self.assertEqual(summary['trigger_relevant']['unknown'],1)
        with self.assertRaises(ValueError): evaluate_interaction(snap,task_sha256='changed')
        with self.assertRaises(ValueError): evaluate_interaction(snap,task_sha256=task,after={'complete_success':True})
        with self.assertRaises(ValueError): evaluate_interaction(snap,task_sha256=task,review={'label_source':'model_self_label'})

    def test_changed_task_cannot_count_as_improvement(self):
        self.start(); r=reply('Use a different event threshold.'); self.service.submit_reply('attempt',r)
        snap=self.service.review_and_refine('attempt',review(r,'changed_task_or_answer_definition'))
        with self.assertRaises(ValueError): evaluate_interaction(snap,task_sha256=snap['records']['created']['task_sha256'],after={'complete_success':True})

    def test_evaluator_bridge_keeps_reference_and_tolerances_out_of_generation(self):
        self.start(); r=reply(); self.service.submit_reply('attempt',r)
        snap=self.service.review_and_refine('attempt',review(r))
        ref={'structured_label':[{k:x[k] for k in ('target_id','value','unit','frame')} for x in self.rows]}
        evaluated=evaluate_original_reference(snap,ref,expected_reference_sha256=digest(ref))
        self.assertTrue(evaluated['before_success']); self.assertTrue(evaluated['after_success'])
        self.assertEqual(evaluated['answer_spec_sha256'],digest(self.p.input['answer_spec']))
        with self.assertRaises(ValueError): evaluate_original_reference(snap,ref,expected_reference_sha256='foreign')
        self.assertNotIn('structured_label',json.dumps(self.provider.calls))

    def test_cli_actual_reply_intake_never_dispatches_provider(self):
        import importlib.util
        from contextlib import redirect_stdout
        import io
        spec=importlib.util.spec_from_file_location('reply_cli',ROOT/'tools/clarification_reply.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.start(); path=Path(self.tmp.name)/'reply.txt'; path.write_text('BC refers to the listed event.')
        with redirect_stdout(io.StringIO()):
            module.main(['reply','--root',self.tmp.name,'--attempt','attempt','--actor','actual-user-fixture','--message-id','fixture-42','--reply-file',str(path)])
        snap=self.store.snapshot('attempt')
        self.assertEqual(snap['status'],'awaiting_reply_review'); self.assertEqual(len(self.provider.calls),1)

    def test_frozen_adapter_mock_payload_has_one_dispatch_and_no_hidden_tools(self):
        asset=json.loads((ROOT/'docs/assets/clarification_v1.json').read_text())
        config={'model':'gpt-5.6-sol','max_attempts_per_request':1,'max_output_tokens':4096,'timeout_seconds':120,'reasoning_effort':'medium'}
        calls=[]; reservations=[]
        def transport(payload,timeout):
            calls.append(payload)
            return {'id':'fixture','model':'gpt-5.6-sol','status':'completed','usage':{'input_tokens':10,'output_tokens':20},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'answer':self.answer,'clarification_request':None})}]}]}
        provider=FrozenClarificationAnswer(config=config,asset=asset,transport=transport,authorize_and_reserve=lambda stage,payload:reservations.append(stage))
        result=ClarificationService(self.store,provider).start('a',self.p,self.f,self.rows)
        self.assertEqual(result['status'],'answered_without_clarification'); self.assertEqual(len(calls),1); self.assertEqual(reservations,['initial'])
        self.assertNotIn('tools',calls[0]); self.assertFalse(calls[0]['store'])
        self.assertEqual(json.loads(calls[0]['input'])['original_evidence']['public_problem']['input'],self.p.input)

    def test_frozen_adapter_requires_external_authorization_before_transport(self):
        asset=json.loads((ROOT/'docs/assets/clarification_v1.json').read_text()); calls=[]
        config={'model':'gpt-5.6-sol','max_attempts_per_request':1,'max_output_tokens':4096,'timeout_seconds':120,'reasoning_effort':'medium'}
        def denied(*args): raise PermissionError('no live budget')
        provider=FrozenClarificationAnswer(config=config,asset=asset,transport=lambda *args:calls.append(args),authorize_and_reserve=denied)
        result=ClarificationService(self.store,provider).start('a',self.p,self.f,self.rows)
        self.assertEqual(result['status'],'unresolved_initial_failure'); self.assertEqual(calls,[])


if __name__=='__main__': unittest.main()
