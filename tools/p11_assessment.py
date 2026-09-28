"""Fixed development familiarity and separate checks; never calibrated OOD."""
from p11_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.assessment.reference import ReferenceBank
from phi_jepa.assessment.checks import physical_checks,contract_score
from phi_jepa.assessment.fixed import combine

def assess():
    import torch
    guard_deployment_io();profile=load(ROOT/'configs/assessment_p04b.json');asset={'prompt':load(ROOT/'docs/assets/prompts.json')['JUDGE_PROMPT'],'schema':load(ROOT/'docs/assets/judge_schema.json')}
    for cohort in ('main','appendix'):
        for domain in load(OUT/'plan.json')['cohorts']:
            run=StudyRun(domain,cohort);folder=run.root/'numerical/phi_jepa';dest=OUT/'assessment'/cohort/domain
            if not (folder/'selected.json').exists():save(dest/'status.json',{'status':'unavailable','reason':'checkpoint_unavailable'});continue
            selected=load(folder/'selected.json');settings=load(folder/'job.json');l=run.layout()
            bundle=torch.load(folder/selected['directory']/selected['checkpoint']['file'],map_location='cpu',weights_only=True)
            projection={k:digest(v.tolist()) for k,v in bundle['state'].items() if k.startswith('projection.')}
            identity={'checkpoint_sha256':selected['checkpoint']['sha256'],'projection_sha256':digest(projection),'encoder_sha256':digest(settings['context_identity']),'solver_sha256':digest(run.c['solver']),'layout_sha256':l.sha256,'profile_sha256':digest(profile)}
            entries=[];queries={}
            for row in run.rows():
                path=folder/'forecasts'/f"{row['sample_id']}.json"
                if not path.exists():continue
                saved=load(path)
                if saved['status']!='success':continue
                e=load(OUT/'embeddings/enriched'/f"{row['sample_id']}.json")
                entry={'sample_id':row['sample_id'],'scenario_id':row['scenario_id'],'split':row['split'],'domain':domain,'origin':'autonomous_prediction','layout_sha256':l.sha256,'cutoff':row['public']['input']['observation_cutoff'],'times':[v['physical_time'] for v in saved['trajectory']['predictions']],'trajectory':[v['values'] for v in saved['trajectory']['predictions']],'embedding':e['values'],'public_sha256':digest(row['public']['input']),'embedding_request_sha256':e['request_sha256']}
                if row['split']=='train':entries.append(entry)
                elif row['split']=='test_id':queries[row['sample_id']]=entry
            try:bank=ReferenceBank.build(identity,entries);path=bank.write(dest/'bank')
            except Exception as exc:save(dest/'status.json',{'status':'unavailable','reason':str(exc)});continue
            save(dest/'bank_identity.json',{'identity':identity,'bank_sha256':bank.sha256,'entries':len(entries)})
            for row in [r for r in run.rows() if r['split']=='test_id']:
                sid=row['sample_id'];p=PublicProblem.parse(row['public']);path=folder/'forecasts'/f'{sid}.json'
                if not path.exists() or sid not in queries:save(dest/f'{sid}.json',{'status':'failure','reason':'forecast_or_embedding_unavailable'});continue
                saved=load(path);ident={**identity,'bank_sha256':bank.sha256,'judge_asset_sha256':digest(asset)}
                result=combine(bank.assess(queries[sid],l,identity=identity),contract_score(p,saved['named'],p.input['controller'].get('constraints',[])),{'status':'unavailable','score':None,'reason':'V1_judge_not_run_in_frozen_deadline_plan'},profile=profile,identity=ident)
                save(dest/f'{sid}.json',{'assessment':result,'physical_checks':physical_checks(p,saved['named'],profile['physical_checks']),'calibration':'unavailable','automatic_OOD_alarm':False})
    save(OUT/'assessment/calibration.json',{'status':'unavailable','threshold':None,'reason':'Required typed assessment contracts and complete V1 components unavailable; no test calibration or tuning','prior_disjoint_inventory':'P10 sealed_inventory preserved; P11 main selection/test IDs recorded separately','OOD_evaluation':'deferred_sealed','clarification':'separate_human_reviewed_not_run'})

if __name__=='__main__':assess()
