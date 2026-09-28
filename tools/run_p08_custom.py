"""Approved 20/180 custom runs: fresh initialization, bounded diagnostics, no repair."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import gc
import time
import torch
from transformers import AutoTokenizer,T5ForConditionalGeneration
from p08_common import *
from phi_jepa.baselines.custom_t5 import CustomT5,CustomSettings
from phi_jepa.baselines.custom_checkpoint import save_checkpoint,load_checkpoint
from phi_jepa.baselines.custom_io import TextCodec,decode_result,compose_hybrid,FORMAT
from phi_jepa.integration.contracts import PublicProblem


def tensors(record, targets=True):
    ids=torch.tensor([record['input_ids']],device='cuda'); result={'input_ids':ids,'attention_mask':torch.ones_like(ids)}
    if targets: result.update(teacher_labels=torch.tensor([record['teacher_labels']],device='cuda'),student_labels=torch.tensor([record['student_labels']],device='cuda'))
    return result


def scalar_losses(output): return {k:float(v.detach()) for k,v in output.items() if v.ndim==0}


def generate(model,codec,record,b,folder,milestone,diagnostic):
    """Record comes from public-prepared.json; no reference/label argument."""
    sid=record['sample_id']; branches={}; costs={}; batch=tensors(record,False); problem=PublicProblem.parse(record['public'])
    for branch in (('coconut',) if model.settings.method.startswith('coconut') else ('student','teacher')):
        started=time.monotonic(); result={'status':'generation_not_completed','answer':None}; name=f'{milestone}-{sid}-{branch}'
        save(folder/'generation-attempts'/f'{name}.json',{'status':'started','branch':branch,'sample_id':sid,'checkpoint_update':milestone})
        with b.operation('custom_generation:'+name,'gpu',('shared_gpu','diagnostic_generation') if diagnostic else ('shared_gpu',)):
            try:
                with torch.autocast('cuda',dtype=torch.bfloat16): ids=model.generate(**batch,branch=branch,generation=CONFIG['generation'])[0].tolist()
                torch.cuda.synchronize(); result=decode_result(codec,ids,problem,teacher=branch!='student')
                eos=codec.tokenizer.eos_token_id in ids[1:]
                result.update(token_ids=ids,EOS_terminated=eos,token_cap_termination=len(ids)-1>=2048 and not eos,missing_EOS=not eos,valid_typed_output=result['status']=='success')
            except (ValueError,RuntimeError) as exc:
                result={'status':'generation_failure','reason':str(exc),'answer':None,'valid_typed_output':False,'EOS_terminated':None,'missing_EOS':None,'token_cap_termination':None}
                if isinstance(exc,torch.cuda.OutOfMemoryError): torch.cuda.empty_cache()
            costs[branch]={'seconds':time.monotonic()-started,'input_tokens':len(record['input_ids']),'generated_tokens':len(result['token_ids'])-1 if 'token_ids' in result else None,'calls':1}
            branches[branch]=result; save(folder/'generation-attempts'/f'{name}.json',{'result':result,'cost':costs[branch],'branch':branch,'sample_id':sid,'checkpoint_update':milestone})
    row={'sample_id':sid,'split':record['split'],'milestone':milestone,'branches':branches,'costs':costs}
    if 'student' in branches: row.update(hybrid=compose_hybrid(branches['student'],branches['teacher']),hybrid_seconds=sum(v['seconds'] for v in costs.values()))
    save(folder/'generations'/f'{milestone}-{sid}.json',row)
    print(json.dumps({'generated':sid,'milestone':milestone,'status':{k:v['status'] for k,v in branches.items()}}),flush=True)


def train(method,phase):
    b=budget(); c=load(ROOT/'configs/custom_p06.json'); short='coconut' if method.startswith('coconut') else 'codi'; diag=phase=='diagnostic'
    buckets=(short+'_training',short+'_'+phase); folder=RUN/'custom'/method/phase; folder.mkdir(parents=True,exist_ok=False)
    source=provenance(method+'-'+phase); records=load(RUN/'private/training-prepared.json')
    if diag: records=[r for r in records if r['sample_id']==CONFIG['diagnostic_sample']]
    public={r['sample_id']:r for r in load(RUN/'public-prepared.json')}; diagnostic_record=next(r for r in records if r['sample_id']==CONFIG['diagnostic_sample'])
    tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True); codec=TextCodec(tok)
    maximum=CONFIG['custom_diagnostic_updates' if diag else 'custom_broad_updates']; order=schedule(len(records),maximum)
    settings=CustomSettings(method,seed=11,latents=c['latents'],teacher_ce_weight=c['teacher_ce_weight'],student_ce_weight=c['student_ce_weight'],distillation_weight=c['distillation_weight'],smoothness_weight=c[short+'_smoothness'],encoder_query_chunk_size=c['encoder_query_chunk_size'])
    identity={'config':c,'pilot_config':CONFIG,'format':FORMAT,'phase':phase,'source_sha256':source,'selection_sha256':file_hash(RUN/'selection.json'),
        'training_samples':[r['sample_id'] for r in records],'training_scenarios':[r['scenario_id'] for r in records], 'independent_fresh_initialization':True}
    save(folder/'identity.json',identity); history=[]; eval_losses=[]; updates=0; started=time.monotonic(); torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(11); torch.cuda.manual_seed_all(11)
    with b.operation(short+':'+phase+':initialize','gpu',buckets,reserve_bytes=1500000000):
        backbone=T5ForConditionalGeneration.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
        model=CustomT5(backbone,settings).to('cuda'); model.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        optimizer=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=c['optimizer']['learning_rate'],weight_decay=c['optimizer']['weight_decay'])
        fixed={k:v.detach().cpu().clone() for k,v in model.teacher_proj.state_dict().items()} if hasattr(model,'teacher_proj') else {}
        initial={name:sha256(p.detach().cpu().numpy().tobytes()).hexdigest() for name,p in model.named_parameters()}
        save(folder/'initialization.json',{'fresh':True,'warm_start':False,'seed':11,'parameter_hashes':initial,'parameters':sum(p.numel() for p in model.parameters()),'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad)})
    def milestone(update):
        model.eval()
        with b.operation(f'{short}:{phase}:eval_loss:{update}','gpu',('shared_gpu','diagnostic_generation') if diag else ('shared_gpu',)):
            with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16): out=model.training_losses(**tensors(diagnostic_record))
            eval_losses.append({'update':update,'sample_id':diagnostic_record['sample_id'],'scope':'training_example_teacher_forced_eval_mode',**scalar_losses(out)})
            del out; save(folder/'eval-losses.json',eval_losses)
        if diag: generate(model,codec,public[CONFIG['diagnostic_sample']],b,folder,update,True)
    if diag: milestone(0)
    for index in order:
        # Local phase time is cumulative training operations, separate from inference.
        remaining=CONFIG['bucket_seconds'][short+'_'+phase]-b.read()['seconds'].get(short+'_'+phase,0)
        if remaining<30: break
        with b.operation(f'{short}:{phase}:update:{updates+1}','gpu',buckets):
            model.train(); optimizer.zero_grad(set_to_none=True); record=records[index]
            with torch.autocast('cuda',dtype=torch.bfloat16): output=model.training_losses(**tensors(record))
            if not torch.isfinite(output['loss']): raise ValueError('nonfinite_loss')
            output['loss'].backward(); norm=torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],c['optimizer']['gradient_clip'],error_if_nonfinite=True)
            values=scalar_losses(output)
            if fixed:
                values['student_projection_gradient_norm']=float(torch.sqrt(sum(p.grad.float().square().sum() for p in model.student_proj.parameters() if p.grad is not None)))
                assert all(not p.requires_grad and p.grad is None for p in model.teacher_proj.parameters())
            optimizer.step(); updates+=1
            if not all(torch.isfinite(p).all() for p in model.parameters()): raise ValueError('nonfinite_parameter')
            if any(not torch.isfinite(v).all() for state in optimizer.state.values() for v in state.values() if torch.is_tensor(v)): raise ValueError('nonfinite_optimizer')
            if fixed: assert all(torch.equal(v,model.teacher_proj.state_dict()[k].cpu()) for k,v in fixed.items())
            history.append({'update':updates,'loss_position':'pre_update','sample_id':record['sample_id'],'gradient_norm_before_clip':float(norm),'elapsed_seconds':time.monotonic()-started,**values})
            del output; torch.cuda.synchronize(); save(folder/'history.json',history)
        if updates in (CONFIG['diagnostic_milestones'] if diag else CONFIG['broad_milestones']):
            milestone(updates)
            if not diag:
                with b.operation(f'{short}:{phase}:checkpoint:{updates}','gpu',buckets,reserve_bytes=1200000000): save_checkpoint(folder/'checkpoint',model,optimizer,identity=identity,updates=updates)
        if updates%5==0: print(json.dumps({'method':method,'phase':phase,'updates':updates,'loss':values['loss']}),flush=True)
    if diag or updates not in CONFIG['broad_milestones']:
        with b.operation(f'{short}:{phase}:final_checkpoint','gpu',buckets,reserve_bytes=1200000000): save_checkpoint(folder/'checkpoint',model,optimizer,identity=identity,updates=updates)
    final={name:sha256(p.detach().cpu().numpy().tobytes()).hexdigest() for name,p in model.named_parameters()}
    save(folder/'fit.json',{'status':'complete' if updates==maximum else 'component_time_cap','updates':updates,'maximum':maximum,'phase':phase,
        'source_sha256':source,'checkpoint':load(folder/'checkpoint/latest.json'),'changed_parameters':[name for name in initial if initial[name]!=final[name]],
        'teacher_projection_unchanged':all(initial[n]==final[n] for n in initial if n.startswith('teacher_proj.')) if fixed else None,
        'seconds_including_diagnostics':time.monotonic()-started,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()})


def inference(method):
    b=budget(); folder=RUN/'custom'/method/'broad'; provenance(method+'-inference'); c=load(ROOT/'configs/custom_p06.json')
    with b.operation(method+':load_for_validation','gpu',('shared_gpu',)):
        model,_,updates=load_checkpoint(folder/'checkpoint',identity=load(folder/'identity.json'),device='cuda',training=False)
        tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True); codec=TextCodec(tok)
    torch.cuda.reset_peak_memory_stats(); started=time.monotonic()
    # Fresh process reads only public preparation and checkpoint for generation.
    for record in load(RUN/'public-prepared.json'):
        if record['split']=='validation': generate(model,codec,record,b,folder,updates,False)
    save(folder/'inference-report.json',{'updates':updates,'seconds':time.monotonic()-started,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('diagnostic','broad','inference')); parser.add_argument('method',choices=('coconut_inspired_t5_gru','codi_inspired_t5_distillation')); args=parser.parse_args()
    torch.set_num_threads(2); torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    if args.stage=='inference': inference(args.method)
    else: train(args.method,args.stage)
