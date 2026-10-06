"""Saved-data engineering tests; probes are not model or human results."""
from copy import deepcopy
from collections import Counter
from pathlib import Path
import os,unittest,json,tempfile
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from simphysqa.io import canonical,digest,read,ROOT
from simphysqa.dataset import load,validate,restore,public_record,pointer
from simphysqa.explanation import build,evidence_roots,validate_explanation
from simphysqa.explanation_evaluation import expected_facts,check_facts,score_facts
from simphysqa.evaluation import request
from simphysqa.scoring import score
from simphysqa.spq01a import verify_manifest,retained

class ExplanationQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=os.environ.get('SIMPHYSQA_EXPLANATION_EXPORT')
        if not root:raise unittest.SkipTest('set SIMPHYSQA_EXPLANATION_EXPORT to saved SPQ03 export')
        cls.root=Path(root);cls.records=list(load(cls.root/'organizer-private/qa-records.jsonl'))
        cls.plan=read(os.environ['SIMPHYSQA_SPQ02_PLAN'])
        cls.conditions=read(ROOT/'configs/simphysqa/evaluation.json')['conditions']

    def test_frozen_pairs_groups_splits_target_and_source_preservation(self):
        self.assertEqual(len(self.records),8)
        self.assertEqual(Counter(r['public']['input']['domain'] for r in self.records),{d:2 for d in ('robotic_arm','driving','object_pushing_stacking','tethered_load')})
        self.assertEqual({r['private']['explanation_evidence']['pair_id'] for r in self.records},{p['pair_id'] for p in self.plan['pairs']})
        exclusions=read(ROOT/'configs/simphysqa/development_exclusions.json')['excluded_groups']
        for r in self.records:
            parent=r['private']['explanation_evidence']['parent_record'];inp=r['public']['input']
            self.assertNotEqual(r['sample_id'],parent['sample_id'])
            self.assertEqual(r['question_type'],'explanation');self.assertEqual(r['trajectory_id'],parent['trajectory_id'])
            self.assertIn(r['trajectory_id'],exclusions)
            self.assertEqual(r['private']['metadata'],parent['private']['metadata'])
            self.assertEqual(inp['answer_spec'],parent['public']['input']['answer_spec'])
            self.assertEqual(canonical(restore(r)),canonical(restore(parent)))
            self.assertEqual(digest(parent),r['private']['explanation_evidence']['parent_record_sha256'])

    def test_task_specific_disclosure_not_observations_or_other_targets(self):
        for r in self.records:
            inp=r['public']['input'];parent=r['private']['explanation_evidence']['parent_record']
            self.assertEqual(canonical(inp['states']),canonical(parent['public']['input']['states']))
            self.assertEqual(inp['observation_cutoff'],.2)
            for k in ('controller','global_context','known_events','entities','coordinate_convention'):
                self.assertEqual(canonical(inp[k]),canonical(parent['public']['input'][k]))
            self.assertEqual(r['public']['annotations'],parent['public']['annotations'])
            s=inp['supplied_comparison'];t=inp['answer_spec'][0]
            self.assertEqual(s['timestamp'],t['end_time']);self.assertGreater(s['timestamp'],inp['observation_cutoff'])
            for k in ('entity_id','quantity','target_id','unit','frame'):self.assertEqual(s[k],t[k])
            self.assertEqual(set(s),{'version','disclosure','target_id','entity_id','quantity','unit','frame','timestamp','readouts'})
            self.assertEqual([x['condition'] for x in s['readouts']],['factual_scheduled','omission'])
            root=evidence_roots(r)
            for ns,entry in zip(('factual','alternative'),s['readouts']):
                state=next(x for x in root[ns]['reference']['states'] if x['timestamp']==t['end_time'])
                m=next(x for x in state['measurements'] if (x['entity_id'],x['name'])==(t['entity_id'],t['quantity']))
                self.assertEqual(canonical(entry['value']),canonical(m['value']))

    def test_questions_readable_unchanged_booleans_and_small_contrasts_retained(self):
        unchanged=small=0
        for r in self.records:
            inp=r['public']['input'];q=inp['question'];t=inp['answer_spec'][0];c=r['private']['reference']['comparison']
            self.assertIn('Explain',q);self.assertIn(t['entity_id'],q);self.assertIn(t['quantity'],q)
            self.assertIn('what stayed fixed',q);self.assertIn('remains undetermined',q)
            if t['answer_type']=='boolean' and c['exact_canonical_equality']:
                unchanged+=1;self.assertIn('unchanged predicate outcome',q)
            if t['answer_type']!='boolean' and not c['exact_canonical_equality'] and c['factual_answer_passes_alternative_scorer']:
                small+=1;self.assertIn('answer tolerance',q)
        self.assertEqual(unchanged,3);self.assertEqual(small,2)

    def test_every_claim_and_trace_binding_resolves_and_trace_supports_claim(self):
        for r in self.records:
            root=evidence_roots(r);ref=r['private']['reference'];claims=ref['claims']
            kinds={c['kind'] for c in claims}
            self.assertTrue({'declared_control','implemented_change','fixed_conditions','matched_outcome','supported_interpretation','remaining_uncertainty'}<=kinds)
            self.assertEqual(ref['explanation'],' '.join(c['text'] for c in claims))
            ids={c['claim_id'] for c in claims};covered=set()
            for item in claims+ref['solution_trace']['steps']:
                self.assertTrue(item['bindings'])
                for b in item['bindings']:self.assertEqual(b['value_sha256'],digest(pointer(root[b['namespace']],b['pointer'])))
                covered.update(item.get('supports_claim_ids',[]))
            self.assertEqual(covered,ids)
            outcome=next(c for c in claims if c['kind']=='matched_outcome')
            self.assertTrue({'factual','alternative','public'}<={b['namespace'] for b in outcome['bindings']})
            for b in outcome['bindings']:
                if b['namespace'] in ('factual','alternative'):self.assertIn('run_id',b)
            self.assertTrue(ref['verification_record']['bindings'])
            self.assertEqual(ref['verification_record']['human_explanation_assessment'],'uncollected')

    def test_boolean_rules_and_history_evidence_not_terminal_substitution(self):
        for r in self.records:
            t=r['public']['input']['answer_spec'][0]
            if t['answer_type']!='boolean':continue
            claim=next(c for c in r['private']['reference']['claims'] if c['kind']=='predicate_rule')
            self.assertIn(t['rule_definition'],claim['text'])
            self.assertEqual({b['namespace'] for b in claim['bindings'] if b['pointer']=='/reference/events'},{'factual','alternative'})

    def test_tampered_readout_target_cutoff_claim_history_or_reservation_rejected(self):
        base=self.records[0]
        for what in ('value','unit','timestamp','cutoff','claim','binding','extra_outcome','reservation'):
            r=deepcopy(base)
            if what=='value':r['public']['input']['supplied_comparison']['readouts'][0]['value']=999
            elif what=='unit':r['public']['input']['supplied_comparison']['unit']='m'
            elif what=='timestamp':r['public']['input']['supplied_comparison']['timestamp']=.2
            elif what=='cutoff':r['public']['input']['observation_cutoff']=1.
            elif what=='claim':r['private']['reference']['claims'][0]['text']='Invented forces caused the outcome.'
            elif what=='binding':r['private']['reference']['claims'][0]['bindings'][0]['pointer']='/states/999'
            elif what=='extra_outcome':r['public']['input']['supplied_comparison']['readouts'].append({'condition':'extra','value':1})
            else:r['private']['explanation_evidence']['parent_record']['private']['answer_annotation']['evidence_context']['runs']['alternative-coarse']['reservation']['dt']=123
            with self.assertRaises((ValueError,KeyError,IndexError,ValidationError)):validate(r)

    def test_72_requests_explanation_contract_tool_free_and_private_roots_absent(self):
        records={r['sample_id']:r for r in self.records};total=0
        for condition in self.conditions:
            requests=read(self.root/'public-requests'/(condition['condition_id']+'.json'))
            self.assertEqual(len(requests),8)
            for req in requests:
                self.assertEqual(req['tools'],[]);self.assertIn('This is explanation QA',req['messages'][0]['content'])
                public=json.loads(req['messages'][0]['content'].split('\n',1)[1])
                r=records[req['sample_id']];self.assertEqual(canonical(public),canonical(public_record(r,association_version='simphysqa-associations/1.1.1')))
                for token in ('verification_record','private','explanation_evidence','solution_trace','answer_annotation','gpt-5.6-sol'):
                    self.assertNotIn(token,canonical(public).decode())
                self.assertIn('supplied_comparison',public['input']);total+=1
        self.assertEqual(total,72)

    def test_factual_component_probe_never_proves_prose_correctness(self):
        r=self.records[0]
        full={**expected_facts(r),'explanation':'A clear connected software test paraphrase.','supported_interpretation':'A software probe.','remaining_uncertainty':'A software probe.'}
        a=check_facts(r,full)
        nonsense={**full,'explanation':'Unsupported real-world causality and invented mechanisms.','supported_interpretation':'Wrong prose.','remaining_uncertainty':'None.'}
        b=check_facts(r,nonsense)
        self.assertTrue(a['factual_components_all_correct']);self.assertTrue(b['factual_components_all_correct'])
        self.assertIsNone(a['overall_explanation_correctness']);self.assertIsNone(b['overall_explanation_correctness'])
        self.assertEqual(b['explanatory_adequacy'],'human_judgment_uncollected')
        wrong=deepcopy(full);wrong['intervention']['omitted_event_id']='other-event'
        self.assertFalse(check_facts(r,wrong)['factual_components_all_correct'])
        wrong=deepcopy(full);wrong['fixed_conditions']=[]
        self.assertFalse(check_facts(r,wrong)['factual_component_checks']['fixed_condition_declarations'])
        invalid=deepcopy(full);invalid['explanation']=''
        with self.assertRaises(ValidationError):check_facts(r,invalid)

    def test_missing_invalid_failed_outputs_stay_in_fact_denominators_and_numeric_route_rejects(self):
        r=self.records[0];cond=self.conditions[0]['condition_id']
        p={'condition_id':cond,'sample_id':r['sample_id'],'annotation_version':r['annotation_version'],
            'task_version':r['public']['input']['explanation_task']['version'],'status':'completed','response':{'malformed':True}}
        result=score_facts(self.records,[p],[cond])
        self.assertEqual(len(result['items']),8)
        self.assertEqual(sum(t['expected_factual_components'] for t in result['tables']),48)
        self.assertEqual(sum(i['status']=='missing' for i in result['items']),7)
        self.assertEqual(sum(i['status']=='invalid' for i in result['items']),1)
        with self.assertRaises(ValueError):score(self.records,[],[cond])

    def test_blank_forms_and_packets_include_new_rubric_and_claim_roots(self):
        m=verify_manifest(self.root/'audit-development');self.assertEqual(len(m['assignments']),8)
        for reviewer in ('R1','R2','R3'):
            result=read(self.root/'verification'/(reviewer+'-blank-import.json'))
            self.assertEqual(result['collected'],0);self.assertEqual(result['blank'],8)
        for a in m['assignments']:
            p=read(self.root/'audit-development/packets'/(a['packet_id']+'.json'))
            self.assertEqual(p['rubric_version'],'matched-explanation-rubric/1.0.0')
            self.assertIn('answer_evidence_roots',p['verification'])
            self.assertIn('claims',p['qa']['reference'])
            self.assertNotIn('gpt-5.6-sol',canonical(p).decode())

    def test_build_offline_and_completed_outputs_are_not_overwritten(self):
        parent=self.records[0]['private']['explanation_evidence']['parent_record']
        with patch('socket.socket',side_effect=AssertionError('no network')),patch('subprocess.Popen',side_effect=AssertionError('no simulator subprocess')):
            self.assertEqual(canonical(build(parent)),canonical(self.records[0]))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'item.json';retained(p,self.records[0]);original=p.read_bytes()
            retained(p,self.records[0]);self.assertEqual(p.read_bytes(),original)
            changed=deepcopy(self.records[0]);changed['sample_id']='changed'
            with self.assertRaises(ValueError):retained(p,changed)
            self.assertEqual(p.read_bytes(),original)

    def test_archive_maps_new_files_to_deterministic_generation_and_reused_language(self):
        archive=Path(os.environ['SIMPHYSQA_PROMPT_ARCHIVE']);index=read(archive/'file-generation-index.json')
        self.assertEqual(index['recovery']['executed_requests'],16)
        self.assertEqual(index['recovery']['unavailable_executed_payloads'],0)
        ids={r['sample_id'] for r in self.records};parent_ids={r['sample_id']:r['private']['explanation_evidence']['parent_sample_id'] for r in self.records};found=set();mapped=0
        for f in index['files']:
            if not f['artifact'].startswith('SPQ03-explanation/'):continue
            for m in f.get('mappings',[]):
                definition=index['mapping_definitions'][m['mapping_id']]
                if definition['sample_id'] not in ids:continue
                found.add(definition['sample_id']);mapped+=1
                for field in definition['field_generation']:
                    if field['field'] in ('question','supplied_comparison') or 'explanation_annotation' in field['field']:
                        self.assertEqual(field['method'],'deterministic_no_model_prompt')
                        self.assertEqual(field['procedure_id'],'explanation-qa/1.0.0')
                        self.assertEqual(field['parent_artifact'],'SPQ02b-enriched/organizer-private/items/'+parent_ids[definition['sample_id']]+'.json')
                    if field['field'].startswith(('trajectory','timestamps')):
                        self.assertEqual(field['method'],'reuse_copy_of_executed_model_measurement_annotation')
        self.assertEqual(found,ids);self.assertGreaterEqual(mapped,8*9)

if __name__=='__main__':unittest.main()
