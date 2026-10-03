"""First-release allowlist; the shared schema retains development domains."""
RELEASE_ENGINES = {
    "robotic_arm": "mujoco",
    "driving": "pybullet",
    "object_pushing_stacking": "pybullet",
    "tethered_load": "mujoco",
}


def check_release_scope(config):
    required = set(RELEASE_ENGINES)
    for key in ("domains", "validated_domain_manifests", "numeric_registries"):
        if set(config.get(key, {})) != required:
            raise ValueError(f"release {key} must select exactly the four included domains")
    for domain, engine in RELEASE_ENGINES.items():
        if config["domains"][domain]["engine"] != engine:
            raise ValueError("release engine mismatch: " + domain)


def check_release_partition(manifest, records, domain, split):
    if domain not in RELEASE_ENGINES:
        raise ValueError("domain excluded from first release")
    if split not in ("train", "validation", "test_id", "test_ood"):
        raise ValueError("development split is not release eligible")
    identity = manifest.get("identity", {})
    if (manifest.get("status") != "release_partition" or
            identity.get("mode") != "release" or identity.get("domain") != domain or
            identity.get("split") != split):
        raise ValueError("development or mismatched partition cannot enter release")
    for record in records:
        if record["input"]["domain"] != domain or record["metadata"]["split"] != split:
            raise ValueError("development or excluded-domain record in release")
