# Stage 7/P06 custom baseline decisions

Authority: revision-4 root implementation plan and the user's explicit Stage 7
alignment/supervision/inference replies. Older official-upstream requirements in
the historical P06 prompt do not apply. Primary Phi-JEPA is unchanged.

Source is preserved `Phi_JEPA_Final_+_Baselines.ipynb`, SHA256
`fd5a19eefd781ae1c09ac31bbef4fe3da31a6c54f0653a72bc022e1d17d66e7b`, matching the
earlier P02a preserved-source manifest. Only whitelisted class ASTs are inspected;
the notebook and its globals are never executed. A draft P06 configuration had an
incorrect notebook hash; the source verification caught and corrected it. Initial
token preparation and the first Coconut qualification record carry that old
configuration digest. Actual notebook contents and model computations did not
change. This provenance correction is retained rather than rewriting old results.

Both independent methods use `google/flan-t5-small`, publisher revision
`0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`, Apache-2.0 model card, locally cached
safetensors with a file hash manifest. Isolated `phi-coconut-custom` and
`phi-codi-custom` environments use PyTorch 2.7.1+cu128 and Transformers 4.51.3;
complete pip freezes are recorded. Qwen remains the primary frozen encoder.

| Method | Latent mechanism and supervision | Objective | Inference |
| --- | --- | --- | --- |
| coconut_inspired_t5_gru | Masked pooled T5 encoder, eight learned queries, gated GRU recurrence, appended encoder memory; descriptive explanation plus typed label target | CE + 0.001 adjacent latent smoothness | Generated explanation plus typed labels |
| codi_inspired_t5_distillation | Shared T5 backbone across plain teacher and eight-token gated-GRU student passes; teacher descriptive explanation plus labels, student labels only | teacher CE + student CE + 0.5 post-answer alignment MSE + 0.001 smoothness | Student-only primary; teacher-explanation/student-label hybrid separate |

These are custom notebook-inspired methods, not official reproductions. They do
not establish pre-answer reasoning transfer. Existing explanations are descriptive
supervision, not verified causal derivations; no replacement reasoning is authored.

CODI keeps the notebook's **shared T5 backbone**. Teacher projection LayerNorm and
Linear are fixed at seeded initialization, require no gradients, are omitted from
the optimizer and retained in checkpoints. Student projection is learned. Only
the teacher alignment target is detached. Thus alignment has no path through the
teacher computation graph, but shared backbone parameters learn through the student
pass; teacher CE separately trains that same backbone. It is not a separate frozen
teacher backbone.

Alignment selects the final decoder layer at the unique actual EOS **label**
position. Shift-right places the final answer token at that decoder input position;
the hidden state predicts EOS after consuming the complete answer. Padding/-100
positions are excluded; missing/multiple/truncated EOS fails explicitly. No last
available token substitute. Real target indices are in the preparation artifact.

Student-only generation consumes public Q/C/enrichment only. Hybrid generates the
teacher explanation/labels independently and returns the teacher explanation; it
never feeds that explanation to the student. The same generated student label is
reused for paired reporting. Teacher-label fallback is triggered only by observed
student generation/typed-parsing failure, never by gold correctness. Failed cases
remain in the denominator; total hybrid teacher+student cost is separate from
physical unique generation calls. Generated Booleans are learned language-model
predictions, not the primary model's qualified deterministic trajectory readout.

Public inputs contain all original fields plus exactly the existing permitted
enrichment. Private targets are prepared separately; inference does not open the
training target file or dataset reference reader. Typed output binds every target
to its identity, quantity, type, unit, frame and absolute query times. Signs,
decimals, vectors and true/false retain their distinctions. No punctuation stripping.

Pinned T5 maps literal braces and some unit characters to unknown tokens. The
`p06-json-ZXQ-hex-v1` transport escapes unrepresentable characters and literal Z as
`ZXQ` + six hexadecimal digits + `ZXQ`, using existing vocabulary. It protects
special/control/repeated whitespace and verifies exact decoded text equality before
accepting any tokenized input or training target. No vocabulary is added, no input
field is removed, and no truncation is enabled. Eight selected enriched contexts
span 10,107–22,323 tokens; the four training targets span 425–1,025 teacher tokens
and 394–994 student tokens. This qualifies this bounded selection, not all release
contexts. All selected round trips are exact.

Bounded engineering profile: one GPU job, microbatch one, seed 11, BF16 autocast
with FP32 parameters, gradient checkpointing, at most two AdamW updates on one
tether training question per method, separate existing tether validation question,
900 seconds per method fit. One longest-selected-context forward/backward attempt
per method is qualification only, with no optimizer update. No validation tuning
or full study. Generation is greedy with max 2,048 new tokens; EOS remains required.
Notebook four-beam decoding and no-repeat-three-gram are deliberately disabled in
this bounded profile: repeated numeric/unit fields are valid structured output.
Checkpoint selection is the final bounded update, not tuned on held-out accuracy.

Memory implementation qualification: the original eager T5 encoder did not finish
its first 22,323-token forward pass within a deliberately shortened 600-second
diagnostic cap and occupied approximately 31,726 MiB according to nvidia-smi.
It was terminated, not reported as a native CUDA OOM. Its incomplete attempt is
preserved under native `p06-correctness-01`. A bounded engineering correction now
computes encoder attention in 512-query blocks, with **all keys**, unchanged
absolute relative positions, shared first-layer relative-bias weights, original
unscaled T5 dot products/softmax/dropout, and recomputation for backward. It adds
no parameters, local-attention window, token filtering or objective change.
Decoder and cross-attention remain the pinned implementation. Dropout random-number
consumption differs from eager execution because of blocking; this is recorded,
not a claim of bit-identical training trajectories across memory implementations.
Multi-layer FP32 output and every parameter-gradient comparison passes against
the original implementation. The final `p06-correctness-02` profile allows one
qualification, one at-most-two-update fit, and one train/validation generation run
per method, each under a hard 900-second subprocess cap. The abandoned eager
attempt is additional counted diagnostic compute, not training. First final-profile
Coconut qualification passed in 28.713 s, with 2,856,586,752 peak allocated bytes.

Checkpoint identity includes model files/revision, formatting, config, split/data
hashes and target hashes; payload includes model, fixed projection, optimizer,
CPU/CUDA RNG, update count and explicit absent scheduler (constant LR). Atomic
hash-addressed files and strict identity checks support resume and fresh inference.
