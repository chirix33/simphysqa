"""Offline synthetic tests, never main reservations or empirical responses."""
import copy,json,tempfile,unittest
from pathlib import Path
from simphysqa.complement_preparation import select,scoped_key,COMBINATIONS,copy as copy_bytes
from simphysqa.io import DOMAINS,QUESTION_TYPES

class Complement(unittest.TestCase):
 def setUp(self):
  self.pool=[{'sample_id':f'FIXTURE-{d}-{f}-{rank}','group_id':f'FIXTURE-G-{d}-{f}-{rank}','domain':d,'family':f,'split':'test_id','qualified_cell_rank':rank,'candidate_rank':rank+3,'nested_core':rank<=10} for d in DOMAINS for f in QUESTION_TYPES for rank in range(1,21)]
  self.core=[r for r in self.pool if r['nested_core']]
 def test_exact_ranked_complement_preserves_source_order(self):
  selected=select(self.core,self.pool,set());self.assertEqual(len(selected),200);self.assertEqual(selected[0]['qualified_cell_rank'],11)
  self.assertEqual([r['sample_id'] for r in selected],[r['sample_id'] for r in self.pool if not r['nested_core']])
  self.assertEqual(selected[0]['candidate_rank'],14)
 def test_exclusion_shortfall_never_replaced(self):
  with self.assertRaisesRegex(ValueError,'excluded'):select(self.core,self.pool,{self.pool[10]['group_id']})
 def test_duplicate_or_changed_group_halts(self):
  pool=copy.deepcopy(self.pool);pool[10]['group_id']=pool[0]['group_id']
  with self.assertRaisesRegex(ValueError,'uniqueness'):select(self.core,pool,set())
  pool=copy.deepcopy(self.pool);pool[0]['group_id']='CHANGED'
  with self.assertRaisesRegex(ValueError,'exact frozen'):select(self.core,pool,set())
 def test_original_split_and_balanced_ranks_enforced(self):
  pool=copy.deepcopy(self.pool);pool[10]['split']='train'
  with self.assertRaisesRegex(ValueError,'split'):select(self.core,pool,set())
  pool=copy.deepcopy(self.pool);pool[10]['qualified_cell_rank']=21
  with self.assertRaisesRegex(ValueError,'ranks'):select(self.core,pool,set())
 def test_shared_file_reuse_exact_bytes_only(self):
  with tempfile.TemporaryDirectory() as root:
   src=Path(root)/'source';dest=Path(root)/'dest';src.write_bytes(b'EXACT FIXTURE')
   copy_bytes(src,dest);copy_bytes(src,dest);self.assertEqual(dest.read_bytes(),b'EXACT FIXTURE')
   src.write_bytes(b'DIFFERENT FIXTURE')
   with self.assertRaisesRegex(ValueError,'no overwrite'):copy_bytes(src,dest)
   self.assertEqual(dest.read_bytes(),b'EXACT FIXTURE')
 def test_combined_uncertainty_resamples_union_not_average_intervals(self):
  from simphysqa.main_analysis import paired_intervals
  rows=[]
  for item in self.pool:
   for label in ('enriched','structured_only'):
    correct=int((item['qualified_cell_rank']<=10)==(label=='enriched'))
    rows.append({**item,'condition_id':'qwen3_8b_direct','input_condition':label,'endpoints':{'typed_correct':correct}})
  result=paired_intervals(rows,replicates=1000)
  self.assertTrue(all(r['independent_qa_items']==80 and r['trajectory_groups']==80 for r in result['summaries']))
  contrasts=[r for r in result['paired_comparisons'] if r['endpoint']=='typed_correct']
  self.assertTrue(all(r['difference_a_minus_b']==0 and r['paired_interval_95'][0]<0<r['paired_interval_95'][1] for r in contrasts))
 def test_namespace_unique_and_no_collaborator_combinations(self):
  selected=select(self.core,self.pool,set());keys=[scoped_key('|'.join([r['sample_id'],cid,label,str(stage)])) for cid,label in COMBINATIONS for r in selected for stage in ([1,2] if r['family']=='clarification' else [1])]
  self.assertEqual(len(keys),1920);self.assertEqual(len(set(keys)),1920);self.assertTrue(all('gemma' not in k and 'deepseek' not in k for k in keys))
if __name__=='__main__':unittest.main()
