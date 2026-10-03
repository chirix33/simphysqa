"""Supervisor cost/failure behavior; no model requests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from p12_interface_qualification_run import reserve, overhead, wait_for_file, terminate, TokenArchive


class SupervisorTests(unittest.TestCase):
    def ledger(self):
        return dict(started_unix=100.,deadline_unix=7300.,finished_unix=None,attempts=[])

    def test_attempts_never_reset_or_repeat(self):
        ledger=self.ledger()
        reserve(ledger,'cot','a','sha',110,240)
        with self.assertRaisesRegex(ValueError,'already counted'):reserve(ledger,'cot','a','sha',120,240)
        ledger['attempts']*=32
        with self.assertRaisesRegex(ValueError,'cap exhausted'):reserve(ledger,'cot','b','sha',120,240)
        self.assertEqual(ledger['deadline_unix'],7300.)

    def test_request_and_setup_allowances(self):
        ledger=self.ledger()
        with self.assertRaisesRegex(ValueError,'shared window'):reserve(ledger,'cot','a','sha',7100,240)
        with self.assertRaisesRegex(ValueError,'overhead'):reserve(ledger,'cot','a','sha',1600,240)
        a=reserve(ledger,'cot','a','sha',110,240);a['finished_unix']=210
        self.assertEqual(overhead(ledger,220),20.)
        self.assertEqual(ledger['deadline_unix'],7300.)

    def test_hard_timeout_and_late_result_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result.json'
            process=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True)
            start=time.time()
            try:
                self.assertEqual(wait_for_file(process,path,start+.15),'hard_time_cap')
                self.assertLess(time.time()-start,1.)
                path.write_text(json.dumps({'worker_finished_unix':start+1}))
                self.assertEqual(wait_for_file(process,path,start+.2),'hard_time_cap')
            finally:terminate(process)
            self.assertIsNotNone(process.poll())

    def test_archive_records_without_changing_tokens(self):
        import torch
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'tokens.jsonl';archive=TokenArchive(path,[5,6])
            archive.put(torch.tensor([[5,6]]))
            token=torch.tensor([7]);archive.put(token);archive.put(torch.tensor([8]));archive.end();archive.close()
            self.assertEqual(token.tolist(),[7])
            self.assertEqual([json.loads(x) for x in path.read_text().splitlines()],[[7],[8]])
            with self.assertRaises(FileExistsError):TokenArchive(path,[5,6])


if __name__=='__main__':unittest.main()
