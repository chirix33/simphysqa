"""Read-only final selection/checkpoint/source checks within the CPU allowance."""
from collections import Counter
import torch
from p08_common import *

b=budget(); provenance('artifact_verification')
with b.operation('verify_selection_and_checkpoint_content','cpu'):
    rows=public_records(); train=[r for r in rows if r['split']=='train']; val=[r for r in rows if r['split']=='validation']
    ts={r['scenario_id'] for r in train}; vs={r['scenario_id'] for r in val}
    assert len(train)==len(ts)==32 and len(val)==len(vs)==8 and not ts&vs
    assert CONFIG['diagnostic_scenario'] in ts and CONFIG['diagnostic_scenario'] not in vs
    assert file_hash(RUN/'selection.json')=='3d621fafc275c20ae96a020f0eaef34ad4fec1753a8db9318bdbd0ff5c5170d6'
    checked=[]; numerical=[]; custom=[]
    for pointer in sorted(RUN.glob('numerical/*/*/latest.json'))+sorted(RUN.glob('custom/*/*/checkpoint/latest.json')):
        value=load(pointer); checkpoint=pointer.parent/value['file']; actual=file_hash(checkpoint)
        assert actual==value['sha256'],str(checkpoint)
        checked.append({'path':str(checkpoint),'sha256':actual,'bytes':checkpoint.stat().st_size})
    for method in CONFIG['numerical_methods']:
        fit=load(RUN/'numerical'/method/'fit.json'); p=fit['provenance']
        assert set(p['training_scenarios'])==ts and not set(p['training_scenarios'])&vs
        assert len(p['training_pair_ids'])==len(set(p['training_pair_ids']))==640
        counts=Counter(p['batch_question_schedule']); assert set(counts.values())=={31,32}
        numerical.append({'method':method,'updates':fit['updates'],'least_squares_fits':fit['least_squares_fits'],
            'question_batch_counts':dict(counts),'pair_population':640,'note':'LR fits each pair once; iterative methods use the saved shuffled-cycle schedule and equal weight in every batch'})
    for method in ('coconut_inspired_t5_gru','codi_inspired_t5_distillation'):
        a=RUN/'custom'/method/'diagnostic'; z=RUN/'custom'/method/'broad'
        first=load(a/'initialization.json'); second=load(z/'initialization.json')
        assert first['fresh'] and second['fresh'] and not first['warm_start'] and not second['warm_start']
        assert first['parameter_hashes']==second['parameter_hashes']
        for phase,folder,expected in [('diagnostic',a,20),('broad',z,180)]:
            identity=load(folder/'identity.json'); fit=load(folder/'fit.json'); history=load(folder/'history.json')
            assert not set(identity['training_scenarios'])&vs
            assert fit['updates']==len(history)==expected
            assert fit['changed_parameters']
            if method.startswith('codi'): assert fit['teacher_projection_unchanged']
            custom.append({'method':method,'phase':phase,'updates':fit['updates'],'changed_parameter_tensors':len(fit['changed_parameters']),
                'changed_backbone_tensors':sum(n.startswith('t5.') for n in fit['changed_parameters']),
                'changed_latent_path_tensors':sum(not n.startswith(('t5.','teacher_proj.','student_proj.')) for n in fit['changed_parameters']),
                'changed_student_projection_tensors':sum(n.startswith('student_proj.') for n in fit['changed_parameters']),
                'updates_with_nonzero_student_projection_gradient':sum(r.get('student_projection_gradient_norm',0)>0 for r in history) if method.startswith('codi') else None,
                'fixed_teacher_projection_unchanged':fit['teacher_projection_unchanged'],'sample_update_counts':dict(Counter(r['sample_id'] for r in history))})
    original=load(ROOT/'docs/reviews/artifacts/P07/sources.json')
    for path,value in original.items(): assert file_hash(Path(path))==value['sha256'],path
    environments={}
    probe="import json,sys,torch,transformers,numpy; print(json.dumps({'python':sys.version,'torch':torch.__version__,'cuda_build':torch.version.cuda,'transformers':transformers.__version__,'numpy':numpy.__version__}))"
    for environment in ('phi-core','phi-coconut-custom','phi-codi-custom'):
        environments[environment]=json.loads(subprocess.check_output([str(NATIVE/'.venvs'/environment/'bin/python'),'-c',probe],text=True))
    hardware=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],text=True).strip()
    save(RUN/'evaluation/runtime-environments.json',{'environments':environments,'GPU':hardware,'precision':'BF16 autocast / FP32 custom parameters; numerical CPU FP32','model_environments_modified':False})
    save(RUN/'evaluation/artifact-verification.json',{'scenario_separation':True,'frozen_selection_sha256':file_hash(RUN/'selection.json'),
        'original_P07_sources_unchanged':len(original),'latest_checkpoint_hashes_verified':checked,'numerical':numerical,'custom':custom,
        'fresh_diagnostic_and_broad_initialization':True,'test_scope':'content/identity and saved-history checks, not new optimizer or inference calls'})
print(json.dumps({'scenario_separation':True,'checkpoint_pointers_verified':len(checked),'original_P07_sources_verified':len(original)}))
