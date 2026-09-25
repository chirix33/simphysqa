"""Standalone scientific learning/error figures from saved evaluator outputs."""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RUN=Path('/home/aashraf/phi-jepa/p08-learning-01')
OUT=RUN/'evaluation/figures'; OUT.mkdir(parents=True,exist_ok=True)
def load(path): return json.loads(path.read_text())
curves=load(RUN/'evaluation/learning-curves.json'); generations=load(RUN/'evaluation/generation-diagnostics.json')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
fig,axes=plt.subplots(2,2,figsize=(12,8))
csv_rows=[]
for i,short in enumerate(('coconut','codi')):
    for j,phase in enumerate(('diagnostic','broad')):
        ax=axes[i,j]; data=curves['custom'][short+'_'+phase]
        components=('loss','ce_loss','smoothness_loss') if short=='coconut' else ('loss','teacher_ce','student_ce','alignment','smoothness_loss')
        for key in components:
            rows=[r for r in data['history'] if key in r]
            if rows:
                ax.plot([r['update'] for r in rows],[r[key] for r in rows],label=key,linewidth=1.1,alpha=.8)
                csv_rows.extend({'method':short,'phase':phase,'kind':'pre_update_train_mode','update':r['update'],'component':key,'value':r[key]} for r in rows)
        if data['eval_losses']:
            ax.scatter([r['update'] for r in data['eval_losses']],[r['loss'] for r in data['eval_losses']],label='train-example eval-mode total',color='black',s=23,zorder=5)
            csv_rows.extend({'method':short,'phase':phase,'kind':'training_example_eval_mode','update':r['update'],'component':key,'value':r[key]} for r in data['eval_losses'] for key in components if key in r)
        ax.set(title=f'{short.capitalize()} — {phase} (fresh initialization)',xlabel='Optimizer update',ylabel='Method-specific loss (log scale)')
        ax.set_yscale('log'); ax.grid(alpha=.2); ax.legend(fontsize=7)
fig.suptitle('Training losses only; diagnostic example fitting is separate from validation',fontsize=12)
fig.tight_layout(); fig.savefig(OUT/'custom-learning-curves.png'); fig.savefig(OUT/'custom-learning-curves.svg'); plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(15,4),sharey=True)
for short,branch in [('coconut','coconut'),('codi','student'),('codi','teacher')]:
    rows=sorted([r for r in generations if r['phase']=='diagnostic' and r['method']==short and r['branch']==branch],key=lambda r:r['milestone'])
    for ax,key in zip(axes,('valid_typed_output','EOS_terminated','complete_success')):
        ax.plot([r['milestone'] for r in rows],[float(r[key]) if r[key] is not None else math.nan for r in rows],marker='o',label=short+' '+branch,alpha=.8)
for ax,title in zip(axes,('Valid typed answer','EOS termination','Complete-answer success')):
    ax.set(title=title,xlabel='Diagnostic update',ylim=(-.1,1.1),yticks=[0,1],ylabel='One training example: 0 / 1'); ax.grid(alpha=.2); ax.legend(fontsize=8)
fig.suptitle('Training-only generation diagnostics; missing observations are gaps')
fig.tight_layout(); fig.savefig(OUT/'diagnostic-generation.png'); fig.savefig(OUT/'diagnostic-generation.svg'); plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,4))
for method,rows in curves['numerical'].items():
    key='loss' if method in ('phi_jepa','no_enrichment') else 'numerical_mse'
    values=[r for r in rows if key in r]
    if not values: continue
    ax=axes[0 if key=='loss' else 1]; ax.plot([r['update'] for r in values],[r[key] for r in values],label=method,linewidth=1)
    csv_rows.extend({'method':method,'phase':'broad','kind':'pre_update_train_mode','update':r['update'],'component':key,'value':r[key]} for r in values)
for ax,title in zip(axes,('Full augmented MSE (2d)','Numerical MSE (d)')):
    ax.set(title=title,xlabel='Optimizer update',ylabel='Raw mixed-unit loss'); ax.set_yscale('log'); ax.grid(alpha=.2); ax.legend(fontsize=7)
fig.suptitle('Different objectives shown separately; these curves are not forecast rankings')
fig.tight_layout(); fig.savefig(OUT/'numerical-learning-curves.png'); fig.savefig(OUT/'numerical-learning-curves.svg'); plt.close(fig)
summary=load(RUN/'evaluation/numerical-summary.json'); rows=[r for r in summary if r['method']=='phi_jepa']
fig,axes=plt.subplots(1,3,figsize=(13,4))
for ax,quantity,unit in zip(axes,('position','swing_angle','angular_velocity'),('m','rad','rad/s')):
    model=[]; hold=[]
    for r in rows:
        model.append(next(m['rmse_valid_only'] for m in r['physical_metrics'] if m['entity_id']=='load' and m['quantity']==quantity))
        h=load(RUN/'evaluation/hold-last'/f"{r['sample_id']}.json")
        hold.append(next(m['rmse_valid_only'] for m in h['physical']['metrics'] if m['entity_id']=='load' and m['quantity']==quantity))
    ax.plot(range(1,len(rows)+1),model,'o-',label='Primary'); ax.plot(range(1,len(rows)+1),hold,'s--',label='Hold-last diagnostic')
    ax.set(title='Load '+quantity,xlabel='Frozen validation question order',ylabel='Trajectory RMSE ('+unit+')'); ax.grid(alpha=.2); ax.legend(fontsize=8)
fig.suptitle('Eight held-out scenarios, one-second questions; diagnostic comparison only')
fig.tight_layout(); fig.savefig(OUT/'primary-hold-last-validation.png'); fig.savefig(OUT/'primary-hold-last-validation.svg'); plt.close(fig)
with (OUT/'learning-curves.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=['method','phase','kind','update','component','value']); writer.writeheader(); writer.writerows(csv_rows)
print(json.dumps({'figure_files':len(list(OUT.glob('*.png'))),'curve_rows':len(csv_rows)}))
