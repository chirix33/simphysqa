from dataclasses import dataclass
from typing import Literal
from .validation import StrictFrozen, convert


@dataclass(frozen=True)
class RunConfig(StrictFrozen):
    mode: Literal["offline", "live"] = "offline"
    seed: int = 11
    model_id: str | None = None
    model_revision: str | None = None
    max_calls: int = 0
    max_output_tokens: int = 0
    max_cost_usd: float = 0.0
    max_runtime_seconds: float = 30.0
    cache_policy: Literal["disabled", "content_hash"] = "disabled"

    def __post_init__(self):
        super().__post_init__()
        if min(self.seed, self.max_calls, self.max_output_tokens, self.max_cost_usd) < 0:
            raise ValueError("seed and budgets must be nonnegative")
        if self.max_runtime_seconds <= 0:
            raise ValueError("positive runtime budget required")
        if self.mode == "offline" and (self.model_id or self.model_revision or self.max_calls or self.max_output_tokens or self.max_cost_usd):
            raise ValueError("offline mode forbids live model settings and budgets")
        if self.mode == "live" and not (self.model_id and self.model_revision and self.max_calls > 0 and self.max_output_tokens > 0 and self.max_cost_usd > 0):
            raise ValueError("live mode requires pinned model and explicit positive budgets")

    @classmethod
    def from_dict(cls, payload: dict) -> "RunConfig":
        return convert(cls, payload)
