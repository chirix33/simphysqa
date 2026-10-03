"""Matched development diagnostics with independent simulator references."""
from dataclasses import asdict
from pathlib import Path
from .common import write
from .sampling import sample
from .pipeline import adapter,comparison
from .records import target_specs,labels
from phi_jepa.artifacts import code_provenance,digest

def compare_engines(config,domain,pairs,output):
    if domain!="robotic_arm" or not 1<=pairs<=config["counts"]["cross_simulator_pilot_pairs"]: raise ValueError("bounded robotic-arm diagnostic only")
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()): raise ValueError("comparison output must be a new directory")
    results=[]; dt=config["time"]["default_timestep_s"]
    for i in range(pairs):
        s=sample(config,domain,i,"cross_simulator")
        try:
            a=adapter(domain).simulate(s,config,dt)
            b=adapter(domain,"pybullet").simulate(s,config,dt)
            targets=target_specs(domain,a.states[-1]["timestamp"],a.states[-1]["measurements"])
            write(output/f"pair-{i:03d}.json",dict(scenario=asdict(s),targets=targets,mujoco=dict(states=a.states,reference_labels=labels(a.states,targets),diagnostics=a.diagnostics,engine_version=a.version,model_asset=a.asset),pybullet=dict(states=b.states,reference_labels=labels(b.states,targets),diagnostics=b.diagnostics,engine_version=b.version,model_asset=b.asset)))
            results.append(dict(index=i,status="measured",comparison=comparison(a,b,domain)))
        except Exception as exc: results.append(dict(index=i,status="failed",error=type(exc).__name__+": "+str(exc)))
    report=dict(protocol="matched development pairs; independent labels; engines need not agree exactly",attempted=pairs,measured=sum(r["status"]=="measured" for r in results),pairs=results,provenance=code_provenance(),config_hash=digest(config))
    write(output/"comparison.json",report)
    return report
