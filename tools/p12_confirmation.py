"""Freeze public-only confirmation inputs and outcome-independent capability masks."""
from p12_common import *
from collections import Counter
from phi_jepa.integration.readers import PublicInputReader
from phi_jepa.capabilities import capability

def main():
    cat=catalog();rows=load(OUT/'confirmation-cohort.json');by_id={r['sample_id']:r for r in rows};public=[];masks=[]
    for domain,split in sorted({(r['domain'],r['split']) for r in rows}):
        path=cat.verified_file(domain,split,'inputs.jsonl')
        for p in PublicInputReader(path,file_hash(path)):
            if p.sample_id not in by_id:continue
            public.append(by_id[p.sample_id]|{'public':{'sample_id':p.sample_id,'schema_version':p.schema_version,'input':p.input}})
            masks.extend({'sample_id':p.sample_id,'target_id':t['target_id'],'common_supported':capability(domain,t['entity_id'],t['quantity'])['implemented']}
                         for t in p.input['answer_spec'])
    save(OUT/'confirmation-public.json',public);save(OUT/'common-target-manifest.json',masks)
    note_ids={p.stem for p in NATIVE.glob('**/enrichment/*.json')}
    potential=[r['sample_id'] for r in rows if r['sample_id'] in note_ids]
    report={'questions':len(rows),'scenarios':len({r['scenario_id'] for r in rows}),'domain_distribution_questions':dict(Counter(r['domain']+'/'+r['split'] for r in rows)),
            'existing_enrichment_candidates':len(potential),'candidate_sample_ids':potential,'missing_enrichment':len(rows)-len(potential),
            'common_targets':sum(r['common_supported'] for r in masks),'all_targets':len(masks),
            'test_reference_outcomes_opened':False,'public_sha256':file_hash(OUT/'confirmation-public.json')}
    save(OUT/'confirmation-summary.json',report);print(report)

if __name__=='__main__':main()
