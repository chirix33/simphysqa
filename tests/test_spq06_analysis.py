import unittest,tempfile
from pathlib import Path
from simphysqa.main_analysis import assess,paired_intervals,unique_result
from simphysqa.main_run import run
from simphysqa.io import write,read,digest
from simphysqa.condition_revisions import resolved_condition

class AnalysisBoundaries(unittest.TestCase):
    def test_failures_stay_in_denominator_and_pairs_share_draws(self):
        rows=[]
        for domain in ('a','b','c','d'):
            for i in range(2):
                for condition in ('A','B'):
                    rows.append({'sample_id':domain+str(i),'group_id':domain+str(i),'domain':domain,'family':'direct',
                        'condition_id':condition,'input_condition':'enriched','endpoints':{'typed_correct':i}})
        result=paired_intervals(rows,replicates=100,seed=11)
        self.assertEqual([r['balanced_domain_mean'] for r in result['summaries']],[.5,.5])
        self.assertEqual(result['paired_comparisons'][0]['paired_interval_95'],[0.,0.])
        self.assertEqual(result['summaries'][0]['independent_qa_items'],8)
        rows[0]['endpoints']['typed_correct']=0
        self.assertEqual(len(result['summaries']),2)
    def test_correlated_group_and_missing_condition_rows_halt(self):
        rows=[{'sample_id':str(i),'group_id':'shared','domain':str(i),'family':'direct','condition_id':'A',
            'input_condition':'enriched','endpoints':{'typed_correct':0}} for i in range(4)]
        with self.assertRaisesRegex(ValueError,'trajectory'):paired_intervals(rows,10)
    def test_missing_and_length_limited_not_repaired(self):
        record={'question_type':'explanation'};condition={'condition_id':'A'}
        absent=assess(record,condition,None,None)
        truncated=assess(record,condition,{'completion_status':'length_limited','raw_output':'{"x":1}'},None)
        self.assertEqual(absent['endpoints'],{'structured_facts_all_correct':0})
        self.assertFalse(truncated['answer_valid']);self.assertEqual(truncated['parsing'],'not_completed')
        self.assertEqual(absent['prose_adequacy'],'human_judgment_uncollected')
    def test_no_main_launch_without_separate_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'authorization'):run(Path(d)/'unused',False,48)
            self.assertFalse((Path(d)/'unused').exists())
    def test_plans_cannot_become_human_model_answer_packets(self):
        from simphysqa.model_prose_review import packets
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);write(root/'run/main-run-plan.json',{})
            with self.assertRaisesRegex(ValueError,'executed'):packets(root/'forms',root/'run',root/'packets')
            self.assertFalse((root/'packets').exists())
    def test_duplicate_stage_results_halt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for number in (1,2):write(root/'jobs'/('A--enriched--stage1--'+str(number))/'results'/'S-stage1.json',{})
            with self.assertRaisesRegex(ValueError,'duplicate'):unique_result(root,'A','enriched','S',1)
    def test_revision_chain_cannot_replace_original_pin(self):
        from simphysqa.formal_sampling import file_hash
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);original=root/'conditions'/'A.json';write(original,{'condition_id':'A','value':1})
            # An unrelated replacement cannot masquerade as a valid predecessor.
            write(root/'condition-revisions'/'A'/'1.0.1.json',{'condition_id':'A','startup_revision':{'previous_condition_sha256':'0'*64},'value':2})
            with self.assertRaises(ValueError):resolved_condition(root,'A')
    def test_blank_prose_forms_are_uncollected_and_resume_exactly(self):
        from simphysqa.model_prose_review import forms,import_submission
        from simphysqa.formal_sampling import file_hash
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);subset=root/'subset.json';output=root/'forms';imports=root/'imports'
            write(subset,{'conditions':['A','B'],'items':[{'sample_id':'S','private_record':'private/S.json'}]})
            forms(subset,output);before=file_hash(output/'P1.csv');forms(subset,output)
            self.assertEqual(before,file_hash(output/'P1.csv'))
            import_submission(output,output/'P1.csv','P1',imports)
            import_submission(output,output/'P1.csv','P1',imports)
            receipt=read(next((imports/'imports').glob('*.json')))
            self.assertEqual(receipt['collected'],0);self.assertEqual(receipt['missing'],2)
            with self.assertRaisesRegex(ValueError,'identity'):import_submission(output,output/'P1.csv','P2',root/'invalid')

if __name__=='__main__':unittest.main()
