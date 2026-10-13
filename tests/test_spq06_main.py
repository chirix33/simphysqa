import unittest
from simphysqa.main_public import project,request_from
from simphysqa.io import canonical

class MainInputs(unittest.TestCase):
    def test_matched_facts_gap_and_comparison(self):
        view={'sample_id':'x','question_type':'clarification','schema_version':'s','export_version':'v',
            'input':{'global_context':'Unique physical setup','query':{'quantity':'position'},
                'states':[{'state_id':'s','timestamp':0.0,'context':'source physical constraint','measurements':[{'value':[1.,2.,3.],'unit':'m','frame':'world'}],
                    'linked_events':[{'event_id':'e','temporal_relationship':'scheduled_future','event_description':'derived'}]}],
                'known_events':[{'event_id':'e','description':'original declaration','event_description':'derived','event_description_status':'declared'}],
                'supplied_comparison':{'readouts':[{'value':False}]}},
            'annotations':{'trajectory':{'text':'trajectory language','claims':[]},'timestamps':[{'state_id':'s','timestamp':0.,'text':'timestamp language'}]}}
        enriched=project(view);structured=project(view,True)
        self.assertEqual(canonical(enriched['input']),canonical(structured['input']))
        self.assertNotIn('timestamp',structured['input']['query'])
        self.assertEqual(enriched['language_annotations']['timestamps'][0]['text'],'timestamp language')
        self.assertEqual(structured['input']['states'][0]['context'],'source physical constraint')
        self.assertEqual(structured['input']['known_events'][0]['description'],'original declaration')
        self.assertFalse(structured['input']['supplied_comparison']['readouts'][0]['value'])
        self.assertNotIn('language_annotations',structured)
        self.assertEqual(view['input']['states'][0]['linked_events'][0]['event_description'],'derived')
    def test_numeric_response_contract_suffix_retained(self):
        view={'sample_id':'x','question_type':'direct','schema_version':'s','export_version':'v','input':{'states':[]}}
        original={'tools':[],'messages':[{'role':'user','content':'Task\n'+canonical(view).decode()+'Return typed JSON.'}]}
        result,_=request_from(original)
        self.assertTrue(result['messages'][0]['content'].endswith('Return typed JSON.'))
        self.assertEqual(original['tools'],[])

if __name__=='__main__':unittest.main()
