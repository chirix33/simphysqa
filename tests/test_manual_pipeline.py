import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import replay_pipeline as replay


class ManualReplayTests(unittest.TestCase):
    def test_historical_output_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'historical'):
            replay.output_path(str(replay.RUNS['p11']/'new-result.json'))

    def test_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'result.json'; path.write_text('original')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                replay.output_path(str(path))
            self.assertEqual(path.read_text(),'original')

    def test_domain_and_matched_appendix_filter(self):
        rows=[{'public':{'input':{'domain':domain}},'split':'test_id','appendix':appendix}
              for domain in ('driving','robotic_arm') for appendix in (False,True)]
        args=Namespace(study='p11',domain='driving',cohort='appendix',split=None,config=None,source_root=Path('/example'))
        with patch.object(replay,'load',return_value=rows):
            selected=replay.choose_rows(args)
        self.assertEqual(selected,[rows[1]])

    def test_new_domain_config_is_not_tether_only(self):
        row={'public':{'input':{'domain':'robotic_arm'}},'split':'validation'}
        args=Namespace(study='p10',domain='robotic_arm',cohort='main',split=None,config=Path('new.json'),source_root=Path('/example'))
        with patch.object(replay,'load',return_value=[row]):
            self.assertEqual(replay.choose_rows(args),[row])


if __name__=='__main__':unittest.main()
