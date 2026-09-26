"""Controlled independent training; evaluator references stay in this stage."""
from collections import Counter
import random
import time
import torch
from p10_common import *
from p10_inference import predict
from phi_jepa.models.conditioning import NumericalConditioning
from phi_jepa.models.augmented_ode import AugmentedODE,ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.training.pairs import PairTrainer,TrainingSettings
from phi_jepa.training.checkpoint import write_checkpoint,load_checkpoint as load_primary
from phi_jepa.baselines.conventional import NumericalComparator,BaselineSettings,NumericalRollout,NumericalPrediction
from phi_jepa.baselines.training import ComparatorTrainer
from phi_jepa.baselines.checkpoint import save_checkpoint,load_checkpoint as load_baseline
from phi_jepa.integration.contracts import PublicProblem,Identity,PhysicalRollout,FullAugmentedPrediction
from phi_jepa.integration.readers import make_pairs,forecast_states
from phi_jepa.inference.readout import named_forecast
from phi_jepa.solvers.rk4 import rk4,SolverSettings,SolveStats
from phi_jepa.typed_evaluation import trajectory_errors,evaluate_targets
from phi_jepa.coordinate_diagnostics import decompose,coordinate_unit
from phi_jepa.training.sampling import fixed_pair_batches,chronological_sequence_order


class BatchEmbeddings:
    """Materialize just the current fixed-size embedding batch."""
    def __init__(self,batches,by_sample): self.batches,self.by_sample=batches,by_sample
    def __getitem__(self,index):
        return torch.stack([self.by_sample[p.identity.sample_id] for p in self.batches[index]]) if self.by_sample else None


def coordinate_columns(layout):
    structure={p:v for p,t,v in layout.structure}; columns=[]
    for path,typ in layout.entries:
        group='fixed_conditioning' if path[0]==('key','fixed_conditioning') else 'time_index' if path[-1] in (('key','timestamp'),('key','step_index')) else 'physical'
        label='.'.join(':'.join(str(v) for v in part[1:]) for part in path)
        for j,part in enumerate(path):
            if part[0]=='quantity' and path[j+1:j+2]==(('key','value'),):
                label=f'{part[1]}.{part[2]}'+''.join(f'[{part[-1]}]' for part in path[j+2:])
                break
        columns.append({'name':label,'path':str(path),'group':group,'unit':coordinate_unit(path,structure)})
    return columns


def diagnostic(run,model,solver,job,rows,refs,*,save_folder=None):
    layout=run.layout(); result=[]; scores=[]; columns=coordinate_columns(layout)
    for row in rows:
        p=PublicProblem.parse(row['public']); ref=refs[p.sample_id]; states=forecast_states(p,ref); n=torch.tensor([layout.flatten(s,p.input) for s in states[:-1]]); truth=[layout.flatten(s,p.input) for s in states[1:]]
        es=torch.tensor([run.embedding(p.sample_id,job['context_identity']['mode'])]*len(n)) if job['method']!='no_text_conditioning' else None
        try:
            saved=predict(run,model,solver,job,row); times=[s['timestamp'] for s in states[1:]]
            with torch.no_grad():
                if job['primary']:
                    x=torch.cat((n,model.projection(es)),dim=-1); one=rk4(model,x,[s['timestamp'] for s in states[:-1]],times,solver,SolveStats())
                    typed=PhysicalRollout(p.sample_id,tuple(FullAugmentedPrediction(layout.sha256,layout.d,tuple(x.tolist()),t) for x,t in zip(one,times)),mode='recorded_input_one_step_diagnostic')
                else:
                    projected=model.projection(es) if es is not None else None; hidden=None; values=[]
                    for i,(a,b) in enumerate(zip(states,states[1:])):
                        v,hidden=model.next_state(n[i:i+1],projected[i:i+1] if projected is not None else None,a['timestamp'],b['timestamp'],solver=solver,stats=SolveStats(),hidden=hidden); values.append(v)
                    one=torch.cat(values); typed=NumericalRollout(p.sample_id,tuple(NumericalPrediction(layout.sha256,layout.d,tuple(x.tolist()),t) for x,t in zip(one,times)),job['method'],mode='recorded_input_one_step_diagnostic')
            named=named_forecast(p,layout,typed,diagnostic=True,numerical_only=not job['primary'])
            answer=evaluate_targets(p,ref,saved['readout'],method=job['variant'])
            numeric=[x for x in answer['targets'] if x['answer_type']!='boolean']
            score=sum(x['error']/max(x.get('tolerance',0),1e-12) if x['error'] is not None else 1e12 for x in numeric)/len(numeric)
            scores.append(score)
            record={'sample_id':p.sample_id,'scenario_id':row['scenario_id'],'split':row['split'],'status':'success',
                'selection_score':score,'answer':answer,'physical_autonomous':trajectory_errors(saved['named']['states'],ref['states'],mode='autonomous'),
                'physical_one_step':trajectory_errors(named['states'],ref['states'],mode='recorded_input_one_step_diagnostic'),
                'coordinate_autonomous':decompose([s['values'][:layout.d] for s in saved['trajectory']['predictions']],truth,columns),
                'coordinate_one_step':decompose(one[:,:layout.d].tolist(),truth,columns)}
        except (ValueError,RuntimeError,OverflowError) as exc:
            scores.append(1e12); record={'sample_id':p.sample_id,'scenario_id':row['scenario_id'],'status':'failure','reason':str(exc)}
        result.append(record)
        if save_folder: save(save_folder/f'{p.sample_id}.json',record)
    return {'eligible':len(rows),'failed':sum(r['status']!='success' for r in result),'selection_score':sum(scores)/len(scores),'rows':result}


def gradients(run,model,solver,pairs,embeddings):
    layout=run.layout(); batch=pairs[:4]; e=embeddings[:4]
    n=torch.tensor([p.n_current for p in batch]); next_n=torch.tensor([p.n_next for p in batch])
    x,target,_=model.projection.pair(n,next_n,e,layout_sha256=layout.sha256)
    prediction=rk4(model,x,[p.start_time for p in batch],[p.end_time for p in batch],solver,SolveStats()); square=(prediction-target).square()
    groups={'physical':[],'time_index':[],'fixed_conditioning':[],'contextual':list(range(layout.d,2*layout.d))}
    for i,(path,typ) in enumerate(layout.entries): groups['fixed_conditioning' if path[0]==('key','fixed_conditioning') else 'time_index' if path[-1] in (('key','timestamp'),('key','step_index')) else 'physical'].append(i)
    params=list(model.parameters()); data={}
    for name,cols in groups.items():
        loss=square[:,cols].sum()/square.numel(); gs=torch.autograd.grad(loss,params,retain_graph=True,allow_unused=True)
        data[name]={'loss_contribution':float(loss.detach()),'gradient_norm':float(torch.sqrt(sum(g.square().sum() for g in gs if g is not None)))}
    with torch.no_grad():
        nums=model.conditioning(n) if model.conditioning is not None else n
        z=torch.cat((nums,x[:,layout.d:],torch.tensor([[p.start_time] for p in batch])),dim=-1)
        h1=model.field[1](model.field[0](z)); h2=model.field[3](model.field[2](h1))
    return {'blocks':data,'tanh1_saturation':float((h1.abs()>.99).float().mean()),'tanh2_saturation':float((h2.abs()>.99).float().mean()),'pair_ids':[p.pair_id for p in batch]}


def numerical(run,variant):
    torch.set_num_threads(2); started=time.monotonic(); layout=run.layout(); c=run.c
    continued=variant.startswith('continued_'); source_variant=variant.removeprefix('continued_')
    prior_seconds=0.
    if continued:
        from p10_continuation import policy
        extra=policy(run)
        if source_variant not in extra['source_methods']: raise ValueError('unapproved_continuation_method')
        c={**c,'numerical_updates':extra['updates'],'checkpoint_milestones':extra['checkpoint_milestones'],'numerical_job_seconds':extra['job_seconds']}
        prior_seconds=load(run.root/'numerical'/variant/'continuation_origin.json')['prior_training_seconds']
    biasinit=source_variant.startswith('biasinit_'); base=source_variant.removeprefix('biasinit_')
    primary=base in ('small_fit','raw_early','conditioned_early','raw_full','conditioned_full','no_enrichment')
    method='phi_jepa' if primary else base; full=base not in ('raw_early','conditioned_early')
    conditioned=base in ('small_fit','conditioned_early','conditioned_full','no_enrichment','constant_context_text_ode','no_text_conditioning')
    mode='public_base_for_offline_audit' if base in ('no_enrichment','no_text_conditioning') else 'enriched'
    folder=run.root/'numerical'/variant; folder.mkdir(parents=True,exist_ok=True)
    rows=[r for r in run.rows() if r['split']=='train']; val=[r for r in run.rows() if r['split']=='validation']
    if base=='small_fit': rows=rows[:c['small_fit_questions']]
    refs=load(run.root/'private/train-references.json'); valrefs=load(run.root/'private/validation-references.json')
    batches=[]; all_pairs=[]; es=[]
    for row in rows:
        p=PublicProblem.parse(row['public']); identity=Identity(p.sample_id,row['scenario_id'],row['split_group'],c['domain'],'train')
        states=forecast_states(p,refs[p.sample_id]); counts=Counter({digest((c['domain'],identity.group_id,a['timestamp'],b['timestamp'])):1 for a,b in zip(states,states[1:])})
        pairs=list(make_pairs(p,refs[p.sample_id],identity,layout,'p10',counts,context_mode=mode,
            enrichment=load(run.root/'enrichment'/f'{p.sample_id}.json') if mode=='enriched' else None,duplicate_policy='equal_question_pairs'))
        if not full: pairs=pairs[:20]
        all_pairs.extend(pairs)
        chunks=[pairs] if method=='constant_context_text_rnn' else [pairs[i:i+c['batch_pairs']] for i in range(0,len(pairs),c['batch_pairs'])]
        for chunk in chunks:
            batches.append(chunk); es.append(torch.tensor([run.embedding(p.sample_id,mode)]*len(chunk)) if method!='no_text_conditioning' else None)
    # This qualification uses same-horizon trajectories; reject unequal batches
    # rather than silently giving shorter sequences extra transition weight.
    mixed=bool(c.get('mixed_horizon_equal_pair_sampling',False))
    if not mixed and method!='fixed_projection_lr' and len({len(x) for x in batches})!=1: raise ValueError('unequal_batch_lengths_require_global_equal_pair_sampler')
    context={'encoder':load(run.root/'encoding-report.json')['settings'] if method!='no_text_conditioning' else None,'mode':mode,'variant':source_variant}
    settings={'variant':variant,'method':method,'primary':primary,'conditioning':conditioned,'full_interval':full,'context_identity':context,'output_bias_initialization':'training_mean_adjacent_derivative' if biasinit else 'seeded_zero_bias'}
    save(folder/'job.json',settings)
    solver=SolverSettings(**c['solver']); maximum=c['small_fit_updates'] if base=='small_fit' else c['numerical_updates']
    if mixed and method=='constant_context_text_rnn':
        order=chronological_sequence_order(batches,maximum,c['seed'])
        sampling='length-proportional whole sequences; unchanged mean transition loss; equal expected pair weight'
    elif mixed and method!='fixed_projection_lr':
        indices=list(fixed_pair_batches(all_pairs,c['batch_pairs'],maximum,c['seed']))
        # Indexed batches avoid duplicating n/target storage. Context is attached
        # to each pair, never borrowed from the first question in a mixed batch.
        batches=[[all_pairs[i] for i in ids] for ids in indices]
        by_sample={r['sample_id']:torch.tensor(run.embedding(r['sample_id'],mode)) for r in rows} if method!='no_text_conditioning' else {}
        es=BatchEmbeddings(batches,by_sample)
        order=list(range(maximum)); sampling='uniform shuffled question-pair cycles, fixed-size batches, tails carried'
    else:
        rng=random.Random(c['seed']); order=[]
        while len(order)<maximum:
            cycle=list(range(len(batches))); rng.shuffle(cycle); order.extend(cycle)
        order=order[:maximum]; sampling='equal-length chronological chunks under shuffled cycles'
    history=load(folder/'history.json') if (folder/'history.json').exists() else []
    if (folder/'resume/latest.json').exists():
        if primary: trainer,_,_=load_primary(folder/'resume',layout=layout,context_identity=context,training=True); model=trainer.model
        else: model,trainer,_,_=load_baseline(folder/'resume',layout=layout,context_identity=context,method=method,training=True)
        history=restored_history(folder,trainer.updates) if trainer else history
    else:
        transform=NumericalConditioning.fit([p.n_current for p in all_pairs],layout_sha256=layout.sha256,
            provenance={'split':'train','sample_ids':[r['sample_id'] for r in rows],'scenario_ids':[r['scenario_id'] for r in rows]}) if conditioned else None
        torch.manual_seed(c['seed'])
        if primary: model=AugmentedODE(layout,ProjectionSettings(1024,seed=c['seed']),ODESettings(seed=c['seed']),transform); trainer=PairTrainer(model,solver,TrainingSettings(context_mode=mode))
        else: model=NumericalComparator(layout,BaselineSettings(method,embedding_width=0 if method=='no_text_conditioning' else 1024,seed=c['seed']),transform); trainer=None if method=='fixed_projection_lr' else ComparatorTrainer(model,solver=solver)
        if biasinit:
            if not hasattr(model,'field'): raise ValueError('existing_ODE_output_bias_required')
            derivative=torch.tensor([[(b-a)/p.dt for a,b in zip(p.n_current,p.n_next)] for p in all_pairs]).mean(0)
            with torch.no_grad():
                model.field[-1].bias[:layout.d].copy_(derivative)
                if primary: model.field[-1].bias[layout.d:].zero_()
            save(folder/'bias_initialization.json',{'source':'training supervised adjacent pairs only','pair_ids':[p.pair_id for p in all_pairs],
                'mean_raw_n_derivative':derivative.tolist(),'new_parameters':False,'bias_remains_trainable':True,'output_rescaling':False,'closed_form_initialization_passes':1})
        save(folder/'initialization.json',{'fresh':True,'seed':c['seed'],'model_manifest':model.manifest(),'parameter_count':sum(p.numel() for p in model.parameters()),'initial_tensor_sha256':{k:digest(v.tolist()) for k,v in model.state_dict().items()}})
    provenance={'training_samples':[r['sample_id'] for r in rows],'training_scenarios':[r['scenario_id'] for r in rows],
        'pair_ids':[p.pair_id for p in all_pairs],'input_selection_sha256':file_hash(run.root/'selection.json'),'batch_order':order,'equal_pair_weights':True,'sampling':sampling}
    if continued:
        old=load(run.root/'numerical'/source_variant/'fit.json')['provenance']
        if any(provenance[k]!=old[k] for k in ('training_samples','training_scenarios','pair_ids','input_selection_sha256')) or order[:len(old['batch_order'])]!=old['batch_order']:
            raise ValueError('continuation_data_or_sampler_prefix_changed')
        provenance['continuation_policy_sha256']=digest(extra)
    starting_update=trainer.updates if trainer else 0
    # Carry elapsed fit time across interrupted/resumed segments as well as the
    # explicitly planned 4k continuation. The aggregate ledger independently
    # retains full worker/failed-attempt wall time.
    if history: prior_seconds=max(prior_seconds,history[-1].get('seconds',0.))
    if continued and (not extra['source_updates']<=starting_update<=maximum or len(history)!=starting_update):
        raise ValueError('continuation_optimizer_or_history_update_mismatch')
    def checkpoint(update):
        directory=folder/'checkpoints'/str(update)/'deployment'
        if primary:
            pointer=write_checkpoint(directory,trainer,context_identity=context,provenance=provenance,sampler_state={},deployment=True)
        else: pointer=save_checkpoint(directory,model,context_identity=context,provenance=provenance,deployment=True)
        selected_rows=rows if base=='small_fit' else val; selected_refs=refs if base=='small_fit' else valrefs
        measured=diagnostic(run,model,solver,settings,selected_rows,selected_refs,save_folder=folder/'milestones'/str(update))
        save(folder/'milestones'/str(update)/'summary.json',{k:v for k,v in measured.items() if k!='rows'})
        score=measured['selection_score']; selected=load(folder/'selected.json') if (folder/'selected.json').exists() else None
        if selected is None or score<selected['score']:
            save(folder/'selected.json',{'directory':str(directory.relative_to(folder)),'checkpoint':pointer,'update':update,'score':score,'selection_split':'train_fitting_only' if base=='small_fit' else 'validation'})
        if primary: save(folder/'milestones'/str(update)/'gradients.json',gradients(run,model,solver,batches[0],es[0]))
        print(json.dumps({'variant':variant,'update':update,'validation_or_fit_score':score,'loss':history[-1].get('loss',history[-1].get('numerical_mse')) if history else None}),flush=True)
    if trainer is None:
        fit=model.fit_lr(torch.tensor([p.n_current for p in all_pairs]),torch.tensor([p.n_next for p in all_pairs]),torch.cat(es)); history=[fit]; checkpoint(0)
    else:
        if trainer.updates==0:
            before=diagnostic(run,model,solver,settings,rows[:2],refs); save(folder/'before_fit.json',before)
        for i in range(trainer.updates,maximum):
            if time.monotonic()-started>c['numerical_job_seconds']-15: break
            index=order[i]; item=trainer.step(batches[index],es[index]); history.append({**item,'sample_id':batches[index][0].identity.sample_id,'pair_ids':[p.pair_id for p in batches[index]],'seconds':prior_seconds+time.monotonic()-started})
            if trainer.updates%500==0 or trainer.updates in c['checkpoint_milestones']:
                save(folder/'history.json',history)
                if primary: write_checkpoint(folder/'resume',trainer,context_identity=context,provenance=provenance,sampler_state={'next':trainer.updates})
                else: save_checkpoint(folder/'resume',model,context_identity=context,provenance=provenance,trainer=trainer,sampler={'next':trainer.updates})
            if trainer.updates in c['checkpoint_milestones']: checkpoint(trainer.updates)
        if not (folder/'selected.json').exists(): checkpoint(trainer.updates)
    save(folder/'history.json',history)
    save(folder/'fit.json',{'status':'complete' if trainer is None or trainer.updates==maximum else 'component_cap',
        'updates':trainer.updates if trainer else 0,'unique_pairs':len(all_pairs),'questions':len(rows),'seconds':prior_seconds+time.monotonic()-started,
        'starting_update':starting_update,'execution_seconds_this_segment':time.monotonic()-started,'prior_training_seconds':prior_seconds,
        'solver_stats':trainer.stats.manifest() if trainer else None,'provenance':provenance})
