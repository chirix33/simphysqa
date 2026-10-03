"""Synthetic money/attempt boundary tests; never use a credential or network."""
import unittest,tempfile,json
from pathlib import Path
from phi_jepa.providers.enrichment_budget import EnrichmentBudget,EnrichmentBudgetStop,reservation,measured_cost

ROOT=Path(__file__).resolve().parents[1]

class BudgetTests(unittest.TestCase):
    def config(self,**changes):
        c=json.loads((ROOT/'configs/enrichment_p12_pilot.json').read_text());return {**c,**changes}
    def payload(self):return {'model':'gpt-5.6-sol','input':'public fixture','max_output_tokens':2048}
    def body(self):return {'model':'gpt-5.6-sol','service_tier':'default','status':'completed','usage':{'input_tokens':100,'output_tokens':10,'input_tokens_details':{'cached_tokens':20,'cache_write_tokens':0}}}
    def test_pre_dispatch_money_reservation_and_unknown_usage_hold(self):
        with tempfile.TemporaryDirectory() as root:
            b=EnrichmentBudget(root,self.config(usd_cap=.15));calls=[]
            def timeout(*args):calls.append(1);raise TimeoutError()
            with self.assertRaises(TimeoutError):b.transport(timeout)(self.payload(),120)
            with self.assertRaises(EnrichmentBudgetStop):b.transport(timeout)(self.payload(),120)
            self.assertEqual(len(calls),1);row=b.read()['attempts'][0]
            self.assertIsNone(row['usage']);self.assertEqual(row['charged_nano_usd'],row['reserved_nano_usd'])
            self.assertLessEqual(row['charged_nano_usd'],150000000)
    def test_attempt_cap_and_resume_cannot_reset_spending(self):
        with tempfile.TemporaryDirectory() as root:
            c=self.config(attempt_cap=2);b=EnrichmentBudget(root,c)
            for _ in range(2):b.transport(lambda *_:self.body())(self.payload(),120)
            again=EnrichmentBudget(root,c)
            with self.assertRaises(EnrichmentBudgetStop):again.transport(lambda *_:self.fail('unexpected dispatch'))(self.payload(),120)
            self.assertEqual(len(again.read()['attempts']),2)
            self.assertEqual(again.read()['attempts'][0]['charged_nano_usd'],528000)
            with self.assertRaises(EnrichmentBudgetStop):EnrichmentBudget(root,self.config(attempt_cap=3))
    def test_price_tier_and_tools_fail_closed_before_dispatch(self):
        c=self.config();payload=self.payload()
        with self.assertRaises(EnrichmentBudgetStop):reservation(payload|{'input':'x'*272000},c['pricing'])
        with self.assertRaises(EnrichmentBudgetStop):reservation(payload|{'model':'other'},c['pricing'])
        with self.assertRaises(EnrichmentBudgetStop):reservation(payload|{'tools':[{}]},c['pricing'])
        direct=measured_cost(self.body(),c['pricing']);fast=measured_cost(self.body()|{'service_tier':'fast'},c['pricing'])
        self.assertEqual(fast['cost_nano_usd'],2*direct['cost_nano_usd'])
        self.assertIsNone(measured_cost(self.body()|{'usage':None},c['pricing']))
        unknown=self.body();unknown['usage']['input_tokens_details'].pop('cache_write_tokens')
        u=measured_cost(unknown,c['pricing']);self.assertIsNone(u['cost_nano_usd'])
        self.assertEqual((u['cost_lower_nano_usd'],u['cost_upper_nano_usd']),(528000,608000))
    def test_incomplete_success_still_charged_and_raw_response_retained(self):
        with tempfile.TemporaryDirectory() as root:
            b=EnrichmentBudget(root,self.config());body=self.body()|{'status':'incomplete'}
            self.assertEqual(b.transport(lambda *_:body)(self.payload(),120),body)
            self.assertEqual(b.read()['attempts'][0]['provider_status'],'incomplete')
            self.assertTrue((Path(root)/'responses/0001.json').exists())

    def test_scope_caps_share_global_ledger(self):
        with tempfile.TemporaryDirectory() as root:
            c=self.config(scope_estimates={'train_validation':{'proposed_attempt_cap':1,'proposed_usd_allocation':1},
                                         'confirmation':{'proposed_attempt_cap':1,'proposed_usd_allocation':1}})
            train=EnrichmentBudget(root,c,scope='train_validation');train.transport(lambda *_:self.body())(self.payload(),120)
            confirm=EnrichmentBudget(root,c,scope='confirmation');confirm.transport(lambda *_:self.body())(self.payload(),120)
            self.assertEqual(len(confirm.read()['attempts']),2)
            with self.assertRaises(EnrichmentBudgetStop):train.transport(lambda *_:self.fail('scope cap bypass'))(self.payload(),120)

    def test_full_run_requires_separate_authorization_before_credentials(self):
        from unittest.mock import patch
        from p12_enrichment_full import run_full
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'disabled.json';path.write_text(json.dumps({'enabled':False}))
            with patch('phi_jepa.providers.credentials.load_openai_key',side_effect=AssertionError('credential access')):
                with self.assertRaisesRegex(ValueError,'separate full-enrichment'):run_full(path,'train_validation')

if __name__=='__main__':unittest.main()
