"""Bounded CPU development check: five scenes, three runs each, no MJX."""
from contextlib import ExitStack
from dataclasses import asdict
from hashlib import sha256
import time
from unittest.mock import patch
from phi_jepa.artifacts import code_provenance
from phi_jepa.simulation.common import ROOT, Scenario, read, write
from phi_jepa.simulation.pipeline import adapter, comparison
from phi_jepa.simulation.scope import RELEASE_ENGINES


def main():
    output = ROOT / "dataset-runs/four-domain-solver-check"
    output.mkdir(exist_ok=False)
    plan = dict(max_rollouts=15, max_wall_seconds=300, domains=list(RELEASE_ENGINES),
                selection="first admitted smoke scenario per scene/subfamily in original partition order",
                runs=["original timestep", "serial repeat", "half timestep with tighter solver"],
                mujoco_override=dict(iterations=200, tolerance=1e-12),
                pybullet_override=dict(numSolverIterations=200),
                admission_thresholds="unchanged pipeline.comparison", development_only=True)
    write(output / "plan.json", plan)
    started = time.monotonic(); rows = []; calls = 0
    for domain in RELEASE_ENGINES:
        path = ROOT / "dataset-runs/final" / domain / ("corrected-smoke" if domain == "tethered_load" else "smoke")
        config = read(path / "config.json"); dt = config["time"]["default_timestep_s"]
        seen = set()
        for data in read(path / "partitions.json"):
            if data["subfamily"] in seen or read(path / "receipts" / (data["group"] + ".json"))["status"] != "accepted":
                continue
            seen.add(data["subfamily"])
            scenario = Scenario(**data); runs = []
            for index, step in enumerate((dt, dt, dt / 2)):
                if calls >= plan["max_rollouts"] or time.monotonic() - started > plan["max_wall_seconds"]:
                    raise RuntimeError("bounded check budget exhausted; keep partial artifacts")
                with ExitStack() as stack:
                    if index == 2 and RELEASE_ENGINES[domain] == "mujoco":
                        from phi_jepa.simulation import engines
                        name = "arm_model" if domain == "robotic_arm" else "tether_model"
                        original = getattr(engines, name)
                        def tighter(*args):
                            return original(*args).replace('iterations="100"', 'iterations="200"').replace('tolerance="1e-10"', 'tolerance="1e-12"')
                        stack.enter_context(patch.object(engines, name, tighter))
                    elif index == 2:
                        import pybullet
                        original = pybullet.setPhysicsEngineParameter
                        def tighter(**kwargs):
                            return original(**{**kwargs, "numSolverIterations": 200})
                        stack.enter_context(patch.object(pybullet, "setPhysicsEngineParameter", tighter))
                    calls += 1
                    result = adapter(domain).simulate(scenario, config, step)
                name = f"{domain}-{scenario.subfamily}-{index}.json"
                write(output / name, dict(rollout=asdict(result), effective_solver_override=plan["mujoco_override" if RELEASE_ENGINES[domain] == "mujoco" else "pybullet_override"] if index == 2 else None))
                runs.append(result)
            row = dict(domain=domain, subfamily=scenario.subfamily, scenario=data,
                       serial_repeat=comparison(runs[0], runs[1], domain, config["time"]["default_target_times_s"]),
                       finer_tighter=comparison(runs[0], runs[2], domain, config["time"]["default_target_times_s"]))
            rows.append(row)
            write(output / "partial-summary.json", dict(rows=rows, simulator_calls=calls))
    summary = dict(plan=plan, rows=rows, simulator_calls=calls,
                   wall_seconds=time.monotonic() - started, source=code_provenance(),
                   status="passed" if all(r[k]["passed"] for r in rows for k in ("serial_repeat", "finer_tighter")) else "failed",
                   caveat="Selected development checks, not full-distribution qualification. PyBullet tighter override is recorded separately from the unchanged authored asset description.",
                   artifacts={p.relative_to(ROOT).as_posix(): dict(bytes=p.stat().st_size, sha256=sha256(p.read_bytes()).hexdigest()) for p in output.glob("*.json")})
    write(output / "summary.json", summary)
    write(ROOT / "docs/reviews/artifacts/PDS_four_domain/solver-check.json", summary)
    print(summary["status"], "simulator calls:", calls)


if __name__ == "__main__":
    main()
