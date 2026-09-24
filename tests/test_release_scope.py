"""Release isolation without running deferred MJX or production generation."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from phi_jepa.simulation.common import ROOT, read
from phi_jepa.simulation.scope import RELEASE_ENGINES, check_release_scope, check_release_partition
from phi_jepa.simulation.pipeline import run
from phi_jepa.simulation.release import release_gates


class ReleaseScopeTests(unittest.TestCase):
    def setUp(self):
        self.config = read(ROOT / "configs/dataset_release_four_domain.json")

    def test_exact_four_domains_and_disabled_generation(self):
        check_release_scope(self.config)
        for path in ("pilot_config.json", "configs/dataset_refined_pilot.json"):
            self.assertEqual(set(read(ROOT / path)["domains"]), set(RELEASE_ENGINES))
        self.assertEqual(sum(self.config["counts"]["proposed_release_per_domain"].values()) * 4, 6800)
        with self.assertRaisesRegex(ValueError, "disabled"):
            release_gates(ROOT / "configs/dataset_release_four_domain.json")

    def test_reject_extra_domain_manifest_or_registry(self):
        for key in ("domains", "validated_domain_manifests", "numeric_registries"):
            bad = copy.deepcopy(self.config)
            bad[key]["quadruped_locomotion"] = "historical"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "four"):
                check_release_scope(bad)

    def test_development_cannot_claim_train_split(self):
        with tempfile.TemporaryDirectory() as temp, patch("phi_jepa.simulation.pipeline.adapter") as engine:
            with self.assertRaisesRegex(ValueError, "development runs"):
                run(self.config, "robotic_arm", 1, Path(temp) / "new", split="train")
            engine.assert_not_called()
            self.assertFalse((Path(temp) / "new").exists())

    def test_quad_release_denied_even_with_enabled_legacy_config(self):
        config = read(ROOT / "configs/dataset_quadruped_development.json")
        config.update(final_generation_enabled=True, status="frozen")
        with tempfile.TemporaryDirectory() as temp, patch("phi_jepa.simulation.pipeline.adapter") as engine:
            with self.assertRaises(ValueError):
                run(config, "quadruped_locomotion", 1, Path(temp) / "new", "release", split="train")
            engine.assert_not_called()
            self.assertFalse((Path(temp) / "new").exists())

    def test_partition_rejects_development_and_foreign_records(self):
        manifest = dict(status="release_partition", identity=dict(mode="release", domain="robotic_arm", split="train"))
        record = dict(input=dict(domain="robotic_arm"), metadata=dict(split="train"))
        check_release_partition(manifest, [record], "robotic_arm", "train")
        for domain, split in (("quadruped_locomotion", "train"), ("robotic_arm", "development")):
            bad = dict(input=dict(domain=domain), metadata=dict(split=split))
            with self.assertRaises(ValueError):
                check_release_partition(manifest, [bad], "robotic_arm", "train")
        manifest["status"] = "development_only"
        with self.assertRaises(ValueError):
            check_release_partition(manifest, [record], "robotic_arm", "train")

    def test_mislabeled_manifest_and_registry_fail_release_gate(self):
        config = copy.deepcopy(self.config)
        config.update(status="frozen", final_generation_enabled=True, asset_license="TEST_ONLY")
        config_path = ROOT / "configs/dataset_release_four_domain.json"
        for wrong in ("manifest", "registry"):
            def lookup(path):
                if path == config_path:
                    return config
                if "dataset_domains" in str(path):
                    return dict(domain="quadruped_locomotion" if wrong == "manifest" else Path(path).stem,
                                status="validated_frozen", asset_license_status="granted",
                                calibration_path="fixture", checks=[dict(status="pass")])
                return dict(domain="quadruped_locomotion")
            with self.subTest(wrong=wrong), patch("phi_jepa.simulation.release.read", side_effect=lookup), \
                    patch("phi_jepa.simulation.release.subprocess.run") as tracked, \
                    patch("phi_jepa.simulation.release.subprocess.check_output", return_value=""), \
                    patch("phi_jepa.simulation.pipeline.validate_dataset", return_value=dict(groups=1)):
                tracked.return_value.returncode = 0
                with self.assertRaisesRegex(ValueError, "identity mismatch|registry domain mismatch"):
                    release_gates(config_path)


if __name__ == "__main__":
    unittest.main()
