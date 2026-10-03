"""Budget-only qualification preparation and disabled fresh-validation v2 freeze.

No model generation, reference reads, reselection or scientific-interface changes.
"""
from copy import deepcopy
from dataclasses import replace,asdict
from pathlib import Path
import argparse
import json
import shutil
from p12_common import ROOT,NATIVE,load,save
from p12_answer_interface_followup import DEST as ORIGINAL, settings as previous_settings, verify as verify_original
from p12_answer_interface import ASSET
from phi_jepa.artifacts import digest,canonical
from phi_jepa.integration.readers import file_hash
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.constrained_local import prepare_request,decoder_schema
from phi_jepa.providers.compact_answer import value_schema,adapt_answer

DEST=ROOT/'docs/reviews/artifacts/P12_qwen_budget_8192_preparation'
CONDITIONS=('qwen3_8b_thinking',)
RUN=NATIVE/'p12-qwen-thinking-budget-8192-01'
FRESH=ROOT/'docs/reviews/artifacts/P12_fresh_validation_v2_8192'


def settings(condition):
    cfg,tokenizer=previous_settings(condition)
    if condition=='qwen3_8b_thinking':cfg=replace(cfg,max_new_tokens=8192,max_seconds=360)
    return cfg,tokenizer


def assert_budget_only(old,new):
    candidate=deepcopy(new)
    candidate['settings']['max_new_tokens']=old['settings']['max_new_tokens']
    candidate['settings']['max_seconds']=old['settings']['max_seconds']
    if candidate!=old:raise ValueError('change outside the two authorized allowance fields')
    if new['settings']['max_new_tokens']!=8192 or new['settings']['max_seconds']!=360:
        raise ValueError('incorrect revised allowances')


def request_from(old,cfg,tok,problem):
    new=json.loads(canonical(prepare_request(tok,problem,load(ASSET)['prompt'],cfg)))
    assert_budget_only(old,new)
    return new


def verify():
    verify_original()
    freeze=load(DEST/'freeze.json')
    for rel,sha in freeze['files'].items():
        if file_hash(ROOT/rel)!=sha:raise ValueError('budget qualification preparation changed: '+rel)
    print(json.dumps({'budget_only_preparation_verified':True,'new_model_calls':0,'freeze_sha256':file_hash(DEST/'freeze.json')}))


def prepare():
    from p10_common import guard_deployment_io
    guard_deployment_io()
    verify_original()
    if (DEST/'freeze.json').exists():verify();return
    cfg=load(ORIGINAL/'development/plan.json');rows=load(ORIGINAL/'development/public-cohort.json')
    if len(rows)!=8 or any(r['split']!='validation' for r in rows):raise ValueError('original eight required')
    s,tok=settings('qwen3_8b_thinking')
    from transformers import AutoConfig
    import xgrammar as xgr
    mc=AutoConfig.from_pretrained(s.model,revision=s.revision,cache_dir=str(NATIVE/'model-cache'),local_files_only=True)
    compiler=xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(tok,vocab_size=mc.vocab_size,stop_token_ids=tok.eos_token_id))
    indexes=[]
    for row in rows:
        p=PublicProblem.parse(row['public']);sid=p.sample_id
        old=load(ORIGINAL/'development/requests/qwen3_8b_thinking'/(sid+'.json'))
        req=request_from(old,s,tok,p)
        compiled=compiler.compile_json_schema(decoder_schema(req,p))
        for abstain in (False,True):
            sample={}
            for spec in p.input['answer_spec']:
                vs=value_schema(p,spec)
                v=False if spec['answer_type']=='boolean' else ([0.]*vs['minItems'] if spec['answer_type']=='vector' else 0.)
                sample[spec['target_id']]=dict(status='unsupported' if abstain else 'supported',value=None if abstain else v,reason='Offline unrelated dummy' if abstain else None)
            text=json.dumps(sample);matcher=xgr.GrammarMatcher(compiled)
            if not all(matcher.accept_token(t) for t in tok.encode(text,add_special_tokens=False)) or not matcher.accept_token(tok.eos_token_id):
                raise ValueError('pinned-tokenizer grammar path failed')
            adapt_answer(p,text)
        path=DEST/'development/requests/qwen3_8b_thinking'/(sid+'.json');save(path,req)
        indexes.append(dict(condition='qwen3_8b_thinking',sample_id=sid,path=str(path.relative_to(ROOT)),sha256=file_hash(path),
            input_tokens=len(req['input_token_ids']),output_token_reserve=8192,
            full_context_reserve=len(req['input_token_ids'])+8192,context_limit=s.max_input_and_output,
            unchanged_messages_input_ids_schema=True,supported_and_unsupported_dummy_paths=True))
    cfg.update(version='p12-qwen-thinking-budget-8192-v1',enabled=True,execution_authorized=True,
        status='authorized_pending_execution',proposed_run_root=str(RUN),
        conditions={'qwen3_8b_thinking':{**cfg['conditions']['qwen3_8b_thinking'],'settings':asdict(s)}},
        request_manifest=indexes,generation_order=list(CONDITIONS),
        prerequisite='User authorized on 2026-10-01: all eight once, eight attempts, one hour, no retries.',
        execution_launcher_status='Versioned supervisor with hard 360-second request deadlines and a persisted 3600-second window.',
        stop_policy='No retries, repairs, forced reasoning termination, additional escalation, confirmation requests or other conditions.',
        fresh_candidate_selection_rule='Recommend the revised setting for the disabled fresh proposal if all eight complete with strict valid answers without repair; forecasting score does not select the budget. Otherwise retain as an unselected candidate requiring review.')
    cfg['budget'].update(maximum_attempts=8,model_window_seconds=3600,maximum_per_request_time_sum_seconds=2880,
        loading_setup_and_overhead_allowance_seconds=720,
        window_policy='Persisted one-hour clock starts before model/tokenizer loading; 8 x 360 seconds reserves 48 minutes, leaving 12 minutes for setup/other overhead. Never reset on resume; do not start a request unless its full allowance fits.')
    cfg['reporting']['separate_conditions']=list(CONDITIONS)
    save(DEST/'development/public-cohort.json',rows);save(DEST/'development/plan.json',cfg)
    save(ROOT/'configs/p12_qwen_completion_8192.approved.json',cfg)
    save(DEST/'offline-verification.json',dict(model_calls=0,request_checks=8,dummy_grammar_paths=16,
        maximum_input_plus_output=max(r['full_context_reserve'] for r in indexes),context_limit=s.max_input_and_output,
        scientific_source_sha256=cfg['source_sha256'],only_setting_changes=['max_new_tokens','max_seconds'],
        prior_development_budget_sha256=file_hash(NATIVE/'p12-answer-interface-qualification-02/budget.json')))
    paths=[p for p in DEST.rglob('*') if p.is_file()]+[ROOT/'configs/p12_qwen_completion_8192.approved.json']
    save(DEST/'freeze.json',dict(files={str(p.relative_to(ROOT)):file_hash(p) for p in paths},model_calls=0))
    verify()


def fresh():
    """Freeze the already-selected fresh cohort only after qualification closes."""
    verify_original()
    if (FRESH/'freeze.json').exists():
        for rel,sha in load(FRESH/'freeze.json')['files'].items():
            if file_hash(ROOT/rel)!=sha:raise ValueError('fresh proposal freeze changed')
        print('Existing disabled fresh proposal verified.');return
    ledger=load(RUN/'budget.json')
    if not ledger.get('finished_unix'):raise ValueError('qualification must close first')
    summary=load(RUN/'evaluation/summary.json')['qwen3_8b_thinking']
    selected=summary['requests_attempted']==summary['requests_completed']==summary['full_contract_valid']==8
    cfg=load(ORIGINAL/'fresh-validation/plan.json');rows=load(ORIGINAL/'fresh-validation/public-cohort.json')
    s,tok=settings('qwen3_8b_thinking');indexes=[]
    for old_index in cfg['request_manifest']:
        old=load(ROOT/old_index['path']);condition=old_index['condition'];sid=old_index['sample_id']
        if condition=='qwen3_8b_thinking':
            row=next(r for r in rows if r['sample_id']==sid)
            req=request_from(old,s,tok,PublicProblem.parse(row['public']))
        else:req=old
        path=FRESH/'requests'/condition/(sid+'.json');save(path,req)
        if condition!='qwen3_8b_thinking' and file_hash(path)!=old_index['sha256']:
            raise ValueError('unchanged condition request changed')
        indexes.append({**old_index,'path':str(path.relative_to(ROOT)),'sha256':file_hash(path),
            'output_token_reserve':req['settings']['max_new_tokens'],
            'full_context_reserve':len(req['input_token_ids'])+req['settings']['max_new_tokens']})
    cfg['conditions']['qwen3_8b_thinking']['settings']=asdict(s)
    cfg['conditions']['llama31_8b_cot']['label']='Llama-3.1-8B-Instruct prompted CoT'
    cfg.update(version='p12-fresh-validation-v2-qwen8192',enabled=False,execution_authorized=False,
        status='frozen_proposal_pending_review',request_manifest=indexes,
        proposed_run_root=str(NATIVE/'p12-answer-interface-fresh-validation-02'),
        qwen_revised_settings_selected_for_proposal=selected,
        selection_reason='All eight development answers completed with strict validity; selection ignores forecasting scores.' if selected else
            'Completion qualification is incomplete; revised settings remain an unselected candidate pending review.',
        qualification_summary_sha256=file_hash(RUN/'evaluation/summary.json'),
        prerequisite='Separate user review and authorization of this frozen fresh-validation proposal. No execution authorized.',
        stop_policy='One round, 32 attempts, no retries/repairs/selective regeneration, no automatic escalation or score-directed prompt tuning.',
        execution_launcher_status='Disabled pending review. Bind a versioned supervisor to this 150-minute manifest before authorized fresh generation.',
        reasoning_compliance='Label Llama as prompted CoT. Report nonempty text before the exact delimiter separately from final-answer validity; retain all eight responses regardless of compliance.',
        freeze_policy='All 32 requests, existing scenario-disjoint cohort and unchanged scientific sources are frozen before any fresh generation or output inspection.')
    cfg['budget'].update(model_window_seconds=9000,maximum_per_request_time_sum_seconds=6720,
        loading_setup_and_overhead_allowance_seconds=2280,
        window_policy='32 requests at 120/360/120/240 seconds total 112 minutes worst case. Shared window is 150 minutes, including 38 minutes setup/other overhead. Persist before loading, never reset, enforce hard deadlines.')
    cfg['reporting']['fields'].append('Llama prompted CoT nonempty reasoning/8 separately from final validity; no filtering')
    save(FRESH/'public-cohort.json',rows)
    if file_hash(FRESH/'public-cohort.json')!=file_hash(ORIGINAL/'fresh-validation/public-cohort.json'):
        raise ValueError('fresh cohort reselection prohibited')
    save(FRESH/'plan.json',cfg);path=ROOT/'configs/p12_answer_interface_fresh_validation_v2.proposed.json';save(path,cfg)
    paths=[p for p in FRESH.rglob('*') if p.is_file()]+[path]
    save(FRESH/'freeze.json',dict(files={str(p.relative_to(ROOT)):file_hash(p) for p in paths},
        scientific_source_files=cfg['source_files'],scientific_source_sha256=cfg['source_sha256'],
        enabled=False,fresh_model_generations=0,cohort_unchanged=True,qwen_revised_settings_selected=selected))
    print(json.dumps(dict(fresh_enabled=False,selected=selected,requests=32,maximum_request_sum_minutes=112,
        shared_window_minutes=150,setup_overhead_minutes=38,freeze_sha256=file_hash(FRESH/'freeze.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('prepare','verify','fresh'));args=parser.parse_args()
    globals()[args.stage]()
