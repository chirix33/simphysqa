from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from torch import nn

from schemas import IntegrationError

DTYPE = torch.float64


def seed_everything(seed: int) -> None:
    """Reproducible CPU numerics within an environment, not deterministic LLMs."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


class DerivativeNet(nn.Module):
    """Two-layer tanh MLP with training-only input/output normalisation."""
    def __init__(self, x: torch.Tensor, y: torch.Tensor, width: int = 32):
        super().__init__()
        self.register_buffer("x_mean", x.mean(0))
        self.register_buffer("x_scale", x.std(0).clamp_min(1e-6))
        self.register_buffer("y_mean", y.mean(0))
        self.register_buffer("y_scale", y.std(0).clamp_min(1e-6))
        self.core = nn.Sequential(
            nn.Linear(x.shape[1], width), nn.Tanh(),
            nn.Linear(width, width), nn.Tanh(),
            nn.Linear(width, y.shape[1]),
        ).to(dtype=DTYPE, device="cpu")

    def normalized_prediction(self, x: torch.Tensor) -> torch.Tensor:
        return self.core((x - self.x_mean) / self.x_scale)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.normalized_prediction(x) * self.y_scale + self.y_mean


def train_network(problem, seed: int = 7, epochs: int = 400, out_dir: str | Path | None = None):
    """Generate disjoint IID splits; fit on train, select on validation, test once.

    Default sizes: 1024 training, 256 validation, 256 test states. The generator
    family is shared, so these are controlled synthetic tests, NOT an OOD claim.
    Optimiser: Adam, lr=0.005; full batch; gradient clip=5; validate every 10
    epochs; keep the lowest-validation-loss checkpoint; no test-based selection.
    """
    if epochs < 1:
        raise ValueError("epochs must be positive")
    seed_everything(seed)
    splits = {}
    for index, (name, size) in enumerate((("train", 1024), ("validation", 256), ("test", 256))):
        rng = np.random.default_rng(np.random.SeedSequence([seed, index, 2026]))
        x, y = problem.sample_training(size, rng)
        splits[name] = (torch.as_tensor(x, dtype=DTYPE), torch.as_tensor(y, dtype=DTYPE))
    x, y = splits["train"]
    net = DerivativeNet(x, y)
    optimiser = torch.optim.Adam(net.parameters(), lr=0.005)
    target = (y - net.y_mean) / net.y_scale
    best_loss, best_epoch, best_weights = float("inf"), 0, None
    history = []
    for epoch in range(1, epochs + 1):
        net.train()
        optimiser.zero_grad(set_to_none=True)
        loss = (net.normalized_prediction(x) - target).square().mean()
        if not torch.isfinite(loss):
            raise RuntimeError("Nonfinite training loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=5.0)
        optimiser.step()
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            net.eval()
            with torch.no_grad():
                vx, vy = splits["validation"]
                val = ((net(vx) - vy) / net.y_scale).square().mean().item()
            history.append({"epoch": epoch, "train_normalized_mse": loss.item(),
                            "validation_normalized_mse": val})
            if val < best_loss:
                best_loss, best_epoch = val, epoch
                best_weights = copy.deepcopy(net.state_dict())
    net.load_state_dict(best_weights)
    net.eval()
    with torch.no_grad():
        tx, ty = splits["test"]
        error = net(tx) - ty
        test_mse_per_component = error.square().mean(0).tolist()
        test_normalized_mse = ((error / net.y_scale).square().mean()).item()
    report = {
        "scenario": problem.name, "seed": seed, "epochs_requested": epochs,
        "best_epoch": best_epoch, "validation_normalized_mse": best_loss,
        "test_normalized_mse": test_normalized_mse,
        "test_mse_per_derivative_component": test_mse_per_component,
        "derivative_order": problem.state_names, "split_sizes": {k: len(v[0]) for k, v in splits.items()},
        "training_method": "supervised_derivatives_not_trajectory_loss",
        "data_origin": "authored_synthetic_generator_shared_by_all_splits",
        "architecture": "input->32 tanh->32 tanh->state_dimension; float64 CPU",
        "optimizer": "Adam lr=0.005, full batch, clip_grad_norm=5",
        "selection": "lowest validation normalized MSE; test evaluated once",
    }
    if out_dir is not None:
        directory = Path(out_dir)
        directory.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(directory / "synthetic_splits.npz", **{
            f"{name}_{axis}": tensor.numpy() for name, pair in splits.items()
            for axis, tensor in zip(("x", "dy"), pair)
        })
        torch.save(net.state_dict(), directory / "network_weights.pt")
        (directory / "training_report.json").write_text(json.dumps(report, indent=2))
        (directory / "training_history.json").write_text(json.dumps(history, indent=2))
    return net, report, history


def rk4_step(rhs: Callable, t: float, y: torch.Tensor, step: float,
             stage_guard: Callable | None = None) -> torch.Tensor:
    """Classical fourth-order Runge--Kutta. All arithmetic remains differentiable.

    No state projection is applied. Intermediate states can be guarded when a
    physical RHS is only defined in an admissible domain.
    """
    def evaluate(time, state):
        if not torch.isfinite(state).all():
            raise IntegrationError("Nonfinite intermediate state")
        if stage_guard is not None:
            stage_guard(state)
        derivative = rhs(time, state)
        if derivative.shape != y.shape or not torch.isfinite(derivative).all():
            raise IntegrationError("Wrong derivative shape or nonfinite derivative")
        return derivative
    k1 = evaluate(t, y)
    k2 = evaluate(t + step / 2, y + step * k1 / 2)
    k3 = evaluate(t + step / 2, y + step * k2 / 2)
    k4 = evaluate(t + step, y + step * k3)
    return y + step * (k1 + 2 * k2 + 2 * k3 + k4) / 6


def integrate(rhs: Callable, initial: torch.Tensor, start: float, end: float, dt: float,
              stage_guard: Callable | None = None, transition_guard: Callable | None = None,
              max_halvings: int = 16):
    """Integrate to *exact* output times; halve rejected steps, never repair states.

    This is guarded fixed-step RK4, NOT an adaptive truncation-error-controlled
    solver. Step-halving for guard violations is a separate safeguard. A dt/2
    comparison is performed elsewhere. A failed guard ultimately raises.
    """
    if not (np.isfinite([start, end, dt]).all() and end > start and dt > 0):
        raise ValueError("Require finite start < end and dt > 0")
    y = initial.clone()
    if stage_guard is not None:
        stage_guard(y)
    count = max(1, int(np.ceil((end - start) / dt)))
    times = np.linspace(start, end, count + 1)
    states = [y.clone()]
    stats = {"accepted_internal_steps": 0, "rejected_internal_steps": 0,
             "requested_dt": float(dt), "minimum_internal_step": float("inf")}

    def safe_advance(time, state, step, depth):
        try:
            candidate = rk4_step(rhs, time, state, step, stage_guard)
            if not torch.isfinite(candidate).all():
                raise IntegrationError("Nonfinite endpoint")
            if stage_guard is not None:
                stage_guard(candidate)
            if transition_guard is not None:
                transition_guard(state, candidate)
            stats["accepted_internal_steps"] += 1
            stats["minimum_internal_step"] = min(stats["minimum_internal_step"], step)
            return candidate
        except IntegrationError:
            stats["rejected_internal_steps"] += 1
            if depth >= max_halvings:
                raise IntegrationError("Step guard still fails after maximum halvings; stopped")
            half = safe_advance(time, state, step / 2, depth + 1)
            return safe_advance(time + step / 2, half, step / 2, depth + 1)
    for left, right in zip(times[:-1], times[1:]):
        y = safe_advance(float(left), y, float(right - left), 0)
        states.append(y.clone())
    return times, torch.stack(states), stats
