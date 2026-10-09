import unittest
from simphysqa.spq06 import parse_answer, conditions, structured_request
from simphysqa.io import canonical, parse


class SPQ06Boundaries(unittest.TestCase):
    def test_actual_reasoning_json_suffix(self):
        value, checks=parse_answer('<think>reason</think>\n{"requested_information":"readout_time"}')
        self.assertEqual(value['requested_information'],'readout_time')
        self.assertTrue(checks['explicit_think_closure'])

    def test_no_json_completion_or_repair(self):
        for s in ('{"targets":', '{"value":NaN}', 'No answer', '{"value":1} trailing'):
            with self.assertRaises(ValueError):parse_answer(s)

    def test_prose_cot_is_not_correctness(self):
        value, checks=parse_answer('Reasoning here.\n{"targets":[]}')
        self.assertEqual(value,{'targets':[]})
        self.assertTrue(checks['prose_prefix_present'])

    def test_condition_identity_and_existing_settings(self):
        values=conditions();self.assertEqual(len(values),9)
        q=next(c for c in values if c['condition_id']=='qwen3_8b_direct')
        self.assertEqual(q['settings']['temperature'],.7)
        self.assertEqual(q['settings']['max_new_tokens'],1024)
        self.assertEqual(next(c for c in values if c['condition_id']=='qwen3_32b_awq_on')['settings']['max_new_tokens'],8192)

    def test_ablation_preserves_hidden_selector_and_supplied_facts(self):
        view={'sample_id':'neutral','input':{'query':{'quantity':'position'},'global_context':'Unique setup fact',
              'supplied_comparison':{'readouts':[{'value':[1,2,3]}]}},'annotations':{'trajectory':{'text':'derived'}}}
        request={'tools':[],'messages':[{'role':'user','content':'Task\n'+canonical(view).decode()}]}
        result=structured_request(request,'clarification');projected=parse(result['messages'][0]['content'].split('\n',1)[1])
        self.assertEqual(projected['input'],view['input'])
        self.assertNotIn('entity_id',projected['input']['query'])
        self.assertNotIn('annotations',projected)
        self.assertIn('annotations',view)


if __name__=='__main__':unittest.main()
