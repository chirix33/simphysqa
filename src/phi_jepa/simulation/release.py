"""Fail-closed release admission. Development runs cannot enable themselves."""
import subprocess
from hashlib import sha256
from pathlib import Path
from .common import ROOT,read

def release_gates(config_path):
    config=read(config_path)
    if not config.get("final_generation_enabled") or config.get("status")!="frozen": raise ValueError("final generation disabled: requires frozen committed release configuration")
    if not config.get("asset_license"): raise ValueError("release requires the actual granted asset license identifier/text")
    relative=Path(config_path).resolve().relative_to(ROOT)
    tracked=subprocess.run(["git","ls-files","--error-unmatch",str(relative)],cwd=ROOT,capture_output=True)
    dirty=subprocess.check_output(["git","status","--porcelain","--",str(relative)],cwd=ROOT,text=True)
    if tracked.returncode or dirty: raise ValueError("release configuration must be committed")
    required={"robotic_arm","driving","object_pushing_stacking","quadruped_locomotion","tethered_load"}
    if set(config.get("validated_domain_manifests",{}))!=required or set(config.get("numeric_registries",{}))!=required: raise ValueError("missing five-domain validated manifests/registries")
    if subprocess.check_output(["git","status","--porcelain","--","src","pyproject.toml"],cwd=ROOT,text=True): raise ValueError("release generator source must be committed")
    for domain,path in config["validated_domain_manifests"].items():
        manifest=read(ROOT/path)
        if manifest.get("status")!="validated_frozen" or manifest.get("unmet_release_gates"): raise ValueError("domain has pending validation: "+domain)
        if manifest.get("asset_license_status")!="granted": raise ValueError("asset redistribution license unresolved")
        if not manifest.get("calibration_path") or not manifest.get("checks") or any(c["status"]!="pass" for c in manifest["checks"]): raise ValueError("missing calibration/physics evidence")
        from .pipeline import validate_dataset
        summary=validate_dataset(ROOT/manifest["calibration_path"])
        if summary["groups"]<1: raise ValueError("no admitted calibration groups")
        from .numeric import Registry
        Registry.from_manifest(read(ROOT/config["numeric_registries"][domain]))
    return config

def generate(config_path,resume=False):
    from .pipeline import run,records_at,validate_dataset
    from .validation import validate_groups
    from .common import write
    config=release_gates(config_path)
    output=ROOT/config["release_output"]
    if not output.resolve().is_relative_to(ROOT): raise ValueError("release output must remain in repository")
    reports={}; all_records=[]
    for domain in config["domains"]:
        for name,count in config["counts"]["proposed_release_per_domain"].items():
            shift=name.removeprefix("ood_") if name.startswith("ood_") else "id"
            split="test_ood" if name.startswith("ood_") else name
            path=output/domain/name
            reports[domain+"/"+name]=run(config,domain,count,path,"release",resume,split=split,release_shift=shift)
            validate_dataset(path); all_records.extend(records_at(path))
    groups=validate_groups(all_records)
    result=dict(status="generated",groups=groups,partitions=reports)
    write(output/"release-manifest.json",result)
    return result
