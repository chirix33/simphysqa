"""Verify nominal evidence, then run the varied 20-case smoke and 100-case pilot.

No single nominal success qualifies the varied set. All varied cases retain the
ordinary per-case refinement gates and rejection accounting.
"""
import argparse
import copy
from hashlib import sha256
from pathlib import Path
from phi_jepa.artifacts import digest
from phi_jepa.simulation.common import ROOT, Rollout, read, write
from phi_jepa.simulation.pipeline import comparison, run
from phi_jepa.simulation.quadruped import settings


def qualified_config(study,development_recheck=False):
    current=study/"qualification-status.json"
    if current.exists() and not read(current)["qualified"] and not development_recheck:
        raise ValueError("later validation revoked nominal qualification; only a development recheck may proceed")
    summary=read(study/"summary.json"); plan=read(study/"plan.json")
    if summary["status"]!="completed" or summary["qualified_candidate"] is None:
        raise ValueError("nominal refinement qualification has not passed; varied pilots remain gated")
    candidate=next(c for c in summary["candidates"] if c["name"]==summary["qualified_candidate"])
    cfg=copy.deepcopy(plan["base_config"])
    cfg["quadruped_settings"].update(candidate["overrides"])
    cfg.pop("quadruped_trace_interval_s",None)
    # Only exact physics-source versions can consume this numerical evidence.
    for name in ("mjx.py","quadruped.py","scenes.py"):
        key="simulation/"+name
        if sha256((ROOT/"src/phi_jepa"/key).read_bytes()).hexdigest()!=summary["source"]["source_files"][key]:
            raise ValueError("nominal evidence is stale for physics source "+name)
    records=candidate["runs"][-2:]
    if len(candidate["runs"])<3 or any("error" in r for r in candidate["runs"]): raise ValueError("incomplete nominal sequence")
    rollouts=[]
    for record in records:
        path=study/record["artifact"]
        if sha256(path.read_bytes()).hexdigest()!=record["sha256"]: raise ValueError("nominal artifact checksum mismatch")
        rollout=Rollout(**read(path)); diag=rollout.diagnostics
        if digest(diag["experiment"])!=diag["experiment_hash"]: raise ValueError("experiment identity mismatch")
        if diag["experiment"]["controller"]!=settings(cfg["quadruped_settings"]): raise ValueError("controller settings differ")
        if diag["fall_by_T"] or diag["forward_displacement_m"]<.2: raise ValueError("nominal locomotion failed")
        rollouts.append(rollout)
    if not comparison(*rollouts,"quadruped_locomotion")["passed"]: raise ValueError("nominal numerical refinement failed")
    cfg["time"]["default_timestep_s"]=records[0]["timestep_s"]
    cfg["limits"]["max_run_wall_seconds"]=3600
    return cfg


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    config=qualified_config(args.study)
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/"nominal-evidence.json",dict(study=str(args.study.resolve()),summary_sha256=sha256((args.study/"summary.json").read_bytes()).hexdigest()))
    for mode,count in (("smoke",20),("calibrate",100)):
        result=run(config,"quadruped_locomotion",count,args.output/mode,mode)
        print(mode,result["counts"],flush=True)
        # Retain the smoke rejection fraction; calibration is a fresh set, not
        # a way to relabel smoke failures. Stop only if smoke admits no cases.
        if mode=="smoke" and not result["counts"]["accepted"]:
            raise ValueError("smoke admitted no scenarios; calibration remains gated")


if __name__=="__main__": main()
