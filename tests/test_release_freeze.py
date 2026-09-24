"""No simulation: drift and licensing must fail before dispatch."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from phi_jepa.simulation.freeze import CONTRACT_KEYS, verify_freeze, verify_license
from phi_jepa.simulation.common import ROOT, read
from phi_jepa.simulation.pipeline import run


class FreezeTests(unittest.TestCase):
    def test_rejected_draws_are_preserved_without_replacement_or_retry(self):
        config = read(ROOT / "pilot_config.json")
        with tempfile.TemporaryDirectory() as tmp, patch("phi_jepa.simulation.pipeline.adapter") as engine:
            engine.return_value.simulate.side_effect = ValueError("TEST intentional failure")
            first = run(config, "tethered_load", 2, Path(tmp))
            self.assertEqual(engine.return_value.simulate.call_count, 2)
            plan = read(Path(tmp) / "partitions.json")
            second = run(config, "tethered_load", 2, Path(tmp), resume=True)
            self.assertEqual(engine.return_value.simulate.call_count, 2)
            self.assertEqual(plan, read(Path(tmp) / "partitions.json"))
            self.assertEqual(first["counts"]["accepted"], 0)
            self.assertEqual(second["counts"]["attempted"], 2)
            self.assertEqual(second["counts"]["rejected"], 2)
            self.assertEqual(len((Path(tmp) / "rejections.jsonl").read_text().splitlines()), 2)

    def test_configuration_source_and_evidence_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "registry.json"; artifact.write_bytes(b"original")
            config = {key: {} for key in CONTRACT_KEYS}
            frozen = dict(generation_contract=copy.deepcopy(config), source=dict(source_files={"x": "a"}, git_commit="revision"),
                          files={"registry.json": sha256(b"original").hexdigest()}, runtime_packages={})
            path = root / "freeze.json"; path.write_text(json.dumps(frozen))
            config["experiment_freeze"] = dict(path="freeze.json", sha256=sha256(path.read_bytes()).hexdigest())
            with patch("phi_jepa.simulation.freeze.ROOT", root), \
                    patch("phi_jepa.simulation.freeze.code_provenance", return_value=dict(source_files={"x": "a"})), \
                    patch("phi_jepa.simulation.freeze.subprocess.run") as git:
                git.return_value.returncode = 0
                verify_freeze(config, check_runtime=False)
                bad = copy.deepcopy(config); bad["master_seed"] = 999
                with self.assertRaisesRegex(ValueError, "settings"):
                    verify_freeze(bad, check_runtime=False)
                artifact.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "artifact"):
                    verify_freeze(config, check_runtime=False)
                with patch("phi_jepa.simulation.freeze.code_provenance", return_value=dict(source_files={"x": "b"})):
                    with self.assertRaisesRegex(ValueError, "source"):
                        verify_freeze(config, check_runtime=False)

    def test_proposed_license_is_not_a_grant(self):
        config = dict(licensing_decision="unused", domains={"robotic_arm": {}}, asset_license="CC-BY-4.0")
        decision = dict(status="pending_rights_holder_authority", license="CC-BY-4.0", domains=["robotic_arm"])
        with patch("phi_jepa.simulation.freeze.read", return_value=decision):
            with self.assertRaisesRegex(ValueError, "supported grant"):
                verify_license(config)
        # A name and selected license alone do not establish authority.
        decision.update(status="granted", grantor="TEST_ONLY")
        with patch("phi_jepa.simulation.freeze.read", return_value=decision):
            with self.assertRaisesRegex(ValueError, "supported grant"):
                verify_license(config)


if __name__ == "__main__":
    unittest.main()
