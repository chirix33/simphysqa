"""Offline synthetic mechanics, explicitly not empirical forecasting evidence."""
import copy
from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import (PublicProblem, Identity, FullAugmentedPrediction,
    validate_enrichment, DOMAINS, SPLITS)
from phi_jepa.integration.layout import StateLayout, rows
from phi_jepa.integration.readers import (PublicInputReader, file_hash, forecast_states,
    make_pairs, strict_json, TrainingSequenceReader, ReleaseCatalog)

def fixture():
    def state(t, step, value):
        return {'state_id':str(step), 'timestamp':t,'step_index':step,'context':'fixture', 'relations':[],
            'measurements':[{'entity_id':'a_b','name':'c','frame':'world','unit':'m','value':[value,2.0,3.0]},
                            {'entity_id':'a','name':'b_c','frame':'world','unit':'1','value':False}]}
    inp={'domain':'robotic_arm','task_type':'fixture','question':'At 0.24 seconds?',
         'observation_cutoff':0.2,'states':[state(0.0,0,0.0),state(0.2,10,1.0)],
         'answer_spec':[{'target_id':'x','end_time':0.24}], 'controller':{'torque':2.0},
         'coordinate_convention':'xyz','entities':[], 'global_context':'digits 123 stay text','known_events':[]}
    public={'schema_version':'1.0.0','sample_id':'sample','input':inp}
    reference={'states':[state(0.22,11,1.5),state(0.24,12,2.0)],'label':'private answer','explanation':'private'}
    return public,reference

class P02aTests(unittest.TestCase):
    def setUp(self):
        self.public,self.ref=fixture()
        self.problem=PublicProblem.parse(self.public)
        self.inp=self.public['input']
        self.state=self.inp['states'][-1]
        self.layout=StateLayout.build(self.state,self.inp,'state_only','train')
        self.identity=Identity('sample','group','group','robotic_arm','train')

    def pairs(self,reference=None,identity=None):
        mult=Counter({digest(('robotic_arm','group',a,b)):2 for a,b in [(0.2,0.22),(0.22,0.24)]})
        return list(make_pairs(self.problem,reference or self.ref,identity or self.identity,self.layout,'provenance',mult))

    def test_semantic_order_vectors_and_digit_strings(self):
        changed=copy.deepcopy(self.state); changed['measurements'].reverse()
        self.assertEqual(self.layout.flatten(changed,self.inp),self.layout.flatten(self.state,self.inp))
        self.assertEqual(self.layout.d,5) # vector xyz plus index/time
        self.assertEqual(len(rows({'a_b':{'c':1},'a':{'b_c':2}})),2)
        self.assertNotEqual(rows({'a_b':{'c':1}})[0][0],rows({'a':{'b_c':1}})[0][0])

    def test_missing_extra_duplicate_and_null_never_zero(self):
        for edit in ('missing','extra','duplicate','null'):
            s=copy.deepcopy(self.state)
            if edit=='missing': s['measurements'].pop()
            if edit=='extra': s['new']=1
            if edit=='duplicate': s['measurements'].append(s['measurements'][0])
            if edit=='null': s['measurements'][0]['value']=None
            with self.subTest(edit=edit),self.assertRaises(ValueError): self.layout.flatten(s,self.inp)

    def test_bool_unit_frame_vector_length_types(self):
        for key,value in [('value',True),('unit','cm'),('frame','body'),('value',[1.0,2.0]),('value',[float('inf'),2.0,3.0])]:
            s=copy.deepcopy(self.state); s['measurements'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError): self.layout.flatten(s,self.inp)

    def test_dynamic_categorical_relations_do_not_change_numeric_layout(self):
        s=copy.deepcopy(self.state)
        s['relations']=[{'subject_id':'a','predicate':'contact','object_id':'b'}]
        self.assertEqual(self.layout.flatten(s,self.inp),self.layout.flatten(self.state,self.inp))
        s['relations'][0]['force']=1.0
        with self.assertRaises(ValueError): self.layout.flatten(s,self.inp)

    def test_reference_integer_prediction_float(self):
        s=copy.deepcopy(self.state); s['step_index']=10.5
        with self.assertRaises(ValueError): self.layout.flatten(s,self.inp)
        self.assertEqual(self.layout.validate_prediction([1.5]*5),(1.5,)*5)
        with self.assertRaises(ValueError): self.layout.validate_prediction([True]*5)

    def test_pair_target_depends_on_recorded_future(self):
        before=self.pairs(); changed=copy.deepcopy(self.ref)
        changed['states'][0]['measurements'][0]['value'][0]=99.0
        after=self.pairs(changed)
        self.assertNotEqual(before[0].n_next,after[0].n_next)
        self.assertEqual(before[0].n_current,after[0].n_current)
        self.assertEqual(before[0].n_next,before[1].n_current)
        self.assertAlmostEqual(before[0].dt,0.02)
        self.assertEqual(before[0].weight,1.0)  # active user-approved default
        self.assertNotIn('private answer',before[0].context_json)

    def test_time_order_horizon_and_context(self):
        with self.assertRaises(ValueError): self.problem.context(0.0)
        for field,value in [('timestamp',0.2),('step_index',10)]:
            ref=copy.deepcopy(self.ref); ref['states'][0][field]=value
            with self.assertRaises(ValueError): forecast_states(self.problem,ref)
        ref=copy.deepcopy(self.ref); ref['states'].pop()
        with self.assertRaises(ValueError): forecast_states(self.problem,ref)

    def test_split_isolation_and_registry_fit(self):
        with self.assertRaises(ValueError): self.pairs(identity=Identity('sample','group','group','robotic_arm','validation'))
        with self.assertRaises(ValueError): StateLayout.build(self.state,self.inp,'state_only','validation')
        with self.assertRaises(ValueError): TrainingSequenceReader(None,'robotic_arm',self.layout,duplicate_policy='drop_questions',context_mode='public_base_for_offline_audit')

    def test_enrichment_required_without_fallback(self):
        with self.assertRaises(ValueError):
            TrainingSequenceReader(None,'robotic_arm',self.layout,duplicate_policy='inverse_transition_multiplicity',context_mode='enriched')
        pairs=self.pairs();mult=Counter({p.transition_id:2 for p in pairs})
        proposal={'public_input':self.inp,'notes':['Public fixture note']}
        enriched=list(make_pairs(self.problem,self.ref,self.identity,self.layout,'test',mult,context_mode='enriched',enrichment=proposal))
        self.assertEqual(enriched[0].context_mode,'enriched')
        self.assertIn('public_enrichment',enriched[0].context_json)
        self.assertNotEqual(enriched[0].pair_id,pairs[0].pair_id)

    def test_public_reader_independent_of_reference_payload(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'inputs.jsonl'; p.write_text(json.dumps(self.public)+'\n')
            ref=Path(td)/'references.jsonl'; ref.write_text(json.dumps(self.ref))
            before=list(PublicInputReader(p,file_hash(p)))
            ref.write_text('malformed private data can never be opened here')
            self.assertEqual(before,list(PublicInputReader(p,file_hash(p))))
            ref.unlink()
            self.assertEqual(before,list(PublicInputReader(p,file_hash(p))))
            original_hash=file_hash(p)
            p.write_text(p.read_text()+' ')
            with self.assertRaises(ValueError): PublicInputReader(p,original_hash)

    def test_question_conditioning_and_provenance_identity(self):
        pairs=self.pairs()
        public=copy.deepcopy(self.public); public['input']['question']='Different question at the same horizon'
        problem=PublicProblem.parse(public)
        mult=Counter({p.transition_id:2 for p in pairs})
        changed=list(make_pairs(problem,self.ref,self.identity,self.layout,'new_source_hash',mult))
        self.assertEqual(changed[0].transition_id,pairs[0].transition_id)
        self.assertNotEqual(changed[0].pair_id,pairs[0].pair_id)
        self.assertNotEqual(changed[0].provenance_sha256,pairs[0].provenance_sha256)
        ref=copy.deepcopy(self.ref);ref['label']='different gold label';ref['explanation']='different private text'
        self.assertEqual(self.pairs(ref),pairs)

    def test_forbidden_fields_and_immutable_enrichment(self):
        for key in ('reference','metadata','label','predictions','A','explanation'):
            public=copy.deepcopy(self.public); public['input']['controller'][key]='secret'
            with self.assertRaises(ValueError): PublicProblem.parse(public)
        for change in ('value','new_list','private'):
            proposal={'public_input':copy.deepcopy(self.inp),'notes':[]}
            if change=='value': proposal['public_input']['controller']['torque']=9.0
            if change=='new_list': proposal['notes']=[9.0]
            if change=='private': proposal['notes']=[{'label':'answer'}]
            with self.assertRaises(ValueError): validate_enrichment(self.problem,proposal)
        validate_enrichment(self.problem,{'public_input':self.inp,'notes':['public-only proposed text']})

    def test_fixed_scope_and_full_feedback(self):
        layout=StateLayout.build(self.state,self.inp,'state_plus_fixed_conditioning','train')
        self.assertGreater(layout.d,self.layout.d)
        prediction=FullAugmentedPrediction(self.layout.sha256,5,tuple(range(10)),0.22)
        self.assertEqual(prediction.feedback(),tuple(range(10)))
        with self.assertRaises(ValueError): FullAugmentedPrediction('x',5,(1.0,)*5,0.22)
        self.assertNotEqual(self.layout.sha256,layout.sha256)
        restored=StateLayout.from_manifest(json.loads(json.dumps(layout.manifest())),layout.sha256)
        self.assertEqual(restored.flatten(self.state,self.inp),layout.flatten(self.state,self.inp))
        with self.assertRaises(ValueError): StateLayout.from_manifest(layout.manifest(),'bad hash')

    def test_strict_json_and_domains(self):
        with self.assertRaises(ValueError): strict_json('{"a":1,"a":2}')
        with self.assertRaises(ValueError): strict_json('{"a":NaN}')
        public=copy.deepcopy(self.public); public['input']['domain']='quadruped_locomotion'
        with self.assertRaises(ValueError): PublicProblem.parse(public)
        with self.assertRaises(ValueError): PublicProblem.parse({**self.public,'reference':self.ref})

    def test_release_catalog_excludes_development_quarantine_and_quad(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=root/'release-manifest.json';manifest.write_text('{}')
            base={'development_included':False,'quarantine_in_admitted_selection':False,
                  'partitions':[{'domain':d,'partition':s} for d in DOMAINS for s in SPLITS]}
            for kind in ('development','quarantine','quad','development_partition'):
                index=copy.deepcopy(base)
                if kind=='development': index['development_included']=True
                if kind=='quarantine': index['quarantine_in_admitted_selection']=True
                if kind=='quad': index['partitions'][0]['domain']='quadruped_locomotion'
                if kind=='development_partition': index['partitions'][0]['partition']='development'
                p=root/'export-index.json';p.write_text(json.dumps(index))
                with self.subTest(kind=kind),self.assertRaises(ValueError): ReleaseCatalog(root,file_hash(p),file_hash(manifest))

if __name__=='__main__': unittest.main()
