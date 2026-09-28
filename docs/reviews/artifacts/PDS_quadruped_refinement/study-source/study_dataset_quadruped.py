"""Bounded fixed-clock MJX refinement/OFAT study; every failure is retained."""
import argparse
import copy
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import platform
import shutil
import time
import traceback
from phi_jepa.artifacts import code_provenance, digest
from phi_jepa.simulation.common import ROOT, read, write
from phi_jepa.simulation.sampling import sample
from phi_jepa.simulation.mjx import MjxAdapter
from phi_jepa.simulation.quadruped import settings, synchronized_comparison
from phi_jepa.simulation.pipeline import comparison


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,default=ROOT/"configs/quadruped_refinement_study.json")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--baseline-only",action="store_true")
    args=parser.parse_args()
    plan=read(args.study)
    base=read(ROOT/"pilot_config.json")
    base["quadruped_settings"]={"controller_period_s":plan["controller_period_s"]}
    base["quadruped_trace_interval_s"]=plan["trace_interval_s"]
    scenario=replace(sample(base,"quadruped_locomotion",0,"nominal_qualification"),event_start=plan["event_start_s"],parameters=plan["nominal_parameters"])
    candidates=plan["candidates"][:1] if args.baseline_only else plan["candidates"]
    for candidate in candidates:
        if len(candidate["overrides"])>1: raise ValueError("OFAT requires at most one override from baseline")
        settings({**base["quadruped_settings"],**candidate["overrides"]})
        if not candidate["name"].replace("_","").isalnum(): raise ValueError("invalid candidate name")
    if len({c["name"] for c in candidates})!=len(candidates): raise ValueError("duplicate candidate")
    if plan["timesteps_s"] != [.001,.0005,.00025]: raise ValueError("required refinement sequence changed")
    args.output.mkdir(parents=True,exist_ok=False)
    source=code_provenance()
    source["study_runner_sha256"]=sha256(Path(__file__).read_bytes()).hexdigest()
    write(args.output/"plan.json",dict(study=plan,base_config=base,scenario=asdict(scenario),code=source,python=platform.python_version(),platform=platform.platform()))
    for path in (ROOT/"src/phi_jepa/simulation/mjx.py",ROOT/"src/phi_jepa/simulation/quadruped.py",ROOT/"src/phi_jepa/simulation/scenes.py",Path(__file__)):
        shutil.copy2(path,args.output/path.name)
    started=time.perf_counter()
    report=dict(status="running",candidates=[],simulations=0,qualified_candidate=None,source=source,plan_sha256=digest(plan),scope="nominal development only; varied scenarios unrun")

    def within_budget():
        disk=sum(f.stat().st_size for f in args.output.rglob("*") if f.is_file())
        return (report["simulations"]<plan["max_simulations"] and time.perf_counter()-started<plan["max_wall_seconds"] and disk<plan["max_disk_gib"]*2**30 and shutil.disk_usage(args.output).free>=plan["minimum_free_disk_gib"]*2**30)

    for candidate in candidates:
        cfg=copy.deepcopy(base)
        cfg["quadruped_settings"].update(candidate["overrides"])
        result=dict(**candidate,runs=[],comparisons=[],qualified=False)
        report["candidates"].append(result)
        rollouts=[]
        timesteps=list(plan["timesteps_s"])
        for dt in timesteps:
            if not within_budget():
                report["status"]="budget_exhausted"
                break
            report["simulations"]+=1
            name=f"{candidate['name']}-{dt:.7f}.json"
            try:
                rollout=MjxAdapter().simulate(scenario,cfg,dt)
                write(args.output/name,asdict(rollout))
                diag={k:v for k,v in rollout.diagnostics.items() if k not in ("trace","experiment")}
                result["runs"].append(dict(timestep_s=dt,artifact=name,sha256=sha256((args.output/name).read_bytes()).hexdigest(),diagnostics=diag))
                if rollouts:
                    result["comparisons"].append(dict(timesteps_s=[rollouts[-1].diagnostics["integration_timestep_s"],dt],labels=comparison(rollouts[-1],rollout,scenario.domain),synchronized=synchronized_comparison(rollouts[-1].diagnostics,rollout.diagnostics)))
                rollouts.append(rollout)
                # Add one finer run only for surviving locomotion with decreasing
                # state differences that still exceed the fixed label tolerances.
                if len(rollouts)==3 and not result["comparisons"][-1]["labels"]["passed"]:
                    old,new=result["comparisons"][-2:]
                    channels=("base_position","base_orientation","joint_position","joint_velocity")
                    settling=all(new["synchronized"]["channels"][k]["rms_error"]<old["synchronized"]["channels"][k]["rms_error"] for k in channels)
                    if settling and all(r.diagnostics["nominal_locomotion_qualified"] for r in rollouts[-2:]):
                        timesteps.append(plan["optional_finer_timestep_s"])
                        result["finer_reason"]="Last two runs locomote and all four state RMS differences decrease, but label tolerances remain unmet."
                print(candidate["name"],dt,diag["forward_displacement_m"],diag["fall_by_T"],flush=True)
            except Exception:
                failure=dict(timestep_s=dt,artifact=name,error=traceback.format_exc())
                write(args.output/(name+".failure.json"),failure)
                result["runs"].append(failure)
                print(candidate["name"],dt,"ERROR",failure["error"],flush=True)
                break
            finally:
                import jax
                jax.clear_caches()
            report["wall_seconds"]=time.perf_counter()-started
            write(args.output/"summary.json",report)
        if len(rollouts)>=3 and len(rollouts)==len(result["runs"]):
            result["qualified"]=bool(result["comparisons"][-1]["labels"]["passed"] and all(r.diagnostics["nominal_locomotion_qualified"] for r in rollouts[-2:]))
        if result["qualified"] and report["qualified_candidate"] is None:
            report["qualified_candidate"]=candidate["name"]
            cfg.pop("quadruped_trace_interval_s")
            cfg["time"]["default_timestep_s"]=rollouts[-2].diagnostics["integration_timestep_s"]
            cfg["limits"]["max_run_wall_seconds"]=3600
            write(args.output/"qualified-pilot-config.json",cfg)
        report["wall_seconds"]=time.perf_counter()-started
        write(args.output/"summary.json",report)
        if report["status"]=="budget_exhausted": break
    if report["status"]=="running": report["status"]="completed"
    write(args.output/"summary.json",report)
    print("Study",report["status"],"nominal qualification:",report["qualified_candidate"],flush=True)


if __name__=="__main__": main()
