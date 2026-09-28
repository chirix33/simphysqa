"""Two complete passes on the frozen matched cohort, final checkpoint only."""
from p11_common import *
from p10_custom import train_inputs,inputs
from hashlib import sha256
import random,torch
from transformers import AutoTokenizer,T5ForConditionalGeneration
from phi_jepa.baselines.custom_t5 import CustomT5,CustomSettings
from phi_jepa.baselines.custom_checkpoint import save_checkpoint,load_checkpoint
from phi_jepa.baselines.custom_io import TextCodec,decode_result
from phi_jepa.integration.contracts import PublicProblem

def generate(model,codec,row,short,folder,update,checkpoint):
    branch='coconut' if short=='coconut' else 'student';path=folder/f'{row["sample_id"]}.json'
    if path.exists():return
    time_guard();start=time.time();p=PublicProblem.parse(row['public'])
    try:
        with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):ids=model.generate(**inputs(row,branch),branch=branch,generation=load(ROOT/'configs/qualification_p10.json')['generation'])[0].tolist()
        result=decode_result(codec,ids,p,teacher=short=='coconut');result.update(token_ids=ids,EOS_terminated=codec.tokenizer.eos_token_id in ids,missing_EOS=codec.tokenizer.eos_token_id not in ids,token_cap_termination=codec.tokenizer.eos_token_id not in ids and len(ids)-1>=2048)
    except Exception as exc:result={'status':'generation_or_parse_failure','reason':str(exc),'answer':None,'text':None,'token_ids':[],'EOS_terminated':False}
    save(path,{'sample_id':p.sample_id,'domain':row['domain'],'scenario_id':row['scenario_id'],'split':row['split'],'branch':branch,'result':result,'update':update,'checkpoint_sha256':checkpoint,'seconds':time.time()-start,'input_tokens':len(row['branch_input_ids'][branch]),'generation_calls':1,'teacher_inference_calls':0,'gold_generation_inputs':False})

def train(short):
    torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    c=load(ROOT/'configs/custom_p06.json');folder=OUT/'custom'/short;folder.mkdir(parents=True,exist_ok=True)
    if (folder/'fit.json').exists() and load(folder/'fit.json')['status']=='complete':return
    public=load(OUT/'custom-public.json');train=[r for r in public if r['split']=='train'];targets={r['sample_id']:r for r in load(OUT/'private/custom-targets.json')}
    expected={sid for v in load(OUT/'plan.json')['cohorts'].values() for sid in v['appendix_train']}
    if {r['sample_id'] for r in train}!=expected or set(targets)!=expected:raise ValueError('frozen_training_population_incomplete')
    identity={'config':c,'seed':11,'method':short,'training_samples':[r['sample_id'] for r in train],'training_scenarios':[r['scenario_id'] for r in train],'plan_sha256':file_hash(OUT/'plan.json'),'targets_sha256':file_hash(OUT/'private/custom-targets.json'),'public_sha256':file_hash(OUT/'custom-public.json'),'instruction_version':'p10-branch-exact-target-inventory-v1'}
    save(folder/'identity.json',identity);archive_sources('custom-'+short);torch.manual_seed(11);torch.cuda.manual_seed_all(11)
    if (folder/'resume/latest.json').exists():model,opt,updates=load_checkpoint(folder/'resume',identity=identity,device='cuda',training=True)
    else:
        backbone=T5ForConditionalGeneration.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
        settings=CustomSettings('coconut_inspired_t5_gru' if short=='coconut' else 'codi_inspired_t5_distillation',seed=11,latents=c['latents'],teacher_ce_weight=c['teacher_ce_weight'],student_ce_weight=c['student_ce_weight'],distillation_weight=c['distillation_weight'],smoothness_weight=c[short+'_smoothness'],encoder_query_chunk_size=c['encoder_query_chunk_size'])
        model=CustomT5(backbone,settings).cuda();opt=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=c['optimizer']['learning_rate'],weight_decay=c['optimizer']['weight_decay']);updates=0
        save(folder/'initialization.json',{'fresh':True,'timing_warm_start':False,'parameters':sum(p.numel() for p in model.parameters()),'parameter_hashes':{k:sha256(v.detach().cpu().numpy().tobytes()).hexdigest() for k,v in model.named_parameters()}})
    model.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    fixed={k:v.detach().cpu().clone() for k,v in model.teacher_proj.state_dict().items()} if short=='codi' else {}
    tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True);codec=TextCodec(tok);rng=random.Random(11);order=[]
    for epoch in range(2):cycle=list(range(len(train)));rng.shuffle(cycle);order.extend(cycle)
    history=restored_history(folder,updates);prior=history[-1]['seconds'] if history else 0;start=time.time();torch.cuda.reset_peak_memory_stats()
    for i in range(updates,len(order)):
        time_guard();budget().check(reserve_bytes=800000000);row=train[order[i]];model.train();opt.zero_grad(set_to_none=True);began=time.time()
        with torch.autocast('cuda',dtype=torch.bfloat16):out=model.training_losses(**train_inputs(row,targets,short))
        if not torch.isfinite(out['loss']):raise ValueError('nonfinite_loss')
        out['loss'].backward();norm=torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],c['optimizer']['gradient_clip'],error_if_nonfinite=True)
        if fixed and any(p.requires_grad or p.grad is not None for p in model.teacher_proj.parameters()):raise ValueError('teacher_projection_gradient')
        record={k:float(v.detach()) for k,v in out.items() if torch.is_tensor(v) and v.ndim==0};opt.step();updates=i+1
        if not all(torch.isfinite(p).all() for p in model.parameters()):raise ValueError('nonfinite_model_parameters')
        if any(not torch.equal(v,model.teacher_proj.state_dict()[k].cpu()) for k,v in fixed.items()):raise ValueError('teacher_projection_changed')
        history.append({**record,'update':updates,'pass':i//len(train)+1,'domain':row['domain'],'sample_id':row['sample_id'],'gradient_norm_before_clip':float(norm),'step_seconds':time.time()-began,'seconds':prior+time.time()-start});save(folder/'history.json',history);del out
        if updates%len(train)==0:
            directory=folder/'checkpoints'/str(updates);pointer=save_checkpoint(directory,model,opt,identity=identity,updates=updates);resume=folder/'resume';resume.mkdir(exist_ok=True);link=resume/pointer['file']
            if not link.exists():link.symlink_to((directory/pointer['file']).resolve())
            save(resume/'latest.json',pointer);model.eval();generate(model,codec,train[0],short,folder/'training_generations'/str(updates),updates,pointer['sha256'])
            if updates==len(order):save(folder/'selected.json',{'directory':str(directory.relative_to(folder)),'checkpoint':pointer,'update':updates,'policy':'final second pass, no heldout selection'})
        if updates%8==0:print(json.dumps({'method':short,'updates':updates,'loss':record['loss'],'seconds':prior+time.time()-start}),flush=True)
    # A process may stop after publishing the final resumable checkpoint but
    # before publishing its generation/selection metadata. Recover without any
    # additional optimizer update or alternative checkpoint choice.
    if updates==len(order) and not (folder/'selected.json').exists():
        directory=folder/'checkpoints'/str(updates);pointer=load(directory/'latest.json')
        if pointer['updates']!=updates:raise ValueError('final_checkpoint_update_mismatch')
        model.eval();generate(model,codec,train[0],short,folder/'training_generations'/str(updates),updates,pointer['sha256'])
        save(folder/'selected.json',{'directory':str(directory.relative_to(folder)),'checkpoint':pointer,'update':updates,'policy':'final second pass, no heldout selection'})
    save(folder/'fit.json',{'status':'complete','updates':updates,'passes':2,'training_examples':len(train),'seconds':prior+time.time()-start,'exposure':dict(__import__('collections').Counter(r['sample_id'] for r in history)),'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'teacher_projection_unchanged':True if fixed else None})

def inference(short):
    guard_deployment_io();torch.set_num_threads(2);folder=OUT/'custom'/short;chosen=load(folder/'selected.json');model,_,updates=load_checkpoint(folder/chosen['directory'],identity=load(folder/'identity.json'),device='cuda',training=False)
    c=load(ROOT/'configs/custom_p06.json');tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True);codec=TextCodec(tok)
    for row in [r for r in load(OUT/'custom-public.json') if r['split']=='test_id']:generate(model,codec,row,short,folder/'test_generations',updates,chosen['checkpoint']['sha256'])

if __name__=='__main__':globals()[sys.argv[1]](sys.argv[2])
