"""Two simultaneous repeats of the qualified nominal pair, before calibration."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import multiprocessing
from pathlib import Path
import time
import numpy as np
from phi_jepa.artifacts import code_provenance
from phi_jepa.simulation.common import Scenario,read,write
from parallel_quadruped_calibration import produce,EmpiricalCache
from run_qualified_quadruped_pilots import qualified_config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    config=qualified_config(args.study)
    s=Scenario(**read(args.study/"plan.json")["scenario"])
    source=code_provenance()["source_sha256"]
    directories=[args.output/str(i) for i in range(2)]
    for path in directories: path.mkdir()
    started=time.perf_counter()
    with ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context("spawn")) as pool:
        futures=[pool.submit(produce,asdict(s),config,str(path),source) for path in directories]
        completed=[f.result() for f in futures]
    summary=read(args.study/"summary.json")
    candidate=next(c for c in summary["candidates"] if c["name"]==summary["qualified_candidate"])
    differences=[]
    for path in directories:
        for run in candidate["runs"][-2:]:
            actual=EmpiricalCache(path,source).simulate(s,config,run["timestep_s"])
            expected=read(args.study/run["artifact"])
            if actual.diagnostics["experiment_hash"]!=expected["diagnostics"]["experiment_hash"]: raise AssertionError("worker experiment changed")
            maximum=0.
            for a,b in zip(actual.states,expected["states"],strict=True):
                if a["timestamp"]!=b["timestamp"]: raise AssertionError("state clocks differ")
                for x,y in zip(a["measurements"],b["measurements"],strict=True):
                    if (x["entity_id"],x["name"])!=(y["entity_id"],y["name"]): raise AssertionError("channel mismatch")
                    delta=float(np.max(np.abs(np.asarray(x["value"],dtype=float)-np.asarray(y["value"],dtype=float))))
                    maximum=max(maximum,delta)
            differences.append(dict(worker=path.name,dt_s=run["timestep_s"],maximum_saved_state_difference=maximum))
    passed=all(r["maximum_saved_state_difference"]<=1e-9 for r in differences)
    write(args.output/"summary.json",dict(passed=passed,replay_tolerance=1e-9,differences=differences,completed=completed,wall_seconds=time.perf_counter()-started,source_sha256=source,role="Same-device concurrent replay audit; four real MJX rollouts, not new nominal development candidates"))
    if not passed: raise AssertionError("concurrent replay exceeded audit tolerance")
    print("Two-worker concurrent nominal replay passed",differences,flush=True)


if __name__=="__main__": main()
