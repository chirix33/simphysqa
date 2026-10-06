"""Grounded shared descriptions; boundary fixtures are synthetic software only."""
from copy import deepcopy
from decimal import Decimal, localcontext, ROUND_UP
import os
from pathlib import Path
import unittest
from jsonschema.exceptions import ValidationError
from simphysqa.associations import VERSION, _project, strip_associations, validate_input, validate_view
from simphysqa.dataset import load, pointer, public_record
from simphysqa.events import derive, POINTS
from simphysqa.event_descriptions import FIELDS, number, render
from simphysqa.io import canonical

class EventDescriptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=list(load(Path(os.environ['SIMPHYSQA_SPQ01A_ROOT'])/'qa-records.jsonl'))
        cls.domains={r['public']['input']['domain']:r for r in cls.records if r['question_type']=='predictive'}

    def fixture(self,domain='robotic_arm',start=.1,end=.2,times=(0.,.3)):
        inp=deepcopy(self.domains[domain]['public']['input'])
        state=inp['states'][0]
        inp['states']=[dict(deepcopy(state),state_id=f'SYNTHETIC-{j}',timestamp=t) for j,t in enumerate(times)]
        inp['observation_cutoff']=times[-1]
        inp['known_events'][0].update(event_id='SYNTHETIC-EVENT',start_time=start,end_time=end)
        links=derive(inp)
        return inp,links,_project(inp,links)

    def test_all_real_description_copies_evidence_and_exact_source_recovery(self):
        for r in self.records:
            original=deepcopy(r)
            view=public_record(r,association_version=VERSION)
            inp=r['public']['input']; indexed=view['input']
            self.assertEqual(canonical(strip_associations(indexed)),canonical(inp))
            self.assertEqual(r,original)
            event=indexed['known_events'][0]
            self.assertEqual(event['description'],inp['known_events'][0]['description'])
            expected=render(inp,r['public']['annotations']['event_context']['links']['events'][0],0)
            self.assertEqual({field:event[field] for field in FIELDS},expected)
            for binding in expected['event_description_bindings']:
                pointer(inp,binding)
                self.assertTrue(binding.startswith(('/known_events/','/controller/')))
                self.assertNotIn('/states/',binding)
            for state in indexed['states']:
                entry=state['linked_events'][0]
                self.assertEqual({field:entry[field] for field in FIELDS},expected)
                self.assertNotEqual(entry['bindings'],entry['event_description_bindings'])
            self.assertNotIn('not yet started',event['event_description'])
            self.assertNotIn('currently active',event['event_description'])
            validate_view(public_record(r),view)

    def test_all_four_domain_controller_distinctions(self):
        events={d:public_record(r,association_version=VERSION)['input']['known_events'][0] for d,r in self.domains.items()}
        arm=events['robotic_arm'];self.assertIn('additive torque pulse',arm['event_description'])
        self.assertIn('+0.5 N*m',arm['event_description']);self.assertIn('not total',arm['event_description'])
        self.assertIn('world',arm['event_description']);self.assertIn('joint_local',arm['event_description'])
        self.assertEqual(arm['event_description_status'],'limited_unresolved_semantics')
        drive=events['driving']['event_description'];self.assertIn('maximum torque limit 0.25 N*m',drive)
        self.assertIn('each axle',drive);self.assertIn('does not specify realized braking torque',drive)
        push=events['object_pushing_stacking']['event_description'];self.assertIn('direct target block_1',push)
        self.assertIn('instantaneous center of mass',push);self.assertIn('+x force',push);self.assertNotIn('target block_2',push)
        tether=events['tethered_load']['event_description'];self.assertIn('direct target support',tether)
        self.assertIn('positive phase: +',tether);self.assertIn('negative phase: -',tether)
        self.assertIn('stationary support afterward',tether);self.assertNotIn('target load',tether)

    def test_shared_renderer_requires_no_states_cutoff_private_or_context(self):
        for r in self.domains.values():
            inp=deepcopy(r['public']['input']);descriptor=r['public']['annotations']['event_context']['links']['events'][0]
            expected=render(inp,descriptor,0)
            for key in ('states','observation_cutoff','entities','question'):
                inp.pop(key,None)
            self.assertEqual(render(inp,descriptor,0),expected)

    def test_synthetic_gap_has_exact_description_copy_not_endpoint_status(self):
        inp,links,indexed=self.fixture()
        gap=indexed['between_state_associations'][0]
        event=indexed['known_events'][0]
        self.assertEqual({k:gap[k] for k in FIELDS},{k:event[k] for k in FIELDS})
        self.assertEqual(gap['endpoint_state_ids'],['SYNTHETIC-0','SYNTHETIC-1'])
        self.assertEqual(gap['temporal_relationship'],'interval_between_saved_states')
        validate_input(inp,links,indexed)

    def test_description_text_bindings_status_missing_and_consistent_forgery_rejected(self):
        inp,links,indexed=self.fixture()
        for location in ('event','state','gap'):
            for field,value in zip(FIELDS,('forged text',['/states/0/timestamp'],'supported_declared_semantics')):
                bad=deepcopy(indexed)
                target=bad['known_events'][0] if location=='event' else bad['states'][0]['linked_events'][0] if location=='state' else bad['between_state_associations'][0]
                target[field]=value
                with self.assertRaises((ValueError,ValidationError)):
                    validate_input(inp,links,bad)
            bad=deepcopy(indexed)
            target=bad['known_events'][0] if location=='event' else bad['states'][0]['linked_events'][0] if location=='state' else bad['between_state_associations'][0]
            del target['event_description_bindings']
            with self.assertRaises((ValueError,ValidationError)):
                validate_input(inp,links,bad)
        bad=deepcopy(indexed)
        entries=bad['known_events']+[e for s in bad['states'] for e in s['linked_events']]+bad['between_state_associations']
        for entry in entries:
            entry['event_description']='same forged description everywhere'
        with self.assertRaisesRegex(ValueError,'noncanonical event description'):
            validate_input(inp,links,bad)

    def test_unsupported_controller_and_event_semantics_remain_limited(self):
        inp,_,_=self.fixture()
        inp['controller']['equations']=['UNSUPPORTED_SYNTHETIC_LAW']
        links=derive(inp);indexed=_project(inp,links);event=indexed['known_events'][0]
        self.assertEqual(event['event_description_status'],'limited_unresolved_semantics')
        self.assertIn('action/application law is unresolved',event['event_description'])
        self.assertIn('/controller/equations',event['event_description_bindings'])
        self.assertIn('Declared parameter magnitude for joint_1: 0.5 N*m',event['event_description'])
        self.assertNotIn('additive torque pulse',event['event_description'])
        inp['known_events'][0]['type']='UNKNOWN_SYNTHETIC_EVENT'
        links=derive(inp);indexed=_project(inp,links)
        self.assertIn('Temporal and application semantics are unresolved',indexed['known_events'][0]['event_description'])
        self.assertEqual(indexed['states'][0]['linked_events'][0]['target_entity_ids'],[])
        validate_input(inp,links,indexed)

    def test_point_event_readout_semantics_no_intervention_target(self):
        for kind in POINTS:
            inp,_,_=self.fixture(start=.1,end=.1)
            inp['known_events'][0]['type']=kind
            links=derive(inp);indexed=_project(inp,links)
            text=indexed['known_events'][0]['event_description']
            self.assertIn(POINTS[kind],text)
            self.assertIn('no direct intervention target is assigned',text)
            self.assertEqual(indexed['states'][0]['linked_events'][0]['target_entity_ids'],[])
            validate_input(inp,links,indexed)

    def test_unresolved_parameter_frames_not_inferred(self):
        inp,_,_=self.fixture(domain='tethered_load',start=.1,end=.3)
        p=next(p for p in inp['controller']['parameters'] if p['name']=='acceleration')
        p['frame']='unresolved'
        links=derive(inp);indexed=_project(inp,links)
        self.assertEqual(indexed['known_events'][0]['event_description_status'],'limited_unresolved_semantics')
        self.assertIn('frame is unresolved',indexed['known_events'][0]['event_description'])
        self.assertIn('in unresolved',indexed['known_events'][0]['event_description'])

    def test_readable_display_rounding_is_not_temporal_matching(self):
        for value,expected in ((.5639000000000001,'0.5639'),(Decimal('1.234565'),'1.23456'),(Decimal('1.234575'),'1.23458'),(0,'0'),(-0.,'0'),(10000000,'1e7')):
            self.assertEqual(number(value),expected)
        with localcontext() as context:
            context.rounding=ROUND_UP
            self.assertEqual(number(Decimal('1.234565')),'1.23456')
        for value in (True,float('nan'),float('inf')):
            with self.assertRaises(ValueError):number(value)
        inp,links,indexed=self.fixture(start=.10000000000001,end=.2,times=(0.,.1,.3))
        self.assertIn('[0.1, 0.2)',indexed['known_events'][0]['event_description'])
        self.assertEqual(indexed['states'][1]['linked_events'][0]['temporal_relationship'],'scheduled_future')
        self.assertEqual(strip_associations(indexed)['known_events'][0]['start_time'],.10000000000001)

    def test_renderer_display_and_schema_versions_in_cache_identity(self):
        r=self.records[0];base=public_record(r);view=public_record(r,association_version=VERSION)
        for field in ('event_description_renderer_version','event_description_renderer_sha256','event_description_display_version','association_schema_sha256'):
            self.assertIn(field,view['association_provenance'])
            bad=deepcopy(view);bad['association_provenance'][field]='stale'
            with self.assertRaisesRegex(ValueError,'version/hash'):
                validate_view(base,bad)

if __name__=='__main__':unittest.main()
