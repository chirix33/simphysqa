"""Static measured learning curves; objectives stay in separate panels."""
from p11_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict

def plots():
    out=OUT/'figures';out.mkdir(exist_ok=True);domains=list(load(OUT/'plan.json')['cohorts'])
    fig,axes=plt.subplots(2,4,figsize=(16,7),constrained_layout=True)
    for i,cohort in enumerate(('main','appendix')):
        for j,domain in enumerate(domains):
            path=StudyRun(domain,cohort).root/'numerical/phi_jepa/history.json';ax=axes[i,j]
            if path.exists():
                rows=load(path);chunks=[rows[k:k+100] for k in range(0,len(rows),100)];ax.plot([c[-1]['update'] for c in chunks],[sum(r['loss'] for r in c)/len(c) for c in chunks]);ax.set_yscale('log')
            ax.set_title(cohort+' / '+domain.replace('_',' '));ax.set_xlabel('Optimizer updates');ax.set_ylabel('Raw full-2d MSE (100-update mean)');ax.grid(alpha=.2)
    fig.savefig(out/'numerical_learning.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,4),constrained_layout=True)
    for ax,short in zip(axes,('coconut','codi')):
        path=OUT/'custom'/short/'history.json'
        if path.exists():
            rows=load(path);keys=[k for k in rows[0] if any(x in k for x in ('loss','ce','distill','smooth','alignment')) and isinstance(rows[0][k],(int,float))]
            for k in keys:ax.plot([r['update'] for r in rows],[r[k] for r in rows],label=k if k=='loss' else k+' (raw)',alpha=.8)
            ax.axvline(64,color='black',ls=':',label='pass boundary')
        ax.set_title('Custom '+short+' (own objective)');ax.set_xlabel('Optimizer updates');ax.set_ylabel('Loss component');ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.savefig(out/'custom_learning.png',dpi=160);plt.close(fig)

if __name__=='__main__':plots()
