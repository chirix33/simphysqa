# Stage 5 fixed assessment — 24 September 2026

The user explicitly approved the `development_r1_v1` adaptation to the complete
2d predicted vector. The general reference-bank architecture is settled. This
decision changes no training objective, projection gradient, ODE state or feedback.

Reference entries are autonomous predictions on training inputs under the same
selected model/projection checkpoint, frozen encoder/context configuration and
solver as the query. The content-addressed bank records those identities and the
layout/profile hashes. A changed identity invalidates loading/assessment. No
recorded training trajectory, label or private event is stored as a reference.
Routing scenario/split metadata is permitted; it is not model input.

Candidate filtering precedes retrieval: exact domain, layout, cutoff and physical
sample grid/horizon. For training queries exclude the entire scenario, including
other question contexts. Retrieve k=1 by cosine of the frozen public-context
embedding, breaking ties by stable sample ID. Zero/nonfinite vectors, absent
compatible entries and incompatible identities are explicit unavailable/errors.

Terminal score is unchanged `1 - cosine(full_query, full_reference)`. No block
normalization or new weights. Dynamic numerical, fixed-conditioning and contextual
norms, block cosines, and additive contributions are diagnostic only. The additive
contribution of block b is half the squared distance between that block's portions
of the two globally unit-normalized vectors; contributions sum to the full score.
The dynamic numerical block includes recorded timestamp and step index. It is not
synonymous with physical coordinates. Log their drift separately.

The unchanged V1 judge compares literal public scenario text with its existing
public schema, using the exact original prompt and `{score,reason}` schema. It
does not assess forecasts, retrieved schemas or hidden causes. The bounded live
profile uses the already selected `gpt-5.6-sol` provider configuration. Returned
alias responses are cached; no immutable snapshot claim is available.

Generic contract operators require exact typed public constraints and evidence.
The release currently has no typed public operator constraints. Initial facts,
answer event thresholds and retrieved training values must not become physical
bounds. Empty/incomplete coverage is unavailable. When complete, preserve the
existing combination `familiarity + 0.5*contract + 0.5*semantic_v1`. Missing any
required component yields partial assessment, no combined score or threshold.

Calibration policy is recorded in `configs/assessment_p04b.json`: disjoint ID
validation calibration scenarios, per-scenario maximum across questions, empirical
95th percentile with the higher algorithm, strict score > threshold, minimum 20
scenarios and nondegenerate scores. Minimum 20 is an engineering qualification
gate, not a statistical guarantee. Selection/calibration overlap, test/OOD tuning
and stale identity reuse are rejected. The bounded one-query run does not calibrate.

Independent physical checks are separate from the combined assessment:

- Quaternion unit-norm error, tolerance 0.001, for qualified orientation channels.
- Taut tether distance versus explicitly public cable length, tolerance 0.001 m.
- Driving forward-position/velocity agreement with the corresponding world-vector
  x components, tolerance 1e-6 in native units. This is redundant physical-channel
  consistency, not a dynamics equation.

These fixed engineering tolerances were configured before the profile and not
tuned to outcomes. Checks use predicted channels only; absent channels/units/frame
or public length cause unsupported results. No arm conservation law is invented,
so an arm forecast with no applicable checks has unavailable PCVR, not zero.
No conservation assumptions are imposed on driven or dissipative systems. Limited
check success does not establish general physical validity or contact outcomes.

High-score numerical replacement remains disabled. Technical failure handling
preserves original and returned prediction artifacts. A supplied public-text-only
callback can be attempted once; it is a separate answer method, never a replacement
numerical trajectory. Without a qualified independent fallback, forecast failure
remains explicit. Answer failure with valid numerical output can use an explicitly
non-LLM deterministic numeric/rule formatter. No recursive fallback, hidden cause,
schema repair, EBM, energy descent or projection reset is introduced.
