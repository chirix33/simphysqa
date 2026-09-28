import json
import tempfile
import unittest
import torch
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import test_p03
from phi_jepa.models.conditioning import NumericalConditioning
from phi_jepa.models.augmented_ode import AugmentedODE,ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.training.pairs import PairTrainer,TrainingSettings
from phi_jepa.training.checkpoint import write_checkpoint,load_checkpoint
from phi_jepa.baselines.custom_io import public_text


class P10Tests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2); self.fixture=test_p03.P03Tests(); self.fixture.setUp()

    def transform(self):
        return NumericalConditioning.fit([p.n_current for p in self.fixture.pairs],layout_sha256=self.fixture.layout.sha256,
            provenance={'split':'train','sample_ids':['sample'],'scenario_ids':['group']})

    def test_reversible_constant_handling_no_trainable_statistics(self):
        t=self.transform(); x=torch.tensor([p.n_current for p in self.fixture.pairs])
        torch.testing.assert_close(t.inverse(t(x)),x)
        self.assertTrue(all(t.scale[i]==1 for i in t.manifest()['constant_columns']))
        self.assertEqual(list(t.parameters()),[])
        with self.assertRaises(ValueError): NumericalConditioning.fit(x,layout_sha256='x',provenance={'split':'validation'})

    def test_only_network_n_input_changes_raw_derivative_and_context(self):
        f=self.fixture; model=AugmentedODE(f.layout,ProjectionSettings(2),ODESettings(hidden_width=8),self.transform())
        n=torch.tensor([p.n_current for p in f.pairs]); x,y,p=model.projection.pair(n,n,f.e,layout_sha256=f.layout.sha256)
        before=x.clone(); times=torch.tensor([[.2],[.22]])
        captured=[]; handle=model.field[0].register_forward_pre_hook(lambda m,args:captured.append(args[0]))
        result=model(times,x); handle.remove()
        torch.testing.assert_close(captured[0][:,:f.layout.d],model.conditioning(n))
        torch.testing.assert_close(captured[0][:,f.layout.d:-1],p)
        torch.testing.assert_close(captured[0][:,-1:],times); torch.testing.assert_close(before,x)
        torch.testing.assert_close(result,model.field(captured[0]))

    def test_target_gradient_paths_checkpoint_and_training_statistics_frozen(self):
        f=self.fixture; model=AugmentedODE(f.layout,ProjectionSettings(2),ODESettings(hidden_width=8),self.transform())
        trainer=PairTrainer(model,f.solver,TrainingSettings()); old=model.conditioning.center.clone()
        trainer.step(f.pairs,f.e); torch.testing.assert_close(old,model.conditioning.center)
        with tempfile.TemporaryDirectory() as folder:
            write_checkpoint(folder,trainer,context_identity={'test':1},provenance={},sampler_state={},deployment=True)
            restored,solver=load_checkpoint(folder,layout=f.layout,context_identity={'test':1},training=False)
            self.assertEqual(restored.manifest(),model.manifest())
            for k,v in model.state_dict().items(): torch.testing.assert_close(v,restored.state_dict()[k])

    def test_branch_format_and_duplicate_instructions_preserve_public_facts(self):
        from test_p04a import example
        p,_=example()
        outputs={b:json.loads(public_text(p,[],branch=b)) for b in ('student','teacher','coconut')}
        for out in outputs.values(): self.assertEqual(out['public_input'],p.input); self.assertIn('Never duplicate',out['instruction'])
        self.assertIn('no explanation key',outputs['student']['instruction'])
        self.assertIn('explanation and targets',outputs['teacher']['instruction'])
        self.assertNotEqual(outputs['student']['instruction'],outputs['teacher']['instruction'])

    def test_teacher_student_branch_inputs_reach_distinct_encoder_calls(self):
        from test_p06 import model,AlignmentTests
        m=model(); batch=AlignmentTests().batch(); teacher=batch['input_ids'].clone(); teacher[:,0]=11
        seen=[]; hook=m.t5.encoder.register_forward_pre_hook(lambda mod,args,kwargs:seen.append(kwargs['input_ids'].clone()),with_kwargs=True)
        out=m.training_losses(**batch,teacher_input_ids=teacher,teacher_attention_mask=batch['attention_mask']); hook.remove()
        torch.testing.assert_close(seen[0],teacher); torch.testing.assert_close(seen[1],batch['input_ids'])
        self.assertFalse(out['teacher_target'].requires_grad)

    def test_qualification_budget_standard_tier_conservative_charge_and_no_second_dispatch(self):
        from p10_common import QualificationBudget
        from phi_jepa.pilot_budget import BudgetExceeded
        from test_p08_budget import PilotBudgetTests
        with tempfile.TemporaryDirectory() as tmp:
            config=PilotBudgetTests().config(); config['export_directory']=str(Path(tmp)/'export')
            budget=QualificationBudget(tmp,config); calls=[]
            def transport(payload,timeout):
                calls.append(payload)
                return {'status':'completed','service_tier':'default','usage':{'input_tokens':10,'output_tokens':2},'output':[]}
            call=budget.transport(transport); call({'model':'gpt-5.6-sol','max_output_tokens':20},1)
            self.assertEqual(calls[0]['service_tier'],'default')
            self.assertAlmostEqual(budget.read()['provider'][0]['charged_usd'],.00009)
            with self.assertRaises(BudgetExceeded): call({'model':'gpt-5.6-sol','max_output_tokens':20},1)
            self.assertEqual(len(calls),1)

    def test_capability_failures_and_unsupported_keep_every_target(self):
        from test_p04a import example
        from phi_jepa.capabilities import target_coverage,matrix
        p,_=example(); rows=target_coverage(p,[],forecast_failure='invalid_forecast')
        self.assertEqual(len(rows),len(p.input['answer_spec']))
        self.assertTrue(all(r['status']=='failure' for r in rows))
        contact=[r for r in matrix() if r['quantity'] in ('stable_stack','support_lost')]
        self.assertEqual(len(contact),2); self.assertTrue(all(not r['implemented'] for r in contact))

    def test_deployment_module_has_no_evaluator_dependency(self):
        import ast
        path=Path(__file__).resolve().parents[1]/'tools/p10_inference.py'
        tree=ast.parse(path.read_text())
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any('evaluation' in (n or '') or 'numerical' in (n or '') for n in imports))
        self.assertNotIn('references.json',path.read_text())

    def test_mixed_horizon_sampling_preserves_pairs_and_expected_transition_weights(self):
        from collections import Counter
        from phi_jepa.training.sampling import fixed_pair_batches,chronological_sequence_order
        values=list(fixed_pair_batches(list(range(7)),4,7,11))
        self.assertTrue(all(len(v)==4 for v in values))
        self.assertEqual(Counter(i for v in values for i in v),Counter({i:4 for i in range(7)}))
        seqs=[list(range(2)),list(range(8))]; order=chronological_sequence_order(seqs,10000,11)
        # This verifies sampling, not model performance. No trajectory is split.
        self.assertTrue(.77<order.count(1)/len(order)<.83)
        self.assertAlmostEqual((2/10)/2,(8/10)/8)

    def test_standalone_deployment_guard_denies_actual_private_open(self):
        import subprocess
        command=[sys.executable,'-c',"from p10_common import guard_deployment_io; import tempfile,pathlib; d=pathlib.Path(tempfile.mkdtemp()); (d/'private').mkdir(); (d/'private/truth.json').write_text('{}'); guard_deployment_io(); (d/'public.json').write_text('{}'); exec(\"try: (d/'private/truth.json').read_text()\\nexcept RuntimeError: print('denied')\\nelse: raise AssertionError('private read allowed')\")"]
        import os
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'tools')}
        result=subprocess.run(command,env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(result.stdout.strip(),'denied')

    def test_sealed_cohort_actions_require_authorization_before_execution(self):
        from types import SimpleNamespace
        from p10_cohort import public_cohort,benchmark_cohort,assessment_cohort
        run=SimpleNamespace(c={'evaluation_authorized':False})
        with patch('p10_cohort.cohort_rows',return_value=[]):
            for operation,job in ((public_cohort,'test_id--forecast'),(benchmark_cohort,'test_id'),(assessment_cohort,'test_id')):
                with self.assertRaisesRegex(ValueError,'authorization'):
                    operation(run,job)

    def test_public_cohort_restores_original_selection_after_failure(self):
        from types import SimpleNamespace
        from p10_cohort import public_cohort
        original=lambda:['original training selection']
        run=SimpleNamespace(c={'evaluation_authorized':True},rows=original)
        with patch('p10_cohort.cohort_rows',return_value=['sealed public inputs']),patch('p10_inference.forecast',side_effect=ValueError('diagnostic failure')) as forecast:
            with self.assertRaisesRegex(ValueError,'diagnostic failure'):
                public_cohort(run,'test_id--forecast')
            forecast.assert_called_once_with(run)
        self.assertIs(run.rows,original)

    def test_failed_forecast_keeps_physical_time_channel_denominators(self):
        from p10_benchmark import diagnostic_physical_rows
        from test_p04a import example
        p,_=example()
        reference={'states':p.input['states']}
        rows=diagnostic_physical_rows({'status':'failure','reason':'nonfinite_solver'},reference)
        expected=2*sum(type(m['value']) is not bool for s in reference['states'] for m in s['measurements'])
        self.assertEqual(len(rows),expected)
        self.assertTrue(all(r['status']=='failure' and r['error'] is None and r['diagnostic_failure']=='nonfinite_solver' for r in rows))

    def test_checkpoint_resume_preserves_uncheckpointed_history(self):
        from p10_common import restored_history,save,load
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp); rows=[{'update':n,'loss':1/n} for n in range(1,4)]
            save(path/'history.json',rows)
            self.assertEqual(restored_history(path,2),rows[:2])
            archive=list((path/'recovery').glob('*.json'))
            self.assertEqual(len(archive),1)
            self.assertEqual(load(archive[0])['historical_rows'],rows)
            self.assertEqual(load(path/'history.json'),rows)

    def test_unchanged_physical_diagnostics_reused_without_solves(self):
        from p10_benchmark import cached_numerical_diagnostic
        from p10_common import save
        subset=[{'sample_id':'sample','public':{'schema':'fixture'}}]
        refs={'sample':{'states':[]}}
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); records=[{'sample_id':'sample','status':'failure','reason':'fixture_failure'}]
            def measured(*args,**kwargs):
                save(kwargs['save_folder']/'sample.json',records[0])
                return {'rows':records}
            with patch('p10_numerical.diagnostic',side_effect=measured) as solve:
                args=(None,None,self.fixture.solver,{},subset,refs,folder,'checkpoint1')
                cached_numerical_diagnostic(*args)
                result=cached_numerical_diagnostic(*args)
                self.assertTrue(result['cache_hit']); self.assertEqual(result['rows'],records)
                self.assertEqual(solve.call_count,1)
                with self.assertRaisesRegex(ValueError,'separate_evidence_run'):
                    cached_numerical_diagnostic(*args[:-1],'checkpoint2')

    def test_coordinate_columns_support_semantic_quantity_triples(self):
        from p10_numerical import coordinate_columns
        columns=coordinate_columns(self.fixture.model.layout)
        self.assertEqual(len(columns),self.fixture.model.layout.d)
        self.assertTrue(any(c['group']=='physical' and '.' in c['name'] for c in columns))

    def test_multirun_aggregation_retains_failures_and_joint_scenario_cluster(self):
        from p10_aggregate import aggregate_records
        base={'role':'test_id','condition':'custom_answer','method':'codi_student','sample_id':'q','scenario_id':'scenario',
            'complete_success':False,'boolean_eligible':0,'boolean_supported':0,'boolean_correct':0,
            'targets':[{'answer_type':'scalar','success':False,'status':'failure','reason':'invalid_generation'}]}
        inputs=[({'domain':'tethered_load','seed':seed},[base]) for seed in (11,17)]
        result=aggregate_records(inputs)[0]
        self.assertEqual(result['numeric_eligible'],2)
        self.assertEqual(result['summary']['pooled']['questions'],2)
        self.assertEqual(result['summary']['pooled']['scenarios'],1)
        self.assertEqual(result['summary']['failure_categories'],{'invalid_generation':2})
        with self.assertRaisesRegex(ValueError,'duplicate'):
            aggregate_records(inputs+inputs[:1])
        with self.assertRaisesRegex(ValueError,'unmatched'):
            aggregate_records([(inputs[0][0],[base,{**base,'method':'other','sample_id':'other_question'}])])

    def test_diagnostic_compatibility_excludes_only_training_entrypoint(self):
        from p10_benchmark import diagnostic_code_unchanged
        before='import math\ndef numerical(): return 1\ndef diagnostic(): return math.pi\n'
        self.assertTrue(diagnostic_code_unchanged(before,before.replace('return 1','return 2')))
        self.assertFalse(diagnostic_code_unchanged(before,before.replace('math.pi','math.e')))
        self.assertFalse(diagnostic_code_unchanged(before,before.replace('import math','import cmath as math')))

    def test_interrupted_selection_diagnostic_recovers_saved_candidate(self):
        from types import SimpleNamespace
        from p10_common import save,load
        from p10_continuation import select_continued_methods
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/'numerical/continued_method'; deployment=folder/'checkpoints/5000/deployment'
            save(deployment/'latest.json',{'file':'weights.pt','sha256':'saved'})
            save(folder/'fit.json',{'updates':20000}); save(folder/'job.json',{'primary':True,'context_identity':{}})
            save(folder/'selected.json',{'update':4000,'score':10})
            save(root/'private/validation-references.json',{})
            run=SimpleNamespace(root=root,layout=lambda:self.fixture.layout,rows=lambda:[])
            policy={'source_methods':['method'],'checkpoint_milestones':[5000,10000,20000],'decision':'fixture'}
            with patch('p10_continuation.policy',return_value=policy),patch('p10_numerical.load_primary',return_value=(self.fixture.model,self.fixture.solver)),patch('p10_numerical.diagnostic',return_value={'rows':[],'selection_score':5}) as diagnostic:
                select_continued_methods(run)
                select_continued_methods(run)
                self.assertEqual(diagnostic.call_count,1)
            self.assertEqual(load(folder/'selected.json')['update'],5000)
            self.assertEqual(load(folder/'recovery/diagnostic-5000.json')['optimizer_updates'],0)

    def test_continuation_forks_mutable_pointers_and_preserves_source(self):
        from types import SimpleNamespace
        from p10_common import save,load
        from p10_continuation import prepare_continuation
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'numerical/method'; resume=source/'resume'; resume.mkdir(parents=True)
            (resume/'original.pt').write_bytes(b'fixture immutable checkpoint')
            save(resume/'latest.json',{'file':'original.pt','sha256':'fixture'})
            save(source/'fit.json',{'updates':4000,'status':'complete','seconds':2.})
            save(source/'selected.json',{'directory':'checkpoints/4000/deployment','update':4000})
            save(source/'history.json',[{'update':i} for i in range(1,4001)]); save(source/'initialization.json',{'fresh':True})
            (source/'checkpoints/4000').mkdir(parents=True); (source/'milestones/4000').mkdir(parents=True)
            proposal=root/'policy.json'; save(proposal,{'source_methods':['method'],'source_updates':4000,'updates':20000})
            before={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            with patch('p10_continuation.POLICY',proposal): prepare_continuation(SimpleNamespace(root=root))
            target=root/'numerical/continued_method'
            self.assertFalse((target/'resume').is_symlink())
            self.assertTrue((target/'resume/original.pt').is_symlink())
            save(target/'resume/latest.json',{'file':'new.pt'})
            save(target/'history.json',[{'update':5000}])
            self.assertEqual({p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()},before)
            self.assertEqual(load(target/'continuation_origin.json')['source_updates'],4000)


if __name__=='__main__': unittest.main()
