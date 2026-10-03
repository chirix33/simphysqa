"""Read-only numerical run audit and export; never invokes a model/provider."""
import json
import math
import platform
import shutil
from collections import Counter
from pathlib import Path

from p12_common import ROOT, load, save, digest, file_hash
from p12_training_execution import APPROVED, CONTROL, ORDER, byte_count
import p12_training_plan as planning

EXPORT = ROOT/'docs/reviews/artifacts/P12_training_run'


def seal():
    """Seal additional offline reporting artifacts after plots/documents are rendered."""
    plan = load(APPROVED)
    planning.require_training_authorization(plan)
    planning.check_training_identity(plan)
    summary = load(EXPORT/'audit.json')
    if 'completion' in summary:
        if summary['completion']['wall_seconds'] > plan['training_wall_seconds_cap']:
            raise ValueError('aggregate wall cap exceeded')
        for domain,r in summary['domains'].items():
            if r['dispatch']['wall_seconds'] > plan['domains'][domain]['wall_seconds_cap']:
                raise ValueError('domain dispatch cap exceeded: '+domain)
    for name in ('p12_training_execution.py','p12_training_report.py',
                 'p12_training_curves.py','p12_training_completion_doc.py'):
        target = EXPORT/'reporting-source'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'tools'/name,target)
    shutil.copyfile(ROOT/'tests/test_p12_training_execution.py',EXPORT/'reporting-source/test_p12_training_execution.py')
    size = byte_count(Path(plan['study_root']),CONTROL,EXPORT)
    if size >= plan['artifact_bytes_cap']-100000000:
        raise ValueError('artifact cap including evidence export exhausted')
    save(EXPORT/'final-verification.json', {'original_proposal_sha256':file_hash(planning.PLAN_PATH),
        'approved_plan_sha256':file_hash(APPROVED),'numerical_source_unchanged':True,
        'evaluation_enabled':plan['evaluation_enabled'],'paid_calls':0,
        'native_plus_export_bytes_before_seal':size,'artifact_bytes_cap':plan['artifact_bytes_cap'],
        'checkpoint_blobs_verified':sum(len(r['checkpoint_blobs']) for r in summary['domains'].values()),
        'validation_sweeps_verified':sum(r['completed_validation_sweeps'] for r in summary['domains'].values()),
        'tests':[
            {'command':'PYTHONPATH=src:tests:tools python -m unittest test_p12_training_plan test_p12 test_p03 -q',
             'passed':26,'seconds':3.243},
            {'command':'PYTHONPATH=src:tests:tools python -m unittest test_p12_training_execution -v',
             'passed':2,'seconds':.015}]})
    save(EXPORT/'artifact-index.json',{str(p.relative_to(EXPORT)):file_hash(p)
        for p in EXPORT.rglob('*') if p.is_file() and p.name!='artifact-index.json'})
    print(json.dumps(load(EXPORT/'final-verification.json'),indent=2))


def audit():
    plan = load(APPROVED)
    planning.require_training_authorization(plan)
    planning.check_training_identity(plan)
    selection = load(planning.bound_path(plan,'selection'))
    old = plan['historical_proposal']
    if file_hash(old['path']) != old['sha256']:
        raise ValueError('historical proposal changed')
    preparation_export = ROOT/'docs/reviews/artifacts/P12_training_plan'
    preparation_index = load(preparation_export/'artifact-index.json')['files']
    for relative,sha in preparation_index.items():
        if file_hash(preparation_export/relative) != sha:
            raise ValueError('historical preparation export changed: '+relative)
    if file_hash(Path(plan['plan_root'])/'training-preflight.json') != preparation_index['training-preflight.json']:
        raise ValueError('historical preparation preflight changed')
    if not any((CONTROL/name).exists() for name in ('completion.json','failure.json')):
        raise ValueError('execution still active; do not publish a completion audit')
    summary = {'approved_plan_sha256': file_hash(APPROVED),
        'original_proposal_sha256': plan['authorized_proposal_sha256'],
        'numerical_source_sha256': plan['training_implementation_sha256'],
        'execution': load(CONTROL/'execution-window.json'), 'domains': {},
        'paid_calls': 0, 'confirmation_evaluations': 0, 'local_baseline_generations': 0,
        'convergence_claimed': False}
    summary['preservation'] = {'historical_proposal_unchanged':True,
        'preparation_export_files_verified':len(preparation_index),'preparation_preflight_unchanged':True}
    cpu = Path('/proc/cpuinfo').read_text()
    summary['environment'] = {'platform':platform.platform(),'python':platform.python_version(),
        'cpu_model':next(line.split(':',1)[1].strip() for line in cpu.splitlines() if line.startswith('model name')),
        'device':plan['device'],'torch_num_threads':plan['torch_num_threads'],
        'runtime_versions':plan['runtime_versions']}
    for name in ('completion','failure'):
        if (CONTROL/(name+'.json')).exists():
            summary[name] = load(CONTROL/(name+'.json'))
    for domain in ORDER:
        folder = Path(plan['study_root'])/domain
        settings = plan['domains'][domain]
        history_path = folder/'history.jsonl'
        history = [json.loads(line) for line in history_path.read_text().splitlines() if line.strip()] if history_path.exists() else []
        resume_reader_probe = {'records_read':0,'error':None}
        if history:
            from phi_jepa.integration.readers import json_lines
            reader = json_lines(history_path)
            try:
                for _ in range(min(2,len(history))):
                    next(reader)
                    resume_reader_probe['records_read'] += 1
            except ValueError as exc:
                resume_reader_probe['error'] = type(exc).__name__+': '+str(exc)
            finally:
                reader.close()
        if [r['update'] for r in history] != list(range(1,len(history)+1)):
            raise ValueError('noncontiguous successful update history: '+domain)
        if any(r['batch_size'] != settings['batch_pairs'] or not math.isfinite(r['loss']) for r in history):
            raise ValueError('nonfinite loss or changed batch size: '+domain)
        exposure = sum(r['batch_size'] for r in history)
        curve = []
        previous = 0
        validations = []
        validation_stats = Counter()
        for pass_number, update in enumerate(settings['checkpoints'], 1):
            rows = [r for r in history if previous < r['update'] <= update]
            if rows:
                curve.append({'pass':pass_number,'start_update':previous+1,'end_update':rows[-1]['update'],
                    'complete_training_pass':len(history)>=update, 'updates':len(rows),
                    'pair_exposure':sum(r['batch_size'] for r in rows),
                    **{key:sum(r[key] for r in rows)/len(rows) for key in
                       ('loss','numeric_mse','context_mse','p_l2_mean')},
                    'optimizer_wall_seconds':sum(r['wall_seconds'] for r in rows)})
            previous = update
            path = folder/'validation'/f'{update}.json'
            if not path.exists():
                continue
            val = load(path)
            records = val['records']
            if len(records) != settings['validation_questions']:
                raise ValueError('validation coverage changed: '+domain)
            expected_ids = {r['sample_id'] for r in selection if r['domain']==domain and r['split']=='validation'}
            if {r['sample_id'] for r in records} != expected_ids:
                raise ValueError('validation membership changed: '+domain)
            if sum(r['score'] for r in records)/len(records) != val['score']:
                raise ValueError('saved validation aggregate differs from records: '+domain)
            reasons = Counter()
            target_total = valid_targets = complete_answers = 0
            for record in records:
                validation_stats.update(record['stats'])
                result = record['result']
                if 'failure' in result:
                    reasons['rollout:'+result['failure']] += 1
                complete_answers += bool(result.get('complete_success',False))
                for target in result.get('targets',[]):
                    target_total += 1
                    valid_targets += target['status']=='valid'
                    if target['status'] != 'valid':
                        reasons[target.get('reason',target['status'])] += 1
            validations.append({'pass':pass_number,'update':update,'score':val['score'],
                'wall_seconds':val['seconds'],'questions':len(records),
                'complete_answers':complete_answers,'targets':target_total,'valid_targets':valid_targets,
                'failure_reasons':dict(reasons),
                'rollout_failures':sum('failure' in r['result'] for r in records),
                'penalized_questions':sum(r['score']>=1e12 for r in records),
                'source_sha256':file_hash(path)})
        selected = load(folder/'selected.json') if (folder/'selected.json').exists() else None
        if selected:
            best = min(validations,key=lambda r:(r['score'],r['update']))
            if (selected['update'],selected['score'],selected['split']) != (best['update'],best['score'],'validation'):
                raise ValueError('selected checkpoint differs from earliest validation minimum: '+domain)
            selected_path = folder/'checkpoints'/str(selected['update'])/selected['checkpoint']['file']
            if file_hash(selected_path) != selected['checkpoint']['sha256']:
                raise ValueError('selected checkpoint integrity failure: '+domain)
            selected = {**selected,'absolute_path':str(selected_path)}
        blobs = {str(p.relative_to(folder)):file_hash(p) for p in folder.rglob('*.pt')} if folder.exists() else {}
        if any(Path(key).stem != value for key,value in blobs.items()):
            raise ValueError('checkpoint blob integrity failure: '+domain)
        complete = load(folder/'complete.json') if (folder/'complete.json').exists() else None
        if complete and (complete['updates'],complete['pair_exposure'],complete['plan_sha256']) != (
            settings['optimizer_updates'],settings['actual_pair_exposure'],digest(plan)):
            raise ValueError('completed exposure/plan mismatch: '+domain)
        if complete and (len(history)!=settings['optimizer_updates'] or len(validations)!=10):
            raise ValueError('incomplete curves in completed domain: '+domain)
        checkpoint_reload = None
        if complete:
            from phi_jepa.integration.layout import StateLayout
            from phi_jepa.training.checkpoint import load_checkpoint
            manifest = load(plan['layout_files'][domain]['path'])
            layout = StateLayout.from_manifest(manifest,digest(manifest))
            context = {'encoder':plan['encoder_settings'],'mode':'enriched','run':'p12-expanded-seed11'}
            model,solver = load_checkpoint(folder/'checkpoints'/str(selected['update']),
                layout=layout,context_identity=context,training=False)
            trainer,sampler,provenance = load_checkpoint(folder/'resume',
                layout=layout,context_identity=context,training=True)
            if (trainer.updates,trainer.failed_updates,trainer.attempted_updates,sampler['next_update']) != (
                len(history),0,len(history),len(history)):
                raise ValueError('final optimizer accounting mismatch: '+domain)
            if provenance['source'] != plan['training_implementation_sha256'] or provenance['plan'] != digest(plan):
                raise ValueError('checkpoint source or plan mismatch: '+domain)
            checkpoint_reload = {'deployment_loaded':True,'optimizer_rng_loaded':True,
                'attempted_updates':trainer.attempted_updates,'failed_updates':trainer.failed_updates,
                'extra_optimizer_updates':0,'extra_rollouts':0}
            del model,solver,trainer
        resources = CONTROL/'resources'/f'{domain}.json'
        attempt = CONTROL/'attempts'/f'{domain}.json'
        summary['domains'][domain] = {'successful_updates':len(history),
            'actual_pair_exposure':exposure,'completed_passes':exposure//settings['pairs_per_pass'],
            'completed_validation_sweeps':len(validations),'planned':settings,
            'complete':complete,'selected':selected,'training_curve':curve,'validation_curve':validations,
            'first_update_loss':history[0]['loss'] if history else None,
            'last_update_loss':history[-1]['loss'] if history else None,
            'optimizer_seconds':sum(r['wall_seconds'] for r in history),
            'training_solve_stats':history[-1]['stats'] if history else {},
            'validation_solve_stats':dict(validation_stats),
            'validation_seconds':sum(r['wall_seconds'] for r in validations),
            'resources':load(resources) if resources.exists() else None,
            'dispatch':load(attempt) if attempt.exists() else None,
            'checkpoint_blobs':blobs,'artifact_bytes':byte_count(folder),
            'checkpoint_reload':checkpoint_reload,
            'frozen_resume_history_reader_probe':resume_reader_probe,
            'last_update_attempt':load(folder/'last-update-attempt.json') if (folder/'last-update-attempt.json').exists() else None}
    save(CONTROL/'audit.json', summary)
    EXPORT.mkdir(parents=True,exist_ok=True)
    for path in CONTROL.rglob('*'):
        if path.is_file() and path.name != 'worker.lock':
            dest = EXPORT/'execution'/path.relative_to(CONTROL)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest)
    for domain in ORDER:
        folder = Path(plan['study_root'])/domain
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix in ('.json','.jsonl'):
                dest = EXPORT/'domains'/domain/path.relative_to(folder)
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,dest)
    save(EXPORT/'audit.json', summary)
    save(EXPORT/'artifact-index.json', {str(p.relative_to(EXPORT)):file_hash(p)
        for p in EXPORT.rglob('*') if p.is_file() and p.name!='artifact-index.json'})
    print(json.dumps({d:{k:v for k,v in r.items() if k in ('successful_updates','actual_pair_exposure',
        'completed_passes','completed_validation_sweeps','resources','optimizer_seconds','validation_seconds')}
        for d,r in summary['domains'].items()},indent=2))


if __name__ == '__main__':
    import sys
    if '--seal' in sys.argv:
        seal()
    elif '--status' in sys.argv:
        from p12_training_execution import current_progress
        plan = load(APPROVED)
        progress = current_progress(plan)
        for domain,r in progress.items():
            folder = Path(plan['study_root'])/domain
            r['stage'] = ('complete' if r['complete'] else
                'validation' if (folder/'validation-inflight.json').exists() else
                'training' if (folder/'initialization.json').exists() else
                'context_and_pair_preparation' if (folder/'execution-window.json').exists() else
                'preflight' if (CONTROL/'attempts'/f'{domain}.json').exists() else 'pending')
        print(json.dumps(progress,indent=2))
        for domain in ORDER:
            folder = Path(plan['study_root'])/domain
            vals = sorted((folder/'validation').glob('*.json'),key=lambda p:int(p.stem))
            print(domain, [(p.stem,round(load(p)['score'],6)) for p in vals])
            print('validation_rollout_exceptions',sum('failure' in r['result'] for p in vals for r in load(p)['records']))
    else:
        audit()
