import copy,json,tempfile,unittest
from pathlib import Path
import torch
from transformers import T5Config,T5ForConditionalGeneration
from phi_jepa.baselines.custom_t5 import CustomT5,CustomSettings,eos_positions,post_answer_hidden
from phi_jepa.baselines.custom_checkpoint import save_checkpoint,load_checkpoint
from phi_jepa.baselines.custom_io import compose_hybrid,parse_typed_answer,training_targets,public_text,TextCodec,decode_result
from phi_jepa.integration.contracts import PublicProblem


def model(method='codi_inspired_t5_distillation'):
    torch.manual_seed(7)
    return CustomT5(T5ForConditionalGeneration(T5Config(vocab_size=32,d_model=16,d_ff=32,num_layers=2,num_decoder_layers=2,num_heads=2,d_kv=8,dropout_rate=0.,decoder_start_token_id=0,eos_token_id=1,pad_token_id=0)),CustomSettings(method,latents=2))


class AlignmentTests(unittest.TestCase):
    def setUp(self): torch.set_num_threads(2)
    def batch(self):
        return dict(input_ids=torch.tensor([[4,5,1],[6,1,0]]),attention_mask=torch.tensor([[1,1,1],[1,1,0]]),teacher_labels=torch.tensor([[7,8,9,1],[4,5,1,-100]]),student_labels=torch.tensor([[9,10,1],[5,1,-100]]))
    def test_eos_shift_and_no_truncation(self):
        m=model(); b=self.batch(); labels=b['student_labels']; pos=eos_positions(labels,1)
        shifted=m.t5._shift_right(labels)
        self.assertEqual(pos.tolist(),[2,1]); self.assertEqual(shifted[0,pos[0]].item(),10)
        hidden=torch.arange(2*3*2).reshape(2,3,2); out,_=post_answer_hidden(hidden,labels,1)
        self.assertEqual(out.tolist(),[hidden[0,2].tolist(),hidden[1,1].tolist()])
        for bad in ([[3,4]],[[1,3]],[[3,1,1]],[[3,-100,1]]):
            with self.assertRaises(ValueError): eos_positions(torch.tensor(bad),1)
    def test_alignment_teacher_graph_detached_shared_backbone_student_grad(self):
        m=model(); out=m.training_losses(**self.batch())
        out['teacher_hidden'].retain_grad(); out['student_hidden'].retain_grad(); out['alignment'].backward()
        self.assertIsNone(out['teacher_hidden'].grad); self.assertGreater(out['student_hidden'].grad.abs().sum().item(),0)
        self.assertFalse(out['teacher_target'].requires_grad)
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in m.teacher_proj.parameters()))
        self.assertGreater(sum(p.grad.abs().sum().item() for p in m.student_proj.parameters() if p.grad is not None),0)
        self.assertGreater(sum(p.grad.abs().sum().item() for p in m.t5.parameters() if p.grad is not None),0)
    def test_teacher_ce_updates_backbone(self):
        m=model(); out=m.training_losses(**self.batch()); out['teacher_hidden'].retain_grad(); out['teacher_ce'].backward()
        self.assertGreater(out['teacher_hidden'].grad.abs().sum().item(),0)
        self.assertGreater(m.t5.shared.weight.grad.abs().sum().item(),0)
        self.assertTrue(all(p.grad is None for p in m.student_proj.parameters()))
    def test_checkpoint_exact_continuation_fixed_projection(self):
        from dataclasses import replace
        from phi_jepa.baselines.t5_memory import install_query_blocks
        m=model(); m.settings=replace(m.settings,encoder_query_chunk_size=2); install_query_blocks(m.t5,2)
        opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=.001)
        fixed=copy.deepcopy(m.teacher_proj.state_dict()); b=self.batch()
        def step(m,opt):
            opt.zero_grad(); loss=m.training_losses(**b)['loss']; loss.backward(); opt.step()
        step(m,opt)
        identity={'data':'test-only','format':'v1','generation':{'num_beams':1}}
        with tempfile.TemporaryDirectory() as d:
            save_checkpoint(d,m,opt,identity=identity,updates=1)
            restored,ro,updates=load_checkpoint(d,identity=identity,training=True)
            self.assertEqual(updates,1); step(m,opt); step(restored,ro)
            for k,v in m.state_dict().items(): self.assertTrue(torch.equal(v,restored.state_dict()[k]),k)
            for k,v in fixed.items(): self.assertTrue(torch.equal(v,m.teacher_proj.state_dict()[k]))
            ids={id(p) for group in ro.param_groups for p in group['params']}
            self.assertTrue(all(id(p) not in ids for p in restored.teacher_proj.parameters()))
            with self.assertRaises(ValueError): load_checkpoint(d,identity={'wrong':True})
    def test_coconut_independent_latent_gradients(self):
        m=model('coconut_inspired_t5_gru'); b=self.batch(); b.pop('student_labels'); out=m.training_losses(**b); out['loss'].backward()
        self.assertGreater(m.latent_queries.grad.abs().sum().item(),0)
    def test_query_block_attention_matches_full_outputs_and_gradients(self):
        from phi_jepa.baselines.t5_memory import install_query_blocks
        original=model(); blocked=copy.deepcopy(original)
        install_query_blocks(blocked.t5,2)
        # Multiple layers exercise shared relative bias recomputation. Compare all
        # parameter gradients, including the first-layer relative-bias weights.
        b=self.batch(); a=original.training_losses(**b); z=blocked.training_losses(**b)
        for key in ('loss','teacher_ce','student_ce','alignment'):
            torch.testing.assert_close(a[key],z[key],rtol=1e-5,atol=1e-6)
        a['loss'].backward(); z['loss'].backward()
        for (name,p),(other,q) in zip(original.named_parameters(),blocked.named_parameters()):
            self.assertEqual(name,other)
            if p.grad is not None: torch.testing.assert_close(p.grad,q.grad,rtol=3e-4,atol=2e-6,msg=name)
    def test_generation_interface_has_no_target(self):
        import inspect
        self.assertEqual(set(inspect.signature(CustomT5.generate).parameters),{'self','input_ids','attention_mask','branch','generation'})
    def test_padding_does_not_change_loss_or_eos_alignment(self):
        m=model(); b=self.batch()
        a=m.training_losses(**b)
        padded={**b,'teacher_labels':torch.nn.functional.pad(b['teacher_labels'],(0,3),value=-100),'student_labels':torch.nn.functional.pad(b['student_labels'],(0,3),value=-100)}
        z=m.training_losses(**padded)
        for key in ('teacher_ce','student_ce','alignment','loss'): torch.testing.assert_close(a[key],z[key],rtol=1e-6,atol=1e-6)
        z['student_hidden'].retain_grad(); z['loss'].backward()
        self.assertEqual(z['student_hidden'].grad[:,-3:].abs().sum().item(),0.)
    def test_hybrid_fallback_observable_no_gold(self):
        good={'status':'success','answer':{'targets':[{'value':False}],'explanation':'generated'}}
        fail={'status':'generation_or_parse_failure','reason':'target_count','answer':None}
        self.assertFalse(compose_hybrid(good,good)['fallback_used'])
        h=compose_hybrid(fail,good); self.assertTrue(h['fallback_used']); self.assertEqual(h['fallback_trigger'],'target_count')
        self.assertFalse(h['teacher_explanation_fed_to_student'])
        self.assertEqual(compose_hybrid(fail,fail)['status'],'generation_or_parse_failure')


class TypedIOTests(unittest.TestCase):
    def example(self):
        from test_p04a import example,replace_input
        p,_=example(); inp=p.input; boolean=inp['answer_spec'][0]
        number={**boolean,'target_id':'load:angle','quantity':'swing_angle','answer_type':'number','unit':'rad'}
        vector={**boolean,'target_id':'load:position','quantity':'position','answer_type':'vector','unit':'m'}
        inp['answer_spec']=[boolean,number,vector]; p=replace_input(p,inp)
        return p,{'explanation':'Descriptive only.','structured_label':[{'target_id':s['target_id'],'unit':s['unit'],'frame':s['frame'],'value':v} for s,v in zip(p.input['answer_spec'],[False,-1.23e-4,[-2.,.03,4e-5]])]}
    def test_typed_supervision_and_units_preserved(self):
        p,r=self.example(); teacher,student=training_targets(p,r)
        out=parse_typed_answer(student,p,explanation_required=False)
        self.assertIs(out['targets'][0]['value'],False); self.assertEqual(out['targets'][1]['value'],-.000123)
        self.assertEqual(out['targets'][2]['value'],[-2.,.03,.00004]); self.assertEqual(out['targets'][1]['unit'],'rad')
        self.assertEqual(parse_typed_answer(teacher,p,explanation_required=True)['explanation'],r['explanation'])
        for value in (0,'false',None):
            broken=json.loads(student); broken['targets'][0]['value']=value
            with self.assertRaises(ValueError): parse_typed_answer(json.dumps(broken),p,explanation_required=False)
        broken=json.loads(student); broken['targets'][1]['unit']='m'
        with self.assertRaises(ValueError): parse_typed_answer(json.dumps(broken),p,explanation_required=False)
    def test_private_inference_enrichment_rejected(self):
        p,r=self.example()
        with self.assertRaises(ValueError): public_text(p,{'nested':{'structured_label':r['structured_label']}})
        text=public_text(p,{'note':'public'})
        self.assertNotIn(r['explanation'],text)
    def test_failed_cases_count_in_shared_evaluator(self):
        from phi_jepa.typed_evaluation import evaluate_targets
        p,r=self.example(); result=evaluate_targets(p,r,[],method='test',failure='generation_missing_EOS')
        self.assertEqual(result['eligible_questions'],1); self.assertEqual(result['eligible_targets'],3)
        self.assertEqual(result['valid_targets'],0); self.assertFalse(result['complete_success'])
    def test_codec_collision_and_no_truncation(self):
        class FakeTokenizer:
            unk_token_id=2; eos_token_id=1; pad_token_id=0
            def encode(self,s,add_special_tokens=True,**kwargs): return [2 if c in '{}^' else ord(c)+3 for c in s]+([1] if add_special_tokens else [])
            def decode(self,ids,**kwargs): return ''.join(chr(i-3) for i in ids)
        codec=TextCodec(FakeTokenizer()); s='{"x":"ZXQ00007BZXQ  ^\\\n","v":-1.23e-4}'
        ids=codec.tokens(s,1000); self.assertEqual(codec.generated_text([0]+ids),s)
        with self.assertRaises(ValueError): codec.tokens(s,2)
        with self.assertRaises(ValueError): codec.generated_text(ids[:-1])


if __name__=='__main__': unittest.main()
