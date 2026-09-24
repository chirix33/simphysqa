"""Budgeted development runs, atomic per-scenario shards, and explicit gates."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import copy
import json
import math
import os
import shutil
import time
import numpy as np
from phi_jepa.artifacts import canonical,digest,code_provenance
from .common import ROOT,read,write,public_record,grid_index
from .sampling import sample,allocation
from .records import build_records,labels,CHANNELS
from .validation import validate,validate_groups
from .environment import inspect_environment
from .numeric import Registry,text_pair

def adapter(domain,engine=None):
    if engine=="pybullet" or domain in ("driving","object_pushing_stacking"):
        from .bullet import BulletAdapter
        return BulletAdapter()
    if domain=="quadruped_locomotion":
        from .mjx import MjxAdapter
        return MjxAdapter()
    from .engines import MujocoAdapter
    return MujocoAdapter()

def comparison(coarse,fine,domain,target_times=(1.,2.,3.),cutoff=.2):
    if domain=="quadruped_locomotion":
        if not coarse.diagnostics.get("experiment_hash") or coarse.diagnostics["experiment_hash"]!=fine.diagnostics.get("experiment_hash"):
            raise ValueError("quadruped refinement changed experiment or lacks fixed-clock provenance")
    differences=[]
    for state in coarse.states:
        if state["timestamp"]<=cutoff: continue
        other=next(s for s in fine.states if s["timestamp"]==state["timestamp"])
        for entity,name,unit in CHANNELS[domain]:
            a=next(v["value"] for v in state["measurements"] if (v["entity_id"],v["name"])==(entity,name))
            b=next(v["value"] for v in other["measurements"] if (v["entity_id"],v["name"])==(entity,name))
            if type(a) is bool:
                delta=0. if a==b else 1.
            elif name=="orientation":
                aa=np.asarray(a); bb=np.asarray(b)
                delta=2*math.acos(float(np.clip(abs(np.dot(aa,bb))/(np.linalg.norm(aa)*np.linalg.norm(bb)),-1,1)))
            else: delta=float(np.linalg.norm(np.asarray(a)-np.asarray(b)))
            tol=0. if type(a) is bool else .01 if unit in ("m/s","rad/s") else .005
            differences.append(dict(entity=entity,quantity=name,time=state["timestamp"],error=delta,tolerance=tol))
    events_a=[(e["type"],e["start_time"]) for e in coarse.events]; events_b=[(e["type"],e["start_time"]) for e in fine.events]
    event_ok=len(events_a)==len(events_b) and all(a[0]==b[0] and abs(a[1]-b[1])<=.01+1e-10 for a,b in zip(events_a,events_b))
    for key in ("stopped_by_T","stable_stack_at_T","fall_by_T"):
        if coarse.diagnostics.get(key)!=fine.diagnostics.get(key): event_ok=False
    endpoints=[v for v in differences if v["time"] in target_times]
    if not endpoints: raise ValueError("no requested endpoints compared")
    return dict(passed=all(v["error"]<=v["tolerance"] for v in endpoints) and event_ok,max_error=max(v["error"] for v in differences),endpoint_max_error=max(v["error"] for v in endpoints),event_agreement=event_ok,worst=sorted(differences,key=lambda v:v["error"]/max(v["tolerance"],1e-10),reverse=True)[:5])

def records_at(path):
    path=Path(path)
    files=sorted((path/"shards").glob("*.jsonl")) if path.is_dir() else [path]
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            if line: yield json.loads(line)

def atomic_write(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+".partial")
    with temp.open("wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(temp,path)

def export(path, allow_pending=False):
    path=Path(path)
    gate=path/"nominal-gate.json"
    if gate.exists() and not read(gate)["qualified"]: raise ValueError("quadruped nominal locomotion export gate not passed")
    records=list(records_at(path)); validate_groups(records)
    for r in records:
        if r["metadata"]["record_origin"]!="simulation": raise ValueError("illustrative records cannot be exported")
        validate(r,admission=not allow_pending)
    for name,values in (("inputs.jsonl",[public_record(r) for r in records]),("references.jsonl",[{"sample_id":r["sample_id"],"reference":r["reference"]} for r in records]),("evaluator.jsonl",[{"sample_id":r["sample_id"],"metadata":r["metadata"]} for r in records])):
        atomic_write(path/name,b"".join(canonical(v) for v in values))
    return len(records)

def check_config(c):
    if c["counts"]["structural_ood_enabled"]: raise ValueError("structural OOD disabled")
    dt=c["time"]["default_timestep_s"]
    for key in ("default_saved_interval_s","default_cutoff_s"):
        grid_index(c["time"][key],dt)
    for t in c["time"]["default_target_times_s"]+c["time"]["quadruped_target_times_s"]:
        grid_index(t,dt)
        grid_index(t,c["time"]["default_saved_interval_s"])
    if c["counts"]["questions_per_base_scenario"]>2: raise ValueError("pilot at most two questions")

def budget(c,path):
    free=shutil.disk_usage(path).free
    if free<c["limits"]["minimum_free_disk_gib"]*2**30: raise RuntimeError("minimum disk headroom gate")
    size=sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
    if size>c["limits"]["pilot_disk_gib"]*2**30: raise RuntimeError("pilot disk budget exceeded")

def run(config,domain,count,output,mode="smoke",resume=False,engine=None,split="development",release_shift=None):
    config=copy.deepcopy(config)
    if domain in config.get("integration_timesteps_s",{}):
        config["time"]["default_timestep_s"]=config["integration_timesteps_s"][domain]
    if mode=="release":
        from .scope import check_release_scope, RELEASE_ENGINES
        check_release_scope(config)
        if domain not in RELEASE_ENGINES: raise ValueError("domain excluded from first release")
        if engine is not None and engine!=RELEASE_ENGINES[domain]: raise ValueError("release engine override forbidden")
        if split not in ("train","validation","test_id","test_ood"): raise ValueError("release requires a release split")
    elif split!="development":
        raise ValueError("development runs cannot write release splits")
    if "sampling" not in config: config["sampling"]=read(ROOT/"configs/dataset_sampling.json")
    check_config(config)
    if domain not in config["domains"]: raise ValueError("unknown domain")
    cap=config["counts"]["calibration_base_scenarios_per_domain"] if mode!="release" else max(config["counts"]["proposed_release_per_domain"].values())
    if count<1 or count>cap: raise ValueError("scenario count exceeds configured budget")
    if mode=="release" and (not config.get("final_generation_enabled") or config.get("status")!="frozen"): raise ValueError("release gate not enabled")
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    budget(config,output)
    provenance=code_provenance(); env=inspect_environment(output)
    identity=dict(config_hash=digest(config),domain=domain,count=count,mode=mode,engine=engine,split=split,release_shift=release_shift,source_hash=provenance["source_sha256"])
    identity_path=output/"identity.json"
    if identity_path.exists():
        if not resume or read(identity_path)!=identity: raise ValueError("existing run requires --resume and exact config/source identity")
    else: write(identity_path,identity)
    write(output/"environment.json",env); write(output/"config.json",config)
    write(output/"source.json",provenance)
    package=ROOT/"src/phi_jepa"
    for name in provenance["source_files"]:
        original=ROOT/name if name=="pyproject.toml" else package/name
        atomic_write(output/"source_snapshot"/name,original.read_bytes())
    shifts=[release_shift]*count if release_shift else allocation(count,mode,config)
    scenarios=[sample(config,domain,i,mode,shift,split) for i,shift in enumerate(shifts)]
    write(output/"partitions.json",[asdict(s) for s in scenarios])
    started=time.perf_counter(); accepted=0; rejected=0; resumed=0
    import psutil
    peak_rss=psutil.Process().memory_info().rss
    dt=config["time"]["default_timestep_s"]
    for index,s in enumerate(scenarios):
        budget(config,output)
        if time.perf_counter()-started>config["limits"].get("max_run_wall_seconds",1800): raise RuntimeError("wall time budget reached; --resume preserves completed scenarios")
        shard=output/"shards"/(s.group+".jsonl"); receipt=output/"receipts"/(s.group+".json")
        if receipt.exists():
            old=read(receipt)
            if old["status"]=="accepted":
                if not shard.exists() or sha256(shard.read_bytes()).hexdigest()!=old["shard_sha256"]: raise ValueError("resume shard integrity failure")
                accepted+=1
            else: rejected+=1
            resumed+=1; continue
        try:
            engine_adapter=adapter(domain,engine)
            result=engine_adapter.simulate(s,config,dt)
            refined=engine_adapter.simulate(s,config,dt/2)
            agreement=comparison(result,refined,domain,config["time"]["quadruped_target_times_s" if domain=="quadruped_locomotion" else "default_target_times_s"],config["time"]["default_cutoff_s"])
            physics=True; detail="Finite simulator state and measured domain validity checks."
            if domain=="quadruped_locomotion":
                physics=True
                detail="Finite MJX trajectory; falls remain valid physical labels. Domain-wide nominal locomotion qualification is a separate export gate."
            if domain=="driving":
                physics=result.diagnostics["min_forward_velocity"]>=-.02
                detail="No backward propulsion beyond 0.02 m/s numerical tolerance."
            if domain=="tethered_load":
                physics=result.diagnostics["min_tension_N"]>0 and result.diagnostics["max_length_error_m"]<1e-6
                detail="Positive tension at every step and length residual <1e-6 m."
            checks=[dict(name="semantic",status="pass",details="Schema, time, entity, endpoint, evidence and label checks."),dict(name="refined_timestep",status="pass" if agreement["passed"] else "fail",details=json.dumps(agreement)),dict(name="domain_physics",status="pass" if physics else "fail",details=detail)]
            records=build_records(s,result,config,provenance,checks)
            for record in records: validate(record)
            asset_hash=sha256(result.asset.encode()).hexdigest()
            atomic_write(output/"assets"/(asset_hash+"."+result.asset_format),result.asset.encode())
            write(output/"diagnostics"/(s.group+".json"),dict(scenario=asdict(s),coarse=result.diagnostics,refined=refined.diagnostics,agreement=agreement))
            if not agreement["passed"] or not physics:
                quarantine=output/"quarantine"/(s.group+".jsonl")
                atomic_write(quarantine,b"".join(canonical(r) for r in records))
                raise ValueError("quarantined: refined timestep or domain qualification failed; physical outcomes preserved")
            for record in records: validate(record,admission=True)
            raw=b"".join(canonical(r) for r in records)
            atomic_write(shard,raw)
            write(receipt,dict(status="accepted",shard_sha256=sha256(raw).hexdigest(),questions=len(records)))
            accepted+=1
        except Exception as exc:
            reject=dict(index=index,scenario=asdict(s),error=type(exc).__name__+": "+str(exc))
            with (output/"rejections.jsonl").open("ab") as f: f.write(canonical(reject)); f.flush(); os.fsync(f.fileno())
            write(receipt,dict(status="rejected",reason=reject["error"]))
            rejected+=1
        peak_rss=max(peak_rss,psutil.Process().memory_info().rss)
        print(json.dumps(dict(domain=domain,index=index+1,total=count,accepted=accepted,rejected=rejected)),flush=True)
    if domain=="quadruped_locomotion":
        evidence=[read(p) for p in (output/"diagnostics").glob("*.json")]
        qualified=any(p["coarse"].get("nominal_locomotion_qualified",False) and p["refined"].get("nominal_locomotion_qualified",False) and p["agreement"]["passed"] and p["scenario"]["shift"]=="id" for p in evidence)
        write(output/"nominal-gate.json",dict(qualified=qualified,criterion="At least one ID periodic-controller refinement pair advances >=0.2m in 3s without fall in both runs and passes numerical agreement; every exported scenario also passes its own gates. Perturbation failures remain valid labels.",release_requires_further_calibration=True))
        if not qualified:
            # Keep runnable records privately, but do not export an unqualified
            # controller as a locomotion benchmark.
            for path in (output/"shards").glob("*.jsonl"):
                atomic_write(output/"quarantine"/path.name,path.read_bytes())
            exported=0
        else: exported=export(output)
    else: exported=export(output)
    records=list(records_at(output))
    if records:
        # Domain registries fixed across query times and admitted shifts.
        registry=Registry.from_manifest(read(ROOT/config["numeric_registries"][domain])) if mode=="release" else Registry.build(public_record(records[0]),domain)
        write(output/"registry.json",registry.manifest())
        from .extracted import ExtractedAdapter,exact_key_bindings
        write(output/"extracted-adapter.json",ExtractedAdapter(registry,exact_key_bindings(registry)).manifest())
        pairs=[]
        for r in records: pairs.append(dict(sample_id=r["sample_id"],**text_pair(public_record(r),r["reference"]["label"],registry)))
        atomic_write(output/"target-texts.jsonl",b"".join(canonical(p) for p in pairs))
        write(output/"text-size.json",dict(characters=[len(p["problem_text"]) for p in pairs],utf8_bytes=[len(p["problem_text"].encode()) for p in pairs],token_counts="unavailable_until_encoder_selected",encoder_calls=0))
        write(output/"review-bundle.json",dict(schema_version="1.0.0",samples={str(i+1):r for i,r in enumerate(records[:4])}))
    files={p.relative_to(output).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob("*")) if p.is_file() and p.name!="manifest.json"}
    subgroup_counts={}
    for s in scenarios:
        key=s.subfamily+"/"+s.shift
        group=subgroup_counts.setdefault(key,dict(attempted=0,accepted=0,rejected=0))
        group["attempted"]+=1
        receipt=read(output/"receipts"/(s.group+".json")); group[receipt["status"]]+=1
    report=dict(status="development_only" if mode!="release" else "release_partition",identity=identity,counts=dict(attempted=count,accepted=accepted,rejected=rejected,questions=len(records),public_exported=exported,resumed=resumed),subgroups=subgroup_counts,wall_seconds=time.perf_counter()-started,peak_rss_bytes=peak_rss,disk_bytes=sum(p.stat().st_size for p in output.rglob("*") if p.is_file()),files=files,final_generation_enabled=mode=="release",unmet_release_gates=["all-domain calibration", "frozen committed configuration", "asset redistribution license", "domain limiting-case suite"] if mode!="release" else [],provenance=provenance)
    write(output/"manifest.json",report)
    return report

def validate_dataset(path):
    path=Path(path); report=read(path/"manifest.json")
    for name,expected in report["files"].items():
        target=(path/name).resolve()
        if not target.is_relative_to(path.resolve()) or target.is_symlink(): raise ValueError("unsafe artifact path")
        if sha256(target.read_bytes()).hexdigest()!=expected: raise ValueError("artifact checksum: "+name)
    records=list(records_at(path)); summary=validate_groups(records)
    for r in records: validate(r,admission=True)
    if summary["records"]!=report["counts"]["questions"]: raise ValueError("manifest count mismatch")
    return summary
