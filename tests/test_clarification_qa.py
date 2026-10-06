"""Saved-data/contract checks, not empirical answering or human assessment."""
from copy import deepcopy
from pathlib import Path
from collections import Counter
import os, unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from simphysqa.io import ROOT, canonical, digest, read, parse
from simphysqa.dataset import load, validate, restore, public_record, pointer
from simphysqa.clarification import disjoint, roots, completed_view, erase_resolution, VERSION
from simphysqa.clarification_evaluation import inspect_stage1, route_reply, continuation, check_stage2, score_interactions
from simphysqa.associations import strip_associations, validate_view as validate_associations
from simphysqa.evaluation import request
from simphysqa.scoring import score, distance
from simphysqa.spq01a import verify_manifest, retained


class ClarificationQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('SIMPHYSQA_CLARIFICATION_EXPORT')
        if not path:raise unittest.SkipTest('set SIMPHYSQA_CLARIFICATION_EXPORT to saved SPQ04 export')
        cls.root=Path(path);cls.records=list(load(cls.root/'organizer-private/qa-records.jsonl'))
        cls.conditions=read(ROOT/'configs/simphysqa/evaluation.json')['conditions']
        cls.plan=read(os.environ['SIMPHYSQA_SPQ02_PLAN'])

    def test_counts_frozen_groups_all_prior_families_and_exclusions(self):
        self.assertEqual(len(self.records),8)
        self.assertEqual(Counter(r['public']['input']['domain'] for r in self.records),{d:2 for d in ('robotic_arm','driving','object_pushing_stacking','tethered_load')})
        self.assertEqual({r['trajectory_id'] for r in self.records},{p['scenario']['group'] for p in self.plan['pairs']})
        index=read(self.root/'item-index.json');self.assertEqual(len(index['accepted_items']),48)
        self.assertEqual(Counter(v['question_type'] for v in index['accepted_items']),dict(direct=16,predictive=16,counterfactual=8,explanation=8))
        ex=read(ROOT/'configs/simphysqa/development_exclusions.json')['excluded_groups']
        for r in self.records:
            p=r['private']['clarification_evidence']['parent_record']
            self.assertEqual(canonical(restore(r)),canonical(restore(p)))
            self.assertEqual(r['source'],p['source']);self.assertEqual(r['private']['metadata'],p['private']['metadata'])
            self.assertIn(r['trajectory_id'],ex)
            self.assertEqual(r['public']['input']['observation_cutoff'],.2)
        self.assertFalse(index['formal_sample_exported']);self.assertFalse(index['ood_claim'])

    def test_acceptance_regions_not_just_one_tolerance(self):
        t=dict(answer_type='number',quantity='position',unit='m',frame='world',absolute_tolerance=.01,relative_tolerance=0.)
        self.assertFalse(disjoint(0.,.015,t,t)['qualified'])
        self.assertFalse(disjoint(0.,.02,t,t)['qualified'])
        self.assertTrue(disjoint(0.,.020001,t,t)['qualified'])
        self.assertTrue(distance(.0075,0.,t)[1]);self.assertTrue(distance(.0075,.015,t)[1])
        t['relative_tolerance']=.1
        self.assertFalse(disjoint(1.,1.15,t,t)['qualified'])
        b={**t,'answer_type':'boolean','relative_tolerance':0.,'absolute_tolerance':0.}
        self.assertFalse(disjoint(True,True,b,b)['qualified']);self.assertTrue(disjoint(True,False,b,b)['qualified'])
        q={**t,'answer_type':'vector','quantity':'orientation','unit':'1','relative_tolerance':0.}
        self.assertFalse(disjoint([0.,0.,0.,1.],[0.,0.,0.,-1.],q,q)['qualified'])

    def test_real_witnesses_strict_and_rejected_candidates_retained(self):
        types=Counter()
        for r in self.records:
            sel=r['private']['clarification_evidence']['selection'];w=r['private']['reference']['witnesses'];types[sel['ambiguity_type']]+=1
            c=disjoint(w[0]['answer']['value'],w[1]['answer']['value'],w[0]['target'],w[1]['target'])
            self.assertTrue(c['qualified']);self.assertEqual(c,sel['certificate'])
            if c['separation'] is not None:self.assertGreater(c['separation'],sum(c['radii']))
            if sel['ambiguity_type']=='readout_time':
                self.assertTrue(all(not v['certificate']['qualified'] for v in sel['candidates'][:-1]))
                self.assertEqual(sel['completion_values'],[.4,1.])
            if sel['ambiguity_type']=='entity_id':
                self.assertTrue(all(not v['certificate']['qualified'] for v in sel['candidates'][:-1]))
                self.assertEqual(sel['completion_values'],['block_1','block_2'])
        self.assertEqual(types,dict(execution_condition=5,entity_id=1,readout_time=2))

    def test_entire_visible_projection_agrees_with_both_completions(self):
        for r in self.records:
            initial=public_record(r);sel=r['private']['clarification_evidence']['selection']
            self.assertNotIn('answer_spec',initial['input']);self.assertNotIn('recorded_reply',initial['input'])
            self.assertEqual(initial['input']['query']['target_id'],'clarified-target')
            for i in (0,1):
                full=completed_view(initial,sel,i)
                self.assertEqual(canonical(erase_resolution(full,sel['ambiguity_type'])),canonical(initial))
                raw=deepcopy(full);raw.pop('export_version');raw.pop('association_provenance');raw['input']=strip_associations(full['input'])
                validate_associations(raw,full)
            raw=deepcopy(initial);raw.pop('export_version');raw.pop('association_provenance');raw['input']=strip_associations(initial['input'])
            validate_associations(raw,initial)
            self.assertEqual(initial['annotations'],r['private']['clarification_evidence']['parent_record']['public']['annotations'])

    def test_claim_trace_and_witness_evidence_resolution(self):
        for r in self.records:
            root=roots(r);ref=r['private']['reference'];ids={v['claim_id'] for v in ref['claims']};supported=set()
            for item in ref['claims']+ref['solution_trace']['steps']+[ref['verification_record']]:
                self.assertTrue(item['bindings'])
                supported.update(item.get('supports_claim_ids',[]))
                for b in item['bindings']:self.assertEqual(digest(pointer(root[b['namespace']],b['pointer'])),b['value_sha256'])
            self.assertEqual(supported,ids)
            for w in ref['witnesses']:
                self.assertTrue(all(v['run_id']==w['run_id'] for v in w['bindings']))
            self.assertEqual(ref['reference_question_origin'],'authored_reference_not_executed_model_response')
            self.assertEqual(ref['verification_record']['human_explanation_assessment'],'uncollected')
            if ref['structured_label'][0]['quantity']=='stopped_by_T':
                c=next(c for c in ref['claims'] if c['kind']=='predicate_rule')
                self.assertTrue(any(b['pointer']=='/reference/events' for b in c['bindings']))

    def test_extra_time_saved_readout_refinement_is_separate_from_scorer(self):
        for r in self.records:
            e=r['private']['clarification_evidence']
            if e['selection']['ambiguity_type']!='readout_time':continue
            self.assertEqual(len(e['additional_readout_checks']),2)
            for c in e['additional_readout_checks']:
                self.assertTrue(c['passed']);self.assertLessEqual(c['error'],.005)
                self.assertEqual(c['tolerance'],.005);self.assertEqual(c['target']['absolute_tolerance'],.01)
                self.assertEqual(c['result_file_sha256'],e['parent_record']['private']['answer_annotation']['evidence_context']['runs']['original-fine']['result_file_sha256'])

    def test_leaks_or_tampered_resolution_answer_or_receipt_rejected(self):
        base=self.records[0]
        for part in ('query','language','controller','association','answer','reply','binding','cutoff','identity','schema'):
            r=deepcopy(base)
            if part=='query':r['public']['input']['query']['execution_condition']='omitted'
            elif part=='language':r['public']['annotations']['trajectory']['text']+=' Answer is 99.'
            elif part=='controller':r['public']['input']['controller']['description']='Omission was selected.'
            elif part=='association':r['public']['input']['known_events'][0]['event_description']='Omission selected.'
            elif part=='answer':r['private']['reference']['structured_label'][0]['value']=99
            elif part=='reply':r['private']['resolved_view']['input']['recorded_reply']['value']='scheduled'
            elif part=='binding':r['private']['reference']['claims'][0]['bindings'][0]['pointer']='/query/999'
            elif part=='cutoff':r['public']['input']['observation_cutoff']=1.
            elif part=='identity':r['sample_id']='spq-clarification-'+'f'*24
            else:r['public']['input']['interaction']['response_schema']['properties']['answer']={'const':99}
            with self.assertRaises((ValueError,KeyError,IndexError,ValidationError)):validate(r)

    def test_equivalent_wording_routes_no_exact_reference_matching(self):
        for r in self.records:
            slot=r['private']['clarification_evidence']['selection']['ambiguity_type']
            for q in ('Please specify the '+slot+'.','Which '+slot+' did you intend?'):
                response=dict(response_kind='clarify',requested_information=slot,clarification_question=q)
                routed=route_reply(r,response);self.assertEqual(routed['status'],'recorded_reply_routed')
                req=continuation(r,self.conditions[0],response)
                self.assertEqual(parse(req['messages'][1]['content']),response);self.assertEqual(req['tools'],[])
            wrong=dict(response_kind='clarify',requested_information=next(s for s in ('execution_condition','entity_id','readout_time') if s!=slot),clarification_question='Which one?')
            self.assertEqual(route_reply(r,wrong)['status'],'unroutable')
            premature={**response,'answer':1.}
            self.assertTrue(inspect_stage1(r,premature)['premature_structured_answer'])
            self.assertEqual(route_reply(r,premature)['status'],'unroutable')

    def test_post_reply_scoring_denominators_and_prose_limits(self):
        predictions=[]
        for r in self.records:
            slot=r['private']['clarification_evidence']['selection']['ambiguity_type']
            stage1=dict(response_kind='clarify',requested_information=slot,clarification_question='Unassessed prose')
            truth=r['private']['reference']['structured_label'][0]
            stage2={'targets':[{k:truth[k] for k in ('target_id','value','unit','frame')}],'explanation':'Unassessed prose'}
            result=check_stage2(r,stage2);self.assertTrue(result['answer_correct_under_existing_typed_scorer'])
            self.assertEqual(result['answer_explanation_adequacy'],'human_judgment_uncollected')
            predictions.append(dict(condition_id=self.conditions[0]['condition_id'],sample_id=r['sample_id'],task_version=VERSION,annotation_version=r['annotation_version'],status='completed',stage1_response=stage1,reply=r['private']['resolved_view']['input']['recorded_reply'],stage2_response=stage2))
        result=score_interactions(self.records,predictions,[c['condition_id'] for c in self.conditions])
        self.assertEqual(len(result['items']),72);self.assertEqual(sum(v['status']=='missing' for v in result['items']),64)
        self.assertEqual(sum(v['stage2'] is not None for v in result['items']),8)
        with self.assertRaises(ValueError):score(self.records,[],[self.conditions[0]['condition_id']])

    def test_public_requests_templates_no_gold_or_fabricated_assistant_response(self):
        forbidden={'reference','solution_trace','verification_record','witnesses','clarification_evidence','supplied_comparison','annotation_provenance','source_record'}
        def scan(v):
            if isinstance(v,dict):
                self.assertFalse(set(v)&forbidden)
                for val in v.values():scan(val)
            elif isinstance(v,list):
                for val in v:scan(val)
        for c in self.conditions:
            initial=read(self.root/'public-requests'/(c['condition_id']+'.json'));templates=read(self.root/'continuation-templates'/(c['condition_id']+'.json'))
            self.assertEqual(len(initial),8);self.assertEqual(len(templates),8)
            for r,req,template in zip(self.records,initial,templates):
                self.assertEqual(req,request(r,c));self.assertEqual(req['tools'],[])
                view=parse(req['messages'][0]['content'].split('\n',1)[1]);scan(view)
                self.assertEqual(view,public_record(r));self.assertNotIn('assistant',[m['role'] for m in req['messages']])
                resolved=parse(template['conditional_continuation']['user_message']['content'].split('\n',1)[1]);scan(resolved)
                self.assertEqual(resolved,r['private']['resolved_view'])
                self.assertEqual(template['status'],'template_not_executed_interaction')
                self.assertNotIn(r['private']['reference']['reference_clarification_question'],canonical(template).decode())

    def test_blank_forms_and_immutable_resume_artifacts(self):
        verify_manifest(self.root)
        for r in self.records:retained(self.root/'organizer-private/items'/(r['sample_id']+'.json'),r)
        for reviewer in ('R1','R2','R3'):
            receipt=read(self.root/'verification'/(reviewer+'-blank-import.json'))
            self.assertEqual((receipt['collected'],receipt['blank']),(0,8))
        changed=deepcopy(self.records[0]);changed['completion']['clarification_qa']='altered'
        with self.assertRaises(ValueError):retained(self.root/'organizer-private/items'/(changed['sample_id']+'.json'),changed)

    def test_no_engine_or_network_calls_on_saved_validation(self):
        with patch('socket.create_connection',side_effect=AssertionError('network forbidden')),patch('subprocess.Popen',side_effect=AssertionError('execution forbidden')):
            for r in self.records:validate(r)

    def test_archive_historical_payloads_and_mappings_exact(self):
        path=os.environ.get('SIMPHYSQA_CLARIFICATION_ARCHIVE')
        if not path:self.skipTest('archive not configured')
        archive=Path(path);previous=archive.parent.parent/'spq03/prompt-archive-1.0.6'
        verify_manifest(archive);old=read(previous/'file-generation-index.json');new=read(archive/'file-generation-index.json')
        self.assertEqual(new['files'][:len(old['files'])],old['files']);self.assertEqual(new['requests'],old['requests'])
        for key,v in old['mapping_definitions'].items():self.assertEqual(new['mapping_definitions'][key],v)
        for req in old['requests']:self.assertEqual((previous/req['payload_file']).read_bytes(),(archive/req['payload_file']).read_bytes())
        for r in self.records:
            matches=[m for m in new['mapping_definitions'].values() if m.get('sample_id')==r['sample_id']]
            self.assertTrue(matches)
            for m in matches:
                if m.get('origin')!='deterministic_clarification_with_reused_observed_language':continue
                for f in m['field_generation']:
                    if f['field'].startswith(('trajectory','timestamps')):self.assertIsNotNone(f['complete_request'])
                    if f['procedure_id']=='clarification-qa/1.0.0':self.assertIn(r['private']['clarification_evidence']['parent_sample_id'],f['parent_artifact'])


if __name__=='__main__':unittest.main()
