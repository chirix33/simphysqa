"""Evaluator-only coordinate/physical diagnostics; never used to select checkpoints."""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
import torch
from p08_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import forecast_states
from phi_jepa.training.checkpoint import load_checkpoint as load_primary
from phi_jepa.baselines.checkpoint import load_checkpoint as load_baseline
from phi_jepa.inference.readout import read_targets
from phi_jepa.coordinate_diagnostics import decompose,coordinate_unit
from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors
from phi_jepa.solvers.rk4 import rk4,SolverSettings,SolveStats


def main():
    torch.set_num_threads(2); b=budget(); provenance('numerical_evaluation'); l=layout(); refs=load(RUN/'private/validation-references.json')
    rows=[r for r in public_records() if r['split']=='validation']; columns=[]; structure={p:v for p,t,v in l.structure}
    for path,typ in l.entries:
        group='fixed_conditioning' if path[0]==('key','fixed_conditioning') else ('time_index' if path[-1] in (('key','timestamp'),('key','step_index')) else 'physical')
        columns.append({'name':'/'.join(':'.join(map(str,x)) for x in path),'unit':coordinate_unit(path,structure),'group':group})
    summary=[]
    with b.operation('numerical_and_hold_last_evaluation','cpu'):
        for method in CONFIG['numerical_methods']:
            folder=RUN/'numerical'/method; info=load(folder/'fit.json'); primary=method in ('phi_jepa','no_enrichment'); mode=info['context_identity']['mode']; stats=SolveStats()
            if primary: model,solver=load_primary(folder/'deployment',layout=l,context_identity=info['context_identity'],training=False)
            else: model,_,_,_=load_baseline(folder/'deployment',layout=l,context_identity=info['context_identity'],method=method,training=False); solver=SolverSettings(**CONFIG['solver'])
            aggregate={k:{'pred':[],'truth':[]} for k in ('one_step','autonomous')}
            for row in rows:
                sid=row['sample_id']; p=PublicProblem.parse(row['public']); ref=refs[sid]; saved=load(folder/'forecasts'/f'{sid}.json'); record={'method':method,'sample_id':sid,'scenario_id':row['scenario_id'],'split':'validation'}
                states=forecast_states(p,ref); truth=torch.tensor([l.flatten(s,p.input) for s in states[1:]]); current=torch.tensor([l.flatten(s,p.input) for s in states[:-1]])
                e=torch.tensor([load(RUN/'embeddings'/mode/f'{sid}.json')['values']]*len(current)) if method!='no_text_conditioning' else None
                try:
                    with torch.no_grad():
                        if primary: one=rk4(model,torch.cat((current,model.projection(e)),dim=-1),[s['timestamp'] for s in states[:-1]],[s['timestamp'] for s in states[1:]],solver,stats)[:,:l.d]
                        else:
                            projected=model.projection(e) if e is not None else None; hidden=None; preds=[]
                            for i,(a,z) in enumerate(zip(states,states[1:])):
                                out,hidden=model.next_state(current[i:i+1],projected[i:i+1] if projected is not None else None,a['timestamp'],z['timestamp'],solver=solver,stats=stats,hidden=hidden); preds.append(out)
                            one=torch.cat(preds)
                    record['one_step']=decompose(one.tolist(),truth.tolist(),columns)
                    aggregate['one_step']['pred'].extend(one.tolist()); aggregate['one_step']['truth'].extend(truth.tolist())
                except (ValueError,RuntimeError) as exc: record['one_step']={'status':'failure','reason':str(exc)}
                if saved['status']=='success':
                    pred=[list(x['values'][:l.d]) for x in saved['trajectory']['predictions']]
                    record['autonomous']=decompose(pred,truth.tolist(),columns); aggregate['autonomous']['pred'].extend(pred); aggregate['autonomous']['truth'].extend(truth.tolist())
                    record['physical']=trajectory_errors(saved['named']['states'],ref['states'],mode='autonomous')
                    record['answer_readout']=evaluate_targets(p,ref,saved['readout'],method=method)
                else:
                    record['autonomous']={'status':'failure','reason':saved['reason']}; record['physical']=trajectory_errors([],ref['states'],mode='autonomous')
                    record['answer_readout']=evaluate_targets(p,ref,[],method=method,failure=saved['reason'])
                if method=='phi_jepa':
                    measures=[m for m in p.input['states'][-1]['measurements'] if type(m['value']) is not bool]
                    hold={'sample_id':sid,'source':'autonomous_numeric_forecast','states':[{'timestamp':s['timestamp'],'measurements':deepcopy(measures)} for s in ref['states']]}
                    save(RUN/'evaluation/hold-last'/f'{sid}.json',{'label':'hold_last_physical_diagnostic_not_paper_baseline','physical':trajectory_errors(hold['states'],ref['states'],mode='autonomous'),'targets':evaluate_targets(p,ref,read_targets(p,hold),method='hold_last_diagnostic')})
                save(RUN/'evaluation/numerical'/method/f'{sid}.json',record)
                summary.append({**{k:record[k] for k in ('method','sample_id','scenario_id')},'one_step_mse':record['one_step'].get('raw_numerical_mse'),
                    'autonomous_mse':record['autonomous'].get('raw_numerical_mse'),'complete_readout_success':record['answer_readout']['complete_success'], 'physical_metrics':record['physical']['metrics']})
            save(RUN/'evaluation/numerical'/method/'aggregate.json',{k:decompose(v['pred'],v['truth'],columns) if v['pred'] else {'status':'all_failed'} for k,v in aggregate.items()}|{'eligible_questions':8,'diagnostic_solver':stats.manifest()})
        save(RUN/'evaluation/numerical-summary.json',summary)
    print(json.dumps({'evaluated_method_questions':len(summary)}),flush=True)


if __name__=='__main__': main()
