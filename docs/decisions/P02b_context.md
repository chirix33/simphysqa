# P02b resolved decisions — 24 September 2026

The latest user instruction supersedes the initial MiniLM selection below:
use **Qwen/Qwen3-Embedding-0.6B**. User authorizes downloads and live calls with
no current budget limits and expressly authorizes the key in `OPENAI_KEY.txt`.
Use `python-dotenv` to resolve `OPENAI_API_KEY_FILE` from ignored `.env` without
copying the secret. Both local files are ignored. No secret is logged or hashed.

Qwen revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` is pinned for model and
tokenizer. Full 1024-wide E, last nonpadding token pooling, BF16 model/FP32 L2
normalization, SDPA attention, no retrieval instruction or chat template, limit
32768 tokens, no truncation/chunking. These follow the selected model's
[published usage](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B); settings are
recorded in config and verified on the RTX 5090. P remains FP32, width d.

The new isolated WSL `phi-core` uses PyTorch 2.7.1+cu128 and Transformers 4.51.3;
`configs/core-wsl-p02b.lock.txt` pins the complete installed dependency set.
CoConuT/CODI environments are unchanged. Model assets and raw provider/embedding
caches live under `/home/aashraf/phi-jepa/`, outside Git. Scripts/source are read
from the Windows checkout through WSL; this was not a native-source speed study.

The eight-record Stage 2 profile is an engineering bound under the unrestricted
user authorization: longest train and validation public input per domain;
maximum 24 attempts, 2048 output tokens per call, 120-second request timeout.
Eight calls succeeded, no retries, 57,571 input / 1,834 output tokens. At the
documented rates, usage-priced cost is USD 0.266964 (not an invoice measurement).
`gpt-5.6-sol` is both requested and returned. No immutable service snapshot is
exposed; raw public-only responses are cached to preserve this run. This is a
declared provider reproducibility limitation, not a fabricated snapshot pin.

The versioned `p02b_enrichment_v1.json` prompt produces separate notes only.
Original prompt/schema assets are preserved. 32 notes across eight records were
manually compared against public units/frames, controller/effect schedules and
answer-spec definitions: no predicted outcome or unsupported numerical value
was observed. This bounded audit does not certify arbitrary future generated
prose; unknown filling, extraction, schema repair and new numeric slots remain
disabled. Complete original inputs accompany the notes unchanged.

All 8,038 train/validation base contexts fit (5387–12750 tokens); eight enriched
contexts fit (5678–12903). 36 offline tests pass with no skips. Actual E/P checks,
cache-only resume and compact artifact hashes are in the completion report.
No forecasting quality claim follows from nonzero question sensitivity in an
untrained P. ODE sensitivity and optimizer integration belong to Stage 3.

The user subsequently selected **equal weight per question-conditioned pair**
for Stage 3. This supersedes the P02a inverse-multiplicity proposal for active
training; retain original P02a evidence and weighting candidate unchanged.

## Historical initial decisions (superseded where noted above)

# P02b context/provider decisions — 24 September 2026

Authority: the user's instruction to execute revision 4 of
`Phi_JEPA_Codex_Implementation_Plan.md` sequentially, followed by the explicit
selection of `sentence-transformers/all-MiniLM-L6-v2` and OpenAI `gpt-5.6-sol`.
Stage 1/P02a remains complete. Later stages have not started.

## Settled selection and reversible implementation settings

- Reuse P02a's complete canonical Q/C serialization, causal cutoff check and
  separately recorded public notes. Preserve every original input leaf and array.
- Resolve MiniLM model/tokenizer to revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, from the publisher's
  [revision metadata](https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2/revision/main).
  Its [configuration](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/main/sentence_bert_config.json)
  specifies 256 tokens. Use FP32, attention-mask mean pooling and L2 normalization,
  as in the publisher's [model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
  These settings are unvalidated locally; no model/tokenizer was downloaded.
- Keep exact `gpt-5.6-sol`. The [official model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
  confirms Responses and structured outputs. The fetched snapshot list exposes
  only that name, so an immutable service snapshot is not established. Record
  this limit explicitly; do not invent a dated ID or silently substitute models.
- P is a separate linear layer per accepted layout, initialized with Xavier
  uniform weights and zero bias, seed 11, FP32. Embedding width is 384; output
  width is layout.d, with no padding or truncation. This is an engineering
  implementation choice, not a cross-domain sharing claim. Stage 3 must include
  P parameters in its optimizer; Stage 2 does not implement that optimizer/ODE.
- Both augmented pair tensors share the same newly computed p and its autograd
  graph. Cache only frozen E outputs; fail on cache corruption. Exact public
  content, context mode, tokenizer output, model/tokenizer/runtime revisions and
  preprocessing settings identify E cache entries.
- Provider-attempt mechanics accept a configured attempt count/timeout and keep
  each result's usage and elapsed time. Only timeout failures retry; content
  failures stop. Unreported cost/tokens remain null. This component is not a live
  spend gate; no live adapter is enabled or implemented yet.
- Notes-only parsing reconstructs `public_input` internally. Extraction and
  unknown-slot filling are not implicitly selected. Original extraction/judge/
  answer assets remain unchanged. Structural validity cannot establish that
  arbitrary generated prose is true or excludes predicted answers semantically;
  prompt design and live semantic qualification remain pending.

## Unresolved gates

The accepted full contexts were previously measured at roughly 15k–30k
characters. Those are P02a character counts, not current MiniLM token counts.
MiniLM's short-context limit therefore needs a measured compatibility check.
Until a new policy is reviewed, reject overlength input without truncation,
summarization or removal. Asked whether to prepare a complete-token-coverage
chunking/pooling proposal or leave the decision to the planner. Chunk pooling
would alter contextual encoding and is not authorized by the model selection
alone; it cannot be described as information-lossless embedding.

The model download/dependency-install budget, bounded live call/token/USD caps,
authorized credential availability, core dependency pins, API snapshot treatment,
and actual enrichment prompt/profile remain unresolved. No scientific loss,
pair weighting, Boolean/event mechanism or later-stage setting is changed here.

No changes were made to the user's implementation plan, legacy source, dataset
release, original prompts/schemas, or P02a artifacts. Working source remains
uncommitted on `full-phi-jepa-from-dataset` at base
`7f2553ca6591301de588bd3362e72838354169a0`.
