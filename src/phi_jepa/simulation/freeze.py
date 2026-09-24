"""Verify the reviewed experiment independently of the production enable switch."""
from hashlib import sha256
import importlib.metadata
import subprocess
from .common import ROOT, read
from phi_jepa.artifacts import code_provenance

CONTRACT_KEYS = ("spec_version", "master_seed", "counts", "time", "domains",
                 "model_data_contract", "integration_timesteps_s", "sampling",
                 "numeric_registries", "validated_domain_manifests", "limits", "release_output",
                 "attempt_policy")


def contract(config):
    return {key: config[key] for key in CONTRACT_KEYS}


def verify_freeze(config, check_runtime=True):
    spec = config.get("experiment_freeze", {})
    path = (ROOT / spec.get("path", "missing-freeze")).resolve()
    if not path.is_relative_to(ROOT) or sha256(path.read_bytes()).hexdigest() != spec.get("sha256"):
        raise ValueError("release freeze checksum mismatch")
    frozen = read(path)
    if contract(config) != frozen["generation_contract"]:
        raise ValueError("release experiment differs from frozen settings")
    current = code_provenance()["source_files"]
    if {name: current.get(name) for name in frozen["source"]["source_files"]} != frozen["source"]["source_files"]:
        raise ValueError("generator source differs from frozen source")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", frozen["source"]["git_commit"], "HEAD"], cwd=ROOT, capture_output=True)
    if ancestor.returncode:
        raise ValueError("frozen source revision is not an ancestor of checkout")
    for name, expected in frozen["files"].items():
        artifact = (ROOT / name).resolve()
        if not artifact.is_relative_to(ROOT) or sha256(artifact.read_bytes()).hexdigest() != expected:
            raise ValueError("frozen artifact mismatch: " + name)
    if check_runtime:
        for name, version in frozen["runtime_packages"].items():
            if importlib.metadata.version(name) != version:
                raise ValueError("release runtime package mismatch: " + name)
    return frozen


def verify_license(config):
    """Require an explicit recorded grant; the enable flag is not permission."""
    decision = read(ROOT / config["licensing_decision"])
    if (decision.get("status") != "granted" or not decision.get("grantor") or
            decision.get("authority_confirmed") is not True or decision.get("code_license") != "MIT" or
            not decision.get("authorization_evidence") or not decision.get("license") or
            decision["license"] != config.get("asset_license")):
        raise ValueError("asset licensing decision lacks an explicit supported grant")
    if set(decision.get("domains", [])) != set(config["domains"]):
        raise ValueError("asset grant does not cover the four-domain release")
