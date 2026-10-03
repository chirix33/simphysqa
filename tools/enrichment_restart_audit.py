"""Read-only crash recovery inventory; never dispatches a provider request."""
from enrichment_run_control import *

def main():
    audit={'at_utc':now(),'files':{},'collections':{}}
    for name in ('spend-ledger.json','status.json','supervisor-status.json','supervisor-budget.json','approved-config.json'):
        path=RUN/name
        try:
            value=load(path)
            info={'sha256':file_hash(path),'bytes':path.stat().st_size}
            if name=='spend-ledger.json':
                rows=value['attempts'];info.update(attempts=len(rows),statuses=dict(Counter(r['status'] for r in rows)),
                    charged_usd=sum(r['charged_nano_usd'] for r in rows)/1e9,stopped=value['stopped'],last_rows=rows[-3:])
            elif name!='approved-config.json':info['value']=value
            audit['files'][name]=info
        except Exception as exc:audit['files'][name]={'failure':type(exc).__name__+': '+str(exc)}
    for folder in ('results','responses','context_cache','enrichment','provider_ledgers'):
        bad=[];valid=[]
        for path in (RUN/folder).glob('*.json'):
            try:value=load(path);valid.append(path.stem)
            except Exception as exc:bad.append({'name':path.name,'bytes':path.stat().st_size,'failure':type(exc).__name__})
        audit['collections'][folder]={'valid':len(valid),'invalid':bad,'valid_ids':valid}
    audit['orphan_provider_ledgers']={p.stem:load(p) for p in (RUN/'provider_ledgers').glob('*.json') if not (RUN/'results'/p.name).exists()}
    dest=ROOT/'docs/reviews/artifacts/P12_enrichment_full'/('restart-audit-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json');atomic_json(dest,audit)
    print(json.dumps({**audit,'collections':{k:{x:y for x,y in v.items() if x!='valid_ids'} for k,v in audit['collections'].items()}},indent=2))

if __name__=='__main__':main()
