SimPhysQA human-audit Overleaf insert

1. In Section 8 (Evaluation Protocol), replace the existing Resource-quality
   audit paragraph with human_annotation_audit.tex, or use:
   \input{human_annotation_audit}
2. Merge audit_references.bib into the project's existing bibliography. The
   insert uses \citep, consistent with an ACL/NAACL natbib-based template.
3. Keep future tense until the audit is performed. After completion, insert
   actual sample counts, acceptance rates, agreement and uncertainty estimates,
   adjudication outcomes, reviewer qualifications and sampling details.
4. The optional schema_revision_paragraph.tex replaces the few-shot framing
   with iterative schema creation/enrichment and human schema review. Its human
   review remains future tense because no completed review is verified here.
   Align the introduction, Section 5 and Figure 2 caption with that change.

Locked planning settings
  Three reviewers; same 140 formal records; 20 separate shared calibration
  records; 160 records per reviewer; 480 individual judgments in total.
  Nominal confidence 80%; two-sided alpha 0.20; target power 80%; anticipated
  acceptable-rating prevalence 90%; kappa null 0.60 and alternative 0.80.
  Minimum model-based sample 130; modeled power at 140 approximately 82.4%.

Reproduction
  python audit_power_analysis.py
  Requires scipy. The calculation reproduces the three-rater PowerBinary
  algorithm in Python; it is not represented as an executed R analysis.
  Equivalent R call:
  kappaSize::PowerBinary(kappa0=.60, kappa1=.80, props=.90,
                        raters=3, alpha=.20, power=.80)

Interpretation
  This is a power calculation for pooled agreement, not a precision calculation
  for an acceptance-rate confidence interval, nor a guarantee of 90% correctness.
  It assumes independent records and the package's correlated binary rating
  model. Some disagreement patterns have sparse expected counts at this sample
  size, so the quoted power is an asymptotic, model-based planning approximation.
  The inference method and uncertainty procedure must be aligned with the
  agreement endpoint before the sample is drawn.

Protocol choices still to freeze
  - Final audit population and dataset/schema version; sampling seed and
    allocation across nonempty domain/question-type cells.
  - Exact material-error rubric, treatment of inapplicable criteria, and
    adjudication procedure; reviewer names/qualifications and generator blinding.
  - Agreement estimator/test and interval method consistent with the design.
  - Correction/re-audit policy and reporting of original versus corrected data.
  - Alternative annotation model(s), matched comparison subset and endpoints.
  - Final implemented QA types, gold/evidence support and difficulty definitions.
  - Baseline roster, input representations, generation budgets and scoring rules.

Do not enlarge or subdivide the primary audit by generator model and retain
the same power claim without recalculating. Domain/type cells and alternative
annotator comparisons are not individually powered by this calculation.
