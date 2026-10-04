# Human audit and power-method reconciliation (SPQ01)

Three independent reviewers review the same 20 calibration records and the same
140 fresh formal records: 160 each, 60 calibration ratings and 420 formal ratings.
Calibration is excluded from formal analysis. The allocation is unchanged.

Primary judgment is acceptable / material_error with criterion-specific findings
and error categories. The fixed draft/0.1 rubric remains in simphysqa.audit and is
hashed into packets. Missing language is a finding; generic context is incomplete.
Auditors receive private references, states, events, units, frames and verification
provenance. Answering models receive public inputs and their public annotations.
Organizer identity keys retain annotation-provider identity and accounting; reviewer
JSON/HTML excludes them. Development deliberately includes direct/predictive pairs
from each group. Calibration and eventual formal sampling allow one item per group.

R1/R2/R3 forms are separate and blank. Copy source forms before reviewers edit them.
Import checks assignments, criteria, categories and packet hashes. Empty judgments
remain uncollected. Original independent submissions are exclusive-created and kept
separate from adjudication and corrected annotation versions. Cross-submission
duplicate handling and incomplete-item analysis remain pending.

## Sampling population

The existing sampler draws groups uniformly, then one question uniformly within
each group. Thus question j in group g has inclusion probability proportional to
1/G times 1/m_g, where m_g is the group's number of eligible questions.
This targets a trajectory-balanced population, not uniform release-wide QA records.
Record-weighted estimates would require a separately specified QA-record sampling
design or design weights proportional to m_g and corresponding variance analysis.
Do not call the present pooled estimates release-wide QA-record estimates.

The actual source release has 11,105 admitted predictive records / 6,340 groups.
The four SPQ00 smoke records are development material, not this release population.
SPQ01 selects 16 train groups for engineering diversity. Configured exclusions
persist the four SPQ00 groups plus these 16 groups. Default fresh previews union
these exclusions with caller-supplied prior calibration/development groups.
Calibration and formal groups must remain disjoint. No definitive formal IDs are
exported. Later freeze must pin the annotation version, release population,
rubric, inclusion rules, allocation, seed, exclusions and missingness policy.
Counts by domain/type are descriptive; 140 records do not power every subgroup.

## Supplied calculation and matching conditional test

Original supplied archive files are preserved byte-for-byte in
[docs/references/spq01_audit](../references/spq01_audit/source-package.json).
Archive SHA256: 1c2e4961c67fc6e0420469fd5f53908b33c2601ec635abbd7f33ed9a65f22695.
Script SHA256: da74f1eab11a1533509bfd71ce26f07ed182264f9f3551fd735b5653a77eac27.
The archive has no declared upstream package version of its own; the local
provenance manifest is supplied-audit-package/1.0.0. Its Python/SciPy script
reproduces kappaSize::PowerBinary, traced to
[kappaSize 1.2 (2018-11-25)](https://cran.r-project.org/web/packages/kappaSize/refman/kappaSize.html)
and the [PowerBinary source](https://github.com/cran/kappaSize/blob/master/R/powerBinary.R).
SPQ01 executed the supplied Python script, not R.

Preserved assumptions: p=.90 acceptable-rating prevalence, kappa0=.60,
kappa1=.80, three raters, two-sided alpha=.20, target power=.80,
nominal confidence=.80, 140 formal independent records. Prevalence is expected,
not observed, and is not an acceptance threshold.

For one record let C be the number of acceptable ratings among three.
The model mixes perfectly shared Bernoulli(p) ratings with probability kappa,
and three independent Bernoulli(p) ratings otherwise. Records are independent;
raters are exchangeable with identical marginal prevalence. This implies the
population pairwise/Fleiss agreement parameter is kappa. Its C-cell probabilities
are q(kappa)=(1-kappa)*Binomial(3,p), plus kappa*(1-p) in C=0 and kappa*p in C=3.
At the null, q0=(.0604,.0108,.0972,.8316); at the alternative,
q1=(.0802,.0054,.0486,.8658).

PowerBinary uses D=sum((q1-q0)^2/q0) and a noncentral chi-square approximation
with ONE degree of freedom, noncentrality N*D and critical chi-square_1(.80).
A matching explicit local test for fixed p is the scalar score test, implemented
and simulated in simphysqa.audit_method:

- w_c=q'_c(kappa0)/q0_c and I0=sum(q'_c^2/q0_c)=.8724305495828674.
- U=sum_i w_(C_i), T=U^2/(N*I0).
- Reject kappa=kappa0 when T>1.642374415149818; the reference p-value is
  chi-square_1 survival(T). Squaring makes this two-sided.
- Because q is linear in kappa, D=(kappa1-kappa0)^2*I0, matching the supplied
  local noncentrality. The score-derived local estimate is
  kappa_tilde=kappa0+U/(N*I0); it is unconstrained and may lie outside [0,1].
  A constrained model likelihood estimate can be specified at analysis freeze.

This is a model-conditioned test of the agreement parameter with prevalence fixed
at .90. It is not a four-cell omnibus Pearson test (which has three degrees of
freedom), nor a Fleiss-kappa Wald test with estimated marginal prevalence.
The supplied function defines a planning approximation, not an implemented
finite-sample Fleiss analysis. Merely reporting Fleiss kappa does not reproduce
the powered test.

The provisional unweighted Fleiss estimator may remain a secondary descriptive
statistic: P_i=sum_j n_ij(n_ij-1)/(3*2), Pbar=mean(P_i),
p_j=sum_i n_ij/(3*N), Pe=sum_j p_j^2, kappa_F=(Pbar-Pe)/(1-Pe).
Report unavailable if Pe=1. Its estimated-prevalence uncertainty/test is not
powered by claiming the fixed-p score calculation. Before formal analysis,
choose whether the fixed-prevalence model is scientifically defensible or use an
explicit nuisance-prevalence/reviewer-heterogeneity analysis and reassess its
operating characteristics. This is an analysis-plan decision, not a software
annotation approval gate. No actual rating analysis has occurred.

## Reproduced approximation and finite sample behavior

Runtime: Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1. The supplied script gives
129.03095760509072 unrounded records, minimum 130, and approximate power
.8237409136265488 at the settled 140 formal records.

Expected pattern counts under null: (8.456,1.512,13.608,116.424).
Under alternative: (11.228,.756,6.804,121.212). Sparse cells motivate a check.
Using seed 20261004 / NumPy PCG64, draw 200,000 independent multinomial samples
under each hypothesis, with 140 records each, and apply the stated score test:

| Quantity | Simulated rate | Monte Carlo SE | 95% Monte Carlo Wilson interval | Exact enumeration |
| --- | ---: | ---: | --- | ---: |
| Type-I error | .199855 | .000894184 | [.198108204,.201613326] | .198617376 |
| Power | .879060 | .000729087 | [.877623731,.880481708] | .879659735 |

Monte Carlo intervals describe simulation uncertainty, not audit confidence
intervals. Exact enumeration collapses C=1 and C=2 because their score weights
coincide, then sums all three-cell multinomial patterns. Saved results are in
audit-method/audit-reconciliation.json under the SPQ01 external artifact root.
Power is 5.532 percentage points above the approximation, exceeding the stated
2-point discrepancy criterion. The finite alternative changes score variance;
the local noncentral approximation is not exact. Report this discrepancy;
do not change 20/140 allocation or claim achieved human agreement.

These conditional simulations do not validate unequal reviewer marginals,
estimated prevalence, within-group dependence, selective missingness or
record-weighted inference. Before freeze specify confidence-interval procedure,
bootstrap replicates/seed and missing-record policy. Retain all three original
judgments together when resampling trajectories; never use adjudication to improve
original agreement. No human acceptance, agreement or annotation-quality result
exists until independent ratings are supplied.
