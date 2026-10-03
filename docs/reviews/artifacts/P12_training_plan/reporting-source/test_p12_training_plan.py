"""Offline manifest-binding, authorization and conservative resume checks."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p12_training_plan as planning
from p12_common import save,load,digest,file_hash
from p12_train import execution_window,check_resume_boundary,train


class TrainingPlanTests(unittest.TestCase):
    def test_obsolete_proposals_cannot_activate_training_or_resolve_inputs(self):
        with self.assertRaisesRegex(ValueError,'obsolete'):
            planning.bound_path({'enabled':True},'cache_coverage')
        with self.assertRaisesRegex(ValueError,'authorization'):
            train({'enabled':True,'authorization':'old permission'},'driving')

    def test_explicit_manifest_path_and_checksum_are_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'complete.json';save(path,{'scope':'complete'})
            plan={'plan_version':planning.VERSION,'inputs':{'cache_coverage':planning.descriptor(path)}}
            self.assertEqual(planning.bound_path(plan,'cache_coverage'),path)
            save(path,{'scope':'changed'})
            with self.assertRaisesRegex(ValueError,'changed'):planning.bound_path(plan,'cache_coverage')

    def test_training_approval_binds_prepared_settings_and_keeps_evaluation_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'plan.json'
            base={'plan_version':planning.VERSION,'enabled':False,'evaluation_enabled':False,
                  'training_enabled':False,'training_authorization':None,'authorized_proposal_sha256':None,'batch':256}
            save(path,base)
            approved={**base,'training_enabled':True,'training_authorization':'fixture only','authorized_proposal_sha256':file_hash(path)}
            with patch.object(planning,'PLAN_PATH',path):
                planning.require_training_authorization(approved)
                for change in ({'batch':512},{'evaluation_enabled':True},{'enabled':True},{'authorized_proposal_sha256':'stale'}):
                    with self.assertRaises(ValueError):planning.require_training_authorization({**approved,**change})

    def test_complete_coverage_requires_every_record_and_unchanged_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);public={'public':'fixture'}
            notes=root/'notes.json';vector=root/'vector.json';origin=root/'origin.json'
            save(notes,{'public_input':public,'notes':[]});save(origin,{'fixture':True})
            save(vector,{'request_sha256':'request','context_sha256':'context','token_count':9,'values':[1.]+[0.]*1023})
            row={'sample_id':'a','domain':'driving','split':'train','scenario_id':'a','split_group':'a','public_sha256':digest(public)}
            provenance={'sample_id':'a','domain':'driving','split':'train','status':'verified',
                        'cache_file':str(origin),'cache_sha256':file_hash(origin),'request_sha256':'notes-request'}
            coverage={**row,'embedding_path':str(vector),'embedding_file_sha256':file_hash(vector),
                      'enrichment_path':str(notes),'enrichment_file_sha256':file_hash(notes),'context_sha256':'context',
                      'embedding_request_sha256':'request','token_count':9,'compatible_origin':provenance}
            self.assertTrue(planning.coverage_check([row],[coverage],[provenance])['ready'])
            with self.assertRaisesRegex(ValueError,'size'):planning.coverage_check([row],[],[provenance])
            swapped={**coverage,'split':'validation'}
            with self.assertRaisesRegex(ValueError,'binding'):planning.coverage_check([row],[swapped],[provenance])
            save(vector,{'tampered':True})
            result=planning.coverage_check([row],[coverage],[provenance])
            self.assertFalse(result['ready']);self.assertEqual(len(result['integrity_failures']),1)

    def test_scenario_groups_stay_together_across_scopes(self):
        rows=[];confirmation=[]
        for domain,(scenarios,questions,_,validation) in planning.EXPECTED.items():
            for split,count in (('train',questions),('validation',validation)):
                for i in range(count):
                    group=f'{domain}/{split}/{i % scenarios}'
                    rows.append({'sample_id':f'{domain}/{split}/q{i}','scenario_id':group,'split_group':group,'domain':domain,'split':split})
            n=80 if domain=='driving' else 140
            for i in range(n):
                group=f'{domain}/test/{i % 80}'
                confirmation.append({'sample_id':f'{domain}/test/q{i}','scenario_id':group,'split_group':group,'domain':domain,'split':'test_id'})
        planning.validate_selection(rows,confirmation)
        confirmation[0]['split_group']=rows[0]['split_group']
        with self.assertRaisesRegex(ValueError,'leakage'):planning.validate_selection(rows,confirmation)

    def test_domain_window_is_persisted_and_not_renewed_on_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan={'domains':{'driving':{'wall_seconds_cap':100}}}
            with patch('p12_train.time.time',return_value=100):self.assertEqual(execution_window(root,plan,'driving'),200)
            with patch('p12_train.time.time',return_value=150):self.assertEqual(execution_window(root,plan,'driving'),200)
            with patch('p12_train.time.time',return_value=201):
                with self.assertRaisesRegex(TimeoutError,'expired'):execution_window(root,plan,'driving')
            with self.assertRaisesRegex(ValueError,'plan changed'):execution_window(root,{**plan,'new':'budget'},'driving')

    def test_resume_refuses_unaccounted_updates_and_incomplete_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);check_resume_boundary(root,0,[10])
            save(root/'last-update-attempt.json',{'status':'reserved','update':1})
            with self.assertRaisesRegex(ValueError,'unresolved'):check_resume_boundary(root,0,[10])
            save(root/'last-update-attempt.json',{'status':'success','update':10})
            (root/'history.jsonl').write_text(''.join('{"update":'+str(i)+'}\n' for i in range(1,10)))
            with self.assertRaisesRegex(ValueError,'uncheckpointed'):check_resume_boundary(root,9,[10])
            (root/'history.jsonl').write_text(''.join('{"update":'+str(i)+'}\n' for i in range(1,11)))
            with self.assertRaisesRegex(ValueError,'validation'):check_resume_boundary(root,10,[10])
            save(root/'validation/10.json',{'score':1})
            check_resume_boundary(root,10,[10])
            save(root/'validation-inflight.json',{'update':10})
            with self.assertRaisesRegex(ValueError,'validation'):check_resume_boundary(root,10,[10])

    def test_numerical_source_identity_excludes_answer_diagnostic_changes(self):
        paths=planning.training_sources()
        self.assertIn('src/phi_jepa/training/pairs.py',paths)
        self.assertIn('src/phi_jepa/typed_evaluation.py',paths)
        self.assertNotIn('tools/p12_answer_interface.py',paths)
        self.assertNotIn('src/phi_jepa/providers/compact_answer.py',paths)
        self.assertNotIn('src/phi_jepa/providers/local_answer.py',paths)


if __name__=='__main__':unittest.main()
