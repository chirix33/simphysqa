"""Fresh training-only proposal bound to completed P12 embedding manifests."""
from p12_common import *
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
import math
import shutil
import time

PLAN_ROOT = NATIVE/'p12-training-plan-01'
PLAN_PATH = PLAN_ROOT/'proposed-training-plan.json'
EMBEDDINGS = NATIVE/'p12-embedding-preparation-01'
EXPORT = ROOT/'docs/reviews/artifacts/P12_training_plan'
VERSION = 'p12-complete-context-training-v2'
EXPECTED = {'driving': (740, 740, 66600, 148), 'robotic_arm': (981, 1962, 127530, 388),
            'object_pushing_stacking': (1000, 2000, 130000, 400), 'tethered_load': (1000, 2000, 130000, 400)}
TRAIN_INPUTS = ('selection', 'cache_coverage', 'enrichment_origins', 'embedding_config', 'embedding_audit', 'encoding_report', 'population_audit')


def training_sources():
    files = [Path(__file__), ROOT/'tools/p12_train.py', ROOT/'tools/p12_common.py',
             ROOT/'src/phi_jepa/artifacts.py', ROOT/'src/phi_jepa/typed_evaluation.py',
             ROOT/'src/phi_jepa/providers/contracts.py', ROOT/'src/phi_jepa/inference/readout.py',
             ROOT/'src/phi_jepa/inference/rollout.py', ROOT/'configs/model_training_p02a.json',
             ROOT/'configs/model_context_p02b.json', ROOT/'MODEL_TRAINING_CONTRACT.md', ROOT/'AGENTS.md']
    files.extend(p for p in (ROOT/'src/phi_jepa/__init__.py', ROOT/'src/phi_jepa/providers/__init__.py',
                             ROOT/'src/phi_jepa/inference/__init__.py') if p.exists())
    for directory in ('integration', 'models', 'solvers', 'training'):
        files.extend((ROOT/'src/phi_jepa'/directory).glob('*.py'))
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(set(files))}


def descriptor(path):
    return {'path': str(path), 'sha256': file_hash(path)}


def bound_path(plan, key):
    if plan.get('plan_version') != VERSION:
        raise ValueError('obsolete proposal; regenerate from completed embedding manifests')
    item = plan['inputs'][key];path = Path(item['path'])
    if file_hash(path) != item['sha256']:
        raise ValueError('bound input changed: '+key)
    return path


def require_training_authorization(plan):
    if not plan.get('training_enabled') or not plan.get('training_authorization'):
        raise ValueError('separate numerical-training authorization required')
    if plan.get('plan_version') != VERSION or plan.get('enabled') is not False or plan.get('evaluation_enabled') is not False:
        raise ValueError('training-only plan required; evaluation stays disabled')
    prepared = load(PLAN_PATH)
    if plan.get('authorized_proposal_sha256') != file_hash(PLAN_PATH):
        raise ValueError('authorization must bind the prepared proposal')
    mutable = {'training_enabled', 'training_authorization', 'authorized_proposal_sha256'}
    if {k:v for k,v in plan.items() if k not in mutable} != {k:v for k,v in prepared.items() if k not in mutable}:
        raise ValueError('approved proposal settings changed')


def check_training_identity(plan):
    current = training_sources()
    if current != plan['training_source_files'] or digest(current) != plan['training_implementation_sha256']:
        raise ValueError('frozen numerical implementation changed')
    if {k:version(k) for k in plan['runtime_versions']} != plan['runtime_versions']:
        raise ValueError('training runtime changed')
    for domain, entry in plan['layout_files'].items():
        if file_hash(entry['path']) != entry['sha256']:raise ValueError('layout changed: '+domain)
    for key in TRAIN_INPUTS:bound_path(plan, key)
    if not (plan['encoder_settings'] == load(bound_path(plan,'encoding_report'))['settings'] == load(bound_path(plan,'embedding_config'))['settings']):
        raise ValueError('frozen encoder identity mismatch')


def validate_selection(rows, confirmation):
    all_rows = rows + confirmation
    if len({r['sample_id'] for r in all_rows}) != len(all_rows):raise ValueError('duplicate selection')
    if any(r['split'] not in ('train', 'validation') for r in rows):raise ValueError('test data in training selection')
    if any(r['split'] in ('train', 'validation') for r in confirmation):raise ValueError('training data in confirmation')
    groups = {}
    for r in all_rows:
        for key in ((r['domain'],r['scenario_id']), ('group',r['split_group'])):
            partition = (r['domain'], r['split'])
            if key in groups and groups[key] != partition:raise ValueError('scenario-group split leakage')
            groups[key] = partition
    for domain, (scenarios, questions, _, validation) in EXPECTED.items():
        train = [r for r in rows if r['domain'] == domain and r['split'] == 'train']
        valid = [r for r in rows if r['domain'] == domain and r['split'] == 'validation']
        if (len({r['scenario_id'] for r in train}),len(train),len(valid)) != (scenarios,questions,validation):
            raise ValueError('expanded selection counts changed: '+domain)
    if len(rows) != 8038 or len(confirmation) != 500 or len({(r['domain'],r['scenario_id']) for r in confirmation}) != 320:
        raise ValueError('expanded population changed')


def coverage_check(selection, coverage, origins, *, deep=True):
    ids = {r['sample_id'] for r in selection}
    if len(coverage) != len(ids) or len(origins) != len(ids):raise ValueError('coverage size mismatch')
    entries = {r['sample_id']:r for r in coverage};by_origin = {r['sample_id']:r for r in origins}
    if set(entries) != ids or set(by_origin) != ids:raise ValueError('coverage membership mismatch')
    missing = [];failures = []
    for selected in selection:
        sid = selected['sample_id'];r = entries[sid];origin = by_origin[sid]
        if not r.get('embedding_path') or not r.get('enrichment_path') or origin.get('status') != 'verified':
            missing.append(sid);continue
        if any(r[k] != selected[k] for k in ('domain','split','scenario_id','split_group','public_sha256')):
            raise ValueError('coverage selection binding mismatch')
        if (origin['domain'],origin['split']) != (r['domain'],r['split']):raise ValueError('origin split mismatch')
        if not deep:continue
        try:
            for kind in ('embedding','enrichment'):
                if file_hash(r[kind+'_path']) != r[kind+'_file_sha256']:raise ValueError(kind+' checksum')
            if file_hash(origin['cache_file']) != origin['cache_sha256']:raise ValueError('provider cache checksum')
            if any(r['compatible_origin'][k] != origin[k] for k in ('cache_file','cache_sha256','request_sha256')):
                raise ValueError('provider origin binding')
            vector = load(r['embedding_path']);notes = load(r['enrichment_path'])
            if digest(notes['public_input']) != selected['public_sha256']:raise ValueError('notes public binding')
            if (vector['request_sha256'],vector['context_sha256'],vector['token_count']) != (r['embedding_request_sha256'],r['context_sha256'],r['token_count']):
                raise ValueError('embedding context identity')
            values = vector['values']
            if len(values) != 1024 or any(type(v) not in (int,float) or not math.isfinite(v) for v in values):raise ValueError('embedding vector invalid')
            if not math.isclose(sum(v*v for v in values),1.,rel_tol=1e-5,abs_tol=1e-5):raise ValueError('embedding norm')
        except (ValueError, OSError, KeyError, TypeError) as exc:
            failures.append({'sample_id':sid,'reason':str(exc)})
    return {'questions':len(selection),'missing':missing,'integrity_failures':failures,'ready':not missing and not failures}


def preflight(plan, *, deep=True):
    started = time.perf_counter();check_training_identity(plan)
    selected = load(bound_path(plan,'selection'));confirmation = load(bound_path(plan,'confirmation_cohort'))
    validate_selection(selected,confirmation)
    scopes = {}
    for scope, rows, coverage_key, origin_key in (
        ('train_validation',selected,'cache_coverage','enrichment_origins'),
        ('confirmation',confirmation,'confirmation_coverage','confirmation_origins')):
        scopes[scope] = coverage_check(rows,load(bound_path(plan,coverage_key)),load(bound_path(plan,origin_key))['records'],deep=deep)
    authorized = False
    if plan.get('training_enabled'):
        require_training_authorization(plan);authorized = True
    report = {'plan_version':VERSION,'prepared_plan_sha256':digest(plan),'scopes':scopes,
              'eligible_questions':8038,'missing_identity_verified_contexts':sum(len(s['missing']) for s in scopes.values()),
              'missing_sample_ids':[sid for s in scopes.values() for sid in s['missing']],
              'integrity_failures':sum(len(s['integrity_failures']) for s in scopes.values()),
              'data_ready':all(s['ready'] for s in scopes.values()),'training_authorized':authorized,
              'can_train':authorized and scopes['train_validation']['ready'], 'evaluation_enabled':False,
              'training_started':False,'model_calls':0,'optimizer_updates':0,'paid_calls':0,
              'checks':'manifest and file hashes, full population membership, group splits, provider origins, frozen vectors',
              'seconds':time.perf_counter()-started}
    save(PLAN_ROOT/'training-preflight.json',report)
    return report


def build_plan():
    from phi_jepa.integration.readers import forecast_states
    from phi_jepa.training.pairs import TrainingSettings
    from phi_jepa.solvers.rk4 import SolverSettings
    from phi_jepa.models.augmented_ode import ODESettings
    from phi_jepa.models.context_projection import ProjectionSettings
    if PLAN_PATH.exists():
        plan = load(PLAN_PATH);check_training_identity(plan);return plan
    started = time.perf_counter();PLAN_ROOT.mkdir(parents=True,exist_ok=True)
    prior_path = OUT/'proposed-training-plan.json';prior_hash = file_hash(prior_path)
    historical_audit = load(OUT/'audit.json');selected = load(OUT/'selection.json');confirmation = load(OUT/'confirmation-cohort.json')
    validate_selection(selected,confirmation)
    completion = load(EMBEDDINGS/'audit.json');encoding = load(EMBEDDINGS/'encoding-report.json')
    if completion['missing'] or completion['coverage'] != {'train_validation':8038,'confirmation':500}:
        raise ValueError('embedding preparation incomplete')
    cat = catalog()
    if cat.identity != historical_audit['release_identity']:raise ValueError('frozen release changed')
    counts = {};domains = {};batch = 256;passes = 10
    selected_ids = {r['sample_id']:r for r in selected}
    for domain, expected in sorted(EXPECTED.items()):
        question_count = 0;pair_count = 0;scenarios = set();seen = set()
        for problem, reference, ident in cat.records(domain,'train'):
            if time.perf_counter()-started > 900:raise TimeoutError('training preparation audit cap')
            meta = selected_ids[problem.sample_id]
            if (ident.scenario_id,ident.group_id,ident.split,digest(problem.input)) != (meta['scenario_id'],meta['split_group'],meta['split'],meta['public_sha256']):
                raise ValueError('recorded training selection changed')
            question_count += 1;scenarios.add(ident.scenario_id);seen.add(problem.sample_id)
            pair_count += len(forecast_states(problem,reference))-1
        if (len(scenarios),question_count,pair_count) != expected[:3]:raise ValueError('training pair count changed')
        if seen != {r['sample_id'] for r in selected if r['domain']==domain and r['split']=='train'}:raise ValueError('training membership changed')
        updates = math.ceil(passes*pair_count/batch)
        domains[domain] = {'scenarios':len(scenarios),'questions':question_count,'pairs_per_pass':pair_count,
            'complete_passes':passes,'batch_pairs':batch,'optimizer_updates':updates,'actual_pair_exposure':updates*batch,
            'extra_pairs_in_next_cycle':updates*batch-passes*pair_count,'checkpoints':[math.ceil(p*pair_count/batch) for p in range(1,passes+1)],
            'validation_questions':expected[3],'wall_seconds_cap':3600}
        counts[domain] = {'scenarios':len(scenarios),'questions':question_count,'pairs':pair_count}
        print({'verified_domain':domain,**counts[domain]},flush=True)
    population = {'release_identity':cat.identity,'domains':counts,'selection_sha256':file_hash(OUT/'selection.json'),
                  'seconds':time.perf_counter()-started,'test_outcomes_opened':False,'optimizer_updates':0}
    save(PLAN_ROOT/'population-audit.json',population)
    paths = {'selection':OUT/'selection.json','cache_coverage':EMBEDDINGS/'cache-coverage.json',
        'enrichment_origins':EMBEDDINGS/'enrichment-origin-audit.json','confirmation_cohort':OUT/'confirmation-cohort.json',
        'confirmation_public':OUT/'confirmation-public.json','confirmation_coverage':EMBEDDINGS/'confirmation-cache-coverage.json',
        'confirmation_origins':EMBEDDINGS/'confirmation-enrichment-origin-audit.json','embedding_config':EMBEDDINGS/'config.json',
        'embedding_audit':EMBEDDINGS/'audit.json','encoding_report':EMBEDDINGS/'encoding-report.json',
        'population_audit':PLAN_ROOT/'population-audit.json'}
    files = training_sources()
    plan = {'plan_version':VERSION,'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'enabled':False,'training_enabled':False,'training_authorization':None,'authorized_proposal_sha256':None,
        'evaluation_enabled':False,'evaluation_authorization':None,'new_budget_required':True,
        'study_root':str(NATIVE/'p12-expanded-study-seed11'),'plan_root':str(PLAN_ROOT),
        'inputs':{k:descriptor(p) for k,p in paths.items()},'encoder_settings':encoding['settings'],
        'training_source_files':files,'training_implementation_sha256':digest(files),
        'layout_files':{d:descriptor(ROOT/f'docs/reviews/artifacts/P02a/{d}.state_plus_fixed_conditioning.json') for d in domains},
        'runtime_versions':{k:version(k) for k in ('torch','transformers','tokenizers','safetensors')},
        'domains':domains,'seed':11,'device':'cpu','torch_num_threads':2,'training_settings':asdict(TrainingSettings()),
        'solver_settings':asdict(SolverSettings()),'ode_settings':asdict(ODESettings(seed=11)),
        'projection_settings':asdict(ProjectionSettings(1024,seed=11)),
        'initialization':'fresh seed 11; train-only coordinate scaling and training-mean derivative bias; no diagnostic checkpoints',
        'training_wall_seconds_cap':14400,'artifact_bytes_cap':16000000000,'checkpoint_every_updates':100,
        'validation':{'split':'validation','schedule':'all validation questions after each complete pass',
                      'metric':'mean tolerance-normalized numerical target error','failed_question_penalty':1e12,'tie_break':'earliest update'},
        'resume_policy':'same immutable approved plan, population, source, cache and optimizer/RNG state; no budget reset; unresolved updates block replay',
        'historical_proposal':{'path':str(prior_path),'sha256':prior_hash,'preserved':True},
        'evaluation_proposal':{'status':'separately disabled pending final answer-interface decisions and authorization',
            'cohort_scenarios':320,'cohort_questions':500,'public_inputs_only_until_selected_checkpoints_locked':True,
            'local_conditions':['qwen3_8b_direct','qwen3_8b_thinking','llama31_8b_direct'],
            'original_model_lock':descriptor(ROOT/'configs/local_answers_p12.lock.json'),
            'maximum_generation_requests':1500,'generation_seconds_cap':64800,'numerical_inference_seconds_cap':1800,
            'automatic_retries':0,'paid_calls':0},
        'training_started':False,'executed_optimizer_updates':0,'paid_calls':0}
    for name, sha in files.items():
        target = PLAN_ROOT/'sources/blobs'/sha;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copyfile(ROOT/name,target)
    save(PLAN_ROOT/'source.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                               'dirty':True,'files':files,'identity':digest(files)})
    save(PLAN_PATH,plan)
    if file_hash(prior_path) != prior_hash:raise ValueError('historical proposal changed')
    return plan


def export():
    EXPORT.mkdir(parents=True,exist_ok=True)
    for path in [*PLAN_ROOT.glob('*.json'),*PLAN_ROOT.glob('*.log')]:shutil.copyfile(path,EXPORT/path.name)
    shutil.copytree(PLAN_ROOT/'sources',EXPORT/'sources',dirs_exist_ok=True)
    save(EXPORT/'artifact-index.json',{'native_root':str(PLAN_ROOT),'files':{str(p.relative_to(EXPORT)):file_hash(p) for p in EXPORT.rglob('*') if p.is_file() and p.name!='artifact-index.json'}})
