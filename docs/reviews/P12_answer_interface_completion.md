# P12 shared answer-interface conclusion — 29 September 2026

This is an eight-case validation diagnostic, not confirmation/test evidence. The original eight public cases and scientific scorer/tolerances are unchanged. No paid calls, fine-tuning, expanded study, paper edits, push or merge occurred.

## Interface status

**Partially resolved.** Compact answers, public metadata adaptation and final-answer grammar constraints are implemented. The native reasoning boundary is preserved. Actual format/contract and completion counts appear below; token-budget failures remain failures. Schema constraints cannot guarantee finite floating-point interpretation (for example, `1e999`), so the unchanged canonical parser remains mandatory.

The first round exposed a missing C compiler required by the CUDA/Triton mask path. All eight Qwen-off attempts failed before emitting a token and remain charged. The single authorized correction moved masking to the installed XGrammar CPU kernel, with transfer overhead measured. It was tested on actual CUDA tensors before round two. The other conditions were not run on the known-broken path.

**32/48 total generation attempts**, two rounds, 14.12 minutes from first model load to last result within the original 120-minute window. There were no automatic retries or output repairs. Eight repeated Qwen-off cases in round two are explicit defect retries; they are not erased by reporting the corrected condition separately.

## Corrected-round measurements

| Condition | Attempted / EOS completed | JSON / full contract | Complete correct | Supported / eligible | Abstentions |
| --- | --- | --- | --- | --- | --- |
| Llama-3.1-8B-Instruct direct | 8 / 8 | 8 / 8 | 0/8 | 40/40 | 0/40 (0.0%) |
| Qwen3-8B thinking-off | 8 / 8 | 8 / 8 | 1/8 | 40/40 | 0/40 (0.0%) |
| Qwen3-8B thinking-on | 8 / 0 | 0 / 0 | 0/8 | 0/40 | 0/40 (0.0%) |

JSON validity is strict syntactic parsing; full validity includes every required target, all field/type/shape checks, and the unchanged canonical parser. EOS completion is not correctness. Missing final answers are not abstentions. All eight questions and all 40 targets (28 numeric, 12 Boolean) remain in denominators.

| Condition | Numeric correct / eligible | Numeric evaluated | Boolean correct / eligible | Boolean evaluated |
| --- | --- | --- | --- | --- |
| hold_last | 13/28 | 28 | 7/12 | 12 |
| Llama-3.1-8B-Instruct direct | 12/28 | 28 | 7/12 | 12 |
| Qwen3-8B thinking-off | 12/28 | 28 | 7/12 | 12 |
| Qwen3-8B thinking-on | 0/28 | 0 | 0/12 | 0 |

Detailed native-unit RMSE by domain/quantity, valid-only error denominators, all target errors, failure categories and scenario grouping are in the [evaluation artifacts](artifacts/P12_answer_interface/evaluation/summary.json) and sibling condition files. No heterogeneous-unit RMSE is pooled.

## Repetition and hold-last control

Equality below is exact numeric value equality against matching entity/quantity/unit/frame channels; no rounding or tolerance. Repeating a Boolean is listed separately because equal Boolean outcomes are not evidence of copying. The hold-last control copies available last-observed target channels, including observed Booleans, without inferring events.

| Condition | Numeric = any observation / evaluated | Numeric = last observation / evaluated | Boolean = last / evaluated |
| --- | --- | --- | --- |
| Llama-3.1-8B-Instruct direct | 24/28 | 13/28 | 12/12 |
| Qwen3-8B thinking-off | 16/28 | 7/28 | 12/12 |
| Qwen3-8B thinking-on | 0/0 | 0/0 | 0/0 |

Hold-last complete-answer accuracy: **1/8**. Persistence is allowed; correct/incorrect repeats retain their ordinary scores. This small diagnostic cannot establish general forecasting superiority or an OOD result.

## Runtime and failures

| Condition | Total request s | Median / max s | Peak allocated / reserved GiB | Token / time caps | Runtime failures |
| --- | --- | --- | --- | --- | --- |
| Llama-3.1-8B-Instruct direct | 36.863 | 3.737 / 8.268 | 17.356 / 17.895 | 0 / 0 | 0 |
| Qwen3-8B thinking-off | 47.674 | 6.253 / 8.064 | 18.484 / 19.172 | 0 / 0 | 0 |
| Qwen3-8B thinking-on | 542.753 | 68.522 / 76.800 | 18.484 / 19.172 | 8 / 0 | 0 |

| Condition | Load + backend s | Schema compile s | Processor bookkeeping + mask/transfers s | Reasoning / final tokens | Cumulative attempts |
| --- | --- | --- | --- | --- | --- |
| Llama-3.1-8B-Instruct direct | 7.876 | 1.230 | 16.603 | 0 / 1225 | 8 |
| Qwen3-8B thinking-off | 8.199 | 1.358 | 18.211 | 0 / 1203 | 16 |
| Qwen3-8B thinking-on | 3.484 | 1.365 | 216.429 | 16384 / 0 | 8 |

The eight first-round runtime failures add **10.098 request seconds**. Request timing includes schema compilation, mask processing and CPU/GPU transfers; model loading/backend initialization is separate. Peak allocated/reserved values are PyTorch process measurements, excluding desktop/driver allocations. Existing per-request generation limits remain 120 seconds, 1,024 final/direct tokens or 2,048 total thinking-plus-final tokens.

## Configuration and validation

- Prompt: [p12_compact_answer_v1.json](../assets/p12_compact_answer_v1.json). Complete public problem plus cutoff/absolute-time header and unrelated dummy example.
- Adapter/schema: `src/phi_jepa/providers/compact_answer.py`; strict duplicate JSON detection; no value synthesis, Boolean inference, unit conversion, or reference input.
- Decoder: XGrammar 0.1.19 via Transformers 4.51.3; additive pinned dependencies in `/home/aashraf/phi-jepa/p12-answer-interface-deps`; CPU mask, native final-only Qwen gate, BF16/SDPA.
- Original models/tokenizers and sampling settings remain pinned by `configs/local_answers_p12.lock.json`: Qwen revision `b968826d9c46dd6066d109eabc6255188de91218`, Llama revision `0e9e39f249a16976918f6564b8830bc894c89659`; seed 11; original temperatures/top-p/top-k.
- Twenty-five offline checks passed before round two, including actual grammar rejection checks and CPU-mask application to CUDA tensors. Real tokenizer preflight passed all 24 requests, without model generations.
- The audit reconstructs all messages/input tokens, verifies raw decoding, reruns the unchanged adapter, checks native reasoning separation, all source/settings identities and durable attempt/deadline accounting.
- Exact-cache resume is verified separately after generation; no output repairs, implicit retries or replacement predictions are permitted.

Branch/base: `main` / `248575fd500947edd325836e636aebe41f9f65d0`; original uncommitted work preserved. Round-one source: `2f3f6b663e26f5b43024798a4cbdce4376e58cff845285960e8a495546fa8a4c`. Round-two executed source: `d92b118db81a4976a417ab2c5f5d6ad627e6f9c37540dd0b3d5165c26dadaed4`. Content-addressed source blobs, exact rendered messages, input token IDs, raw generations, output token IDs, parser results and per-request costs are in [the artifact export](artifacts/P12_answer_interface/verification.json).

The decoder integration follows the [versioned XGrammar HF implementation](https://github.com/mlc-ai/xgrammar/blob/v0.1.19/python/xgrammar/contrib/hf.py); the scope of enforcement was checked empirically, not inferred from generic JSON validity.

## Reproducible commands

The following are the actual generation/evaluation commands for the archived round-two source. That exact executable snapshot is `/home/aashraf/phi-jepa/p12-answer-interface-01/executed-source`. The completed run supports zero-call resume from that snapshot. Current v1.1 source intentionally fails the old generation identity check instead of silently renewing or reusing its budget. Full-study execution requires separate authorization.

```bash
export PYTHONPATH=/home/aashraf/phi-jepa/p12-answer-interface-deps:src:tests:tools
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
"$PY" -m unittest test_p12_answer_interface test_p12 test_p11 -v
"$PY" tools/p12_answer_interface.py prepare
"$PY" tools/p12_answer_interface.py preflight
# Original round-one Qwen-off run produced the retained missing-compiler failures.
# After the CPU-mask correction and CUDA-tensor test:
"$PY" tools/p12_answer_interface.py register_correction
"$PY" tools/p12_answer_interface.py preflight
"$PY" tools/p12_answer_interface.py generate --condition qwen3_8b_direct
"$PY" tools/p12_answer_interface.py generate --condition qwen3_8b_thinking
"$PY" tools/p12_answer_interface.py generate --condition llama31_8b_direct
"$PY" tools/p12_answer_interface.py evaluate
"$PY" tools/p12_answer_interface_audit.py
"$PY" tools/p12_answer_interface_report.py
"$PY" tools/p12_answer_interface.py export
```

## Final offline corrections and freeze decision

**Not ready to freeze for the expanded study.** The current final interface is `p12-compact-interface-v1.1-order-preserved`, with status `implemented_pending_validation`. The model measurements above belong to the archived round-two v1 CPU-mask configuration, not to this final offline correction.

The audit found that canonical artifact serialization sorted schema properties. XGrammar 0.1.19 follows that order, so the executed decoder emitted alphabetical keys (including reason/status/value) despite the prompt requesting target order and status/value/reason. The unordered canonical parser correctly accepted those answers; their scores stand. The final code stores an ordered `schema_json` string, verifies its identity after reload, and compiles that exact string. This matters because even semantically equivalent key orders can affect generation; no third model round was run.

The final all-unsupported tokenizer test also exposed slow matching with the ambiguous reason pattern `.*\S.*`. It was interrupted during token acceptance after over 90 seconds. The simplified pattern `\S[\s\S]*` requires a non-whitespace first character without ambiguous repeated partitions. All **24 actual-tokenizer request checks**, covering **48 supported/unsupported grammar paths**, subsequently passed with zero model calls. **26 final offline regression tests passed**. The canonical parser still checks nonempty reasons and finite values.

Final offline source SHA-256: `551ec3a54852397a8f817347093ab6a83b4c25263dec11181c91ebe0d0581617`. See [verification](artifacts/P12_answer_interface/final-offline/verification.json), [test log](artifacts/P12_answer_interface/final-offline-tests.log), and [candidate interface lock](../../configs/local_answers_p12.interface_v1.lock.json). The old model lock, enrichment artifacts, selections, scientific rules and paper remain unchanged.

Final offline verification commands, from the current checkout:

```bash
export PYTHONPATH=/home/aashraf/phi-jepa/p12-answer-interface-deps:src:tests:tools
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
"$PY" -m unittest test_p12_answer_interface test_p12 test_p11 -v
"$PY" tools/p12_answer_interface_verify_final.py
"$PY" tools/p12_answer_interface_report.py
"$PY" tools/p12_answer_interface.py export
```

The user chose **planning a separate qualification with a larger thinking budget**. The [disabled proposal](../../configs/p12_answer_interface_followup.proposed.json) uses the final v1.1 interface on the same eight validation cases across all three conditions, one round, 24 attempts, a two-hour model window, and **8,192 total tokens / 360 seconds for thinking-on**. Direct conditions retain 1,024 tokens / 120 seconds. The worst-case request-time sum is 4,800 seconds before loading/setup. This is a larger-compute thinking condition, not a compute-matched comparison. The input/output reserve must still pass before any generation.

That proposal is **not authorized for execution**. The remaining decision is whether to authorize its explicit budget and requalify the final configuration before freezing. No accuracy target is an acceptance gate; failure to forecast well does not justify further prompt tuning. No additional scientific interpretation is needed to score the current results.

**Subsequent baseline amendment:** the user added Llama-3.1-8B-Instruct CoT as a
fourth condition, separate from Llama direct. The disabled proposal now lists
32 requests on the same eight public cases. CoT means explicit reasoning prompting,
not a native Llama thinking switch. It will use the same final answer contract;
its reasoning/final boundary, token/time limits and shared-window feasibility
remain to be implemented and qualified. The measurements above and the archived
three-condition proposal are unchanged. No additional generation was launched.
