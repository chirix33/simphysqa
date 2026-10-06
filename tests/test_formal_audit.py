"""SPQ05 sampling, extraction and import behavior. Fixtures are software probes."""
from copy import deepcopy
import csv
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from simphysqa.io import DOMAINS, QUESTION_TYPES, canonical, digest
from simphysqa.formal_sampling import candidates, save_bytes
from simphysqa.focused_audit import extract, blank_forms, validate_form, COLUMNS, CRITERIA, import_form


def packet():
    # Field names match actual saved exports. Minimal synthetic physics is not audit data.
    state = {'state_id': 's1', 'timestamp': 0.0, 'context': 'generic original context',
             'measurements': [{'entity_id': 'car', 'name': 'speed', 'value': 1, 'unit': 'm/s', 'frame': 'world'}],
             'relations': [], 'linked_events': []}
    return {'sample_id': 'sample', 'packet_id': 'packet', 'question_type': 'predictive',
            'annotation_version': 'test', 'export_version': 'simphysqa-associations/1.1.1',
            'structured_inputs': {'domain': 'driving', 'global_context': 'physical setup',
                'states': [state], 'controller': {}, 'known_events': [], 'entities': [],
                'observation_cutoff': 0.0, 'coordinate_convention': 'world'},
            'language_annotations': {'trajectory': {'text': 'observed trajectory', 'bindings': ['/states/0/measurements/0']},
                'timestamps': [{'state_id': 's1', 'timestamp': 0.0, 'text': 'actual timestamp language', 'bindings': ['/states/0/timestamp']}]},
            'qa': {'question': 'future readout?', 'reference': {'secret_gold': 99}},
            'verification': {'metadata': {'split_group_id': 'g1', 'split': 'train', 'simulation': {'generator': 'secret_generator'}}}}


class SamplingTests(unittest.TestCase):
    def rows(self):
        rows = []
        for domain in DOMAINS:
            for i in range(76):
                for j in range(2):
                    rows.append({'sample_id': f'{domain}-{i}-{j}', 'group_id': f'{domain}-{i}',
                        'trajectory_id': f'{domain}-{i}', 'domain': domain, 'split': 'train',
                        'question_type': 'predictive', 'target_time': j+1})
        return rows

    def test_balanced_distinct_reproducible_and_excluded(self):
        excluded = {'driving-0'}
        a, rejected, pools = candidates(self.rows(), excluded, 20261006)
        b, _, _ = candidates(list(reversed(self.rows())), excluded, 20261006)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 280)
        self.assertEqual(len({c['source']['group_id'] for c in a}), 280)
        self.assertEqual(len(rejected), 2)
        self.assertFalse(excluded & {c['source']['group_id'] for c in a})
        for domain in DOMAINS:
            for family in QUESTION_TYPES:
                cell = [c for c in a if c['cell'] == domain+'/'+family]
                self.assertEqual([c['rank'] for c in cell], list(range(1, 15)))
                self.assertEqual([c['role'] for c in cell], ['primary']*7+['reserve']*7)
        self.assertEqual(len(pools), 20)

    def test_questions_random_not_earliest_and_outcomes_unused(self):
        rows = self.rows()
        a, _, _ = candidates(rows, set(), 20261006)
        self.assertEqual({c['source']['target_time'] for c in a}, {1, 2})
        for row in rows:
            row['description_appeal'] = 'different'
            row['private_outcome'] = 999
        b, _, _ = candidates(rows, set(), 20261006)
        self.assertEqual([c['candidate_id'] for c in a], [c['candidate_id'] for c in b])

    def test_duplicate_and_cross_split_groups_rejected(self):
        rows = self.rows()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            candidates(rows+[deepcopy(rows[0])], set(), 1)
        rows[1]['split'] = 'test_id'
        with self.assertRaisesRegex(ValueError, 'crosses'):
            candidates(rows, set(), 1)


class ExtractionTests(unittest.TestCase):
    def test_roles_types_privacy_and_zero_event_states(self):
        source = packet()
        before = canonical(source)
        out = extract(source, 'hash', 'auditor-only/packet.json')
        self.assertEqual(out['missing_required_fields'], [])
        self.assertEqual(out['validation_errors'], [])
        self.assertEqual(out['structured_inputs']['global_context'], 'physical setup')
        self.assertEqual(out['language_annotations']['trajectory']['text'], 'observed trajectory')
        self.assertEqual(out['states'][0]['context'], 'generic original context')
        self.assertEqual(out['states'][0]['timestamp_language']['text'], 'actual timestamp language')
        self.assertIs(type(out['states'][0]['measurements'][0]['value']), int)
        self.assertEqual(out['states'][0]['linked_events'], [])
        self.assertNotIn(b'secret_gold', canonical(out))
        self.assertNotIn(b'secret_generator', canonical(out))
        self.assertEqual(before, canonical(source))

    def test_state_id_join_and_time_type_fidelity(self):
        p = packet()
        p['structured_inputs']['states'].append(deepcopy(p['structured_inputs']['states'][0]))
        p['structured_inputs']['states'][1].update(state_id='s2', timestamp=0.1)
        p['language_annotations']['timestamps'].insert(0, {'state_id':'s2', 'timestamp':0.1, 'text':'second language', 'bindings':[]})
        out = extract(p, 'h', 'e')
        self.assertEqual(out['states'][0]['timestamp_language']['text'], 'actual timestamp language')
        self.assertEqual(out['states'][1]['timestamp_language']['text'], 'second language')
        p['language_annotations']['timestamps'][1]['timestamp'] = 0
        self.assertTrue(extract(p,'h','e')['validation_errors'])

    def test_missing_language_never_uses_context_and_dangling_bindings(self):
        p = packet()
        p['language_annotations']['timestamps'] = []
        out = extract(p, 'h', 'e')
        self.assertIsNone(out['states'][0]['timestamp_language'])
        self.assertTrue(out['missing_required_fields'])
        p = packet()
        p['language_annotations']['trajectory']['bindings'] = ['/states/20/timestamp']
        self.assertIn('unresolved_binding', str(extract(p,'h','e')['validation_errors']))


class RatingTests(unittest.TestCase):
    def assignments(self):
        return [{'packet_id':'packet','sample_id':'sample','packet_sha256':'hash'}]

    def test_same_items_three_independent_blank_forms(self):
        forms = blank_forms(self.assignments(), 'formal')
        for reviewer, raw in forms.items():
            self.assertEqual(validate_form(raw, self.assignments(), reviewer, 'formal')['collected'], 0)
            self.assertEqual(validate_form(raw, self.assignments(), reviewer, 'formal')['blank'], 1)

    def filled(self, reviewer='R1'):
        data = blank_forms(self.assignments(), 'formal')[reviewer]
        row = next(csv.DictReader(io.StringIO(data.decode())))
        row.update(judgment='material_error', criteria=';'.join(k+'=material_error' for k in CRITERIA),
                   error_categories='wrong_time', source_locations='/qa/question', comments='incorrect requested time')
        out = io.StringIO(newline='')
        writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator='\n')
        writer.writeheader(); writer.writerow(row)
        return out.getvalue().encode()

    def test_material_findings_and_identity_checks(self):
        data = self.filled()
        self.assertEqual(validate_form(data, self.assignments(), 'R1', 'formal')['collected'], 1)
        for bad in (data.replace(b'hash', b'changed'), data.replace(b'R1', b'R2'),
                    data.replace(b'/qa/question', b''), data.replace(b'wrong_time', b'unknown')):
            with self.assertRaises(ValueError):
                validate_form(bad, self.assignments(), 'R1', 'formal')

    def test_omitted_rows_duplicate_criteria_and_blank_findings_rejected(self):
        with self.assertRaises(ValueError):
            validate_form((','.join(COLUMNS)+'\n').encode(), self.assignments(), 'R1', 'formal')
        data = self.filled().replace(b'global_context=material_error', b'trajectory_language=material_error')
        with self.assertRaises(ValueError):
            validate_form(data, self.assignments(), 'R1', 'formal')
        with self.assertRaises(ValueError):
            validate_form(self.filled().replace(b',material_error,', b',,'), self.assignments(), 'R1', 'formal')

    def test_exclusive_resume_and_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'frozen.json'
            save_bytes(path, b'original')
            save_bytes(path, b'original')
            with self.assertRaises(ValueError):
                save_bytes(path, b'changed')
            self.assertEqual(path.read_bytes(), b'original')

    def test_immutable_csv_and_duplicate_reviewer_import(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            form = root/'submitted.csv'; form.write_bytes(self.filled())
            info = {'phase':'development_extraction_check', 'assignments':self.assignments()}
            # Use test-only phase to avoid pretending this one-item fixture is a140-item freeze.
            form.write_bytes(form.read_bytes().replace(b'formal', b'development_extraction_check'))
            with patch('simphysqa.focused_audit.verify_manifest', return_value=info):
                import_form(root, form, 'R1', root/'originals')
                self.assertEqual((root/'originals/R1/original.csv').read_bytes(), form.read_bytes())
                with self.assertRaises(FileExistsError):
                    import_form(root, form, 'R1', root/'originals')


if __name__ == '__main__':
    unittest.main()
