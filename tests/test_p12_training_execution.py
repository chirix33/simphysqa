"""Offline checks for the extra execution envelope, without optimizer steps."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import p12_training_execution as run


class ExecutionEnvelopeTests(unittest.TestCase):
    def exercise(self, expired=False, artifact_cap=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root/'control'
            approved = root/'approved.json'
            plan = {'study_root':str(root/'study'), 'artifact_bytes_cap':1 if artifact_cap else 1000000000,
                    'domains':{d:{'wall_seconds_cap':3600,'optimizer_updates':1} for d in run.ORDER}}
            run.save(approved,plan)
            deadline = time.time()+(-1 if expired else 1000)
            run.save(control/'execution-window.json', {'deadline_unix':deadline,'started_unix':time.time(),
                'approved_plan_sha256':run.file_hash(approved),'launcher_sha256':run.file_hash(run.__file__)})
            with patch.object(run,'CONTROL',control), patch.object(run,'APPROVED',approved), \
                 patch.object(run,'authorize',return_value=plan), \
                 patch.object(run.planning,'preflight',return_value={'can_train':True,
                    'integrity_failures':0,'missing_identity_verified_contexts':0}), \
                 patch.object(run.subprocess,'Popen') as launch:
                with self.assertRaises(TimeoutError if expired else ValueError):
                    run.execute()
                launch.assert_not_called()
                self.assertEqual(run.load(control/'execution-window.json')['deadline_unix'],deadline)
                self.assertTrue((control/'failure.json').exists())
                self.assertFalse((control/'attempts').exists())
                with self.assertRaisesRegex(ValueError,'previous stopped execution'):
                    run.execute()
                launch.assert_not_called()

    def test_expired_global_window_never_renews_or_dispatches(self):
        self.exercise(expired=True)

    def test_artifact_cap_blocks_dispatch_and_retry(self):
        self.exercise(artifact_cap=True)


if __name__ == '__main__':
    unittest.main()
