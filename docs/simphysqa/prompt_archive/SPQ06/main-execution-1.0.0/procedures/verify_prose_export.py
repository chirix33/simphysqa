"""Temporary-only offline form/provenance check; no model or ledger operations."""
import json,tempfile
from pathlib import Path
from finish_main import BASE,SHARDS,adapter,prose,read,sha
from simphysqa.model_prose_review import import_submission

def check():
    frozen=read(BASE/'main-preparation-1.0.0/model-prose-assessment-subset.json')
    records={adapter.stage_key(i['sample_id'],c,'enriched',1):{'raw_output':'OFFLINE FIXTURE — NOT MODEL EVIDENCE','completion_status':'fixture_only'}
             for i in frozen['items'] for c in frozen['conditions'] if c+'--enriched' in SHARDS}
    with tempfile.TemporaryDirectory(prefix='spq06-offline-prose-') as temp:
        output=Path(temp)/'mock-export';prose(records,output)
        index=read(output/'index.json')
        assert len(index['available_responses'])==48 and index['missing_planned_count']==24 and index['submitted_judgments']==0
        assert len(list((output/'packets').glob('*.json')))==48
        for name in ('assignments.json','private/condition-code-map.json','P1.csv','P2.csv'):
            assert sha(output/name)==sha(BASE/'model-prose-forms-1.0.0'/name)
        known={i['assessment_id'] for i in read(output/'assignments.json')['items']}
        assert all(i['assessment_id'] in known for i in index['available_responses'])
        assert all(read(p)['actual_returned_text']=='OFFLINE FIXTURE — NOT MODEL EVIDENCE' for p in (output/'packets').glob('*.json'))
        for assessor in ('P1','P2'):
            imported=Path(temp)/('fixture-blank-import-'+assessor)
            import_submission(output,output/(assessor+'.csv'),assessor,imported)
            receipts=list((imported/'imports').glob('*.json'))
            assert len(receipts)==1 and read(receipts[0])['collected']==0 and read(receipts[0])['missing']==72
    print(json.dumps({'scope':'offline temporary fixture only','passed':True,'available_mock_packets':48,'missing_mock_packets':24,'frozen_forms_and_codes_byte_equal':True,'answering_calls':0,'main_reservations':0,'fixture_artifacts_retained':False}))

if __name__=='__main__':check()
