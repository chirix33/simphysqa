"""Offline boundary tests for the three local baseline conditions and expanded sampler."""
import json
import unittest
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from phi_jepa.artifacts import digest
from phi_jepa.providers.local_answer import LocalAnswerSettings,prepare_tokens,messages,separate_output,LocalAnswerBackend,InputLengthFailure,verify_cached_record
from phi_jepa.providers.openai_answer import parse_answer,AnswerParseFailure
from phi_jepa.training.sampling import fixed_pair_batches
from test_p04a import example,llm_result
from phi_jepa.inference.readout import target_result


class Tokenizer:
    chat_template='official-fixture-template'
    unk_token_id=0
    def apply_chat_template(self,rows,**kwargs):
        self.rows,self.kwargs=rows,kwargs
        return [1,2,3]
    def convert_tokens_to_ids(self,t):return 99
    def decode(self,ids,**kwargs):return ''.join(map(str,ids))


class LocalTests(unittest.TestCase):
    def test_qualified_followup_root_is_hashed_and_preserves_historical_root(self):
        from unittest.mock import patch
        from p12_local import qualified_artifact_root
        import p12_local
        with patch('p12_local.load',return_value={'llama31_8b_direct':{'qualification_root':'/new/llama','qualification_sha256':'expected','acquisition_sha256':'expected'}}),patch('p12_local.file_hash',return_value='expected'):
            self.assertEqual(qualified_artifact_root('llama31_8b_direct'),Path('/new/llama'))
        with patch('p12_local.load',return_value={'qwen3_8b_direct':{}}):
            self.assertEqual(qualified_artifact_root('qwen3_8b_direct'),p12_local.OUT)
        with patch('p12_local.load',return_value={'llama31_8b_direct':{'qualification_sha256':'expected'}}),patch('p12_local.file_hash',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'identity changed'):qualified_artifact_root('llama31_8b_direct')

    def settings(self,thinking=False):
        return LocalAnswerSettings('Qwen/Qwen3-8B','a'*40,'a'*40,digest(Tokenizer.chat_template),(('test','fixture'),),thinking,max_input_and_output=20,max_new_tokens=5)
    def test_official_template_switch_and_output_reservation(self):
        p,_=example();t=Tokenizer()
        for thinking in (False,True):
            prepare_tokens(t,p,'public instruction',self.settings(thinking))
            self.assertEqual(t.kwargs['enable_thinking'],thinking)
            self.assertFalse(t.kwargs['truncation'])
            self.assertNotIn('tools',t.kwargs)
        llama=replace(self.settings(),model='meta-llama/Llama-3.1-8B-Instruct',enable_thinking=None)
        prepare_tokens(t,p,'instruction',llama);self.assertNotIn('enable_thinking',t.kwargs)
        with self.assertRaises(ValueError):replace(llama,enable_thinking=False)
        with self.assertRaises(InputLengthFailure) as over:prepare_tokens(t,p,'instruction',replace(self.settings(),max_input_and_output=7))
        self.assertEqual((over.exception.input_tokens,over.exception.output_reserve),(3,5))
        with self.assertRaises(ValueError):prepare_tokens(t,p,'instruction',replace(self.settings(),template_sha256='other'))
    def test_reasoning_is_not_parsed_as_final_answer(self):
        value=separate_output([10,11,99,12,13],Tokenizer(),True)
        self.assertEqual(value['reasoning_token_ids'],[10,11,99]);self.assertEqual(value['final_token_ids'],[12,13])
        incomplete=separate_output([10,11],Tokenizer(),True)
        self.assertEqual(incomplete['final_text'],'');self.assertEqual(incomplete['separation_failure'],'missing_thinking_end')
    def test_request_identities_bind_model_template_mode_runtime_and_decode(self):
        p,_=example();obj=object.__new__(LocalAnswerBackend);obj.instruction='same public prompt'
        base=self.settings();identities=[]
        for s in (base,replace(base,enable_thinking=True),replace(base,revision='b'*40),replace(base,tokenizer_revision='c'*40),
                  replace(base,template_sha256='different'),replace(base,max_new_tokens=6),replace(base,runtime=(('test','different'),)),
                  replace(base,model='meta-llama/Llama-3.1-8B-Instruct',enable_thinking=None)):
            obj.settings=s;identities.append(digest(obj.request_identity(p,[1,2,3])))
        self.assertEqual(len(set(identities)),len(identities))
        identity=obj.request_identity(p,[1,2,3]);record={'identity':identity,'request_sha256':digest(identity)}
        verify_cached_record(record,identity)
        with self.assertRaises(ValueError):verify_cached_record(record,{**identity,'tools':True})
    def test_public_problem_and_strict_target_binding(self):
        p,_=example();payload=json.loads(messages(p,'instruction')[1]['content'])
        self.assertEqual(payload['public_problem'],p.input)
        self.assertEqual(set(payload),{'public_problem','required_answer_schema'})
        with self.assertRaises(ValueError):messages({'reference':'hidden'},'instruction')
        row=target_result(p.input['answer_spec'][0],'supported',value=False,source='direct')
        answer=llm_result(p,[row]);parse_answer(p,json.dumps(answer),[],boolean_policy='direct_prediction')
        answer['targets'][0]['unit']='wrong'
        with self.assertRaises(AnswerParseFailure):parse_answer(p,json.dumps(answer),[],boolean_policy='direct_prediction')
    def test_all_pairs_equal_exposure_fixed_batches_with_carried_tails(self):
        batches=list(fixed_pair_batches(list(range(17)),8,7,11));flat=[v for b in batches for v in b]
        self.assertTrue(all(len(b)==8 for b in batches))
        for index in range(3):self.assertEqual(set(flat[index*17:(index+1)*17]),set(range(17)))
        self.assertEqual(len(flat),56)
    def test_full_training_requires_new_authority_and_complete_contexts(self):
        from p12_train import train
        from p12_training_plan import coverage_check
        with self.assertRaisesRegex(ValueError,'authorization'):train({'enabled':False},'driving')
        rows=[{'sample_id':s,'domain':'driving','split':'train','scenario_id':s,'split_group':s,'public_sha256':s} for s in ('a','b')]
        coverage=[{**rows[0],'embedding_path':'cache','enrichment_path':'notes'},{**rows[1],'embedding_path':None}]
        origins=[{'sample_id':s,'domain':'driving','split':'train','status':'verified'} for s in ('a','b')]
        result=coverage_check(rows,coverage,origins,deep=False)
        self.assertFalse(result['ready']);self.assertEqual(result['missing'],['b'])
    def test_token_time_caps_and_runtime_failure_cannot_become_predictions(self):
        import torch
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        from contextlib import ExitStack
        p,_=example();tokenizer=Tokenizer();tokenizer.pad_token_id=0;tokenizer.eos_token_id=99
        model=SimpleNamespace(eval=lambda:None,parameters=lambda:[],device='cpu',generation_config=SimpleNamespace(eos_token_id=99),generate=Mock())
        backend=LocalAnswerBackend(model,tokenizer,replace(self.settings(),max_new_tokens=2),'instruction')
        with ExitStack() as stack:
            for name in ('synchronize','reset_peak_memory_stats','manual_seed_all','max_memory_allocated','max_memory_reserved'):
                stack.enter_context(patch('torch.cuda.'+name,return_value=0))
            parser=stack.enter_context(patch('phi_jepa.providers.local_answer.parse_answer'))
            for tokens,reason in (([50,51],'token_cap'),([50],'time_cap')):
                model.generate.return_value=torch.tensor([[1,2,3,*tokens]])
                record=backend.answer(p)
                self.assertEqual(record['status'],'generation_incomplete');self.assertEqual(record['failure'],reason)
                self.assertIsNone(record['answer']);self.assertEqual(record['generated_token_ids'],tokens)
            parser.assert_not_called()
            model.generate.side_effect=RuntimeError('fixture runtime failure')
            record=backend.answer(p);self.assertEqual(record['status'],'runtime_failure');self.assertEqual(record['output_tokens'],0)
            self.assertIsNone(record['answer'])
    def test_study_requires_completed_fits_and_seals_selected_checkpoints(self):
        import tempfile
        import p12_common as common
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            native=Path(directory);qualification=native/'qualification';qualification.mkdir()
            (qualification/'confirmation-public.json').write_text('[]')
            study=native/'study';proposal={'enabled':True,'authorization':'fixture only','implementation_sha256':'fixture',
                 'study_root':str(study),'domains':{'driving':{}},'confirmation_public_sha256':common.file_hash(qualification/'confirmation-public.json')}
            with patch.object(common,'NATIVE',native),patch.object(common,'OUT',qualification),patch.object(common,'implementation_identity',return_value='fixture'):
                with self.assertRaisesRegex(ValueError,'complete'):common.study_lock(proposal)
                (study/'driving').mkdir(parents=True)
                (study/'driving/complete.json').write_text('{}');(study/'driving/selected.json').write_text('{"update":1}')
                first=common.study_lock(proposal);self.assertEqual(common.study_lock(proposal),first)
                (study/'driving/selected.json').write_text('{"update":2}')
                with self.assertRaisesRegex(ValueError,'changed'):common.study_lock(proposal)
    def test_failed_and_unsupported_answers_remain_in_accuracy_denominators(self):
        from phi_jepa.typed_evaluation import evaluate_targets
        from p12_evaluate import summarize
        p,_=example();spec=p.input['answer_spec'][0]
        truth={'structured_label':[{**spec,'value':False}]}
        valid=target_result(spec,'supported',value=False,source='fixture')
        unsupported=target_result(spec,'unsupported',reason='fixture unsupported',source='fixture')
        records=[]
        for i,(rows,failure) in enumerate((([valid],None),([unsupported],None),([], 'token_cap'))):
            r=evaluate_targets(p,truth,rows,method='fixture',failure=failure)
            for t in r['targets']:t['quantity']=spec['quantity']
            records.append({**r,'domain':p.input['domain'],'distribution':'id','scenario_id':str(i),
                            'typed_output_valid':not failure,'generation_failure':failure})
        result=summarize(records)
        self.assertEqual(result['eligible_questions'],3);self.assertEqual(result['unsupported_targets'],1)
        self.assertEqual(result['grouped']['pooled']['complete_success_rate'],1/3)
        self.assertEqual(result['boolean_accuracy_all_eligible'],1/3)
        self.assertEqual(result['grouped']['pooled']['boolean_accuracy_supported'],1)

if __name__=='__main__':unittest.main()
