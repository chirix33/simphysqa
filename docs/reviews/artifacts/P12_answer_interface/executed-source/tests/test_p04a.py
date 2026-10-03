"""Synthetic behavior checks; no network and no empirical accuracy claims."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from phi_jepa.integration.contracts import PublicProblem, PhysicalRollout, FullAugmentedPrediction
from phi_jepa.integration.layout import StateLayout
from phi_jepa.inference.readout import (RULES, CONVENTION, NUMERIC_RULE, BINDING,
    InvalidForecast, named_forecast, read_targets)
from phi_jepa.providers.openai_answer import OpenAIAnswer, parse_answer, AnswerParseFailure
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.contracts import ProviderFailure, FailureCode

ROOT = Path(__file__).resolve().parents[1]


def measurement(entity, name, value, unit='m', frame='world'):
    return dict(entity_id=entity, name=name, value=value, unit=unit, frame=frame)


def example(name='boundary_crossed', end=.44):
    domain, entity, rule = RULES.get(name, ('object_pushing_stacking', 'block_2', 'contact-dependent'))
    if name == 'joint_limit_by_T': ms = [measurement(j, 'angle', 0., 'rad', 'joint_local') for j in ('joint_1', 'joint_2')]
    elif name == 'stopped_by_T': ms = [measurement('car', 'velocity', [0.,0.,0.], 'm/s'), measurement('car','forward_velocity',0.,'m/s')]
    else: ms = [measurement(entity, 'position', [0.,0.,1.])]
    def state(i): return dict(state_id=str(i), timestamp=round(i*.02,8), step_index=i, measurements=deepcopy(ms), relations=[], context='fixture')
    target = dict(target_id=entity+':'+name, entity_id=entity, quantity=name, answer_type='boolean',
        unit='1', frame='world', query_kind='at_time', start_time=end, end_time=end,
        rule_id='terminal_readout_v1', rule_definition=rule, absolute_tolerance=0., relative_tolerance=0.)
    inp = dict(domain=domain, task_type='future_state_prediction', question='fixture?', observation_cutoff=.2,
        states=[state(i) for i in range(11)], answer_spec=[target], entities=[], controller={'magnitude':2.},
        known_events=[], global_context='fixture', coordinate_convention=CONVENTION)
    p = PublicProblem.parse(dict(sample_id='fixture', schema_version='1.0.0', input=inp))
    return p, {'sample_id': p.sample_id, 'states': [state(i) for i in range(11,round(end/.02)+1)]}


def replace_input(p, inp): return PublicProblem.parse(dict(sample_id=p.sample_id, schema_version=p.schema_version, input=inp))


def llm_result(p, rows):
    return {'plain_text_answer': 'fixture answer', 'targets': [{k:r[k] for k in (*BINDING, 'status', 'value', 'reason')} for r in rows]}


class P04aTests(unittest.TestCase):
    def test_mapping_preserves_values_and_excludes_context_and_fixed_coordinates(self):
        p, payload = example()
        inp = p.input
        layout = StateLayout.build(inp['states'][-1], inp, 'state_plus_fixed_conditioning', 'train')
        vals = tuple(layout.flatten(inp['states'][-1], inp)) + (8765.,)*layout.d
        full = PhysicalRollout(p.sample_id, (FullAugmentedPrediction(layout.sha256, layout.d, vals, .22),))
        original = asdict(full)
        result = named_forecast(p, layout, full)
        self.assertEqual(result['states'][0]['measurements'], inp['states'][-1]['measurements'])
        self.assertEqual(result['states'][0]['timestamp'], .22)
        self.assertNotIn('8765', json.dumps(result))
        self.assertNotIn('fixed_conditioning', json.dumps(result))
        self.assertEqual(asdict(full), original)
        wrong = PhysicalRollout('foreign', full.predictions)
        with self.assertRaises(InvalidForecast): named_forecast(p,layout,wrong)

    def test_crossing_hysteresis_and_event_survives_return(self):
        p, f = example()
        f['states'][1]['measurements'][0]['value'][0] = .105
        self.assertIs(read_targets(p,f)[0]['value'], False)
        f['states'][1]['measurements'][0]['value'][0] = .106
        self.assertIs(read_targets(p,f)[0]['value'], True)
        inp=p.input; inp['states'][-1]['measurements'][0]['value'][0]=.1
        r=read_targets(replace_input(p,inp),f)[0]
        self.assertEqual(r['reason'],'initial_crossing_state_not_qualified')
        self.assertIsNone(r['value'])

    def test_table_exit_is_endpoint_not_event(self):
        p,f=example('left_table')
        f['states'][0]['measurements'][0]['value'][0]=3.
        self.assertIs(read_targets(p,f)[0]['value'],False)
        f['states'][-1]['measurements'][0]['value'][1]=2.01
        self.assertIs(read_targets(p,f)[0]['value'],True)

    def test_joint_limit_accumulates_and_initial_history_required(self):
        p,f=example('joint_limit_by_T')
        f['states'][0]['measurements'][1]['value']=-2.8
        self.assertIs(read_targets(p,f)[0]['value'],True)
        inp=p.input; inp['states']=inp['states'][1:]
        self.assertEqual(read_targets(replace_input(p,inp),f)[0]['reason'],'time_coverage')

    def test_stopping_dwell_and_speed_components(self):
        p,f=example('stopped_by_T')
        inp=p.input
        for s in inp['states']: s['measurements'][1]['value']=1.
        p=replace_input(p,inp)
        self.assertIs(read_targets(p,f)[0]['value'],True)  # .22 to .44
        f['states'][4]['measurements'][0]['value'][1]=.04
        self.assertIs(read_targets(p,f)[0]['value'],False)
        f['states'][4]['measurements'][0]['value'][1]=0.
        f['states'][4]['measurements'][1]['value']=.02
        self.assertIs(read_targets(p,f)[0]['value'],False)  # strict speed threshold

    def test_support_qualification_per_target_and_invalid_forecast(self):
        for mutation in ('unit','frame','missing','grid','rule','convention','shape'):
            p,f=example(); inp=p.input
            if mutation in ('unit','frame'): f['states'][0]['measurements'][0][mutation]='wrong'
            elif mutation=='missing': f['states'][0]['measurements']=[]
            elif mutation=='grid': f['states'].pop(2)
            elif mutation=='rule': inp['answer_spec'][0]['rule_definition']='different threshold'
            elif mutation=='convention': inp['coordinate_convention']='unknown'
            elif mutation=='shape': f['states'][0]['measurements'][0]['value']=[0.,0.]
            with self.subTest(mutation=mutation):
                row=read_targets(replace_input(p,inp),f)[0]
                self.assertEqual(row['status'],'unsupported'); self.assertIsNone(row['value'])
        p,f=example(); f['states'][0]['measurements'][0]['value'][0]=float('nan')
        with self.assertRaises(InvalidForecast): read_targets(p,f)

    def test_contact_outputs_explicitly_unsupported(self):
        for name in ('stable_stack','support_lost'):
            p,f=example(name)
            row=read_targets(p,f)[0]
            self.assertEqual(row['status'],'unsupported')
            self.assertEqual(row['reason'],'missing_contact_force_and_history')
            self.assertIsNone(row['value'])

    def test_numeric_scalar_vector_and_no_boolean_cast(self):
        p,f=example(); inp=p.input
        t=inp['answer_spec'][0]; t.update(target_id='load:position',quantity='position',answer_type='vector',unit='m',rule_definition=NUMERIC_RULE)
        p=replace_input(p,inp); row=read_targets(p,f)[0]
        self.assertEqual(row['value'],[0.,0.,1.])
        t['answer_type']='number'
        self.assertEqual(read_targets(replace_input(p,inp),f)[0]['status'],'unsupported')

    def test_parser_rejects_missing_duplicate_binding_type_and_boolean_invention(self):
        p,f=example(); rows=read_targets(p,f); good=llm_result(p,rows)
        self.assertEqual(parse_answer(p,json.dumps(good),rows),good)
        for key,value in [('end_time',5.),('unit','m'),('frame','body'),('value',0),('value',True),('quantity','other')]:
            bad=deepcopy(good); bad['targets'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(AnswerParseFailure): parse_answer(p,json.dumps(bad),rows)
        for targets in ([],good['targets']*2):
            bad=deepcopy(good); bad['targets']=targets
            with self.assertRaises(AnswerParseFailure): parse_answer(p,json.dumps(bad),rows)
        p,f=example('stable_stack'); rows=read_targets(p,f); bad=llm_result(p,rows)
        bad['targets'][0].update(status='supported',value=False,reason=None)
        with self.assertRaises(AnswerParseFailure): parse_answer(p,json.dumps(bad),rows)

    def test_provider_accounting_cache_leakage_and_parser_vs_api_failure(self):
        p,f=example(); rows=read_targets(p,f)
        asset=json.loads((ROOT/'docs/assets/p04a_answer_v1.json').read_text())
        config=json.loads((ROOT/'configs/answer_p04a.json').read_text())
        calls=[]
        def transport(payload,timeout):
            calls.append(payload)
            self.assertNotIn('reference',json.loads(payload['input']))
            self.assertEqual(json.loads(payload['input'])['public_problem']['input'],p.input)
            return {'id':'fixture','model':'fixture','status':'completed','usage':{'input_tokens':10,'output_tokens':20},
                'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(llm_result(p,rows))}]}]}
        with tempfile.TemporaryDirectory() as temp:
            provider=OpenAIAnswer('fixture',config,asset,FrozenOutputCache(temp),transport=transport)
            provider.answer(p,f,rows,condition='fixture'); provider.answer(p,f,rows,condition='fixture')
            self.assertEqual(len(calls),1); self.assertEqual(provider.cache_hits,1)
            self.assertEqual(provider.runner.events[0]['usage']['input_tokens'],10)
            def bad(payload,timeout):
                body=transport(payload,timeout); body['output'][0]['content'][0]['text']='{}'; return body
            provider=OpenAIAnswer('fixture',config,asset,None,transport=bad)
            with self.assertRaises(AnswerParseFailure): provider.answer(p,f,rows,condition='fixture')
            self.assertEqual(provider.runner.events[0]['usage']['output_tokens'],20)
            def unavailable(payload,timeout): raise ProviderFailure(FailureCode.PROVIDER_UNAVAILABLE)
            provider=OpenAIAnswer('fixture',config,asset,None,transport=unavailable)
            with self.assertRaises(ProviderFailure) as caught: provider.answer(p,f,rows,condition='fixture')
            self.assertNotIsInstance(caught.exception,AnswerParseFailure)

    def test_unsupported_and_failed_answers_remain_in_complete_denominator(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('p04a_eval',ROOT/'tools/evaluate_p04a_answers.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        p,f=example('stable_stack'); rows=read_targets(p,f)
        reference={'structured_label':[{'target_id':p.input['answer_spec'][0]['target_id'],'value':False}]}
        for actual in (rows,[]):
            result=module.score(p,reference,actual)
            self.assertEqual(result['eligible_questions'],1)
            self.assertEqual(result['boolean_eligible'],1)
            self.assertEqual(result['boolean_coverage'],0)
            self.assertIsNone(result['boolean_accuracy_supported'])
            self.assertEqual(result['complete_answer_success_all_eligible'],0)

    def test_no_private_payload_or_foreign_readout_accepted(self):
        p,f=example(); f['reference']={'states':[]}
        with self.assertRaises(InvalidForecast): read_targets(p,f)
        del f['reference']; rows=read_targets(p,f); rows[0]['value']=True
        config=json.loads((ROOT/'configs/answer_p04a.json').read_text())
        asset=json.loads((ROOT/'docs/assets/p04a_answer_v1.json').read_text())
        def forbidden(*args): self.fail('network must not be reached')
        provider=OpenAIAnswer('fixture',config,asset,None,transport=forbidden)
        with self.assertRaises(ValueError): provider.answer(p,f,rows,condition='fixture')


if __name__ == '__main__': unittest.main()
