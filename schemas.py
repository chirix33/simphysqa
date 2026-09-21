from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model


class StrictModel(BaseModel):
    """Forbid unrecognised keys; all agent-message fields are required."""
    model_config = ConfigDict(extra="forbid")


class Blueprint(StrictModel):
    """The Architect's schema-design decision, before numerical values exist."""
    scenario_id: str
    state_order: list[str]
    operators: list[str]
    parameter_fields: list[str]
    assumptions: list[str]
    missing_information: list[str]
    revision_summary: str


class SourcedNumber(StrictModel):
    """A number is not trusted merely because the JSON is valid.

    ``None`` means the source did not supply the value. Verification then refuses
    execution; the Executor must never fill an absent value by guessing.
    """
    value: float | None = Field(allow_inf_nan=False)
    unit: str
    source_id: str


class Critique(StrictModel):
    """Public audit findings, not a request for a private reasoning trace."""
    verdict: Literal["approve", "revise", "abstain"]
    issues: list[str]
    evidence_ids: list[str]
    suggested_changes: list[str]
    decision_summary: str


class Evidence(StrictModel):
    """A result actually computed by Python, not supplied by the LLM."""
    evidence_id: str
    passed: bool
    summary: str
    details: dict[str, Any]


class ContractError(RuntimeError):
    """An unsafe, unsupported, incomplete, or unapproved contract."""


class IntegrationError(RuntimeError):
    """No admissible numerical step was found; nothing is silently clipped."""


class ProviderError(RuntimeError):
    """An API/manual-input failure. Never triggers an offline fallback."""


def canonical_json(value: Any) -> str:
    """Stable JSON suitable for hashes, cache keys, and audit records."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_contract_model(blueprint: Blueprint, catalogue: dict[str, dict]) -> type[BaseModel]:
    """Compile safe field *data* into a real, problem-specific Pydantic class.

    An allowlist, identifier validation, field-count limit and duplicate check
    prevent arbitrary attributes/code/imports from entering this construction.
    Physical correctness is checked separately in the verification functions below.
    """
    names = blueprint.parameter_fields
    if not names or len(names) > 32 or len(names) != len(set(names)):
        raise ContractError("parameter_fields must contain 1..32 unique field names")
    for name in names:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name) or name not in catalogue:
            raise ContractError(f"Unknown or unsafe parameter field: {name!r}")
    fields = {
        name: (
            SourcedNumber,
            Field(description=(
                f"{catalogue[name]['description']} "
                f"Required unit: {catalogue[name]['unit']}. "
                "Copy value, unit, and source_id from the provided facts. "
                "Use null for value when evidence is missing."
            )),
        ) for name in names
    }
    # Hashes, not model-written strings, become Python class names.
    name = "Contract_" + content_hash(blueprint)[:12]
    return create_model(name, __base__=StrictModel, **fields)


def make_evidence(identifier: str, passed: bool, summary: str, **details: Any) -> Evidence:
    return Evidence(evidence_id=identifier, passed=bool(passed), summary=summary, details=details)
