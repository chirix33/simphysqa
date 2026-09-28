# End-to-end question/answer runner completion

Branch: `full-phi-jepa-from-dataset`. Base HEAD:
`d2e9fe3daba63cc0b5295fa108177628c4319098`. Changes are local and uncommitted;
pre-existing staged P11 files are preserved. No push, checkpoint replacement,
training, new paid calls or historical report changes occurred.

## Implemented behavior

`tools/answer_pipeline.py` provides list, run, explicit train-and-run, resume,
and separate evaluate commands. It selects the same three held-out questions
per requested domain by default, recomputes selected-checkpoint inference,
invokes the final answer interface, prints prose and writes `report.md` plus
per-case JSON/text and provenance. Missing checkpoints are unavailable rather
than automatically trained or substituted. Model failures remain in denominators.

The user's final policy is fresh vanilla `gpt-5.6-sol` API calls by default,
with a USD 5 aggregate per-run ceiling. Phi-JEPA final answers prefer an exact
compatible cache; its numerical predictions are fresh. CLI overrides permit
fresh Phi-JEPA final answers or explicitly cached vanilla runs. API reservations
and token/attempt caps reuse the existing budget adapter. No HTTP endpoint,
model profile, original prompt, parser or readout semantics changed.

Deployment workers enforce the existing reference-open guard. The provider
worker obtains credentials before installing that guard, only when calls are
enabled. Evaluator references are opened in a separate process after answers
are fixed. Assessment is not recomputed; underlying assessment remains partial
and uncalibrated. Human-reviewed clarification is not silently invoked.

## Affected files

- `tools/answer_pipeline.py`: orchestration, public-only inference workers,
  exact read-through caches, fresh-call bypass, budgeted provider transport,
  question/answer reports and separate evaluation.
- `src/phi_jepa/providers/openai_answer.py`: optional public request capture
  callback; cache keys and request contents are unchanged.
- `tests/test_answer_pipeline.py`: eight targeted offline behavior tests.
- `docs/Run_answers_WSL.md`: executable inference and optional training commands,
  availability, model identities, cache/live policies, artifacts and limitations.
- `docs/README.md`, `docs/Manual_WSL.md`, `docs/PROGRESS.md`, and
  `docs/decisions/Answer_runner.md`: updated entry point and durable decisions.

## Executed verification

Using `/home/aashraf/phi-jepa/.venvs/phi-core/bin/python` in WSL:

```bash
python -m unittest discover -s tests -p test_answer_pipeline.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_p04a.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_p11.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_manual_pipeline.py -v
```

**29 tests pass** (8 + 12 + 5 + 4). They cover equal case selection,
checkpoint unavailability, exact-cache identity, no historical cache writes,
fresh vanilla bypass of all caches, request capture, public-only direct inputs,
budget denial before transport, strict parsing and failure display. Fresh
provider-mode verification uses mock transport and is not new empirical evidence.
One initial standalone P04a invocation omitted `PYTHONPATH=src` and failed import;
the corrected command above passed. `git diff --check` passed.

Final four-domain check explicitly disabled new spending:

```bash
python tools/answer_pipeline.py run --domains all --max-api-usd 0 \
  --vanilla-answers cache \
  --output /home/aashraf/phi-jepa/manual-outputs/answer-runner-final-offline
# Repeated with --resume: saved successes/failures retained, only evaluation rerun.
```

All 12 fresh Phi-JEPA forecasts completed; all 12 final Phi answers were valid
exact-cache hits. Eight vanilla answers were valid cache hits; four had no valid
cache and were retained explicitly. Under unchanged evaluation, complete-answer
success was 2/12 Phi-JEPA and 6/12 cached vanilla; Phi had six unsupported target
components. These are selected-case replay measurements, not a new independent
benchmark or proof of superiority. New provider attempts/tokens/cost: **0/0/0**.
Worker elapsed time including the separate resume evaluation was **24.73 s**.

See [the readable comparison](artifacts/Answer_runner/answer-runner-final-offline/report.md),
[summary](artifacts/Answer_runner/answer-runner-final-offline/summary.json), and
[source identity](artifacts/Answer_runner/answer-runner-final-offline/source/identity.json).
Original full native run files remain under the output path above.

An additional matched appendix tethered-load check ran fresh existing custom
Coconut and CODI student checkpoints sequentially, without optimizer updates.
Their GPU-worker wall times were **11.30 s** and **10.30 s**. Coconut failed
target-count parsing; CODI generated malformed JSON. Both failures and raw tokens
remain recorded; neither was repaired. Matched Phi's cached typed answer was
valid but not completely correct. See
[custom report](artifacts/Answer_runner/answer-runner-custom-check-01/report.md).
This check predates the default fresh-vanilla setting and contains no vanilla
condition; its exact source identity/configuration is preserved separately.

## Limits and remaining work

The inference interface is working on the available four-domain checkpoints.
Existing bounded training is complete; convergence/generalization and strong
answer quality are not established. Contact-dependent targets remain unsupported
where evidence is absent. Missing-domain numerical-baseline checkpoints and
uncached public embeddings remain explicit limitations. The initial selectable
inventory is P11's prepared cases, including 12 held-out questions per domain,
not every question in the full dataset release.

Fresh real API calls were not spent merely to retest the existing transport.
The default live path has offline mocked verification and reuses the previously
live-tested provider adapter. Optional train-and-run is wired to the existing
supervised numerical stages; new learning runs were not launched for this UI
change. Custom training remains the existing explicit P10 pipeline. No unresolved
scientific choice is needed to use the requested Phi-JEPA/vanilla comparison.
