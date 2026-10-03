# P12 shared local answer interface — 29 September 2026

Authority: the user's explicit implementation and bounded-debugging request in
this chat supersedes the historical decision to retain the fence-prone prompt.
No scientific architecture, enrichment, target, tolerance, held-out selection,
or paper change is authorized. The original local model lock and old diagnostics
remain historical; a new interface uses the same pinned models and settings.

1. Use a versioned common public-only prompt with prominent observation cutoff
   and absolute target times. Historical observations, controls and future public
   interventions remain complete. Persistence is allowed. The dummy example is
   explicitly unrelated to the current question. The final output is a compact
   JSON object keyed by every exact target ID, in public specification order.
2. The only generated target fields are `status`, `value`, `reason`. The adapter
   attaches all bindings from the immutable public specification and provides an
   empty narrative string. It never invents or edits a prediction, infers an
   event, or consults a reference. The original canonical parser remains the
   final acceptance boundary, including finite values and genuine Booleans.
3. XGrammar 0.1.19 compiles each full schema, including required keys, exact
   vector dimensions and supported/unsupported branches. JSON lexical validity
   alone does not imply finite IEEE values: `1e999` is an explicitly tested
   decoder limitation, rejected by the unchanged final parser. Its fixed key
   order is disclosed in the prompt; the adapter itself accepts arbitrary order.
4. Qwen thinking-on remains one model generation with its native template and
   total 2,048-token budget. The logits processor is inactive until generated
   `</think>`; it constrains only the subsequent final answer. No forced marker,
   reasoning truncation, extra generation call or hidden thinking-off fallback.
   Qwen thinking-off and Llama retain their 1,024-token caps. All retain original
   sampling, seed, BF16, SDPA, context reserve and 120-second request limit.
5. Decoder dependencies are pinned in an additive isolated directory, preserving
   the existing PyTorch 2.7.1+cu128 / Transformers 4.51.3 core environment. No model
   or fine-tuning download, paid API request, or expanded-study run is performed.
6. Round one exposed a runtime integration defect: the XGrammar CUDA/Triton mask
   requires a C compiler absent in WSL. Eight Qwen-direct runtime failures are
   retained and charged against the 48-attempt cap. Do not run other conditions
   on that known-broken path. The single allowed correction uses XGrammar's
   CPU mask kernel and copies masked logits back to the GPU. Transfer and mask
   overhead count in request latency. Actual CUDA-tensor tests verify this path
   before round two. The prompt and model settings do not change between rounds.
7. The same eight original diagnostic validation cases are used across all three
   corrected conditions. The first model load starts a persisted two-hour wall
   window; it is never renewed on resume or round change. Requests reserve an
   attempt before compilation/generation. Unresolved attempts are not retried.
   A process lock and GPU occupancy preflight serialize workers. The embedding
   completion report and actual GPU process query confirmed no active embedding
   worker before generation. Second-round outputs have separate paths.
8. Evaluation is a separately launched process using validation references only.
   Report failures in denominators, coverage, abstentions, numeric/Boolean
   correctness, exact repetition of any observed/last value, and a disclosed
   hold-last control. Boolean persistence is copying an observed Boolean, not a
   physical inference. Neither low accuracy nor abstention authorizes retuning.

Native artifacts: `/home/aashraf/phi-jepa/p12-answer-interface-01`.
Export: `docs/reviews/artifacts/P12_answer_interface/`.
The conclusion report records the actual measurements and freeze recommendation.

Post-run offline corrections: canonical artifact JSON sorting changed the
grammar's property order relative to the prompt, although the unordered schema
and canonical parser accepted the generated answers. The final implementation
stores an exact ordered schema string and verifies its identity after reload.
An all-unsupported actual-tokenizer check then exposed slow matching of the
ambiguous `.*\S.*` reason pattern. Replacing it with `\S[\s\S]*` requires a
non-whitespace first character and eliminates that observed slow path; the
canonical parser still checks nonempty reasons. Both changes have offline
coverage, not a third model round. They are versioned v1.1 and do not rewrite
the executed v1 CPU-mask results or original model registry.

The user selected **planning a separate qualification with a larger thinking
budget** after all eight thinking-on cases exhausted 2,048 tokens before their
final marker. The disabled proposal is
`configs/p12_answer_interface_followup.proposed.json`: one 24-attempt round,
same eight validation cases, thinking-on 8,192 total tokens / 360 seconds,
direct conditions unchanged, two-hour shared model window. This is a proposed
compute condition, not new execution authorization or a renewed old budget.
