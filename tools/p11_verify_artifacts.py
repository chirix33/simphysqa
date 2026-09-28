"""Independent saved-artifact checks; no training, providers or score repair."""
from p11_common import *
from collections import Counter

def verify():
    import torch
    from hashlib import sha256
    plan=load(OUT/'plan.json');rows=load(OUT/'selected-public.json');checks=[]
    manifests=list((OUT/'sources').glob('*.json'))
    for path in manifests:
        for name,sha in load(path)['files'].items():assert file_hash(OUT/'sources/blobs'/sha)==sha
    checks.append({'check':'source_blob_integrity','status':'passed','manifests':len(manifests)})
    for domain,c in plan['cohorts'].items():
        train={r['scenario_id'] for r in rows if r['domain']==domain and r['split']=='train'};val={r['scenario_id'] for r in rows if r['domain']==domain and r['split']=='validation'};test={r['scenario_id'] for r in rows if r['domain']==domain and r['split']=='test_id'}
        assert not (train&val or train&test or val&test)
        checks.append({'check':'scenario_separation','domain':domain,'status':'passed','counts':[len(train),len(val),len(test)]})
        for cohort in ('main','appendix'):
            folder=StudyRun(domain,cohort).root/'numerical/phi_jepa'
            if not (folder/'fit.json').exists():checks.append({'check':'numerical_fit','domain':domain,'cohort':cohort,'status':'unavailable'});continue
            fit=load(folder/'fit.json');selected=load(folder/'selected.json');history=load(folder/'history.json')
            assert set(fit['provenance']['training_samples'])==set(c[cohort+'_train'])
            assert len(history)==fit['updates']==20000
            ids=[pid for row in history for pid in row['pair_ids']];exposure=Counter(ids)
            assert len(ids)==400000 and set(exposure)==set(fit['provenance']['pair_ids']) and max(exposure.values())-min(exposure.values())<=1
            if cohort=='appendix':assert selected['update']==20000 and selected['selection_split']=='fixed_final_no_heldout_selection'
            else:
                scores=[]
                for update in (5000,10000,20000):
                    vals=[load(p).get('selection_score',1e12) for p in (folder/'selection'/str(update)).glob('*.json')];scores.append((sum(vals)/len(vals),update))
                assert selected['update']==min(scores)[1]
            pointer=folder/selected['directory']/selected['checkpoint']['file'];assert file_hash(pointer)==selected['checkpoint']['sha256']
            checks.append({'check':'numerical_data_exposure_checkpoint','domain':domain,'cohort':cohort,'status':'passed','unique_pairs':len(exposure),'pair_exposure_range':[min(exposure.values()),max(exposure.values())],'selected_update':selected['update']})
    expected={sid for c in plan['cohorts'].values() for sid in c['appendix_train']}
    for short in ('coconut','codi'):
        folder=OUT/'custom'/short
        if not (folder/'fit.json').exists():checks.append({'check':'custom_two_passes','method':short,'status':'unavailable'});continue
        history=load(folder/'history.json');counts=Counter(r['sample_id'] for r in history);assert set(counts)==expected and set(counts.values())=={2} and len(history)==128
        assert all({r['sample_id'] for r in history if r['pass']==epoch}==expected for epoch in (1,2))
        selected=load(folder/'selected.json');assert selected['update']==128 and file_hash(folder/selected['directory']/selected['checkpoint']['file'])==selected['checkpoint']['sha256']
        payload=torch.load(folder/selected['directory']/selected['checkpoint']['file'],map_location='cpu',weights_only=True)
        initial=load(folder/'initialization.json')['parameter_hashes']
        changed=[name for name,original in initial.items() if sha256(payload['model'][name].numpy().tobytes()).hexdigest()!=original]
        assert any(name.startswith('t5.') for name in changed)
        if short=='codi':
            assert any(name.startswith('student_proj.') for name in changed)
            assert not any(name.startswith('teacher_proj.') for name in changed)
        save(folder/'parameter_update_verification.json',{'changed_parameters':changed,'total_named_parameters':len(initial),'teacher_projection_unchanged':True if short=='codi' else None,'meaning':'Actual checkpoint changes; gradient-path causality is covered by the unchanged offline model tests.'})
        del payload
        for p in (folder/'test_generations').glob('*.json'):assert load(p)['gold_generation_inputs'] is False and load(p)['teacher_inference_calls']==0
        checks.append({'check':'custom_two_passes','method':short,'status':'passed','updates':len(history),'examples':len(counts),'heldout_selection':False})
    for p in (OUT/'evaluation').glob('answers.json'):
        records=load(p);expected_questions={'main':48,'appendix':16}
        for cohort,n in expected_questions.items():
            values=[r for r in records if r['cohort']==cohort and r['condition']=='answer_generation'];grouped=Counter(r['method'] for r in values)
            methods={'Phi-JEPA','gpt-5.6-sol direct'} if cohort=='main' else {'Phi-JEPA','custom Coconut','custom CODI student'}
            assert set(grouped)==methods and all(v==n for v in grouped.values())
            expected_targets=sum(len(r['public']['input']['answer_spec']) for r in rows if r['split']=='test_id' and (cohort=='main' or r['appendix']))
            assert all(sum(v['eligible_targets'] for v in values if v['method']==m)==expected_targets for m in methods)
            checks.append({'check':'complete_question_denominators','cohort':cohort,'status':'passed','counts':dict(grouped)})
    save(OUT/'artifact_verification.json',{'checks':checks,'status':'passed_available_artifacts','missing_work_is_not_success':True});print(json.dumps(checks))

if __name__=='__main__':verify()
