"""Training-input timing only; discarded models, no held-out outcomes."""
import json,sys,time,subprocess,os,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from phi_jepa.pilot_budget import save

OUT=Path('/home/aashraf/phi-jepa/p11-tonight-01'); NATIVE=OUT.parent

def worker(short):
    import torch,gc
    from transformers import AutoTokenizer,T5ForConditionalGeneration
    from phi_jepa.baselines.custom_t5 import CustomT5,CustomSettings
    from phi_jepa.baselines.custom_io import TextCodec,public_text
    from phi_jepa.integration.contracts import PublicProblem
    c=json.loads((ROOT/'configs/custom_p06.json').read_text());torch.set_num_threads(2)
    tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True);tok.model_max_length=c['max_input_tokens'];codec=TextCodec(tok)
    records=json.loads((NATIVE/'p06-profile/training-prepared.json').read_text());results=[]
    for row in sorted(records,key=lambda r:r['public']['input']['domain']):
        assert row['split']=='train';p=PublicProblem.parse(row['public']);torch.manual_seed(11);torch.cuda.manual_seed_all(11)
        backbone=T5ForConditionalGeneration.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
        settings=CustomSettings('coconut_inspired_t5_gru' if short=='coconut' else 'codi_inspired_t5_distillation',seed=11,latents=c['latents'],teacher_ce_weight=c['teacher_ce_weight'],student_ce_weight=c['student_ce_weight'],distillation_weight=c['distillation_weight'],smoothness_weight=c[short+'_smoothness'],encoder_query_chunk_size=c['encoder_query_chunk_size'])
        model=CustomT5(backbone,settings).cuda();model.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.train()
        opt=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=c['optimizer']['learning_rate'],weight_decay=c['optimizer']['weight_decay'])
        branch='student' if short=='codi' else 'coconut'; ids=codec.tokens(public_text(p,row['enrichment'],branch=branch),c['max_input_tokens'])
        data={'input_ids':torch.tensor([ids],device='cuda'),'attention_mask':torch.ones((1,len(ids)),dtype=torch.long,device='cuda'),'teacher_labels':torch.tensor([row['teacher_labels']],device='cuda')}
        if short=='codi':
            teacher=codec.tokens(public_text(p,row['enrichment'],branch='teacher'),c['max_input_tokens']);data.update(student_labels=torch.tensor([row['student_labels']],device='cuda'),teacher_input_ids=torch.tensor([teacher],device='cuda'),teacher_attention_mask=torch.ones((1,len(teacher)),dtype=torch.long,device='cuda'))
        torch.cuda.reset_peak_memory_stats();measure=[]
        for i in range(2):
            torch.cuda.synchronize();start=time.monotonic();opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.bfloat16): result=model.training_losses(**data)
            result['loss'].backward();torch.nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad),c['optimizer']['gradient_clip'],error_if_nonfinite=True);opt.step();torch.cuda.synchronize()
            measure.append(time.monotonic()-start);del result
        results.append({'domain':p.input['domain'],'sample_id':p.sample_id,'source_split':'train','method':short,'input_tokens':len(ids),'teacher_target_tokens':len(row['teacher_labels']),'student_target_tokens':len(row['student_labels']),'step_seconds':measure,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'discarded_updates':2,'heldout_outcomes_opened':False})
        save(OUT/'timing'/f'{short}.json',results);print(json.dumps(results[-1]),flush=True)
        del model,backbone,opt,data;gc.collect();torch.cuda.empty_cache()

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    if len(sys.argv)>1: worker(sys.argv[1])
    else:
        start=time.time();deadline=start+780;operations=[]
        for short in ('coconut','codi'):
            path=OUT/'timing'/f'{short}.log';path.parent.mkdir(exist_ok=True)
            with path.open('w') as f:
                p=subprocess.Popen([str(NATIVE/'.venvs'/f'phi-{short}-custom/bin/python'),str(Path(__file__).resolve()),short],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'})
                began=time.time()
                while p.poll() is None and time.time()<deadline: time.sleep(.5)
                if p.poll() is None: os.killpg(p.pid,signal.SIGTERM);p.wait()
            operations.append({'method':short,'gpu_wall_seconds':time.time()-began,'exit_code':p.returncode})
            save(OUT/'timing/supervisor.json',{'started':start,'deadline':deadline,'operations':operations,'seconds':time.time()-start,'maximum_seconds':780})
            if p.returncode: break
