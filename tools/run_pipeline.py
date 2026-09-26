"""Executable stage graph and resource supervisor for qualification/study runs."""
import argparse
import os
import signal
import subprocess
import time
from p10_common import Run,ROOT,load,save,file_hash

BASELINES=('biasinit_constant_context_text_ode','fixed_projection_lr','constant_context_text_rnn','biasinit_no_enrichment','biasinit_no_text_conditioning')
CONTINUATIONS=('biasinit_conditioned_full','biasinit_constant_context_text_ode','constant_context_text_rnn','biasinit_no_enrichment','biasinit_no_text_conditioning')
STUDY=[('prepare',None),('prepare_evaluation',None),('verify',None),('enrich',None),('encode',None),('select_methods',None),
    ('numerical','biasinit_conditioned_full'),*[('numerical',x) for x in BASELINES],('custom_prepare',None),
    ('custom','coconut_broad'),('custom','codi_broad'),('forecast',None),('custom_forecast','coconut'),('custom_forecast','codi'),
    ('evaluate',None),('diagnose',None),('assessment',None),('answers',None),('evaluate',None),('setup_report',None),('report',None),('export',None)]
ORDER=[('prepare',None),('validate_release',None),('prepare_evaluation',None),('verify',None),('enrich',None),('encode',None),('numerical','small_fit'),
    *[('numerical',x) for x in ('raw_early','conditioned_early','raw_full','conditioned_full')],
    *[('numerical','biasinit_'+x) for x in ('small_fit','raw_early','conditioned_early','raw_full','conditioned_full')],
    ('select_methods',None),*[('numerical',x) for x in BASELINES],
    ('custom_prepare',None),('custom','coconut_small'),('custom','codi_small'),('custom','coconut_broad'),('custom','codi_broad'),
    ('custom_forecast','coconut'),('custom_forecast','codi'),('prepare_continuation',None),*[('numerical','continued_'+m) for m in CONTINUATIONS],('select_continued_methods',None),
    ('forecast',None),('evaluate',None),('diagnose',None),('assessment',None),('answers',None),('evaluate',None),('setup_report',None),('report',None),('export',None)]


def launch(run,stage,job=None,*,force=False):
    if run.c.get('full_study') and run.c.get('execution_authorized') is not True:
        raise RuntimeError('full_study_proposal_not_authorized_for_execution')
    lock=run.b.root/'.pipeline.lock'
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try: return _launch(run,stage,job,force=force)
    finally: os.close(descriptor); lock.unlink()


def _launch(run,stage,job=None,*,force=False):
    resource='gpu' if stage in ('custom','custom_forecast','encode') else 'cpu'
    if stage=='custom_cohort': resource='gpu'
    if stage=='public_cohort' and job.endswith('--encode'): resource='gpu'
    # Provider stages reserve calls independently; charge CPU process time there,
    # not HTTP wall time against the CPU execution allowance.
    if stage in ('answers','enrich','clarify','assessment_cohort'): resource=None
    if stage=='public_cohort' and job.endswith(('--answers','--enrich')): resource=None
    key=stage+('-'+job if job else '')
    path=run.root/'stages'/f'{key}.json'
    if path.exists() and load(path)['status'] in ('complete','complete_bounded') and not force:
        print(key+': already complete',flush=True); return
    run.b.check()
    if run.b.read()['active']: raise RuntimeError('inspect_interrupted_active_stage_before_resume')
    stage_env=('phi-coconut-custom' if job and job.startswith('coconut') else 'phi-codi-custom') if stage in ('custom','custom_forecast') else 'phi-core'
    if stage=='custom_cohort': stage_env='phi-coconut-custom' if job.endswith('--coconut') else 'phi-codi-custom'
    command=[str(run.native/'.venvs'/stage_env/'bin/python'),str(ROOT/'tools/p10_worker.py'),str(run.config_path),stage]
    if stage=='report':
        command[0]=str(run.root/'report-env/bin/python')
        if not __import__('pathlib').Path(command[0]).exists(): raise RuntimeError('run_setup_report_stage_first')
    if job: command.append(job)
    env={**os.environ,'P10_SUPERVISED':'1','HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false','MPLCONFIGDIR':str(run.root/'plot-config')}
    if resource!='gpu': env['CUDA_VISIBLE_DEVICES']=''
    start=time.time(); initial=run.b.read()['seconds'].get(resource,0) if resource else 0
    initial_cpu=run.b.read()['seconds'].get('cpu',0); sampled_cpu=0.
    limit=run.c['caps'][resource+'_seconds']-initial if resource else run.c.get('provider_stage_seconds',3600)
    if stage=='numerical':
        if job.startswith('continued_'):
            from p10_continuation import policy
            limit=min(limit,policy(run)['job_seconds'])
        else: limit=min(limit,run.c['numerical_job_seconds'])
    if stage=='custom': limit=min(limit,run.c['custom_job_seconds'][job])
    record={'status':'running','stage':stage,'job':job,'started':start,'resource':resource,'command':command,'source_sha256':run.provenance(key),'deadline':start+limit}
    attempt_id=f'{key}-{time.time_ns()}'
    save(path,record); log=run.root/'logs'/f'{attempt_id}.log'; log.parent.mkdir(exist_ok=True)
    peak_rss=None
    with log.open('w') as stream:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        reason=None
        while process.poll() is None:
            try:
                rss=next(int(line.split()[1]) for line in __import__('pathlib').Path(f'/proc/{process.pid}/status').read_text().splitlines() if line.startswith('VmRSS:'))
                peak_rss=max(peak_rss or 0,rss)
                stat=__import__('pathlib').Path(f'/proc/{process.pid}/stat').read_text().split()
                sampled_cpu=(int(stat[13])+int(stat[14]))/os.sysconf('SC_CLK_TCK')
            except (OSError,StopIteration): pass
            state=run.b.read()
            if state['stopped']: reason=state['stopped']
            elif resource is None and initial_cpu+sampled_cpu+.5>=run.c['caps']['cpu_seconds']: reason='cpu_seconds'
            elif time.time()>=start+limit: reason='stage_time_cap'
            elif run.b.size()>=run.c['caps']['artifact_bytes']: reason='artifact_bytes'
            if reason:
                os.killpg(process.pid,signal.SIGTERM)
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL); process.wait()
                break
            time.sleep(.5)
    elapsed=time.time()-start; state=run.b.read()
    if resource: state['seconds'][resource]=state['seconds'].get(resource,0)+elapsed
    else: state['seconds']['cpu']=max(state['seconds'].get('cpu',0),initial_cpu+sampled_cpu+.5)
    state['operations'].append({'name':key,'resource':resource,'seconds':elapsed,'exit_code':process.returncode,'reason':reason})
    if reason in ('artifact_bytes','cpu_seconds') or (resource and state['seconds'].get(resource,0)>=run.c['caps'][resource+'_seconds']): state['stopped']=reason or resource+'_seconds'
    save(run.b.path,state)
    record.update(status='complete' if process.returncode==0 else 'capped' if reason else 'failed',exit_code=process.returncode,reason=reason,seconds=elapsed,log=str(log),peak_worker_rss_kib=peak_rss)
    if process.returncode==0 and stage in ('numerical','custom'):
        fit=load(run.root/stage/job/'fit.json')
        if fit['status']=='component_cap': record.update(status='complete_bounded',reason='training_stopped_at_component_allowance',actual_updates=fit['updates'])
    save(run.root/'attempts'/f'{attempt_id}.json',record)
    save(path,record); print(__import__('json').dumps(record),flush=True)
    if stage=='export' and process.returncode==0:
        # Close exported accounting after the worker is charged. Otherwise the
        # copied budget/export-stage record would lag its own completion.
        import shutil
        destination=ROOT/run.c['export_directory']; manifest=load(destination/'manifest.json')
        for source,relative in [(run.b.path,'budget.json'),(path,'stages/'+path.name),(run.root/'attempts'/f'{attempt_id}.json','attempts/'+attempt_id+'.json')]:
            target=destination/relative; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,target)
            manifest['files'][relative]={'sha256':file_hash(target),'bytes':target.stat().st_size}
        manifest.update(accounting_closed_after_export=True,aggregate_new_bytes=run.b.size(),export_bytes=sum(v['bytes'] for v in manifest['files'].values()))
        save(destination/'manifest.json',manifest)
    if process.returncode!=0: raise RuntimeError('stage_incomplete:'+key+'; see '+str(log))


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--config',default=str(ROOT/'configs/qualification_p10.json'))
    p.add_argument('stage',choices=['all','study','controls','bias_controls','baselines','numerical_all','customs','status',*[x[0] for x in ORDER],'enrich','encode','seal','calibrate','clarify','report','public_cohort','benchmark_cohort','custom_cohort','assessment_cohort','aggregate'])
    p.add_argument('job',nargs='?'); p.add_argument('--refresh',action='store_true'); a=p.parse_args(); run=Run(a.config)
    if a.stage=='status': print(__import__('json').dumps({'budget':run.b.read(),'stages':{p.stem:load(p) for p in (run.root/'stages').glob('*.json')}},indent=2)); return
    if a.stage in ('numerical','custom','custom_forecast','public_cohort','custom_cohort','assessment_cohort','benchmark_cohort','clarify','aggregate') and not a.job:
        p.error('this stage requires an explicit job, cohort role, or clarification request ID')
    if a.stage=='bias_controls':
        for variant in ('small_fit','raw_early','conditioned_early','raw_full','conditioned_full'): launch(run,'numerical','biasinit_'+variant)
        return
    if a.stage=='baselines':
        launch(run,'select_methods')
        for variant in BASELINES: launch(run,'numerical',variant)
        return
    if a.stage in ('controls','numerical_all','customs'):
        selected=[x for x in ORDER if (x[0]=='numerical' if a.stage=='numerical_all' else x[0]=='numerical' and x[1] in ('raw_early','conditioned_early','raw_full','conditioned_full') if a.stage=='controls' else x[0] in ('custom_prepare','custom','custom_forecast'))]
        if a.stage=='numerical_all': launch(run,'select_methods')
        for stage,job in selected:
            if job and job.startswith('continued_'): launch(run,'prepare_continuation')
            launch(run,stage,job)
        if a.stage=='numerical_all': launch(run,'select_continued_methods')
        return
    if a.stage in ('all','study'):
        for stage,job in ORDER if a.stage=='all' else STUDY: launch(run,stage,job,force=stage in ('evaluate','report','export'))
    else: launch(run,a.stage,a.job,force=a.refresh)


if __name__=='__main__': main()
