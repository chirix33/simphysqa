# SPQ05 analysis specification /1.0.0

Freeze before human review. No ratings, acceptance, agreement, achieved power or
model performance exist at preparation. Three original reviewers,140 independent
group items,20 domain/family cells of7. Every reviewer sees all140. No calibration.
The population is the balanced audit design conditional on frozen qualification,
not the natural record-weighted quality of11,105 predictive release records.
Attrition/reserve substitution may change the eligible population; report all
candidate denominators, reasons and specifically clarification attrition alongside
quality summaries. Seven/cell supports descriptive listings, not powered subgroup claims.

Primary descriptive quality: mean of per-item acceptable-rating fractions across
the fixed140 items; equivalently observed acceptable ratings/420 when complete.
Also report each reviewer acceptable/material-error/blank counts, all-three
acceptable count, any-material-error count and criterion/category counts. An
all-three acceptable item requires three actual acceptable judgments. Never infer
acceptable from a blank or adjudication. Present failures, eligibility rejections,
unused reserves and attrition separately; generation success is not human quality.

Missingness: preserve all420 assignments. Show missing rates by reviewer and
domain/family. For pooled acceptance give identification bounds
`acceptable_observed/420` through `(acceptable_observed + missing)/420`.
Describe observed-rating acceptance separately with its explicit denominator.
Agreement uses complete three-rating items only; give their number and composition
by cell. If any cell has zero complete items, a fully balanced complete-case
agreement estimate and bootstrap interval are unavailable. Complete-case agreement
conditions on response and may be biased under informative missingness. Do not
silently change140 to the complete count or impute ratings. Partial forms retain
blank rows; importer requires the full assignment list. No fabricated values.

Descriptive agreement: empirical-prevalence unweighted Fleiss kappa for complete
items; binary counts n_ij, P_i=sum_j n_ij(n_ij-1)/6, Pbar=mean_i(P_i),
p_j=sum_i n_ij/(3N), Pe=sum_j p_j^2, kappa=(Pbar-Pe)/(1-Pe). If incomplete cells
retain unequal complete counts, also report a design-balanced version with each
cell contributing1/20 to Pbar and p_j, clearly distinguished from the unweighted
complete-case estimate. Pe=1 makes kappa unavailable, not zero or perfect. Also
report pairwise raw agreement and reviewer marginal acceptability as diagnostics;
do not assume identical reviewer marginals for descriptive summaries.

Uncertainty: nominal80% percentile intervals,10,000 bootstrap replicates,
Python Random(20261006). For acceptance summaries and missingness bounds, resample
whole items (all three original ratings, including blanks) with replacement within
each of20 cells, retaining seven draws/cell. For complete-case agreement resample
whole complete triplets within cells at their observed complete-cell counts;
compute both balanced and unweighted estimators per replicate. Report incomplete
cells and conditional interpretation. Use sorted replicates and linear-interpolated
.10/.90 quantiles. Report undefined kappa replicates and their fraction; if more
than5% are undefined, do not give a kappa interval. No finite-population correction:
qualification-generated finite frame is not fully known, so this is an empirical
design-stratified superpopulation approximation. With seven/cell, interval stability
is limited; no universal coverage or achieved-power claim. Adjudication cannot
replace originals in estimates or resampling.

Preserve historical planning discrepancy: supplied PowerBinary approximation
requires129.0309576 (minimum130) and gives.8237409136 at140. Conditional fixed-p=.90
one-parameter score simulation gave.879060 (exact.879659735), a5.532 percentage-point
discrepancy; type-I simulated.199855 (exact.198617376), alpha.20. These are model-
conditioned planning calculations, not human results. See unchanged audit.md and
preserved source/receipts. Fleiss kappa with empirical prevalence is not that
powered test. If reported later, retain fixed-p kappa0=.60 scalar score statistic
only as a separately labeled planning-model sensitivity diagnostic with its
exchangeability/fixed-prevalence assumptions. Do not use it as a quality gate,
claim this balanced family audit achieves its power, or silently generalize it to
unequal raters/missingness/qualification. No acceptance threshold is specified.

Import commands (only after the separate final140 packet root exists):

```powershell
# Validate only: omission of --output preserves all files.
python -m simphysqa.focused_audit import-ratings --packets $FinalPacketRoot --form $SubmittedR1 --reviewer R1
# Import immutable original CSV and normalized JSON; duplicate reviewer import fails.
python -m simphysqa.focused_audit import-ratings --packets $FinalPacketRoot --form $SubmittedR1 --reviewer R1 --output $OriginalSubmissionsRoot
```

Repeat for R2/R3. The exporter seals forms; reviewers edit copies. Packet manifests
and hashes, full assignments, phase, reviewer slot, noncontradictory criteria,
categories, material-error locations/comments and duplicate submissions are checked.
Blank forms validate as uncollected and cannot be imported as a collected submission.
Original CSV bytes survive import. Store adjudication/discussion/corrections under
separate roots linked to original hashes. Numerical rating analysis implementation
and actual execution remain pending incoming human ratings; this specification
is prepared now and may not be silently revised after seeing ratings.
