import unittest
from simphysqa.result_diagnostics import parse_stage,schema_errors,summarize
from simphysqa.spq06 import parse_answer
class Diagnostics(unittest.TestCase):
 def test_rejected_fenced_object_not_repaired(self):
  raw={'completion_status':'completed','raw_output':'Some prose\n```json\n{"value":1}\n```'}
  d,v=parse_stage(raw);self.assertEqual(d['category'],'json_parsing_failure');self.assertIsNone(v)
  self.assertEqual(d['failure_surface'],'decodable_fenced_JSON_with_prose_or_trailing_text')
  with self.assertRaises(ValueError):parse_answer(raw['raw_output'])
 def test_length_limit_and_missing_separate_from_parser(self):
  d,v=parse_stage({'completion_status':'length_limited','raw_output':'{"value":1}'})
  self.assertEqual(d['category'],'generation_noncompletion');self.assertEqual(v,{'value':1})
  self.assertEqual(parse_stage(None)[0]['category'],'execution_missing')
 def test_noncompletion_never_counted_as_primary_parser_failure(self):
  d,v=parse_stage({'completion_status':'length_limited','raw_output':'truncated'})
  d.update(condition_id='FIXTURE',representation='fixture',sample_id='FIXTURE')
  self.assertEqual(summarize([d])['summaries'][0]['parser_failure_surfaces'],{})
 def test_unit_frame_and_type_diagnostics(self):
  errors=schema_errors({'type':'object','properties':{'unit':{'const':'m'},'frame':{'const':'world'},'value':{'type':'number'}}},{'unit':'rad','frame':'body','value':'bad'})
  self.assertEqual({e['kind'] for e in errors},{'unit_invalid','frame_invalid','type_invalid'})
if __name__=='__main__':unittest.main()
