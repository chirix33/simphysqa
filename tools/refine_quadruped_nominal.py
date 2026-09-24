"""Bounded 0.125 ms check after nominal repeat instability, with two repeats.

All saved 0.25 ms nominal trajectories are retained in the comparison envelope;
there is no selection of the favorable coarse or fine realization.
"""
import argparse
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import time
from phi_jepa.artifacts import code_provenance
from phi_jepa.simulation.common import Scenario,Rollout,read,write
from phi_jepa.simulation.mjx import MjxAdapter
from phi_jepa.simulation.pipeline import comparison,budget
from run_qualified_quadruped_pilots import qualified_config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,required=True)
    parser.add_argument("--replays",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    cfg=qualified_config(args.study,development_recheck=True)
    cfg["quadruped_trace_interval_s"]=.001
    s=Scenario(**read(args.study/"plan.json")["scenario"])
    summary=read(args.study/"summary.json")
    candidate=next(c for c in summary["candidates"] if c["name"]==summary["qualified_candidate"])
    quarter=next(r for r in candidate["runs"] if r["timestep_s"]==.00025)
    parents=[args.study/quarter["artifact"]]
    coarse=[Rollout(**read(parents[0]))]
    for path in sorted(args.replays.glob("*/*.json")):
        if ".receipt." in path.name: continue
        payload=read(path)
        if payload["identity"]["dt_s"]==.00025:
            coarse.append(Rollout(**payload["rollout"])); parents.append(path)
    if len(coarse)!=3: raise ValueError("expected original quarter-ms run and both retained repeats")
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/"plan.json",dict(reason="Repeated nominal pair failed original label tolerances; finer integration now needed",max_simulations=2,max_wall_seconds=600,dt_s=.000125,config=cfg,scenario=asdict(s),parents=[dict(path=str(p.resolve()),sha256=sha256(p.read_bytes()).hexdigest()) for p in parents],source=code_provenance(),runner_sha256=sha256(Path(__file__).read_bytes()).hexdigest()))
    started=time.perf_counter()
    fine=[]
    report=dict(status="running",qualified=False,runs=[],comparisons=[],repeat=None,
                coarse_replays=[dict(a=i,b=j,labels=comparison(coarse[i],coarse[j],s.domain)) for i in range(3) for j in range(i+1,3)])
    for repeat in range(2):
        if time.perf_counter()-started>600: raise RuntimeError("finer study launch budget exceeded")
        budget(cfg,args.output)
        result=MjxAdapter().simulate(s,cfg,.000125)
        path=args.output/f"repeat-{repeat}.json"
        write(path,asdict(result))
        fine.append(result)
        report["runs"].append(dict(path=path.name,sha256=sha256(path.read_bytes()).hexdigest(),diagnostics={k:v for k,v in result.diagnostics.items() if k not in ("trace","experiment")}))
        for index,parent in enumerate(coarse):
            report["comparisons"].append(dict(coarse=index,fine=repeat,labels=comparison(parent,result,s.domain)))
        report["wall_seconds"]=time.perf_counter()-started
        write(args.output/"summary.json",report)
        print("finer nominal",repeat,result.diagnostics["forward_displacement_m"],result.diagnostics["fall_by_T"],flush=True)
        import jax
        jax.clear_caches()
    report["repeat"]=comparison(fine[0],fine[1],s.domain)
    report["qualified"]=all(r.diagnostics["nominal_locomotion_qualified"] for r in coarse+fine) and all(c["labels"]["passed"] for c in report["comparisons"]+report["coarse_replays"]) and report["repeat"]["passed"]
    report["status"]="completed"; report["wall_seconds"]=time.perf_counter()-started
    write(args.output/"summary.json",report)
    print("All-realization finer nominal qualification",report["qualified"],flush=True)


if __name__=="__main__": main()
