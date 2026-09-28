"""Independently initialized custom models with explicit consistent branch text."""
from hashlib import sha256
import random
import time
import torch
from transformers import AutoTokenizer,T5ForConditionalGeneration
from p10_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.baselines.custom_t5 import CustomT5,CustomSettings
from phi_jepa.baselines.custom_checkpoint import save_checkpoint,load_checkpoint
from phi_jepa.baselines.custom_io import TextCodec,decode_result,compose_hybrid


def inputs(row,branch):
    ids=torch.tensor([row['branch_input_ids'][branch]],device='cuda')
    return {'input_ids':ids,'attention_mask':torch.ones_like(ids)}


def train_inputs(row,targets,short):
    data=inputs(row,'student' if short=='codi' else 'coconut')
    target=targets[row['sample_id']]
    data['teacher_labels']=torch.tensor([target['teacher_labels']],device='cuda')
    if short=='codi':
        data['student_labels']=torch.tensor([target['student_labels']],device='cuda')
        teacher=inputs(row,'teacher'); data['teacher_input_ids']=teacher['input_ids']; data['teacher_attention_mask']=teacher['attention_mask']
    return data


def generate(run,model,codec,row,folder,milestone,short,checkpoint_sha256=None):
    branches={}; costs={}; p=PublicProblem.parse(row['public'])
    for branch in (('coconut',) if short=='coconut' else ('student','teacher')):
        start=time.perf_counter()
        try:
            with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16): ids=model.generate(**inputs(row,branch),branch=branch,generation=run.c['generation'])[0].tolist()
            result=decode_result(codec,ids,p,teacher=branch!='student')
            result.update(token_ids=ids,EOS_terminated=codec.tokenizer.eos_token_id in ids,
                missing_EOS=codec.tokenizer.eos_token_id not in ids,token_cap_termination=codec.tokenizer.eos_token_id not in ids and len(ids)-1>=run.c['generation']['max_new_tokens'])
        except (ValueError,RuntimeError) as exc: result={'status':'generation_or_parse_failure','reason':str(exc),'answer':None,'text':None,'token_ids':[],'EOS_terminated':False}
        branches[branch]=result; costs[branch]={'seconds':time.perf_counter()-start,'calls':1,'input_tokens':len(row['branch_input_ids'][branch]),'generated_tokens':max(0,len(result['token_ids'])-1)}
    out={'sample_id':p.sample_id,'scenario_id':row['scenario_id'],'split':row['split'],'milestone':milestone,'branches':branches,'costs':costs,
        'condition':'p10_branch_inventory_instructions','gold_generation_inputs':False,'checkpoint_sha256':checkpoint_sha256}
    if short=='codi': out['hybrid']=compose_hybrid(branches['student'],branches['teacher'])
    save(folder/'generations'/f'{milestone}-{p.sample_id}.json',out)
    return out


def custom(run,job):
    torch.set_num_threads(2); torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    short,phase=job.split('_'); small=phase=='small'; method='coconut_inspired_t5_gru' if short=='coconut' else 'codi_inspired_t5_distillation'
    c=load(ROOT/'configs/custom_p06.json'); folder=run.root/'custom'/job; folder.mkdir(parents=True,exist_ok=True)
    public=load(run.root/'custom-public.json'); targets={r['sample_id']:r for r in load(run.root/'private/custom-targets.json')}
    train=[r for r in public if r['split']=='train']; validation=[r for r in public if r['split']=='validation'][:run.c.get('custom_selection_questions',2)]
    if small: train=train[:1]
    maximum=run.c['custom_small_updates'] if small else run.c['custom_broad_updates']; milestones=run.c['custom_small_milestones'] if small else run.c['custom_broad_milestones']
    seed=run.c['seed']
    identity={'config':c,'seed':seed,'phase':phase,'instruction_version':'p10-branch-exact-target-inventory-v1','training_samples':[r['sample_id'] for r in train],
        'training_scenarios':[r['scenario_id'] for r in train],'selection_sha256':file_hash(run.root/'selection.json'),'public_token_sha256':file_hash(run.root/'custom-public.json'),
        'training_target_sha256':file_hash(run.root/'private/custom-targets.json'),'method':method,'independent_fresh_initialization':True}
    if (folder/'identity.json').exists():
        prior=load(folder/'identity.json')
        # Earlier P10 seed-11 jobs recorded this fixed seed in initialization.json.
        compatible=prior==identity or ('seed' not in prior and seed==11 and prior=={k:v for k,v in identity.items() if k!='seed'})
        if not compatible: raise ValueError('custom_training_identity_changed')
        identity=prior
    else: save(folder/'identity.json',identity)
    started=time.monotonic(); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    if (folder/'resume/latest.json').exists():
        model,optimizer,updates=load_checkpoint(folder/'resume',identity=identity,device='cuda',training=True)
    else:
        backbone=T5ForConditionalGeneration.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(run.native/'model-cache'),local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
        settings=CustomSettings(method,seed=seed,latents=c['latents'],teacher_ce_weight=c['teacher_ce_weight'],student_ce_weight=c['student_ce_weight'],distillation_weight=c['distillation_weight'],smoothness_weight=c[short+'_smoothness'],encoder_query_chunk_size=c['encoder_query_chunk_size'])
        model=CustomT5(backbone,settings).to('cuda'); model.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        optimizer=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=c['optimizer']['learning_rate'],weight_decay=c['optimizer']['weight_decay']); updates=0
        save(folder/'initialization.json',{'seed':seed,'fresh':True,'warm_start':False,'parameter_hashes':{k:sha256(v.detach().cpu().numpy().tobytes()).hexdigest() for k,v in model.named_parameters()},'parameters':sum(p.numel() for p in model.parameters())})
    tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(run.native/'model-cache'),local_files_only=True); codec=TextCodec(tok)
    fixed={k:v.detach().cpu().clone() for k,v in model.teacher_proj.state_dict().items()} if short=='codi' else {}
    rng=random.Random(seed); order=[]
    while len(order)<maximum:
        cycle=list(range(len(train))); rng.shuffle(cycle); order.extend(cycle)
    history=restored_history(folder,updates)
    torch.cuda.reset_peak_memory_stats()
    def milestone(update):
        model.eval(); losses=[]
        for row in train[:1] if small else validation:
            with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16): out=model.training_losses(**train_inputs(row,targets,short))
            losses.append({'sample_id':row['sample_id'],'split':row['split'],**{k:float(v.detach()) for k,v in out.items() if torch.is_tensor(v) and v.ndim==0}})
            del out
        save(folder/'milestones'/f'{update}.json',losses)
        if update>0:
            run.b.check(reserve_bytes=1000000000)
            pointer=save_checkpoint(folder/'checkpoints'/str(update),model,optimizer,identity=identity,updates=update)
            score=sum(x['loss'] for x in losses)/len(losses)
            old=load(folder/'selected.json') if (folder/'selected.json').exists() else None
            if old is None or score<old['loss']:
                save(folder/'selected.json',{'directory':f'checkpoints/{update}','checkpoint':pointer,'update':update,'loss':score,'selection_split':'train_fitting_only' if small else 'validation','validation_ids':[] if small else [r['sample_id'] for r in validation]})
            # Resume points to the same content-addressed checkpoint; only a
            # symlink is created, avoiding another multi-hundred-MB artifact.
            resume=folder/'resume'; resume.mkdir(exist_ok=True); target=folder/'checkpoints'/str(update)/pointer['file']
            link=resume/pointer['file']
            if not link.exists(): link.symlink_to(target.resolve())
            save(resume/'latest.json',pointer)
        # Small fitting checks only on training input; broader milestones include
        # one training and two selection questions, never calibration/test.
        for row in train[:1] if small else [train[0],*validation[:2]]:
            generate(run,model,codec,row,folder,update,short,pointer['sha256'] if update>0 else 'initialization:'+file_hash(folder/'initialization.json'))
    if updates==0 and small: milestone(0)
    for index in order[updates:maximum]:
        if time.monotonic()-started>run.c['custom_job_seconds'][job]-120: break
        run.b.check(); model.train(); optimizer.zero_grad(set_to_none=True); row=train[index]
        with torch.autocast('cuda',dtype=torch.bfloat16): out=model.training_losses(**train_inputs(row,targets,short))
        if not torch.isfinite(out['loss']): raise ValueError('nonfinite_custom_loss')
        out['loss'].backward(); norm=torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],c['optimizer']['gradient_clip'],error_if_nonfinite=True)
        record={k:float(v.detach()) for k,v in out.items() if torch.is_tensor(v) and v.ndim==0}
        if short=='codi':
            record['student_projection_gradient_norm']=float(torch.sqrt(sum(p.grad.square().sum() for p in model.student_proj.parameters() if p.grad is not None)))
            if any(p.requires_grad or p.grad is not None for p in model.teacher_proj.parameters()): raise ValueError('teacher_projection_not_fixed')
        optimizer.step(); updates+=1
        if not all(torch.isfinite(p).all() for p in model.parameters()): raise ValueError('nonfinite_model')
        if any(not torch.equal(v,model.teacher_proj.state_dict()[k].cpu()) for k,v in fixed.items()): raise ValueError('teacher_projection_changed')
        history.append({'update':updates,'sample_id':row['sample_id'],'gradient_norm_before_clip':float(norm),'seconds':time.monotonic()-started,**record}); del out
        save(folder/'history.json',history)
        if updates in milestones: milestone(updates)
        if updates%20==0: print(json.dumps({'job':job,'update':updates,'loss':record['loss'],'seconds':time.monotonic()-started}),flush=True)
    if not (folder/'selected.json').exists() or updates not in milestones: milestone(updates)
    init=load(folder/'initialization.json')['parameter_hashes']; final={k:sha256(v.detach().cpu().numpy().tobytes()).hexdigest() for k,v in model.named_parameters()}
    save(folder/'fit.json',{'status':'complete' if updates==maximum else 'component_cap','updates':updates,'seconds':time.monotonic()-started,
        'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
        'changed_parameters':[k for k in final if final[k]!=init[k]],'teacher_projection_unchanged':all(torch.equal(v,model.teacher_proj.state_dict()[k].cpu()) for k,v in fixed.items()) if fixed else None})


def custom_forecast(run,job=None):
    guard_deployment_io()
    started=time.monotonic(); torch.cuda.reset_peak_memory_stats()
    torch.set_num_threads(2); c=load(ROOT/'configs/custom_p06.json')
    tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(run.native/'model-cache'),local_files_only=True); codec=TextCodec(tok)
    # Deliberately no private target file is read by this stage.
    rows=[r for r in load(run.root/'custom-public.json') if r['split']=='validation']
    if job not in ('coconut','codi'): raise ValueError('explicit_custom_environment_required')
    for short in (job,):
        folder=run.root/'custom'/f'{short}_broad'
        if not (folder/'selected.json').exists(): continue
        chosen=load(folder/'selected.json'); model,_,update=load_checkpoint(folder/chosen['directory'],identity=load(folder/'identity.json'),device='cuda',training=False)
        generated=0
        for row in rows:
            path=folder/'validation/generations'/f"{update}-{row['sample_id']}.json"
            if path.exists():
                if load(path).get('checkpoint_sha256')!=chosen['checkpoint']['sha256']: raise ValueError('stale_custom_generation_requires_separate_evidence_run')
                continue
            generate(run,model,codec,row,folder/'validation',update,short,chosen['checkpoint']['sha256']); generated+=1
        save(folder/'validation/inference_reports'/f'{time.time_ns()}.json',{'seconds':time.monotonic()-started,'new_questions':generated,
            'checkpoint_sha256':chosen['checkpoint']['sha256'],'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
            'references_or_private_targets_opened':False,'deployment_guard_enabled':True})
        del model; torch.cuda.empty_cache()
