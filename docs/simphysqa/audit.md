# Human audit preparation

Three reviewers independently rate the same 20 calibration examples, then the
same 140 fresh formal records. Each sees 160; total 60 calibration and 420 formal
ratings. Calibration and formal records and their physical groups must be disjoint.
Calibration informs rubric revisions; do not pool calibration into formal results.
Primary judgment is acceptable / material_error, with five criterion findings
and explicit error categories. Draft fixed rubric is embedded in simphysqa.audit
and hashed into packets; it is not the final research rubric.

Auditor packets include structured inputs, public language, QA/reference, private
verification states/events/checks, and target-specific evidence bindings.
Auditors alone receive private evidence. The HTML/JSON packet excludes annotation
generator identity; organizer-private/identity-key.json retains it. Separate R1/R2/R3
CSV forms use immutable packet/sample/phase assignments. Criteria syntax:
physical_reference=acceptable;language_fidelity=material_error;qa_validity=acceptable;evidence_sufficiency=acceptable;public_private_separation=acceptable
Use not_applicable only with justification in notes. Error categories are in the
rubric/code. Missing annotation is a possible material-error finding, never silently
accepted. Import retains original form and packet hashes, validates categories and
assignments, and creates a new exclusive file. Blank forms mean uncollected ratings.

Do not edit packet-source forms in place: copy them to a reviewer return location.
Preserve original independent ratings as immutable submissions. A later adjudication
record must reference the three original hashes/decisions, adjudicator, rationale
and corrected annotation version. Corrections form new versions, not overwritten
ratings or references. Cross-submission duplicate checks and final analysis storage
are pending; the importer prevents duplicates within a submission and overwrites.

## Sampling

sample-preview reads an explicitly supplied versioned frame. Include admitted
simulator records; no quarantined records, no silent filling/resampling. Randomize
physical split groups with seed 20261004 and select one random question per group.
Take calibration first and formal next from the remaining randomized groups.
Exclude prior inspected/development/calibration groups explicitly. Record frame hash,
group counts, seed, inclusion rules, available allocation and shortfall.
The preview never exports formal IDs or freezes a sample. Definitive formal export
is disabled in this milestone. Before it is enabled, pin the annotation version,
release population manifest, final rubric and prior-group exclusions. Also document
any sampling allocation adjustments and group weighting.

The planned pooled estimand is acceptability across group-balanced physical
trajectories in the declared release frame, with one randomly selected question per
trajectory. This differs from a uniform record-weighted population when trajectories
have unequal numbers of questions. Counts by domain and family are descriptive;
140 formal records do not establish power for every domain-by-family subgroup.

## Planning assumptions and analysis

Retain nominal 80% confidence, two-sided alpha .20, target power .80, expected
acceptable-rating prevalence .90, and kappa comparison .60 versus .80.
Expected prevalence is a planning assumption, not an observed outcome or pass
threshold. Sample sizes are settled; no achieved power claim is made.

The original power calculation (formula, variance, estimator, dependence assumptions,
source or software) was not supplied and was not found in the targeted repository
documents. Preserve its requested inputs; recovering and checking the original
calculation is a scientific pending item. Do not substitute a calculation secretly.

Provisional primary agreement estimator is unweighted Fleiss kappa on the 140
complete original three-rater formal records: P_i = sum_j n_ij(n_ij-1)/(3*2),
Pbar = mean(P_i), p_j = sum_i n_ij/(N*3), Pe = sum_j p_j^2,
kappa = (Pbar-Pe)/(1-Pe). Report unavailable when Pe=1. Reconcile this estimator
with the original power calculation before locking the analysis. Do not call a
pairwise Cohen calculation a three-rater Fleiss calculation.
Proposed uncertainty is an 80% percentile bootstrap of physical groups retaining
all three judgments together, with pinned seed/replicate count (replicate count
pending). Report marginal acceptability, agreement, disagreement categories,
complete-record counts and reviewer/item missingness separately. Never use
adjudication to improve original agreement. Missing ratings are not acceptable
and must be reported; final incomplete-item handling remains a freeze decision.
Bootstrap confidence intervals alone do not recreate or validate the power test.
No ratings, agreement values, confidence intervals or human results exist yet.
