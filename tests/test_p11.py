"""Offline checks for the new comparison policy; strict historical mode remains."""
import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_p04a import example,llm_result
from phi_jepa.inference.readout import target_result
from phi_jepa.providers.openai_answer import parse_answer,AnswerParseFailure,OpenAIAnswer

class DeadlineStudyTests(unittest.TestCase):
    def test_direct_boolean_attempt_keeps_strict_types(self):
        p,_=example('stable_stack');row=target_result(p.input['answer_spec'][0],'supported',value=True,source='direct')
        text=json.dumps(llm_result(p,[row]))
        self.assertTrue(parse_answer(p,text,[],boolean_policy='direct_prediction')['targets'][0]['value'])
        with self.assertRaises(AnswerParseFailure):parse_answer(p,text,[])
        value=llm_result(p,[row]);value['targets'][0]['value']=1
        with self.assertRaises(AnswerParseFailure):parse_answer(p,json.dumps(value),[],boolean_policy='direct_prediction')
    def test_direct_never_repairs_duplicates_or_missing(self):
        p,_=example();row=target_result(p.input['answer_spec'][0],'supported',value=False,source='direct')
        for rows in ([],[row,row]):
            with self.assertRaises(AnswerParseFailure):parse_answer(p,json.dumps(llm_result(p,rows)),[],boolean_policy='direct_prediction')
    def test_historical_boolean_restriction_preserved(self):
        p,_=example();row=target_result(p.input['answer_spec'][0],'supported',value=True,source='direct');unsupported=target_result(p.input['answer_spec'][0],'unsupported',reason='no_forecast',source='control')
        with self.assertRaises(AnswerParseFailure):parse_answer(p,json.dumps(llm_result(p,[row])),[unsupported])
    def test_direct_rejects_forecast_and_unknown_policy_before_transport(self):
        obj=object.__new__(OpenAIAnswer);p,_=example()
        with self.assertRaises(ValueError):obj.answer(p,{},[],condition='x',boolean_policy='direct_prediction')
        with self.assertRaises(ValueError):obj.answer(p,None,[],condition='x',boolean_policy='unknown')
    def test_frozen_cohorts_and_checkpoint_policies(self):
        root=Path(__file__).resolve().parents[1];plan=json.loads((root/'configs/study_p11_frozen.json').read_text())
        for c in plan['cohorts'].values():
            self.assertEqual([len(c[k]) for k in ('main_train','main_test','main_selection','appendix_train','appendix_test')],[48,12,8,16,4])
            self.assertFalse(set(c['main_train'])&set(c['main_test']));self.assertFalse(set(c['main_selection'])&set(c['main_test']))
            self.assertTrue(set(c['appendix_train'])<=set(c['main_train']));self.assertTrue(set(c['appendix_test'])<=set(c['main_test']))
        self.assertFalse(plan['heldout_outcomes_opened_before_freeze']);self.assertEqual(plan['custom_policy']['passes'],2)

if __name__=='__main__':unittest.main()
