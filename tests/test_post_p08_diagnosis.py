"""Cross-check derived evidence against preserved P08 artifacts, no model work."""
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/reviews/artifacts/Post_P08_diagnosis'


class PostP08EvidenceTests(unittest.TestCase):
    def test_complete_time_and_window_denominators(self):
        rows=list(csv.DictReader((D/'physical_errors_by_time.csv').read_text().splitlines()))
        self.assertEqual(len(rows),7*8*40*5)
        counts=Counter((r['method'],r['scenario_id'],r['quantity'],r['entity_id'],r['window']) for r in rows)
        self.assertEqual(set(counts.values()),{20})
        self.assertTrue(all(.2<float(r['time'])<=1 for r in rows))
        self.assertTrue(all(r['status']=='valid' for r in rows))

    def test_window_composition_matches_original_full_horizon(self):
        rows=list(csv.DictReader((D/'physical_errors_by_window.csv').read_text().splitlines()))
        groups=defaultdict(dict)
        for r in rows: groups[(r['method'],r['scenario_id'],r['entity_id'],r['quantity'])][r['window']]=float(r['rmse'])
        for windows in groups.values():
            self.assertAlmostEqual(windows['full_horizon']**2,(windows['(0.20,0.60]']**2+windows['(0.60,1.00]']**2)/2,places=12)

    def test_gradient_blocks_use_full_denominator_and_no_updates(self):
        rows=json.loads((D/'gradient_blocks.json').read_text()); grouped=defaultdict(list)
        for r in rows:
            self.assertEqual(r['optimizer_updates'],0); grouped[(r['checkpoint_update'],r['sample_id'])].append(r)
        self.assertEqual(len(grouped),8)
        for batch in grouped.values():
            self.assertEqual(sum(r['width'] for r in batch),280)
            self.assertAlmostEqual(sum(r['full_loss_contribution'] for r in batch),batch[0]['full_loss'])

    def test_preserved_strict_generation_failures_are_not_repaired(self):
        rows=json.loads((D/'generation_failure_trace.json').read_text())
        failures=[r for r in rows if r['method'].startswith('coconut') and r['strict_reason']=='target_count']
        self.assertEqual(len(failures),4)
        self.assertTrue(all(len(r['emitted_ids'])==5 and r['duplicated_ids'] and not r['omitted_ids'] for r in failures))
        student=[r for r in rows if r['branch']=='student']; self.assertEqual(len(student),8)
        self.assertTrue(all(r['strict_reason']=='answer_envelope' and set(r['envelope_keys'])=={'targets','explanation'} for r in student))

    def test_scenario_separation_and_exposure(self):
        reg=json.loads((D/'scheduled_regimes.json').read_text()); train=[r for r in reg if r['split']=='train']; val=[r for r in reg if r['split']=='validation']
        self.assertEqual((len(train),len(val)),(32,8))
        self.assertFalse({r['scenario_id'] for r in train}&{r['scenario_id'] for r in val})
        self.assertEqual(sum(sum(r['training_regime_counts'].values()) for r in train),640)
        self.assertEqual(sum(r['training_regime_counts'].get('post_event',0) for r in train),0)


if __name__=='__main__': unittest.main()
