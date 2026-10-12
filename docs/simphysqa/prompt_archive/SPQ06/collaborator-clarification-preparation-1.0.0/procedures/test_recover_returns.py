"""Synthetic CPU software probes only; no scientific returns or inference."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import recover_returns as recovery


class RecoveryTests(unittest.TestCase):
    def test_missing_original_artifacts_are_reported_without_creation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            root = Path(temporary)
            key = 'SYNTHETIC-NOT-MAIN|gemma3_27b_qat_cot|enriched|1'
            recovery.put(root / 'ticket.json', {'id': 'SYNTHETIC-PROCESS', 'keys': [key]})
            index = {'results': [{'process_reservation': 'SYNTHETIC-PROCESS', 'key': key, 'result_file_sha256': '0' * 64}]}
            before = list(root.rglob('*'))
            result = recovery.check_job(root, index)
            self.assertIn('process-receipt.json', result['missing'])
            self.assertIn('worker-output/executed-requests/SYNTHETIC-NOT-MAIN-stage1.json', result['missing'])
            self.assertEqual(before, list(root.rglob('*')))

    def test_inventory_and_export_do_not_fabricate_missing_jobs(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            root = Path(temporary)
            recovery.put(root / 'expected.json', {'results': [{'process_reservation': 'SYNTHETIC-PROCESS'}]})
            args = SimpleNamespace(expected=str(root / 'expected.json'), search_root=[str(root)],
                                   export_root=str(root / 'export'), output=str(root / 'inventory.json'))
            with contextlib.redirect_stdout(io.StringIO()):
                recovery.inventory(args)
            inv = recovery.read(args.output)
            self.assertEqual(inv['missing_processes'], ['SYNTHETIC-PROCESS'])
            self.assertEqual(inv['status'], 'missing_original_evidence')
            with self.assertRaisesRegex(ValueError, 'complete unique original job inventory required'):
                recovery.export(SimpleNamespace(expected=args.expected, inventory=args.output))
            self.assertFalse((root / 'export').exists())

    def test_discovery_returns_existing_job_and_package_paths(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            root = Path(temporary)
            recovery.put(root / 'job/ticket.json', {'id': 'SYNTHETIC-PROCESS'})
            recovery.put(root / 'package/package-manifest.json', {'files': {}})
            (root / 'package/procedures').mkdir()
            (root / 'package/procedures/public_executor.py').write_text('# synthetic discovery only\n')
            recovery.put(root / '.cache/ignored/ticket.json', {'id': 'SKIP-CACHE'})
            jobs, packages = recovery.discover([str(root), str(root)])
            self.assertEqual(jobs, [(root / 'job').resolve()])
            self.assertEqual(packages, [(root / 'package').resolve()])


if __name__ == '__main__':
    unittest.main()
