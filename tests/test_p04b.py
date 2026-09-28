"""Fixed assessment and common evaluator behavior; offline fixtures only."""
from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
import unittest
from phi_jepa.artifacts import digest
from phi_jepa.integration.layout import StateLayout
from phi_jepa.assessment.reference import ReferenceBank,block_diagnostics
from phi_jepa.assessment.fixed import combine,calibrate,apply_threshold,bounded_fallback
from phi_jepa.assessment.checks import physical_checks,contract_score
from phi_jepa.providers.openai_judge import parse_judge,OpenAIJudge
from phi_jepa.providers.contracts import ProviderFailure
from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors,grouped_summary,physical_error
from phi_jepa.inference.readout import read_targets
from test_p04a import example,measurement,replace_input

ROOT=Path(__file__).resolve().parents[1]


class P04bTests(unittest.TestCase):
    def setUp(self):
        self.p,self.f=example(); inp=self.p.input
        self.layout=StateLayout.build(inp['states'][-1],inp,'state_plus_fixed_conditioning','train')
        self.identity={k:'fixture-'+k for k in ('checkpoint_sha256','encoder_sha256','projection_sha256','solver_sha256','profile_sha256')}
        self.identity['layout_sha256']=self.layout.sha256
        self.row={'sample_id':'reference','scenario_id':'scenario-a','split':'train','origin':'autonomous_prediction','domain':inp['domain'],
            'layout_sha256':self.layout.sha256,'cutoff':.2,'times':[.22,.24],'embedding':[1.,0.],
            'trajectory':[[1.]*self.layout.d+[2.]*self.layout.d]*2}
        self.query={**deepcopy(self.row),'sample_id':'query','scenario_id':'scenario-b','split':'validation'}
        self.profile=json.loads((ROOT/'configs/assessment_p04b.json').read_text())

    def test_training_only_identity_invalidation_and_immutable_bank(self):
        bank=ReferenceBank.build(self.identity,[self.row]); copied=bank.data; copied['rows'][0]['trajectory'][0][0]=99
        self.assertNotEqual(bank.data,copied)
        for field in ('checkpoint_sha256','encoder_sha256','projection_sha256'):
            changed={**self.identity,field:'new'}
            with self.assertRaises(ValueError): bank.assess(self.query,self.layout,identity=changed)
        row={**self.row,'split':'validation'}
        with self.assertRaises(ValueError): ReferenceBank.build(self.identity,[row])
        row={**self.row,'origin':'recorded_target'}
        with self.assertRaises(ValueError): ReferenceBank.build(self.identity,[row])
        with tempfile.TemporaryDirectory() as tmp:
            path=bank.write(tmp); loaded=ReferenceBank.load(path,identity=self.identity)
            self.assertEqual(loaded,bank)
            path.write_text('{}')
            with self.assertRaises((ValueError,KeyError)): ReferenceBank.load(path,identity=self.identity)

    def test_filter_before_retrieval_scenario_exclusion_and_stable_tie(self):
        other={**deepcopy(self.row),'sample_id':'aaa','scenario_id':'scenario-c','embedding':[1.,0.]}
        wrong={**deepcopy(other),'sample_id':'000','times':[.22,.26]}
        bank=ReferenceBank.build(self.identity,[self.row,other,wrong])
        self.assertEqual(bank.assess(self.query,self.layout,identity=self.identity)['reference_id'],'aaa')
        q={**self.query,'split':'train','scenario_id':'scenario-c'}
        self.assertEqual(bank.assess(q,self.layout,identity=self.identity)['reference_id'],'reference')
        q={**self.query,'times':[.22,.28]}
        self.assertEqual(bank.assess(q,self.layout,identity=self.identity)['reason'],'no_compatible_reference')

    def test_full_2d_block_contributions_and_invalid_vectors(self):
        bank=ReferenceBank.build(self.identity,[self.row]); q=deepcopy(self.query)
        q['trajectory'][-1]=[2.]*self.layout.d+[-3.]*self.layout.d
        result=bank.assess(q,self.layout,identity=self.identity)
        self.assertAlmostEqual(sum(b['familiarity_contribution'] for b in result['blocks'].values()),result['score'])
        self.assertEqual(sum(b['width'] for b in result['blocks'].values()),2*self.layout.d)
        for vector in ([0.]*2*self.layout.d,[float('nan')]*2*self.layout.d):
            q['trajectory'][-1]=vector
            self.assertEqual(bank.assess(q,self.layout,identity=self.identity)['reason'],'invalid_query_trajectory')
        q['embedding']=[0.,0.]
        self.assertEqual(bank.assess(q,self.layout,identity=self.identity)['reason'],'invalid_query_embedding')

    def test_partial_assessment_has_no_score_or_threshold_and_no_zero_fill(self):
        available={'status':'available','score':.3}
        missing={'status':'unavailable','score':None}
        result=combine(available,missing,available,profile=self.profile,identity=self.identity)
        self.assertEqual(result['status'],'partial'); self.assertIsNone(result['score']); self.assertIsNone(result['threshold_decision'])
        result=combine(available,available,available,profile=self.profile,identity=self.identity)
        self.assertAlmostEqual(result['score'],.6)
        contracts=contract_score(self.p,self.f,[])
        self.assertEqual(contracts['status'],'unavailable'); self.assertIsNone(contracts['score'])
        with self.assertRaises(ValueError): contract_score(self.p,self.f,[{'operator':'le'}])

    def test_validation_calibration_identity_grouping_and_strict_threshold(self):
        records=[]; policy=self.profile['calibration']
        for i in range(20):
            a=combine({'status':'available','score':i/20},{'status':'available','score':0.},{'status':'available','score':0.},profile=self.profile,identity=self.identity)
            records.append({'sample_id':str(i),'scenario_id':str(i),'split':'validation','distribution':'id','role':'calibration','assessment':a})
        cal=calibrate(records,assessment_identity=self.identity,profile_sha256=digest(self.profile),policy=policy)
        self.assertEqual(cal['status'],'calibrated'); self.assertEqual(cal['threshold'],.95)
        self.assertFalse(apply_threshold(records[-1]['assessment'],cal)['threshold_decision'])
        changed=deepcopy(records[-1]['assessment']); changed['score']=1.
        self.assertTrue(apply_threshold(changed,cal)['threshold_decision'])
        for key,val in [('split','test_id'),('role','selection'),('distribution','ood_parameter_extrapolation')]:
            bad=deepcopy(records); bad[0][key]=val
            with self.assertRaises(ValueError): calibrate(bad,assessment_identity=self.identity,profile_sha256=digest(self.profile),policy=policy)
        with self.assertRaises(ValueError): calibrate(records,assessment_identity=self.identity,profile_sha256=digest(self.profile),policy=policy,selection_scenarios=['0'])
        empty=calibrate([],assessment_identity=self.identity,profile_sha256=digest(self.profile),policy=policy)
        self.assertEqual(empty['status'],'uncalibrated')
        changed['identity']={**self.identity,'checkpoint_sha256':'new'}
        with self.assertRaises(ValueError): apply_threshold(changed,cal)

    def test_physical_checks_are_independent_empty_unavailable(self):
        p,f=example('joint_limit_by_T')
        result=physical_checks(p,f,self.profile['physical_checks'])
        self.assertEqual(result['evaluated'],0); self.assertIsNone(result['pcvr'])
        p,f=example('left_table'); inp=p.input
        inp['states'][-1]['measurements'].append(measurement('block_2','orientation',[0.,0.,0.,1.],'1'))
        p=replace_input(p,inp)
        for state in f['states']: state['measurements'].append(measurement('block_2','orientation',[0.,0.,0.,2.],'1'))
        result=physical_checks(p,f,self.profile['physical_checks'])
        self.assertEqual(result['pcvr'],1.)
        self.assertEqual(result['evaluated'],len(f['states']))

    def test_typed_evaluator_quaternion_decimal_failures_and_full_denominators(self):
        self.assertAlmostEqual(physical_error(-.125,.125,'x')[0],.25)
        self.assertEqual(physical_error([0.,0.,0.,-1.],[0.,0.,0.,1.],'orientation')[0],0.)
        with self.assertRaises(ValueError): physical_error([0.,0.,0.,0.],[0.,0.,0.,1.],'orientation')
        p,f=example('stable_stack'); row=read_targets(p,f)[0]
        reference={'structured_label':[{'target_id':row['target_id'],'value':False,'unit':'1','frame':'world'}]}
        for rows in ([],[row],[row,row]):
            result=evaluate_targets(p,reference,rows,method='fixture')
            self.assertEqual(result['eligible_targets'],1); self.assertFalse(result['complete_success'])
            self.assertEqual(result['boolean_supported'],0)

    def test_trajectory_modes_and_scenario_grouped_reporting(self):
        result=trajectory_errors(self.f['states'],self.f['states'],mode='autonomous')
        self.assertTrue(all(r['error']==0 for r in result['per_time_channel']))
        missing=trajectory_errors([],self.f['states'],mode='recorded_input_one_step_diagnostic')
        self.assertTrue(all(r['valid']==0 for r in missing['metrics']))
        rows=[]
        for i in range(3):
            rows.append({'scenario_id':str(i//2),'domain':'tethered_load','distribution':'id','complete_success':i<2,
                'boolean_eligible':1,'boolean_supported':int(i<2),'boolean_correct':int(i<2),'targets':[]})
        summary=grouped_summary(rows,resamples=100)
        self.assertEqual(summary['pooled']['scenarios'],2)
        self.assertAlmostEqual(summary['pooled']['complete_success_rate'],2/3)
        self.assertEqual(summary['pooled']['scenario_macro_complete_success'],.5)

    def test_exact_v1_judge_scope_and_bounds(self):
        prompts=json.loads((ROOT/'docs/assets/prompts.json').read_text()); schema=json.loads((ROOT/'docs/assets/judge_schema.json').read_text())
        config=json.loads((ROOT/'configs/answer_p04a.json').read_text())
        def transport(payload,timeout):
            self.assertEqual(payload['instructions'],prompts['JUDGE_PROMPT'])
            data=json.loads(payload['input']); self.assertEqual(set(data),{'scenario','schema'})
            self.assertEqual(data['schema'],self.p.input)
            return {'id':'fixture','model':'fixture','status':'completed','usage':{'input_tokens':2,'output_tokens':4},'output':[{'type':'message','content':[{'type':'output_text','text':'{"score":0.2,"reason":"fixture"}'}]}]}
        provider=OpenAIJudge('fixture',config,{'prompt':prompts['JUDGE_PROMPT'],'schema':schema},None,transport=transport)
        self.assertEqual(provider.judge(self.p)['scope'],'scenario_schema_v1')
        for text in ('{"score":true,"reason":"x"}','{"score":1.1,"reason":"x"}','{"score":0,"reason":""}'):
            with self.assertRaises(ProviderFailure): parse_judge(text)

    def test_bounded_fallback_preserves_original_and_no_high_score_replacement(self):
        original={'values':[1.,2.]}; calls=[]
        def fallback(): calls.append(1); return {'method':'public_only','usage':{'calls':1}}
        result=bounded_fallback(original,text_answer=fallback)
        self.assertEqual(calls,[]); self.assertEqual(result['returned_prediction'],original)
        result=bounded_fallback(None,failure='forecast_failure',text_answer=fallback)
        self.assertEqual(len(calls),1); self.assertIsNone(result['returned_prediction'])
        self.assertEqual(result['fallback_calls'],1)
        result=bounded_fallback(original,failure='answer_failure',numeric_formatter=lambda x:x)
        self.assertEqual(result['original_prediction'],original)
        self.assertEqual(result['fallback_status'],'deterministic_numeric_format')

    def test_contract_excess_monotonic_with_exact_public_evidence(self):
        p,f=example('stopped_by_T'); inp=p.input
        inp['global_context']='Forward velocity must be at most 1 m/s.'
        c={'constraint_id':'speed','entity_id':'car','quantity':'forward_velocity','unit':'m/s','frame':'world',
           'operator':'le','bounds':[1.],'scale':1.,'tolerance':0.,'evidence':inp['global_context']}
        inp['controller']['constraints']=[c]; p=replace_input(p,inp)
        self.assertEqual(contract_score(p,f,[c])['score'],0.)
        for state in f['states']: state['measurements'][1]['value']=2.
        self.assertEqual(contract_score(p,f,[c])['score'],1.)
        for state in f['states']: state['measurements'][1]['value']=3.
        self.assertEqual(contract_score(p,f,[c])['score'],2.)

    def test_diagnostic_cannot_feed_autonomous_answer_and_formatter_is_explicit(self):
        from phi_jepa.inference.readout import InvalidForecast
        from phi_jepa.assessment.fixed import deterministic_answer
        f=deepcopy(self.f); f['source']='recorded_input_one_step_diagnostic'
        with self.assertRaises(InvalidForecast): read_targets(self.p,f)
        formatted=deterministic_answer(self.p,self.f)
        self.assertFalse(formatted['llm_narrative_available'])
        self.assertEqual(formatted['targets'][0]['value'],False)

    def test_evaluator_rejects_wrong_bindings_even_for_correct_values(self):
        p,f=example(); row=read_targets(p,f)[0]
        reference={'structured_label':[{'target_id':row['target_id'],'value':False,'unit':'1','frame':'world'}]}
        good=evaluate_targets(p,reference,[row],method='fixture')
        self.assertTrue(good['complete_success'])
        for key,value in [('end_time',5.),('frame','body'),('unit','m'),('answer_type','number')]:
            bad={**row,key:value}
            result=evaluate_targets(p,reference,[bad],method='fixture')
            self.assertFalse(result['complete_success']); self.assertEqual(result['valid_targets'],0)


if __name__=='__main__': unittest.main()
