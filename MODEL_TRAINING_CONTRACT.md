# Active model-training contract — 2.0.0-candidate.1

**Implementation update, 24 September 2026:** Stage 2 is validated with frozen
Qwen/Qwen3-Embedding-0.6B and separately recorded public-only OpenAI gpt-5.6-sol
notes. Stage 3 implements the settled computation below. The user selected
**equal weight per question-conditioned pair**, superseding the inverse-
multiplicity proposal below for active training. A capped 20-pair/200-update
correctness fit is complete; full training remains disabled. Earlier statements
that providers/models are unimplemented or all training is disabled describe
P02a history. See `docs/reviews/P02b_completion.md` and `P03_completion.md`.

24 September 2026. Authority: the user's Stage 1/P02a revision-3 instructions and
confirmed adjacent-pair/full-feedback decisions. This is a separately versioned
training contract. `MODEL_DATA_CONTRACT.md` 1.1.0, dataset schema 1.0.0, export
registries, frozen configuration, labels and simulation records remain unchanged.
The candidate suffix marks contract review and the later Boolean/event mechanism
proposal; the user has settled the input/enrichment policies and projection rules.

## Settled computation

For one domain/layout of numerical width d, at each recorded adjacent pair:

```text
e = E(serialize(Q, C))                # frozen E; no gold answers
p = P_phi(e)                        # trainable; width d
x_k = concat(n_k, p)                # width 2d
y_k = concat(n_(k+1), p)            # SAME current p; target gradients enabled
x_hat_(k+1) = ODE_theta(x_k, [t_k, t_(k+1)])
loss_pair = mean((x_hat_(k+1) - y_k)^2)
```

Optimize P jointly with the ODE. Do not detach target p, freeze P, cache projected
p across optimizer updates, or introduce an EMA/teacher. E remains frozen; its
cached output must carry exact model/revision/preprocessing/content provenance.
No E(Q,C,A) target, answer-embedding inverse, learned language decoder, tree
encoder, physical readout head, semantic regularizer, EBM, energy descent or
schema repair is authorized. This phase implements interfaces, not the models.
Future model tests must verify gradients through BOTH occurrences of p and the
ODE, and frozen E. Projection collapse/scale is a diagnostic, not authorization
to replace the accepted objective.

Autonomous inference starts from the final observed n and initial p, then carries
the complete predicted 2d vector forward. Never replace predicted context with p
on later steps. Integration intervals use physical timestamps; predicted timestamp
and step-index coordinates remain real-valued loss coordinates, without rounding.
The requested physical integration grid is an external scheduling input, not a
clock reconstructed from a possibly inaccurate predicted timestamp.

## Data boundaries

- `PublicInputReader`: reads only the checksummed `inputs.jsonl`; no truth handle.
- `TrainingSequenceReader`: train only; combines public history with recorded
  `reference.states` as legitimate numerical supervision. It never reads
  `target-texts.jsonl` or uses the historical Q/C/A objective.
- `EvaluatorTruthReader`: explicit evaluator-only diagnostics on any release
  partition. Recorded-state diagnostics are never autonomous forecasting results.
- Metadata routes domain/split/group and records provenance. None enters E or n.
- Public answer_spec remains the request. Gold labels, private explanations and
  gold/predicted answers are excluded from enrichment and ODE context/targets.
  Named predictions are a distinct downstream typed payload.

## Candidate numerical scope and context

See [state mapping](docs/docs/P02a_state_mapping.md) and exact machine manifests in
`docs/reviews/artifacts/P02a/`. The selected active scope is state_plus_fixed_conditioning; state_only remains
a separately named comparison candidate. Every integer/float within the chosen
scope enters n, including step index and timestamp. Boolean fields and variable
categorical relations remain outside numeric MSE; a separate Boolean/event
mechanism is proposed for later review.
Null/missing/extra/duplicate/nonfinite data fails, never becomes zero. Digits in
strings remain text. Unit/frame mismatches fail. Vector components are preserved.
Reference validation enforces declared integer types; predicted vectors accept
finite real coordinates, including float-valued predicted indices.

For both candidates, Q/C retains the original complete public problem, including
the public history through cutoff, model parameters, controls, known events and
answer_spec. No earlier pair is constructed using this full history. User-approved public-only LLM
enrichment has a separate immutable-input interface;
no provider is called. No truncation or context compression is silently applied.

## Pair window and weighting proposal

Start at the actual last public state, exactly at observation_cutoff, followed by
consecutive reference states through the requested horizon. Require positive
actual dt, increasing reference indices, matching identities, and final horizon.
Pair identity hashes sample, physical transition, layout and Q/C identity.
Physical transition identity hashes domain/group/start/end times.

Preserve all distinct question contexts over overlapping horizons. Proposed
explicit weighting: each question-conditioned pair receives 1/m where m is the
number of contexts for that physical transition in the selected training domain.
Reduce as sum(w*loss_pair)/sum(w) over the declared epoch population, or an
unbiased equivalent sampler; do not normalize each minibatch by a variable
random sum and silently claim the same objective. This gives each unique
transition equal aggregate weight without dropping question contexts. Domain
mixing/sampling remains a later explicit training configuration, not a quota edit.

## Baselines and remaining gates

Custom Coconut-inspired and CODI-inspired baselines are intentional. They must be
named as custom variants and compared honestly, not replaced by upstream methods.
Upstream bug claims remain user-reported unless independently reproduced.
Existing descriptive explanations are eligible for baseline target review; missing
official-method CoT traces is not an automatic rejection. No baseline is trained
in P02a. Selected dependencies/model checks remain isolated and pinned in later
phases; no repeated generic GPU qualification is needed.

Training is disabled. All three P02a policy choices are settled; the separate Boolean/event mechanism still needs later design/qualification. P width follows d; ODE width
follows 2d and requires no separate width decision.

## User scope decision — 24 September 2026

The user selected **state plus fixed conditioning**. Active d and p widths are
arm 177, driving 106, objects 86, tether 140; ODE widths are 354/212/172/280.

The state-only mapping remains a documented comparison candidate, not an active
choice. Public-only LLM enrichment, separately recorded, is also user-approved.
The user selected a separate Boolean/event mechanism proposal for a later phase.

## Enrichment implementation boundary

The selected later E input includes Q/C plus separately recorded public-only LLM
notes. Original public facts remain immutable; answers and private explanations
are forbidden. `context_mode=enriched` fails on missing enrichment. P02a audit
uses the explicitly named `public_base_for_offline_audit` mode and makes no live
call; its context character lengths are base-context measurements, not enriched
lengths or tokenizer counts. Provider/model/prompt/cache budgets and actual output
validation belong to the next separately authorized interface phase.

Boolean/event update (24 September 2026): the user selected a separate mechanism
proposal for later review. No Boolean casting, new head or objective is implemented
here. See `docs/docs/P02a_boolean_event_proposal.md` from the repository root.
