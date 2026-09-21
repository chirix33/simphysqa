from .base import PROBLEMS, Phase, Problem, clip_tensor, get_problem

# Importing these registers each Problem instance into PROBLEMS.
from . import driving, rocket, reactor, oscillator, sir  # noqa: F401,E402

__all__ = ["PROBLEMS", "Phase", "Problem", "clip_tensor", "get_problem"]
