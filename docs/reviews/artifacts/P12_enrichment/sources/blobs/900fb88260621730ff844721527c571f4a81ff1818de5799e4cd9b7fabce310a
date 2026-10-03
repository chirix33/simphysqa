"""Public-only confirmation context audit. Never creates enrichment or embeddings."""
from p12_common import *
from phi_jepa.integration.contracts import PublicProblem,validate_enrichment,enriched_context
from phi_jepa.providers.qwen import QwenEncoder
from dataclasses import asdict
from collections import defaultdict
import math

def main():
    encoder=QwenEncoder(str(NATIVE/'model-cache'),runtime_versions=load(ROOT/'configs/model_context_p02b.json')['encoder']['runtime_versions'],load_model=False)
    settings=asdict(encoder.settings);notes=defaultdict(list)
    for p in NATIVE.glob('**/enrichment/*.json'):notes[p.stem].append(p)
    roots=[p.parent for p in NATIVE.glob('**/encoding-report.json') if load(p)['settings']==settings]
    records=[]
    for row in load(OUT/'confirmation-public.json'):
        problem=PublicProblem.parse(row['public']);sid=problem.sample_id
        result={'sample_id':sid,'domain':row['domain'],'split':row['split'],'enrichment_path':None,'embedding_path':None,
                'embedding_request_sha256':None,'enrichment_file_sha256':None,'embedding_file_sha256':None}
        for path in notes[sid]:
            value=load(path)
            try:validate_enrichment(problem,value)
            except (ValueError,TypeError,KeyError):continue
            result.update(enrichment_path=str(path),enrichment_file_sha256=file_hash(path))
            context=enriched_context(problem,value,problem.input['observation_cutoff']);tokens=encoder.tokenize(context)
            request={'kind':'frozen_E','version':1,'settings':settings,'serialization':'P02a-Q-C-enrichment-v1',
                     'context_mode':'enriched','text':context,'tokens_sha256':digest(tokens)}
            for root in roots:
                candidate=root/'embeddings/enriched'/f'{sid}.json'
                if not candidate.exists():continue
                emb=load(candidate)
                if emb.get('request_sha256')!=digest(request) or emb.get('context_sha256')!=digest(context) or emb.get('token_count')!=len(tokens):continue
                if len(emb.get('values',[]))!=1024 or not all(type(v) in (int,float) and math.isfinite(v) for v in emb['values']):continue
                result.update(embedding_path=str(candidate),embedding_file_sha256=file_hash(candidate),embedding_request_sha256=digest(request));break
            if result['embedding_path']:break
        records.append(result)
    save(OUT/'confirmation-cache-coverage.json',records)
    print({'questions':len(records),'matching_notes':sum(r['enrichment_path'] is not None for r in records),'matching_embeddings':sum(r['embedding_path'] is not None for r in records)})

if __name__=='__main__':main()
