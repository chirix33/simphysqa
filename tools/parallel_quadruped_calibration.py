"""Bounded two-process empirical MJX cache, then ordinary dataset validation.

Only executes the original MjxAdapter, with no batching/vectorization changes.
Assembly reads content-verified real rollouts; no fixtures or fallback physics.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import asdict
from hashlib import sha256
import multiprocessing
from pathlib import Path
import shutil
import time
import traceback
from phi_jepa.artifacts import canonical, code_provenance, digest
from phi_jepa.simulation.common import ROOT, Rollout, Scenario, read, write
from phi_jepa.simulation import pipeline
from phi_jepa.simulation.sampling import allocation, sample
from run_qualified_quadruped_pilots import qualified_config


def cache_identity(scenario,config,dt,source):
    return dict(scenario=asdict(scenario),config_sha256=digest(config),dt_s=dt,source_sha256=source)


def produce(scenario_dict,config,cache,source):
    from phi_jepa.simulation.mjx import MjxAdapter
    import jax
    s=Scenario(**scenario_dict)
    cache=Path(cache)
    status=[]
    for dt in (config["time"]["default_timestep_s"],config["time"]["default_timestep_s"]/2):
        ident=cache_identity(s,config,dt,source)
        key=digest(ident)
        path=cache/(key+".json")
        receipt=cache/(key+".receipt.json")
        if receipt.exists():
            status.append(read(receipt)); continue
        started=time.perf_counter()
        try:
            rollout=MjxAdapter().simulate(s,config,dt)
            payload=dict(identity=ident,rollout=asdict(rollout))
            state="simulated"
        except Exception:
            payload=dict(identity=ident,error=traceback.format_exc())
            state="failed"
        pipeline.atomic_write(path,canonical(payload))
        rec=dict(path=path.name,sha256=sha256(path.read_bytes()).hexdigest(),state=state,wall_seconds=time.perf_counter()-started)
        pipeline.atomic_write(receipt,canonical(rec))
        status.append(rec)
        jax.clear_caches()
        if state=="failed": break
    return dict(group=s.group,results=status)


class EmpiricalCache:
    def __init__(self,path,source):
        self.path=path; self.source=source

    def simulate(self,scenario,config,dt):
        ident=cache_identity(scenario,config,dt,self.source)
        key=digest(ident)
        path=self.path/(key+".json")
        receipt=self.path/(key+".receipt.json")
        if not receipt.exists(): raise ValueError("empirical rollout unavailable; no simulator/fixture fallback")
        rec=read(receipt)
        if rec["path"]!=path.name or sha256(path.read_bytes()).hexdigest()!=rec["sha256"]: raise ValueError("empirical rollout checksum mismatch")
        payload=read(path)
        if payload["identity"]!=ident: raise ValueError("empirical rollout identity mismatch")
        if "error" in payload: raise RuntimeError("recorded simulator failure: "+payload["error"])
        result=Rollout(**payload["rollout"])
        if result.engine!="mjx" or result.diagnostics["backend"]!="gpu": raise ValueError("expected real GPU MJX rollout")
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--worker-verification",type=Path,required=True)
    parser.add_argument("--max-wall-seconds",type=float,default=7200.)
    args=parser.parse_args()
    if not read(args.worker_verification/"summary.json")["passed"]:
        raise ValueError("parallel worker replay qualification failed; calibration cannot proceed")
    if not 0<args.max_wall_seconds<=7200: raise ValueError("maximum wall budget is 7200 seconds")
    config=qualified_config(args.study)
    config.setdefault("sampling",read(ROOT/"configs/dataset_sampling.json"))
    source=code_provenance()
    smoke=read(args.output.parent/"smoke/manifest.json")
    if smoke["counts"]["attempted"]!=20 or smoke["identity"]["config_hash"]!=digest(config) or smoke["identity"]["source_hash"]!=source["source_sha256"]:
        raise ValueError("complete matching 20-case smoke evidence is required before calibration")
    runner_sha=sha256(Path(__file__).read_bytes()).hexdigest()
    scenarios=[sample(config,"quadruped_locomotion",i,"calibrate",shift,"development") for i,shift in enumerate(allocation(100,"calibrate",config))]
    args.cache.mkdir(parents=True,exist_ok=True)
    identity=dict(config_sha256=digest(config),source_sha256=source["source_sha256"],runner_sha256=runner_sha,workers=2,scenario_plan_sha256=digest([asdict(s) for s in scenarios]))
    if (args.cache/"identity.json").exists() and read(args.cache/"identity.json")!=identity: raise ValueError("cache resume identity mismatch")
    write(args.cache/"identity.json",identity)
    write(args.cache/"scenario-plan.json",[asdict(s) for s in scenarios])
    write(args.cache/"config.json",config)
    write(args.cache/"source.json",source)
    shutil.copy2(__file__,args.cache/Path(__file__).name)
    existing=args.output/"identity.json"
    if existing.exists():
        old=read(existing)
        if old["config_hash"]!=digest(config) or old["source_hash"]!=source["source_sha256"] or old["count"]!=100 or old["mode"]!="calibrate": raise ValueError("existing calibration is incompatible")
    pending=[s for s in scenarios if not (args.output/"receipts"/(s.group+".json")).exists()]
    started=time.perf_counter()
    report=dict(identity=identity,status="running",completed=[],preexisting_receipts=100-len(pending),max_wall_seconds=args.max_wall_seconds,workers=2)
    write(args.cache/"execution.json",report)
    iterator=iter(pending)
    def submit(pool):
        pipeline.budget(config,args.cache)
        if time.perf_counter()-started>args.max_wall_seconds: return None
        try: scenario=next(iterator)
        except StopIteration: return None
        return pool.submit(produce,asdict(scenario),config,str(args.cache),source["source_sha256"])
    # Two separate processes, serial coarse/refined integration inside each.
    with ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context("spawn")) as pool:
        active={f for _ in range(2) if (f:=submit(pool)) is not None}
        while active:
            done,active=wait(active,timeout=30,return_when=FIRST_COMPLETED)
            for future in done:
                report["completed"].append(future.result())
                report["wall_seconds"]=time.perf_counter()-started
                write(args.cache/"execution.json",report)
                print("simulated calibration scenarios",len(report["completed"]),"of",len(pending),flush=True)
                new=submit(pool)
                if new is not None: active.add(new)
    report["wall_seconds"]=time.perf_counter()-started
    if len(report["completed"])!=len(pending):
        report["status"]="budget_exhausted"; write(args.cache/"execution.json",report)
        raise RuntimeError("simulation budget reached; resume exact content-verified cache")
    report["status"]="simulations_completed"
    write(args.cache/"execution.json",report)
    if code_provenance()["source_sha256"]!=source["source_sha256"]: raise ValueError("source changed during simulation; cannot assemble")
    # Explicit empirical-cache injection only during assembly. The ordinary
    # pipeline still applies its scenario, schema, physics and refinement gates.
    # Its assembly wall time excludes GPU time, which execution.json records.
    original=pipeline.adapter
    cache=EmpiricalCache(args.cache,source["source_sha256"])
    try:
        pipeline.adapter=lambda domain,engine=None: cache if domain=="quadruped_locomotion" and engine is None else original(domain,engine)
        result=pipeline.run(config,"quadruped_locomotion",100,args.output,"calibrate",resume=existing.exists())
    finally:
        pipeline.adapter=original
    report["status"]="completed"; report["counts"]=result["counts"]
    report["wall_seconds_including_assembly"]=time.perf_counter()-started
    write(args.cache/"execution.json",report)
    print("calibration",result["counts"],flush=True)


if __name__=="__main__": main()
