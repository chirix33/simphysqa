# P01 data and evaluation decisions

Authority: user authorized P01 and supplied the expanded `docs/prompts/P01_data.md`.
Starting branch `codex/p00-bootstrap`, HEAD `dbff9573fa3d13adf4edafa42976afc2e5208e90`.
P00 was committed before this phase; the sole starting edit was the expanded prompt.
That edit is preserved byte-for-byte (SHA-256
`4778fd4c5ebc580f6675293a9ea32b65f457f32ad6e04bbaa74f5e62bd70a969`).

## Dataset scope and partitions

Use seed 11 and 32 base families: 16 train, 4 selection, 4 calibration, 4 ID test,
and one each low-friction, high-friction, combination and event OOD. This replaces
the older illustrative 24/4/4 allocation under the active prompt's authority.
Each family has two paraphrases and two physical query times, giving 128 records.
Assign partitions before expanding views; UUID-shaped pseudorandom IDs encode no
split, target or physical parameter. No statistical OOD conclusion is supported.

ID ranges: v0 [5,20] m/s, mu [0.3,0.7], x0 [-10,10] m, T [0.5,5] s;
gravity 9.81 m/s². Parameter OOD mu is [0.05,0.15] or [0.85,1.0]. Reserve
v0 >=15 AND mu <=0.4 from every ID partition. Combination fixture uses v0=17.5,
mu=0.35; training anchors include v0=17.5 with mu=0.55 and v0=10 with mu=0.35.
Thus both exact marginal values occur in training, but never together there.
These anchors also exercise moving and stopped targets at the default ranges.
Event OOD explicitly changes friction to zero at 0.25 s; it is not topology OOD.

Configuration exposes counts, ranges, seed, paraphrases, sample intervals and query
fractions. The bounded wiring implementation caps total families at 256, paraphrases
at two and query fractions at four; it does not authorize a main-study dataset.
Query time is Tmin + fraction*(base_horizon-Tmin), keeping all variants inside
the configured physical horizon interval. Fractions default to 0.5 and 1.
Near-duplicate handling groups known correlated views and rejects exact duplicate
base parameter records; it is not an arbitrary-language semantic deduplicator.

## Oracle and time semantics

All authored dynamics are under `src/phi_jepa/benchmarks/`. Constant friction uses
closed form, scheduled changes use piecewise analytic segments. Zero horizon is
explicitly rejected consistently with P00. Events must have unique strictly increasing
times in (0,T]; no ambiguous simultaneous or out-of-horizon events. Friction is
right-continuous; position/speed are continuous at the boundary. A change at T has
no effect on terminal state. Rest is absorbing even when friction later becomes zero.
Grids include exact zero, T and event boundaries, plus eight equal sample intervals.

Independent validation uses forward Euler position updates from old speed and projects
speed to nonnegative values; it never calls the analytic oracle or stopping-time formula.
Both solvers land on event/sample times. Compare steps 0.02 and 0.01 s. Fine position
error must be <= g*max_mu*T*0.01 + 1e-8 m per case; speed error <=1e-8 m/s, and fine
position error must not exceed coarse error plus 1e-8 m. A separate smooth case asserts
the expected factor-two first-order refinement. These are oracle checks, not model errors.

## Boundaries, normalization and evaluation

ScenarioInput contains observed facts and complete deterministic text only. Truth,
OOD/split metadata, trajectories and base-generation records are separate artifacts.
No solution annotations are generated in P01. Models and P00 fixture inference do not
import benchmark dynamics/truth. PhysicalPrediction adds a numerical envelope independent
of any answer prose. Units/order/names/frame/time/shape/finiteness are checked.

Fit population mean/std from train terminals only, keyed by observable ID/unit/frame.
Collapse identical family/time paraphrases so wording duplication cannot reweight scaling.
Persist all training family/scenario IDs and selected training-target hash. A standard
deviation <=1e-12 uses scale 1 physical unit and sets a constant-coordinate flag.
The training-example constructor rejects held-out truth; changing held-out targets leaves
the scaler unchanged. Endpoint errors remain in physical units; macro normalized MSE is
the mean of x/v MSE divided by their train-fitted squared scales.

Unknown/duplicate prediction IDs reject the whole file. Missing/invalid rows count as
failures; valid-only errors always carry their denominator and coverage. No valid rows
means null errors, not zero. Schema validity is distinct from physics. Four independent
endpoint predicates test nonnegative speed, no speed gain, no backward displacement,
and displacement <= v0*T, with declared observable absolute tolerances 1e-8.
These weak bounds are necessary, not sufficient for the correct answer. Report violations /
evaluated checks, eligible/unsupported/unevaluated counts, coverage, per-check excess in
physical units, failed samples and family macro PCVR. No checks means unavailable.

Trajectory RMSE uses only actual supplied compatible time grids and terminal bindings,
with explicit sample/timepoint denominators. A structurally finite but incompatible
trajectory is unavailable without discarding an otherwise valid endpoint; malformed or
nonfinite numerical envelopes invalidate the prediction. No interpolation or invented
rollout is used. NCS, detection, diagnosis, fallback and study confidence intervals are
outside this P01 slice.

## Provenance and integration fixes

No new dependencies. Existing Python 3.12.14 CPU environment remains sufficient.
Extend source hashing recursively: P00's top-level glob would otherwise omit new benchmark
modules. Add manifest/artifact integrity verification before reading run bundles.
Existing P00 fixture behavior and old artifact files remain unchanged. Dataset, validation
and evaluation runs use exclusive-create content-addressed bundles. Solves and numerical
steps are counted; model calls remain zero. The source registry identifies local authored
physics and external candidates, with unknown licenses/download status left unknown.

The handoff checker now ignores an explicit negative instruction saying not to use the
old installation path, preserving the user's P01 prompt instead of rewriting it.
No professor decision, trained objective, latent reference definition or judge was changed.
