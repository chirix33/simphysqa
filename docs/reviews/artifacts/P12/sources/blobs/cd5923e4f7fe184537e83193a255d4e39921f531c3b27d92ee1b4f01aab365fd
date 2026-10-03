"""Bounded public checkpoint acquisition; gated access failures remain failures."""
from p12_common import *
import time

def main():
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
    api=HfApi(); models=load(OUT/'model-acquisition.json') if (OUT/'model-acquisition.json').exists() else {}; started=time.time()
    if models:save(OUT/'acquisition-attempts'/f'{time.time_ns()}.json',models)
    for model in dict.fromkeys(c['model'] for c in CONFIG['models']):
        record={'model':model}
        try:
            pinned=models.get(model,{}).get('revision')
            if models.get(model,{}).get('status')=='available':continue
            info=api.model_info(model,revision=pinned,files_metadata=True,timeout=30)
            record.update(revision=info.sha,tokenizer_revision=info.sha)
            wanted=[f for f in info.siblings if f.rfilename.endswith(('.safetensors','.json','.jinja')) and '/' not in f.rfilename]
            size=sum(f.size or 0 for f in wanted)
            record['expected_bytes']=size
            if size>CONFIG['qualification']['download_bytes']: raise ValueError('checkpoint_download_byte_cap')
            # Probe actual gated file access before bulk download.
            hf_hub_download(model,'config.json',revision=info.sha,cache_dir=str(NATIVE/'model-cache'),etag_timeout=30)
            save(OUT/'model-acquisition.json',models|{model:record|{'status':'downloading'}})
            path=snapshot_download(model,revision=info.sha,cache_dir=str(NATIVE/'model-cache'),
                                   allow_patterns=[f.rfilename for f in wanted],max_workers=4,etag_timeout=30)
            record.update(status='available',snapshot=path,files={p.name:file_hash(p) for p in Path(path).iterdir() if p.is_file()})
        except Exception as exc:
            record.update(status='unavailable',failure_type=type(exc).__name__)
        models[model]=record;save(OUT/'model-acquisition.json',models)
        print(json.dumps({'model':model,'status':record['status'],'revision':record.get('revision'),'failure':record.get('failure_type')}),flush=True)
    save(OUT/'download-cost.json',{'seconds':time.time()-started,'paid_api_calls':0})

if __name__=='__main__':main()
