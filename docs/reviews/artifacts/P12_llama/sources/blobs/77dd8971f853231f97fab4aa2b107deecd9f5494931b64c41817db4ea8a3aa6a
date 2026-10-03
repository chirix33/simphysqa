"""Measure preparation with the approved frozen encoder and existing notes only."""
from p12_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import PublicInputReader
import time
from dataclasses import asdict

def main():
    import torch
    from phi_jepa.providers.qwen import QwenEncoder
    from phi_jepa.providers.context import ContextEncoder
    torch.set_num_threads(2);cat=catalog();config=load(ROOT/'configs/model_context_p02b.json')['encoder']
    backend=QwenEncoder(str(NATIVE/'model-cache'),runtime_versions=config['runtime_versions']);enc=ContextEncoder(backend,None)
    coverage=load(OUT/'cache-coverage.json');results=[]
    for domain in sorted({r['domain'] for r in coverage}):
        available={r['sample_id']:r for r in coverage if r['domain']==domain and r['split']=='validation' and r['enrichment_path']}
        path=cat.verified_file(domain,'validation','inputs.jsonl')
        choices=[p for p in PublicInputReader(path,file_hash(path)) if p.sample_id in available]
        if not choices:results.append({'domain':domain,'status':'no_cached_validation_notes'});continue
        problem=max(choices,key=lambda p:len(p.input_json));row=available[problem.sample_id]
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();started=time.perf_counter()
        value=enc.encode(problem,problem.input['observation_cutoff'],mode='enriched',enrichment=load(row['enrichment_path']))
        torch.cuda.synchronize()
        result={'domain':domain,'sample_id':problem.sample_id,'status':'success','seconds':time.perf_counter()-started,
                'tokens':value.token_count,'request_sha256':value.request_sha256,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                'meaning':'fresh encoding of existing notes; no new enrichment; discarded output'}
        results.append(result);save(OUT/'context-profile.json',{'settings':asdict(backend.settings),'results':results,'paid_calls':0});print(result,flush=True)

if __name__=='__main__':main()
