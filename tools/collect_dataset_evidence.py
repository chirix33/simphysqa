"""Collect actual run evidence and compact review artifacts; never invent results."""
from hashlib import sha256
from pathlib import Path
import shutil
from phi_jepa.simulation.common import ROOT,read,write,public_record
from phi_jepa.simulation.pipeline import validate_dataset,records_at
from phi_jepa.simulation.numeric import Registry
from phi_jepa.simulation.extracted import ExtractedAdapter,exact_key_bindings,adopted_contract
from phi_jepa.simulation.records import CHANNELS
from phi_jepa.artifacts import code_provenance

def main():
    dest=ROOT/"docs/reviews/artifacts/PDS"; dest.mkdir(parents=True,exist_ok=True)
    summaries=[]; sampling=read(ROOT/"configs/dataset_sampling.json")
    for domain in ("robotic_arm","driving","object_pushing_stacking","tethered_load"):
        for mode in ("smoke","calibrate"):
            folder=("corrected-"+mode) if domain=="tethered_load" else mode
            run=ROOT/"dataset-runs/final"/domain/folder
            result=validate_dataset(run); manifest=read(run/"manifest.json")
            entry=dict(domain=domain,mode=mode,path=run.relative_to(ROOT).as_posix(),counts=manifest["counts"],validation=result,wall_seconds=manifest["wall_seconds"],peak_rss_bytes=manifest["peak_rss_bytes"],disk_bytes=manifest["disk_bytes"],subgroups=manifest["subgroups"],manifest_sha256=sha256((run/"manifest.json").read_bytes()).hexdigest())
            summaries.append(entry)
            shutil.copyfile(run/"manifest.json",dest/f"{domain}-{mode}-manifest.json")
            if mode=="smoke":
                record=next(records_at(run))
                write(dest/f"{domain}-example.json",record)
                write(dest/f"{domain}-public.json",public_record(record))
                registry=Registry.from_manifest(read(run/"registry.json"))
                write(ROOT/f"configs/dataset_registries/{domain}.json",registry.manifest())
                write(ROOT/f"configs/dataset_registries/{domain}.extracted.json",ExtractedAdapter(registry,exact_key_bindings(registry)).manifest())
                asset=record["metadata"]["simulation"]["assets"][0]
                target=dest/asset["path"]; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(run/asset["path"],target)
                domain_manifest=dict(version="1.0.0",domain=domain,primary_engine=record["metadata"]["simulation"]["engine"],status="development_validated_release_pending",model=record["metadata"]["simulation"],public_channels=[{k:v for k,v in q.items() if k!="value"} for q in record["input"]["states"][0]["measurements"]],controller=record["input"]["controller"],target_definitions=record["input"]["answer_spec"],sampling=sampling,config_path="configs/dataset_refined_pilot.json" if domain in ("robotic_arm","driving") else "pilot_config.json",calibration_path=f"dataset-runs/final/{domain}/"+("corrected-calibrate" if domain=="tethered_load" else "calibrate"),asset_license_status="not_granted",unmet_release_gates=["asset redistribution license","committed frozen release configuration","five-domain qualification"],numeric_registry=f"configs/dataset_registries/{domain}.json")
                write(ROOT/f"configs/dataset_domains/{domain}.json",domain_manifest)
    quad=ROOT/"dataset-runs/quadruped-smoke-v2"
    qmanifest=read(quad/"manifest.json")
    summaries.append(dict(domain="quadruped_locomotion",mode="smoke",path=quad.relative_to(ROOT).as_posix(),counts=qmanifest["counts"],wall_seconds=qmanifest["wall_seconds"],peak_rss_bytes=qmanifest["peak_rss_bytes"],disk_bytes=qmanifest["disk_bytes"],status="failed_refinement_and_controller_gate"))
    shutil.copyfile(quad/"manifest.json",dest/"quadruped-smoke-manifest.json")
    record=next(records_at(next((quad/"quarantine").glob("*.jsonl"))))
    write(dest/"quadruped-quarantined-example.json",record)
    registry=Registry.build(public_record(record),"quadruped_locomotion")
    write(ROOT/"configs/dataset_registries/quadruped_locomotion.json",registry.manifest())
    write(ROOT/"configs/dataset_registries/quadruped_locomotion.extracted.json",ExtractedAdapter(registry,exact_key_bindings(registry)).manifest())
    write(ROOT/"configs/dataset_domains/quadruped_locomotion.json",dict(version="1.0.0",domain="quadruped_locomotion",primary_engine="mjx",implementation="jax",status="implemented_pending_validation",model=record["metadata"]["simulation"],controller=record["input"]["controller"],public_channels=[{k:v for k,v in q.items() if k!="value"} for q in record["input"]["states"][0]["measurements"]],target_definitions=record["input"]["answer_spec"],sampling=sampling,asset_license_status="not_granted",unmet_release_gates=["nominal gait stable under refinement","100-scenario calibration not run after failed smoke","asset license","frozen release config"],numeric_registry="configs/dataset_registries/quadruped_locomotion.json"))
    for name in ("environment-windows.json","environment-wsl-mjx.json","mjx-batch-profile.json","quadruped-nominal-check.json","gait-development.json","tests-windows-final.log","tests-linux-final.log"):
        source=ROOT/"dataset-runs"/name
        if source.exists(): shutil.copyfile(source,dest/name)
    shutil.copyfile(ROOT/"dataset-runs/final/arm-comparison/comparison.json",dest/"arm-comparison.json")
    schema,prompt=adopted_contract()
    summary=dict(status="implemented_pending_validation",runs=summaries,comparison=read(dest/"arm-comparison.json"),provenance=code_provenance(),extraction_schema_sha256=sha256((ROOT/"docs/assets/extract_schema.json").read_bytes()).hexdigest(),extraction_prompt_sha256=sha256(prompt.encode()).hexdigest(),final_generation_enabled=False)
    write(dest/"summary.json",summary)
    write(dest/"checksums.json",{p.relative_to(dest).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob("*")) if p.is_file() and p.name!="checksums.json"})
    print([(r["domain"],r["mode"],r["counts"]) for r in summaries])

if __name__=="__main__": main()
