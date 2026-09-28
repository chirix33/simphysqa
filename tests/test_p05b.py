"""Behavior checks for independently trained numerical-only text comparisons."""
from collections import Counter
from dataclasses import replace,asdict
import json
from pathlib import Path
import tempfile
import unittest
import torch
from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import PublicProblem,Identity
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import make_pairs
from phi_jepa.baselines.conventional import NumericalComparator,BaselineSettings,forecast
from phi_jepa.baselines.training import ComparatorTrainer,validate_pairs
from phi_jepa.baselines.checkpoint import save_checkpoint,load_checkpoint
from phi_jepa.solvers.rk4 import SolveStats,SolverSettings
from phi_jepa.inference.readout import named_forecast
from test_p02a import fixture


class P05bTests(unittest.TestCase):
    def setUp(self):
        pub,ref=fixture(); self.p=PublicProblem.parse(pub); inp=self.p.input
        self.layout=StateLayout.build(inp['states'][-1],inp,'state_plus_fixed_conditioning','train')
        mult=Counter({digest(('robotic_arm','g',a,b)):1 for a,b in ((.2,.22),(.22,.24))})
        self.pairs=list(make_pairs(self.p,ref,Identity('sample','g','g','robotic_arm','train'),self.layout,'fixture',mult,context_mode='enriched',
            enrichment={'public_input':inp,'notes':[]},duplicate_policy='equal_question_pairs'))
        self.e=torch.tensor([[.3,.8],[.3,.8]])

    def model(self,method): return NumericalComparator(self.layout,BaselineSettings(method,embedding_width=2,hidden_width=8))

    def test_ode_has_independent_trainable_p_constant_within_rollout(self):
        a=self.model('constant_context_text_ode'); b=self.model('constant_context_text_ode')
        self.assertNotEqual(a.projection.linear.weight.data_ptr(),b.projection.linear.weight.data_ptr())
        initial=b.projection.linear.weight.detach().clone(); trainer=ComparatorTrainer(a)
        log=trainer.step(self.pairs,self.e)
        self.assertGreater(log['projection_gradient_norm_after_clip'],0.)
        self.assertTrue(torch.equal(initial,b.projection.linear.weight))
        calls=[]; original=a.next_state
        def wrapped(n,p,*args,**kwargs): calls.append(p.detach().clone()); return original(n,p,*args,**kwargs)
        a.next_state=wrapped
        result,usage=forecast(a,self.p,self.e[:1],[.2,.22,.24])
        self.assertTrue(torch.equal(calls[0],calls[1]))
        self.assertEqual(len(result.predictions[0].values),self.layout.d)
        self.assertEqual(usage['solver']['nfe'],8)
        mapped=named_forecast(self.p,self.layout,result,numerical_only=True)
        self.assertEqual(len(mapped['states']),2)

    def test_lr_fixed_projection_rank_fit_and_interval_rejection(self):
        model=self.model('fixed_projection_lr'); before=model.projection.linear.weight.clone()
        n,y=validate_pairs(model,self.pairs,self.e); info=model.fit_lr(n,y,self.e)
        json.dumps(info,allow_nan=False)
        diagnostics=model.lr_diagnostics(n,y,self.e)
        self.assertEqual(diagnostics['rank'],info['rank'])
        self.assertFalse(any(p.requires_grad for p in model.projection.parameters()))
        self.assertTrue(torch.equal(before,model.projection.linear.weight)); self.assertTrue(info['underdetermined'])
        with torch.no_grad(): predicted,_=model.next_state(n,model.projection(self.e),.2,.22,solver=SolverSettings(),stats=SolveStats())
        torch.testing.assert_close(predicted,y,rtol=1e-5,atol=1e-5)
        with self.assertRaises(ValueError): model.next_state(n,model.projection(self.e),.2,.23,solver=SolverSettings(),stats=SolveStats())

    def test_rnn_chronology_hidden_carry_and_reset(self):
        model=self.model('constant_context_text_rnn'); trainer=ComparatorTrainer(model)
        log=trainer.step(self.pairs,self.e); self.assertGreater(log['projection_gradient_norm_after_clip'],0.)
        with self.assertRaises(ValueError): trainer.step(list(reversed(self.pairs)),self.e)
        hiddens=[]; original=model.next_state
        def wrapped(n,p,*args,**kwargs): hiddens.append(kwargs.get('hidden')); return original(n,p,*args,**kwargs)
        model.next_state=wrapped
        first,_=forecast(model,self.p,self.e[:1],[.2,.22,.24]); second,_=forecast(model,self.p,self.e[:1],[.2,.22,.24])
        self.assertIsNone(hiddens[0]); self.assertIsNotNone(hiddens[1]); self.assertIsNone(hiddens[2])
        self.assertEqual(first,second)

    def test_rnn_equal_transitions_not_equal_sequences(self):
        model=self.model('constant_context_text_rnn'); trainer=ComparatorTrainer(model,learning_rate=1e-12)
        other=replace(self.pairs[0],identity=Identity('other','other','other','robotic_arm','train'))
        pairs=[*self.pairs,other]; e=torch.cat((self.e,self.e[:1])); n,y=validate_pairs(model,pairs,e)
        with torch.no_grad():
            p=model.projection(e); a,h=model.next_state(n[:1],p[:1],.2,.22,solver=SolverSettings(),stats=SolveStats())
            b,_=model.next_state(n[1:2],p[1:2],.22,.24,solver=SolverSettings(),stats=SolveStats(),hidden=h)
            c,_=model.next_state(n[2:],p[2:],.2,.22,solver=SolverSettings(),stats=SolveStats())
            expected=float((torch.cat((a,b,c))-y).square().mean())
        self.assertAlmostEqual(trainer.step(pairs,e)['numerical_mse'],expected,places=4)
        with self.assertRaises(ValueError): trainer.step([replace(other,weight=.5)],e[:1])

    def test_checkpoint_resume_and_method_role_isolation(self):
        for method in ('constant_context_text_ode','constant_context_text_rnn'):
            model=self.model(method); trainer=ComparatorTrainer(model); trainer.step(self.pairs,self.e)
            with tempfile.TemporaryDirectory() as temp:
                save_checkpoint(temp,model,context_identity={'fixture':1},provenance={'pairs':['a','b']},trainer=trainer,sampler={'step':1})
                model2,trainer2,sampler,_=load_checkpoint(temp,layout=self.layout,context_identity={'fixture':1},method=method,training=True)
                trainer.step(self.pairs,self.e); trainer2.step(self.pairs,self.e)
                self.assertEqual(sampler,{'step':1})
                for key,value in model.state_dict().items(): torch.testing.assert_close(value,model2.state_dict()[key],rtol=0,atol=0)
                with self.assertRaises(ValueError): load_checkpoint(temp,layout=self.layout,context_identity={'fixture':1},method='fixed_projection_lr',training=True)
                with self.assertRaises(ValueError): load_checkpoint(temp,layout=self.layout,context_identity={'fixture':1},method=method,training=False)

    def test_nonfinite_or_wrong_split_never_trains(self):
        model=self.model('constant_context_text_ode'); trainer=ComparatorTrainer(model)
        wrong=replace(self.pairs[0],identity=Identity('x','g','g','robotic_arm','validation'))
        with self.assertRaises(ValueError): trainer.step([wrong],self.e[:1])
        self.assertEqual(trainer.failures,1); self.assertEqual(trainer.updates,0)
        e=self.e.clone(); e[0,0]=float('nan')
        with self.assertRaises(ValueError): trainer.step(self.pairs,e)

    def test_runtime_controls_do_not_claim_retraining_or_hide_failure(self):
        from phi_jepa.baselines.controls import runtime_control
        from test_p04a import example
        p,f=example(); calls=[]
        def assess(): calls.append('assessment'); return {'status':'partial'}
        def answer(forecast,outcomes): calls.append('answer'); return {'forecast_present':forecast is not None}
        result=runtime_control('without_fixed_assessment',p,f,checkpoint_sha256='fixture',assess=assess,answer=answer)
        self.assertEqual(calls,['answer']); self.assertEqual(result['kind'],'runtime_intervention_not_retraining')
        def failure(*args): raise ValueError('fixture failure')
        result=runtime_control('without_fallback',p,f,checkpoint_sha256='fixture',assess=assess,answer=failure)
        self.assertIsNone(result['answer']); self.assertFalse(result['fallback_used']); self.assertEqual(result['failure'],'answer_failure')
        result=runtime_control('public_only_answer',p,f,checkpoint_sha256='fixture',assess=assess,answer=answer)
        self.assertFalse(result['answer']['forecast_present'])
        result=runtime_control('without_fallback',p,f,checkpoint_sha256='fixture',assess=assess,answer=answer,fallback_active=False)
        self.assertTrue(result['no_op'])

    def test_no_text_ablation_has_no_projection_or_embedding_path(self):
        model=NumericalComparator(self.layout,BaselineSettings('no_text_conditioning',embedding_width=0,hidden_width=8))
        self.assertIsNone(model.projection)
        self.assertFalse(any('projection' in name for name,_ in model.named_parameters()))
        pairs=[replace(p,context_mode='public_base_for_offline_audit') for p in self.pairs]
        trainer=ComparatorTrainer(model); log=trainer.step(pairs,None)
        self.assertIsNone(log['projection_gradient_norm_after_clip'])
        result,_=forecast(model,self.p,None,[.2,.22,.24])
        self.assertEqual(len(result.predictions[0].values),self.layout.d)
        with self.assertRaises(ValueError): forecast(model,self.p,self.e[:1],[.2,.22,.24])

    def test_no_enrichment_keeps_full_target_gradients_and_default_primary_gate(self):
        from phi_jepa.models.augmented_ode import AugmentedODE,ODESettings
        from phi_jepa.models.context_projection import ProjectionSettings
        from phi_jepa.training.pairs import PairTrainer,TrainingSettings
        from phi_jepa.training.checkpoint import write_checkpoint,load_checkpoint as load_primary
        pub,ref=fixture(); p=PublicProblem.parse(pub)
        counts=Counter({r.transition_id:1 for r in self.pairs})
        pairs=list(make_pairs(p,ref,self.pairs[0].identity,self.layout,'base',counts,duplicate_policy='equal_question_pairs'))
        self.assertTrue(all('public_enrichment' not in pair.context_json for pair in pairs))
        model=AugmentedODE(self.layout,ProjectionSettings(2),ODESettings(hidden_width=8))
        primary=PairTrainer(model,SolverSettings(),TrainingSettings())
        with self.assertRaises(ValueError): primary.step(pairs,self.e)
        trainer=PairTrainer(model,SolverSettings(),TrainingSettings(context_mode='public_base_for_offline_audit'))
        self.assertGreater(trainer.step(pairs,self.e)['projection_gradient_norm_after_clip'],0.)
        n=torch.tensor([r.n_current for r in pairs]); y=torch.tensor([r.n_next for r in pairs])
        x,target,projected=model.projection.pair(n,y,self.e,layout_sha256=self.layout.sha256)
        self.assertTrue(target.requires_grad); self.assertEqual(target.shape[-1],2*self.layout.d)
        torch.testing.assert_close(target[:,self.layout.d:],projected)
        with tempfile.TemporaryDirectory() as tmp:
            write_checkpoint(tmp,trainer,context_identity={'variant':'no_enrichment'},provenance={'fixture':True},sampler_state={})
            resumed,_,_=load_primary(tmp,layout=self.layout,context_identity={'variant':'no_enrichment'},training=True)
            resumed.step(pairs,self.e)
            self.assertEqual(resumed.updates,2)


if __name__=='__main__': unittest.main()
