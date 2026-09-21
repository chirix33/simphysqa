from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ValidationError

from schemas import ProviderError, content_hash
from problems import get_problem

ROLE_INSTRUCTIONS = {
    "architect": """You are THE ARCHITECT in a bounded metacognitive Neural ODE workflow.
Design the contract structure for the supplied problem. Select the needed operators
and parameter_fields from the developer-maintained catalogues; state_order must match.
All supported operators listed for this teaching problem are necessary complementary
pieces. Do not invent operators, equations, fields, constants or executable Python.
Review previous_feedback and revise the actual design when evidence reveals a defect.
List missing_information rather than guessing. A valid JSON schema is not a physics
proof. Return only the requested structured Blueprint with a brief public revision
summary, not a hidden chain-of-thought transcript.""",
    "executor": """You are THE EXECUTOR. Populate the Architect's dynamic contract schema.
For EVERY parameter, copy value, unit and source_id exactly from the supplied facts.
A fact is a toy assumption, not a measured or independently verified real-world fact.
When a numeric source is absent, set value=null; never estimate or invent a safety
threshold. Do not change the schema, add keys, write Python, or claim verification.
Return only the requested structured contract instance.""",
    "critic": """You are THE CRITIC, reviewing a candidate Neural ODE contract.
Use the original problem, blueprint, values, and ACTUAL machine_evidence. Any failed
machine test requires revise (or abstain when information is missing). You cannot
waive a failure, change a test, or assert a test ran when it did not. Cite real
machine evidence_ids. All numerical and semantic tests passing with no unresolved
issue should produce approve. Identify concise concrete issues and design changes,
not private deliberation. Tests establish only their stated finite scope, never
universal safety. Unknown source values require abstention, not hallucinated repairs.
Return only the requested structured Critique.""",
}


class Backend:
    """Small interface keeps agent roles separate from the numerical simulator."""
    origin = "abstract"
    def ask(self, role: str, response_model: type[BaseModel], payload: dict) -> BaseModel:
        raise NotImplementedError

    @property
    def usage(self) -> dict:
        return {"origin": self.origin}


class FixtureBackend(Backend):
    """DETERMINISTIC AUTHOR-WRITTEN TEST DATA, NOT an LLM or saved OpenAI output.

    This lets users test Python, neural training, and repair-loop wiring without
    credentials. It deliberately does not measure real Critic/Architect ability.
    """
    origin = "authored_offline_fixture_not_openai"
    def __init__(self):
        self.calls = 0

    def ask(self, role, response_model, payload):
        self.calls += 1
        problem = get_problem(payload["problem"]["scenario_id"])
        if role == "architect":
            data = problem.canonical_blueprint().model_dump()
            data["revision_summary"] = (
                "AUTHORED FIXTURE: restore supported operator composition after rejection."
                if payload.get("previous_feedback") else
                "AUTHORED FIXTURE: initial canonical supported composition."
            )
        elif role == "executor":
            facts = payload["problem"]["facts"]
            data = {name: facts.get(name, {"value": None, "unit": problem.catalogue[name]["unit"],
                                          "source_id": "missing"})
                    for name in response_model.model_fields}
        elif role == "critic":
            evidence = payload["machine_evidence"]
            failed = [item for item in evidence if not item["passed"]]
            data = {"verdict": "revise" if failed else "approve",
                    "issues": [item["summary"] for item in failed],
                    "evidence_ids": [item["evidence_id"] for item in evidence],
                    "suggested_changes": ["Use the supported operator set and exact supplied facts."] if failed else [],
                    "decision_summary": "AUTHORED FIXTURE: decision follows Python tests; not an LLM evaluation."}
        else:
            raise ValueError(f"Unknown role: {role}")
        return response_model.model_validate(data)

    @property
    def usage(self):
        return {"origin": self.origin, "fixture_role_calls": self.calls, "paid_api_requests": 0}


class OpenAIBackend(Backend):
    """Real OpenAI Responses API with Pydantic Structured Outputs.

    Uses client.responses.parse(..., text_format=Model). No temperature or seed
    parameters are assumed, making model substitution less brittle. SDK retries
    are bounded. Call counts are logical requests, not a billing guarantee.
    Request/response caches contain prompts: keep the output directory private
    when using private data. API keys and request headers are never persisted.
    """
    origin = "openai_api"
    def __init__(self, model: str = "gpt-4.1-mini-2025-04-14", api_key: str | None = None,
                 out_dir: str | Path = "results/openai_requests", max_calls: int = 120,
                 max_output_tokens: int = 4096, use_cache: bool = True,
                 client=None, timeout: float = 90.0):
        if max_calls < 1 or max_output_tokens < 256:
            raise ValueError("Invalid call/token budget")
        self.model, self.max_calls = model, max_calls
        self.max_output_tokens, self.use_cache = max_output_tokens, use_cache
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.calls, self.cache_hits, self.input_tokens, self.output_tokens = 0, 0, 0, 0
        if client is not None:  # Dependency injection is used only by offline transport tests.
            self.client = client
        else:
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ProviderError("No OPENAI_API_KEY. Use Colab Secrets/getpass, or explicitly select manual/fixture mode.")
            try:
                from openai import OpenAI
            except ImportError as error:
                raise ProviderError("Install the official SDK: %pip install 'openai>=1.68,<3'") from error
            self.client = OpenAI(api_key=key, timeout=timeout, max_retries=2)

    def ask(self, role, response_model, payload):
        instruction = ROLE_INSTRUCTIONS[role]
        request = {"role": role, "model": self.model, "instructions": instruction,
                   "payload": payload, "json_schema": response_model.model_json_schema(),
                   "max_output_tokens": self.max_output_tokens, "store": False}
        key = content_hash(request)
        path = self.out_dir / f"{role}_{key}.json"
        if self.use_cache and path.exists():
            data = json.loads(path.read_text())
            if data.get("origin") != "openai_live":
                raise ProviderError("Cache provenance mismatch; refusing to use non-OpenAI cache")
            self.cache_hits += 1
            return response_model.model_validate(data["parsed_response"])
        if self.calls >= self.max_calls:
            raise ProviderError(f"Logical API request budget {self.max_calls} reached; stopped")
        self.calls += 1
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[{"role": "system", "content": instruction},
                       {"role": "user", "content": json.dumps(payload, allow_nan=False)}],
                text_format=response_model,
                max_output_tokens=self.max_output_tokens,
                store=False,
            )
        except Exception as error:
            # Do not dump the SDK request, authorization headers or a client object.
            status = getattr(error, "status_code", None)
            explanation = {
                400: "Check model support, schema, token settings, or request arguments.",
                401: "API key authentication failed; a ChatGPT login is not an API key.",
                403: "The API project/account does not have permission.",
                404: "The selected API model is unavailable to this project. Change model explicitly.",
                429: "Check API quota/billing and rate limits; SDK retries are bounded.",
            }.get(status, "Check SDK installation, network access, timeout, or provider status.")
            raise ProviderError(f"OpenAI request failed ({type(error).__name__}, status={status}). {explanation}") from error
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.input_tokens += getattr(usage, "input_tokens", 0) or 0
            self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        status = getattr(response, "status", None)
        if status != "completed":
            raise ProviderError(f"Response status={status!r}; possibly truncated. No contract accepted. Increase token budget only explicitly.")
        for output in getattr(response, "output", []):
            for part in getattr(output, "content", []):
                if getattr(part, "type", None) == "refusal":
                    raise ProviderError("The model returned a refusal. No simulation is authorised.")
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise ProviderError("No parsed structured response was returned; no fixture fallback is permitted.")
        if not isinstance(parsed, response_model):
            parsed = response_model.model_validate(parsed)
        record = {"origin": "openai_live", "request": request,
                  "response_id": getattr(response, "id", None),
                  "returned_model": getattr(response, "model", self.model),
                  "parsed_response": parsed.model_dump(mode="json"),
                  "usage": {"input_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
                            "output_tokens": getattr(usage, "output_tokens", 0) if usage else 0}}
        path.write_text(json.dumps(record, indent=2, allow_nan=False))
        return parsed

    @property
    def usage(self):
        return {"origin": self.origin, "requested_model": self.model,
                "logical_live_requests": self.calls, "cache_hits": self.cache_hits,
                "reported_input_tokens": self.input_tokens, "reported_output_tokens": self.output_tokens,
                "note": "Counts omit tokens unavailable on failed requests; SDK retries may add HTTP attempts."}


class ManualChatGPTBackend(Backend):
    """Use ChatGPT's browser interface by copying prompts and pasting JSON replies.

    Colab calls ``input`` once per role. Paste a compact, single-line JSON object.
    The complete prompts are also saved to text files. No API billing is involved
    in this transport; ChatGPT UI usage remains subject to the user's plan limits.
    The LLM's physics is still tested by exactly the same Python verifier.
    """
    origin = "manual_chatgpt_user_pasted_unverified_provenance"
    def __init__(self, out_dir: str | Path = "results/manual_requests", input_fn: Callable = input):
        self.out_dir = Path(out_dir); self.out_dir.mkdir(parents=True, exist_ok=True)
        self.input_fn, self.calls = input_fn, 0

    def ask(self, role, response_model, payload):
        self.calls += 1
        prompt = (ROLE_INSTRUCTIONS[role] + "\n\nINPUT:\n" + json.dumps(payload, indent=2) +
                  "\n\nREQUIRED JSON SCHEMA:\n" + json.dumps(response_model.model_json_schema(), indent=2) +
                  "\nReturn ONLY a compact single-line JSON object, without Markdown fences.")
        path = self.out_dir / f"{self.calls:03d}_{role}.txt"
        path.write_text(prompt)
        print(f"\n--- COPY INTO CHATGPT ({role.upper()}) ---\n{prompt}\n--- END PROMPT ---")
        reply = self.input_fn("Paste ChatGPT's single-line JSON response here: ")
        if len(reply) > 200_000:
            raise ProviderError("Manual response exceeded the input-size limit")
        try:
            parsed = response_model.model_validate_json(reply.strip())
        except (ValidationError, ValueError) as error:
            raise ProviderError("Manual reply is not valid schema-conforming JSON; do not paste prose or fences.") from error
        path.with_suffix(".json").write_text(json.dumps({"origin": self.origin,
            "parsed_response": parsed.model_dump(mode="json")}, indent=2))
        return parsed

    @property
    def usage(self):
        return {"origin": self.origin, "manual_role_calls": self.calls, "paid_api_requests": 0}


def make_backend(mode: str, out_dir: str | Path = "results/provider", **kwargs) -> Backend:
    if mode == "fixture":
        return FixtureBackend()
    if mode == "openai":
        return OpenAIBackend(out_dir=out_dir, **kwargs)
    if mode == "manual":
        return ManualChatGPTBackend(out_dir=out_dir)
    raise ValueError("mode must be exactly 'openai', 'manual', or 'fixture'")
