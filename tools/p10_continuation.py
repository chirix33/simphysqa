"""One recorded exposure continuation; original model evidence is immutable."""
import shutil
from p10_common import *


POLICY=ROOT/'configs/qualification_p10_continuation.json'


def policy(run):
    value=load(POLICY)
    if load(run.root/'continuation_policy.json')!=value:
        raise ValueError('changed_continuation_policy_requires_new_evidence_run')
    return value


def prepare_continuation(run,job=None):
    value=load(POLICY); frozen=run.root/'continuation_policy.json'
    if frozen.exists() and load(frozen)!=value: raise ValueError('continuation_policy_changed')
    save(frozen,value)
    for method in value['source_methods']:
        source=run.root/'numerical'/method; target=run.root/'numerical'/('continued_'+method)
        marker=target/'continuation_origin.json'
        fit=load(source/'fit.json'); selected=load(source/'selected.json'); pointer=load(source/'resume/latest.json')
        if fit['updates']!=value['source_updates'] or fit['status']!='complete': raise ValueError('completed_source_fit_required')
        if len(load(source/'history.json'))!=fit['updates']: raise ValueError('source_exposure_history_mismatch')
        identity={'source_method':method,'source_resume':pointer,'source_selected':selected,'source_fit_sha256':file_hash(source/'fit.json'),
            'source_history_sha256':file_hash(source/'history.json'),'source_updates':fit['updates'],'prior_training_seconds':fit['seconds'],
            'policy_sha256':digest(value),'preserved_original_directory':str(source),'same_method_optimizer_continuation':True}
        if marker.exists():
            if load(marker)!=identity: raise ValueError('continuation_origin_changed')
            continue
        target.mkdir(parents=True,exist_ok=True)
        for name in ('initialization.json','bias_initialization.json','before_fit.json','history.json','selected.json'):
            if (source/name).exists(): shutil.copyfile(source/name,target/name)
        resume=target/'resume'; resume.mkdir(exist_ok=True)
        link=resume/pointer['file']
        if not link.exists(): link.symlink_to((source/'resume'/pointer['file']).resolve())
        save(resume/'latest.json',pointer)
        # Checkpoints are immutable content-addressed data. Only individual old
        # update directories are linked; new update directories remain local.
        for category in ('checkpoints','milestones'):
            (target/category).mkdir(exist_ok=True)
            for old in (source/category).iterdir():
                link=target/category/old.name
                if not link.exists(): link.symlink_to(old.resolve(),target_is_directory=old.is_dir())
        save(marker,identity)
    print(json.dumps({'continuations_prepared':len(value['source_methods']),'maximum_total_updates':value['updates'],'new_budget':False}))


def select_continued_methods(run,job=None):
    value=policy(run); methods=['continued_'+name for name in value['source_methods']]
    for method in methods:
        if not (run.root/'numerical'/method/'fit.json').exists(): raise ValueError('continuation_not_finished:'+method)
        # A failed diagnostic must not silently remove a saved selection
        # candidate. Recover its original checkpoint without optimizer updates.
        folder=run.root/'numerical'/method
        for update in value['checkpoint_milestones']:
            directory=folder/'checkpoints'/str(update)/'deployment'
            summary=folder/'milestones'/str(update)/'summary.json'
            if not (directory/'latest.json').exists() or summary.exists(): continue
            import torch
            from p10_numerical import diagnostic,load_primary,load_baseline,SolverSettings
            torch.set_num_threads(2); settings=load(folder/'job.json')
            if settings['primary']:
                model,solver=load_primary(directory,layout=run.layout(),context_identity=settings['context_identity'],training=False)
            else:
                model,_,_,_=load_baseline(directory,layout=run.layout(),context_identity=settings['context_identity'],method=settings['method'],training=False)
                solver=SolverSettings(**run.c['solver'])
            measured=diagnostic(run,model,solver,settings,[r for r in run.rows() if r['split']=='validation'],
                load(run.root/'private/validation-references.json'),save_folder=summary.parent)
            save(summary,{k:v for k,v in measured.items() if k!='rows'})
            pointer=load(directory/'latest.json'); selected=load(folder/'selected.json')
            if (measured['selection_score'],update)<(selected['score'],selected['update']):
                save(folder/'selected.json',{'directory':str(directory.relative_to(folder)),'checkpoint':pointer,
                    'update':update,'score':measured['selection_score'],'selection_split':'validation'})
            save(folder/'recovery'/f'diagnostic-{update}.json',{'checkpoint':pointer,'optimizer_updates':0,
                'reason':'saved candidate diagnostic interrupted; original failed attempt retained','selection_score':measured['selection_score']})
    methods.insert(2,'fixed_projection_lr')
    save(run.root/'active_methods.json',{'methods':methods,'prior_methods_preserved':value['source_methods'],
        'policy_sha256':digest(value),'reason':value['decision'],'lr':'Original independent least-squares fit reused; no iterative exposure change applies.'})
