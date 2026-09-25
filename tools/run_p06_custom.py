"""Bounded real-model GPU qualification/fit and gold-free generation entrypoints."""
import argparse,gc,json,sys,time
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from transformers import AutoTokenizer,T5ForConditionalGeneration
from phi_jepa.artifacts import canonical,digest,code_provenance
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.baselines.custom_t5 import CustomT5,CustomSettings
from phi_jepa.baselines.custom_io import TextCodec,public_text,decode_result,compose_hybrid,FORMAT
from phi_jepa.baselines.custom_checkpoint import save_checkpoint,load_checkpoint


def save(path,value):
    tmp=path.with_suffix('.pending'); tmp.write_bytes(canonical(value)); tmp.replace(path)


def settings(config,method):
    return CustomSettings(method,seed=config['seed'],latents=config['latents'],teacher_ce_weight=config['teacher_ce_weight'],student_ce_weight=config['student_ce_weight'],distillation_weight=config['distillation_weight'],smoothness_weight=config['coconut_smoothness'] if method.startswith('coconut') else config['codi_smoothness'],encoder_query_chunk_size=config.get('encoder_query_chunk_size',0))


def load_model(config,args):
    backbone=T5ForConditionalGeneration.from_pretrained(config['model'],revision=config['revision'],cache_dir=args.cache_dir,local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
    model=CustomT5(backbone,settings(config,args.method)).to('cuda')
    if config['correctness']['gradient_checkpointing']: model.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    return model


def tensors(record):
    ids=torch.tensor([record['input_ids']],device='cuda')
    return {'input_ids':ids,'attention_mask':torch.ones_like(ids),'teacher_labels':torch.tensor([record['teacher_labels']],device='cuda'),
        'student_labels':torch.tensor([record['student_labels']],device='cuda')}


def train_call(model,batch):
    with torch.autocast('cuda',dtype=torch.bfloat16): return model.training_losses(**batch)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--mode',choices=('qualify','fit','infer'),required=True)
    p.add_argument('--method',required=True); p.add_argument('--profile',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--cache-dir',required=True); args=p.parse_args()
    root=Path(__file__).resolve().parents[1]; config=json.loads((root/'configs/custom_p06.json').read_text())
    if args.method not in config['methods'] or config['correctness']['max_updates_per_method']>2: raise ValueError('bounded_p06_profile')
    args.output.mkdir(parents=True,exist_ok=True); torch.set_num_threads(2); torch.manual_seed(config['seed']); torch.cuda.manual_seed_all(config['seed'])
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    torch.cuda.reset_peak_memory_stats(); started=time.perf_counter()
    report={'mode':args.mode,'method':args.method,'status':'started','config_sha256':digest(config),'gpu':torch.cuda.get_device_name(),
        'train_calls_attempted':0,'teacher_branch_calls_attempted':0,'student_branch_calls_attempted':0,'updates':0,'backward_calls_attempted':0,
        'precision':config['correctness']['precision'],'source':code_provenance()}
    path=args.output/f'{args.mode}-report.json'; save(path,report)
    try:
        if args.mode in ('qualify','fit'):
            records=json.loads((args.profile/'training-prepared.json').read_text())
            record=max(records,key=lambda r:r['tokens']) if args.mode=='qualify' else next(r for r in records if r['public']['input']['domain']=='tethered_load')
            report.update(sample_id=record['public']['sample_id'],input_tokens=record['tokens'],teacher_tokens=len(record['teacher_labels']),student_tokens=len(record['student_labels']),scenario_id=record['scenario_id'])
            model=load_model(config,args); model.train(); batch=tensors(record)
            report.update(parameters=sum(x.numel() for x in model.parameters()),trainable_parameters=sum(x.numel() for x in model.parameters() if x.requires_grad))
            optimizer=torch.optim.AdamW([x for x in model.parameters() if x.requires_grad],lr=config['optimizer']['learning_rate'],weight_decay=config['optimizer']['weight_decay'])
            fixed={k:v.detach().cpu().clone() for k,v in model.teacher_proj.state_dict().items()} if hasattr(model,'teacher_proj') else {}
            identity={'config':config,'format':FORMAT,'method':args.method,'model_download':json.loads((args.profile/'model-download.json').read_text()),
                'training_sample':record['public']['sample_id'],'training_scenario':record['scenario_id'],'input_sha256':record['input_sha256'],
                'target_sha256':record['target_sha256'],'release':json.loads((args.profile/'preparation.json').read_text())['release_identity']}
            if args.mode=='fit': save(args.output/'checkpoint-identity.json',identity)
            history=[]; maximum=1 if args.mode=='qualify' else config['correctness']['max_updates_per_method']
            for update in range(maximum):
                if time.perf_counter()-started>config['correctness']['max_seconds_per_method']: raise TimeoutError('configured_fit_time_limit')
                report['train_calls_attempted']+=1; report['student_branch_calls_attempted']+=1
                report['teacher_branch_calls_attempted']+=int(args.method.startswith('codi')); save(path,report)
                optimizer.zero_grad(set_to_none=True); output=train_call(model,batch)
                if not torch.isfinite(output['loss']): raise ValueError('nonfinite_loss')
                report['backward_calls_attempted']+=1; save(path,report); output['loss'].backward()
                norm=torch.nn.utils.clip_grad_norm_([x for x in model.parameters() if x.requires_grad],config['optimizer']['gradient_clip'],error_if_nonfinite=True)
                item={k:float(v.detach()) for k,v in output.items() if v.ndim==0}; item['gradient_norm']=float(norm)
                if hasattr(model,'teacher_proj'):
                    item['teacher_projection_frozen']=all(not x.requires_grad and x.grad is None for x in model.teacher_proj.parameters())
                    item['student_projection_gradient_norm']=float(torch.sqrt(sum(x.grad.float().square().sum() for x in model.student_proj.parameters() if x.grad is not None)))
                    item['teacher_eos_position']=output['teacher_eos_positions'].tolist(); item['student_eos_position']=output['student_eos_positions'].tolist()
                if args.mode=='fit': optimizer.step(); report['updates']+=1
                if not all(torch.isfinite(x).all() for x in model.parameters()): raise ValueError('nonfinite_parameters')
                if any(not torch.isfinite(v).all() for s in optimizer.state.values() for v in s.values() if isinstance(v,torch.Tensor)): raise ValueError('nonfinite_optimizer_state')
                history.append(item); del output; report['history']=history; save(path,report)
                if args.mode=='fit':
                    pointer=save_checkpoint(args.output/'checkpoint',model,optimizer,identity=identity,updates=report['updates']); report['checkpoint']=pointer
                    if update==0:
                        del model,optimizer; gc.collect(); torch.cuda.empty_cache()
                        model,optimizer,restored_updates=load_checkpoint(args.output/'checkpoint',identity=identity,device='cuda',training=True)
                        if config['correctness']['gradient_checkpointing']: model.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
                        if restored_updates!=1: raise ValueError('resume_update')
                        report['resumed_after_update']=1
            if fixed:
                report['teacher_projection_unchanged']=all(torch.equal(v,model.teacher_proj.state_dict()[k].cpu()) for k,v in fixed.items())
                if not report['teacher_projection_unchanged']: raise ValueError('teacher_projection_changed')
            report['status']='success'
        else:
            # This branch opens public preparation and checkpoint only, never references or target preparation.
            identity=json.loads((args.output/'checkpoint-identity.json').read_text())
            model,_,updates=load_checkpoint(args.output/'checkpoint',identity=identity,device='cuda',training=False)
            tok=AutoTokenizer.from_pretrained(config['model'],revision=config['revision'],cache_dir=args.cache_dir,local_files_only=True); codec=TextCodec(tok)
            records=[r for r in json.loads((args.profile/'public-prepared.json').read_text()) if r['public']['input']['domain']=='tethered_load']
            results=[]
            for record in records:
                problem=PublicProblem.parse(record['public']); original=public_text(problem,record['enrichment'])
                ids_list=codec.tokens(original,config['max_input_tokens'])
                if ids_list!=record['input_ids'] or digest(original)!=record['input_sha256']: raise ValueError('public_token_identity')
                ids=torch.tensor([ids_list],device='cuda'); mask=torch.ones_like(ids); branches={}; costs={}
                for branch in (('coconut',) if args.method.startswith('coconut') else ('student','teacher')):
                    key='teacher_branch_calls_attempted' if branch=='teacher' else 'student_branch_calls_attempted'; report[key]+=1; save(path,report); when=time.perf_counter()
                    try:
                        with torch.autocast('cuda',dtype=torch.bfloat16): generated=model.generate(ids,mask,branch=branch,generation=config['generation'])
                        torch.cuda.synchronize(); tokens=generated[0].tolist(); branches[branch]=decode_result(codec,tokens,problem,teacher=branch!='student')
                        costs[branch]={'model_calls':1,'input_tokens':len(ids_list),'decoder_tokens_generated':len(tokens)-1,'seconds':time.perf_counter()-when}
                        branches[branch]['token_ids']=tokens
                    except (ValueError,RuntimeError) as exc:
                        branches[branch]={'status':'generation_failure','reason':str(exc),'answer':None}; costs[branch]={'model_calls':1,'input_tokens':len(ids_list),'decoder_tokens_generated':None,'seconds':time.perf_counter()-when}
                        if isinstance(exc,torch.cuda.OutOfMemoryError): torch.cuda.empty_cache()
                row={'sample_id':problem.sample_id,'split':record['split'],'branches':branches,'costs':costs}
                if 'student' in branches:
                    row['hybrid']=compose_hybrid(branches['student'],branches['teacher']); row['hybrid_cost']={'model_calls':2,'seconds':sum(c['seconds'] for c in costs.values()),'input_tokens':sum(c['input_tokens'] for c in costs.values()),'physical_student_generation_reused':True}
                results.append(row); save(args.output/'generations.json',results)
            report.update(status='success',inference_examples=len(results),checkpoint_updates=updates)
    except Exception as exc:
        report.update(status='failed',failure_type=type(exc).__name__,reason=str(exc))
    finally:
        report.update(seconds=time.perf_counter()-started,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
        save(path,report); print(json.dumps(report),flush=True)
    return 0 if report['status']=='success' else 2


if __name__=='__main__': raise SystemExit(main())
