"""Independent per-layout fits; main selection and appendix final policy differ."""
from p11_common import *
from p10_numerical import *
from phi_jepa.training.sampling import fixed_pair_batches

def train(domain,cohort):
    run=StudyRun(domain,cohort);torch.set_num_threads(2);folder=run.root/'numerical/phi_jepa';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'fit.json').exists() and load(folder/'fit.json')['status']=='complete':return
    source=archive_sources(f'numerical-{cohort}-{domain}');l=run.layout();rows=[r for r in run.rows() if r['split']=='train'];refs=load(OUT/'private'/domain/'train-references.json')
    all_pairs=[]
    for row in rows:
        p=PublicProblem.parse(row['public']);ident=Identity(p.sample_id,row['scenario_id'],row['split_group'],domain,'train');states=forecast_states(p,refs[p.sample_id]);counts=Counter({digest((domain,ident.group_id,a['timestamp'],b['timestamp'])):1 for a,b in zip(states,states[1:])})
        all_pairs.extend(make_pairs(p,refs[p.sample_id],ident,l,'p11',counts,context_mode='enriched',enrichment=load(OUT/'enrichment'/f'{p.sample_id}.json'),duplicate_policy='equal_question_pairs'))
    embeddings={r['sample_id']:torch.tensor(run.embedding(r['sample_id'])) for r in rows};context={'encoder':load(OUT/'encoding-report.json')['settings'],'mode':'enriched','variant':f'p11-{cohort}-{domain}'}
    job={'variant':'phi_jepa','method':'phi_jepa','primary':True,'context_identity':context,'conditioning':True,'full_interval':True,'output_bias_initialization':'training_mean_adjacent_derivative'};save(folder/'job.json',job)
    solver=SolverSettings(method='rk4',substeps=1);provenance={'training_samples':[r['sample_id'] for r in rows],'training_scenarios':[r['scenario_id'] for r in rows],'pair_ids':[p.pair_id for p in all_pairs],'equal_pair_weights':True,'sampler':'uniform shuffled pair cycles, fixed batches with carried tails','source_identity':source,'plan_sha256':file_hash(OUT/'plan.json')}
    if (folder/'resume/latest.json').exists():trainer,_,_=load_primary(folder/'resume',layout=l,context_identity=context,training=True);model=trainer.model
    else:
        transform=NumericalConditioning.fit([p.n_current for p in all_pairs],layout_sha256=l.sha256,provenance={'split':'train','sample_ids':provenance['training_samples'],'scenario_ids':provenance['training_scenarios']})
        torch.manual_seed(11);model=AugmentedODE(l,ProjectionSettings(1024,seed=11),ODESettings(seed=11),transform);trainer=PairTrainer(model,solver,TrainingSettings(context_mode='enriched'))
        derivative=torch.tensor([[(b-a)/p.dt for a,b in zip(p.n_current,p.n_next)] for p in all_pairs]).mean(0)
        with torch.no_grad():model.field[-1].bias[:l.d].copy_(derivative);model.field[-1].bias[l.d:].zero_()
        save(folder/'initialization.json',{'fresh':True,'seed':11,'manifest':model.manifest(),'train_mean_derivative':derivative.tolist(),'parameter_count':sum(p.numel() for p in model.parameters())})
    history=restored_history(folder,trainer.updates);start=time.time();prior=history[-1]['seconds'] if history else 0
    for i,ids in enumerate(fixed_pair_batches(all_pairs,20,20000,11)):
        if i<trainer.updates:continue
        time_guard();batch=[all_pairs[k] for k in ids];e=torch.stack([embeddings[p.identity.sample_id] for p in batch]);record=trainer.step(batch,e)
        history.append({**record,'update':trainer.updates,'pair_ids':[p.pair_id for p in batch],'seconds':prior+time.time()-start})
        if trainer.updates%500==0:
            save(folder/'history.json',history);write_checkpoint(folder/'resume',trainer,context_identity=context,provenance=provenance,sampler_state={'next':trainer.updates})
        if trainer.updates in (5000,10000,20000):
            directory=folder/'checkpoints'/str(trainer.updates)/'deployment';pointer=write_checkpoint(directory,trainer,context_identity=context,provenance=provenance,sampler_state={},deployment=True)
            if cohort=='main':
                val=[r for r in run.rows() if r['split']=='validation'];valrefs=load(OUT/'private'/domain/'validation-references.json');metric=diagnostic(run,model,solver,job,val,valrefs,save_folder=folder/'selection'/str(trainer.updates));score=metric['selection_score']
                old=load(folder/'selected.json') if (folder/'selected.json').exists() else None
                choose=old is None or score<old['score']
            else:score=None;choose=trainer.updates==20000
            if choose:save(folder/'selected.json',{'directory':str(directory.relative_to(folder)),'checkpoint':pointer,'update':trainer.updates,'score':score,'selection_split':'validation' if cohort=='main' else 'fixed_final_no_heldout_selection'})
            save(folder/'gradients'/f'{trainer.updates}.json',gradients(run,model,solver,batch,e));print(json.dumps({'domain':domain,'cohort':cohort,'update':trainer.updates,'score':score}),flush=True)
    save(folder/'fit.json',{'status':'complete','updates':trainer.updates,'unique_pairs':len(all_pairs),'pair_exposures':trainer.updates*20,'equivalent_pair_passes':trainer.updates*20/len(all_pairs),'questions':len(rows),'seconds':prior+time.time()-start,'provenance':provenance,'solver_stats':trainer.stats.manifest()})

def inference(domain,cohort):
    from p10_inference import load_selected,predict
    guard_deployment_io();run=StudyRun(domain,cohort);torch.set_num_threads(2);folder=run.root/'numerical/phi_jepa';model,solver,job=load_selected(run,'phi_jepa');chosen=load(folder/'selected.json')
    for row in run.rows():
        time_guard();path=folder/'forecasts'/f"{row['sample_id']}.json"
        if path.exists():continue
        try:result=predict(run,model,solver,job,row)
        except Exception as exc:result={'status':'failure','reason':str(exc),'type':type(exc).__name__}
        save(path,{**result,'checkpoint_sha256':chosen['checkpoint']['sha256'],'public_sha256':digest(row['public']),'deployment_guard':True})

if __name__=='__main__':
    globals()[sys.argv[1]](sys.argv[2],sys.argv[3])
