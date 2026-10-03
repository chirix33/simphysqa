"""Evaluator-only raw coordinate decomposition; never changes model/loss/state."""
import math


def coordinate_unit(path, structure):
    """Named time/tolerance fields override a parent target's physical unit."""
    field = path[-1]
    if field in tuple(('key', name) for name in ('timestamp', 'start_time', 'end_time', 'observation_cutoff', 'update_interval_s')):
        return 's'
    if field == ('key', 'step_index'): return 'integration_step_count'
    if field == ('key', 'relative_tolerance'): return '1'
    for length in range(len(path), 0, -1):
        unit = structure.get(path[:length] + (('key', 'unit'),))
        if unit is not None: return unit
    return 'not_declared_in_public_metadata'


def decompose(predictions,targets,columns):
    if not predictions or len(predictions)!=len(targets) or not columns: raise ValueError('diagnostic_shape')
    width=len(columns); rows=[]; groups={}
    for p,t in zip(predictions,targets):
        if len(p)!=width or len(t)!=width or any(type(x) not in (int,float) or not math.isfinite(x) for x in (*p,*t)): raise ValueError('diagnostic_shape_or_finite')
    total=0.
    for i,column in enumerate(columns):
        p=[r[i] for r in predictions]; t=[r[i] for r in targets]
        mse=math.fsum((a-b)**2 for a,b in zip(p,t))/len(p)
        row={**column,'column':i,'prediction_range':[min(p),max(p)],'target_range':[min(t),max(t)],'coordinate_mse':mse,'raw_numerical_mse_contribution':mse/width}
        rows.append(row); total+=mse/width
        group=groups.setdefault(column['group'],{'width':0,'raw_numerical_mse_contribution':0.})
        group['width']+=1; group['raw_numerical_mse_contribution']+=mse/width
    for row in rows: row['fraction_of_raw_mse']=row['raw_numerical_mse_contribution']/total if total else 0.
    for group in groups.values():
        group['within_group_mse']=group['raw_numerical_mse_contribution']*width/group['width']
        group['fraction_of_raw_mse']=group['raw_numerical_mse_contribution']/total if total else 0.
    return {'timepoints':len(predictions),'numerical_width':width,'raw_numerical_mse':total,'groups':groups,'coordinates':rows,'meaning':'raw mixed-unit coordinate MSE decomposition, not unit-consistent physical accuracy'}
