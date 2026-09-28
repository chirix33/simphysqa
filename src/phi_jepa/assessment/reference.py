"""Training-prediction-only, content-addressed reference bank and exact retrieval."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import reject_private


def norm(values):
    if not values or any(type(v) not in (int,float) or not math.isfinite(v) for v in values): return None
    n=math.hypot(*values)
    return n if math.isfinite(n) and n>0 else None


def cosine(a,b):
    na,nb=norm(a),norm(b)
    if na is None or nb is None or len(a)!=len(b): return None
    return max(-1.,min(1.,sum((x/na)*(y/nb) for x,y in zip(a,b))))


def block_diagnostics(layout, query, reference):
    nq,nr=norm(query),norm(reference)
    if nq is None or nr is None or len(query)!=2*layout.d or len(reference)!=2*layout.d: return None
    groups={'dynamic_numerical':[],'fixed_conditioning':[],'contextual':list(range(layout.d,2*layout.d))}
    for i,(path,_) in enumerate(layout.entries):
        groups['fixed_conditioning' if path[0]==('key','fixed_conditioning') else 'dynamic_numerical'].append(i)
    result={}
    for name,indices in groups.items():
        q=[query[i] for i in indices]; r=[reference[i] for i in indices]
        dot=sum((x/nq)*(y/nr) for x,y in zip(q,r))
        # Additive decomposition of half squared distance between normalized full
        # vectors, exactly summing to 1-cosine. This does not reweight blocks.
        contribution=.5*sum((x/nq-y/nr)**2 for x,y in zip(q,r))
        result[name]={'width':len(indices),'query_norm':math.hypot(*q),'reference_norm':math.hypot(*r),
            'cosine_numerator_contribution':dot,'familiarity_contribution':contribution,'block_cosine_diagnostic':cosine(q,r)}
    return result


@dataclass(frozen=True)
class ReferenceBank:
    json_data: str

    @classmethod
    def build(cls, identity, rows):
        required={'checkpoint_sha256','encoder_sha256','projection_sha256','solver_sha256','layout_sha256','profile_sha256'}
        if set(identity)!=required or any(not isinstance(v,str) or not v for v in identity.values()): raise ValueError('bank_identity')
        ids=set()
        for row in rows:
            reject_private(row)
            if row['split']!='train' or row['origin']!='autonomous_prediction': raise ValueError('training_predictions_only')
            if row['sample_id'] in ids: raise ValueError('duplicate_reference')
            ids.add(row['sample_id'])
            if row['layout_sha256']!=identity['layout_sha256']: raise ValueError('reference_layout')
            if not row['scenario_id'] or len(row['times'])!=len(row['trajectory']) or not row['times'] or any(b<=a for a,b in zip(row['times'],row['times'][1:])):
                raise ValueError('reference_grid')
            if row['times'][-1]<=row['cutoff'] or row['times'][0]<=row['cutoff']: raise ValueError('reference_horizon')
            width=len(row['trajectory'][0])
            if width<=0 or width%2 or any(len(v)!=width for v in row['trajectory']): raise ValueError('reference_width')
        return cls(canonical({'version':'development_r1_v1_full_2d_v1','identity':identity,'rows':rows}).decode())

    @property
    def data(self): return json.loads(self.json_data)

    @property
    def sha256(self): return digest(self.data)

    def write(self, directory):
        directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
        path=directory/(self.sha256+'.json')
        if path.exists():
            if path.read_text()!=self.json_data: raise ValueError('bank_collision')
        else:
            with path.open('x',encoding='utf-8',newline='') as stream: stream.write(self.json_data)
        return path

    @classmethod
    def load(cls,path,*,identity):
        data=json.loads(Path(path).read_text())
        if data.get('version')!='development_r1_v1_full_2d_v1' or set(data)!={'version','identity','rows'}: raise ValueError('bank_version')
        bank=cls.build(data['identity'],data['rows'])
        if Path(path).stem!=bank.sha256 or data['identity']!=identity: raise ValueError('stale_or_corrupt_bank')
        return bank

    def assess(self, query, layout, *, identity):
        data=self.data
        if data['identity']!=identity or layout.sha256!=identity['layout_sha256']: raise ValueError('stale_bank_identity')
        unavailable=lambda reason,**extra: {'status':'unavailable','reason':reason,'score':None,'bank_sha256':self.sha256,**extra}
        if query.get('layout_sha256')!=layout.sha256: return unavailable('query_layout_mismatch')
        if query.get('origin')!='autonomous_prediction': return unavailable('query_not_autonomous')
        if norm(query['embedding']) is None: return unavailable('invalid_query_embedding')
        candidates=[]; rejected=[]
        for row in data['rows']:
            if (row['domain'],row['layout_sha256'],row['cutoff'],row['times'])!=(query['domain'],layout.sha256,query['cutoff'],query['times']): continue
            if query['split']=='train' and row['scenario_id']==query['scenario_id']: continue
            similarity=cosine(query['embedding'],row['embedding'])
            if similarity is None: rejected.append(row['sample_id']); continue
            candidates.append((-similarity,row['sample_id'],row))
        if not candidates: return unavailable('no_compatible_reference',invalid_embedding_references=rejected)
        _,_,selected=min(candidates,key=lambda x:(x[0],x[1]))
        terminal=query['trajectory'][-1] if query['trajectory'] else []
        ref=selected['trajectory'][-1]
        if len(query['trajectory'])!=len(query['times']) or any(len(v)!=2*layout.d or norm(v) is None for v in query['trajectory']): return unavailable('invalid_query_trajectory')
        if any(len(v)!=2*layout.d or norm(v) is None for v in selected['trajectory']): return unavailable('invalid_reference_trajectory',reference_id=selected['sample_id'])
        similarity=cosine(terminal,ref)
        return {'status':'available','reason':None,'score':1-similarity,'bank_sha256':self.sha256,
            'reference_id':selected['sample_id'],'reference_scenario_id':selected['scenario_id'],
            'retrieval_cosine':cosine(query['embedding'],selected['embedding']),
            'blocks':block_diagnostics(layout,terminal,ref),'meaning':'development_familiarity_not_physical_correctness_or_uncertainty'}
