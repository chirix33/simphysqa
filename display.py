from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

from problems import get_problem


def print_summary(result) -> None:
    problem = get_problem(result.name)
    print(problem.title)
    print("Origin:", result.summary["backend_origin"])
    print("Neural derivative test MSE (normalised):", result.summary["training"]["test_normalized_mse"])
    print("Complete-trajectory dt/2 comparison:", result.summary["full_rollout_step_refinement_max_scaled_error"])
    for report in result.summary["phase_reports"]:
        print(f"\nPhase {report['phase']}, {report['rounds']} design round(s)")
        print(json.dumps(report["state_checks"]["governed_neural"], indent=2))
    print("\nResults directory:", result.path)


def audit_rows(result) -> list[dict]:
    """Compact public audit: design, failure evidence, Critic verdict, Python gate."""
    rows=[]
    for contract in result.contracts:
        for line in contract.audit_path.read_text().splitlines():
            record=json.loads(line)
            rows.append({"phase":record["phase"],"round":record["round"],
                "origin":record["backend_origin"],"injected_fault":record["injected_test_fault"],
                "operators":record["blueprint_used"]["operators"],
                "failed_checks":[e["evidence_id"] for e in record["machine_evidence"] if not e["passed"]],
                "critic":record["critic_response"]["verdict"],"runtime_approved":record["runtime_gate_approved"]})
    return rows


def plot_result(result, show: bool = True, save: bool = True) -> list[Path]:
    """Plot every state separately, plus a conservation/energy diagnostic.

    Baseline and governed curves use the SAME trained weights. The reference
    is the specified synthetic equation under the same policy, not field data.
    All figures identify provider provenance so fixtures cannot masquerade as
    OpenAI evaluation results.
    """
    problem=get_problem(result.name)
    directory=result.path/"figures"
    if save:
        directory.mkdir(exist_ok=True)
    paths=[]
    variants=[("ungoverned_neural","Ungoverned trained Neural ODE"),
              ("governed_neural","Governed trained Neural ODE"),
              ("governed_reference","Governed toy reference")]
    unit="days" if result.name=="sir" else "seconds"

    def finish(fig,ax,title,filename):
        for boundary in result.summary["phase_boundaries"]:
            ax.axvline(boundary,linestyle=":",label="Context change")
        ax.set_xlabel(f"Time ({unit})")
        ax.set_title(title+"\n"+result.summary["backend_origin"],fontsize=10)
        handles,labels=ax.get_legend_handles_labels()
        distinct=dict(zip(labels,handles));ax.legend(distinct.values(),distinct.keys(),fontsize=8)
        ax.grid(True,alpha=0.25)
        fig.tight_layout()
        if save:
            path=directory/filename;fig.savefig(path,dpi=140);paths.append(path)
        if show:
            plt.show()
        plt.close(fig)

    for j,(name,state_unit) in enumerate(zip(problem.state_names,problem.state_units)):
        fig,ax=plt.subplots(figsize=(8,4.5))
        for variant,label in variants:
            ax.plot(result.times,result.trajectories[variant][:,j],label=label,
                    linestyle="--" if variant=="governed_reference" else "-")
        if result.name=="driving":
            ax.axhline(problem.default_parameters["speed_limit"],linestyle="-.",label="Speed limit")
        if result.name=="reactor" and name=="temperature":
            ax.axhline(problem.default_parameters["temperature_limit"],linestyle="-.",label="Temperature limit")
        ax.set_ylabel(f"{name} ({state_unit})")
        finish(fig,ax,problem.title+": "+name,f"state_{name}.png")
    if result.name in ("reactor","sir","oscillator"):
        fig,ax=plt.subplots(figsize=(8,4.5))
        for variant,label in variants:
            states=result.trajectories[variant]
            if result.name=="reactor":
                value=states[:,0]+states[:,1]-1;ylabel="A+B-1 (mol/L)";title="Material-balance residual"
            elif result.name=="sir":
                value=states.sum(1)-1;ylabel="S+I+R-1";title="Population-balance residual"
            else:
                value=problem.energy(states,result.contracts[0].parameters);ylabel="Energy (J)";title="Specified mechanical energy"
            ax.plot(result.times,value,label=label,linestyle="--" if variant=="governed_reference" else "-")
        ax.set_ylabel(ylabel)
        finish(fig,ax,title,"invariant.png")
    fig,ax=plt.subplots(figsize=(8,4.5))
    h=result.training_history
    ax.plot([r["epoch"] for r in h],[r["train_normalized_mse"] for r in h],label="Train")
    ax.plot([r["epoch"] for r in h],[r["validation_normalized_mse"] for r in h],label="Validation")
    ax.set_yscale("log");ax.set_xlabel("Epoch");ax.set_ylabel("Normalised derivative MSE")
    ax.set_title(problem.title+"\nTraining-only normalisation; validation checkpoint selection",fontsize=10)
    ax.legend();ax.grid(True,alpha=0.25);fig.tight_layout()
    if save:
        path=directory/"training_curve.png";fig.savefig(path,dpi=140);paths.append(path)
    if show:plt.show()
    plt.close(fig)
    return paths
