"""Two simultaneous repeats of the qualified nominal pair, before calibration."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import multiprocessing
from pathlib import Path
from hashlib import sha256
import time
import numpy as np
from phi_jepa.artifacts import code_provenance
from phi_jepa.simulation.common import Scenario,Rollout,read,write
from phi_jepa.simulation.pipeline import comparison
from parallel_quadruped_calibration import produce,EmpiricalCache
from run_qualified_quadruped_pilots import qualified_config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    runner_sha=sha256(Path(__file__).read_bytes()).hexdigest()
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
    differences=[]; label_checks=[]
    for path in directories:
        actual_pair=[]
        for run in candidate["runs"][-2:]:
            actual=EmpiricalCache(path,source).simulate(s,config,run["timestep_s"])
            expected=read(args.study/run["artifact"])
            actual_pair.append(actual)
            label_checks.append(dict(worker=path.name,kind="same_timestep_replay",dt_s=run["timestep_s"],labels=comparison(Rollout(**expected),actual,s.domain)))
            if actual.diagnostics["experiment_hash"]!=expected["diagnostics"]["experiment_hash"]: raise AssertionError("worker experiment changed")
            maximum=0.
            for a,b in zip(actual.states,expected["states"],strict=True):
                if a["timestamp"]!=b["timestamp"]: raise AssertionError("state clocks differ")
                for x,y in zip(a["measurements"],b["measurements"],strict=True):
                    if (x["entity_id"],x["name"])!=(y["entity_id"],y["name"]): raise AssertionError("channel mismatch")
                    delta=float(np.max(np.abs(np.asarray(x["value"],dtype=float)-np.asarray(y["value"],dtype=float))))
                    maximum=max(maximum,delta)
            differences.append(dict(worker=path.name,dt_s=run["timestep_s"],maximum_saved_state_difference=maximum))
        label_checks.append(dict(worker=path.name,kind="refinement_pair",labels=comparison(actual_pair[0],actual_pair[1],s.domain)))
    passed=all(r["labels"]["passed"] for r in label_checks)
    write(args.output/"summary.json",dict(passed=passed,strict_state_replay_diagnostic=all(r["maximum_saved_state_difference"]<=1e-9 for r in differences),strict_state_diagnostic_tolerance=1e-9,label_checks=label_checks,differences=differences,completed=completed,wall_seconds=time.perf_counter()-started,source_sha256=source,runner_sha256=runner_sha,role="Same-device concurrent replay audit; unchanged endpoint/event gates. Strict state equality is a separate diagnostic."))
    if not passed: raise AssertionError("concurrent replay failed original label tolerances")
    print("Two-worker concurrent nominal replay passed",differences,flush=True)


if __name__=="__main__": main()
