# Project context and decision authority

[Start](../README.md) · [Architecture](02_architecture.md) · [Sources](09_sources.md)

## Goal and role of this implementation

Phi-JEPA asks whether a learned continuous latent dynamics model, conditioned on frozen language features and automatically extracted structure, can answer physical questions while reducing hand-authored physics inside the predictive method. It should provide numerical predictions, an interpretable final answer, and an assessment of anomalous cases. The experiments must distinguish predictive accuracy, physical compliance, structural extraction quality, OOD detection/diagnosis, engineering effort, and cost.

The name JEPA and the manuscript's self-supervised terminology do not remove the actual dependence on supervised physical targets. Describe the implemented objective honestly. No implementation can guarantee correctness merely by reconstructing the question embedding or returning valid JSON.

## Authority, in order

1. Latest explicit user instruction or professor clarification supplied by the user.
2. September 22 part 2's final decisions; part 1's morning decisions where not superseded.
3. Active newer manuscript, interpreted using those corrections.
4. Approved demo prompt/schema artifacts; code is implementation evidence, not a scientific specification.
5. Older transcripts and original numerical prototype for historical context only.

The professor explicitly said to stick with the morning decisions when the demo reintroduced energy minimization and schema repair. Both remain excluded. The later part-2 decoding discussion at 18:35–19:53 supersedes an earlier proposal for a separately trained arbitrary-JSON decoder. The physical-state readout is still learned.

## Settled design decisions

| Topic | Decision |
| --- | --- |
| Architecture | PDF-style latent language/structure pipeline; generic types and modular schemas are appropriate |
| Frozen components | Question/text encoder and prompted extractor, judge and answer generator |
| Learned components | Schema encoder, hybrid projection, ODE vector field, linear physical readout, question reconstruction head |
| Physical objective | MSE on decoded terminal targets only; no intermediate-state guidance loss in the primary method |
| Semantic objective | Terminal reconstruction/alignment with the frozen question embedding; explicit no-regularizer ablation |
| Structure | Preserve numeric and string values plus relationships/topology; interchangeable tree/graph encoders |
| Extraction | Demo's exact generic envelope; scenario-dependent contents; explicit unknown outputs |
| Final answer | Frozen LLM uses question, original structure, initial information and named predicted states |
| Energy | Fixed untrained assessment; no separate EBM or DSM training |
| Inference | No parameter fitting, latent optimization or topology correction based on predictions |
| Bregman | Deferred |
| OOD | Detection and evidence-supported possible causes, with defined fallback; no automatic recovery guarantee |
| Empirical claims | User-run experiments populate manuscript tables; demo/expected ranges are not final results |
| Baselines | Standard neural ODE, proper physics-informed ODE, representative direct LLMs, CoConuT and CODI, plus agreed ablations |
| Model categories | Representative high/moderate/non-reasoning models; exact IDs must be selected and logged |

The initial brainstormed `domain`, `objects` and `formulas` fields are not mandatory additions to the later adopted demo envelope. Do not replace the adopted response schemas just because the transcript explored alternatives first.

## Current source status

Repository: https://github.com/chirix33/phi-jepa (private, default branch `main`). The planning review verified repository access and current `requirements.txt`; root README.md and AGENTS.md requests returned 404. It did not audit a complete current checkout. Phase 0 must discover actual files, branch and commit; absence at a requested path does not prove the whole repository lacks documentation.

The earlier full prototype audit was at commit `6e5f7d0f35b44db32056476d9e3b1ed24878d393`. Do not call that the current head. It implemented numeric derivative learning, hand-authored domain constraints, contract agents and guarded RK4. Fixture mode works; the user confirmed failures in OpenAI mode. That old execution issue needs diagnosis from its actual error logs if the path is reused, not a claim that the new demo solved it.

The supplied generating notebook and result ZIP are a second prototype. Twenty cases (9 train/3 validation/8 evaluation), one seed and two epochs do not constitute a paper experiment. The records configure `gpt-5`; the conversational description “GPT-5.5-Instant” is not verified by API metadata.

## Demo defects already established

| Defect | Required consequence |
| --- | --- |
| All-time MSE/target-embedding objective and unused online target encoder | Replace with terminal physical MSE and explicit semantic reconstruction; no inherited EMA machinery |
| Schema branch embeds paths/numbers but ignores string values | Encode names, units, relation operators, events and evidence; test distinguishability |
| `[B,T,D]` passed where `[T,D]` expected | Validate axes; compact named vectors; batch-one payload must not repeat the whole trajectory |
| PCVR is evidence/numeric substring matching | Separate provenance from actual physical verification; empty coverage is not perfect compliance |
| Learned numeric reconstruction is called energy | Implement and label fixed assessment explicitly; do not carry value probes forward without a separate justified role |
| All baseline labels reuse one full checkpoint | Train independent methods; distinguish retraining ablations from runtime switches |
| Without-energy branch still uses energy fallback | Assert its disabled components are not called |
| PIN penalty never trains a PIN baseline | Implement actual domain residuals in the PIN baseline only |
| Full cases all fall back to identical trajectories | Track original/candidate/final outputs and fallback reasons; do not interpret identical curves as independent wins |
| Vehicle force drives the car backward after stopping | Correct the physical oracle or relabel it as imposed-force motion; default first benchmark is passive stopping |
| “Fluid” demo is pendulum-like and “topology” shifts are parameter/events | Label them honestly; add genuine fluid/topology tasks separately if desired |
| Wrong sample time origin, incomplete checkpoints, weak leakage guard, stale cache keys | Correct timestamp contracts, checkpoint metadata, API boundaries and content hashes |
| Judge disabled in saved results; incomplete cost/NFE accounting | Log actual component execution and all calls/solves |

The detailed [audit](../references/demo_review.md) preserves evidence and limitations. Reuse approved prompts/contracts, basic provider patterns and solver concepts selectively. Preserve original notebooks/results as read-only historical artifacts. No rewriting history, deleting legacy code wholesale, or importing its hand-authored physics into the new primary model.

## Domain engineering boundary

Domain-specific simulation and independent evaluator formulas are necessary benchmark infrastructure. Proper PIN-ODE baselines also need authored residuals. Keep those in separate packages/registries and count their work separately. The Phi-JEPA predictor must not import a domain-specific derivative function, analytic target solver, hidden simulator parameter or ground-truth trajectory at inference. Observable names/units and generic types are metadata, not a hidden solver, but record per-domain readout/metadata effort.

An LLM-generated formula is untrusted text. Never `eval` extracted expressions. The first implementation supports a finite generic relation vocabulary; unsupported physics checks are reported as unavailable. An independent evaluator may contain reviewed physics code without falsely attributing those checks to autonomous inference.

## Collaboration arrangement

The user will paste prompts into a separate Codex session and relay completed work or questions to this planning assistant. This package does not authorize launching another agent here. Codex should finish the authorized phase's concrete slice, report evidence and stop at that phase boundary. It can resolve routine implementation choices, but must surface contradictions to settled science and requests that need credentials, paid run budgets or missing external assets. See [workflow](07_workflow.md).
