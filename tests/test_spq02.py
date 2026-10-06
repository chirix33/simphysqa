"""Offline engineering checks; supplied answers are test probes, never benchmarks."""
from copy import deepcopy
from pathlib import Path
import os,unittest
from jsonschema.exceptions import ValidationError
from simphysqa.io import read,digest,DOMAINS
from simphysqa.dataset import restore,load,validate,public_record
from simphysqa.counterfactual import public_input
from simphysqa.event_language import render,measurement_base
from simphysqa.associations import associated_view,strip_associations,validate_view
from simphysqa.evaluation import request
from simphysqa.scoring import score
from simphysqa.spq01a import verify_manifest

class PreparedOmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('SIMPHYSQA_SPQ02_PLAN')
        if not path:raise unittest.SkipTest('set SIMPHYSQA_SPQ02_PLAN to the frozen existing-development plan')
        cls.plan=read(Path(path));cls.pairs=cls.plan['pairs']

    def test_frozen_groups_seed_and_existing_exclusions(self):
        self.assertEqual(self.plan['sampling_seed'],20261004)
        self.assertEqual(len({p['scenario']['group'] for p in self.pairs}),8)
        self.assertEqual([p['scenario']['domain'] for p in self.pairs],list(DOMAINS)*2)
        selection=read(Path(os.environ['SIMPHYSQA_SPQ02_PLAN']).parent/'selection-manifest.json')
        self.assertEqual(selection['plan_sha256'],digest(self.plan))
        self.assertTrue({p['scenario']['group'] for p in self.pairs}<=set(selection['future_formal_excluded_groups']))
        self.assertEqual(len(selection['future_formal_excluded_groups']),20)
        self.assertFalse(selection['formal_sample_exported'])
        self.assertEqual({p['scenario']['subfamily'] for p in self.pairs if p['scenario']['domain']=='object_pushing_stacking'},{'pushing','pre_stacked'})

    def test_public_omission_is_explicit_and_prefix_exact(self):
        for p in self.pairs:
            source=restore(p['source_wrapper']);target=source['input']['answer_spec'][0]
            inp=public_input(source,p['pair_id'],target)
            self.assertEqual(inp['states'],source['input']['states'])
            self.assertEqual(inp['observation_cutoff'],.2)
            self.assertEqual(inp['known_events'],source['input']['known_events'])
            self.assertEqual(inp['counterfactual']['omitted_event_ids'],[inp['known_events'][0]['event_id']])
            self.assertNotEqual(inp['question'],source['input']['question'])
            self.assertEqual(inp['answer_spec'],[target])
            self.assertGreater(target['end_time'],inp['known_events'][0]['start_time'])

    def test_private_outcomes_not_accessed_for_public_projection(self):
        for p in self.pairs:
            source=restore(p['source_wrapper']);target=source['input']['answer_spec'][0]
            expected=public_input(source,p['pair_id'],target)
            source['reference']={'PRIVATE_SENTINEL':'future states/events must never be read'}
            self.assertEqual(public_input(source,p['pair_id'],target),expected)

    def test_missing_or_wrong_event_target_rejected(self):
        p=self.pairs[0];source=restore(p['source_wrapper']);target=deepcopy(source['input']['answer_spec'][0])
        source['input']['known_events']=[]
        with self.assertRaises(ValueError):public_input(source,p['pair_id'],target)
        source=restore(p['source_wrapper']);target['end_time']=.2
        with self.assertRaises(ValueError):public_input(source,p['pair_id'],target)
        target=deepcopy(source['input']['answer_spec'][0]);target['frame']='invented-frame'
        with self.assertRaises(ValueError):public_input(source,p['pair_id'],target)

    def test_no_relabeling_without_paired_evidence(self):
        for p in self.pairs:
            item=deepcopy(p['source_wrapper']);item['question_type']='counterfactual'
            with self.assertRaises(ValueError):validate(item)

    def test_accepted_associations_on_new_public_task(self):
        for p in self.pairs:
            parent=p['source_wrapper'];source=restore(parent)
            inp=public_input(source,p['pair_id'],source['input']['answer_spec'][0])
            annotations=render(inp,measurement_base(parent['public']['annotations']))
            base={'schema_version':'simphysqa/0.3.0','question_type':'counterfactual','sample_id':'software-projection-test-only',
                  'annotation_version':parent['annotation_version'],'input':inp,'annotations':annotations}
            view=associated_view(base)
            validate_view(base,view)
            self.assertEqual(strip_associations(view['input']),base['input'])
            self.assertEqual({l['temporal_relationship'] for l in annotations['event_context']['links']['state_links']},{'scheduled_future'})

class VerifiedCounterfactualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('SIMPHYSQA_COUNTERFACTUAL_QA')
        if not path:raise unittest.SkipTest('counterfactual simulations/exports not yet qualified; no automatic fixture substitution')
        cls.records=list(load(Path(path)))
        if not cls.records:raise unittest.SkipTest('no qualified counterfactual records exported; inspect retained failures')

    def test_exact_parent_restore_and_private_answer_readout(self):
        for r in self.records:
            source=restore(r);proof=r['private']['counterfactual_evidence'];target=r['public']['input']['answer_spec'][0]
            self.assertEqual(digest(source),r['source']['record_sha256'])
            self.assertEqual(r['trajectory_id'],source['metadata']['base_scenario_id'])
            self.assertEqual(r['public']['input']['states'],source['input']['states'])
            truth=next(x for x in proof['alternative_record']['reference']['structured_label'] if x['target_id']==target['target_id'])
            self.assertEqual(r['private']['reference']['structured_label'],[truth])
            self.assertEqual(r['private']['evidence_bindings'][0]['alternative_run_id'],proof['alternative_run_id'])

    def test_public_models_cannot_open_paired_evidence(self):
        for r in self.records:
            view=public_record(r,association_version='simphysqa-associations/1.1.1')
            self.assertNotIn('private',view);self.assertNotIn('reference',view)
            self.assertNotIn('counterfactual_evidence',view)
            msg=request(r,{'condition_id':'software-only','reasoning':'direct'},association_version='simphysqa-associations/1.1.1')
            self.assertEqual(msg['tools'],[])
            self.assertNotIn('alternative_record',msg['messages'][0]['content'])

    def test_mutated_answer_world_unit_and_cutoff_rejected(self):
        paths=[('public','input','observation_cutoff'),('private','evidence_bindings',0,'alternative_run_id'),
               ('public','input','answer_spec',0,'frame'),('private','reference','structured_label',0,'unit')]
        for r in self.records:
            for path in paths:
                changed=deepcopy(r);node=changed
                for part in path[:-1]:node=node[part]
                node[path[-1]]=.22 if path[-1]=='observation_cutoff' else 'WRONG'
                with self.assertRaises((ValueError,ValidationError)):validate(changed)
            changed=deepcopy(r);changed['private']['counterfactual_evidence']['verification']['replay']['passed']=False
            with self.assertRaises(ValueError):validate(changed)
            changed=deepcopy(r);changed['private']['counterfactual_evidence']['simulation_artifacts'].pop('alternative-fine')
            with self.assertRaises(ValidationError):validate(changed)

    def test_scoring_missing_invalid_and_exact_software_probes(self):
        # These supplied answers test scorer behavior; no answering model is invoked.
        probes=[]
        for r in self.records:
            truth=deepcopy(r['private']['reference']['structured_label'])
            probes.append({'sample_id':r['sample_id'],'condition_id':'software-test','annotation_version':r['annotation_version'],
                           'status':'completed','targets':truth})
        exact=score(self.records,probes,['software-test'])
        self.assertTrue(all(i['whole_question_correct'] for i in exact['items']))
        self.assertTrue(all(i['status']=='missing' and not i['whole_question_correct'] for i in score(self.records,[],['software-test'])['items']))
        for probe in probes:probe['targets'][0]['frame']='incorrect-frame'
        self.assertTrue(all(i['valid_targets']==0 for i in score(self.records,probes,['software-test'])['items']))

if __name__=='__main__':unittest.main()
