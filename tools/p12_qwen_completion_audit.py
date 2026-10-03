"""Post-run trace comparison and retained-baseline compliance; no generation."""
from pathlib import Path
from p12_common import ROOT,NATIVE,load,save
from p12_qwen_completion_run import RUN,EXPORT,checked
from phi_jepa.integration.readers import file_hash
from phi_jepa.providers.explicit_reasoning import DELIMITER


def main():
    cfg,rows=checked();budget=load(RUN/'budget.json')
    if budget['finished_unix'] is None:raise ValueError('model run must close first')
    oldrun=NATIVE/'p12-answer-interface-qualification-02'
    comparisons=[];failures=[]
    for row in rows:
        sid=row['sample_id'];rel=Path('round-1/qwen3_8b_thinking')/(sid+'.json')
        before,after=load(oldrun/rel),load(RUN/rel)
        oldids,newids=before['generated_token_ids'],after['generated_token_ids']
        comparisons.append(dict(sample_id=sid,previous_status=before['status'],current_status=after['status'],
            previous_tokens=len(oldids),current_tokens=len(newids),previous_reasoning_tokens=before['reasoning_tokens'],
            current_reasoning_tokens=after.get('reasoning_tokens'),current_final_tokens=after.get('final_answer_tokens'),
            previous_sequence_preserved_as_prefix=newids[:len(oldids)]==oldids,
            current_separation_failure=after.get('separation_failure'),current_failure=after.get('failure'),
            previous_sha256=file_hash(oldrun/rel),current_sha256=file_hash(RUN/rel)))
        if after['status']!='success':
            # An incomplete trace is evidence only; never recover an answer from it.
            decoded=load(RUN/'partial-decoded/qwen3_8b_thinking'/(sid+'.json')) if after.get('raw_completion') is None else after
            failures.append(dict(sample_id=sid,failure=after.get('failure'),boundary_failure=decoded.get('separation_failure'),
                reasoning_tail=decoded.get('reasoning','')[-2000:],final_text=decoded.get('final_text',''),
                output_tokens=after['output_tokens'],automatic_escalation=False))
    compliance=[]
    for row in rows:
        path=oldrun/'round-1/llama31_8b_cot'/(row['sample_id']+'.json');r=load(path)
        text=r.get('reasoning','');prefix=text.split(DELIMITER,1)[0] if DELIMITER in text else text
        compliance.append(dict(sample_id=row['sample_id'],nonempty_reasoning=bool(prefix.strip()),
            final_answer_valid=r['full_contract_valid'],reasoning_segment_tokens=r['reasoning_tokens'],
            reasoning_prefix_characters=len(prefix.strip()),source_sha256=file_hash(path)))
    previous=load(oldrun/'evaluation/summary.json');current=load(RUN/'evaluation/summary.json')
    retained={c:{'label':'Llama-3.1-8B-Instruct prompted CoT' if c=='llama31_8b_cot' else c,
        'new_attempts_in_this_qualification':0,'source_run':str(oldrun),'summary':previous[c]}
        for c in ('qwen3_8b_direct','llama31_8b_direct','llama31_8b_cot')}
    record=dict(comparisons=comparisons,remaining_failure_traces=failures,retained_conditions=retained,
        qwen_4096_summary=previous['qwen3_8b_thinking'],qwen_8192_summary=current['qwen3_8b_thinking'],
        llama_prompted_cot=dict(new_generations=0,eligible=8,nonempty_reasoning=sum(x['nonempty_reasoning'] for x in compliance),
            strict_valid=sum(x['final_answer_valid'] for x in compliance),definition='Non-whitespace text before the exact final delimiter; marker itself is excluded.',
            filtering=False,selective_regeneration=False,records=compliance),
        historical_budget_unchanged=file_hash(oldrun/'budget.json')==load(ROOT/'docs/reviews/artifacts/P12_qwen_budget_8192_preparation/offline-verification.json')['prior_development_budget_sha256'],
        scientific_source_sha256=cfg['source_sha256'],audit_source_sha256=file_hash(Path(__file__)))
    if not record['historical_budget_unchanged']:raise ValueError('historical budget changed')
    path=RUN/'evaluation/completion-and-compliance-audit.json';save(path,record)
    save(EXPORT/'evaluation/completion-and-compliance-audit.json',record)
    sha=file_hash(Path(__file__))
    for root in (RUN,EXPORT):
        blob=root/'sources/blobs'/sha;blob.parent.mkdir(parents=True,exist_ok=True);blob.write_bytes(Path(__file__).read_bytes())
    save(EXPORT/'artifact-index.json',{str(p.relative_to(EXPORT)):file_hash(p) for p in EXPORT.rglob('*') if p.is_file() and p.name!='artifact-index.json'})
    print({'same_previous_token_prefixes':sum(x['previous_sequence_preserved_as_prefix'] for x in comparisons),
        'cases':len(comparisons),'remaining_failures':len(failures),'llama_prompted_cot_nonempty_reasoning':record['llama_prompted_cot']['nonempty_reasoning'],
        'llama_prompted_cot_strict_valid':record['llama_prompted_cot']['strict_valid'],'retained_baseline_new_generations':0})


if __name__=='__main__':main()
