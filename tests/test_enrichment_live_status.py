import unittest
from enrichment_live_status import effective_status

class LiveStatusTests(unittest.TestCase):
    def test_old_pid_or_missing_lock_does_not_claim_running(self):
        for matching,locked in ((False,False),(True,False),(False,True)):
            self.assertEqual(effective_status('running',matching,locked),'interrupted_or_stale')
    def test_live_worker_and_terminal_states(self):
        self.assertEqual(effective_status('running',True,True),'running')
        self.assertEqual(effective_status('finished',False,False),'finished')

if __name__=='__main__':unittest.main()
