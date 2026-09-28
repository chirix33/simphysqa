"""Dispatch explicit stage boundaries; references are opened only by data/eval/train."""
import os
import sys
from p10_common import Run,save

if __name__=='__main__':
    if os.environ.get('P10_SUPERVISED')!='1': raise RuntimeError('use run_pipeline.py resource supervisor')
    run=Run(sys.argv[1]); stage=sys.argv[2]; job=sys.argv[3] if len(sys.argv)>3 else None
    import importlib.metadata
    import platform
    import time
    packages={}
    for name in ('torch','transformers','sentence-transformers','numpy','scipy','tokenizers','safetensors','python-dotenv','matplotlib'):
        try: packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: packages[name]=None
    save(run.root/'environments'/f"{stage}-{job or 'default'}-{time.time_ns()}.json",{'interpreter':sys.executable,'python':sys.version,
        'platform':platform.platform(),'packages':packages,'offline_models':os.environ.get('HF_HUB_OFFLINE'),'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),
        'observed_at_stage':stage,'job':job,'meaning':'Observed for this worker; does not retroactively relabel earlier execution environments.'})
    if stage=='setup_report':
        import p10_setup as module
    elif stage in ('prepare','enrich','encode','seal','custom_prepare','validate_release'):
        import p10_data as module
    elif stage=='numerical':
        import p10_numerical as module
    elif stage in ('custom','custom_forecast'):
        import p10_custom as module
    elif stage=='forecast':
        import p10_inference as module
    elif stage=='clarify':
        import p10_clarification as module
    elif stage=='report':
        import p10_report as module
    elif stage=='diagnose':
        import p10_diagnostics as module
    elif stage=='aggregate':
        import p10_aggregate as module
    elif stage in ('prepare_continuation','select_continued_methods'):
        import p10_continuation as module
    elif stage in ('prepare_evaluation','public_cohort','benchmark_cohort','custom_cohort','assessment_cohort'):
        import p10_cohort as module
    else:
        import p10_benchmark as module
    getattr(module,stage)(run,job)
